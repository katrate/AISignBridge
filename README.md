# 🤟 AI Sign Bridge

Real-time **ASL (American Sign Language) fingerspelling translator**. Uses your webcam to recognize hand signs (A-Z, 0-9) and speaks them aloud. Also supports **speech → sign** — say a letter and see how to sign it.

[![Website](https://img.shields.io/badge/website-aisignbridge.vercel.app-amber)](https://aisignbridge.vercel.app)
[![GitHub](https://img.shields.io/badge/github-katrate/AISignBridge-181717)](https://github.com/katrate/AISignBridge)
[![Python](https://img.shields.io/badge/python-3.12%20%7C%203.13-blue)](https://python.org)

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🎥 **Live Webcam Detection** | Real-time hand tracking via MediaPipe Tasks API (21 landmarks, 30+ FPS) |
| 🧠 **Ensemble AI Engine** | 3-model ensemble (Random Forest + HistGradientBoosting + MLP) with 95%+ accuracy |
| 🔄 **Bidirectional Translation** | Sign → Speech AND Speech → Sign (say a letter, see how to sign it) |
| 🎤 **Voice Recognition** | Vosk-based speech-to-sign with restricted grammar (A–Z, 0–9) for high accuracy |
| 🔒 **100% Offline** | All processing runs locally — no internet required, complete privacy |
| 🖼️ **Reference Images** | Displays ASL sign reference photos for every recognized letter |
| 📜 **History Tracking** | Scrollable history of detected signs with temporal smoothing |
| 🌐 **Website Demo** | Browser-based demo at [aisignbridge.vercel.app](https://aisignbridge.vercel.app) with MediaPipe.js hand tracking |
| 🪟 **Desktop App** | PyQt6 native UI with glassmorphism design, real-time webcam, and speech synthesis |

---

## 📋 Requirements

- **Windows 10/11**, macOS, or Linux
- **Python 3.12** (recommended) or **3.13** (partial support — see below)
- Webcam

### Python 3.13 Compatibility

Python 3.13 works for the **website demo server** and most scripts, but **TensorFlow does not yet support 3.13**. If you have 3.13:

- ✅ Website demo (`website/demo_server.py`) — works
- ✅ Data collection, feature extraction — works  
- ❌ TensorFlow model training/loading — use 3.12

---

## 🚀 Quick Start

### 1. Install Python 3.12

```bash
winget install Python.Python.3.12
```

### 2. Install dependencies

```bash
py -3.12 -m pip install -r requirements.txt
```

### 3. Download Vosk speech model

```bash
py -3.12 scripts/download_vosk_model.py
```

### 4. Run the app

```bash
py -3.12 app/main.py
```

Click **Start** and show hand signs to the camera!

### Run the Website Demo

```bash
pip install flask flask-cors
py website/demo_server.py
# Opens at http://localhost:5000
```

The website is also live at **[aisignbridge.vercel.app](https://aisignbridge.vercel.app)**.

---

## 🧠 How It Works

### Sign → Speech Pipeline

1. **Camera Capture** — OpenCV captures frames from your webcam at 30 FPS
2. **Hand Landmarks** — MediaPipe Tasks API detects 21 precise 3D hand landmarks
3. **Feature Extraction** — 101 geometric features: normalized coordinates, fingertip distances, extension ratios, bend angles, palm orientation
4. **Ensemble Classification** — Weighted average of 3 models (RF + HGB + MLP) — each model gets different classes wrong, so their average outperforms any single model
5. **Temporal Smoothing** — Sliding window (15 frames) + majority vote + top-2 gap check prevents flickering
6. **Speech Output** — pyttsx3 speaks the recognized sign via offline TTS with queued background thread

### Speech → Sign Pipeline

1. **Microphone Input** — sounddevice captures 16 kHz audio
2. **Vosk Recognition** — Restricted grammar mode (only A–Z, 0–9) for high letter accuracy
3. **Sign Display** — Shows the corresponding ASL hand sign reference image

---

## 🎯 Usage Tips

- **Good lighting** improves detection accuracy dramatically
- Hold your hand **~30–50 cm** from the camera
- Keep your hand **flat and facing the camera**
- Say letters clearly for the speech → sign feature
- The app works **fully offline** — no internet required

---

## 📊 Training Your Own Model

The app comes with a pre-trained ensemble model (~95% accuracy), but you can improve it:

### Collect gesture data

```bash
py -3.12 scripts/collect_data.py --label A --samples 200
```

### Train the ensemble model

```bash
py -3.12 scripts/train_model.py
```

### Train voice classifier

```bash
py -3.12 scripts/collect_voice_data.py --label A
py -3.12 scripts/train_voice_classifier.py
```

---

## 🏗️ Project Structure

```
ai-sign-bridge/
├── app/
│   ├── main.py                   # Entry point
│   ├── main_window.py            # PyQt6 UI (glassmorphism, 1069 lines)
│   ├── sign_detector.py          # Webcam + MediaPipe + ensemble inference
│   ├── speech_engine.py          # Offline TTS with background worker thread
│   ├── speech_listener.py        # Vosk speech recognition (grammar mode)
│   ├── feature_extraction.py     # 101-dim hand landmark features
│   ├── voice_features.py         # MFCC audio features (52-dim)
│   └── ensemble_model.py         # Weighted RF + HGB + MLP ensemble
├── models/
│   ├── gesture_model.h5          # Trained TF/Keras model
│   ├── gesture_model.pkl         # Fallback sklearn ensemble
│   ├── label_encoder.pkl         # Label mappings (A–Z, 0–9)
│   ├── normalizer.pkl            # Feature normalization
│   ├── voice_classifier.pkl      # Voice recognition model
│   └── hand_landmarker.task      # MediaPipe hand model
├── data/
│   └── raw_images/               # ASL sign reference images (A–Z, 0–9)
├── scripts/
│   ├── train_model.py            # Ensemble training pipeline
│   ├── collect_data.py           # Gesture data collection
│   ├── train_voice_classifier.py # Voice model training
│   ├── collect_voice_data.py     # Voice sample collection
│   ├── download_vosk_model.py    # Download Vosk speech model
│   └── augment_dataset.py        # Data augmentation
├── website/
│   ├── index.html                # Landing page
│   ├── demo.html                 # Browser-based webcam demo (MediaPipe.js)
│   ├── demo_server.py            # Flask backend (real model inference API)
│   ├── release-data.json         # Latest release download URLs
│   └── vercel.json               # Vercel deployment config
└── .github/workflows/
    └── build.yml                 # CI: build EXE/DMG/AppImage on tags
```

---

## 🌐 Website

The project website is deployed on **Vercel** at [aisignbridge.vercel.app](https://aisignbridge.vercel.app).

- Built with vanilla HTML/CSS/JS + Three.js animations
- Browser-based hand tracking demo using MediaPipe.js
- Responsive design with dark/light theme
- Auto-detects your OS and provides the correct download link
- Real-time sign detection using MediaPipe Tasks Vision WASM

### Deploy your own

```bash
cd website
vercel --prod
```

Or connect the repo to Vercel (root: `website/`) for automatic deploys on push.

---

## 📦 Downloads

Pre-built binaries are built automatically via GitHub Actions when a new tag (`v*`) is pushed:

| Platform | Format | How to get |
|----------|--------|-----------|
| Windows | `.exe` (PyInstaller) | [Releases page](https://github.com/katrate/AISignBridge/releases) |
| macOS | `.dmg` | [Releases page](https://github.com/katrate/AISignBridge/releases) |
| Linux | `.AppImage` | [Releases page](https://github.com/katrate/AISignBridge/releases) |

To trigger a build:

```bash
git tag v1.0.0
git push origin v1.0.0
```

---

## 🛠 Tech Stack

| Component | Library |
|-----------|---------|
| UI | PyQt6 |
| Hand Tracking | MediaPipe Tasks API |
| ML Ensemble | scikit-learn (RF + HGB + MLP) |
| Deep Learning | TensorFlow/Keras |
| Speech Output | pyttsx3 (SAPI5) |
| Speech Input | Vosk (grammar mode) |
| Audio I/O | sounddevice |
| Audio Features | SciPy MFCC |
| Video | OpenCV |
| Build Tool | PyInstaller |
| Website | HTML/CSS/JS + Three.js |
| Deployment | Vercel |
| CI/CD | GitHub Actions |

---

## 📝 License

MIT
