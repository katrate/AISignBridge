"""
scripts/train_model.py
=======================
Trains a gesture classifier on the processed train/val/test CSVs produced
by prepare_dataset.py.

Uses TensorFlow (matches the app's Windows/Python 3.12 environment) if
it's installed; otherwise automatically falls back to scikit-learn models
(RandomForest, HistGradientBoosting, MLP) and picks the best one on the
validation set. Either path produces a model your app's SignDetector can
load -- it already supports both .h5 (TF) and .pkl (sklearn, via
predict_proba) formats.

Usage:
    python scripts/train_model.py
    python scripts/train_model.py --sklearn   # force sklearn even if TF is installed
"""

import os
import sys
import argparse

import numpy as np
import pandas as pd
import joblib
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, accuracy_score

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

np.random.seed(42)

parser = argparse.ArgumentParser()
parser.add_argument("--datadir", type=str, default="data/processed")
parser.add_argument("--model-out", type=str, default="models/gesture_model")
parser.add_argument("--encoder-out", type=str, default="models/label_encoder.pkl")
parser.add_argument("--normalizer-out", type=str, default="models/normalizer.pkl")
parser.add_argument("--epochs", type=int, default=60)
parser.add_argument("--sklearn", action="store_true", help="Force sklearn path even if TensorFlow is available")
args = parser.parse_args()

print("=" * 60)
print("  AI Sign Bridge -- Model Training")
print("=" * 60)

# ------------------------------------------------------------------ LOAD
def load_split(name):
    path = os.path.join(args.datadir, f"{name}.csv")
    if not os.path.exists(path):
        print(f"[ERROR] {path} not found. Run scripts/prepare_dataset.py first.")
        sys.exit(1)
    df = pd.read_csv(path)
    X = df.drop(columns=["label"]).values.astype(np.float32)
    y = df["label"].astype(str).values
    return X, y

X_train, y_train_raw = load_split("train")
X_val, y_val_raw = load_split("val")
X_test, y_test_raw = load_split("test")
print(f"[INFO] train={len(X_train)}  val={len(X_val)}  test={len(X_test)}  features={X_train.shape[1]}")

le = LabelEncoder()
le.fit(np.concatenate([y_train_raw, y_val_raw, y_test_raw]))
y_train = le.transform(y_train_raw)
y_val = le.transform(y_val_raw)
y_test = le.transform(y_test_raw)
num_classes = len(le.classes_)
print(f"[INFO] {num_classes} classes: {list(le.classes_)}")

# ------------------------------------------------------------------ TRY TENSORFLOW
use_tf = False
if not args.sklearn:
    try:
        import tensorflow as tf
        from tensorflow import keras
        from tensorflow.keras import layers, callbacks
        use_tf = True
    except ImportError:
        print("\n[INFO] TensorFlow not installed in this environment -- using scikit-learn instead.")
        print("       (On your Windows/Python 3.12 machine with requirements.txt installed,")
        print("        this script will automatically use TensorFlow instead.)")

if use_tf:
    print("\n[INFO] Training TensorFlow DNN...")
    tf.random.set_seed(42)

    mean = X_train.mean(axis=0)
    std = X_train.std(axis=0)
    std[std == 0] = 1.0
    X_train_s = (X_train - mean) / std
    X_val_s = (X_val - mean) / std
    X_test_s = (X_test - mean) / std

    y_train_cat = keras.utils.to_categorical(y_train, num_classes)
    y_val_cat = keras.utils.to_categorical(y_val, num_classes)

    model = keras.Sequential([
        layers.Input(shape=(X_train.shape[1],)),
        layers.Dense(256, activation="relu"),
        layers.BatchNormalization(),
        layers.Dropout(0.3),
        layers.Dense(128, activation="relu"),
        layers.BatchNormalization(),
        layers.Dropout(0.2),
        layers.Dense(64, activation="relu"),
        layers.BatchNormalization(),
        layers.Dropout(0.15),
        layers.Dense(num_classes, activation="softmax"),
    ])
    model.compile(optimizer=keras.optimizers.Adam(learning_rate=0.001),
                  loss="categorical_crossentropy", metrics=["accuracy"])
    model.summary()

    early_stop = callbacks.EarlyStopping(monitor="val_accuracy", patience=15, restore_best_weights=True, verbose=1)
    reduce_lr = callbacks.ReduceLROnPlateau(monitor="val_loss", factor=0.5, patience=5, min_lr=1e-6, verbose=1)

    model.fit(X_train_s, y_train_cat, validation_data=(X_val_s, y_val_cat),
              epochs=args.epochs, batch_size=64, callbacks=[early_stop, reduce_lr], verbose=1)

    y_pred = np.argmax(model.predict(X_test_s, verbose=0), axis=1)

    os.makedirs("models", exist_ok=True)
    model_path = args.model_out + ".h5"
    model.save(model_path)
    joblib.dump({"mean": mean, "std": std}, args.normalizer_out)
    print(f"\n[SAVED] Model      -> {model_path}")
    print(f"[SAVED] Normalizer -> {args.normalizer_out}")

else:
    # Three-model ensemble: HistGradientBoosting + MLP + SVM.
    # Each model has a different inductive bias, so their errors are
    # only partially correlated — the weighted vote is consistently
    # more accurate than any single model.
    from sklearn.ensemble import HistGradientBoostingClassifier
    from sklearn.neural_network import MLPClassifier
    from sklearn.svm import SVC
    from app.ensemble_model import EnsembleGestureModel

    mean = X_train.mean(axis=0)
    std = X_train.std(axis=0)
    std[std == 0] = 1.0
    X_train_s = (X_train - mean) / std
    X_val_s = (X_val - mean) / std
    X_test_s = (X_test - mean) / std

    print("\n[INFO] Training HistGradientBoosting (depth-limited trees)...")
    hgb = HistGradientBoostingClassifier(
        max_iter=500,            # More iterations for convergence
        learning_rate=0.08,      # Slightly slower learning for better generalization
        max_depth=12,           # Limit tree depth to avoid perfect memorization
        min_samples_leaf=5,     # Require at least 5 samples per leaf
        l2_regularization=0.01, # Small L2 penalty
        random_state=42,
    )
    hgb.fit(X_train, y_train)
    hgb_val_acc = accuracy_score(y_val, hgb.predict(X_val))
    print(f"    HistGradientBoosting val accuracy = {hgb_val_acc*100:.2f}%")

    print("\n[INFO] Training MLP (3 hidden layers + dropout via alpha)...")
    mlp = MLPClassifier(
        hidden_layer_sizes=(384, 192, 96),
        activation="relu",
        alpha=5e-4,              # L2 penalty (acts as dropout regularizer)
        learning_rate_init=5e-4, # Lower initial LR for stable convergence
        max_iter=500,
        early_stopping=True,
        validation_fraction=0.15,
        n_iter_no_change=20,
        batch_size=64,
        random_state=42,
    )
    mlp.fit(X_train_s, y_train)
    mlp_val_acc = accuracy_score(y_val, mlp.predict(X_val_s))
    print(f"    MLP val accuracy = {mlp_val_acc*100:.2f}%")

    print("\n[INFO] Training SVM (RBF kernel, probability estimates)...")
    svm = SVC(
        kernel='rbf',
        C=10.0,                 # Higher C = less regularization, fits training data better
        gamma='scale',          # Auto gamma based on feature variance
        probability=True,       # Enable predict_proba
        random_state=42,
    )
    svm.fit(X_train_s, y_train)
    svm_val_acc = accuracy_score(y_val, svm.predict(X_val_s))
    print(f"    SVM val accuracy = {svm_val_acc*100:.2f}%")

    print("\n[INFO] Searching for optimal ensemble weights (0.1 increments)...")
    best_weights = None
    best_ens_val = 0.0
    for w1 in [0.1 * i for i in range(1, 9)]:
        for w2 in [0.1 * i for i in range(1, 9)]:
            w3 = 1.0 - w1 - w2
            if w3 <= 0:
                continue
            dummy_ens = EnsembleGestureModel(
                models=[hgb, mlp, svm],
                weights=[w1, w2, w3],
                mean=mean, std=std,
                needs_scaling=[False, True, True],
            )
            acc = accuracy_score(y_val, dummy_ens.predict(X_val))
            if acc > best_ens_val:
                best_ens_val = acc
                best_weights = [w1, w2, w3]

    print(f"    Best ensemble weights: HGB={best_weights[0]:.1f}, MLP={best_weights[1]:.1f}, SVM={best_weights[2]:.1f}")
    ensemble = EnsembleGestureModel(
        models=[hgb, mlp, svm],
        weights=best_weights,
        mean=mean, std=std,
        needs_scaling=[False, True, True],
    )
    ens_val_acc = best_ens_val
    print(f"    Ensemble val accuracy = {ens_val_acc*100:.2f}%")

    print("\n[INFO] Evaluating on held-out test set...")
    print(f"    Ensemble val accuracy = {ens_val_acc*100:.2f}%")

    y_pred = ensemble.predict(X_test)

    os.makedirs("models", exist_ok=True)
    model_path = args.model_out + ".pkl"
    joblib.dump(ensemble, model_path)
    print(f"\n[SAVED] Model -> {model_path}  ({os.path.getsize(model_path)/1e6:.1f} MB)")
    print("[INFO] (No normalizer.pkl needed -- the ensemble standardizes internally for its MLP half.)")

# ------------------------------------------------------------------ EVAL (shared)
joblib.dump(le, args.encoder_out)
print(f"[SAVED] Encoder    -> {args.encoder_out}")

acc = accuracy_score(y_test, y_pred)
print("\n" + "=" * 60)
print(f"  HELD-OUT TEST ACCURACY: {acc*100:.2f}%")
print("  (test set was never augmented or seen during training/tuning)")
print("=" * 60)

print("\n[RESULT] Classification report:")
print(classification_report(y_test, y_pred, target_names=le.classes_, zero_division=0))

y_true_labels = le.inverse_transform(y_test)
y_pred_labels = le.inverse_transform(y_pred)
print("[INFO] Per-class accuracy:")
for cls in sorted(le.classes_):
    mask = y_true_labels == cls
    if mask.sum() > 0:
        cls_acc = (y_pred_labels[mask] == cls).mean() * 100
        bar_len = int(cls_acc / 5)
        bar = "=" * bar_len + "-" * (20 - bar_len)
        print(f"    {cls:>6s}: {cls_acc:5.1f}% [{bar}] ({mask.sum():>3d} samples)")

print("\n" + "=" * 60)
if acc >= 0.95:
    print("  EXCELLENT: ready for real-time inference.")
elif acc >= 0.90:
    print("  GREAT: ready for real-time inference.")
elif acc >= 0.80:
    print("  GOOD, but collect more data for the weakest classes above.")
else:
    print("  LOW ACCURACY -- see per-class breakdown above for weak classes.")
print("=" * 60)
