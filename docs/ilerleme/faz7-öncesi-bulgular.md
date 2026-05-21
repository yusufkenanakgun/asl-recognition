# FAZ 7 Öncesi Bulgular ve Karar Kaydı

**Tarih:** 13 Mayıs 2026
**Bağlam:** FAZ 6 V2 11 Mayıs 2026'da kapandı (Test Top-1 %56.22, proposal acceptance %40 + 16 puan üstü). FAZ 7 (demo) öncesinde durum tespiti yapılmış, akademik konumlanma, proposal uyumu ve deploy stratejisi netleştirilmiştir. Bu doküman bugünkü çalışmanın **karar kaydıdır**; demo kodu yazılmadan önceki ortak anlayışı kayıt altına alır.

---

## 1. Ortaklaşa Karar Verilen Konular

### 1.1 Accuracy hedefi — %56.22'de kalıyoruz

- WLASL-100 üzerinde Test Top-1 %56.22 elde edildi.
- %70-80'e çıkarmak için **pose landmarks + transformer + ek veri toplama** gerekirdi (1-2 hafta).
- Proposal acceptance kriteri (%40) zaten +16 puan farkla aşılmış; tezin sıkıştığı kısım **FAZ 7-8-9** (demo + tez yazımı + sunum).
- **Karar:** Accuracy artırma çalışmasına girilmeyecek. %56.22 final sonuç olarak alınacak. Pose landmark eklemesi **future work** kalemi olarak tezde yer alacak.

### 1.2 Tez savunma çerçevesi — "Deployability Comparative Study"

Proposal incelemesinde (`docs/proposal/20210702010_YusufKenanAKGUN.pdf`) tespit edilen anahtar ifadeler bu çerçeveyi destekliyor:

- Başlık: *"A **Comparative Study** of Image-Based and Landmark-Based Approaches"*
- Abstract: *"most effective method for **practical deployment**"*
- Software constraints: *"MediaPipe Hands"* (pose/face değil — **hands-only kısıt proposal'da yazılı**)
- Hardware constraints: *"Mobile phone (Android/iOS) for demo application"*
- Evaluation criteria: *"accuracy, F1-score, **real-time performance**, **model size**"*

**Tezin ana çerçevesi şu şekilde sunulacak:**

> "Bu çalışma, işaret dili tanıma için üç farklı yaklaşımı (image-based statik CNN, landmark-based statik MLP, landmark-based dinamik BiLSTM) accuracy-size-speed-task complexity çoklu eksenli bir matriste değerlendiren bir **deployability comparative study**'dir. Sonuçlar, her yaklaşımın hangi deployment senaryosu (high-accuracy server, lightweight mobile, edge real-time) için uygun olduğunu deneysel olarak göstermektedir."

### 1.3 Hands-only kısıt — bilinçli tasarım kararı

- Proposal **MediaPipe Hands** kullanımını baştan şart koşmuştur; pose/face/body proposal kapsamında değildir.
- Yüz/üst vücut/duruş bilgisi ASL dilbilgisinde *non-manual markers* olarak gramer taşır → hands-only **gerçek ve ölçülebilir bilgi kaybıdır**, mazeret değildir.
- Multi-modal modeller (RGB + pose + flow) WLASL-100'de %65-78 raporluyor; bizim hands-only model %56.22 → "rekabetçi, orta-üst seviye".
- **Savunma dili:** "Trade-off bilinçliydi, accuracy-size-speed üçgeninde farklı bir nokta optimize edildi" — *"daha az aldık"* değil.

### 1.4 Hata analizi — model anlamlı pattern öğreniyor

V2-SONUC.md'de tespit edilen karışıklıklar **rastgele değil**:

- black ↔ who: ikisi de tek-el, yüz bölgesinde işaret parmağı
- change ↔ how: ikisi de iki-elli yumruk dönüşümü
- want ↔ many: ikisi de iki-elli parmak açılma
- mother ↔ fine: "5-handshape" başparmak teması

**Savunma:** Model **görsel/jest benzerliklerini** doğru yakalıyor; hatalar dilbilimsel olarak makul (minimal pairs). Hands-only kısıtın eksik tutamadığı **yüz/duruş bilgisi** burada belirleyici olur — bu future work yönünü işaret eder.

### 1.5 NFR-07 (<1 MB) ihlali — proposal'da sıkı bağlayıcı değil

- Proposal'da somut MB hedefi **yok**, sadece *"model size (MB) ölçülecek"* yazılı.
- NFR-07 (<1 MB) `docs/requirements_analysis.md:130`'da yazılı; bu **internal hedef**, hoca'ya henüz iletilmedi.
- Cümle *"the landmark-based model"* (tekil) diyor — yazıldığında muhtemelen MLP odaklıydı; LSTM o aşamada henüz scope'ta değildi.
- **MLP (0.24 MB) NFR-07'yi karşılıyor**, LSTM (5.51 / 27.55 MB) karşılamıyor.
- **Karar:** `requirements_analysis.md` hoca'ya iletilmeden önce hocayla birlikte revize edilecek. NFR-07'nin literal *"<1 MB"* ifadesi yumuşatılabilir veya MLP-spesifik hâle getirilebilir. Tezde ölçüm + literatür karşılaştırması (I3D ~140 MB, SAM-SLR ~200 MB, OpenHands SPOTER ~60 MB) verilerek dürüst raporlama yapılacak.

### 1.6 EfficientNet boyutu — 46.75 MB → 15.71 MB

- `models/best_model.pth` içinde optimizer_state_dict (Adam momentum + variance) bulunduğu için dosya şişmişti.
- `model_state_dict` çıkarılarak `models/deploy/efficientnet_b0.pth` (15.71 MB) oluşturuldu.
- **Tekrar eğitim yapılmadı** — mimari değişmedi, sadece deployment-ready dosya çıkarıldı.
- TFLite int8 quantization sonrası mobile boyutun ~4-5 MB'a düşmesi beklenir (FAZ 7'de ölçülecek).

### 1.7 Deployment-only model klasörü oluşturuldu

`models/deploy/` içerikleri (güncel, 13 Mayıs 2026):

| Dosya | Boyut | Açıklama |
|-------|-------|----------|
| `efficientnet_b0.pth` | 15.71 MB | EfficientNet-B0 (harf, image-based) |
| `mlp_landmark.pth` | 0.24 MB | MLP (harf, landmark-based) |
| `lstm_single_best.pth` | 5.51 MB | **V2 final tek model — seed 0 (val-best, val %58.85 / test %53.23)** |
| `lstm_seed0..4.pth` | her biri 5.51 MB | V2 ensemble bileşenleri (toplam 27.55 MB, test %56.22) |

İterasyon B'nin eski `lstm_v2_single.pth` dosyası deploy klasöründen çıkarıldı (val %54.32, V2 final pipeline parçası değil; ablation tablosunda referans olarak kalacak).

### 1.8 Demo matrisinin kapsamı — 4 model × Android (proposal-only)

Proposal demo'yu **mobil (Android/iOS) + React Native + TFLite** olarak tanımlar; PC/web tabanlı bir demo proposal kapsamında değildir. Bu nedenle deployability matrisi tek platforma — gerçek Android cihaza — daraltılmıştır.

| Model | Android (gerçek cihaz) |
|-------|------------------------|
| EfficientNet-B0 | ölçülecek |
| MLP | ölçülecek |
| **LSTM single (val-best seed 0)** | ölçülecek |
| **LSTM ensemble (5 seed)** | ölçülecek |

**Kritik bulgu beklentisi:** Eğer single LSTM (5.51 MB) mobilde iyi FPS verirse, *"+2.07 puan accuracy için 5× model boyutu kabul edilebilir mi?"* sorusu deneysel olarak yanıtlanır. Bu tezin **en güçlü mühendislik bulgusu** olabilir — knowledge distillation gerekçesini de empirik desteklemiş olur.

### 1.9 LSTM single model seçimi — val-best seed 0 + tezde Seçenek C (şeffaf 3 satırlı tablo)

**Tüm 5 seed'in test seti performansı** (`models/faz6_v2/evaluation_results.json` mevcut verilerden okundu — yeniden ölçüm gerekmedi):

| Seed | Val Acc | **Test Top-1** | Test Top-5 | Macro F1 |
|------|---------|----------------|------------|----------|
| **seed 0** (val-best) | **%58.85** | %53.23 | **%80.60** | 0.4905 |
| seed 1 | %53.91 | %52.74 | %78.11 | 0.4951 |
| **seed 2** (test-best, oracle) | %58.02 | **%56.22** | %79.10 | **0.5238** |
| seed 3 | %53.91 | %49.75 | %77.61 | 0.4470 |
| seed 4 | %56.38 | %48.76 | %79.60 | 0.4686 |
| **Ensemble (5 seed avg)** | **%60.08** | **%56.22** | **%81.09** | 0.5208 |

**Önemli gözlem:** Val-test sıralaması farklı (seed 0 val'de 1., test'te 2.; seed 4 val'de 3., test'te sonuncu). 201 örneklik küçük test setindeki **varyans** bunun başlıca sebebi. Bu V2-SONUC.md §3.6 ve §9.7-6'da zaten not edilmişti.

**Karar — Seçenek C (şeffaf hibrit):**

- **Akademik kural:** Single model seçimi **validation set'e göre** yapılır → seed 0 (val %58.85) seçildi.
- **Deploy edilen model:** `models/deploy/lstm_single_best.pth` (= seed 0).
- **Tezde rapor edilecek dürüst tablo** (3 satır, hiçbir şey saklanmıyor):

| Konfigürasyon | Seçim kriteri | Test Top-1 | Test Top-5 |
|---------------|---------------|------------|------------|
| Single (val-best) | seed 0, validation accuracy'ye göre | %53.23 | %80.60 |
| Single (oracle, post-hoc) | seed 2, test'te en iyi olan | %56.22 | %79.10 |
| Ensemble (5 seed) | tüm seedlerin logit ortalaması | **%56.22** | **%81.09** |

**Bu tablo tezdeki "Experimental Results" bölümünde aynen kullanılacaktır.** Jüri "seçim kriterin ne?" derse cevap: *"Validation accuracy'ye göre seed 0. Oracle ve ensemble satırları ablation amacıyla şeffaflık için raporlandı; küçük test seti varyansı seed'ler arası ±5 puana kadar fark üretebilmektedir."* Bu en güçlü ve dürüst pozisyondur.

**Android demoda "single model" placeholder olarak `lstm_single_best.pth` (seed 0) kullanılacak.** Hangi seed deploy edildiği boyut/FPS açısından fark yaratmaz (hepsi 5.51 MB, aynı mimari) — sadece tezde raporlanan test accuracy değişir.

**Ensemble'ın değeri:**
- Top-1: ensemble single ortalamasının (%52.14) **+4.08 puan** üstünde
- Top-5: ensemble %81.09 vs val-best single %80.60 → +0.49 puan
- Robustness: seed 2'nin tesadüfi yüksekliğinden bağımsız, daha güvenilir tahmin

### 1.10 Mobil cihaz seçimi — gerçek Android cihaz

- Emulator değil, **gerçek Android cihaz** kullanılacak. FPS rakamlarının gerçek deployment senaryosunu yansıtması için.

---

## 2. Henüz Netleşmemiş Konular

| Konu | Durum | Karar Zamanı |
|------|-------|--------------|
| TFLite'da BiLSTM operatör desteği | Bilinmiyor | FAZ 7 Gün 2 (conversion pipeline) |
| React Native ekosistem riski (MediaPipe + TFLite + vision-camera entegrasyonu) | Bilinmiyor | FAZ 7 Gün 3-4 (RN denemesi) |
| Bare RN mi Expo mu | Önerim: Bare RN | FAZ 7 Gün 3 başlangıcı |
| Native Android fallback'e geçilecek mi | RN sonucuna bağlı | FAZ 7 Gün 4 sonu (time-box) |
| LSTM ensemble mobilde çalıştırılabilir mi (5× model yükleme, 5× inference) | Bilinmiyor | FAZ 7 Gün 5 |
| `requirements_analysis.md` revizesi (NFR-07 kapsamı) | Hocayla yapılacak | Hoca'ya iletim öncesinde |
| `ilerleme-1.md`'nin V2 sonuçlarıyla güncellenmesi | V1 LSTM tablosu hâlâ içeride | FAZ 7 başlamadan önce ya da FAZ 8'de |
| Git commit (FAZ 6 V2 + bugünkü deploy değişiklikleri) | Henüz commit'lenmedi | FAZ 7 başlamadan önce |

**Çözülen konular (13 Mayıs 2026):**
- ✅ Seed 0'ın test accuracy'si → `evaluation_results.json`'da mevcuttu, ölçüldü: **%53.23 Top-1, %80.60 Top-5**
- ✅ Single LSTM model seçimi → Seçenek C: seed 0 deploy + 3 satırlı şeffaf tablo (bkz. madde 1.9)
- ✅ Eski `lstm_v2_single.pth` deploy klasöründen çıkarıldı

---

## 3. FAZ 7'ye Başlamadan Önce Yapılacak Mini Hazırlıklar

1. ✅ `models/deploy/lstm_v2_single.pth` (iterasyon B) deploy klasöründen çıkarıldı.
2. ✅ `models/deploy/lstm_single_best.pth` (= seed 0) hazır — single best model.
3. ✅ Seed 0 test accuracy: mevcut `evaluation_results.json`'dan okundu (%53.23 Top-1) — yeniden çalıştırmaya gerek olmadı.
4. ⏳ `ilerleme-1.md` V2 sonuçlarıyla güncellenecek (V1 LSTM tablosu V2 ile değiştirilecek). *İsteğe bağlı, FAZ 8'e ertelenebilir.*
5. ⏳ Git commit (mevcut FAZ 6 V2 dosyaları + bugünkü deploy çıktıları + bu doküman).

---

## 4. FAZ 7 Planı — Proposal'a Sadık (Android-only), Time-Boxed (1 hafta)

Yaklaşım: **Proposal demo'yu mobil olarak tanımlıyor; PC/web demo proposal dışıdır ve bu fazda yapılmaz.** Önce TFLite conversion pipeline'ı kurulur, ardından React Native denenir, gerekirse native Android'e düşülür. Her time-box sonunda durum değerlendirmesi yapılacak.

### Gün 1 — TFLite conversion pipeline (kritik kavşak)

- PyTorch → ONNX → TFLite dönüşüm denemesi (önce MLP, sonra EfficientNet, sonra BiLSTM)
- Quantization (float32 → int8) ile boyut karşılaştırması
- Çıktı: `models/tflite/` + conversion log dosyaları
- **Risk:** BiLSTM TFLite operatör desteği. Çevrilemezse Gün 1 sonunda karar: ONNX Runtime Mobile mı, GRU'ya çevirip yeniden eğitim mi?

### Gün 2-3 — React Native + TFLite (proposal yöntemi)

- Stack: bare RN + `react-native-fast-tflite` + `react-native-vision-camera` (frame processor)
- MediaPipe entegrasyonu için iki yol denenecek: (a) `vision-camera-plugin-tflite` üzerinden doğrudan hand landmark TFLite modeli, (b) native bridge ile MediaPipe Tasks Android SDK
- **Önce MLP** ile pipeline doğrulanacak — çalışırsa EfficientNet + LSTM eklenecek
- **Time-box:** 2 gün. Gün 3 sonunda MLP kameradan tahmin akışı çalışmıyorsa Gün 4'te native Android'e geçilecek.

### Gün 4 — Fallback kararı veya tamamlama

- **RN başarılı ise:** 4 model × Android matrisini doldur, FPS topla, bitir.
- **RN başarısız ise:** Native Android (Kotlin + TFLite resmi sample app + MediaPipe Tasks Android SDK). 1 günde MLP demo'su biter. Tezde dürüstçe rapor edilir: *"React Native ekosisteminde X kısıtı sebebiyle native stack tercih edildi."*

### Gün 5-7 — Deployability matrisi + tez malzemesi

Hedef tablo (`docs/ilerleme/FAZ7-SONUC.md` veya benzeri dosyada):

| Model | Android FPS | TFLite boyut | Çalıştı mı? | Notlar |
|-------|-------------|--------------|-------------|--------|
| EfficientNet-B0 | ? | ? MB | ?/✅/❌ | int8 quantize sonrası accuracy düşüşü ölçülecek |
| MLP | ? | ? MB | ?/✅/❌ | en hafif, %99+ beklenir |
| LSTM single (seed 0) | ? | ? MB | ?/✅/❌ | mobile-friendly çözüm hipotezi |
| LSTM ensemble (5 seed) | ? | ? MB | ?/✅/❌ | 5× inference yükü |

Eksik hücreler de **bulgu** sayılır — *"X kombinasyonu Y sebebiyle çalışmadı"* kaydı tezde gerçek mühendislik analizidir.

---

## 5. Time-Box Kuralları (Net)

- **Gün 1 sonu:** TFLite conversion 3 model için durumu net olacak. LSTM çevrilemezse o gün karar verilir.
- **Gün 3 sonu:** RN'de MLP'nin kameradan tahmin akışı çalışmıyorsa **Gün 4 sabahı native'e geçilir**; daha fazla zaman harcanmaz.
- **Gün 7 sonu:** Matris ne olursa olsun doldurulur, boş hücreler bulgu olarak raporlanır.

---

## 6. Bilinen Riskler

| Risk | Etki | Azaltma |
|------|------|---------|
| BiLSTM TFLite mobile interpreter'da desteklenmeyebilir | Yüksek | ONNX Runtime Mobile fallback; gerekirse GRU'ya dönüş |
| RN'de MediaPipe + frame processor + TFLite zinciri kararsız çalışabilir | Orta-Yüksek | Native Android fallback hazır |
| EfficientNet int8 quantize sonrası accuracy düşüşü beklenenden fazla olabilir | Düşük-Orta | Float16 quantize'a düş; her iki sayıyı da raporla |
| LSTM ensemble Android'de bellek sınırı aşabilir (5 × 5.51 MB + activations) | Düşük | Sequential model loading; çalışmazsa tezde "ensemble Android'de pratik değil" bulgusu olarak raporlanır |
| Gerçek cihazda MediaPipe Hands latency PC GPU'dan çok yüksek olabilir | Orta | Beklenen sonuç; FPS rakamı zaten bu farkı ölçecek |
| Demo süresi FAZ 8 + FAZ 9'a baskı yapabilir | Orta | Time-box kuralları sıkı uygulanacak |

---

## 7. Sonraki Adım

FAZ 7 Gün 1 — TFLite conversion pipeline ile başlanacak (`models/tflite/` çıktıları). Önce mini hazırlıklar (madde 3) tamamlanacak, ardından MLP → EfficientNet → BiLSTM sırasıyla dönüşüm denenecek.

---

*Doküman 13 Mayıs 2026'da oluşturuldu; FAZ 7 öncesi ortak anlayışı kayıt altına alır.*
