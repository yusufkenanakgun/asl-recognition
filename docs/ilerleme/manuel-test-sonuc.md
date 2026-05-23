# FAZ 7 — Manuel Test Sonuç Raporu

> Bu dosya `manuel-test.md` prosedürünün doldurulmuş halidir. Her bölüm sırayla doldurulur, ✓/✗ ve sayısal değerler yazılır.

**Test tarihi:** 2026-05-22
**Test cihazı (model, Android sürümü):** TECNO SPARK 20C
**Test kullanıcısı (kim test etti):** Yusuf Kenan Akgün
**Ortam (aydınlatma, arka plan):** Evde cama bakan bir noktada (görüntü çok net )
**APK build commit:** .\gradlew installDebug

---

## 0. Hazırlık Kontrol Listesi

- [y ] Wireless ADB aktif, `adb devices` cihazı görüyor
- [y ] Son APK yüklendi
- [y ] Şarj ≥ %50, Battery Saver kapalı
- [y ] Aydınlatma & arka plan kontrol edildi
- [n ] Ekran kaydı başladı (`/sdcard/test.mp4`)

---

## 1. Smoke Test Sonuçları

| Deneme | Açılış süresi (s) | Letters kamera (s) | Words kamera (s) | Çökme / hata? |
|---|---|---|---|---|
| 1 | 5 | 1 | 1 | yok — letters direkt açıldı, words "collecting frames" sonrası tahmin başladı |
| 2 | 5| 1 | 1 | yok |
| 3 | 4 | 1 | 1 | yok |

**Geçer/kalır (3/3 olmalı):** **3 / 3** ☑

> Not: Açılış süresi 4-5 sn (FAZ7'deki ≤ 3 sn hedefini ~1-2 sn aştı). Cold-start blok düzeltmeleri sonrası beklenen aralıkta; "Bilinen sınırlamalar" bölümüne yazılacak.

Logcat'te `MediaPipeException` / `FATAL` görüldü mü? ☐ Bugün ☑ Sadece eski log

**Bulgu:** İlk `adb logcat -d` çıktısında 2 adet `MediaPipeException: smaller timestamp than processed timestamp` (FATAL) kaydı bulundu. **Zaman damgası 2026-05-20 03:03 ve 03:14 — bugünkü manuel testten 2 gün önceki çalışmaya ait** (FAZ7.md'de bilinen hata, fix uygulanmadan önce).

**Doğrulama:** `adb logcat -c` ile buffer temizlendi, uygulama 2 dk çalıştırıldı (Letters + Words), sonra tekrar dump:

| Durum | Sonuç |
|---|---|
| Bugünkü çalışma boyunca UI crash | YOK |
| Bugünkü çalışma boyunca logcat exception | YOK (logcat boş çıktı) |

→ Fix çalışıyor.

Stack trace özeti (eski log için, referans):
```
FATAL EXCEPTION: pool-5-thread-1
com.google.mediapipe.framework.MediaPipeException: failed precondition:
The received packets having a smaller timestamp than the processed timestamp.
  at HandLandmarker.detectAsync(HandLandmarker.java:387)
  at HandLandmarkerSource.detectAsync(HandLandmarkerSource.kt:80)
  at FrameAnalyzer.analyze(FrameAnalyzer.kt:28)
```

---

## 2. Letters — Doğruluk

### 2A. EfficientNet-B0 (29 sınıf × 1 deneme, 28 ölçülebilir)

> **Kayıt formatı:**
> - `Top-1`: doğru ise `Y`, yanlış ise `N → <tahmin>` (örn: `N → S`), test edilemiyorsa `N/A`
> - `Güven %`: Top-3 panelindeki **ilk** tahminin yüzdesi (örn: `99`)
> - `Top-3 doğru?`: Top-1 yanlışsa Top-3'te doğru sınıf var mı (`Y`/`N`). Top-1 doğruysa `—`.

| Sınıf | Top-1 | Güven % | Top-3 doğru? | Not |
|---|---|---|---|---|
| A | Y | 99 | — | top-1 %98-100 arası stabil |
| B | Y | 100 | — | |
| C | Y | 100 | — | |
| D | N → K/R | 60 | Y | çok kararsız, K veya R ile karışıyor |
| E | Y | 100 | — | |
| F | Y | 82 | — | 4-5 sn sonra %90 üstü (warm-up) |
| G | Y | 75 | — | |
| H | Y | 100 | — | |
| I | Y | 100 | — | |
| J | Y | 50 | — | bazen I ile karışıyor (statik tutuldu) |
| K | N → W | 40 | Y | W ile karışıyor, genelde W diyor |
| L | Y | 100 | — | |
| M | Y | 100 | — | |
| N | Y | 87 | — | |
| O | Y | 100 | — | |
| P | Y | 95 | — | |
| Q | Y | 100 | — | |
| R | Y | 100 | — | |
| S | Y | 99 | — | |
| T | Y | 100 | — | |
| U | Y | 100 | — | |
| V | Y | 95 | — | |
| W | Y | 100 | — | |
| X | Y | 100 | — | |
| Y | Y | 100 | — | |
| Z | Y | 90 | — | |
| del | Y | 90 | — | |
| nothing | N/A | N/A | N/A | pipeline el algılamadığında classifier çağrılmıyor (kasıtlı) |
| space | Y | 100 | — | |

**Özet (28 ölçülebilir sınıf üzerinden):**
- Top-1 doğru: **26 / 28 = %92.9** (yanlış: D, K)
- Top-3 doğru (Top-1 doğru + Top-3'te bulunan yanlışlar): **28 / 28 = %100**
- Ortalama güven % (26 doğru tahmin üzerinden): **~%94.7**
- **Eşik (Top-1 ≥ %70 yani ≥ 20/28):** ☑ GEÇTİ ☐ KALDI
- **Eşik (Top-3 ≥ %88 yani ≥ 25/28):** ☑ GEÇTİ ☐ KALDI
- **Eşik (Ortalama güven ≥ %75):** ☑ GEÇTİ ☐ KALDI

### 2B. MLP Landmark (29 sınıf × 1 deneme, 28 ölçülebilir)

| Sınıf | Top-1 | Güven % | Top-3 doğru? | Not |
|---|---|---|---|---|
| A | Y | 100 | — | |
| B | Y | 100 | — | |
| C | Y | 100 | — | |
| D | Y | 100 | — | EffNet'in zayıf olduğu D burada çok sağlam |
| E | Y | 100 | — | |
| F | Y | 100 | — | |
| G | Y | 100 | — | |
| H | Y | 100 | — | |
| I | Y | 100 | — | |
| J | Y | 100 | — | çok kararlı (EffNet'te %50 → MLP %100) |
| K | Y | 100 | — | EffNet'in zayıf olduğu K burada çok sağlam |
| L | Y | 100 | — | |
| M | Y | 90 | — | tüm sınıflar arasında en düşük güven |
| N | Y | 100 | — | |
| O | Y | 100 | — | |
| P | Y | 100 | — | |
| Q | Y | 100 | — | |
| R | Y | 100 | — | |
| S | Y | 100 | — | |
| T | Y | 100 | — | |
| U | Y | 100 | — | |
| V | Y | 100 | — | |
| W | Y | 100 | — | |
| X | Y | 100 | — | |
| Y | Y | 100 | — | |
| Z | Y | 100 | — | |
| del | Y | 99 | — | |
| nothing | N/A | N/A | N/A | pipeline el algılamadığında classifier çağrılmıyor (kasıtlı) |
| space | Y | 100 | — | |

**Özet (28 ölçülebilir sınıf üzerinden):**
- Top-1 doğru: **28 / 28 = %100**
- Top-3 doğru: **28 / 28 = %100**
- Ortalama güven %: **~%99.6**
- **Eşik (Top-1 ≥ %65 yani ≥ 19/28):** ☑ GEÇTİ ☐ KALDI
- **Eşik (Top-3 ≥ %85 yani ≥ 24/28):** ☑ GEÇTİ ☐ KALDI
- **Eşik (Ortalama güven ≥ %75):** ☑ GEÇTİ ☐ KALDI

---

## 3. Words — Doğruluk

Alt küme (15 kelime): `drink, mother, computer, yes, no, like, help, book, dance, family, blue, eat, want, time, who`

### 3A. BiLSTM Single

| Kelime | T1 | T2 | T3 | Top-1 doğru | Top-3 doğru | Not |
|---|---|---|---|---|---|---|
| drink | | | | / 3 | / 3 | |
| mother | | | | / 3 | / 3 | |
| computer | | | | / 3 | / 3 | |
| yes | | | | / 3 | / 3 | |
| no | | | | / 3 | / 3 | |
| like | | | | / 3 | / 3 | |
| help | | | | / 3 | / 3 | |
| book | | | | / 3 | / 3 | |
| dance | | | | / 3 | / 3 | |
| family | | | | / 3 | / 3 | |
| blue | | | | / 3 | / 3 | |
| eat | | | | / 3 | / 3 | |
| want | | | | / 3 | / 3 | |
| time | | | | / 3 | / 3 | |
| who | | | | / 3 | / 3 | |

**Özet:**
- Top-1 toplam: ___ / 45 = ___ %
- Top-3 toplam: ___ / 45 = ___ %
- **Eşik (Top-1 ≥ %35):** □ GEÇTİ □ KALDI
- **Eşik (Top-3 ≥ %60):** □ GEÇTİ □ KALDI

### 3B. BiLSTM Ensemble (x5)

| Kelime | T1 | T2 | T3 | Top-1 doğru | Top-3 doğru | Not |
|---|---|---|---|---|---|---|
| drink | | | | / 3 | / 3 | |
| mother | | | | / 3 | / 3 | |
| computer | | | | / 3 | / 3 | |
| yes | | | | / 3 | / 3 | |
| no | | | | / 3 | / 3 | |
| like | | | | / 3 | / 3 | |
| help | | | | / 3 | / 3 | |
| book | | | | / 3 | / 3 | |
| dance | | | | / 3 | / 3 | |
| family | | | | / 3 | / 3 | |
| blue | | | | / 3 | / 3 | |
| eat | | | | / 3 | / 3 | |
| want | | | | / 3 | / 3 | |
| time | | | | / 3 | / 3 | |
| who | | | | / 3 | / 3 | |

**Özet:**
- Top-1 toplam: ___ / 45 = ___ %
- Top-3 toplam: ___ / 45 = ___ %
- Ensemble − Single (Top-1): +___ puan
- **Eşik (Top-1 ≥ %40):** □ GEÇTİ □ KALDI
- **Eşik (Top-3 ≥ %65):** □ GEÇTİ □ KALDI
- **Eşik (Ensemble > Single en az +3 puan):** □ GEÇTİ □ KALDI

---

## 4. Performans — FPS & Latency

Her satır: badge'den 10 saniye aralıklarla okunan 6 örneğin değerleri.

### EfficientNet-B0
| t=10s | t=20s | t=30s | t=40s | t=50s | t=60s | Ort FPS | Min FPS | Maks FPS | Ort ms | Maks ms |
|---|---|---|---|---|---|---|---|---|---|---|
| | | | | | | | | | | |

- Eşik FPS ≥ 15 (ort ≥ 12): □ GEÇTİ □ KALDI
- Eşik latency ≤ 60 ms (maks ≤ 120): □ GEÇTİ □ KALDI

### MLP Landmark
| t=10s | t=20s | t=30s | t=40s | t=50s | t=60s | Ort FPS | Min FPS | Maks FPS | Ort ms | Maks ms |
|---|---|---|---|---|---|---|---|---|---|---|
| | | | | | | | | | | |

- Eşik FPS ≥ 25 (ort ≥ 20): □ GEÇTİ □ KALDI
- Eşik latency ≤ 35 ms (maks ≤ 70): □ GEÇTİ □ KALDI

### BiLSTM Single
| t=10s | t=20s | t=30s | t=40s | t=50s | t=60s | Ort FPS | Min FPS | Maks FPS | Ort ms | Maks ms |
|---|---|---|---|---|---|---|---|---|---|---|
| | | | | | | | | | | |

- Eşik FPS ≥ 20 (ort ≥ 16): □ GEÇTİ □ KALDI
- Eşik latency ≤ 40 ms (maks ≤ 80): □ GEÇTİ □ KALDI

### BiLSTM Ensemble (x5)
| t=10s | t=20s | t=30s | t=40s | t=50s | t=60s | Ort FPS | Min FPS | Maks FPS | Ort ms | Maks ms |
|---|---|---|---|---|---|---|---|---|---|---|
| | | | | | | | | | | |

- Eşik FPS ≥ 12 (ort ≥ 9.6): □ GEÇTİ □ KALDI
- Eşik latency ≤ 60 ms (maks ≤ 120): □ GEÇTİ □ KALDI

---

## 5. UI / UX Regresyon

| # | Senaryo | Sonuç |
|---|---|---|
| 1 | Home → Letters → Words → Home turu (bottom bar highlight) | □ ✓ □ ✗ |
| 2 | Letters toggle EffNet↔MLP, ≤1 sn yeni tahmin | □ ✓ □ ✗ |
| 3 | Words toggle Single↔Ensemble, ≤1 sn yeni tahmin | □ ✓ □ ✗ |
| 4 | Ekran kilitle/aç, kamera tekrar başlıyor | □ ✓ □ ✗ |
| 5 | 30 sn arka plan, geri dön, kamera tekrar başlıyor | □ ✓ □ ✗ |
| 6 | Status bar bölgesinde beyaz şerit yok | □ ✓ □ ✗ |
| 7 | Ön kamera + landmark aynalaması tutarlı | □ ✓ □ ✗ |
| 8 | İzin ilk seferde red → tekrar isteme akışı | □ ✓ □ ✗ |

**Sonuç:** ___ / 8

---

## 6. Çıktı Dosyaları

- [ ] `manuel-test-kayit.mp4` (ekran kaydı) — yol:
- [ ] Letters screenshot (Top-3 paneli görünür) — yol:
- [ ] Words screenshot (Top-3 paneli görünür) — yol:
- [ ] Logcat extract — yol:

---

## 7. Genel Değerlendirme

**Smoke:** □ GEÇTİ □ KALDI
**Letters (her iki model):** □ GEÇTİ □ KALDI
**Words (her iki model):** □ GEÇTİ □ KALDI
**Performans (4 model):** □ GEÇTİ □ KALDI
**UI Regresyon:** □ GEÇTİ □ KALDI

**Proposal kabul kriteri ("tanınan harf/kelime ekrana yazılır; FPS ve latency ölçülür") karşılandı mı?** □ EVET □ HAYIR

**Bilinen sınırlamalar / teze yansıyacak notlar:**

- **Cold-start MediaPipe exception (geçmiş, çözüldü):** Geçmişte LIVE_STREAM modunda cold-start sırasında frame'ler monotonik olmayan timestamp ile geliyordu ve `MediaPipeException: smaller timestamp than processed timestamp` FATAL hatasına yol açıyordu. `lastSentTsMs` volatile guard + `detectAsync` etrafına `try/catch` ile fix uygulandı. **Bugünkü manuel testte ne UI etkisi ne de logcat'te yeni exception gözlemlendi.**

- **Cold-start süresi:** Uygulama açılışı ~4-5 sn (FAZ7'deki ≤ 3 sn hedefinin ~1-2 sn üstünde). MediaPipe CPU init süresi (GPU delegate'ten vazgeçilmesinin getirisi: kararlılık) ana sebep. Kamera ve tahmin akışı açılır açılmaz başlıyor.

- **Tek-kullanıcı OOD bulgusu (Letters):** Landmark-tabanlı MLP (%100 Top-1) piksel-tabanlı EfficientNet-B0'ı (%92.9 Top-1) tek-kullanıcı koşulunda geçti. Test set sonuçları (%99 vs %100) tersini gösteriyordu. MediaPipe landmark soyutlaması, ham görüntü piksellerine kıyasla ışık/arka plan/kamera farklarına karşı daha sağlam — bu, native demo için landmark-tabanlı modelleri tercih etmek için pratik bir argüman.

- **`nothing` sınıfı (pipeline davranışı):** `HandLandmarker` el algılamadığında classifier hiç çağrılmıyor; bu yüzden `nothing` doğrudan ölçülemiyor. Pratikte bu **doğru davranış** — el yokken false-positive üretilmiyor (robustness).

- **D ve K karışıklığı (yalnız EfficientNet):** D harfi yapıldığında EffNet K veya R diyor (güven ~%60), K harfi yapıldığında W diyor (güven ~%40). MLP'de bu karışıklık yok (ikisi de %100). ASL alfabesinde parmak şekli olarak benzer harfler, piksel-tabanlı modeli yanıltıyor.

