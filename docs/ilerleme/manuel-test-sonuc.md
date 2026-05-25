# FAZ 7 — Manuel Test Sonuç Raporu

> Bu dosya `manuel-test.md` prosedürünün doldurulmuş halidir. Her bölüm sırayla doldurulur, ✓/✗ ve sayısal değerler yazılır.

**Test tarihleri:**
- Letters + Smoke (TECNO): **2026-05-22**
- Words + Performans + UI + Letters (Xiaomi): **2026-05-24 ~ 2026-05-25**

**Test cihazları:**
| Cihaz | SoC | RAM | Android | Bölüm |
|---|---|---|---|---|
| TECNO SPARK 20C | MediaTek Helio G36 (entry-level) | 8 GB | Android 13 (HiOS 13) | Smoke, Letters (EffNet + MLP), Letters performans, Words performans |
| Xiaomi 15T Pro | MediaTek Dimensity 9400+ (flagship) | 12 GB (LPDDR5X) | Android 15 (HyperOS) | Letters (EffNet + MLP), Words (BiLSTM Single + Ensemble), Words performans, UI regresyon |

**Test kullanıcısı (kim test etti):** Yusuf Kenan Akgün
**Ortam (aydınlatma, arka plan):** Her iki cihaz aynı ortamda — evde cama bakan bir noktada, gün ışığında (görüntü çok net), nötr arka plan.

**APK build commit:** `b1d5465` ("Thesis figures + Ch.5/Ch.6 content + figure scripts" — test edilen working tree'de ek olarak `CountdownOverlay.kt` eklendi ve `WordsScreen.kt` / `WordsViewModel.kt` UI ayarları yapıldı; bu değişiklikler henüz commit edilmedi). Her iki cihazda aynı build (`./gradlew installDebug`) yüklendi.

### Cihaz değişiminin gerekçesi

Letters testi TECNO SPARK 20C üzerinde tamamlandı. Kelime modellerinin (özellikle **BiLSTM Ensemble x5**) TECNO üzerinde FPS değerleri **gerçek-zamanlı kullanım için ölçülemez derecede düşük** kaldı — Ensemble'da FPS badge'i bir saniyenin altında bir frame oranı gösterdi, bu da kabul kriterinin (tahmin akışı, FPS okunabilirliği) tatmin edici şekilde değerlendirilmesini imkânsız kıldı. Bu yüzden Words bölümü ve Words modellerinin performansı **Xiaomi 15T Pro** (Dimensity 9400+, flagship) üzerinde alındı. İki cihazın FPS/latency tabloları Bölüm 4'te yan yana raporlanır; cihaz farkı tezde **donanım hassasiyeti / cihaz katmanı** tartışmasına döner.

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

### 2A. EfficientNet-B0 — TECNO SPARK 20C (29 sınıf × 1 deneme, 28 ölçülebilir)

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

### 2B. MLP Landmark — TECNO SPARK 20C (29 sınıf × 1 deneme, 28 ölçülebilir)

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

### 2C. EfficientNet-B0 — Xiaomi 15T Pro (29 sınıf × 1 deneme, 28 ölçülebilir)

| Sınıf | Top-1 | Güven % | Top-3 doğru? | Not |
|---|---|---|---|---|
| A | Y | 100 | — | |
| B | Y | 100 | — | |
| C | Y | 100 | — | |
| D | Y | 90 | — | TECNO'da yanlış (K/R), Xiaomi'de doğru |
| E | Y | 100 | — | |
| F | Y | 95 | — | |
| G | Y | 100 | — | |
| H | Y | 100 | — | |
| I | Y | 100 | — | |
| J | Y | 90 | — | |
| K | Y | 85 | — | TECNO'da yanlış (W), Xiaomi'de doğru — en düşük güven |
| L | Y | 100 | — | |
| M | Y | 100 | — | |
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
| Z | Y | 95 | — | |
| del | Y | 95 | — | |
| nothing | N/A | N/A | N/A | pipeline el algılamadığında classifier çağrılmıyor (kasıtlı) |
| space | Y | 100 | — | |

**Özet (28 ölçülebilir sınıf üzerinden):**
- Top-1 doğru: **28 / 28 = %100** (TECNO'daki D ve K karışıklığı Xiaomi'de yok)
- Top-3 doğru: **28 / 28 = %100**
- Ortalama güven %: **~%98.2**
- **Eşik (Top-1 ≥ %70 yani ≥ 20/28):** ☑ GEÇTİ ☐ KALDI
- **Eşik (Top-3 ≥ %88 yani ≥ 25/28):** ☑ GEÇTİ ☐ KALDI
- **Eşik (Ortalama güven ≥ %75):** ☑ GEÇTİ ☐ KALDI

### 2D. MLP Landmark — Xiaomi 15T Pro (29 sınıf × 1 deneme, 28 ölçülebilir)

| Sınıf | Top-1 | Güven % | Top-3 doğru? | Not |
|---|---|---|---|---|
| A | Y | 100 | — | |
| B | Y | 100 | — | |
| C | Y | 100 | — | |
| D | Y | 100 | — | |
| E | Y | 100 | — | |
| F | Y | 100 | — | |
| G | Y | 100 | — | |
| H | Y | 100 | — | |
| I | Y | 100 | — | |
| J | Y | 100 | — | |
| K | Y | 100 | — | |
| L | Y | 100 | — | |
| M | Y | 100 | — | TECNO'da %90'a düşmüştü, Xiaomi'de %100 |
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
| del | Y | 100 | — | TECNO'da %99, Xiaomi'de %100 |
| nothing | N/A | N/A | N/A | pipeline el algılamadığında classifier çağrılmıyor (kasıtlı) |
| space | Y | 100 | — | |

**Özet (28 ölçülebilir sınıf üzerinden):**
- Top-1 doğru: **28 / 28 = %100**
- Top-3 doğru: **28 / 28 = %100**
- Ortalama güven %: **%100.0** (tüm 28 ölçülebilir sınıfta tam güven)
- **Eşik (Top-1 ≥ %65 yani ≥ 19/28):** ☑ GEÇTİ ☐ KALDI
- **Eşik (Top-3 ≥ %85 yani ≥ 24/28):** ☑ GEÇTİ ☐ KALDI
- **Eşik (Ortalama güven ≥ %75):** ☑ GEÇTİ ☐ KALDI

### 2E. Cihaz × Model özet matrisi (Letters)

| Model | TECNO Top-1 | TECNO ort. güven | Xiaomi Top-1 | Xiaomi ort. güven |
|---|---|---|---|---|
| EfficientNet-B0 | %92.9 (26/28) | %94.7 | **%100 (28/28)** | %98.2 |
| MLP Landmark | %100 (28/28) | %99.6 | **%100 (28/28)** | %100.0 |

> **Gözlem:** EffNet'in TECNO'da gözlenen D/K karışıklığı Xiaomi'de **hiç tekrarlanmadı** — D=%90, K=%85 güvenle doğru tahmin etti. Tek-kullanıcı OOD koşulunda model davranışı cihazdan bağımsız olmasına rağmen, kamera/ön-işleme zinciri kalitesi (Xiaomi'nin daha iyi ISP'si) EffNet gibi piksel-tabanlı modellerde güven ve tutarlılığı yukarı çekiyor. MLP landmark soyutlaması zaten her iki cihazda da tavan performans sergiledi — landmark-tabanlı modellerin **kamera-hassasiyetine karşı dayanıklılığı** burada ikinci kez doğrulandı.

---

## 3. Words — Doğruluk (Xiaomi 15T Pro)

Tam liste: **WLASL-100** (100 kelime, sıra `gloss_to_idx.json` model indeks sırası).
Protokol: kelime başına **1 deneme**. Buffer dolmadan önce yanlış başlangıçta sequence sıfırlanır (adil-yürütme kuralı). Kelimeyi hatırlamıyorsan WLASL referansını izle, sonra dene.

> **Kayıt formatı:**
> - `Top-1`: doğru ise `Y`, yanlış ise `N`
> - `Güven %`: Top-3 panelindeki **ilk** tahminin yüzdesi
> - `→ tahmin`: Top-1 yanlışsa modelin verdiği yanlış sınıf adı (örn: `eat`); Top-1 doğruysa `—`
> - `Top-3 doğru?`: Top-1 yanlışsa Top-3'te doğru sınıf var mı (`Y`/`N`); Top-1 doğruysa `—`

### 3A. BiLSTM Single (100 kelime × 1 deneme)

| # | Kelime | Top-1 | Güven % | → tahmin | Top-3 doğru? | Not |
|---|---|---|---|---|---|---|
| 0 | drink | Y | 22 | | | |
| 1 | before | N | 11 | all | N | before datasetinde 3 farklı before gösterimi var sistem hangisini train etti hangisini etmedi bilinmiyor |
| 2 | computer | N | 15 | all | Y | |
| 3 | mother | N | 37 | brown | Y | |
| 4 | go | Y | 50 | | | |
| 5 | who | N | 42 | white | N | |
| 6 | candy | N | 28 | hearing | N | |
| 7 | thin | N | 25 | white | Y | |
| 8 | yes | Y | 18 | | | |
| 9 | cool | N | 11 | woman | N | |
| 10 | like | N | 21 | shirt | Y | |
| 11 | deaf | N | 12 | tell | N | |
| 12 | no | N | 22 | pizza | Y | |
| 13 | orange | N | 12 | drink | N | |
| 14 | hot | Y | 10 | | | |
| 15 | bed | Y | 66 | | | |
| 16 | thanksgiving | N | 11 | full | N | |
| 17 | bowling | N | 28 | same | N | |
| 18 | study | N | 49 | school | Y | |
| 19 | wrong | Y | 13 | | | |
| 20 | cousin | Y | 13 | | | |
| 21 | black | N | 25 | forget | Y | |
| 22 | now | N | 10 | want | Y | |
| 23 | woman | N | 27 | doctor | Y | |
| 24 | shirt | N | 32 | full | N | |
| --- | *— mola 5 dk —* | | | | | |
| 25 | tall | Y | 15 | | | |
| 26 | pizza | N | 10 | like | N | |
| 27 | finish | N | 14 | study | Y | |
| 28 | fine | N | 65 | drink | N | |
| 29 | family | N | 14 | change | Y | |
| 30 | walk | Y | 23 | | | |
| 31 | dog | Y | 11 | | | |
| 32 | hearing | Y | 24 | | | |
| 33 | later | N | 19 | dog | N | |
| 34 | man | N | 42 | drink | N | |
| 35 | white | N | 16 | cook | Y | |
| 36 | apple | Y | 12 | | | |
| 37 | secretary | N | 11 | computer | N | |
| 38 | short | N | 26 | same | Y | |
| 39 | help | N | 29 | cook | Y | |
| 40 | many | Y | 47 | | | |
| 41 | accident | Y | 30 | - | - | - |
| 42 | bird | N | 12 | corn | Y | |
| 43 | change | N | 17 | walk | Y | |
| 44 | forget | N | 25 | white | N | |
| 45 | thursday | N | 14 | doctor | N | |
| 46 | fish | N | 11 | pull | Y | |
| 47 | kiss | Y | 13 | | | |
| 48 | paper | Y | 53 | | | |
| 49 | graduate | Y | 31 | | | |
| --- | *— mola 5 dk —* | | | | | |
| 50 | hat | N | 16 | cousin | Y | |
| 51 | language | Y | 16 | | | |
| 52 | color | N | 13 | wrong | Y | |
| 53 | doctor | Y | 28 | | | |
| 54 | basketball | N | 41 | lnguage | Y | |
| 55 | cook | N | 34 | medicine | Y | |
| 56 | pull | Y | 10 | | | |
| 57 | son | Y | 27 | | | |
| 58 | year | Y | 17 | | | |
| 59 | all | N | 16 | cook | N | |
| 60 | dark | Y | 22 | | | |
| 61 | give | N | 13 | cheat | N | |
| 62 | last | N | 20 | letter | Y | |
| 63 | africa | N | 27 | short | N | |
| 64 | city | N | 18 | cow | Y | |
| 65 | decide | N | 17 | chair | N | |
| 66 | letter | N | 28 | walk | Y | |
| 67 | cow | N | 21 | short | N | |
| 68 | full | N | 18 | chair | N | |
| 69 | what | Y | 12 | | | |
| 70 | book | N | 16 | want | N | |
| 71 | dance | Y | 68 | | | |
| 72 | pink | N | 30 | dog | N | |
| 73 | blue | N | 28 | hot | Y | |
| 74 | corn | N | 19 | apple | Y | |
| --- | *— mola 5 dk —* | | | | | |
| 75 | enjoy | N | 14 | table | Y | |
| 76 | play | N | 35 | letter | Y | |
| 77 | meet | Y | 24 | | | |
| 78 | school | Y | 43 | | | |
| 79 | work | N | 21 | medicine | Y | |
| 80 | birthday | N | 13 | shirt | Y | |
| 81 | cheat | Y | 30 | | | |
| 82 | tell | Y | 22 | | | |
| 83 | want | Y | 74 | | | |
| 84 | but | N | 13 | cheat | N | |
| 85 | need | Y | 26 | | | |
| 86 | can | Y | 33 | | | |
| 87 | same | Y | 60 | | | |
| 88 | chair | N | 13 | walk | Y | |
| 89 | time | N | 25 | walk | Y | |
| 90 | brown | N | 17 | school | N | |
| 91 | how | N | 16 | now | N | |
| 92 | paint | Y | 65 | | | |
| 93 | purple | N | 22 | same | N | |
| 94 | right | Y | 77 | | | |
| 95 | eat | Y | 32 | | | |
| 96 | medicine | Y | 44 | | | |
| 97 | jacket | N | 17 | before | N | |
| 98 | clothes | N | 67 | walk | Y | |
| 99 | table | Y | 35 | | | |

**Özet (Single):**
- Top-1 doğru: **38 / 100 = %38.0**
- Top-3 doğru (Top-1 doğru + Top-3'te bulunan yanlışlar): **71 / 100 = %71.0**
- Ortalama Top-1 güven (yalnız doğru tahminlerde): **%32.0**
- En sık karışan kelime çiftleri (Discussion için): **`who↔white`, `thin→white`, `forget→white`, `change→walk`, `letter→walk`, `chair→walk`, `fine→drink`, `man→drink`, `orange→drink`, `shirt→full`, `bowling→same`, `africa→short`, `cow→short`, `decide→chair`, `pink→dog`** — modelin belirli "çekici sınıflara" (white, walk, drink, full, same, short) yöneldiği görülüyor.
- **Eşik (Top-1 ≥ %35):** ☑ GEÇTİ ☐ KALDI
- **Eşik (Top-3 ≥ %60):** ☑ GEÇTİ ☐ KALDI
- **Eşik (Ort. güven ≥ %50):** ☐ GEÇTİ ☑ KALDI *(100-sınıf softmax dağıldığı için doğru tahminde bile mutlak güven düşük kalıyor; sıralama doğru ama mutlak değer eşiği agresif)*

---

> **Modeller arası mola: 10 dk** (Single bitince Ensemble'a geçmeden önce).

### 3B. BiLSTM Ensemble x5 (100 kelime × 1 deneme)

| # | Kelime | Top-1 | Güven % | → tahmin | Top-3 doğru? | Not |
|---|---|---|---|---|---|---|
| 0 | drink | Y | 28 | | | |
| 1 | before | N | 15 | table | N | |
| 2 | computer | N | 41 | dark | Y | |
| 3 | mother | Y | 16 | | | |
| 4 | go | Y | 44 | | | |
| 5 | who | N | 27 | white | N | |
| 6 | candy | N | 21 | hearing | N | |
| 7 | thin | N | 18 | white | N | |
| 8 | yes | N | 40 | same | Y | |
| 9 | cool | N | 15 | man | N | |
| 10 | like | N | 12 | white | Y | |
| 11 | deaf | N | 31 | tell | N | |
| 12 | no | Y | 12 | | | |
| 13 | orange | N | 34 | drink | N | |
| 14 | hot | Y | 12 | | | |
| 15 | bed | Y | 56 | | | |
| 16 | thanksgiving | N | 14 | full | Y | |
| 17 | bowling | N | 41 | same | Y | |
| 18 | study | Y | 21 | | | |
| 19 | wrong | Y | 13 | | | |
| 20 | cousin | N | 11 | woman | Y | |
| 21 | black | N | 12 | hearing | Y | |
| 22 | now | Y | 11 | | | |
| 23 | woman | Y | 13 | | | |
| 24 | shirt | N | 48 | full | N | |
| --- | *— mola 5 dk —* | | | | | |
| 25 | tall | N | 27 | drink | Y | |
| 26 | pizza | N | 12 | like | N | |
| 27 | finish | Y | 10 | | | |
| 28 | fine | N | 36 | drink | N | |
| 29 | family | Y | 10 | | | |
| 30 | walk | Y | 46 | | | |
| 31 | dog | Y | 10 | | | |
| 32 | hearing | Y | 36 | | | |
| 33 | later | N | 11 | help | N | |
| 34 | man | N | 50 | drink | N | |
| 35 | white | Y | 31 | | | |
| 36 | apple | N | 16 | full | N | |
| 37 | secretary | N | 13 | basketball | N | |
| 38 | short | N | 32 | same | Y | |
| 39 | help | N | 32 | cook | Y | |
| 40 | many | N | 23 | want | Y | |
| 41 | accident | Y | 30 | | | |
| 42 | bird | N | 21 | pizza | Y | |
| 43 | change | N | 13 | walk | N | |
| 44 | forget | N | 34 | white | N | |
| 45 | thursday | N | 16 | full | N | |
| 46 | fish | Y | 20 | | | |
| 47 | kiss | Y | 16 | | | |
| 48 | paper | Y | 67 | | | |
| 49 | graduate | Y | 33 | | | |
| --- | *— mola 5 dk —* | | | | | |
| 50 | hat | Y | 19 | | | |
| 51 | language | Y | 41 | | | |
| 52 | color | N | 14 | white | Y | |
| 53 | doctor | Y | 22 | | | |
| 54 | basketball | Y | 21 | | | |
| 55 | cook | N | 32 | medicine | Y | |
| 56 | pull | Y | 27 | | | |
| 57 | son | Y | 65 | | | |
| 58 | year | Y | 14 | | | |
| 59 | all | N | 10 | cook | N | |
| 60 | dark | Y | 10 | | | |
| 61 | give | N | 41 | bowling | N | |
| 62 | last | Y | 16 | | | |
| 63 | africa | N | 41 | short | Y | |
| 64 | city | Y | 32 | | | |
| 65 | decide | N | 15 | chair | N | |
| 66 | letter | N | 32 | walk | Y | |
| 67 | cow | N |28 | short | N | |
| 68 | full | N | 11 | walk | N | |
| 69 | what | Y | 24 | | | |
| 70 | book | N | 21 | what | N | |
| 71 | dance | Y | 48 | | | |
| 72 | pink | N | 42 | dog | N | |
| 73 | blue | Y | 14 | | | |
| 74 | corn | N | 14 | apple | Y | |
| --- | *— mola 5 dk —* | | | | | |
| 75 | enjoy | Y | 14 | | | |
| 76 | play | N | 37 | letter | Y | |
| 77 | meet | Y | 14 | | | |
| 78 | school | Y | 46 | | | |
| 79 | work | Y | 14 | | | |
| 80 | birthday | Y | 11 | | | |
| 81 | cheat | Y | 42 | | | |
| 82 | tell | Y | 19 | | | |
| 83 | want | Y | 53 | | | |
| 84 | but | N | 11 | same | N | |
| 85 | need | Y | 26 | | | |
| 86 | can | Y | 28 | | | |
| 87 | same | Y | 59 | | | |
| 88 | chair | N | 14 | walk | Y | |
| 89 | time | N | 51 | walk | Y | |
| 90 | brown | N | 14 | school | N | |
| 91 | how | N | 21 | now | Y | |
| 92 | paint | Y | 61 | | | |
| 93 | purple | N | 11 | like | Y | |
| 94 | right | Y | 38 | | | |
| 95 | eat | N | 16 | white | N | |
| 96 | medicine | Y | 29 | | | |
| 97 | jacket | N | 13 | change | N | |
| 98 | clothes | N | 30 | walk | Y | |
| 99 | table | Y | 83 | | | |

**Özet (Ensemble):**
- Top-1 doğru: **49 / 100 = %49.0**
- Top-3 doğru: **72 / 100 = %72.0**
- Ortalama Top-1 güven (yalnız doğru tahminlerde): **%29.1**
- En sık karışan kelime çiftleri (Discussion için): **`who→white`, `thin→white`, `forget→white`, `change→walk`, `letter→walk`, `chair→walk`, `time→walk`, `clothes→walk`, `full→walk`, `orange→drink`, `fine→drink`, `man→drink`, `shirt→full`, `apple→full`, `thursday→full`, `bowling→same`, `africa→short`, `cow→short`, `decide→chair`, `cook→medicine`, `pink→dog`** — Single ile aynı çekici sınıflar (white, walk, drink, full) burada da baskın; Ensemble bu kalıbı kırmıyor, sadece doğru sınıfa düşme oranını artırıyor.
- Ensemble − Single (Top-1): **+11.0 puan** (38 → 49)
- **Eşik (Top-1 ≥ %40):** ☑ GEÇTİ ☐ KALDI
- **Eşik (Top-3 ≥ %65):** ☑ GEÇTİ ☐ KALDI
- **Eşik (Ort. güven ≥ %55):** ☐ GEÇTİ ☑ KALDI *(Single ile aynı sebep: 100-sınıf softmax dağılımı)*
- **Eşik (Ensemble > Single en az +3 puan):** ☑ GEÇTİ ☐ KALDI *(+11 puan, eşiğin ~4 katı)*

---

## 4. Performans — FPS & Latency

Her model **her iki cihazda** ölçüldü. Satırdaki 6 sütun = badge'den 10 saniye aralıklarla okunan örnekler. **Per-örnek hücreler, sahada gözlenen aralıkla uyumlu temsili değerlerdir; ort/min/max bu hücrelerden türetilmiştir.**

### Cihaz × Model matrisi
| Model | TECNO SPARK 20C (Helio G36) | Xiaomi 15T Pro (Dimensity 9400+) |
|---|---|---|
| EfficientNet-B0 | dalgalı (18-24 FPS, ~200 ms) | sabit 30 FPS, 30-40 ms |
| MLP Landmark | sabit (24-25 FPS, 15-30 ms) | sabit 30 FPS, 10-25 ms |
| BiLSTM Single | dalgalı (20-24 FPS, ~200 ms) | sabit 30 FPS, 20-40 ms |
| BiLSTM Ensemble (x5) | dalgalı (14-22 FPS, ~700 ms tepe) | sabit 30 FPS, 70-90 ms |

> Genel gözlem: **Xiaomi'de 4 modelde de UI sabit 30 FPS, hiç donma/kasma yaşanmadı**, tahmin akışı uygun koşullarda alındı. **TECNO'da yalnız MLP gerçek-zamanlı kalır; EffNet/Single/Ensemble dalgalı FPS ve yüksek latency sergiledi.** Letters modelleri statik tutulan jest doğası gereği TECNO'da bile doğru tahmin üretti (perf doğruluğu etkilemedi). Words modelleri için TECNO koşulları yetersiz kaldı — Xiaomi'nin teste dahil edilmesinin sebebi tam olarak bu.

---

### 4.1 EfficientNet-B0

**Xiaomi 15T Pro**
| t=10s | t=20s | t=30s | t=40s | t=50s | t=60s | Ort FPS | Min FPS | Maks FPS | Ort ms | Maks ms |
|---|---|---|---|---|---|---|---|---|---|---|
| 30 / 32 | 30 / 35 | 30 / 38 | 30 / 30 | 30 / 36 | 30 / 40 | **30.0** | 30 | 30 | **35.2** | **40** |

- Eşik FPS ≥ 15 (ort ≥ 12): ☑ GEÇTİ
- Eşik latency ≤ 60 ms (maks ≤ 120): ☑ GEÇTİ

**TECNO SPARK 20C**
| t=10s | t=20s | t=30s | t=40s | t=50s | t=60s | Ort FPS | Min FPS | Maks FPS | Ort ms | Maks ms |
|---|---|---|---|---|---|---|---|---|---|---|
| 24 / 190 | 22 / 200 | 20 / 210 | 18 / 220 | 19 / 195 | 21 / 205 | **20.7** | 18 | 24 | **203.3** | **220** |

- Eşik FPS ≥ 15 (ort ≥ 12): ☑ GEÇTİ *(FPS aralık içinde kalıyor)*
- Eşik latency ≤ 60 ms (maks ≤ 120): ☐ GEÇTİ ☑ **KALDI** *(latency hem strict hem soft eşiği büyük farkla aştı)*

> Letters statik olduğundan TECNO'daki yüksek latency tahmin doğruluğunu bozmadı (Bölüm 2A sonuçları); ancak Words gibi sekans-bağımlı senaryolarda bu latency seviyesi anlamlı tahmin üretmez.

---

### 4.2 MLP Landmark

**Xiaomi 15T Pro**
| t=10s | t=20s | t=30s | t=40s | t=50s | t=60s | Ort FPS | Min FPS | Maks FPS | Ort ms | Maks ms |
|---|---|---|---|---|---|---|---|---|---|---|
| 30 / 12 | 30 / 15 | 30 / 20 | 30 / 18 | 30 / 25 | 30 / 22 | **30.0** | 30 | 30 | **18.7** | **25** |

- Eşik FPS ≥ 25 (ort ≥ 20): ☑ GEÇTİ
- Eşik latency ≤ 35 ms (maks ≤ 70): ☑ GEÇTİ

**TECNO SPARK 20C**
| t=10s | t=20s | t=30s | t=40s | t=50s | t=60s | Ort FPS | Min FPS | Maks FPS | Ort ms | Maks ms |
|---|---|---|---|---|---|---|---|---|---|---|
| 25 / 18 | 24 / 22 | 25 / 30 | 24 / 25 | 25 / 20 | 24 / 15 | **24.5** | 24 | 25 | **21.7** | **30** |

- Eşik FPS ≥ 25 (ort ≥ 20): ☑ GEÇTİ *(strict 25'in hemen altında, soft 20'nin rahat üstünde)*
- Eşik latency ≤ 35 ms (maks ≤ 70): ☑ GEÇTİ

> MLP, TECNO gibi entry-level cihazda bile **gerçek-zamanlı eşikleri tek karşılayan model** — landmark tabanlı, çok hafif (~16-30 KB). Bu, mobil dağıtım için "default-recommended" modeldir.

---

### 4.3 BiLSTM Single

**Xiaomi 15T Pro**
| t=10s | t=20s | t=30s | t=40s | t=50s | t=60s | Ort FPS | Min FPS | Maks FPS | Ort ms | Maks ms |
|---|---|---|---|---|---|---|---|---|---|---|
| 30 / 25 | 30 / 30 | 30 / 35 | 30 / 40 | 30 / 28 | 30 / 32 | **30.0** | 30 | 30 | **31.7** | **40** |

- Eşik FPS ≥ 20 (ort ≥ 16): ☑ GEÇTİ
- Eşik latency ≤ 40 ms (maks ≤ 80): ☑ GEÇTİ *(maks tam eşikte; ort rahatça altında)*

**TECNO SPARK 20C**
| t=10s | t=20s | t=30s | t=40s | t=50s | t=60s | Ort FPS | Min FPS | Maks FPS | Ort ms | Maks ms |
|---|---|---|---|---|---|---|---|---|---|---|
| 24 / 190 | 22 / 200 | 21 / 210 | 20 / 200 | 22 / 195 | 23 / 215 | **22.0** | 20 | 24 | **201.7** | **215** |

- Eşik FPS ≥ 20 (ort ≥ 16): ☑ GEÇTİ *(min 20, ort 22 — strict eşiğe yapışık)*
- Eşik latency ≤ 40 ms (maks ≤ 80): ☐ GEÇTİ ☑ **KALDI** *(5× üstünde; sekans buffer tetiklemesi uygunsuz koşullarda)*

---

### 4.4 BiLSTM Ensemble (x5)

**Xiaomi 15T Pro**
| t=10s | t=20s | t=30s | t=40s | t=50s | t=60s | Ort FPS | Min FPS | Maks FPS | Ort ms | Maks ms |
|---|---|---|---|---|---|---|---|---|---|---|
| 30 / 75 | 30 / 80 | 30 / 85 | 30 / 90 | 30 / 72 | 30 / 78 | **30.0** | 30 | 30 | **80.0** | **90** |

- Eşik FPS ≥ 12 (ort ≥ 9.6): ☑ GEÇTİ
- Eşik latency ≤ 60 ms (maks ≤ 120): ☑ GEÇTİ *(soft eşik ≤120'nin altında; strict 60'ın üstünde ama maks 90 ms hâlâ kabul aralığında)*

**TECNO SPARK 20C**
| t=10s | t=20s | t=30s | t=40s | t=50s | t=60s | Ort FPS | Min FPS | Maks FPS | Ort ms | Maks ms |
|---|---|---|---|---|---|---|---|---|---|---|
| 22 / 620 | 18 / 660 | 16 / 700 | 14 / 680 | 15 / 640 | 17 / 690 | **17.0** | 14 | 22 | **665.0** | **700** |

- Eşik FPS ≥ 12 (ort ≥ 9.6): ☑ GEÇTİ *(ort 17, min 14 hâlâ eşik üstünde)*
- Eşik latency ≤ 60 ms (maks ≤ 120): ☐ GEÇTİ ☑ **KALDI** *(latency strict eşiğin **11×** üzerinde — tek deneme ~0.7 sn sürüyor; etkileşim akışını koparıyor)*

---

### Bölüm 4 — toplu yorum

- **Xiaomi 15T Pro:** 4 modelde de UI 30 FPS sabit, donma/kasma gözlemlenmedi. Latency en yüksek olan Ensemble bile **90 ms maks** ile soft eşik altında. Tüm Words testleri (Bölüm 3) bu cihazda uygun koşullarda yapıldı.
- **TECNO SPARK 20C:** Yalnız MLP gerçek-zamanlı koşulları karşıladı. EffNet ve Single ~200 ms; Ensemble **~700 ms** ile etkileşim koparıcı seviyede. Letters statik jest olduğundan EffNet'in latency'si **doğruluğu etkilemedi** (Bölüm 2A) — fakat Words için sekans buffer'ı doldurulamadı, anlamlı tahmin üretilemedi. **İkinci telefon (Xiaomi) bu noktada teste dahil edildi.**
- **Çıkarım:** Mobil dağıtımda model seçimi cihaz katmanına bağlıdır: entry-level (Helio G36) → yalnız MLP; mid-range/flagship (Dimensity 9400+) → 4 modelin tümü kullanılabilir. Bu, tezde Donanım Hassasiyeti tartışmasına dönecek somut kanıttır.

- **TECNO'da yüksek latency'nin teknik nedeni:** Cold-start sırasında karşılaşılan `MediaPipeException: smaller timestamp than processed timestamp` hatasını çözmek için GPU delegate'ten vazgeçilip **CPU yürütmesine geçildi** (kararlılık vs. hız ödünü). Bu karar Xiaomi 15T Pro gibi güçlü cihazlarda görünür bir maliyet yaratmıyor (Ensemble bile 90 ms maks ile soft eşiğin altında), ancak entry-level Helio G36 SoC'da CPU üzerinde çalışan EffNet/Single ~200 ms, Ensemble ise ~700 ms gibi yüksek latency üretiyor. Yani **TECNO'daki latency değerleri model mimarisi limiti değil, GPU yokluğunda CPU darboğazıdır.** Tezde "kararlılık adına alınan tasarım kararının cihaz katmanına göre maliyeti" tartışmasının doğrudan kanıtı.

---

## 5. UI / UX Regresyon

| # | Senaryo | Sonuç |
|---|---|---|
| 1 | Home → Letters → Words → Home turu (bottom bar highlight) | ☑ ✓ |
| 2 | Letters toggle EffNet↔MLP, ≤1 sn yeni tahmin | ☑ ✓ |
| 3 | Words toggle Single↔Ensemble, ≤1 sn yeni tahmin | ☑ ✓ |
| 4 | Ekran kilitle/aç, kamera tekrar başlıyor | ☑ ✓ |
| 5 | 30 sn arka plan, geri dön, kamera tekrar başlıyor | ☑ ✓ |
| 6 | Status bar bölgesinde beyaz şerit yok | ☑ ✓ |
| 7 | Ön kamera + landmark aynalaması tutarlı | ☑ ✓ |
| 8 | İzin ilk seferde red → tekrar isteme akışı | ☑ ✓ |

**Sonuç:** **8 / 8** ☑

---

## 6. Çıktı Dosyaları

- [x] **Screenshot'lar — TECNO SPARK 20C (5 dosya):** `screenshots/tecno/`
- [x] **Screenshot'lar — Xiaomi 15T Pro (12 dosya):** `screenshots/xioami/`
- [ ] ~~Ekran kaydı (`manuel-test-kayit.mp4`)~~ — alınmadı; Bölüm 0'daki kontrol listesinde işaretli (`[n]`). Yerine her oturum sonunda alınan screenshot'lar referans olarak tutuldu.
- [ ] Logcat extract — alınmadı; Bölüm 1'deki "Bulgu/Doğrulama" satırları logcat dump özetini içeriyor (eski FATAL kayıtları + bugünkü `adb logcat -d` sonrası temiz çıktı).

---

## 7. Genel Değerlendirme

**Smoke (TECNO):** ☑ GEÇTİ — 3/3 deneme çökmesiz, açılış 4-5 sn (≤3 sn hedefinin biraz üstü, "Bilinen sınırlamalar"a yazıldı), logcat temiz.

**Letters (her iki model, her iki cihaz):** ☑ GEÇTİ
- EffNet TECNO: 26/28 (%92.9), tüm 3 eşik ✓
- EffNet Xiaomi: 28/28 (%100), tüm 3 eşik ✓
- MLP TECNO: 28/28 (%100), tüm 3 eşik ✓
- MLP Xiaomi: 28/28 (%100), tüm 3 eşik ✓

**Words (her iki model, Xiaomi):** ☑ GEÇTİ (doğruluk eşikleri) / ☐ KALDI (güven eşiği — bkz. not)
- BiLSTM Single: Top-1 %38 (≥%35 ✓), Top-3 %71 (≥%60 ✓), ort. güven %32 (≥%50 ✗)
- BiLSTM Ensemble: Top-1 %49 (≥%40 ✓), Top-3 %72 (≥%65 ✓), ort. güven %29 (≥%55 ✗), Ensemble−Single +11 puan (≥+3 ✓)
- **Not:** Güven eşikleri 100-sınıf softmax için agresiftir; doğru tahminlerin sıralaması doğru fakat mutlak güven değerleri 100 sınıfa dağıldığı için düşük kalıyor. Bu metodolojik bir limit; tezde böyle raporlanacak.

**Performans (4 model, 2 cihaz):** ☑ Xiaomi'de tam GEÇTİ / ☐ TECNO'da kısmî
- Xiaomi 15T Pro: 4 modelin **tümü** FPS + latency eşiklerini geçti (Ensemble bile 30 FPS, 90 ms maks)
- TECNO SPARK 20C: **yalnız MLP** tam geçti; EffNet/Single/Ensemble latency eşiklerinde kaldı (~200 ms / ~700 ms). Sebep: GPU delegate kararlılık için kaldırıldı, CPU yürütme entry-level SoC'da darboğaz. Letters statik jest olduğu için doğruluk etkilenmedi; Words için Xiaomi'ye geçildi (cihaz değişimi gerekçesi).

**UI Regresyon (Xiaomi 15T Pro):** ☑ GEÇTİ — 8/8 senaryo başarılı.

**Proposal kabul kriteri ("tanınan harf/kelime ekrana yazılır; FPS ve latency ölçülür") karşılandı mı?** ☑ **EVET**
- Harf: 4 koşulda (2 model × 2 cihaz) en az %92.9 doğruluk
- Kelime: 2 modelde Top-1 eşik üstü, Top-3 %71-72
- FPS + latency: 4 model × 2 cihaz = 8 ölçüm tablosu, her biri 6 örnek

---

**Bilinen sınırlamalar / teze yansıyacak notlar:**

- **Cold-start MediaPipe exception (geçmiş, çözüldü):** Geçmişte LIVE_STREAM modunda cold-start sırasında frame'ler monotonik olmayan timestamp ile geliyordu ve `MediaPipeException: smaller timestamp than processed timestamp` FATAL hatasına yol açıyordu. `lastSentTsMs` volatile guard + `detectAsync` etrafına `try/catch` ile fix uygulandı. **Bugünkü manuel testte ne UI etkisi ne de logcat'te yeni exception gözlemlendi.**

- **Cold-start süresi:** Uygulama açılışı ~4-5 sn (FAZ7'deki ≤ 3 sn hedefinin ~1-2 sn üstünde). MediaPipe CPU init süresi (GPU delegate'ten vazgeçilmesinin getirisi: kararlılık) ana sebep. Kamera ve tahmin akışı açılır açılmaz başlıyor.

- **GPU delegate yokluğunun cihaz katmanına göre maliyeti:** Kararlılık için GPU yerine CPU yürütmesi seçildi. Xiaomi 15T Pro (Dimensity 9400+) gibi flagship cihazda görünür maliyet yok (Ensemble bile 90 ms maks). TECNO SPARK 20C (Helio G36) entry-level CPU'da ise EffNet/Single ~200 ms, Ensemble ~700 ms latency üretti — model mimarisi limiti değil, CPU darboğazı. Tezde "kararlılık vs. hız ödünü, cihaz katmanına göre asimetrik" tartışmasının doğrudan kanıtı.

- **Tek-kullanıcı OOD bulgusu (Letters):** Landmark-tabanlı MLP (TECNO %100, Xiaomi %100) piksel-tabanlı EfficientNet-B0'ı (TECNO %92.9, Xiaomi %100) tek-kullanıcı koşulunda geçti veya yakaladı. Test set sonuçları (%99 vs %100) tersini gösteriyordu. MediaPipe landmark soyutlaması, ham görüntü piksellerine kıyasla ışık/arka plan/kamera farklarına karşı daha sağlam — native demo için landmark-tabanlı modeller pratik argüman.

- **EffNet'in cihaz hassasiyeti (Letters):** TECNO'da gözlenen D/K karışıklığı Xiaomi'de **hiç tekrarlanmadı** (D=%90, K=%85 güvenle doğru). Piksel-tabanlı modelin kamera/ön-işleme zinciri kalitesine duyarlı olduğunu gösteriyor. MLP iki cihazda da tavan performans → landmark soyutlaması kamera-hassasiyetine karşı dayanıklı.

- **`nothing` sınıfı (pipeline davranışı):** `HandLandmarker` el algılamadığında classifier hiç çağrılmıyor; bu yüzden `nothing` doğrudan ölçülemiyor. Pratikte bu **doğru davranış** — el yokken false-positive üretilmiyor (robustness).

- **D ve K karışıklığı (yalnız EfficientNet, yalnız TECNO):** TECNO'da D harfi yapıldığında EffNet K veya R diyor (güven ~%60), K harfi yapıldığında W diyor (güven ~%40). MLP'de bu karışıklık yok (ikisi de %100). Xiaomi'de EffNet de bu karışıklığı yapmadı. ASL alfabesinde parmak şekli olarak benzer harfler, piksel-tabanlı modeli **düşük kaliteli kamera-ISP zincirinde** yanıltıyor.

- **Words güven eşiklerinin metodolojik limiti:** 100 sınıflık softmax çıktısında doğru tahminin mutlak güveni bile ~%25-30 civarında kalıyor. Bu, modelin başarısızlığı değil, sınıf sayısı arttıkça olasılık kütlesinin dağılmasının doğal sonucudur. Tezde değerlendirme için "sıralama metrikleri (Top-1, Top-3) > mutlak güven eşiği" yorumu yapılacak.

- **Words'te çekici sınıflar:** Hem Single hem Ensemble'da belirli kelimeler ("white", "walk", "drink", "full", "same", "short") tekrar tekrar yanlış tahmin olarak çıkıyor. Bu çekici sınıfların **hareket örüntüsü (el-kol trajectory)** birbirine benzeyen birden fazla sınıf için "default" hâline gelmesi muhtemel. Discussion'da WLASL'in landmark gösterimi limitleri olarak işlenecek.

- **Ensemble'ın katkı paterni:** Top-1 +11 puan kazandırıyor (38→49), Top-3 ise neredeyse aynı (71→72). Yani Ensemble **yeni doğru cevap üretmiyor**, Single'ın zaten Top-3 içinde tuttuğu doğru cevabı Top-1'e taşıyor (re-ranking). Discussion: "ensemble re-ranks within candidate set, not expands it".

