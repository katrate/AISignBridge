"""
scripts/prepare_dataset.py
===========================
Takes a raw landmarks CSV (63 raw x,y,z coords + label, OR 42 raw xy coords
+ label -- no header) and produces leak-free, balanced, feature-engineered
train/val/test CSVs.

Supports two input formats:
  64 columns: 63 raw xyz (21×3) + label  -- from collect_data.py
  43 columns: 42 raw xy  (21×2) + label  -- from older extraction scripts

Fixes vs the previous version:
  1. TRAIN/TEST LEAK: previously, augmentation (mirror/rotate/scale/jitter)
     was applied BEFORE the train/test split, so near-duplicate versions of
     the same original sample could land in both splits. That inflates
     reported test accuracy without helping real-world accuracy -- the
     model looks great on paper and underperforms on your webcam. Now we
     split FIRST (by original sample), and only ever augment the train set.
  2. CLASS IMBALANCE: classes ranged from 44 to 1348 samples. Rather than
     dropping rare classes (which silently makes some letters impossible to
     predict), we oversample rare classes more aggressively via augmentation
     so every class reaches a similar effective size.
  3. NOISE LABEL: the 'unknown' class (5 samples) is dropped -- not a real
     sign, just noise.
  4. FEATURES: uses app/feature_extraction.py (42 normalized xy + 21 z +
     38 engineered geometric features) instead of only 42 raw xy features.
     The same function is used by the live app, so train and inference
     always match.

Usage:
    python scripts/prepare_dataset.py --input data/combined_dataset.csv
"""

import os
import sys
import argparse
from collections import Counter

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.feature_extraction import extract_features, N_FEATURES

parser = argparse.ArgumentParser()
parser.add_argument("--input", type=str, required=True, help="Raw landmarks CSV (63 or 42 coords + label, no header)")
parser.add_argument("--outdir", type=str, default="data/processed", help="Output directory")
parser.add_argument("--drop-classes", nargs="*", default=["unknown"], help="Label values to discard as noise")
parser.add_argument("--target-per-class", type=int, default=1200, help="Target #samples per class in the TRAIN split after augmentation")
parser.add_argument("--val-size", type=float, default=0.15)
parser.add_argument("--test-size", type=float, default=0.15)
parser.add_argument("--seed", type=int, default=42)
args = parser.parse_args()

rng = np.random.default_rng(args.seed)

# ------------------------------------------------------------------ LOAD
print(f"[INFO] Loading raw dataset: {args.input}")
df = pd.read_csv(args.input, header=None, low_memory=False)
before = len(df)
df = df.dropna()
if len(df) < before:
    print(f"[INFO] Dropped {before - len(df)} NaN rows")

# Handle both 64-col (63 xyz + label) and 43-col (42 xy + label) formats.
if df.shape[1] == 64:
    raw_xyz = df.iloc[:, :63].values.astype(np.float32).reshape(-1, 21, 3)
    labels = df.iloc[:, 63].astype(str).values
elif df.shape[1] == 43:
    print("[INFO] Detected 42-xy-format (no z coordinate) -- padding z=0")
    raw_xy = df.iloc[:, :42].values.astype(np.float32).reshape(-1, 21, 2)
    labels = df.iloc[:, 42].astype(str).values
    # Add zero z coordinates to match (21, 3) shape expected by extract_features
    raw_xyz = np.concatenate([raw_xy, np.zeros((len(raw_xy), 21, 1), dtype=np.float32)], axis=2)
else:
    print(f"[ERROR] Expected 64 columns (63 xyz + label) or 43 columns (42 xy + label), got {df.shape[1]}")
    sys.exit(1)

# ------------------------------------------------------------------ DROP NOISE
keep_mask = ~np.isin(labels, args.drop_classes)
dropped_n = (~keep_mask).sum()
if dropped_n:
    print(f"[INFO] Dropping {dropped_n} rows in noise classes {args.drop_classes}")
raw_xyz = raw_xyz[keep_mask]
labels = labels[keep_mask]

print(f"[INFO] {len(labels)} samples across {len(set(labels))} classes after cleaning")
print("[INFO] Class distribution (raw):")
for cls, cnt in sorted(Counter(labels).items()):
    print(f"    {cls:>6s}: {cnt}")

# ------------------------------------------------------------------ SPLIT FIRST (leak-free)
# Stratified split on ORIGINAL samples, before any augmentation exists.
idx = np.arange(len(labels))
class_counts = Counter(labels)
too_rare_for_split = [c for c, n in class_counts.items() if n < 3]
if too_rare_for_split:
    print(f"[WARNING] Classes with <3 samples can't be safely stratified: {too_rare_for_split}")

idx_train, idx_temp = train_test_split(
    idx, test_size=(args.val_size + args.test_size), random_state=args.seed, stratify=labels
)
rel_test = args.test_size / (args.val_size + args.test_size)
idx_val, idx_test = train_test_split(
    idx_temp, test_size=rel_test, random_state=args.seed, stratify=labels[idx_temp]
)

print(f"\n[INFO] Split (on ORIGINAL samples, before augmentation): "
      f"train={len(idx_train)}  val={len(idx_val)}  test={len(idx_test)}")


# ------------------------------------------------------------------ AUGMENTATION (train only)
def rotate_xy(xy, angle_rad):
    cx, cy = xy.mean(axis=0)
    cos_a, sin_a = np.cos(angle_rad), np.sin(angle_rad)
    R = np.array([[cos_a, -sin_a], [sin_a, cos_a]])
    centered = xy - [cx, cy]
    return centered @ R.T + [cx, cy]


def augment_one(xyz):
    """Apply one random augmentation to a single (21,3) raw landmark sample."""
    xyz = xyz.copy()
    xy = xyz[:, :2]

    # random rotation
    angle = rng.uniform(-np.pi / 6, np.pi / 6)
    xy = rotate_xy(xy, angle)

    # random scale
    scale = rng.uniform(0.85, 1.15)
    center = xy.mean(axis=0)
    xy = center + (xy - center) * scale

    # random aspect stretch
    sx = rng.uniform(0.9, 1.1)
    sy = rng.uniform(0.9, 1.1)
    xy = center + (xy - center) * [sx, sy]

    # jitter (sensor/landmark-detection noise)
    xy = xy + rng.normal(0, 0.006, xy.shape)
    z = xyz[:, 2] + rng.normal(0, 0.006, xyz[:, 2].shape)

    xyz[:, :2] = xy
    xyz[:, 2] = z
    return xyz


def mirror_one(xyz):
    """Left/right hand mirror -- flips the x axis around the sample's own center."""
    xyz = xyz.copy()
    cx = xyz[:, 0].mean()
    xyz[:, 0] = 2 * cx - xyz[:, 0]
    return xyz


def build_split(indices, split_name, augment_to_target):
    X_feats, y_out = [], []
    split_xyz = raw_xyz[indices]
    split_labels = labels[indices]

    if not augment_to_target:
        for xyz, lab in zip(split_xyz, split_labels):
            X_feats.append(extract_features(xyz))
            y_out.append(lab)
        print(f"[INFO] {split_name}: {len(y_out)} samples (no augmentation -- kept clean for honest evaluation)")
        return np.array(X_feats, dtype=np.float32), np.array(y_out)

    # Train split: always include the mirrored variant (real, not synthetic
    # noise -- ASL is commonly signed with either hand), then top up each
    # class with randomized augmentation until it reaches target_per_class.
    per_class_xyz = {}
    for xyz, lab in zip(split_xyz, split_labels):
        per_class_xyz.setdefault(lab, []).append(xyz)

    for lab, samples in per_class_xyz.items():
        base = list(samples) + [mirror_one(s) for s in samples]
        for xyz in base:
            X_feats.append(extract_features(xyz))
            y_out.append(lab)

        n_needed = max(0, args.target_per_class - len(base))
        for _ in range(n_needed):
            src = base[rng.integers(0, len(base))]
            aug = augment_one(src)
            X_feats.append(extract_features(aug))
            y_out.append(lab)

    print(f"[INFO] {split_name}: {len(y_out)} samples after mirror + balancing augmentation")
    return np.array(X_feats, dtype=np.float32), np.array(y_out)


print("\n[INFO] Building splits (train is augmented+balanced, val/test are left clean)...")
X_train, y_train = build_split(idx_train, "train", augment_to_target=True)
X_val, y_val = build_split(idx_val, "val", augment_to_target=False)
X_test, y_test = build_split(idx_test, "test", augment_to_target=False)

print("\n[INFO] Final train class distribution:")
for cls, cnt in sorted(Counter(y_train).items()):
    print(f"    {cls:>6s}: {cnt}")

# ------------------------------------------------------------------ SAVE
os.makedirs(args.outdir, exist_ok=True)
feat_cols = [f"f{i}" for i in range(N_FEATURES)]

for name, X, y in [("train", X_train, y_train), ("val", X_val, y_val), ("test", X_test, y_test)]:
    out_df = pd.DataFrame(X, columns=feat_cols)
    out_df["label"] = y
    path = os.path.join(args.outdir, f"{name}.csv")
    out_df.to_csv(path, index=False)
    print(f"[SAVED] {path}  ({len(out_df)} rows, {X.shape[1]} features)")

print("\n[NEXT] python scripts/train_model.py")
