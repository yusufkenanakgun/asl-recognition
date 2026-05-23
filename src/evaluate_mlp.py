"""
FAZ 4: MLP Model Evaluation
Test seti üzerinde değerlendirme: Confusion Matrix, F1-Score, FPS
"""

import torch
import numpy as np
import time
import json
from pathlib import Path
from sklearn.metrics import classification_report, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns

from train_mlp import LandmarkMLP, CLASSES


def load_model(model_path, device):
    """Eğitilmiş MLP modelini yükle"""
    checkpoint = torch.load(model_path, map_location=device)

    hidden_sizes = checkpoint.get('hidden_sizes', [256, 128, 64])
    model = LandmarkMLP(input_size=63, hidden_sizes=hidden_sizes, num_classes=29)
    model.load_state_dict(checkpoint['model_state_dict'])
    model = model.to(device)
    model.eval()

    print(f"Checkpoint yüklendi (Val Acc: {checkpoint.get('best_val_acc', 'N/A'):.2f}%)")
    return model


def evaluate(model, X_test, y_test, device, batch_size=256):
    """Model değerlendirmesi"""
    model.eval()
    all_preds = []

    X_tensor = torch.FloatTensor(X_test).to(device)

    with torch.no_grad():
        for i in range(0, len(X_tensor), batch_size):
            batch = X_tensor[i:i+batch_size]
            outputs = model(batch)
            _, preds = torch.max(outputs, 1)
            all_preds.extend(preds.cpu().numpy())

    return np.array(all_preds)


def measure_fps(model, X_test, device, num_samples=5000):
    """Inference hızını ölç (FPS)"""
    model.eval()
    X_tensor = torch.FloatTensor(X_test[:num_samples]).to(device)

    # Warmup
    with torch.no_grad():
        for _ in range(100):
            _ = model(X_tensor[:100])

    # Gerçek ölçüm
    torch.cuda.synchronize() if device.type == 'cuda' else None
    start_time = time.perf_counter()

    with torch.no_grad():
        for i in range(0, len(X_tensor), 64):
            _ = model(X_tensor[i:i+64])

    torch.cuda.synchronize() if device.type == 'cuda' else None
    elapsed = time.perf_counter() - start_time

    fps = len(X_tensor) / elapsed
    return fps, len(X_tensor), elapsed


def plot_confusion_matrix(cm, classes, save_path):
    """Confusion matrix görselleştir"""
    plt.figure(figsize=(16, 14))

    cm_normalized = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis] * 100

    sns.heatmap(cm_normalized, annot=True, fmt='.1f', cmap='Blues',
                xticklabels=classes, yticklabels=classes,
                annot_kws={'size': 8})

    plt.xlabel('Predicted', fontsize=12)
    plt.ylabel('True', fontsize=12)
    plt.title('Confusion Matrix (%) — Landmark MLP, test set', fontsize=14)
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
    model_path = "models/best_mlp_model.pth"
    data_dir = Path("data/landmarks")
    output_dir = Path("models")

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
    print(f"Model boyutu: {model_size:.4f} MB")

    # Test verisi yükle
    print("\nTest verisi yükleniyor...")
    X_test = np.load(data_dir / "X_test.npy")
    y_test = np.load(data_dir / "y_test.npy")
    print(f"Test örnek sayısı: {len(X_test)}")

    # Değerlendirme
    print("\n" + "="*60)
    print("MLP MODEL - TEST SETİ DEĞERLENDİRMESİ")
    print("="*60)

    preds = evaluate(model, X_test, y_test, device)

    # Accuracy
    accuracy = (preds == y_test).mean() * 100
    print(f"\nTest Accuracy: {accuracy:.2f}%")

    # Mevcut sınıfları bul (nothing sınıfında el tespit edilememiş olabilir)
    unique_labels = np.unique(np.concatenate([y_test, preds]))
    present_classes = [CLASSES[i] for i in unique_labels]

    # Eksik sınıfları göster (MediaPipe tespit edemedi)
    missing_classes = [CLASSES[i] for i in range(len(CLASSES)) if i not in unique_labels]
    if missing_classes:
        print(f"Eksik sınıflar (el tespit edilemedi): {missing_classes}")

    # Classification Report
    print("\n" + "-"*60)
    print("CLASSIFICATION REPORT (Per-Class Metrics)")
    print("-"*60)

    report = classification_report(y_test, preds, labels=unique_labels,
                                   target_names=present_classes, digits=4)
    print(report)

    report_dict = classification_report(y_test, preds, labels=unique_labels,
                                         target_names=present_classes,
                                         digits=4, output_dict=True)

    # Confusion Matrix
    print("\nConfusion matrix oluşturuluyor...")
    cm = confusion_matrix(y_test, preds, labels=unique_labels)
    plot_confusion_matrix(cm, present_classes, output_dir / "mlp_confusion_matrix.png")

    # En çok karıştırılan sınıflar
    print("\n" + "-"*60)
    print("EN ÇOK KARIŞTIRILAN SINIFLAR")
    print("-"*60)

    cm_copy = cm.copy()
    np.fill_diagonal(cm_copy, 0)
    top_confusions = []
    for i in range(len(present_classes)):
        for j in range(len(present_classes)):
            if cm_copy[i, j] > 0:
                top_confusions.append((present_classes[i], present_classes[j], cm_copy[i, j]))

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

    fps, total_samples, elapsed = measure_fps(model, X_test, device)
    print(f"FPS: {fps:.1f}")
    print(f"Ölçüm: {total_samples} örnek / {elapsed:.4f} saniye")
    print(f"Örnek başına: {1000000/fps:.2f} µs ({1000/fps:.4f} ms)")

    # Sonuçları kaydet
    results = {
        "model": "MLP Landmark-Based",
        "model_path": model_path,
        "model_size_mb": round(model_size, 4),
        "test_accuracy": round(accuracy, 2),
        "test_samples": len(X_test),
        "fps": round(fps, 1),
        "ms_per_sample": round(1000/fps, 4),
        "per_class_metrics": report_dict,
        "device": str(device),
        "gpu": torch.cuda.get_device_name(0) if device.type == 'cuda' else None
    }

    results_path = output_dir / "mlp_evaluation_results.json"
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nSonuçlar kaydedildi: {results_path}")

    print("\n" + "="*60)
    print("MLP DEĞERLENDİRME TAMAMLANDI!")
    print("="*60)


if __name__ == "__main__":
    main()
