"""
FAZ 6: LSTM Model Evaluation
Test seti üzerinde değerlendirme
"""

import torch
import numpy as np
import json
from pathlib import Path
from sklearn.metrics import classification_report, confusion_matrix, top_k_accuracy_score
import matplotlib.pyplot as plt
import seaborn as sns

from train_lstm import LSTMClassifier


def load_model(model_path, num_classes, device):
    """Eğitilmiş LSTM modelini yükle"""
    checkpoint = torch.load(model_path, map_location=device)

    model = LSTMClassifier(
        input_size=63,
        hidden_size=128,
        num_layers=2,
        num_classes=num_classes,
        dropout=0.3,
        bidirectional=True
    )
    model.load_state_dict(checkpoint['model_state_dict'])
    model = model.to(device)
    model.eval()

    print(f"Checkpoint yüklendi (Val Acc: {checkpoint.get('best_val_acc', 'N/A'):.2f}%)")
    return model


def evaluate(model, X_test, y_test, device, batch_size=32):
    """Model değerlendirmesi"""
    model.eval()
    all_preds = []
    all_probs = []

    X_tensor = torch.FloatTensor(X_test)

    with torch.no_grad():
        for i in range(0, len(X_tensor), batch_size):
            batch = X_tensor[i:i+batch_size].to(device)
            outputs = model(batch)
            probs = torch.softmax(outputs, dim=1)

            _, preds = torch.max(outputs, 1)
            all_preds.extend(preds.cpu().numpy())
            all_probs.extend(probs.cpu().numpy())

    return np.array(all_preds), np.array(all_probs)


def plot_confusion_matrix(cm, classes, save_path, top_n=20):
    """En çok örneği olan sınıflar için confusion matrix"""
    # Çok fazla sınıf varsa sadece top_n göster
    if len(classes) > top_n:
        # En çok örneği olan sınıfları bul
        class_counts = cm.sum(axis=1)
        top_indices = np.argsort(class_counts)[-top_n:]
        cm = cm[np.ix_(top_indices, top_indices)]
        classes = [classes[i] for i in top_indices]

    plt.figure(figsize=(14, 12))

    cm_normalized = cm.astype('float') / (cm.sum(axis=1)[:, np.newaxis] + 1e-10) * 100

    sns.heatmap(cm_normalized, annot=True, fmt='.0f', cmap='Blues',
                xticklabels=classes, yticklabels=classes,
                annot_kws={'size': 8})

    plt.xlabel('Tahmin Edilen', fontsize=12)
    plt.ylabel('Gerçek', fontsize=12)
    plt.title(f'Confusion Matrix (%) - LSTM Model - Top {len(classes)} Sınıf', fontsize=14)
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
    model_path = "models/best_lstm_model.pth"
    data_dir = Path("data/wlasl/landmarks")
    output_dir = Path("models")

    # Device
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")
    if device.type == 'cuda':
        print(f"GPU: {torch.cuda.get_device_name(0)}")

    # Veri yükle
    print("\nTest verisi yükleniyor...")
    X_test = np.load(data_dir / "X_test.npy")
    y_test = np.load(data_dir / "y_test.npy")

    with open(data_dir / "gloss_to_idx.json", "r") as f:
        gloss_to_idx = json.load(f)

    idx_to_gloss = {v: k for k, v in gloss_to_idx.items()}
    classes = [idx_to_gloss[i] for i in range(len(gloss_to_idx))]
    num_classes = len(classes)

    print(f"Test örnek sayısı: {len(X_test)}")
    print(f"Sınıf sayısı: {num_classes}")

    # Model yükle
    print(f"\nModel yükleniyor: {model_path}")
    model = load_model(model_path, num_classes, device)

    # Model boyutu
    model_size = get_model_size(model_path)
    print(f"Model boyutu: {model_size:.2f} MB")

    # Değerlendirme
    print("\n" + "="*60)
    print("LSTM MODEL - TEST SETİ DEĞERLENDİRMESİ")
    print("="*60)

    preds, probs = evaluate(model, X_test, y_test, device)

    # Top-1 Accuracy
    top1_acc = (preds == y_test).mean() * 100
    print(f"\nTop-1 Accuracy: {top1_acc:.2f}%")

    # Top-5 Accuracy
    top5_acc = top_k_accuracy_score(y_test, probs, k=5) * 100
    print(f"Top-5 Accuracy: {top5_acc:.2f}%")

    # Classification Report (özet)
    print("\n" + "-"*60)
    print("CLASSIFICATION REPORT (Özet)")
    print("-"*60)

    report_dict = classification_report(y_test, preds, target_names=classes,
                                         digits=4, output_dict=True, zero_division=0)

    # Macro/weighted averages
    print(f"Macro F1-score: {report_dict['macro avg']['f1-score']:.4f}")
    print(f"Weighted F1-score: {report_dict['weighted avg']['f1-score']:.4f}")

    # En iyi ve en kötü sınıflar
    class_f1 = [(cls, report_dict[cls]['f1-score']) for cls in classes if cls in report_dict]
    class_f1.sort(key=lambda x: x[1], reverse=True)

    print("\nEn iyi 5 sınıf (F1-score):")
    for cls, f1 in class_f1[:5]:
        print(f"  {cls}: {f1:.4f}")

    print("\nEn kötü 5 sınıf (F1-score):")
    for cls, f1 in class_f1[-5:]:
        print(f"  {cls}: {f1:.4f}")

    # Confusion Matrix
    print("\nConfusion matrix oluşturuluyor...")
    cm = confusion_matrix(y_test, preds)
    plot_confusion_matrix(cm, classes, output_dir / "lstm_confusion_matrix.png")

    # En çok karıştırılan sınıflar
    print("\n" + "-"*60)
    print("EN ÇOK KARIŞTIRILAN SINIFLAR")
    print("-"*60)

    cm_copy = cm.copy()
    np.fill_diagonal(cm_copy, 0)
    top_confusions = []
    for i in range(len(classes)):
        for j in range(len(classes)):
            if cm_copy[i, j] > 0:
                top_confusions.append((classes[i], classes[j], cm_copy[i, j]))

    top_confusions.sort(key=lambda x: x[2], reverse=True)

    print(f"{'Gerçek':<15} {'Tahmin':<15} {'Sayı':<10}")
    print("-" * 40)
    for true_cls, pred_cls, count in top_confusions[:10]:
        print(f"{true_cls:<15} {pred_cls:<15} {count:<10}")

    # Sonuçları kaydet
    results = {
        "model": "LSTM Bidirectional",
        "model_path": model_path,
        "model_size_mb": round(model_size, 2),
        "num_classes": num_classes,
        "test_samples": len(X_test),
        "top1_accuracy": round(top1_acc, 2),
        "top5_accuracy": round(top5_acc, 2),
        "macro_f1": round(report_dict['macro avg']['f1-score'], 4),
        "weighted_f1": round(report_dict['weighted avg']['f1-score'], 4),
        "device": str(device)
    }

    results_path = output_dir / "lstm_evaluation_results.json"
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nSonuçlar kaydedildi: {results_path}")

    print("\n" + "="*60)
    print("LSTM DEĞERLENDİRME TAMAMLANDI!")
    print("="*60)


if __name__ == "__main__":
    main()
