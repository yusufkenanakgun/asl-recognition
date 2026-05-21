package com.cse492.aslrecognition.mediapipe

import android.content.Context
import android.graphics.Bitmap
import android.os.SystemClock
import android.util.Log
import com.google.mediapipe.framework.image.MPImage
import com.google.mediapipe.tasks.core.BaseOptions
import com.google.mediapipe.tasks.core.Delegate
import com.google.mediapipe.tasks.vision.core.RunningMode
import com.google.mediapipe.tasks.vision.handlandmarker.HandLandmarker
import com.google.mediapipe.tasks.vision.handlandmarker.HandLandmarkerResult
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

/**
 * MediaPipe HandLandmarker'ın LIVE_STREAM modundaki tek noktadan akan
 * singleton sarmalayıcısı. AppContainer tutar; FrameAnalyzer çağırır,
 * Compose ekranları [state]'i collect eder.
 *
 * Delegate seçimi: önce GPU dener, başarısızsa CPU'ya düşer. GPU varsayılan
 * CPU'ya göre ~2-3x daha hızlıdır (~30ms → ~10ms hand detection).
 */
class HandLandmarkerSource(private val context: Context) {

    private var landmarker: HandLandmarker? = null
    private val _state = MutableStateFlow(HandsState.Empty)
    val state: StateFlow<HandsState> = _state.asStateFlow()

    @Volatile
    private var lastDetectStartMs: Long = 0L

    // MediaPipe LIVE_STREAM modu monoton artan timestamp ister. Tab geçişlerinde
    // iki analyzer havuzu üst üste binebildiği için son gönderilen timestamp'i
    // takip edip eşit/küçük olanları sessizce atıyoruz — yoksa MediaPipe
    // "failed precondition: smaller timestamp" ile crash atar.
    @Volatile
    private var lastSentTsMs: Long = Long.MIN_VALUE

    /**
     * En son MediaPipe'a verilen upright Bitmap. EfficientNet inference'i
     * için ViewModel okur. Landmark frame ile birebir senkron değil (en
     * fazla 1-2 frame öncesi olabilir); el hareketi yavaş olduğundan kabul
     * edilebilir gecikme.
     */
    @Volatile
    var latestBitmap: Bitmap? = null
        internal set

    @Synchronized
    fun ensureInitialized() {
        if (landmarker != null) return
        // GPU init bu cihazlarda 30+ sn sürebiliyor (shader compile cache).
        // Hand landmarker küçük bir model — CPU'da ~15-25 ms zaten.
        landmarker = create(useGpu = false).also {
            Log.i(TAG, "HandLandmarker initialized (CPU)")
        }
    }

    private fun create(useGpu: Boolean): HandLandmarker {
        val base = BaseOptions.builder()
            .setModelAssetPath(MODEL_ASSET)
            .apply { if (useGpu) setDelegate(Delegate.GPU) }
            .build()
        val options = HandLandmarker.HandLandmarkerOptions.builder()
            .setBaseOptions(base)
            .setRunningMode(RunningMode.LIVE_STREAM)
            .setNumHands(2)
            .setMinHandDetectionConfidence(0.5f)
            .setMinHandPresenceConfidence(0.5f)
            .setMinTrackingConfidence(0.5f)
            .setResultListener { result, _ -> onResult(result) }
            .setErrorListener { e -> Log.e(TAG, "HandLandmarker error", e) }
            .build()
        return HandLandmarker.createFromOptions(context, options)
    }

    /**
     * FrameAnalyzer'dan çağrılır; tek analyzer thread'den girer.
     * Görüntü zaten upright olarak gelmelidir.
     */
    fun detectAsync(image: MPImage, timestampMs: Long) {
        val lm = landmarker ?: return
        if (timestampMs <= lastSentTsMs) return
        lastSentTsMs = timestampMs
        lastDetectStartMs = SystemClock.uptimeMillis()
        try {
            lm.detectAsync(image, timestampMs)
        } catch (e: Throwable) {
            Log.w(TAG, "detectAsync failed (timestampMs=$timestampMs)", e)
        }
    }

    private fun onResult(result: HandLandmarkerResult) {
        val latency = SystemClock.uptimeMillis() - lastDetectStartMs
        _state.value = HandsState.from(result, latency)
    }

    @Synchronized
    fun close() {
        landmarker?.close()
        landmarker = null
        _state.value = HandsState.Empty
    }

    companion object {
        private const val TAG = "HandLandmarkerSource"
        private const val MODEL_ASSET = "models/hand_landmarker.task"
    }
}
