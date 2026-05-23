"""Tez Bölüm 4 için veri seti örnek görselleri.

Çıktı:
  thesis/figures/ch4_asl_alphabet_samples.png    8 harf, 2x4 grid
  thesis/figures/ch4_wlasl_strip_drink.png       drink: 6 eş aralıklı frame
  thesis/figures/ch4_wlasl_strip_before.png      before: 6 eş aralıklı frame
"""
from __future__ import annotations

from pathlib import Path

import cv2
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "thesis" / "figures"
OUT.mkdir(parents=True, exist_ok=True)

ASL_LETTERS = ["A", "E", "M", "N", "R", "V", "del", "space"]
# (gloss, video_index)  — video_index folder içindeki sıralı .mp4 dosyalarından hangisini seçeceğini gösterir
WLASL_SIGNS = [("drink", 0), ("mother", 1)]
N_FRAMES = 6


def plot_asl_grid() -> None:
    fig, axes = plt.subplots(2, 4, figsize=(10, 5.5))
    for ax, letter in zip(axes.flat, ASL_LETTERS):
        folder = ROOT / "data" / "asl-split" / "test" / letter
        first = sorted(folder.glob("*.jpg"))[0]
        img = cv2.cvtColor(cv2.imread(str(first)), cv2.COLOR_BGR2RGB)
        ax.imshow(img)
        ax.set_title(letter, fontsize=12)
        ax.axis("off")
    fig.tight_layout()
    fig.savefig(OUT / "ch4_asl_alphabet_samples.png", dpi=150)
    plt.close(fig)


def plot_wlasl_strip(gloss: str, video_idx: int = 0) -> None:
    folder = ROOT / "data" / "wlasl" / "videos" / gloss
    video = sorted(folder.glob("*.mp4"))[video_idx]

    cap = cv2.VideoCapture(str(video))
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    indices = np.linspace(0, total - 1, N_FRAMES).astype(int)

    frames = []
    for idx in indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(idx))
        ok, frame = cap.read()
        if not ok:
            continue
        frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    cap.release()

    fig, axes = plt.subplots(2, 3, figsize=(9, 6))
    for ax, frame, idx in zip(axes.flat, frames, indices):
        ax.imshow(frame)
        pct = int(round(100 * idx / max(total - 1, 1)))
        ax.set_title(f"t={pct}%", fontsize=10)
        ax.axis("off")
    fig.suptitle(f"WLASL — '{gloss}' (video {video.stem})", fontsize=12)
    fig.tight_layout()
    fig.savefig(OUT / f"ch4_wlasl_strip_{gloss}.png", dpi=150)
    plt.close(fig)


def main() -> None:
    plot_asl_grid()
    for gloss, idx in WLASL_SIGNS:
        plot_wlasl_strip(gloss, idx)

    print("Generated:")
    for p in sorted(OUT.glob("ch4_*.png")):
        print(f"  {p.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
