"""
EfficientNet-B0 Eğitim Script'i
ASL Alphabet Recognition
"""

import torch
import torch.nn as nn
import torch.optim as optim
from pathlib import Path
import time
import json

from model import create_model, unfreeze_model
from dataset import get_dataloaders, CLASSES


class Trainer:
    def __init__(
        self,
        model,
        train_loader,
        val_loader,
        device,
        lr=0.001,
        save_dir="models"
    ):
        self.model = model.to(device)
        self.train_loader = train_loader
        self.val_loader = val_loader
        self.device = device
        self.save_dir = Path(save_dir)
        self.save_dir.mkdir(exist_ok=True)

        self.criterion = nn.CrossEntropyLoss()
        self.optimizer = optim.Adam(
            filter(lambda p: p.requires_grad, model.parameters()),
            lr=lr
        )

        # Eğitim geçmişi
        self.history = {
            "train_loss": [],
            "train_acc": [],
            "val_loss": [],
            "val_acc": []
        }
        self.best_val_acc = 0.0

    def train_epoch(self):
        """Bir epoch eğitim"""
        self.model.train()
        running_loss = 0.0
        correct = 0
        total = 0

        for images, labels in self.train_loader:
            images = images.to(self.device)
            labels = labels.to(self.device)

            self.optimizer.zero_grad()
            outputs = self.model(images)
            loss = self.criterion(outputs, labels)
            loss.backward()
            self.optimizer.step()

            running_loss += loss.item() * images.size(0)
            _, predicted = outputs.max(1)
            total += labels.size(0)
            correct += predicted.eq(labels).sum().item()

        epoch_loss = running_loss / total
        epoch_acc = 100.0 * correct / total
        return epoch_loss, epoch_acc

    def validate(self):
        """Validation"""
        self.model.eval()
        running_loss = 0.0
        correct = 0
        total = 0

        with torch.no_grad():
            for images, labels in self.val_loader:
                images = images.to(self.device)
                labels = labels.to(self.device)

                outputs = self.model(images)
                loss = self.criterion(outputs, labels)

                running_loss += loss.item() * images.size(0)
                _, predicted = outputs.max(1)
                total += labels.size(0)
                correct += predicted.eq(labels).sum().item()

        epoch_loss = running_loss / total
        epoch_acc = 100.0 * correct / total
        return epoch_loss, epoch_acc

    def train(self, epochs, early_stop_patience=5):
        """
        Tam eğitim döngüsü

        Args:
            epochs: Toplam epoch sayısı
            early_stop_patience: Kaç epoch gelişme olmazsa dur
        """
        print(f"\n{'='*60}")
        print(f"Eğitim başlıyor - {epochs} epoch")
        print(f"Device: {self.device}")
        print(f"Train batches: {len(self.train_loader)}")
        print(f"Val batches: {len(self.val_loader)}")
        print(f"{'='*60}\n")

        patience_counter = 0
        start_time = time.time()

        for epoch in range(1, epochs + 1):
            epoch_start = time.time()

            # Train
            train_loss, train_acc = self.train_epoch()

            # Validate
            val_loss, val_acc = self.validate()

            # Geçmişe kaydet
            self.history["train_loss"].append(train_loss)
            self.history["train_acc"].append(train_acc)
            self.history["val_loss"].append(val_loss)
            self.history["val_acc"].append(val_acc)

            epoch_time = time.time() - epoch_start

            # Sonuçları yazdır
            print(f"Epoch {epoch:3d}/{epochs} | "
                  f"Train Loss: {train_loss:.4f} | Train Acc: {train_acc:.2f}% | "
                  f"Val Loss: {val_loss:.4f} | Val Acc: {val_acc:.2f}% | "
                  f"Time: {epoch_time:.1f}s")

            # En iyi model kontrolü
            if val_acc > self.best_val_acc:
                self.best_val_acc = val_acc
                self.save_checkpoint("best_model.pth")
                print(f"  -> Yeni en iyi model kaydedildi! (Val Acc: {val_acc:.2f}%)")
                patience_counter = 0
            else:
                patience_counter += 1

            # Early stopping
            if patience_counter >= early_stop_patience:
                print(f"\nEarly stopping! {early_stop_patience} epoch gelişme yok.")
                break

        total_time = time.time() - start_time
        print(f"\n{'='*60}")
        print(f"Eğitim tamamlandı!")
        print(f"Toplam süre: {total_time/60:.1f} dakika")
        print(f"En iyi Val Accuracy: {self.best_val_acc:.2f}%")
        print(f"{'='*60}")

        # Geçmişi kaydet
        self.save_history()

        return self.history

    def save_checkpoint(self, filename):
        """Model checkpoint kaydet"""
        path = self.save_dir / filename
        torch.save({
            "model_state_dict": self.model.state_dict(),
            "optimizer_state_dict": self.optimizer.state_dict(),
            "best_val_acc": self.best_val_acc,
            "history": self.history
        }, path)

    def save_history(self):
        """Eğitim geçmişini JSON olarak kaydet"""
        path = self.save_dir / "training_history.json"
        with open(path, "w") as f:
            json.dump(self.history, f, indent=2)
        print(f"Eğitim geçmişi kaydedildi: {path}")


def main():
    # Ayarlar
    BATCH_SIZE = 32
    LEARNING_RATE = 0.001
    EPOCHS_PHASE1 = 5      # Feature extraction (frozen backbone)
    EPOCHS_PHASE2 = 10     # Fine-tuning (tüm model)
    EARLY_STOP_PATIENCE = 3

    # Device
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Kullanılan device: {device}")
    if device.type == "cuda":
        print(f"GPU: {torch.cuda.get_device_name(0)}")

    # DataLoader
    print("\nDataLoader'lar hazırlanıyor...")
    train_loader, val_loader, test_loader = get_dataloaders(
        batch_size=BATCH_SIZE,
        num_workers=0  # Windows için 0
    )
    print(f"Train: {len(train_loader.dataset)} görüntü")
    print(f"Val: {len(val_loader.dataset)} görüntü")

    # ========== FAZ 1: Feature Extraction ==========
    print("\n" + "="*60)
    print("FAZ 1: Feature Extraction (Backbone dondurulmuş)")
    print("="*60)

    model = create_model(num_classes=29, pretrained=True, freeze_backbone=True)

    trainer = Trainer(
        model=model,
        train_loader=train_loader,
        val_loader=val_loader,
        device=device,
        lr=LEARNING_RATE,
        save_dir="models"
    )

    trainer.train(epochs=EPOCHS_PHASE1, early_stop_patience=EARLY_STOP_PATIENCE)

    # ========== FAZ 2: Fine-tuning ==========
    print("\n" + "="*60)
    print("FAZ 2: Fine-tuning (Tüm model eğitiliyor)")
    print("="*60)

    # Backbone'u aç
    model = unfreeze_model(model)

    # Yeni optimizer (daha düşük lr)
    trainer.optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE / 10)

    trainer.train(epochs=EPOCHS_PHASE2, early_stop_patience=EARLY_STOP_PATIENCE)

    print("\nEğitim tamamlandı! En iyi model: models/best_model.pth")


if __name__ == "__main__":
    main()
