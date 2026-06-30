"""
2-panelli confusion matrix karşılaştırması — EfficientNet-B0 harf sınıflandırıcısı:
(a) in-distribution (kusursuz köşegen, leakage ile şişmiş) vs
(b) harici çok-imzalayıcılı cross-dataset (off-diagonal çöküş).

Ayrıca harf görevinin harici doğruluklarına Wilson %95 GA hesaplar.

Çıktı: thesis/figures/ch5_cm_cnn_indomain_vs_external.png
Çalıştırma (proje kökünden): python src/plot_cm_comparison.py
"""

import math
from pathlib import Path

import numpy as np
import torch
from PIL import Image
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix

from model import create_model
from dataset import get_transforms, CLASSES, CLASS_TO_IDX

EXT_DIR = Path("data/asl-independent-test")
EFFNET = "models/best_model.pth"
OUT = Path("thesis/figures/ch5_cm_cnn_indomain_vs_external.png")


def wilson_ci(correct, n, z=1.96):
    """Wilson %95 binom güven aralığı (yüzde olarak)."""
    if n == 0:
        return (0.0, 0.0)
    p = correct / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = (z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / denom
    return (100 * (center - half), 100 * (center + half))


def main():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")

    model = create_model(num_classes=29, pretrained=False, freeze_backbone=False)
    ck = torch.load(EFFNET, map_location=device)
    model.load_state_dict(ck.get("model_state_dict", ck) if isinstance(ck, dict) else ck)
    model = model.to(device).eval()
    tf = get_transforms("test", 224)

    # Harici set tahminleri
    y_true, y_pred = [], []
    with torch.no_grad():
        for cls in CLASSES:
            d = EXT_DIR / cls
            if not d.exists():
                continue
            for p in sorted(d.glob("*.jpg")):
                x = tf(Image.open(p).convert("RGB")).unsqueeze(0).to(device)
                y_pred.append(int(torch.argmax(model(x), 1).item()))
                y_true.append(CLASS_TO_IDX[cls])

    labels = list(range(29))
    ext_cm = confusion_matrix(y_true, y_pred, labels=labels).astype(float)
    with np.errstate(all="ignore"):
        ext_norm = np.nan_to_num(ext_cm / ext_cm.sum(axis=1, keepdims=True) * 100)

    # In-distribution: raporlanan kusursuz köşegen (%100, sıfır off-diagonal)
    ind_norm = np.eye(29) * 100

    fig, axes = plt.subplots(1, 2, figsize=(30, 13))
    panels = [
        (axes[0], ind_norm,
         "(a) In-distribution (same recording) — strictly diagonal, leakage-inflated"),
        (axes[1], ext_norm,
         "(b) External cross-dataset (multi-signer) — off-diagonal collapse"),
    ]
    for ax, M, title in panels:
        sns.heatmap(M, annot=True, fmt=".0f", cmap="Blues", vmin=0, vmax=100,
                    xticklabels=CLASSES, yticklabels=CLASSES,
                    annot_kws={"size": 6}, cbar=True, ax=ax)
        ax.set_title(title, fontsize=13)
        ax.set_xlabel("Predicted")
        ax.set_ylabel("True")
        ax.set_xticklabels(CLASSES, rotation=45, ha="right", fontsize=7)
        ax.set_yticklabels(CLASSES, rotation=0, fontsize=7)
    plt.tight_layout()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(OUT, dpi=150)
    plt.close()
    print(f"Kaydedildi: {OUT}")

    # Wilson GA'lar (tezde rapor için)
    print("\n--- Wilson %95 GA ---")
    lo, hi = wilson_ci(520, 870)
    print(f"EfficientNet harici (520/870 = 59.77%): [{lo:.1f}, {hi:.1f}]")
    lo, hi = wilson_ci(714, 787)
    print(f"MLP harici el-tespit (714/787 = 90.72%): [{lo:.1f}, {hi:.1f}]")
    lo, hi = wilson_ci(714, 840)
    print(f"MLP harici el-içeren tümü (714/840 = 85.00%): [{lo:.1f}, {hi:.1f}]")
    lo, hi = wilson_ci(496, 840)
    print(f"EfficientNet harici el-içeren (496/840 = 59.05%): [{lo:.1f}, {hi:.1f}]")


if __name__ == "__main__":
    main()
