# 🤟 AI Sign Bridge

Real-time **ASL (American Sign Language) fingerspelling translator**. Uses your webcam to recognize hand signs (A-Z, 0-9) and speaks them aloud. Also supports **speech → sign** — say a letter and see how to sign it.

---

## 📋 Requirements

- **Windows 10/11**
- **Python 3.12** (TensorFlow not available on 3.13+)
- Webcam

---

## 🚀 Quick Start

### 1. Install Python 3.12

If you don't have it:
```bash
winget install Python.Python.3.12
```

### 2. Install dependencies

```bash
py -3.12 -m pip install -r requirements.txt
```

### 3. Run the app

```bash
py -3.12 app\main.py
```

Click **Start** and show hand signs to the camera!

---

## 🧠 How It Works

1. **Webcam capture** — OpenCV captures frames from your camera
2. **Hand tracking** — MediaPipe detects 21 hand landmarks in real-time
3. **Sign classification** — A TensorFlow DNN predicts the letter/number from the landmarks
4. **Speech output** — pyttsx3 speaks the detected sign aloud
5. **Speech input** — Vosk listens for spoken letters and shows the corresponding sign image

---

## 📊 Training Your Own Model

The app comes with a pre-trained model, but you can retrain for better accuracy:

### Train the TensorFlow DNN:
```bash
py -3.12 scripts\train_model.py
```

### Collect more data for specific letters:
```bash
py -3.12 scripts\collect_data.py --label A --samples 200
```

Then retrain:
```bash
py -3.12 scripts\train_model.py --input data\combined_dataset.csv
```

---

## 📁 Project Structure

```
ai-sign-bridge/
├── app/
│   ├── main.py              # Entry point
│   ├── main_window.py       # UI (PyQt6)
│   ├── sign_detector.py     # Webcam + hand landmark detection
│   ├── speech_engine.py     # Text-to-speech
│   └── speech_listener.py   # Speech recognition (Vosk)
├── models/
│   ├── gesture_model.h5     # Trained TF DNN model
│   ├── gesture_model.pkl    # Fallback pickle model
│   ├── label_encoder.pkl    # Label mappings
│   ├── normalizer.pkl       # Feature normalization params
│   └── hand_landmarker.task # MediaPipe hand model
├── data/
│   ├── combined_dataset.csv # Training dataset
│   └── raw_images/          # Sign reference images (A-Z, 0-9)
├── scripts/
│   ├── train_model.py       # TF DNN training
│   ├── collect_data.py      # Data collection
│   └── extract_features_from_images.py
├── requirements.txt
└── README.md
```

---

## 🎯 Usage Tips

- **Good lighting** improves detection accuracy
- Hold your hand **~30-50cm** from the camera
- Keep your hand **flat and facing the camera**
- Say letters clearly for the speech → sign feature
- The app works **fully offline** — no internet required

---

## 🛠 Tech Stack

| Component | Library |
|-----------|---------|
| UI | PyQt6 |
| Hand Tracking | MediaPipe Tasks API |
| ML Model | TensorFlow/Keras DNN |
| Speech Output | pyttsx3 |
| Speech Input | Vosk |
| Video | OpenCV |

---

## 📝 License

MIT
