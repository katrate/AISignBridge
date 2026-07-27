"""
app/voice_features.py
======================
SINGLE SOURCE OF TRUTH for extracting voice features from raw audio.
Used by BOTH:
  - scripts/train_voice_classifier.py (training)
  - app/speech_listener.py          (live inference)

This matters because train/inference feature mismatch silently breaks the
model. Keeping this in one place makes that class of bug impossible.

Input: 1D float32 numpy array of audio samples at 16 kHz.
Output: 1D float32 feature vector (52 values: 13 MFCC coeffs × 4 stats).
"""

import numpy as np
from scipy.fft import dct
from scipy.signal import spectrogram

SAMPLE_RATE = 16000
N_MFCC = 13
N_FFT = 512
HOP_LENGTH = 256


def compute_mfcc_vector(audio: np.ndarray) -> np.ndarray:
    """Extract MFCC summary features from raw audio.

    Returns a 52-element vector: for each of 13 MFCC coefficients,
    the mean, std, max, and min across all frames.

    Args:
        audio: 1D float32 array of audio samples at SAMPLE_RATE (16 kHz).

    Returns:
        float32 array of shape (52,).
    """
    # Pre-emphasis (boost high frequencies)
    audio = np.append(audio[0], audio[1:] - 0.97 * audio[:-1])

    # Magnitude spectrogram
    _, _, Sxx = spectrogram(
        audio, fs=SAMPLE_RATE, nperseg=N_FFT,
        noverlap=N_FFT - HOP_LENGTH,
        window='hamming', mode='magnitude',
    )

    # Mel filter bank (26 filters)
    n_filt = 26
    low_mel = 0
    high_mel = 2595 * np.log10(1 + SAMPLE_RATE / 2 / 700)
    mel_points = np.linspace(low_mel, high_mel, n_filt + 2)
    hz_points = 700 * (10 ** (mel_points / 2595) - 1)
    bin_indices = np.floor((N_FFT + 1) * hz_points / SAMPLE_RATE).astype(int)
    bin_indices = np.clip(bin_indices, 0, N_FFT // 2)

    filterbank = np.zeros((n_filt, N_FFT // 2 + 1))
    for m in range(1, n_filt + 1):
        l, c, r = bin_indices[m - 1], bin_indices[m], bin_indices[m + 1]
        for k in range(l, c):
            filterbank[m - 1, k] = (k - l) / (c - l)
        for k in range(c, r):
            filterbank[m - 1, k] = (r - k) / (r - c)

    # Apply mel filterbank, log, DCT
    mel_spec = np.maximum(filterbank @ Sxx, 1e-10)
    log_mel = np.log(mel_spec)
    mfccs = dct(log_mel, axis=0, type=2, norm='ortho')[:N_MFCC]

    # Summarize each coefficient across frames: mean, std, max, min
    feats = []
    for i in range(mfccs.shape[0]):
        feats.extend([
            float(np.mean(mfccs[i])),
            float(np.std(mfccs[i])),
            float(np.max(mfccs[i])),
            float(np.min(mfccs[i])),
        ])

    return np.array(feats, dtype=np.float32)
