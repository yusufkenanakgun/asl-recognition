# FAZ 7 — Manuel Test Planı

Tarih (planlanan): kullanıcı uygun olduğunda
Amaç: Native Android demo uygulamasının proposal'da tanımlanan **"tanınan harf/kelime ekrana yazılır; FPS ve latency ölçülür"** kabul kriterini gerçek cihazda doğrulamak.

> Bu doküman bir **test prosedürü** + **başarı kriterleri** listesidir. Otomatik test değil — kullanıcının cihazda elle uygulayacağı senaryolar.

---

## 0. Hazırlık (test başlamadan önce, 1 kere)

- [ ] Cihazda **wireless ADB** açık (`adb devices` cihazı görüyor)
- [ ] Son APK yüklü: `.\gradlew installDebug`
- [ ] Cihazın şarjı ≥ %50, **Battery Saver kapalı** (CPU throttling olmasın)
- [ ] **Aydınlatma:** doğal gün ışığı veya en az iki noktadan beyaz LED — sahnede sert gölge olmamalı
- [ ] **Arka plan:** düz, tek renkli, elden farklı bir yüzey (duvar / beyaz panel)
- [ ] Kameraya el mesafesi: **30–50 cm**
- [ ] Test sırasında kayıt için: ekran kaydı (`adb shell screenrecord /sdcard/test.mp4`) veya cihazın kendi ekran kaydı açık
- [ ] Sonuçları tutmak için `docs/ilerleme/manuel-test-sonuc.md` boş şablon hazır

---

## 1. Smoke Test (her açılışta 1 kere — toplam 3 kere)

Amaç: uygulama soğuk açılışta çökmüyor, kameraya erişiyor, ilk frame'i çiziyor.

| Adım | Beklenen |
|---|---|
| 1. Uygulamayı baştan başlat (force-stop sonrası) | App ≤ 3 sn'de Home ekranına gelir |
| 2. Home'da iki action card'a sırayla bas | Sırasıyla Letters / Words sekmesine geçer |
| 3. Letters sekmesi açıldığında | ≤ 2 sn içinde kamera preview görünür, ≤ 1 sn sonra FPS badge > 0 olur |
| 4. Words sekmesinde aynı | Aynı |
| 5. 30 sn boyunca akış izle | Logcat'te `MediaPipeException` veya `FATAL` yok |

**Kriter:** 3 cold-start denemesinin **3/3'ü** geçmeli. 1 fail = bug.

---

## 2. Letters — Sembol-Bazlı Doğruluk Testi

24 statik harf (J ve Z hariç ASL alfabesi). İki model için ayrı.

### Prosedür
- Her harf için: kullanıcı doğru işareti yapar, **3 saniye sabit tutar**, ekrandaki Top-1 tahmini okunur.
- Her harfi **3 kez** tekrar et (toplam 24 × 3 = 72 deneme / model).
- Top-1 doğru ise ✓, değilse Top-3 içinde var mı kontrol et (✓3).

### Modeller
- [ ] **EfficientNet-B0** (24 harf × 3 = 72 deneme)
- [ ] **MLP Landmark** (24 harf × 3 = 72 deneme)

### Başarı kriteri

| Metrik | Eşik (EfficientNet) | Eşik (MLP) | Kaynak |
|---|---|---|---|
| Top-1 accuracy (manuel) | ≥ %80 | ≥ %75 | FAZ 3/4 test seti sonuçlarıyla tutarlı olmalı (gerçek cihazda 5–10 puan düşüş normal) |
| Top-3 accuracy | ≥ %92 | ≥ %88 | – |
| Kararlılık (aynı harf 3 deneme) | en az 2/3 tutarlı | en az 2/3 tutarlı | – |

> **Not:** Test setiyle aynı sayıyı beklemiyoruz. Manuel testte tek bir kullanıcı (kendi eli) test ediyor — bu hem dağılım dışı (out-of-distribution) hem de tek bir el morfolojisi. Hedef: "model gerçek dünyada çalışıyor mu" doğrulaması, "yeni accuracy değeri ölç" değil.

---

## 3. Words — Kelime-Bazlı Doğruluk Testi

Eğitilen kelime listesi (FAZ 6 — `models/lstm/labels.txt` veya benzeri). İki model için ayrı.

### Prosedür
- Her kelime için: doğal hızda işaret et (~1 sn süren bir hareket), buffer dolana kadar bekle (alt panelde sequence progress overlay biter).
- Her kelimeyi **3 kez** tekrar et.
- Top-1 doğruysa ✓, Top-3 içinde varsa ✓3.

### Modeller
- [ ] **BiLSTM Single** (N kelime × 3)
- [ ] **BiLSTM Ensemble (x5)** (N kelime × 3)

### Başarı kriteri

| Metrik | Eşik (Single) | Eşik (Ensemble) |
|---|---|---|
| Top-1 accuracy (manuel) | ≥ %50 | ≥ %60 |
| Top-3 accuracy | ≥ %75 | ≥ %85 |
| Ensemble > Single farkı | – | en az +5 puan Top-1 |

> Kelime modeli zaten test setinde harf modelinden düşük; manuel testte tek kişilik OOD koşulda **%50 üstü** sembolik bir hedef — proposal'ın "tanınıyor" şartı için yeterli.

---

## 4. Performans Testi — FPS & Latency

Proposal direkt şart koşuyor: *"FPS ve latency ölçülür"*.

### Prosedür
- Her model için Letters/Words sekmesinde **60 saniye boyunca** elini kameranın önünde tut (sabit harf / sabit kelime).
- Bu süre içinde FPS badge'i ekran kaydından **her 10 saniyede bir** okuyarak 6 örnek topla.
- Latency badge'inden aynı şekilde 6 örnek (ms).
- Ortalama + min + maks raporla.

### Başarı kriteri (RTX'siz orta seviye Android cihaz için)

| Model | FPS hedefi | Latency hedefi (ms) |
|---|---|---|
| MediaPipe HandLandmarker (CPU) | – | ≤ 35 |
| EfficientNet-B0 | ≥ 15 fps | ≤ 60 |
| MLP Landmark | ≥ 25 fps | ≤ 10 |
| BiLSTM Single | ≥ 20 fps | ≤ 25 |
| BiLSTM Ensemble | ≥ 12 fps | ≤ 50 |

**Geçer kriter:** her modelin **ortalama FPS'i hedefin en az %80'i** ve **maks latency'si hedefin 2 katından küçük** olmalı.

---

## 5. UI / UX Regresyon Testi (1 kere)

| Adım | Beklenen |
|---|---|
| Home → Letters → Words → Home tur at | Bottom bar doğru sekmeyi highlight ediyor |
| Letters'ta toggle: EfficientNet ↔ MLP | Model değişir, ≤ 1 sn'de yeni tahminler gelir |
| Words'te toggle: Single ↔ Ensemble | Aynı |
| Kamera açıkken ekranı kilitle, aç | Crash yok, kamera tekrar başlar |
| Uygulamayı arka plana al (Home button), 30 sn bekle, geri dön | Crash yok, kamera tekrar başlar |
| Status bar bölgesi | Kamera oraya kadar uzanıyor, beyaz şerit yok |
| Front kamera + landmark çizimi | Aynalama tutarlı — elini sağa hareket ettir, landmark da sağa hareket etsin |
| Permission ilk açılışta reddet → tekrar dene | "Permission gate" ekranı görünür, ayarlara yönlendirir veya tekrar sorar |

**Kriter:** 8/8 geçmeli.

---

## 6. Çıktılar (test bittikten sonra teslim edilecek)

- [ ] `manuel-test-sonuc.md` — her bölümün doluş hali (✓/✗ tablosu + sayılar)
- [ ] FPS/latency CSV (model × 6 örnek)
- [ ] **Demo videosu** (Letters'tan en az 5 harf, Words'ten en az 3 kelime, hem Single hem Ensemble görünsün) — proposal sunumu için
- [ ] Her sekmeden en az 1 screenshot (Top-3 paneli görünür, FPS badge okunur)
- [ ] Logcat extract: cold-start + 5 dakika çalışma boyunca `MediaPipeException` / `FATAL` aramaları (boş çıkmalı)

---

## 7. Başarısızlık Davranışı

- Smoke test fail → **derhal kod düzeltme**, raporlama durur
- Accuracy %eşik altında → "bilinen sınırlama" olarak tezde Discussion bölümüne yaz, model yeniden eğitilmez (proposal kapsamı dışı)
- FPS hedefin %50 altında → "cihaz kısıtı" notu + alternatif cihazda re-test öner

---

## 8. Tahmini Süre

| Bölüm | Süre |
|---|---|
| Hazırlık | 15 dk |
| Smoke (3 cold-start) | 10 dk |
| Letters (2 model × 72 deneme) | ~60 dk |
| Words (2 model × N × 3) | ~30 dk (N≈10 ise) |
| FPS/Latency (4 model × 60 sn + okuma) | ~20 dk |
| UI regresyon | 10 dk |
| Video + screenshot | 15 dk |
| **TOPLAM** | **~2.5 saat** |
