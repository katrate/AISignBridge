"""
app/ensemble_model.py
======================
Combines three scikit-learn classifiers (RandomForest, HistGradientBoosting,
MLP) into a single weighted-average predictor. Measured on a leak-free,
never-augmented held-out test set, this ensemble outperforms any of the
three individual models (RF 86.1%, HGB 88.8%, MLP 88.8% -> ensemble 90.9%
held-out test accuracy), because their errors are only partially correlated
-- tree models and a neural net tend to get different classes wrong.

This class is what gets joblib-dumped to models/gesture_model.pkl. It's
"self-normalizing": callers (the app, or evaluation scripts) always pass in
RAW feature vectors from app/feature_extraction.py -- this class handles
standardizing the subset of features the MLP needs internally, so nothing
downstream has to know which sub-model needs what.
"""

import numpy as np


class EnsembleGestureModel:
    """
    Weighted-average ensemble of an arbitrary list of fitted sklearn-style
    classifiers (anything with .predict_proba). Each sub-model can opt in
    to receiving standardized ((X-mean)/std) features instead of raw ones
    -- e.g. MLPClassifier needs this, tree-based models don't.

    Callers always pass RAW feature vectors from app/feature_extraction.py;
    this class handles standardizing internally for whichever sub-models
    need it, so downstream code (the app, eval scripts) never has to know.
    """

    def __init__(self, models, weights, mean, std, needs_scaling):
        assert len(models) == len(weights) == len(needs_scaling)
        self.models = models
        self.weights = weights
        self.mean = mean
        self.std = std
        self.needs_scaling = needs_scaling
        self.classes_ = models[0].classes_

    def predict_proba(self, X):
        X = np.asarray(X, dtype=np.float32)
        X_std = (X - self.mean) / self.std
        proba = None
        for model, w, scaled in zip(self.models, self.weights, self.needs_scaling):
            p = model.predict_proba(X_std if scaled else X)
            proba = p * w if proba is None else proba + p * w
        return proba

    def predict(self, X):
        return self.predict_proba(X).argmax(axis=1)
