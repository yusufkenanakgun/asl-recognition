# FAZ 7 — Manuel Test Planı

Tarih (planlanan): kullanıcı uygun olduğunda
Amaç: Native Android demo uygulamasının proposal'da tanımlanan **"tanınan harf/kelime ekrana yazılır; FPS ve latency ölçülür"** kabul kriterini gerçek cihazda doğrulamak.

> Bu doküman bir **test prosedürü** + **başarı kriterleri** listesidir. Otomatik test değil — kullanıcının cihazda elle uygulayacağı senaryolar.

---

## 0. Hazırlık (test başlamadan önce, 1 kere)

### 0.1 Wireless ADB bağlantısı (internet gerekmez, aynı yerel ağ yeterli)

İlk kez (eşleştirme):
1. Telefon → Geliştirici Seçenekleri → **Kablosuz hata ayıklama** → Aç → **"Bilgisayarı eşleştirmek için kod kullan"**
2. Bilgisayarda:
   ```bash
   adb pair <telefon-ip>:<pairing-port>     # ekrandaki 6 haneli kodu gir
   adb connect <telefon-ip>:<debug-port>    # eşleştirme bilgisinden farklı port
   adb devices                              # cihaz "device" olarak görünmeli
   ```
3. mDNS otomatik bulduysa serial string'ini bir kere export et (bu repoda kullanılan örnek):
   ```bash
   export ANDROID_SERIAL="adb-<seri>._adb-tls-connect._tcp"
   ```

Sonraki seferler: `adb connect <telefon-ip>:<debug-port>` yeterli.

### 0.2 Test ortamı

- [ ] `adb devices` cihazı görüyor
- [ ] Son APK yüklü: `.\gradlew installDebug`
- [ ] Cihazın şarjı ≥ %50, **Battery Saver kapalı** (CPU throttling olmasın)
- [ ] **Aydınlatma:** doğal gün ışığı veya en az iki noktadan beyaz LED — sahnede sert gölge olmamalı
- [ ] **Arka plan:** düz, tek renkli, elden farklı bir yüzey (duvar / beyaz panel)
- [ ] Kameraya el mesafesi: **30–50 cm**

### 0.3 Ekran kaydı (opsiyonel ama önerilen)

```bash
# kayıt başlat (Ctrl+C ile durdur, max 180 sn)
adb shell screenrecord /sdcard/test.mp4
# kaydı bilgisayara çek
adb pull /sdcard/test.mp4 docs/ilerleme/manuel-test-kayit.mp4
adb shell rm /sdcard/test.mp4
```
Alternatif: cihazın kendi ekran kaydı özelliği.

### 0.4 Sonuç şablonu

- [ ] `docs/ilerleme/manuel-test-sonuc.md` açık ve bu prosedüre eşlik ediyor (boş ✓/✗ tabloları hazır)

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

29 sınıf: 26 harf (A-Z) + `del` + `nothing` + `space`. İki model için ayrı.

> **J ve Z notu:** ASL'de bu iki harf hareket içerir; modellerimiz **statik kare** üzerinde eğitildi (`asl_alphabet_train/J/` ve `Z/` klasörlerindeki statik kareler). Manuel testte hareket yapmadan, eğitim verisindeki statik pozu sabit tut.
>
> **`nothing` notu:** Bu sınıf "el algılanmadı" durumunu temsil eder. Uygulama pipeline'ı `HandLandmarker` el algılamadığında classifier'ı **çağırmıyor**, dolayısıyla `nothing` için Top-1/güven okunamaz. Bu kasıtlı davranış (false-positive engelleyici). Şablonda `N/A` işaretle, özet hesabını **28 testable** üzerinden yap.

### Prosedür
- Her sınıf için: kullanıcı doğru işareti yapar, **3 saniye sabit tutar**, Top-3 panelindeki **ilk tahmini ve güven yüzdesini** okur.
- Her sınıf için **1 deneme** (toplam 29 deneme / model, ölçülebilir 28). Letters modelleri test setinde ~%99-100, tek deneme tanıma yeteneğini doğrulamak için yeterli.
- Top-1 doğru ise ✓, değilse Top-3 panelinde doğru harf var mı kontrol et (✓3).

### Modeller
- [ ] **EfficientNet-B0** (29 deneme, 28 ölçülebilir)
- [ ] **MLP Landmark** (29 deneme, 28 ölçülebilir)

### Başarı kriteri (28 ölçülebilir sınıf üzerinden)

| Metrik | Eşik (EfficientNet) | Eşik (MLP) | Kaynak |
|---|---|---|---|
| Top-1 accuracy (manuel) | ≥ %70 (20/28+) | ≥ %65 (19/28+) | FAZ 3/4 test setinde her ikisi de ≥%99 (`evaluation_results.json`, `mlp_evaluation_results.json`). Manuel testte tek-kullanıcı OOD'de 20-30 puan düşüş beklenir. |
| Top-3 accuracy | ≥ %88 (25/28+) | ≥ %85 (24/28+) | – |
| Ortalama Top-1 güven (doğru tahminlerde) | ≥ %75 | ≥ %75 | Modelin emin olup olmadığını gösterir; düşük güven uyarı işaretidir |

> **Not:** Test setiyle aynı sayıyı beklemiyoruz. Manuel testte tek bir kullanıcı (kendi eli) test ediyor — bu hem dağılım dışı (out-of-distribution) hem de tek bir el morfolojisi. Hedef: "model gerçek dünyada çalışıyor mu" doğrulaması, "yeni accuracy değeri ölç" değil.

---

## 3. Words — Kelime-Bazlı Doğruluk Testi

Eğitilen tam liste: **WLASL-100 (100 kelime)**, kaynak `labels/WordLabels.kt` (sıra `data/faz6_v2/landmarks_wlasl100/gloss_to_idx.json` ile aynı).

> **Pratik kısıt:** 100 kelime × 3 tekrar × 2 model = 600 deneme ≈ 4 saat. Bu manuel testin amacı **tam değerlendirme** değil, proposal'ın "kelime tanınıyor" kabul kriterinin doğrulanmasıdır. Bu yüzden **temsili alt küme** ile çalışılır.

### Alt küme (15 kelime)

Aşağıdaki 15 kelime, sınıf çeşitliliğini (nesne / fiil / aile / renk / soyut) ve hareket kalıplarını (tek-el / iki-el / küçük-büyük genlik) kapsayacak şekilde seçildi:

```
drink, mother, computer, yes, no, like, help,
book, dance, family, blue, eat, want, time, who
```

Tam 100 kelimelik test isteniyorsa: bu prosedürü genişlet, ama süreyi (~4 saat) ve seans sayısını (en az 2 oturum) önceden planla.

### Prosedür
- Her kelime için: doğal hızda işaret et (~1 sn süren bir hareket), buffer dolana kadar bekle (alt panelde sequence progress overlay biter).
- Her kelimeyi **3 kez** tekrar et.
- Top-1 doğruysa ✓, Top-3 içinde varsa ✓3.

### Modeller
- [ ] **BiLSTM Single** (15 kelime × 3 = 45 deneme)
- [ ] **BiLSTM Ensemble (x5)** (15 kelime × 3 = 45 deneme)

### Başarı kriteri

Referans (test set, `models/faz6_v2/ensemble_results.json`):
- Single Top-1 ≈ **%53**, Top-5 ≈ **%80**
- Ensemble Top-1 = **%56.22**, Top-5 = **%81.09**

| Metrik | Eşik (Single) | Eşik (Ensemble) | Açıklama |
|---|---|---|---|
| Top-1 accuracy (manuel) | ≥ %35 | ≥ %40 | Test seti zaten %53/%56; tek-kişilik OOD'de 10-20 puan düşüş normal |
| Top-3 accuracy | ≥ %60 | ≥ %65 | Test seti Top-5 ≈%80; Top-3 doğal olarak biraz düşer |
| Ensemble > Single farkı | – | en az +3 puan Top-1 | Test setinde fark +3 puan (53→56) |

> **Not:** Eşikler test set sonuçlarının **altında** kasıtlı olarak — manuel test farklı kullanıcı, farklı el morfolojisi ve farklı kamera açısıyla yapıldığı için OOD'dir. Proposal'ın gereksinimi "kelime tanınıyor" olup, sayısal accuracy iddiası değildir.

---

## 4. Performans Testi — FPS & Latency

Proposal direkt şart koşuyor: *"FPS ve latency ölçülür"*.

### Prosedür
- Her model için Letters/Words sekmesinde **60 saniye boyunca** elini kameranın önünde tut (sabit harf / sabit kelime).
- Bu süre içinde FPS badge'i ekran kaydından **her 10 saniyede bir** okuyarak 6 örnek topla.
- Latency badge'inden aynı şekilde 6 örnek (ms).
- Ortalama + min + maks raporla.

### Başarı kriteri (orta seviye Android cihaz için)

`FpsBadge` ekrandaki **toplam end-to-end** latency'yi gösterir (kamera frame → MediaPipe → classifier → UI). MediaPipe'ı izole etmek için `adb logcat -s FrameAnalyzer:* HandLandmarkerSource:*` çıktısı kullanılır; ayrı ölçüm zorunlu değil.

| Model | FPS hedefi (badge) | Latency hedefi (badge, ms) |
|---|---|---|
| EfficientNet-B0 | ≥ 15 fps | ≤ 60 |
| MLP Landmark | ≥ 25 fps | ≤ 35 |
| BiLSTM Single | ≥ 20 fps | ≤ 40 |
| BiLSTM Ensemble | ≥ 12 fps | ≤ 60 |

> Latency hedefleri MediaPipe (~12-25 ms) + model inference toplamı. FAZ7.md'deki gerçek cihaz ölçümleri (toplam ~24-28 fps) ile tutarlı.

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
| Hazırlık (wireless ADB + ortam + şablon) | 20 dk |
| Smoke (3 cold-start) | 10 dk |
| Letters (2 model × 29 deneme) | ~35 dk |
| Words alt küme (2 model × 15 × 3 = 90 deneme) | ~45 dk |
| FPS/Latency (4 model × 60 sn + okuma) | ~20 dk |
| UI regresyon | 10 dk |
| Screenshot + `adb pull` | 10 dk |
| **TOPLAM** | **~2 saat 15 dk** (tek seans) |

> Tam 100 kelime seçilirse Words bölümü ~4 saate çıkar; bu durumda toplamı 2 oturuma böl.
