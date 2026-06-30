"""
Bağımsız Test Değerlendirmesi (Data Leakage Kontrolü)
=====================================================
Mevcut eğitilmiş modelleri (EfficientNet + MLP) YENİDEN EĞİTMEDEN,
Kaggle'ın ORİJİNAL bağımsız test klasöründe değerlendirir:
    data/asl-alphabet/asl_alphabet_test/asl_alphabet_test/

Bu klasördeki görüntüler eğitim setinden FARKLI bir çekimdir, dolayısıyla
train/test arasında near-duplicate kare sızıntısı (data leakage) yoktur.
Amaç: tezdeki %100'lük sonucun leakage kaynaklı olup olmadığını dürüstçe
göstermek.

Çalıştırma (proje kökünden):
    python src/evaluate_independent.py
"""

import json
from pathlib import Path

import numpy as np
import torch
from PIL import Image

from model import create_model
from dataset import get_transforms, CLASSES, CLASS_TO_IDX
from train_mlp import LandmarkMLP
from extract_landmarks import (
    download_model,
    create_hand_landmarker,
    extract_landmarks_from_image,
)

# Bağımsız test klasörü (Kaggle orijinal test seti)
TEST_DIR = Path("data/asl-alphabet/asl_alphabet_test/asl_alphabet_test")
EFFNET_PATH = "models/best_model.pth"
MLP_PATH = "models/best_mlp_model.pth"
OUTPUT_PATH = Path("models/independent_evaluation_results.json")


def list_test_images():
    """
    Test klasöründeki görüntüleri (yol, gerçek_sınıf) olarak döndür.
    Dosya adı formatı: '<CLASS>_test.jpg'  ->  etiket = CLASS
    """
    samples = []
    for img_path in sorted(TEST_DIR.glob("*.jpg")):
        # 'A_test.jpg' -> 'A',  'nothing_test.jpg' -> 'nothing'
        label_name = img_path.stem.replace("_test", "")
        if label_name in CLASS_TO_IDX:
            samples.append((img_path, label_name, CLASS_TO_IDX[label_name]))
        else:
            print(f"  [atlandı] Bilinmeyen sınıf: {img_path.name}")
    return samples


def evaluate_efficientnet(samples, device):
    """EfficientNet'i bağımsız test görüntülerinde değerlendir."""
    print("\n" + "=" * 64)
    print("1) EfficientNet-B0 — Bağımsız Test")
    print("=" * 64)

    model = create_model(num_classes=29, pretrained=False, freeze_backbone=False)
    checkpoint = torch.load(EFFNET_PATH, map_location=device)
    state = checkpoint.get("model_state_dict", checkpoint) if isinstance(checkpoint, dict) else checkpoint
    model.load_state_dict(state)
    model = model.to(device).eval()

    transform = get_transforms("test", img_size=224)

    rows = []
    correct = 0
    with torch.no_grad():
        for img_path, true_name, true_idx in samples:
            image = Image.open(img_path).convert("RGB")
            x = transform(image).unsqueeze(0).to(device)
            logits = model(x)
            probs = torch.softmax(logits, dim=1)
            conf, pred_idx = torch.max(probs, dim=1)
            pred_idx = pred_idx.item()
            pred_name = CLASSES[pred_idx]
            ok = pred_idx == true_idx
            correct += int(ok)
            rows.append({
                "true": true_name,
                "pred": pred_name,
                "confidence": round(conf.item() * 100, 1),
                "correct": ok,
            })

    acc = 100.0 * correct / len(samples) if samples else 0.0
    print_table(rows)
    print(f"\n>> EfficientNet bağımsız test accuracy: {acc:.2f}%  ({correct}/{len(samples)})")
    return acc, rows


def evaluate_mlp(samples, device):
    """MLP'yi bağımsız test görüntülerinden çıkarılan landmark'larla değerlendir."""
    print("\n" + "=" * 64)
    print("2) Landmark MLP — Bağımsız Test")
    print("=" * 64)

    checkpoint = torch.load(MLP_PATH, map_location=device)
    hidden_sizes = checkpoint.get("hidden_sizes", [256, 128, 64])
    model = LandmarkMLP(input_size=63, hidden_sizes=hidden_sizes, num_classes=29)
    model.load_state_dict(checkpoint["model_state_dict"])
    model = model.to(device).eval()

    # MediaPipe Hand Landmarker
    model_path = download_model()
    landmarker = create_hand_landmarker(model_path)

    rows = []
    correct = 0
    evaluated = 0  # el tespit edilebilen görüntü sayısı
    no_hand = []

    with torch.no_grad():
        for img_path, true_name, true_idx in samples:
            landmarks = extract_landmarks_from_image(img_path, landmarker)
            if landmarks is None:
                # MediaPipe el bulamadı (örn. 'nothing' sınıfı) -> sınıflandırılamaz
                no_hand.append(true_name)
                rows.append({
                    "true": true_name,
                    "pred": "(el yok)",
                    "confidence": None,
                    "correct": False,
                })
                continue

            x = torch.FloatTensor(landmarks).unsqueeze(0).to(device)
            logits = model(x)
            probs = torch.softmax(logits, dim=1)
            conf, pred_idx = torch.max(probs, dim=1)
            pred_idx = pred_idx.item()
            pred_name = CLASSES[pred_idx]
            ok = pred_idx == true_idx
            correct += int(ok)
            evaluated += 1
            rows.append({
                "true": true_name,
                "pred": pred_name,
                "confidence": round(conf.item() * 100, 1),
                "correct": ok,
            })

    landmarker.close()

    # İki accuracy: (a) tüm görüntüler üzerinden, (b) sadece el tespit edilenler üzerinden
    acc_all = 100.0 * correct / len(samples) if samples else 0.0
    acc_detected = 100.0 * correct / evaluated if evaluated else 0.0

    print_table(rows)
    if no_hand:
        print(f"\nMediaPipe el tespit edemedi ({len(no_hand)}): {no_hand}")
    print(f"\n>> MLP accuracy (tüm {len(samples)} görüntü):        {acc_all:.2f}%  ({correct}/{len(samples)})")
    print(f">> MLP accuracy (sadece el tespit edilen {evaluated}): {acc_detected:.2f}%  ({correct}/{evaluated})")
    return acc_all, acc_detected, rows, no_hand


def print_table(rows):
    print(f"\n{'Gerçek':<10}{'Tahmin':<12}{'Güven':<10}{'Sonuç'}")
    print("-" * 40)
    for r in rows:
        conf = f"{r['confidence']:.1f}%" if r["confidence"] is not None else "-"
        mark = "OK" if r["correct"] else "X"
        print(f"{r['true']:<10}{r['pred']:<12}{conf:<10}{mark}")


def main():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")
    if not TEST_DIR.exists():
        print(f"HATA: Test klasörü bulunamadı: {TEST_DIR}")
        return

    samples = list_test_images()
    print(f"\nBağımsız test görüntüsü sayısı: {len(samples)}")
    print(f"Sınıflar: {[s[1] for s in samples]}")

    eff_acc, eff_rows = evaluate_efficientnet(samples, device)
    mlp_acc_all, mlp_acc_det, mlp_rows, no_hand = evaluate_mlp(samples, device)

    # Özet karşılaştırma
    print("\n" + "=" * 64)
    print("ÖZET — Bağımsız Test (data leakage YOK)")
    print("=" * 64)
    print(f"{'Model':<22}{'Bağımsız Test Acc':<20}")
    print("-" * 42)
    print(f"{'EfficientNet-B0':<22}{eff_acc:.2f}%")
    print(f"{'Landmark MLP (tümü)':<22}{mlp_acc_all:.2f}%")
    print(f"{'Landmark MLP (el var)':<22}{mlp_acc_det:.2f}%")
    print("\nNot: Bu set küçüktür (her sınıftan 1 görüntü) ama eğitim setinden")
    print("tamamen bağımsız bir çekimdir. Eğitim setindeki ~%100 ile buradaki")
    print("sonuç arasındaki fark, leakage'in büyüklüğünü gösterir.")

    results = {
        "test_dir": str(TEST_DIR),
        "num_images": len(samples),
        "efficientnet": {
            "independent_test_accuracy": round(eff_acc, 2),
            "per_image": eff_rows,
        },
        "mlp": {
            "independent_test_accuracy_all": round(mlp_acc_all, 2),
            "independent_test_accuracy_detected": round(mlp_acc_det, 2),
            "no_hand_detected": no_hand,
            "per_image": mlp_rows,
        },
        "device": str(device),
    }
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nSonuçlar kaydedildi: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
