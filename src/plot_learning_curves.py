"""Üç model için learning curve grafiklerini çıkar.

Çıktı:
  thesis/figures/ch5_lc_cnn.png    EfficientNet-B0 train/val loss + acc
  thesis/figures/ch5_lc_mlp.png    Landmark MLP train/val loss + acc
  thesis/figures/ch5_lc_lstm.png   5-seed BiLSTM overlay + ortalama
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "thesis" / "figures"
OUT.mkdir(parents=True, exist_ok=True)


def plot_single(history_path: Path, out_path: Path, title: str) -> None:
    h = json.loads(history_path.read_text(encoding="utf-8"))
    epochs = np.arange(1, len(h["train_loss"]) + 1)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4))

    ax1.plot(epochs, h["train_loss"], label="train", color="black", linewidth=1.4)
    ax1.plot(epochs, h["val_loss"],   label="val",   color="black",
             linewidth=1.4, linestyle="--")
    ax1.set_xlabel("Epoch")
    ax1.set_ylabel("Loss")
    ax1.legend()
    ax1.grid(alpha=0.3)

    ax2.plot(epochs, h["train_acc"], label="train", color="black", linewidth=1.4)
    ax2.plot(epochs, h["val_acc"],   label="val",   color="black",
             linewidth=1.4, linestyle="--")
    ax2.set_xlabel("Epoch")
    ax2.set_ylabel("Accuracy (%)")
    ax2.legend()
    ax2.grid(alpha=0.3)

    fig.suptitle(title)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def plot_lstm_seeds(out_path: Path) -> None:
    """5 seed'i tek panelde overlay + bold ortalama eğrisi.

    Seed'ler early stopping nedeniyle farklı uzunluklarda olabilir;
    her seed kendi epoch aralığında çizilir, ortalama overlapping
    aralık (min uzunluk) üzerinden hesaplanır.
    """
    paths = [ROOT / f"models/faz6_v2/training_history_seed{i}.json" for i in range(5)]
    histories = [json.loads(p.read_text(encoding="utf-8")) for p in paths]
    min_len = min(len(h["train_loss"]) for h in histories)
    epochs_mean = np.arange(1, min_len + 1)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4))

    for h in histories:
        e = np.arange(1, len(h["train_loss"]) + 1)
        ax1.plot(e, h["train_loss"], color="gray",  linewidth=0.8, alpha=0.5)
        ax1.plot(e, h["val_loss"],   color="black", linewidth=0.8, alpha=0.4,
                 linestyle="--")
        ax2.plot(e, h["train_acc"],  color="gray",  linewidth=0.8, alpha=0.5)
        ax2.plot(e, h["val_acc"],    color="black", linewidth=0.8, alpha=0.4,
                 linestyle="--")

    mean_tl = np.mean([h["train_loss"][:min_len] for h in histories], axis=0)
    mean_vl = np.mean([h["val_loss"][:min_len]   for h in histories], axis=0)
    mean_ta = np.mean([h["train_acc"][:min_len]  for h in histories], axis=0)
    mean_va = np.mean([h["val_acc"][:min_len]    for h in histories], axis=0)

    ax1.plot(epochs_mean, mean_tl, color="black", linewidth=2, label="train mean")
    ax1.plot(epochs_mean, mean_vl, color="black", linewidth=2, linestyle="--",
             label="val mean")
    ax2.plot(epochs_mean, mean_ta, color="black", linewidth=2, label="train mean")
    ax2.plot(epochs_mean, mean_va, color="black", linewidth=2, linestyle="--",
             label="val mean")

    ax1.set_xlabel("Epoch")
    ax1.set_ylabel("Loss")
    ax1.legend()
    ax1.grid(alpha=0.3)
    ax2.set_xlabel("Epoch")
    ax2.set_ylabel("Accuracy (%)")
    ax2.legend()
    ax2.grid(alpha=0.3)

    fig.suptitle("BiLSTM (5 seeds, mean overlaid)")
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def main() -> None:
    plot_single(
        ROOT / "models" / "training_history.json",
        OUT / "ch5_lc_cnn.png",
        "EfficientNet-B0 (letters)",
    )
    plot_single(
        ROOT / "models" / "mlp_training_history.json",
        OUT / "ch5_lc_mlp.png",
        "Landmark MLP (letters)",
    )
    plot_lstm_seeds(OUT / "ch5_lc_lstm.png")

    print("Generated:")
    for p in sorted(OUT.glob("ch5_lc_*.png")):
        print(f"  {p.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
