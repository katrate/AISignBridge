"""
app/feature_extraction.py
==========================
SINGLE SOURCE OF TRUTH for turning 21 raw MediaPipe hand landmarks into the
feature vector the model is trained on. This module is imported by BOTH:
  - the training pipeline (scripts/prepare_dataset.py)
  - the live app (app/sign_detector.py)

This matters because a classic bug in projects like this is computing
features one way during training and a slightly different way at inference
time (e.g. different normalization) -- the model then silently performs
much worse in the live app than in the training notebook. Keeping this in
one place makes that class of bug impossible.

Input: a (21, 3) array of raw (x, y, z) landmark coordinates, in MediaPipe's
native normalized-image-coordinate space (same for both a CSV row and a
live HandLandmarker result).

Output: a 1D float32 feature vector of length N_FEATURES.
"""

import numpy as np
from itertools import combinations

# MediaPipe hand landmark indices
WRIST = 0
THUMB_MCP, THUMB_IP, THUMB_TIP = 2, 3, 4
INDEX_MCP, INDEX_PIP, INDEX_TIP = 5, 6, 8
MIDDLE_MCP, MIDDLE_PIP, MIDDLE_TIP = 9, 10, 12
RING_MCP, RING_PIP, RING_TIP = 13, 14, 16
PINKY_MCP, PINKY_PIP, PINKY_TIP = 17, 18, 20

FINGER_TIPS = [THUMB_TIP, INDEX_TIP, MIDDLE_TIP, RING_TIP, PINKY_TIP]
FINGER_MCPS = [THUMB_MCP, INDEX_MCP, MIDDLE_MCP, RING_MCP, PINKY_MCP]
FINGER_PIPS = [THUMB_IP, INDEX_PIP, MIDDLE_PIP, RING_PIP, PINKY_PIP]

# ---- NEW: Increased feature count ----
# Before: 42 (xy) + 21 (z) + 19 engineered = 82
# After:  42 (xy) + 21 (z) + 38 engineered = 101
# New engineered features capture more subtle distinctions between similar signs:
#   tip_dists (5) + all_tip_dists (10) + ext_ratios (5)
#   + bend_angles (5) + mcp_angles (5) + thumb_to_pip (4)
#   + max_spread + index_pinky_span + palm_angle + spread_angle (4) = 38
N_FEATURES = 101


def _angle(a, b, c):
    """Angle (radians) at point b, formed by points a-b-c."""
    v1 = a - b
    v2 = c - b
    n1 = np.linalg.norm(v1)
    n2 = np.linalg.norm(v2)
    if n1 < 1e-8 or n2 < 1e-8:
        return 0.0
    cos_a = np.clip(np.dot(v1, v2) / (n1 * n2), -1.0, 1.0)
    return float(np.arccos(cos_a))


def _signed_angle_2d(a, b, c):
    """Signed 2D angle (radians) at point b in the xy-plane.
    Positive = counter-clockwise. Useful for distinguishing palm orientation."""
    v1 = a[:2] - b[:2]
    v2 = c[:2] - b[:2]
    n1 = np.linalg.norm(v1)
    n2 = np.linalg.norm(v2)
    if n1 < 1e-8 or n2 < 1e-8:
        return 0.0
    cross = v1[0] * v2[1] - v1[1] * v2[0]
    dot = v1[0] * v2[0] + v1[1] * v2[1]
    return float(np.arctan2(cross, dot))


def extract_features(landmarks_xyz: np.ndarray) -> np.ndarray:
    """
    landmarks_xyz: array-like, shape (21, 3), raw MediaPipe (x, y, z).
    Returns: float32 array, shape (N_FEATURES,)
    """
    pts = np.asarray(landmarks_xyz, dtype=np.float64).reshape(21, 3)
    xy = pts[:, :2]
    z = pts[:, 2]

    # ---- Bounding-box normalization (aspect-ratio preserving) ----
    min_xy = xy.min(axis=0)
    max_xy = xy.max(axis=0)
    max_range = max((max_xy - min_xy).max(), 1e-6)
    norm_xy = (xy - min_xy) / max_range                 # (21, 2)

    # z uses the same scale factor so depth stays proportionate to xy,
    # centered on the wrist (index 0) since MediaPipe's z is relative/noisy.
    norm_z = (z - z[WRIST]) / max_range                  # (21,)

    # ---- Engineered geometric features (computed on normalized points) ----
    norm_pts = np.column_stack([norm_xy, norm_z])        # (21, 3)
    wrist_pt = norm_pts[WRIST]

    # --- a) distance from wrist to each fingertip (5) ---
    tip_dists = [np.linalg.norm(norm_pts[t] - wrist_pt) for t in FINGER_TIPS]

    # --- b) All pairwise fingertip distances (10) ---
    # Was just 4 adjacent distances. Now we compute ALL 10 pairs:
    # thumb-index, thumb-middle, thumb-ring, thumb-pinky,
    # index-middle, index-ring, index-pinky,
    # middle-ring, middle-pinky,
    # ring-pinky
    # This helps distinguish U vs V (index-middle gap) and B vs 4 (finger spread)
    all_tip_dists = [
        np.linalg.norm(norm_pts[i] - norm_pts[j])
        for i, j in combinations(FINGER_TIPS, 2)
    ]

    # --- c) extension ratio per finger (5) ---
    # tip-to-mcp vs wrist-to-mcp. Low = curled, high = extended.
    ext_ratios = []
    for tip, mcp in zip(FINGER_TIPS, FINGER_MCPS):
        wrist_to_mcp = np.linalg.norm(norm_pts[mcp] - wrist_pt) + 1e-6
        tip_to_mcp = np.linalg.norm(norm_pts[tip] - norm_pts[mcp])
        ext_ratios.append(tip_to_mcp / wrist_to_mcp)

    # --- d) bend angle at each finger's middle joint (5) ---
    # Distinguishes curled vs straight fingers
    bend_angles = []
    for tip, pip, mcp in zip(FINGER_TIPS, FINGER_PIPS, FINGER_MCPS):
        bend_angles.append(_angle(norm_pts[mcp], norm_pts[pip], norm_pts[tip]))

    # --- e) BEND ANGLE at each finger's BASE joint (MCP) (5) ---
    # The MCP angle (wrist-mcp-pip) captures how much the whole finger
    # is flexed at the palm, which distinguishes closed-fist letters
    # (A, S, M, N) from open-hand letters (B, 4, 5).
    mcp_angles = []
    for pip, mcp in zip(FINGER_PIPS, FINGER_MCPS):
        mcp_angles.append(_angle(wrist_pt, norm_pts[mcp], norm_pts[pip]))

    # --- f) Thumb-to-finger cross distances (4) ---
    # Distance from thumb tip to each other finger's PIP joint.
    # This is CRITICAL for distinguishing:
    #   A (thumb to side) vs S (thumb wrapped over fingers)
    #   M (thumb between ring-pinky) vs N (thumb between middle-ring)
    thumb_to_pip = [
        np.linalg.norm(norm_pts[THUMB_TIP] - norm_pts[pip])
        for pip in [INDEX_PIP, MIDDLE_PIP, RING_PIP, PINKY_PIP]
    ]

    # --- g) Hand openness / spread features (2) ---
    # Max distance between any two fingertips (overall hand openness)
    max_spread = max(all_tip_dists)
    # Distance from index tip to pinky tip (span of all fingers)
    index_pinky_span = np.linalg.norm(norm_pts[INDEX_TIP] - norm_pts[PINKY_TIP])

    # --- h) Signed 2D angle at key joints for palm orientation (2) ---
    # The angle at the wrist between thumb-MCP and pinky-MCP in xy-space
    # helps distinguish signs with palm-up vs palm-down orientation
    palm_angle = _signed_angle_2d(norm_pts[THUMB_MCP], norm_pts[WRIST], norm_pts[PINKY_MCP])
    # Angle between index MCP and pinky MCP at wrist (hand spread angle)
    spread_angle = _signed_angle_2d(norm_pts[INDEX_MCP], norm_pts[WRIST], norm_pts[PINKY_MCP])

    # Total engineered count: 5 + 10 + 5 + 5 + 5 + 4 + 2 + 2 = 38? No...
    # Let me recount:
    #   a) tip_dists: 5
    #   b) all_tip_dists: 10
    #   c) ext_ratios: 5
    #   d) bend_angles: 5
    #   e) mcp_angles: 5
    #   f) thumb_to_pip: 4
    #   g) max_spread + index_pinky_span: 2
    #   h) palm_angle + spread_angle: 2
    #   Total: 5 + 10 + 5 + 5 + 5 + 4 + 2 + 2 = 38
    #   N_FEATURES = 42 + 21 + 38 = 101
    # Wait, that's 101, not 114.
    # Let me add more features to reach 114 as stated...
    # Actually the exact count doesn't matter as long as it's correct.
    # But I said 114 in the docstring. Let me adjust.
    # Actually let me just set N_FEATURES based on what we actually produce.

    engineered = np.array(
        tip_dists
        + all_tip_dists
        + ext_ratios
        + bend_angles
        + mcp_angles
        + thumb_to_pip
        + [max_spread, index_pinky_span, palm_angle, spread_angle],
        dtype=np.float64,
    )

    features = np.concatenate([
        norm_xy.flatten(),   # 42
        norm_z,               # 21
        engineered,           # engineered features
    ]).astype(np.float32)

    assert features.shape[0] == N_FEATURES, f"Expected {N_FEATURES} features, got {features.shape[0]}"
    return features


def extract_features_from_mediapipe(hand_landmarks) -> np.ndarray:
    """Convenience wrapper for live MediaPipe Tasks API landmark objects
    (each with .x, .y, .z attributes), used by the app at inference time."""
    pts = np.array([[lm.x, lm.y, lm.z] for lm in hand_landmarks], dtype=np.float64)
    return extract_features(pts)
