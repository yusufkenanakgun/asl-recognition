"""
FAZ 6 V2 - Adım 4: LSTM eğitimi (proposal'a sadık, V1'in bug'larını gideren sürüm).

V1'e göre değişiklikler:
- input_size 63 → 128 (2 el: sol + sağ, her biri presence_flag + 21*3)
- Dropout 0.3 → 0.5 (overfitting tut)
- Adam → AdamW, weight_decay 1e-4 → 5e-4
- Label smoothing 0.1 (handedness karışıklığını yumuşat)
- Sequence augmentation: jitter + dropout + noise + time-scale (sadece train)
- Mixup (α=0.4) + WeightedRandomSampler
- ReduceLROnPlateau + early stopping aynı
- Çoklu seed ile ensemble (--n-models N)
- Checkpoint: models/faz6_v2/best_lstm_seed{N}.pth (ensemble) veya best_lstm.pth (tek)

Kullanım:
    python src/faz6/train_v2.py               # tek model (seed 0)
    python src/faz6/train_v2.py --n-models 5  # 5-seed ensemble
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset, WeightedRandomSampler


ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data" / "faz6_v2" / "landmarks_wlasl100"
OUT_DIR = ROOT / "models" / "faz6_v2"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Hiperparametreler
INPUT_SIZE = 128
HIDDEN_SIZE = 192          # 128 → 192 (kapasite artışı)
NUM_LAYERS = 2
DROPOUT = 0.5
BIDIRECTIONAL = True
NUM_EPOCHS = 100
BATCH_SIZE = 32
LR = 1e-3
WEIGHT_DECAY = 5e-4
LABEL_SMOOTHING = 0.1
PATIENCE = 15

# Augmentation — agresif paket
TEMPORAL_JITTER = 4         # 2 → 4 (±4 frame kayma)
FRAME_DROPOUT_P = 0.15      # 0.10 → 0.15 (%15 frame sıfırla)
NOISE_STD = 0.02            # 0.01 → 0.02 (gauss gürültü σ)
TIME_SCALE_RANGE = (0.8, 1.2)  # Sequence'ı zaman ekseninde ±%20 esnet
MIXUP_ALPHA = 0.4           # Beta(α, α); 0.2 → 0.4 (daha düz blend, az dalgalı train)

# Class balance
USE_WEIGHTED_SAMPLER = True  # WeightedRandomSampler ile imbalance dengele


# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------
class LSTMClassifier(nn.Module):
    def __init__(self, input_size=128, hidden_size=128, num_layers=2,
                 num_classes=100, dropout=0.5, bidirectional=True):
        super().__init__()
        self.bidirectional = bidirectional

        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0,
            bidirectional=bidirectional,
        )

        fc_in = hidden_size * 2 if bidirectional else hidden_size
        self.fc = nn.Sequential(
            nn.Linear(fc_in, 128),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(128, num_classes),
        )

    def forward(self, x):
        _, (h_n, _) = self.lstm(x)
        if self.bidirectional:
            hidden = torch.cat((h_n[-2], h_n[-1]), dim=1)
        else:
            hidden = h_n[-1]
        return self.fc(hidden)


# ---------------------------------------------------------------------------
# Dataset + sequence augmentation
# ---------------------------------------------------------------------------
class SeqDataset(Dataset):
    """Train için augmentation uygular; val/test'te sade okur."""

    def __init__(self, X: np.ndarray, y: np.ndarray, augment: bool):
        self.X = torch.from_numpy(X).float()
        self.y = torch.from_numpy(y).long()
        self.augment = augment

    def __len__(self):
        return len(self.y)

    def __getitem__(self, idx):
        x = self.X[idx].clone()  # (T, D)
        y = self.y[idx]
        if self.augment:
            x = self._augment(x)
        return x, y

    def _augment(self, x: torch.Tensor) -> torch.Tensor:
        T, D = x.shape

        # 1) Time-scaling — sequence'ı ±%20 zaman ekseninde esnet (yavaş/hızlı işaret)
        scale = float(torch.empty(1).uniform_(TIME_SCALE_RANGE[0], TIME_SCALE_RANGE[1]).item())
        new_T = max(8, int(round(T * scale)))
        if new_T != T:
            x_interp = F.interpolate(
                x.T.unsqueeze(0),       # (1, D, T)
                size=new_T, mode="linear", align_corners=False,
            ).squeeze(0).T              # (new_T, D)
            if new_T >= T:
                x = x_interp[:T]
            else:
                pad = torch.zeros(T - new_T, D)
                x = torch.cat([x_interp, pad], dim=0)
            # Presence flag'leri (idx 0 ve 64) eski binary değerlerine yuvarla
            x[:, 0] = (x[:, 0] > 0.5).float()
            x[:, 64] = (x[:, 64] > 0.5).float()

        # 2) Temporal jitter — sequence'ı ±N frame kaydır (kırp + sıfır pad)
        shift = int(torch.randint(-TEMPORAL_JITTER, TEMPORAL_JITTER + 1, (1,)).item())
        if shift > 0:
            x = torch.cat([torch.zeros(shift, D), x[:-shift]], dim=0)
        elif shift < 0:
            x = torch.cat([x[-shift:], torch.zeros(-shift, D)], dim=0)

        # 3) Frame dropout — %p frame'i tamamen sıfırla
        mask = (torch.rand(T) < FRAME_DROPOUT_P).unsqueeze(1)  # (T, 1)
        x = x.masked_fill(mask, 0.0)

        # 4) Gauss noise — sadece koordinat boyutlarına (presence flag 0/1 kalır)
        noise = torch.randn_like(x) * NOISE_STD
        noise[:, 0] = 0    # sol presence flag
        noise[:, 64] = 0   # sağ presence flag
        x = x + noise

        return x


# ---------------------------------------------------------------------------
# Mixup
# ---------------------------------------------------------------------------
def mixup_batch(X: torch.Tensor, y: torch.Tensor, alpha: float):
    """Beta(α, α)'dan λ örnekle, batch içinde rasgele permutasyonla blend et."""
    if alpha <= 0:
        return X, y, y, 1.0
    lam = float(np.random.beta(alpha, alpha))
    idx = torch.randperm(X.size(0), device=X.device)
    X_mix = lam * X + (1.0 - lam) * X[idx]
    return X_mix, y, y[idx], lam


# ---------------------------------------------------------------------------
# Eğitim / değerlendirme döngüleri
# ---------------------------------------------------------------------------
def run_epoch(model, loader, criterion, optimizer, device, train: bool, mixup_alpha: float = 0.0):
    model.train() if train else model.eval()
    total_loss = 0.0
    correct = 0
    total = 0

    ctx = torch.enable_grad() if train else torch.no_grad()
    with ctx:
        for X_batch, y_batch in loader:
            X_batch = X_batch.to(device, non_blocking=True)
            y_batch = y_batch.to(device, non_blocking=True)

            if train and mixup_alpha > 0:
                X_in, y_a, y_b, lam = mixup_batch(X_batch, y_batch, mixup_alpha)
                outputs = model(X_in)
                loss = lam * criterion(outputs, y_a) + (1.0 - lam) * criterion(outputs, y_b)
                # Accuracy hesabı orijinal y'ye göre (mixup'sız bakış)
                outputs_eval = outputs
            else:
                outputs = model(X_batch)
                loss = criterion(outputs, y_batch)
                outputs_eval = outputs

            if train:
                optimizer.zero_grad()
                loss.backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
                optimizer.step()

            total_loss += loss.item() * X_batch.size(0)
            preds = outputs_eval.argmax(1)
            total += y_batch.size(0)
            correct += (preds == y_batch).sum().item()

    return total_loss / total, 100.0 * correct / total


# ---------------------------------------------------------------------------
# Tek model eğitim fonksiyonu
# ---------------------------------------------------------------------------
def train_one(
    seed: int,
    X_train: np.ndarray, y_train: np.ndarray,
    X_val: np.ndarray, y_val: np.ndarray,
    num_classes: int, device: torch.device,
    ckpt_path: Path, history_path: Path,
) -> float:
    """Tek bir model eğitir, best checkpoint kaydeder, best val acc döndürür."""
    # Determinism
    torch.manual_seed(seed)
    np.random.seed(seed)
    if device.type == "cuda":
        torch.cuda.manual_seed_all(seed)

    # Sampler / DataLoader
    train_dataset = SeqDataset(X_train, y_train, augment=True)
    if USE_WEIGHTED_SAMPLER:
        class_counts = np.bincount(y_train, minlength=num_classes).astype(np.float32)
        class_weights = 1.0 / np.clip(class_counts, 1, None)
        sample_weights = class_weights[y_train]
        sampler = WeightedRandomSampler(
            weights=torch.from_numpy(sample_weights).double(),
            num_samples=len(y_train), replacement=True,
        )
        train_loader = DataLoader(
            train_dataset, batch_size=BATCH_SIZE, sampler=sampler,
            num_workers=0, pin_memory=(device.type == "cuda"),
        )
    else:
        train_loader = DataLoader(
            train_dataset, batch_size=BATCH_SIZE, shuffle=True,
            num_workers=0, pin_memory=(device.type == "cuda"),
        )
    val_loader = DataLoader(
        SeqDataset(X_val, y_val, augment=False),
        batch_size=BATCH_SIZE, shuffle=False,
        num_workers=0, pin_memory=(device.type == "cuda"),
    )

    # Model
    model = LSTMClassifier(
        input_size=INPUT_SIZE, hidden_size=HIDDEN_SIZE,
        num_layers=NUM_LAYERS, num_classes=num_classes,
        dropout=DROPOUT, bidirectional=BIDIRECTIONAL,
    ).to(device)

    criterion = nn.CrossEntropyLoss(label_smoothing=LABEL_SMOOTHING)
    optimizer = optim.AdamW(model.parameters(), lr=LR, weight_decay=WEIGHT_DECAY)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode="max", factor=0.5, patience=5, min_lr=1e-5,
    )

    history = {"train_loss": [], "train_acc": [], "val_loss": [], "val_acc": [], "lr": []}
    best_val_acc = 0.0
    epochs_no_improve = 0
    t0 = time.time()

    for epoch in range(1, NUM_EPOCHS + 1):
        ep_start = time.time()
        tr_loss, tr_acc = run_epoch(
            model, train_loader, criterion, optimizer, device,
            train=True, mixup_alpha=MIXUP_ALPHA,
        )
        v_loss, v_acc = run_epoch(model, val_loader, criterion, optimizer, device, train=False)
        scheduler.step(v_acc)

        cur_lr = optimizer.param_groups[0]["lr"]
        history["train_loss"].append(tr_loss)
        history["train_acc"].append(tr_acc)
        history["val_loss"].append(v_loss)
        history["val_acc"].append(v_acc)
        history["lr"].append(cur_lr)

        improved = v_acc > best_val_acc
        marker = "  ←best" if improved else ""
        print(f"  E{epoch:3d}/{NUM_EPOCHS} | "
              f"tr {tr_loss:.3f}/{tr_acc:5.2f}% | "
              f"val {v_loss:.3f}/{v_acc:5.2f}% | "
              f"lr {cur_lr:.1e} | {time.time()-ep_start:4.1f}s{marker}")

        if improved:
            best_val_acc = v_acc
            epochs_no_improve = 0
            torch.save({
                "model_state_dict": model.state_dict(),
                "best_val_acc": best_val_acc,
                "epoch": epoch, "seed": seed,
                "hyperparameters": {
                    "input_size": INPUT_SIZE, "hidden_size": HIDDEN_SIZE,
                    "num_layers": NUM_LAYERS, "dropout": DROPOUT,
                    "bidirectional": BIDIRECTIONAL, "num_classes": num_classes,
                },
            }, ckpt_path)
        else:
            epochs_no_improve += 1
            if epochs_no_improve >= PATIENCE:
                print(f"  Early stopping — {PATIENCE} epoch gelişme yok.")
                break

    with history_path.open("w") as f:
        json.dump(history, f, indent=2)

    print(f"  → seed {seed} best val acc: {best_val_acc:.2f}% ({(time.time()-t0)/60:.1f} dk)")
    return best_val_acc


# ---------------------------------------------------------------------------
# Ensemble değerlendirmesi
# ---------------------------------------------------------------------------
def ensemble_eval(
    ckpts: list[Path],
    X_val: np.ndarray, y_val: np.ndarray,
    num_classes: int, device: torch.device,
) -> dict:
    """Birden çok modelin val logits'lerini ortalayıp ensemble accuracy hesaplar."""
    X_t = torch.from_numpy(X_val).float()
    y_t = torch.from_numpy(y_val).long().to(device)

    accum_logits = None
    individual_acc = []

    for ckpt in ckpts:
        chk = torch.load(ckpt, map_location=device)
        hp = chk["hyperparameters"]
        model = LSTMClassifier(
            input_size=hp["input_size"], hidden_size=hp["hidden_size"],
            num_layers=hp["num_layers"], num_classes=hp["num_classes"],
            dropout=hp["dropout"], bidirectional=hp["bidirectional"],
        ).to(device)
        model.load_state_dict(chk["model_state_dict"])
        model.eval()

        with torch.no_grad():
            outs = []
            for i in range(0, len(X_t), BATCH_SIZE):
                xb = X_t[i:i + BATCH_SIZE].to(device)
                outs.append(model(xb).cpu())
            logits = torch.cat(outs, dim=0)  # (N, C)

        ind = (logits.argmax(1) == y_t.cpu()).float().mean().item() * 100
        individual_acc.append(ind)
        accum_logits = logits if accum_logits is None else (accum_logits + logits)

    accum_logits = accum_logits / len(ckpts)
    ensemble_pred = accum_logits.argmax(1)
    ensemble_acc = (ensemble_pred == y_t.cpu()).float().mean().item() * 100

    return {
        "individual_val_acc": [round(a, 2) for a in individual_acc],
        "individual_mean": round(float(np.mean(individual_acc)), 2),
        "ensemble_val_acc": round(ensemble_acc, 2),
        "ensemble_gain_vs_best_single": round(ensemble_acc - max(individual_acc), 2),
        "num_models": len(ckpts),
    }


# ---------------------------------------------------------------------------
# Ana akış
# ---------------------------------------------------------------------------
def main(n_models: int = 1) -> None:
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")
    if device.type == "cuda":
        print(f"GPU: {torch.cuda.get_device_name(0)}")

    # Veri (tek sefer yükle, hepsi paylaşır)
    print("\nVeri yükleniyor...")
    X_train = np.load(DATA_DIR / "X_train.npy")
    y_train = np.load(DATA_DIR / "y_train.npy")
    X_val = np.load(DATA_DIR / "X_val.npy")
    y_val = np.load(DATA_DIR / "y_val.npy")
    with (DATA_DIR / "gloss_to_idx.json").open() as f:
        gloss_to_idx = json.load(f)
    num_classes = len(gloss_to_idx)

    print(f"  Train: {X_train.shape} | Val: {X_val.shape} | Sınıf: {num_classes}")
    class_counts = np.bincount(y_train, minlength=num_classes).astype(int)
    print(f"  Train class range: {class_counts.min()}-{class_counts.max()}, "
          f"ortalama {class_counts.mean():.1f}")

    # Eğitim — N farklı seed
    ckpts: list[Path] = []
    print("\n" + "=" * 70)
    print(f"EĞİTİM — {n_models} model (mixup α={MIXUP_ALPHA}, hidden={HIDDEN_SIZE})")
    print("=" * 70)
    start_time = time.time()

    for i in range(n_models):
        seed = i
        if n_models == 1:
            ckpt = OUT_DIR / "best_lstm.pth"
            hist = OUT_DIR / "training_history.json"
        else:
            ckpt = OUT_DIR / f"best_lstm_seed{seed}.pth"
            hist = OUT_DIR / f"training_history_seed{seed}.json"
        print(f"\n--- Model {i+1}/{n_models} (seed={seed}) → {ckpt.name} ---")
        train_one(
            seed=seed,
            X_train=X_train, y_train=y_train,
            X_val=X_val, y_val=y_val,
            num_classes=num_classes, device=device,
            ckpt_path=ckpt, history_path=hist,
        )
        ckpts.append(ckpt)

    elapsed = time.time() - start_time
    print("\n" + "=" * 70)
    print("TÜM EĞİTİMLER TAMAMLANDI")
    print("=" * 70)
    print(f"Toplam süre: {elapsed/60:.1f} dakika")

    # Ensemble değerlendirmesi
    if n_models > 1:
        print("\nEnsemble değerlendirmesi...")
        result = ensemble_eval(ckpts, X_val, y_val, num_classes, device)
        print(f"  Bireysel val acc'ler: {result['individual_val_acc']}")
        print(f"  Bireysel ortalama:    {result['individual_mean']:.2f}%")
        print(f"  ENSEMBLE val acc:     {result['ensemble_val_acc']:.2f}%")
        print(f"  Best single'a kazanç: +{result['ensemble_gain_vs_best_single']:.2f} puan")

        with (OUT_DIR / "ensemble_results.json").open("w") as f:
            json.dump(result, f, indent=2)


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--n-models", type=int, default=1,
                   help="Kaç model eğitilecek (ensemble için 5 önerilir)")
    args = p.parse_args()
    main(n_models=args.n_models)
