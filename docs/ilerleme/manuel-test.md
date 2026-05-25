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

> **Bu sürümün değişikliği:** Eski plan 15 kelimelik alt küme × 3 tekrar idi; "kelime tanınıyor" kabul kriterini doğrularken WLASL-100'ün **tüm sınıflarını** kapsama almak için tam liste × **1 deneme** olarak revize edildi. 1 deneme tercih edilmesinin sebebi: 100 × 3 × 2 = 600 denemenin pratik olmaması ve 100'lük örneklem büyüklüğünün tek deneme gürültüsünü sayıca emmesi.

### Cihaz
- [ ] **Xiaomi 15T Pro** üzerinde yapılır. (Letters TECNO SPARK 20C'de yapıldı; bkz. Bölüm 4'teki cihaz değişimi gerekçesi.)

### Test kelimeleri (sıra: `gloss_to_idx.json` model indeks sırası — denetim için sabit)

```
0:drink  1:before  2:computer  3:mother  4:go  5:who  6:candy  7:thin  8:yes  9:cool
10:like  11:deaf  12:no  13:orange  14:hot  15:bed  16:thanksgiving  17:bowling  18:study  19:wrong
20:cousin  21:black  22:now  23:woman  24:shirt  25:tall  26:pizza  27:finish  28:fine  29:family
30:walk  31:dog  32:hearing  33:later  34:man  35:white  36:apple  37:secretary  38:short  39:help
40:many  41:accident  42:bird  43:change  44:forget  45:thursday  46:fish  47:kiss  48:paper  49:graduate
50:hat  51:language  52:color  53:doctor  54:basketball  55:cook  56:pull  57:son  58:year  59:all
60:dark  61:give  62:last  63:africa  64:city  65:decide  66:letter  67:cow  68:full  69:what
70:book  71:dance  72:pink  73:blue  74:corn  75:enjoy  76:play  77:meet  78:school  79:work
80:birthday  81:cheat  82:tell  83:want  84:but  85:need  86:can  87:same  88:chair  89:time
90:brown  91:how  92:paint  93:purple  94:right  95:eat  96:medicine  97:jacket  98:clothes  99:table
```

### Prosedür
- Her kelime için: doğal hızda işaret et (~1 sn süren bir hareket), buffer dolana kadar bekle (alt panelde sequence progress overlay biter).
- Her kelime **1 kez** denenir.
- Her kelime için kaydedilenler: **Top-1 doğru mu (Y/N)**, **Top-1 güven %**, **Top-1 yanlışsa hangi sınıfa karıştı (confusion)**, **Top-3 içinde doğru var mı (yalnız Top-1 yanlışsa)**.

### Adil-yürütme kuralı (single-trial telafisi)
- Buffer dolmadan önce işareti yanlış başlattığını fark edersen elini indir → sequence sıfırlanır → baştan yap. **Sequence buffer'ı dolup tahmin geldikten sonra tekrar yapılmaz** (kelime "denendi" sayılır).
- Bir kelimenin işaretini hatırlamıyorsan **bilgisayarda WLASL referansını aç** ve bir kez izle, sonra dene. Hatırlamamak yüzünden yapılan yanlış işaret veriyi zehirler.

### Mola planı (yorgunluk yanlış-pozitif üretir)
- Her **25 kelimede bir 5 dk mola.** Yani: model başına 4 mola (25 / 50 / 75 / 100 sonrası). Tüm Single bittikten sonra modeller arası **10 dk mola.**

### WLASL referans erişimi
- Test öncesi `data/wlasl/videos/` klasöründen ilgili gloss videosu hazır olsun **veya** signdictionary / WLASL gloss listesi bir browser tab'ında açık tutulsun.

### Modeller
- [ ] **BiLSTM Single** (100 kelime × 1 = 100 deneme)
- [ ] **BiLSTM Ensemble (x5)** (100 kelime × 1 = 100 deneme)

### Başarı kriteri

Referans (test set, `models/faz6_v2/ensemble_results.json`):
- Single Top-1 ≈ **%53**, Top-5 ≈ **%80**
- Ensemble Top-1 = **%56.22**, Top-5 = **%81.09**

| Metrik | Eşik (Single) | Eşik (Ensemble) | Açıklama |
|---|---|---|---|
| Top-1 accuracy (manuel) | ≥ %35 (≥ 35/100) | ≥ %40 (≥ 40/100) | Test seti zaten %53/%56; tek-kişilik OOD'de 10-20 puan düşüş normal |
| Top-3 accuracy | ≥ %60 (≥ 60/100) | ≥ %65 (≥ 65/100) | Test seti Top-5 ≈%80; Top-3 doğal olarak biraz düşer |
| Ortalama Top-1 güven (doğru tahminlerde) | ≥ %50 | ≥ %55 | Kelime modelleri Letters'tan doğal olarak daha düşük güven verir; sıralama bilgisi olarak izlenir |
| Ensemble > Single farkı | – | en az +3 puan Top-1 | Test setinde fark +3 puan (53→56) |

> **Not:** Eşikler test set sonuçlarının **altında** kasıtlı olarak — manuel test farklı kullanıcı, farklı el morfolojisi ve farklı kamera açısıyla yapıldığı için OOD'dir. Proposal'ın gereksinimi "kelime tanınıyor" olup, sayısal accuracy iddiası değildir.

> **Confusion analizi:** Tablonun "→ tahmin" kolonu sonradan Discussion bölümünde "hangi kelime kümeleri birbirine karışıyor" desenlerini çıkarmak için kullanılır (örn: aile kelimeleri / renkler / fiiller).

---

## 4. Performans Testi — FPS & Latency

Proposal direkt şart koşuyor: *"FPS ve latency ölçülür"*.

### Cihaz değişiminin gerekçesi

Letters bölümü **TECNO SPARK 20C** (Helio G36, entry-level) üzerinde tamamlandı. TECNO'da kelime modelleri (BiLSTM Single ve özellikle Ensemble x5) gerçek-zamanlı kullanım için **ölçülemez derecede yavaş** çalıştı — Ensemble pratikte gözlemlenemeyecek kadar düşük FPS verdi (oturum sırasında badge okumak için bile yetersiz). Bu yüzden Words bölümü **Xiaomi 15T Pro** (Dimensity 9400+, flagship) üzerinde alındı. İki cihazda da ilgili modeller için FPS/latency raporlanıyor; cihaz farkı tezde donanım hassasiyeti tartışmasına dönüşür.

### Cihaz-model eşleşmesi (bu manuel test için)

| Cihaz | Üzerinde ölçülen modeller |
|---|---|
| TECNO SPARK 20C | EfficientNet-B0, MLP Landmark (Letters sekmesi) |
| Xiaomi 15T Pro | BiLSTM Single, BiLSTM Ensemble (x5) (Words sekmesi) |

### Prosedür
- Her model için ilgili sekmede **60 saniye boyunca** elini kameranın önünde tut (sabit harf / sabit kelime).
- Bu süre içinde FPS badge'i ekran kaydından **her 10 saniyede bir** okuyarak 6 örnek topla.
- Latency badge'inden aynı şekilde 6 örnek (ms).
- Ortalama + min + maks raporla.

### Başarı kriteri

`FpsBadge` ekrandaki **toplam end-to-end** latency'yi gösterir (kamera frame → MediaPipe → classifier → UI). MediaPipe'ı izole etmek için `adb logcat -s FrameAnalyzer:* HandLandmarkerSource:*` çıktısı kullanılır; ayrı ölçüm zorunlu değil.

| Model | Cihaz | FPS hedefi (badge) | Latency hedefi (badge, ms) |
|---|---|---|---|
| EfficientNet-B0 | TECNO SPARK 20C | ≥ 15 fps | ≤ 60 |
| MLP Landmark | TECNO SPARK 20C | ≥ 25 fps | ≤ 35 |
| BiLSTM Single | Xiaomi 15T Pro | ≥ 20 fps | ≤ 40 |
| BiLSTM Ensemble (x5) | Xiaomi 15T Pro | ≥ 12 fps | ≤ 60 |

> Latency hedefleri MediaPipe (~12-25 ms) + model inference toplamı. Hedefler cihazdan bağımsız tutuldu (entry-level + flagship'in birlikte bir "kullanılabilirlik bandı" oluşturması için).

**Geçer kriter:** her modelin **ortalama FPS'i hedefin en az %80'i** ve **maks latency'si hedefin 2 katından küçük** olmalı.

> **Tezde not:** TECNO'da Words modellerinin ölçülemediği gözlemi bizzat raporun bir sonucudur — "donanım katmanı, kelime modelleri için entry-level Android'i pratikte dışlıyor" tespiti Discussion'a yazılır.

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

| Bölüm | Cihaz | Süre |
|---|---|---|
| Hazırlık (wireless ADB + ortam + şablon) | her ikisi | 20 dk |
| Smoke (3 cold-start) | her ikisi | 10 dk |
| Letters (2 model × 29 deneme) | TECNO | ~35 dk |
| Words tam liste (2 model × 100 × 1 = 200 deneme) | Xiaomi | ~90 dk + 40 dk mola = ~130 dk |
| FPS/Latency (4 model × 60 sn + okuma) | TECNO (2) + Xiaomi (2) | ~20 dk |
| UI regresyon | her ikisi (kısa) | 10 dk |
| Screenshot + `adb pull` | her ikisi | 10 dk |
| **TOPLAM** | – | **~4 saat** (tek uzun seans veya 2 kısa oturum) |

> Letters TECNO'da zaten tamamlandı (~35 dk düşülür). Words 130 dk + Performans 20 dk + diğerleri ≈ **3 saat** kalan iş yükü.
