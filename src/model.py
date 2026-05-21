"""
EfficientNet-B0 Transfer Learning Model
ASL Alphabet Recognition (29 sınıf)
"""

import torch
import torch.nn as nn
from torchvision.models import efficientnet_b0, EfficientNet_B0_Weights


def create_model(num_classes=29, pretrained=True, freeze_backbone=True):
    """
    EfficientNet-B0 modelini ASL sınıflandırması için hazırlar.

    Args:
        num_classes: Çıkış sınıf sayısı (ASL için 29)
        pretrained: ImageNet ağırlıklarını kullan
        freeze_backbone: Backbone'u dondur (sadece son katman eğitilir)

    Returns:
        model: Hazırlanmış PyTorch modeli
    """
    # Pretrained model yükle
    if pretrained:
        weights = EfficientNet_B0_Weights.IMAGENET1K_V1
        model = efficientnet_b0(weights=weights)
    else:
        model = efficientnet_b0(weights=None)

    # Backbone'u dondur (opsiyonel)
    if freeze_backbone:
        for param in model.parameters():
            param.requires_grad = False

    # Son katmanı değiştir (classifier)
    # EfficientNet-B0: classifier[1] -> Linear(1280, 1000)
    in_features = model.classifier[1].in_features
    model.classifier[1] = nn.Linear(in_features, num_classes)

    return model


def unfreeze_model(model):
    """Tüm katmanları eğitilebilir yapar (fine-tuning için)."""
    for param in model.parameters():
        param.requires_grad = True
    return model


if __name__ == "__main__":
    # Test
    model = create_model(num_classes=29, freeze_backbone=True)
    print(f"Model oluşturuldu!")
    print(f"Classifier: {model.classifier}")

    # Parametre sayısı
    total = sum(p.numel() for p in model.parameters())
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"Toplam parametre: {total:,}")
    print(f"Eğitilebilir parametre: {trainable:,}")
