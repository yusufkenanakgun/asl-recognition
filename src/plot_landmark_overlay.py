"""Tek bir ASL imajı üzerinde MediaPipe Hands landmark'larını çiz.

Tasks API kullanır (projenin diğer extract script'leri ile aynı runtime).

Çıktı:
  thesis/figures/ch4_landmark_overlay.png    raw image | 21 keypoint overlay
"""
from __future__ import annotations

from pathlib import Path

import cv2
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "thesis" / "figures"
OUT.mkdir(parents=True, exist_ok=True)

MODEL_PATH = ROOT / "models" / "hand_landmarker.task"
SAMPLE_DIR = ROOT / "data" / "asl-split" / "test" / "L"

# 21-keypoint HAND_CONNECTIONS (MediaPipe Hands kanonik bağlantıları)
HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),         # thumb
    (0, 5), (5, 6), (6, 7), (7, 8),         # index
    (5, 9), (9, 10), (10, 11), (11, 12),    # middle
    (9, 13), (13, 14), (14, 15), (15, 16),  # ring
    (13, 17), (17, 18), (18, 19), (19, 20), # pinky
    (0, 17),                                # palm
]


def draw_landmarks(image, hand_landmarks) -> None:
    h, w = image.shape[:2]
    pts = [(int(lm.x * w), int(lm.y * h)) for lm in hand_landmarks]

    for a, b in HAND_CONNECTIONS:
        cv2.line(image, pts[a], pts[b], (0, 0, 0), 2)
    for x, y in pts:
        cv2.circle(image, (x, y), 5, (255, 255, 255), -1)
        cv2.circle(image, (x, y), 5, (0, 0, 0), 1)


def main() -> None:
    first = sorted(SAMPLE_DIR.glob("*.jpg"))[0]
    img_bgr = cv2.imread(str(first))
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)

    base_options = python.BaseOptions(model_asset_path=str(MODEL_PATH))
    options = vision.HandLandmarkerOptions(
        base_options=base_options,
        num_hands=1,
        min_hand_detection_confidence=0.5,
    )
    landmarker = vision.HandLandmarker.create_from_options(options)

    mp_image = mp.Image.create_from_file(str(first))
    result = landmarker.detect(mp_image)

    overlay = img_rgb.copy()
    if result.hand_landmarks:
        draw_landmarks(overlay, result.hand_landmarks[0])
    else:
        print(f"WARNING: MediaPipe didn't detect a hand in {first}")

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8, 4))
    ax1.imshow(img_rgb)
    ax1.set_title("Input frame", fontsize=11)
    ax1.axis("off")
    ax2.imshow(overlay)
    ax2.set_title("MediaPipe Hands landmarks", fontsize=11)
    ax2.axis("off")
    fig.tight_layout()
    out_path = OUT / "ch4_landmark_overlay.png"
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"Generated: {out_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
