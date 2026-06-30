"""
Harici (Gerçek Dünya) Bağımsız Test Değerlendirmesi
===================================================
Mevcut eğitilmiş modelleri (EfficientNet + MLP) YENİDEN EĞİTMEDEN,
FARKLI kişiler/arka planlar/ışık koşullarında çekilmiş HARİCİ bir test
setinde değerlendirir:

    data/asl-independent-test/<SINIF>/*.jpg   (29 sınıf × 30 = 870 görüntü)
    (Kaynak: Kaggle 'danrasband/asl-alphabet-test' — gerçek dünya fotoğrafları)

Bu set eğitim setiyle AYNI kişi/ortam DEĞİLDİR. Dolayısıyla buradaki sonuç,
modelin işareti mi yoksa sadece eğitim ortamını mı öğrendiğini dürüstçe
gösterir (hocanın istediği "yeni input" testi).

Çalıştırma (proje kökünden):
    python src/evaluate_external.py
    python src/evaluate_external.py data/baska-klasor   # farklı bir set için
"""

import sys
import json
from pathlib import Path
from collections import defaultdict

import numpy as np
import torch
from PIL import Image
from sklearn.metrics import classification_report, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns

from model import create_model
from dataset import get_transforms, CLASSES, CLASS_TO_IDX
from train_mlp import LandmarkMLP
from extract_landmarks import (
    download_model,
    create_hand_landmarker,
    extract_landmarks_from_image,
)

# Varsayılan harici test klasörü (CLI ile değiştirilebilir)
DEFAULT_TEST_DIR = Path("data/asl-independent-test")
EFFNET_PATH = "models/best_model.pth"
MLP_PATH = "models/best_mlp_model.pth"
OUTPUT_JSON = Path("models/external_evaluation_results.json")
EFFNET_CM = Path("thesis/figures/ch5_cm_cnn_external.png")
MLP_CM = Path("thesis/figures/ch5_cm_mlp_external.png")


def list_images(test_dir):
    """
    <SINIF>/*.jpg yapısındaki tüm görüntüleri (yol, sınıf_adı, sınıf_idx) döndür.
    """
    samples = []
    for cls in CLASSES:
        cls_dir = test_dir / cls
        if not cls_dir.exists():
            continue
        for img_path in sorted(cls_dir.glob("*.jpg")):
            samples.append((img_path, cls, CLASS_TO_IDX[cls]))
    return samples


def plot_cm(y_true, y_pred, labels_idx, label_names, title, save_path):
    """Confusion matrix çiz ve kaydet (yüzde normalize)."""
    cm = confusion_matrix(y_true, y_pred, labels=labels_idx)
    with np.errstate(all="ignore"):
        cm_norm = cm.astype("float") / cm.sum(axis=1)[:, np.newaxis] * 100
        cm_norm = np.nan_to_num(cm_norm)

    plt.figure(figsize=(16, 14))
    sns.heatmap(cm_norm, annot=True, fmt=".0f", cmap="Blues",
                xticklabels=label_names, yticklabels=label_names,
                annot_kws={"size": 7})
    plt.xlabel("Predicted")
    plt.ylabel("True")
    plt.title(title)
    plt.xticks(rotation=45, ha="right")
    plt.yticks(rotation=0)
    plt.tight_layout()
    plt.savefig(save_path, dpi=150)
    plt.close()
    print(f"Confusion matrix kaydedildi: {save_path}")


def per_class_accuracy(correct_by_cls, total_by_cls):
    """Sınıf başına doğruluk tablosu yazdır."""
    print(f"\n{'Sınıf':<10}{'Doğru':<8}{'Toplam':<8}{'Acc'}")
    print("-" * 34)
    for cls in CLASSES:
        tot = total_by_cls.get(cls, 0)
        if tot == 0:
            continue
        cor = correct_by_cls.get(cls, 0)
        print(f"{cls:<10}{cor:<8}{tot:<8}{100.0*cor/tot:.1f}%")


def evaluate_efficientnet(samples, device):
    print("\n" + "=" * 64)
    print("1) EfficientNet-B0 — Harici Bağımsız Test")
    print("=" * 64)

    model = create_model(num_classes=29, pretrained=False, freeze_backbone=False)
    ckpt = torch.load(EFFNET_PATH, map_location=device)
    state = ckpt.get("model_state_dict", ckpt) if isinstance(ckpt, dict) else ckpt
    model.load_state_dict(state)
    model = model.to(device).eval()

    transform = get_transforms("test", img_size=224)

    y_true, y_pred = [], []
    correct_by_cls = defaultdict(int)
    total_by_cls = defaultdict(int)

    with torch.no_grad():
        for img_path, true_name, true_idx in samples:
            image = Image.open(img_path).convert("RGB")
            x = transform(image).unsqueeze(0).to(device)
            pred_idx = int(torch.argmax(model(x), dim=1).item())
            y_true.append(true_idx)
            y_pred.append(pred_idx)
            total_by_cls[true_name] += 1
            if pred_idx == true_idx:
                correct_by_cls[true_name] += 1

    acc = 100.0 * sum(correct_by_cls.values()) / len(samples)
    per_class_accuracy(correct_by_cls, total_by_cls)
    print(f"\n>> EfficientNet harici test accuracy: {acc:.2f}%  "
          f"({sum(correct_by_cls.values())}/{len(samples)})")

    present = sorted(set(y_true) | set(y_pred))
    plot_cm(y_true, y_pred, present, [CLASSES[i] for i in present],
            "Confusion Matrix (%) — EfficientNet-B0, external cross-dataset test", EFFNET_CM)

    return {
        "accuracy": round(acc, 2),
        "correct": sum(correct_by_cls.values()),
        "total": len(samples),
        "per_class": {c: {"correct": correct_by_cls[c], "total": total_by_cls[c]}
                      for c in CLASSES if total_by_cls[c] > 0},
    }


def evaluate_mlp(samples, device):
    print("\n" + "=" * 64)
    print("2) Landmark MLP — Harici Bağımsız Test")
    print("=" * 64)

    ckpt = torch.load(MLP_PATH, map_location=device)
    hidden = ckpt.get("hidden_sizes", [256, 128, 64])
    model = LandmarkMLP(input_size=63, hidden_sizes=hidden, num_classes=29)
    model.load_state_dict(ckpt["model_state_dict"])
    model = model.to(device).eval()

    landmarker = create_hand_landmarker(download_model())

    # 'nothing' tek elsiz sınıftır: doğru sonuç = el bulunmaması.
    # Diğer tüm sınıflar (harfler + del + space) el içerir; el bulunamazsa
    # bu gerçek bir tespit hatasıdır. Bu yüzden ikisini ayrı sayıyoruz.
    NOTHING = "nothing"

    y_true_det, y_pred_det = [], []      # sadece el içeren sınıflardan, el tespit edilenler
    correct_by_cls = defaultdict(int)
    total_by_cls = defaultdict(int)       # tüm görüntüler
    detected_by_cls = defaultdict(int)    # el tespit edilenler (sadece el içeren sınıflar)
    no_hand_total = 0                     # el OLMASI gerekirken bulunamadı (gerçek hata)

    # 'nothing' sınıfı için ayrı sayaçlar
    nothing_total = 0
    nothing_correct = 0                   # doğru: el bulunmadı
    nothing_falsepos = 0                  # yanlış: elsiz karede el "bulundu"

    with torch.no_grad():
        for img_path, true_name, true_idx in samples:
            total_by_cls[true_name] += 1
            landmarks = extract_landmarks_from_image(img_path, landmarker)

            if true_name == NOTHING:
                nothing_total += 1
                if landmarks is None:
                    nothing_correct += 1        # el yok -> doğru
                else:
                    nothing_falsepos += 1       # hayalet el -> yanlış
                continue

            # El içermesi gereken sınıf (harf / del / space)
            if landmarks is None:
                no_hand_total += 1              # el bulunamadı = tespit hatası
                continue
            detected_by_cls[true_name] += 1
            x = torch.FloatTensor(landmarks).unsqueeze(0).to(device)
            pred_idx = int(torch.argmax(model(x), dim=1).item())
            y_true_det.append(true_idx)
            y_pred_det.append(pred_idx)
            if pred_idx == true_idx:
                correct_by_cls[true_name] += 1

    landmarker.close()

    # El içeren sınıflar üzerinden metrikler (nothing hariç)
    hand_total = len(samples) - nothing_total
    detected = sum(detected_by_cls.values())
    correct = sum(correct_by_cls.values())
    acc_all = 100.0 * correct / hand_total if hand_total else 0.0   # el-içeren tüm görüntüler
    acc_det = 100.0 * correct / detected if detected else 0.0       # sadece el tespit edilenler
    det_rate = 100.0 * detected / hand_total if hand_total else 0.0 # tespit oranı (nothing hariç)

    # Sınıf başına: doğru / tespit / toplam
    print(f"\n{'Sınıf':<10}{'Doğru':<8}{'ElVar':<8}{'Toplam':<8}{'Acc(elvar)'}")
    print("-" * 46)
    for cls in CLASSES:
        tot = total_by_cls.get(cls, 0)
        if tot == 0 or cls == NOTHING:
            continue
        det = detected_by_cls.get(cls, 0)
        cor = correct_by_cls.get(cls, 0)
        acc_c = f"{100.0*cor/det:.1f}%" if det else "-"
        print(f"{cls:<10}{cor:<8}{det:<8}{tot:<8}{acc_c}")

    print(f"\nMediaPipe el tespit oranı (el içeren sınıflar): {det_rate:.1f}% ({detected}/{hand_total})")
    print(f">> MLP accuracy (el içeren tüm {hand_total} görüntü):        {acc_all:.2f}%  ({correct}/{hand_total})")
    print(f">> MLP accuracy (sadece el tespit edilen {detected}):  {acc_det:.2f}%  ({correct}/{detected})")
    if nothing_total:
        print(f"\n'nothing' sınıfı (el yok = doğru): {nothing_correct}/{nothing_total} doğru "
              f"({100.0*nothing_correct/nothing_total:.1f}%), {nothing_falsepos} hayalet-el tespiti")

    if y_true_det:
        present = sorted(set(y_true_det) | set(y_pred_det))
        plot_cm(y_true_det, y_pred_det, present, [CLASSES[i] for i in present],
                "Confusion Matrix (%) — Landmark MLP, external cross-dataset test (detected-hand subset)", MLP_CM)

    return {
        "accuracy_all_handclasses": round(acc_all, 2),
        "accuracy_detected": round(acc_det, 2),
        "hand_detection_rate": round(det_rate, 2),
        "hand_classes_total": hand_total,
        "detected": detected,
        "correct": correct,
        "no_hand_failures": no_hand_total,
        "nothing": {"total": nothing_total, "correct": nothing_correct,
                    "false_positive": nothing_falsepos},
        "per_class": {c: {"correct": correct_by_cls[c],
                          "detected": detected_by_cls[c],
                          "total": total_by_cls[c]}
                      for c in CLASSES if total_by_cls[c] > 0 and c != NOTHING},
    }


def main():
    test_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_TEST_DIR
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")
    print(f"Test klasörü: {test_dir}")

    if not test_dir.exists():
        print(f"HATA: Test klasörü bulunamadı: {test_dir}")
        return

    samples = list_images(test_dir)
    if not samples:
        print("HATA: Hiç görüntü bulunamadı. Beklenen yapı: <SINIF>/*.jpg")
        return

    present_classes = sorted({s[1] for s in samples})
    print(f"Toplam görüntü: {len(samples)} | Sınıf sayısı: {len(present_classes)}")

    eff = evaluate_efficientnet(samples, device)
    mlp = evaluate_mlp(samples, device)

    print("\n" + "=" * 64)
    print("ÖZET — Harici Bağımsız Test (farklı kişi/ortam, leakage YOK)")
    print("=" * 64)
    print(f"{'Model':<32}{'Harici Test Acc'}")
    print("-" * 50)
    print(f"{'EfficientNet-B0':<32}{eff['accuracy']:.2f}%")
    print(f"{'Landmark MLP (el-içeren tümü)':<32}{mlp['accuracy_all_handclasses']:.2f}%")
    print(f"{'Landmark MLP (el tespit edilen)':<32}{mlp['accuracy_detected']:.2f}%")
    print(f"{'MediaPipe tespit oranı':<32}{mlp['hand_detection_rate']:.2f}%")
    print("\nKarşılaştırma: Eğitim/aynı-ortam test setinde ~%100 idi.")
    print("Bu setteki düşüş, o %100'ün ne kadarının ortam ezberi (leakage/")
    print("overfitting) kaynaklı olduğunu gösterir.")

    results = {
        "test_dir": str(test_dir),
        "num_images": len(samples),
        "num_classes": len(present_classes),
        "efficientnet": eff,
        "mlp": mlp,
        "device": str(device),
    }
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nSonuçlar kaydedildi: {OUTPUT_JSON}")


if __name__ == "__main__":
    main()
