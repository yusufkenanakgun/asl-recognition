"""
FAZ 6 V2 - Adım 6: Test seti değerlendirmesi (ensemble destekli).

Hem tek model (en yüksek val acc'li seed) hem 5-seed ensemble metrikleri çıkar:
  - Top-1, Top-5 accuracy (proposal FR-03 acceptance criteria)
  - Per-class F1 score
  - Confusion matrix görseli
  - Model size (MB), inference FPS

Çıktı:
  models/faz6_v2/evaluation_results.json    (özet metrikler)
  models/faz6_v2/confusion_matrix.png       (ensemble confusion)
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import torch
from sklearn.metrics import (
    classification_report, confusion_matrix, top_k_accuracy_score,
)

from train_v2 import LSTMClassifier, BATCH_SIZE


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_DIR = ROOT / "data" / "faz6_v2" / "landmarks_wlasl100"
DEFAULT_MODEL_DIR = ROOT / "models" / "faz6_v2"


# ---------------------------------------------------------------------------
# Yükleme yardımcıları
# ---------------------------------------------------------------------------
def load_model(ckpt_path: Path, device: torch.device) -> tuple[LSTMClassifier, dict]:
    chk = torch.load(ckpt_path, map_location=device)
    hp = chk["hyperparameters"]
    model = LSTMClassifier(
        input_size=hp["input_size"], hidden_size=hp["hidden_size"],
        num_layers=hp["num_layers"], num_classes=hp["num_classes"],
        dropout=hp["dropout"], bidirectional=hp["bidirectional"],
    ).to(device)
    model.load_state_dict(chk["model_state_dict"])
    model.eval()
    return model, chk


def predict_logits(model: LSTMClassifier, X: torch.Tensor, device: torch.device) -> np.ndarray:
    """Tüm X için (N, C) logits döndür."""
    all_logits = []
    with torch.no_grad():
        for i in range(0, len(X), BATCH_SIZE):
            xb = X[i:i + BATCH_SIZE].to(device)
            all_logits.append(model(xb).cpu())
    return torch.cat(all_logits, dim=0).numpy()


# ---------------------------------------------------------------------------
# Metrik hesaplamaları
# ---------------------------------------------------------------------------
def compute_metrics(logits: np.ndarray, y_true: np.ndarray, num_classes: int) -> dict:
    preds = logits.argmax(axis=1)
    probs = np.exp(logits - logits.max(axis=1, keepdims=True))
    probs = probs / probs.sum(axis=1, keepdims=True)

    top1 = float((preds == y_true).mean() * 100)
    top5 = float(top_k_accuracy_score(y_true, probs, k=5, labels=np.arange(num_classes)) * 100)

    report = classification_report(
        y_true, preds, labels=np.arange(num_classes),
        output_dict=True, zero_division=0,
    )
    return {
        "top1_acc": round(top1, 2),
        "top5_acc": round(top5, 2),
        "macro_f1": round(report["macro avg"]["f1-score"], 4),
        "weighted_f1": round(report["weighted avg"]["f1-score"], 4),
        "preds": preds, "probs": probs, "report": report,
    }


def plot_confusion(cm: np.ndarray, classes: list[str], out_path: Path, top_n: int = 25) -> None:
    """En yoğun top_n sınıf için normalize edilmiş confusion matrix."""
    sums = cm.sum(axis=1)
    top_idx = np.argsort(sums)[-top_n:]
    cm = cm[np.ix_(top_idx, top_idx)]
    classes = [classes[i] for i in top_idx]

    cm_norm = cm.astype(float) / (cm.sum(axis=1, keepdims=True) + 1e-10) * 100

    plt.figure(figsize=(14, 12))
    sns.heatmap(
        cm_norm, annot=True, fmt=".0f", cmap="Blues",
        xticklabels=classes, yticklabels=classes,
        annot_kws={"size": 7}, cbar_kws={"label": "%"},
    )
    plt.xlabel("Predicted")
    plt.ylabel("True")
    plt.title(f"Confusion Matrix — Top {top_n} classes (% normalised)")
    plt.xticks(rotation=45, ha="right")
    plt.yticks(rotation=0)
    plt.tight_layout()
    plt.savefig(out_path, dpi=120)
    plt.close()


# ---------------------------------------------------------------------------
# Ana akış
# ---------------------------------------------------------------------------
def main(ckpt_dir: Path = DEFAULT_MODEL_DIR, data_dir: Path = DEFAULT_DATA_DIR) -> None:
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")
    if device.type == "cuda":
        print(f"GPU: {torch.cuda.get_device_name(0)}")

    print(f"Ckpt klasörü: {ckpt_dir}")
    print(f"Veri klasörü: {data_dir}")

    # Veri yükle
    print("\nTest verisi yükleniyor...")
    X_test = np.load(data_dir / "X_test.npy")
    y_test = np.load(data_dir / "y_test.npy")
    with (data_dir / "gloss_to_idx.json").open() as f:
        gloss_to_idx = json.load(f)
    idx_to_gloss = {v: k for k, v in gloss_to_idx.items()}
    classes = [idx_to_gloss[i] for i in range(len(gloss_to_idx))]
    num_classes = len(classes)

    print(f"  Test: {X_test.shape} — {num_classes} sınıf")

    X_test_t = torch.from_numpy(X_test).float()

    # Checkpoint'leri bul
    ensemble_ckpts = sorted(ckpt_dir.glob("best_lstm_seed*.pth"))
    single_ckpt = ckpt_dir / "best_lstm.pth"
    has_ensemble = len(ensemble_ckpts) >= 2

    print(f"\nBulunan modeller:")
    if has_ensemble:
        print(f"  Ensemble: {len(ensemble_ckpts)} model")
        for p in ensemble_ckpts:
            chk = torch.load(p, map_location="cpu")
            print(f"    {p.name}  val_acc={chk['best_val_acc']:.2f}%")
    if single_ckpt.exists():
        chk = torch.load(single_ckpt, map_location="cpu")
        print(f"  Tek model: {single_ckpt.name}  val_acc={chk['best_val_acc']:.2f}%")

    # ---------------------------------------------------------------
    # Değerlendir
    # ---------------------------------------------------------------
    results = {"num_classes": num_classes, "test_size": len(X_test)}

    # 1) Ensemble (varsa)
    if has_ensemble:
        print("\n--- Ensemble değerlendirmesi ---")
        accum_logits = None
        individual_results = []
        for p in ensemble_ckpts:
            model, _ = load_model(p, device)
            logits = predict_logits(model, X_test_t, device)
            ind_metrics = compute_metrics(logits, y_test, num_classes)
            individual_results.append({
                "ckpt": p.name,
                "top1": ind_metrics["top1_acc"],
                "top5": ind_metrics["top5_acc"],
                "macro_f1": ind_metrics["macro_f1"],
            })
            print(f"  {p.name}: top1={ind_metrics['top1_acc']:.2f}%  "
                  f"top5={ind_metrics['top5_acc']:.2f}%  "
                  f"macro F1={ind_metrics['macro_f1']:.3f}")
            accum_logits = logits if accum_logits is None else accum_logits + logits

        ensemble_logits = accum_logits / len(ensemble_ckpts)
        ens_m = compute_metrics(ensemble_logits, y_test, num_classes)

        print(f"\n  🏆 ENSEMBLE: top1={ens_m['top1_acc']:.2f}%  "
              f"top5={ens_m['top5_acc']:.2f}%  "
              f"macro F1={ens_m['macro_f1']:.3f}")

        # Confusion matrix (ensemble)
        cm = confusion_matrix(y_test, ens_m["preds"], labels=np.arange(num_classes))
        plot_confusion(cm, classes, ckpt_dir / "confusion_matrix.png", top_n=25)
        print(f"  Confusion matrix: {ckpt_dir / 'confusion_matrix.png'}")

        # En çok karıştırılan sınıflar
        cm_nodiag = cm.copy()
        np.fill_diagonal(cm_nodiag, 0)
        top_conf = []
        for i in range(num_classes):
            for j in range(num_classes):
                if cm_nodiag[i, j] > 0:
                    top_conf.append((classes[i], classes[j], int(cm_nodiag[i, j])))
        top_conf.sort(key=lambda x: -x[2])
        print(f"\n  En çok karıştırılan 10 çift (gerçek → tahmin):")
        for t, p_, n in top_conf[:10]:
            print(f"    {t:<15} → {p_:<15} {n}")

        # Per-class F1 — en kötü 5
        cls_f1 = sorted(
            [(c, ens_m["report"][c]["f1-score"], int(ens_m["report"][c]["support"]))
             for c in classes if c in ens_m["report"]],
            key=lambda x: x[1]
        )
        print(f"\n  En kötü 5 sınıf (F1):")
        for c, f1, supp in cls_f1[:5]:
            print(f"    {c:<15} F1={f1:.3f}  test örneği={supp}")
        print(f"  En iyi 5 sınıf (F1):")
        for c, f1, supp in cls_f1[-5:]:
            print(f"    {c:<15} F1={f1:.3f}  test örneği={supp}")

        results["ensemble"] = {
            "num_models": len(ensemble_ckpts),
            "top1_acc": ens_m["top1_acc"],
            "top5_acc": ens_m["top5_acc"],
            "macro_f1": ens_m["macro_f1"],
            "weighted_f1": ens_m["weighted_f1"],
            "individual_models": individual_results,
            "top_confusions": [{"true": t, "pred": p, "count": n} for t, p, n in top_conf[:20]],
        }

    # 2) Tek model FPS ölçümü için bir checkpoint seç (single_ckpt veya seed0)
    perf_ckpt = single_ckpt if single_ckpt.exists() else (
        ensemble_ckpts[0] if ensemble_ckpts else None
    )
    if perf_ckpt is not None:
        print(f"\n--- Tek model değerlendirmesi ({perf_ckpt.name}) ---")
        model, perf_chk = load_model(perf_ckpt, device)
        logits = predict_logits(model, X_test_t, device)
        single_m = compute_metrics(logits, y_test, num_classes)
        print(f"  top1={single_m['top1_acc']:.2f}%  top5={single_m['top5_acc']:.2f}%  "
              f"macro F1={single_m['macro_f1']:.3f}")
        size_mb = perf_ckpt.stat().st_size / (1024 * 1024)

        # FPS ölçümü (ckpt'in kendi hyperparametreleriyle)
        hp = perf_chk["hyperparameters"]
        model_perf = LSTMClassifier(
            input_size=hp["input_size"], hidden_size=hp["hidden_size"],
            num_layers=hp["num_layers"], num_classes=num_classes,
            dropout=hp["dropout"], bidirectional=hp["bidirectional"],
        ).to(device).eval()
        x_one = torch.randn(1, 32, hp["input_size"], device=device)
        # warmup
        with torch.no_grad():
            for _ in range(20):
                _ = model_perf(x_one)
        if device.type == "cuda":
            torch.cuda.synchronize()
        t0 = time.time()
        N = 500
        with torch.no_grad():
            for _ in range(N):
                _ = model_perf(x_one)
        if device.type == "cuda":
            torch.cuda.synchronize()
        elapsed = time.time() - t0
        fps = N / elapsed
        ms = 1000.0 / fps

        results["single"] = {
            "top1_acc": single_m["top1_acc"],
            "top5_acc": single_m["top5_acc"],
            "macro_f1": single_m["macro_f1"],
            "weighted_f1": single_m["weighted_f1"],
            "model_size_mb": round(size_mb, 3),
            "inference_fps": round(fps, 1),
            "inference_ms_per_sample": round(ms, 3),
        }
        print(f"  Model boyutu: {size_mb:.2f} MB")
        print(f"  Inference: {fps:.0f} FPS ({ms:.2f} ms/sample) on {device}")

    # Kaydet
    out = ckpt_dir / "evaluation_results.json"
    with out.open("w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 70)
    print("DEĞERLENDİRME TAMAMLANDI")
    print("=" * 70)
    print(f"Özet → {out}")
    if has_ensemble:
        print(f"ENSEMBLE Top-1: {results['ensemble']['top1_acc']:.2f}% "
              f"(proposal acceptance ≥%40, hedef ≥%60)")


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--ckpt-dir", type=str, default=None,
                   help="Checkpoint klasörü (varsayılan: models/faz6_v2)")
    p.add_argument("--data-dir", type=str, default=None,
                   help="Test data klasörü (varsayılan: data/faz6_v2/landmarks_wlasl100)")
    args = p.parse_args()
    ckpt_dir = Path(args.ckpt_dir) if args.ckpt_dir else DEFAULT_MODEL_DIR
    data_dir = Path(args.data_dir) if args.data_dir else DEFAULT_DATA_DIR
    main(ckpt_dir=ckpt_dir, data_dir=data_dir)
