# İlerleme Raporu #1
**Tarih:** 13 Mart 2026
**Proje:** AI Destekli İşaret Dili Tanıma Sistemi
**Öğrenci:** Yusuf Kenan Akgün

---

## Tamamlanan Fazlar

### FAZ 1: Ortam Kurulumu ✓

| Bileşen | Versiyon | Açıklama |
|---------|----------|----------|
| Python | 3.x | Sanal ortam (venv) |
| PyTorch | 2.6.0+cu124 | CUDA destekli, GPU eğitimi |
| torchvision | 0.21.0+cu124 | Pretrained modeller (EfficientNet) |
| MediaPipe | 0.10.32 | El landmark tespiti |
| OpenCV | 4.13.0 | Görüntü işleme, kamera |
| NumPy | 2.4.3 | Array işlemleri |
| scikit-learn | - | Metrikler, split |
| matplotlib, seaborn | - | Görselleştirme |

**GPU:** NVIDIA GeForce RTX 3050 Laptop GPU (4GB VRAM)
**CUDA:** 12.4 (Driver 13.0 uyumlu)

**Klasör Yapısı:**
```
ai-isaret/
├── data/           → Veri setleri
├── models/         → Eğitilmiş modeller
├── notebooks/      → Jupyter notebook'lar
├── src/            → Kaynak kodları
├── docs/           → Dokümantasyon
├── demo/           → Demo uygulaması
├── requirements.txt
└── .gitignore
```

---

### FAZ 2: Veri Seti Hazırlığı ✓

**Dataset:** ASL Alphabet (Kaggle)

| Özellik | Değer |
|---------|-------|
| Toplam görüntü | 87,000 |
| Sınıf sayısı | 29 (A-Z + del, nothing, space) |
| Sınıf başına | 3,000 görüntü (dengeli) |
| Görüntü boyutu | 200×200 piksel |

**Train/Val/Test Split:**

| Set | Görüntü | Oran |
|-----|---------|------|
| Train | 60,900 | %70 |
| Validation | 13,050 | %15 |
| Test | 13,050 | %15 |

**Augmentation (Train için):**
- RandomHorizontalFlip (p=0.3)
- RandomRotation (±15°)
- ColorJitter (brightness, contrast)
- Resize → 224×224 (EfficientNet için)
- ImageNet normalization

**Oluşturulan Dosyalar:**
- `src/data_analysis.py` — Dataset analizi
- `src/data_split.py` — Train/Val/Test split
- `src/dataset.py` — PyTorch DataLoader ve augmentation

---

---

### FAZ 3: EfficientNet-B0 Transfer Learning ✓

| Aşama | Epoch | Train Acc | Val Acc | Süre |
|-------|-------|-----------|---------|------|
| Feature Extraction | 5 | 88.52% | 94.90% | 38.5 dk |
| Fine-tuning | 6 (early stop) | 99.87% | 100.00% | 85.4 dk |

**Test Seti Sonuçları:**

| Metrik | Değer |
|--------|-------|
| Test Accuracy | **100.00%** |
| Per-class F1-score | 1.0000 (tüm sınıflar) |
| Yanlış sınıflandırma | 0 |
| Model boyutu (training checkpoint) | 46.75 MB |
| Model boyutu (deployment, state_dict) | **15.71 MB** |
| Inference hızı | **490.9 FPS** |
| Görüntü başına | 2.04 ms |

**Kaydedilen Dosyalar:**
- `models/best_model.pth` — Eğitilmiş model
- `models/training_history.json` — Eğitim geçmişi
- `models/evaluation_results.json` — Değerlendirme sonuçları
- `models/confusion_matrix.png` — Confusion matrix görselleştirmesi

---

## Kalan Fazlar

### FAZ 4: MLP Landmark-Based Model ✓

**Landmark Extraction:**

| Metrik | Değer |
|--------|-------|
| Toplam görüntü | 87,000 |
| Başarılı extraction | 63,590 (%73.09) |
| Başarısız (el bulunamadı) | 23,410 (%26.91) |

*Not: `nothing` sınıfında el yok, `N` ve `M` harflerinde düşük tespit oranı.*

**MLP Eğitim Sonuçları:**

| Aşama | Epoch | Val Acc | Süre |
|-------|-------|---------|------|
| Eğitim | 100 | 99.33% | 5 dk |

**Test Seti Sonuçları:**

| Metrik | Değer |
|--------|-------|
| Test Accuracy | **99.38%** |
| Model boyutu | **0.24 MB** |
| Inference hızı | **91,650 FPS** |
| Örnek başına | 0.01 ms |

**En çok karıştırılan harfler:** M↔N, R↔U

**Kaydedilen Dosyalar:**
- `models/best_mlp_model.pth` — Eğitilmiş MLP model
- `models/mlp_training_history.json` — Eğitim geçmişi
- `models/mlp_evaluation_results.json` — Değerlendirme sonuçları
- `models/mlp_confusion_matrix.png` — Confusion matrix
- `data/landmarks/` — Extracted landmark verileri

### FAZ 5: Karşılaştırmalı Analiz ✓

| Metrik | EfficientNet-B0 | MLP Landmark |
|--------|-----------------|--------------|
| Test Accuracy | **100.00%** | 99.38%* |
| Model Boyutu (deployment) | 15.71 MB | **0.24 MB** |
| FPS (GPU) | 490.9 | **91,650** |
| Detection Rate | **100%** | 73.09% |
| Eğitim Süresi | ~2 saat | **5 dakika** |
| Bağımlılık | Yok | MediaPipe |

*\*MLP accuracy sadece el tespit edilen görüntülerde ölçülmüştür.*

**Sonuç:**
- EfficientNet daha güvenilir (her görüntüde çalışır)
- MLP çok daha hafif ve hızlı (mobil/edge için uygun)
- Trade-off: Güvenilirlik vs Hafiflik

### FAZ 6: LSTM Kelime Tanıma (Sıradaki)
- [ ] WLASL dataset indirme
- [ ] Video → frame extraction
- [ ] Frame başına landmark → sequence
- [ ] LSTM/GRU model eğitimi

### FAZ 7: Demo Uygulama (Proposal: mobil-only)
- [ ] PyTorch → ONNX → TFLite dönüşüm pipeline'ı (MLP, EfficientNet, LSTM)
- [ ] React Native + TFLite + MediaPipe Tasks ile Android demo (fallback: native Android/Kotlin)
- [ ] Gerçek Android cihazda canlı harf/kelime tanıma + FPS/latency ölçümü

### FAZ 8: Tez Yazımı
- [ ] Introduction, Related Work
- [ ] Methodology, Implementation
- [ ] Experimental Results
- [ ] Discussion, Conclusion

### FAZ 9: Sunum
- [ ] 15-20 slide sunum
- [ ] Canlı demo hazırlığı
- [ ] Prova

---

## Notlar

### Data Leakage Hakkında
Dataset tek kaynaktan geldiği için person-wise split yapılamadı. Random split kullanıldı. Gerçek generalization performansı mobil demoda (Android cihazda yeni el görüntüleri ile) test edilecek. Bu durum tezde "Limitations" bölümünde belirtilecek.

### GitHub
Repo: https://github.com/yusufkenanakgun/ai-isaret-dili

---

*Son güncelleme: 13 Mart 2026*
