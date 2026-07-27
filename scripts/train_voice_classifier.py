"""
scripts/train_voice_classifier.py
==================================
Trains a custom speech-to-letter classifier on YOUR voice recordings
(collected by collect_voice_data.py).

Uses MFCC features (computed via scipy) which capture how each letter
sounds when YOU say it. This is far more accurate for similar-sounding
letters (K/A, I/E, M/N) than a generic Vosk model.

Usage:
    python scripts/train_voice_classifier.py
"""

import os
import sys
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, classification_report
import joblib

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.voice_features import compute_mfcc_vector

DATA_DIR = os.path.join("data", "voice_samples")
MODEL_OUT = os.path.join("models", "voice_classifier.pkl")
ENCODER_OUT = os.path.join("models", "voice_label_encoder.pkl")


def extract_features_from_file(filepath: str) -> np.ndarray:
    """Load a .npy audio file and return the MFCC feature vector."""
    audio = np.load(filepath)
    # Normalize volume
    max_val = np.max(np.abs(audio))
    if max_val > 0:
        audio = audio / max_val
    return compute_mfcc_vector(audio)


def main():
    print("=" * 60)
    print("  AI Sign Bridge — Voice Classifier Training")
    print("=" * 60)

    # Check for data
    if not os.path.isdir(DATA_DIR):
        print(f"\n[ERROR] No data found at '{DATA_DIR}'.")
        print("  Run:  python scripts/collect_voice_data.py")
        sys.exit(1)

    files = [f for f in os.listdir(DATA_DIR) if f.endswith(".npy")]
    if not files:
        print(f"\n[ERROR] No .npy files found in '{DATA_DIR}'.")
        print("  Run:  python scripts/collect_voice_data.py")
        sys.exit(1)

    print(f"\n[INFO] Found {len(files)} audio samples in '{DATA_DIR}/'")

    # Extract features
    print("\n[INFO] Extracting MFCC features...")
    X, y = [], []
    for fname in sorted(files):
        label = fname.split("_")[0]  # e.g. "A_01.npy" -> "A"
        fpath = os.path.join(DATA_DIR, fname)
        feats = extract_features_from_file(fpath)
        X.append(feats)
        y.append(label)

    X = np.array(X, dtype=np.float32)
    y = np.array(y)

    print(f"[INFO] Feature vectors: {X.shape[0]} samples × {X.shape[1]} features")

    # Encode labels
    le = LabelEncoder()
    y_enc = le.fit_transform(y)
    print(f"[INFO] Classes: {list(le.classes_)}")

    # Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_enc, test_size=0.2, random_state=42, stratify=y_enc
    )
    print(f"[INFO] Train: {len(X_train)}  Test: {len(X_test)}")

    # Train Random Forest
    print("\n[INFO] Training Random Forest classifier...")
    rf = RandomForestClassifier(
        n_estimators=200, max_depth=20, min_samples_leaf=2,
        random_state=42, n_jobs=-1
    )
    rf.fit(X_train, y_train)
    rf_test_acc = accuracy_score(y_test, rf.predict(X_test))
    print(f"    RandomForest test accuracy = {rf_test_acc*100:.1f}%")

    # Train MLP
    print("\n[INFO] Training MLP classifier...")
    mlp = MLPClassifier(
        hidden_layer_sizes=(128, 64), activation="relu",
        alpha=1e-3, max_iter=300, early_stopping=True,
        random_state=42
    )
    mlp.fit(X_train, y_train)
    mlp_test_acc = accuracy_score(y_test, mlp.predict(X_test))
    print(f"    MLP test accuracy = {mlp_test_acc*100:.1f}%")

    # Pick the better one
    if rf_test_acc >= mlp_test_acc:
        model = rf
        print("\n[INFO] Using RandomForest (better accuracy).")
    else:
        model = mlp
        print("\n[INFO] Using MLP (better accuracy).")

    # Save
    os.makedirs("models", exist_ok=True)
    joblib.dump(model, MODEL_OUT)
    joblib.dump(le, ENCODER_OUT)
    print(f"\n[SAVED] Voice classifier -> {MODEL_OUT}")
    print(f"[SAVED] Label encoder     -> {ENCODER_OUT}")

    # Report
    y_pred = model.predict(X_test)
    print("\n" + "=" * 60)
    print("  Classification Report (held-out test):")
    print("=" * 60)
    print(classification_report(y_test, y_pred, target_names=le.classes_, zero_division=0))

    acc = accuracy_score(y_test, y_pred)
    print(f"\n  OVERALL TEST ACCURACY: {acc*100:.1f}%")
    print("=" * 60)

    print("\n[NEXT] Run the app:  python app/main.py")
    print("       The app will auto-detect and use your custom voice model.")


if __name__ == "__main__":
    main()
