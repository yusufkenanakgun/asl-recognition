# FAZ 6: Kelime Tanıma (LSTM) - Gün 1
**Tarih:** 13 Mart 2026

---

## Hedef
WLASL (Word-Level American Sign Language) dataset ile kelime tanıma modeli eğitmek.

---

## Deneme 1: YouTube'dan Video İndirme

### Yapılan
1. `download_wlasl.py` scripti yazıldı
2. WLASL GitHub'dan JSON metadata indirildi
3. yt-dlp ile YouTube videolarını indirme denendi

### Ayarlar
- Dataset: WLASL100 (100 kelime)
- max_per_class: 80 video/kelime

### Sonuç
```
İndirilecek video: 2038
Başarılı: 452 (%22)
Başarısız: 1586 (%78)
```

### Sorun
YouTube videoları yıllar içinde silinmiş. WLASL'ın bilinen bir problemi.

---

## Deneme 2: Eksik Videoları Tamamlama

### Yapılan
`download_wlasl_missing.py` scripti yazıldı - eksik kelimeler için ek video indirme denemesi.

### Sonuç
```
Başarılı: 0
Başarısız: 285
```

### Sorun
Tüm eksik videolar için URL'ler artık çalışmıyor.

---

## Deneme 3: Mevcut Videolarla Eğitim

### Landmark Extraction
```
Toplam video: 452
Başarılı extraction: 452 (%100)
```

### Filtreleme Sorunu
- Stratified split için her sınıfta minimum örnek gerekli
- 50 sınıf filtrelendi (< 5 video)
- Kalan: 50 sınıf, 297 video

### LSTM Eğitimi
```
Train: 207 örnek
Val: 45 örnek
Test: 45 örnek
Sınıf sayısı: 50
```

### Sonuç
```
En iyi Val Accuracy: %8.89
```

### Analiz
- Çok az veri (sınıf başına ~4 örnek)
- Overfitting: Train %40, Val %8
- Model öğrenemiyor

---

## Deneme 4: Kaggle WLASL Processed

### Keşif
Kaggle'da hazır indirilmiş WLASL videoları mevcut:
- https://www.kaggle.com/datasets/risangbaskoro/wlasl-processed

### İndirme
```powershell
kaggle datasets download -d risangbaskoro/wlasl-processed -p data/wlasl-kaggle
```

### Sonuç
```
İndirilen: 4.82 GB
Video sayısı: 11,980
```

### Veri Yapısı
```
data/wlasl-kaggle/
├── videos/           # Tüm videolar (00335.mp4, ...)
├── nslt_100.json     # 100 sınıf için etiketler
├── nslt_300.json     # 300 sınıf için etiketler
├── nslt_1000.json    # 1000 sınıf için etiketler
├── nslt_2000.json    # 2000 sınıf için etiketler
├── wlasl_class_list.txt  # Sınıf isimleri
└── WLASL_v0.3.json   # Orijinal metadata
```

### JSON Formatı
```json
"05237": {"subset": "train", "action": [77, 1, 55]}
```
- `05237`: video_id (05237.mp4)
- `subset`: train/val/test
- `action[0]`: class_id (77 = "write")

### Sınıf Listesi (örnek)
```
0   book
1   drink
2   computer
3   before
4   chair
...
```

---

## Sonraki Adımlar

1. **Kaggle landmark extraction**: `python src/extract_kaggle_landmarks.py`
2. **LSTM eğitimi**: `python src/train_lstm.py`
3. **Değerlendirme**: `python src/evaluate_lstm.py`

---

## Karşılaşılan Teknik Sorunlar

### 1. MediaPipe API Değişikliği
- **Sorun:** `mp.solutions.hands` artık yok
- **Çözüm:** Yeni Tasks API kullanıldı (`mediapipe.tasks.vision.HandLandmarker`)

### 2. Stratified Split Hatası
- **Sorun:** Bazı sınıflarda < 2 örnek
- **Çözüm:** Minimum örnek sayısını 5'e çıkardık + fallback random split

### 3. Video Timing
- **Sorun:** Bazı videolar 3-4 dakika uzunluğunda
- **Çözüm:** WLASL JSON'dan start_time/end_time bilgisi kullanıldı

---

## Öğrenilen Dersler

1. **WLASL dataset erişim sorunu**: YouTube videoları zamanla siliniyor, Kaggle versiyonu daha güvenilir
2. **Veri miktarı kritik**: 50 sınıf için 297 video yeterli değil, en az 1000+ gerekli
3. **Kelime tanıma zor**: Harf tanımada %100 aldık ama kelime tanıma çok daha zorlu

---

## Beklentiler (Kaggle verisiyle)

| Metrik | YouTube Verisi | Kaggle Verisi (Beklenti) |
|--------|----------------|--------------------------|
| Video sayısı | 452 | ~2000+ |
| Sınıf sayısı | 50 | 100 |
| Val Accuracy | %8.89 | %40-60 (hedef) |

---

*Son güncelleme: 13 Mart 2026, ~23:00*
