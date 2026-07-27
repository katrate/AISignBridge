"""
Phase 1a: Extract Features from Images (Kaggle Dataset)
======================================================
This script reads images from data/raw_images/, extracts MediaPipe 
hand landmarks, and saves them to a CSV format compatible with
our training pipeline.

Directory structure expected:
data/
  raw_images/
    A/
      image1.jpg
      image2.jpg
    B/
      image1.jpg
    ...
    0/
    ...

Usage:
    python scripts/extract_features_from_images.py
"""

import os
import cv2
import csv
import sys
import argparse
import mediapipe as mp
from tqdm import tqdm

parser = argparse.ArgumentParser()
parser.add_argument("--dir", type=str, default=None, help="Directory containing class subfolders")
args = parser.parse_args()

RAW_DATA_DIR = args.dir
if not RAW_DATA_DIR:
    if os.path.exists("data/raw_images") and len(os.listdir("data/raw_images")) > 10:
        RAW_DATA_DIR = "data/raw_images"
    elif os.path.exists(r"c:\Users\HP\Documents\Comp\archive\asl-numbers-alphabet-dataset"):
        RAW_DATA_DIR = r"c:\Users\HP\Documents\Comp\archive\asl-numbers-alphabet-dataset"
    else:
        RAW_DATA_DIR = "data/raw_images"

OUTPUT_CSV = "data/landmarks_from_images.csv"

# Initialize MediaPipe Hands (legacy solutions API)
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=True, 
    max_num_hands=1, 
    min_detection_confidence=0.5
)

def extract_features():
    if not os.path.exists(RAW_DATA_DIR):
        print(f"[ERROR] Directory '{RAW_DATA_DIR}' not found.")
        print(f"Please download the Kaggle dataset, extract it, and place the class folders (A-Z, 0-9) inside '{RAW_DATA_DIR}'.")
        return

    classes = [d for d in os.listdir(RAW_DATA_DIR) if os.path.isdir(os.path.join(RAW_DATA_DIR, d))]
    
    if not classes:
        print(f"[ERROR] No class folders found in '{RAW_DATA_DIR}'.")
        return
        
    print(f"[INFO] Found {len(classes)} classes: {sorted(classes)}")
    
    total_images_processed = 0
    total_hands_detected = 0

    os.makedirs(os.path.dirname(OUTPUT_CSV) if os.path.dirname(OUTPUT_CSV) else ".", exist_ok=True)
    
    with open(OUTPUT_CSV, mode="w", newline="") as f:
        writer = csv.writer(f)
        
        for class_name in sorted(classes):
            class_dir = os.path.join(RAW_DATA_DIR, class_name)
            images = [img for img in os.listdir(class_dir) if img.lower().endswith(('.png', '.jpg', '.jpeg'))]
            
            print(f"[INFO] Processing class '{class_name}' ({len(images)} images)...")
            
            for img_name in tqdm(images, leave=False):
                img_path = os.path.join(class_dir, img_name)
                total_images_processed += 1
                
                # Read image
                image = cv2.imread(img_path)
                if image is None:
                    continue
                
                # Convert BGR to RGB for MediaPipe
                image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                
                # Process image
                results = hands.process(image_rgb)
                
                # If hand is detected
                if results.multi_hand_landmarks:
                    total_hands_detected += 1
                    # We only process the first hand found
                    hand_landmarks = results.multi_hand_landmarks[0]
                    
                    row = []
                    # Extract x, y, z for all 21 landmarks (63 features)
                    for landmark in hand_landmarks.landmark:
                        row.extend([landmark.x, landmark.y, landmark.z])
                    
                    # Add the label as the 64th column
                    row.append(class_name)
                    
                    # Write to CSV
                    writer.writerow(row)
                    
    print(f"\n[SUCCESS] Extraction complete.")
    print(f"[INFO] Total images processed: {total_images_processed}")
    print(f"[INFO] Hands detected and saved: {total_hands_detected}")
    print(f"[INFO] Data saved to {OUTPUT_CSV}")
    print(f"[NEXT] Run: python scripts/prepare_dataset.py --input {OUTPUT_CSV} --output data/landmarks_dnn.csv")

if __name__ == "__main__":
    extract_features()
