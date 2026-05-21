# FAZ 7 — Native Android Demo (İlerleme Notları)

Tarih: 2026-05-21
Hedef: Eğitilen 4 modeli (EfficientNet-B0, MLP Landmark, BiLSTM Single, BiLSTM Ensemble x5) tek bir native Android uygulamasında, gerçek zamanlı kamera akışıyla çalıştırmak.

---

## 1. Mimari

- **Dil/UI:** Kotlin + Jetpack Compose (Material 3)
- **Kamera:** CameraX (`PreviewView` + `ImageAnalysis`)
- **El landmark çıkarımı:** MediaPipe Tasks `HandLandmarker` (LIVE_STREAM modu)
- **Inference:** TFLite (`org.tensorflow:tensorflow-lite` + GPU/XNNPACK delegate)
- **Navigation:** Compose Navigation, 3 sekmeli bottom bar (Home / Letters / Words)
- **DI:** Basit `AppContainer` singleton (Application.onCreate'te kuruluyor)

Önemli sınıflar:
- `mediapipe/HandLandmarkerSource` — MediaPipe lifecycle + state flow
- `camera/FrameAnalyzer` — `ImageAnalysis.Analyzer`, her frame'i MediaPipe'a basıyor
- `camera/FpsMeter` — sliding window FPS
- `inference/InferenceManager` — model seçimi + TFLite interpreter cache
- `inference/*Classifier` — EfficientNet (image input), MLP (landmark input), LSTM (landmark sequence)
- `ui/letters/*`, `ui/words/*` — sekme başına `ViewModel` + ekran

## 2. Yapılan İşler (Kronolojik)

### 2A. İskelet & 4 model entegrasyonu
- Proje yapısı, `AppContainer`, theme/colors/dimens
- HandLandmarker init (önce GPU sonra CPU fallback)
- 4 model için TFLite classifier sınıfları (input tensor şekli kontrolü, label dosyaları assets/)
- LSTM için 30 frame sliding buffer + landmark normalization (wrist-relative)
- Letters/Words ekranları: kamera + landmark overlay + Top-3 panel + ModelToggle

### 2B. UI cilası
- Home sekmesi: başlık, hızlı geçiş action card'ları, "models" tablosu, dataset footer
- Kamera sekmelerinde **status bar**'a kadar uzanan kamera (edge-to-edge)
- Top-left **ModelToggle** (segmented pill, teal-bordered)
- Top-right **FpsBadge** (FPS · ms)
- Bottom **Top3Panel** (170dp yükseklik, üst köşeleri yuvarlatılmış)
- Words sekmesinde **SequenceProgressOverlay** (30 frame buffer dolana kadar progress)

### 2C. Bug'lar ve düzeltmeler

| Sorun | Kök neden | Çözüm |
|---|---|---|
| **İlk açılışta ~30 sn FPS/el algılama yok** | `HandLandmarkerSource.ensureInitialized()` analyzer thread'inde bloklanıyordu; ayrıca MediaPipe GPU delegate MediaTek cihazda 30+ sn init süresi | (1) `viewModelScope.launch(Dispatchers.IO) { source.ensureInitialized() }` ile arka planda preload (2) GPU denemesi tamamen kaldırıldı, MediaPipe doğrudan **CPU**'da çalışıyor |
| **`MediaPipeException: smaller timestamp than processed timestamp`** | LIVE_STREAM modu monotonik timestamp şartı; cold-start blok sonrası frame'ler sıra dışı geliyordu | `lastSentTsMs` volatile guard + `detectAsync` etrafına `try/catch` |
| **Arka kamera sign-language için ters** | CameraX default `DEFAULT_BACK_CAMERA` | `CameraSelector.DEFAULT_FRONT_CAMERA` |
| **PreviewView aynalı ama landmark'lar ters** | Ön kamerada `PreviewView` otomatik mirror yapıyor, MediaPipe ham bitmap işliyor | `LandmarkOverlay`'de x koordinatı `(1f - x) * width` ile flip |
| **Status bar bölgesi beyaz kalıyordu** | Default Scaffold top inset uyguluyordu | `WindowCompat.setDecorFitsSystemWindows(window, false)` + `Scaffold(contentWindowInsets = WindowInsets.systemBars.only(WindowInsetsSides.Bottom))`; Home ekranı kendi `statusBarsPadding()`'ini ekledi |
| **Toggle/FPS sıralama büyütüldükten sonra çirkin** | Geçici font/padding büyütme | Orijinal değerlere geri döndü (11.5sp / 12sp) |
| **Top3 paneli kamera alanını çok kapatıyordu** | 260dp panel | 170dp + top title bar kaldırıldı |
| **Home action card'lar tıklanmıyordu** | Sadece görseldi, `onClick` yoktu | `clickable { onClick() }` + `AppNav`'dan navigate callback'leri geçiriliyor |

### 2D. Performans gözlemleri

- MediaPipe CPU init: ~300 ms (GPU yerine)
- HandLandmarker detection: ~12–25 ms/frame
- MLP Landmark: <2 ms
- EfficientNet-B0: ~25–40 ms (GPU delegate aktif)
- BiLSTM Single: ~5 ms
- BiLSTM Ensemble (x5): ~20–30 ms
- Toplam FPS: kararlı **~24–28 fps** (kamera bağlı)

## 3. Test Cihazı

- MediaTek tabanlı Android cihaz (Mali GPU)
- Wireless ADB (TLS pairing, mDNS auto-discovery)
- Deploy: `$env:ANDROID_SERIAL = "adb-10843153BL004369-AWleMV._adb-tls-connect._tcp"; .\gradlew installDebug`

## 4. Mevcut Durum

- ✅ 4 model uygulamada çalışıyor
- ✅ Letters/Words sekmelerinde model toggle ile anlık geçiş
- ✅ Edge-to-edge kamera, doğru aynalama, status bar şeffaf
- ✅ Ana sayfa kartları artık tıklanabilir buton (Letters/Words sekmelerine geçiş)
- ✅ Cold-start bloklanması çözüldü, MediaPipe crash guard'ı eklendi

## 5. Kalan İşler (FAZ 7-E: Polish + Ölçüm)

- [ ] FPS/latency CSV logging (model bazında)
- [ ] Model karşılaştırma tablosu (gerçek cihaz ölçümleri)
- [ ] Demo video + screenshot seti
- [ ] README (demo/mobile/android/)
- [ ] Tez yazımı: "Native Android Demo" bölümü
