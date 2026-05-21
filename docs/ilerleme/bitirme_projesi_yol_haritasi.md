# Bitirme Projesi Yol Haritası
## AI Destekli İşaret Dili Tanıma Sistemi
### CSE492 — Yusuf Kenan Akgün

---

## FAZ 1: Temel Araştırma ve Hazırlık (2-3 Hafta)

### Literatür Taraması

En az 15-20 makale okunmalı. Öncelik sırasıyla:

- ASL harf tanıma üzerine temel makaleler (özellikle EfficientNet ve landmark-based yaklaşımlar)
- MediaPipe Hands'in teknik makalesi (Zhang et al., 2020)
- WLASL dataset makalesi (Li et al., 2020) — kelime tanıma kısmı için kritik
- Transfer learning ve EfficientNet orijinal makalesi (Tan & Le, 2019)
- Sign language recognition survey makaleleri (genel bakış için)

Her makale için kısa notlar tutulmalı: yöntem, dataset, sonuçlar, sınırlamalar. Bu notlar tezin **Related Work** bölümünü oluşturacak.

### Ortam Kurulumu

- Google Colab Pro veya Docker ile GPU ortamı kurulacak
- Gerekli kütüphaneler: Python, PyTorch, MediaPipe, OpenCV, NumPy, Matplotlib
- Tüm bağımlılıklar `requirements.txt` dosyasına yazılacak
- Git reposu oluşturulacak, baştan itibaren versiyon kontrolü yapılacak
- Klasör yapısı:
  ```
  project/
  ├── data/
  ├── models/
  ├── notebooks/
  ├── src/
  ├── docs/
  └── requirements.txt
  ```

---

## FAZ 2: Veri Seti Hazırlığı (1-2 Hafta)

### Harf Tanıma için Dataset

- ASL Alphabet dataset indirilecek (Kaggle, ~87K görüntü, 29 sınıf)
- Veri incelemesi: sınıf dağılımı, görüntü boyutları, kalite kontrolü
- Train/Validation/Test split (70/15/15)
- Data augmentation stratejisi: rotation, flip, brightness, contrast

### Kelime Tanıma için Dataset

- WLASL dataset indirilecek ve hazırlanacak
- Video bazlı olduğu için frame extraction yapılacak
- Başlangıçta küçük bir subset ile çalışılacak (WLASL-100)
- Video kalitesi ve etiket tutarlılığı kontrol edilecek

---

## FAZ 3: Model 1 — EfficientNet-B0 Transfer Learning (2-3 Hafta)

### Geliştirme Süreci

1. PyTorch'ta pretrained EfficientNet-B0 yüklenir (ImageNet ağırlıkları)
2. Son katman ASL sınıf sayısına göre değiştirilir
3. Önce sadece son katman eğitilir (feature extraction), sonra tüm model fine-tune edilir
4. Hyperparameter denemeleri: learning rate, batch size, optimizer (Adam vs SGD), scheduler
5. Training loop yazılır: loss tracking, validation accuracy, early stopping
6. Her deney loglanır (epoch, lr, accuracy, loss) — tezde tablo olarak kullanılacak

### Beklenen Çıktılar

- Training/Validation loss ve accuracy grafikleri
- Confusion matrix
- Per-class F1 score
- Model boyutu (MB)
- Inference süresi (FPS)

---

## FAZ 4: Model 2 — MLP Landmark-Based (2-3 Hafta)

### Geliştirme Süreci

1. MediaPipe Hands ile tüm datasetdeki görüntülerden landmark çıkarılır (21 nokta × 3 koordinat = 63 boyutlu vektör)
2. Landmark'lar normalize edilir (el boyutundan bağımsız hale getirilir)
3. MLP mimarisi tasarlanır: input(63) → hidden layers → output(sınıf sayısı)
4. Farklı hidden layer konfigürasyonları denenir
5. Dropout, batch normalization gibi regularization teknikleri uygulanır
6. Aynı metriklerle değerlendirilir

### Önemli Not

MediaPipe bazı görüntülerde el tespit edemeyebilir — bu durumlar loglanmalı ve tezde **"detection failure rate"** olarak raporlanmalı. Bu, iki yaklaşımın karşılaştırmasında önemli bir tartışma noktası olacak.

---

## FAZ 5: Karşılaştırmalı Analiz (1 Hafta)

İki model şu metriklerde karşılaştırılacak:

| Metrik | Açıklama |
|--------|----------|
| Top-1 Accuracy | En yüksek olasılıklı tahmin doğruluğu |
| Top-5 Accuracy | İlk 5 tahmin içinde doğru sınıfın bulunma oranı |
| Per-class F1 Score | Her harf için ayrı ayrı F1 |
| Confusion Matrix | Benzer harflerde karışıklık analizi (M-N, A-S gibi) |
| Model Boyutu (MB) | Deploy edilebilirlik açısından |
| Inference Hızı (FPS) | Gerçek zamanlı kullanım için |
| Eğitim Süresi | Toplam training time |
| Dayanıklılık | Farklı ışık, arka plan koşullarında performans |

Tüm sonuçlar tablolar ve grafiklerle belgelenir.

---

## FAZ 6: Kelime Tanıma — LSTM Uzantısı (2-3 Hafta)

### Geliştirme

1. WLASL subset'inden videolar frame'lere ayrılır
2. Her frame'den MediaPipe ile landmark çıkarılır → frame başına 63 boyutlu vektör
3. Video = frame dizisi → sequence olarak LSTM/GRU'ya beslenir
4. Sequence padding/truncation stratejisi belirlenir
5. LSTM modeli eğitilir ve değerlendirilir
6. En azından temel sonuçlar elde edilir

> **Not:** Mükemmel olması şart değil — tezde "gelecek çalışma" olarak genişletilebilir.

---

## FAZ 7: Demo Uygulama (1-2 Hafta)

### Mobil Demo (Android + TensorFlow Lite) — Proposal yöntemi

Proposal'da demo uygulaması **mobil (Android/iOS) + React Native + TensorFlow Lite** olarak tanımlanmıştır. Bu faz aynen bu kapsamda yürütülür; PC/web tabanlı bir demo proposal kapsamında değildir.

- PyTorch → ONNX → TFLite dönüşüm pipeline'ı (önce MLP, sonra EfficientNet, sonra LSTM)
- Mobil cihaz kamerası erişimi + MediaPipe Tasks (Android) ile el landmark çıkarımı
- TFLite üzerinden cihaz-üstü (on-device) inference
- Tanınan harf/kelime ekrana yazılır; FPS ve latency ölçülür
- Stack tercihi: bare React Native + `react-native-fast-tflite` + `react-native-vision-camera`. RN ekosistem riski engelse fallback **native Android (Kotlin + TFLite + MediaPipe Tasks Android SDK)**.

> **Sunum İpucu:** Canlı demo gösterimi çok etkili olur. Backup olarak mutlaka bir demo videosu kaydedilmeli.

---

## FAZ 8: Tez Yazımı (3-4 Hafta, paralel başlanmalı)

### Tez Yapısı

1. **Introduction** — Problem tanımı, motivasyon, katkılar
2. **Related Work** — Literatür taraması
3. **Methodology** — Sistem mimarisi, veri seti, iki model yaklaşımı, LSTM uzantısı
4. **Implementation** — Teknik detaylar, ortam, parametreler
5. **Experimental Results** — Tablolar, grafikler, karşılaştırma
6. **Discussion** — Sonuçların yorumlanması, hangi model neden daha iyi, sınırlamalar
7. **Conclusion & Future Work**

### İpuçları

- Metodoloji bölümü kod yazılırken paralel yazılmalı — ne yapıldığı o an en iyi hatırlanır
- Her deneyin parametreleri ve sonuçları not alınmalı
- UML diyagramları (Use Case, Sequence, State) metodoloji kısmına girecek
- LaTeX kullanılması önerilir (Overleaf ile online çalışılabilir)

---

## FAZ 9: Sunum Hazırlığı (1 Hafta)

- 15-20 slide'lık sunum hazırlanacak
- Canlı demo gösterimi planlanacak (backup: video kayıt)
- Olası sorular tahmin edilip cevapları hazırlanacak
- Prova yapılacak — zamanlama kontrol edilecek

---

## Genel Zaman Çizelgesi

| Faz | Süre | Notlar |
|-----|------|--------|
| FAZ 1: Literatür + Ortam | 2-3 hafta | Paralel yürütülecek |
| FAZ 2: Veri Hazırlığı | 1-2 hafta | |
| FAZ 3: EfficientNet-B0 | 2-3 hafta | |
| FAZ 4: MLP Landmark | 2-3 hafta | Tez yazmaya başlanmalı |
| FAZ 5: Karşılaştırma | 1 hafta | |
| FAZ 6: LSTM Kelime | 2-3 hafta | |
| FAZ 7: Demo | 1-2 hafta | |
| FAZ 8: Tez | 3-4 hafta | Son düzeltmeler |
| FAZ 9: Sunum | 1 hafta | |
| **TOPLAM** | **~16-20 hafta** | |

---

## Pratik Tavsiyeler

- **Git:** Her şey versiyon kontrolünde tutulmalı
- **Deney Takibi:** Spreadsheet veya Weights & Biases ile loglanmalı
- **Tez:** Erken başlanmalı — sona bırakılmamalı
- **Danışman:** En az 2 haftada bir ilerleme paylaşılmalı
- **Yardım:** Takılınca Claude'dan destek alınabilir (model mimarisi, hata analizi, tez yazımı)

---

*Son güncelleme: Mart 2026*
