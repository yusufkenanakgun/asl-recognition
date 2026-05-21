"""
FAZ 6: LSTM Model Eğitimi
Video landmark sequence'larından kelime tanıma
Input: (batch, seq_len, 63) -> Output: (batch, num_classes)
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import numpy as np
import json
import time
from pathlib import Path


class LSTMClassifier(nn.Module):
    """
    LSTM-based sequence classifier for sign language recognition
    """
    def __init__(self, input_size=63, hidden_size=128, num_layers=2,
                 num_classes=100, dropout=0.3, bidirectional=True):
        super().__init__()

        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.bidirectional = bidirectional

        # LSTM layer
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0,
            bidirectional=bidirectional
        )

        # Fully connected layers
        lstm_output_size = hidden_size * 2 if bidirectional else hidden_size

        self.fc = nn.Sequential(
            nn.Linear(lstm_output_size, 128),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(128, num_classes)
        )

    def forward(self, x):
        # x: (batch, seq_len, input_size)

        # LSTM forward
        lstm_out, (h_n, c_n) = self.lstm(x)
        # lstm_out: (batch, seq_len, hidden_size * num_directions)

        # Son hidden state'i al (bidirectional için concat)
        if self.bidirectional:
            # Forward ve backward son state'leri concat
            hidden = torch.cat((h_n[-2], h_n[-1]), dim=1)
        else:
            hidden = h_n[-1]

        # Classification
        out = self.fc(hidden)
        return out


def load_data(data_dir):
    """Landmark verilerini yükle"""
    data_dir = Path(data_dir)

    X_train = np.load(data_dir / "X_train.npy")
    y_train = np.load(data_dir / "y_train.npy")
    X_val = np.load(data_dir / "X_val.npy")
    y_val = np.load(data_dir / "y_val.npy")
    X_test = np.load(data_dir / "X_test.npy")
    y_test = np.load(data_dir / "y_test.npy")

    with open(data_dir / "gloss_to_idx.json", "r") as f:
        gloss_to_idx = json.load(f)

    return X_train, y_train, X_val, y_val, X_test, y_test, gloss_to_idx


def create_dataloaders(X_train, y_train, X_val, y_val, batch_size=32):
    """DataLoader'lar oluştur"""
    train_dataset = TensorDataset(
        torch.FloatTensor(X_train),
        torch.LongTensor(y_train)
    )
    val_dataset = TensorDataset(
        torch.FloatTensor(X_val),
        torch.LongTensor(y_val)
    )

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)

    return train_loader, val_loader


def train_epoch(model, dataloader, criterion, optimizer, device):
    """Bir epoch eğitim"""
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0

    for X_batch, y_batch in dataloader:
        X_batch, y_batch = X_batch.to(device), y_batch.to(device)

        optimizer.zero_grad()
        outputs = model(X_batch)
        loss = criterion(outputs, y_batch)
        loss.backward()
        optimizer.step()

        running_loss += loss.item() * X_batch.size(0)
        _, predicted = outputs.max(1)
        total += y_batch.size(0)
        correct += predicted.eq(y_batch).sum().item()

    return running_loss / total, 100. * correct / total


def validate(model, dataloader, criterion, device):
    """Validation"""
    model.eval()
    running_loss = 0.0
    correct = 0
    total = 0

    with torch.no_grad():
        for X_batch, y_batch in dataloader:
            X_batch, y_batch = X_batch.to(device), y_batch.to(device)

            outputs = model(X_batch)
            loss = criterion(outputs, y_batch)

            running_loss += loss.item() * X_batch.size(0)
            _, predicted = outputs.max(1)
            total += y_batch.size(0)
            correct += predicted.eq(y_batch).sum().item()

    return running_loss / total, 100. * correct / total


def train_model(model, train_loader, val_loader, device, num_epochs=100, lr=0.001, patience=15):
    """Model eğitimi"""
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='max', factor=0.5, patience=5)

    best_val_acc = 0.0
    epochs_no_improve = 0
    history = {'train_loss': [], 'train_acc': [], 'val_loss': [], 'val_acc': []}

    print("\n" + "="*60)
    print(f"LSTM Eğitimi başlıyor - {num_epochs} epoch")
    print(f"Device: {device}")
    print(f"Train batches: {len(train_loader)}")
    print(f"Val batches: {len(val_loader)}")
    print("="*60 + "\n")

    start_time = time.time()

    for epoch in range(num_epochs):
        epoch_start = time.time()

        # Train
        train_loss, train_acc = train_epoch(model, train_loader, criterion, optimizer, device)

        # Validate
        val_loss, val_acc = validate(model, val_loader, criterion, device)

        # Scheduler
        scheduler.step(val_acc)

        # History
        history['train_loss'].append(train_loss)
        history['train_acc'].append(train_acc)
        history['val_loss'].append(val_loss)
        history['val_acc'].append(val_acc)

        epoch_time = time.time() - epoch_start

        # Print progress
        print(f"Epoch {epoch+1:3d}/{num_epochs} | "
              f"Train Loss: {train_loss:.4f} | Train Acc: {train_acc:.2f}% | "
              f"Val Loss: {val_loss:.4f} | Val Acc: {val_acc:.2f}% | "
              f"Time: {epoch_time:.1f}s")

        # Save best model
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            epochs_no_improve = 0
            torch.save({
                'model_state_dict': model.state_dict(),
                'best_val_acc': best_val_acc,
                'history': history,
                'num_classes': model.fc[-1].out_features
            }, 'models/best_lstm_model.pth')
            print(f"  -> Yeni en iyi model kaydedildi! (Val Acc: {val_acc:.2f}%)")
        else:
            epochs_no_improve += 1

        # Early stopping
        if epochs_no_improve >= patience:
            print(f"\nEarly stopping! {patience} epoch gelişme yok.")
            break

    total_time = time.time() - start_time

    print("\n" + "="*60)
    print("Eğitim tamamlandı!")
    print(f"Toplam süre: {total_time/60:.1f} dakika")
    print(f"En iyi Val Accuracy: {best_val_acc:.2f}%")
    print("="*60)

    # History kaydet
    with open('models/lstm_training_history.json', 'w') as f:
        json.dump(history, f, indent=2)
    print(f"Eğitim geçmişi kaydedildi: models/lstm_training_history.json")

    return best_val_acc, history


def main():
    # Device
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Kullanılan device: {device}")
    if device.type == 'cuda':
        print(f"GPU: {torch.cuda.get_device_name(0)}")

    # Veri yükle
    print("\nLandmark verileri yükleniyor...")
    data_dir = "data/wlasl-kaggle/landmarks"

    try:
        X_train, y_train, X_val, y_val, X_test, y_test, gloss_to_idx = load_data(data_dir)
    except FileNotFoundError:
        print(f"HATA: {data_dir} klasöründe veri bulunamadı!")
        print("Önce 'python src/extract_video_landmarks.py' çalıştırın.")
        return

    num_classes = len(gloss_to_idx)

    print(f"\nVeri boyutları:")
    print(f"  Train: {X_train.shape}")
    print(f"  Val:   {X_val.shape}")
    print(f"  Test:  {X_test.shape}")
    print(f"  Sınıf sayısı: {num_classes}")

    # DataLoader
    train_loader, val_loader = create_dataloaders(X_train, y_train, X_val, y_val, batch_size=32)

    # Model
    model = LSTMClassifier(
        input_size=63,
        hidden_size=128,
        num_layers=2,
        num_classes=num_classes,
        dropout=0.3,
        bidirectional=True
    ).to(device)

    # Parametre sayısı
    total_params = sum(p.numel() for p in model.parameters())
    print(f"\nModel parametreleri: {total_params:,}")

    # Eğitim
    best_acc, history = train_model(
        model, train_loader, val_loader, device,
        num_epochs=100,
        lr=0.001,
        patience=15
    )

    print(f"\nEğitim tamamlandı! En iyi model: models/best_lstm_model.pth")
    print("Sonraki adım: python src/evaluate_lstm.py çalıştırın")


if __name__ == "__main__":
    main()
