#!/usr/bin/env python3
"""
AI Sign Bridge — Demo Server
================================
Optional Python backend for the web demo page.
Provides a simulated sign detection API endpoint.

Usage:
    pip install flask flask-cors
    python demo_server.py

Then visit http://localhost:5000/demo.html
The demo page will connect to this server for enhanced interactivity.
"""

import random
import time
import json
import os
import threading

try:
    from flask import Flask, jsonify, request, send_from_directory
    from flask_cors import CORS
except ImportError:
    print("=" * 60)
    print("  Flask not installed. Install with:")
    print("  pip install flask flask-cors")
    print("=" * 60)
    print("  Falling back: The demo will work without the server.")
    print("  The interactive sign grid works client-side.")
    print("=" * 60)
    exit(0)

app = Flask(__name__, static_folder='.')
CORS(app)

# ── Simulated Detection Engine ──

LETTERS = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
DETECTION_HISTORY = []
SESSION_STATS = {
    "total_detections": 47,
    "avg_confidence": 96.3,
    "start_time": time.time(),
}

@app.route('/api/detect', methods=['POST'])
def detect():
    """
    Simulate sign detection. Accepts optional 'letter' parameter
    or returns a random prediction with realistic confidence.
    """
    data = request.get_json() or {}
    letter = data.get('letter')

    if letter and letter.upper() in LETTERS:
        letter = letter.upper()
    else:
        letter = random.choice(LETTERS)

    # Simulate realistic confidence (92-99%)
    confidence = round(92 + random.random() * 7, 1)

    detection = {
        "letter": letter,
        "confidence": confidence,
        "timestamp": time.time(),
        "latency_ms": round(random.uniform(45, 95), 1),
    }

    DETECTION_HISTORY.append(detection)
    SESSION_STATS["total_detections"] += 1
    SESSION_STATS["avg_confidence"] = round(
        (SESSION_STATS["avg_confidence"] * (SESSION_STATS["total_detections"] - 1) + confidence)
        / SESSION_STATS["total_detections"],
        1
    )

    return jsonify(detection)


@app.route('/api/stats', methods=['GET'])
def stats():
    """Return current session statistics."""
    uptime = time.time() - SESSION_STATS["start_time"]
    return jsonify({
        **SESSION_STATS,
        "uptime_seconds": round(uptime, 1),
        "history_count": len(DETECTION_HISTORY),
        "recent_history": DETECTION_HISTORY[-10:] if DETECTION_HISTORY else [],
    })


@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "ok",
        "model": "AI Sign Bridge Demo v1.0",
        "endpoint": "simulated (client-side in browser)",
    })


# Serve static files (the website)
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')


@app.route('/<path:path>')
def static_files(path):
    if os.path.exists(os.path.join('.', path)):
        return send_from_directory('.', path)
    return send_from_directory('.', 'index.html')


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"""
╔══════════════════════════════════════════════════╗
║        AI Sign Bridge — Demo Server              ║
╠══════════════════════════════════════════════════╣
║  Running on: http://localhost:{port}              ║
║                                                    ║
║  API Endpoints:                                    ║
║    POST /api/detect  — Simulate sign detection     ║
║    GET  /api/stats   — Session statistics          ║
║    GET  /api/health  — Health check                ║
║                                                    ║
║  Press Ctrl+C to stop the server.                  ║
╚══════════════════════════════════════════════════╝
    """)
    app.run(host='0.0.0.0', port=port, debug=False)
