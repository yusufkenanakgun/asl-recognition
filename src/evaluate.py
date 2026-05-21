"""
FAZ 3: Model Evaluation
Test seti üzerinde final değerlendirme: Confusion Matrix, F1-Score, FPS
"""

import torch
import numpy as np
import time
import json
from pathlib import Path
from sklearn.metrics import classification_report, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns

from model import create_model
from dataset import get_dataloaders, CLASSES, IDX_TO_CLASS


def load_model(model_path, device):
    """Eğitilmiş modeli yükle"""
    model = create_model(num_classes=29, pretrained=False, freeze_backbone=False)

    # Checkpoint formatında kaydedilmiş olabilir
    checkpoint = torch.load(model_path, map_location=device)

    if isinstance(checkpoint, dict) and 'model_state_dict' in checkpoint:
        model.load_state_dict(checkpoint['model_state_dict'])
        print(f"Checkpoint yüklendi (Val Acc: {checkpoint.get('best_val_acc', 'N/A')})")
    else:
        model.load_state_dict(checkpoint)

    model = model.to(device)
    model.eval()
    return model


def evaluate(model, dataloader, device):
    """Model değerlendirmesi - tüm tahminleri topla"""
    all_preds = []
    all_labels = []

    with torch.no_grad():
        for images, labels in dataloader:
            images = images.to(device)
            outputs = model(images)
            _, preds = torch.max(outputs, 1)

            all_preds.extend(preds.cpu().numpy())
            all_labels.extend(labels.numpy())

    return np.array(all_preds), np.array(all_labels)


def measure_fps(model, dataloader, device, num_batches=50):
    """Inference hızını ölç (FPS)"""
    model.eval()

    # Warmup
    images, _ = next(iter(dataloader))
    images = images.to(device)
    with torch.no_grad():
        for _ in range(10):
            _ = model(images)

    # Gerçek ölçüm
    total_images = 0
    torch.cuda.synchronize() if device.type == 'cuda' else None
    start_time = time.perf_counter()

    with torch.no_grad():
        for i, (images, _) in enumerate(dataloader):
            if i >= num_batches:
                break
            images = images.to(device)
            _ = model(images)
            total_images += images.size(0)

    torch.cuda.synchronize() if device.type == 'cuda' else None
    elapsed = time.perf_counter() - start_time

    fps = total_images / elapsed
    return fps, total_images, elapsed


def plot_confusion_matrix(cm, classes, save_path):
    """Confusion matrix görselleştir ve kaydet"""
    plt.figure(figsize=(16, 14))

    # Normalize edilmiş confusion matrix (yüzde olarak)
    cm_normalized = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis] * 100

    sns.heatmap(cm_normalized, annot=True, fmt='.1f', cmap='Blues',
                xticklabels=classes, yticklabels=classes,
                annot_kws={'size': 8})

    plt.xlabel('Tahmin Edilen', fontsize=12)
    plt.ylabel('Gerçek', fontsize=12)
    plt.title('Confusion Matrix (%) - Test Seti', fontsize=14)
    plt.xticks(rotation=45, ha='right')
    plt.yticks(rotation=0)
    plt.tight_layout()
    plt.savefig(save_path, dpi=150)
    plt.close()
    print(f"Confusion matrix kaydedildi: {save_path}")


def get_model_size(model_path):
    """Model dosya boyutunu MB olarak döndür"""
    size_bytes = Path(model_path).stat().st_size
    size_mb = size_bytes / (1024 * 1024)
    return size_mb


def main():
    # Ayarlar
    model_path = "models/best_model.pth"
    output_dir = Path("models")
    output_dir.mkdir(exist_ok=True)

    # Device
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")
    if device.type == 'cuda':
        print(f"GPU: {torch.cuda.get_device_name(0)}")

    # Model yükle
    print(f"\nModel yükleniyor: {model_path}")
    model = load_model(model_path, device)

    # Model boyutu
    model_size = get_model_size(model_path)
    print(f"Model boyutu: {model_size:.2f} MB")

    # DataLoader
    print("\nDataLoader hazırlanıyor...")
    _, _, test_loader = get_dataloaders(batch_size=32, num_workers=0)
    print(f"Test görüntü sayısı: {len(test_loader.dataset)}")

    # Değerlendirme
    print("\n" + "="*60)
    print("TEST SETİ DEĞERLENDİRMESİ")
    print("="*60)

    preds, labels = evaluate(model, test_loader, device)

    # Accuracy
    accuracy = (preds == labels).mean() * 100
    print(f"\nTest Accuracy: {accuracy:.2f}%")

    # Classification Report
    print("\n" + "-"*60)
    print("CLASSIFICATION REPORT (Per-Class Metrics)")
    print("-"*60)
    report = classification_report(labels, preds, target_names=CLASSES, digits=4)
    print(report)

    # Report'u JSON olarak da kaydet
    report_dict = classification_report(labels, preds, target_names=CLASSES,
                                         digits=4, output_dict=True)

    # Confusion Matrix
    print("\nConfusion matrix oluşturuluyor...")
    cm = confusion_matrix(labels, preds)
    plot_confusion_matrix(cm, CLASSES, output_dir / "confusion_matrix.png")

    # En çok karıştırılan sınıflar
    print("\n" + "-"*60)
    print("EN ÇOK KARIŞTIRILAN SINIFLAR")
    print("-"*60)

    # Off-diagonal elementleri bul
    np.fill_diagonal(cm, 0)  # Diagonal'ı sıfırla
    top_confusions = []
    for i in range(len(CLASSES)):
        for j in range(len(CLASSES)):
            if cm[i, j] > 0:
                top_confusions.append((CLASSES[i], CLASSES[j], cm[i, j]))

    top_confusions.sort(key=lambda x: x[2], reverse=True)

    if top_confusions:
        print(f"{'Gerçek':<10} {'Tahmin':<10} {'Sayı':<10}")
        print("-" * 30)
        for true_cls, pred_cls, count in top_confusions[:10]:
            print(f"{true_cls:<10} {pred_cls:<10} {count:<10}")
    else:
        print("Hiç yanlış sınıflandırma yok!")

    # FPS Ölçümü
    print("\n" + "-"*60)
    print("INFERENCE HIZI (FPS)")
    print("-"*60)

    fps, total_imgs, elapsed = measure_fps(model, test_loader, device)
    print(f"FPS: {fps:.1f}")
    print(f"Ölçüm: {total_imgs} görüntü / {elapsed:.2f} saniye")
    print(f"Görüntü başına: {1000/fps:.2f} ms")

    # Sonuçları kaydet
    results = {
        "model": "EfficientNet-B0",
        "model_path": model_path,
        "model_size_mb": round(model_size, 2),
        "test_accuracy": round(accuracy, 2),
        "test_images": len(test_loader.dataset),
        "fps": round(fps, 1),
        "ms_per_image": round(1000/fps, 2),
        "per_class_metrics": report_dict,
        "device": str(device),
        "gpu": torch.cuda.get_device_name(0) if device.type == 'cuda' else None
    }

    results_path = output_dir / "evaluation_results.json"
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nSonuçlar kaydedildi: {results_path}")

    print("\n" + "="*60)
    print("DEĞERLENDİRME TAMAMLANDI!")
    print("="*60)


if __name__ == "__main__":
    main()
