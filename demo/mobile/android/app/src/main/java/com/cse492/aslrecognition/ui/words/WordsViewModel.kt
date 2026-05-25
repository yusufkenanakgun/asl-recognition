package com.cse492.aslrecognition.ui.words

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.cse492.aslrecognition.inference.ClassificationResult
import com.cse492.aslrecognition.inference.InferenceManager
import com.cse492.aslrecognition.inference.ModelType
import com.cse492.aslrecognition.mediapipe.HandLandmarkerSource
import com.cse492.aslrecognition.preprocessing.SequenceBuffer
import com.cse492.aslrecognition.preprocessing.frameWordFeature
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.util.concurrent.atomic.AtomicBoolean

/**
 * Words sekmesinin sınıflandırma orkestrasyonu.
 *
 * Her HandLandmarker state'inde 128-dim feature çıkarılır ve 32-frame sliding
 * window'a push edilir. Buffer dolunca tek-atış (single-shot) modunda inference
 * koşturulur: top1 güveni [DEAD_ZONE_CONFIDENCE] üzerindeyse tahmin "lock"lanır
 * ve [EMPTY_HAND_RESET_FRAMES] kadar ardışık "el yok" frame'i gelene dek yeni
 * tahmin üretilmez. Bu manuel testte değer okunurken tahminin kaymasını önler.
 */
class WordsViewModel(
    private val source: HandLandmarkerSource,
    private val inferenceManager: InferenceManager,
) : ViewModel() {

    private val _selectedModel = MutableStateFlow(ModelType.LSTM_SINGLE_WORDS)
    val selectedModel: StateFlow<ModelType> = _selectedModel.asStateFlow()

    private val _result = MutableStateFlow<ClassificationResult?>(null)
    val result: StateFlow<ClassificationResult?> = _result.asStateFlow()

    private val _fillCount = MutableStateFlow(0)
    val fillCount: StateFlow<Int> = _fillCount.asStateFlow()

    private val _countdownRemainingFrames = MutableStateFlow(0)
    val countdownRemainingFrames: StateFlow<Int> = _countdownRemainingFrames.asStateFlow()
    val countdownTotalFrames: Int = COUNTDOWN_FRAMES

    private val buffer = SequenceBuffer()
    val seqLen: Int get() = buffer.seqLen

    private val inFlight = AtomicBoolean(false)

    private var locked = false
    private var emptyHandFrames = 0
    private var countdownFrames = 0

    init {
        // HandLandmarker'ı arka planda ısıt — GPU shader compile + memory alloc
        // 1-3 sn sürer. Kamera frame göndermeden hazır olsun, yoksa ilk frame
        // analyzer thread'inde bloklar ve FPS/detection birkaç saniye gelmez.
        viewModelScope.launch(Dispatchers.IO) {
            source.ensureInitialized()
        }

        viewModelScope.launch {
            source.state.collect { state ->
                if (locked) {
                    // Tahmin sabit; el indirildiğinde yeni sequence için reset.
                    if (state.hands.isEmpty()) {
                        emptyHandFrames++
                        if (emptyHandFrames >= EMPTY_HAND_RESET_FRAMES) {
                            buffer.reset()
                            _fillCount.value = 0
                            locked = false
                            emptyHandFrames = 0
                        }
                    } else {
                        emptyHandFrames = 0
                    }
                    return@collect
                }

                // Frame toplamadan önce 1 sn'lik "hazır olun" fazı: kullanıcı
                // elini kameraya kaldırınca countdown başlar, ilk frame'i
                // istemediği bir poz/açıyla yakalamayalım diye.
                if (buffer.fillCount == 0 && countdownFrames < COUNTDOWN_FRAMES) {
                    if (state.hands.isEmpty()) {
                        countdownFrames = 0
                        _countdownRemainingFrames.value = 0
                        return@collect
                    }
                    countdownFrames++
                    _countdownRemainingFrames.value = COUNTDOWN_FRAMES - countdownFrames
                    if (countdownFrames < COUNTDOWN_FRAMES) {
                        return@collect
                    }
                    // Countdown bitti — bu frame'i de buffer'a alalım.
                    _countdownRemainingFrames.value = 0
                }

                val feat = frameWordFeature(state.hands)
                buffer.push(feat)
                _fillCount.value = buffer.fillCount

                if (!buffer.isFull) return@collect
                if (!inFlight.compareAndSet(false, true)) return@collect
                try {
                    val model = _selectedModel.value
                    val snapshot = buffer.snapshot()
                    val r = withContext(Dispatchers.Default) {
                        inferenceManager.classifyWords(model, snapshot, state.timestampMs)
                    }
                    val top1 = r?.top3?.firstOrNull()?.confidence ?: 0f
                    // Ölü-bölge: buffer henüz gerçek işareti içermiyorsa (ör. el
                    // yeni girdi), top1 uniform'a yakın çıkar — lock'lama, kayan
                    // pencerede bir sonraki frame'de yeniden dene.
                    if (r != null && top1 >= DEAD_ZONE_CONFIDENCE) {
                        _result.value = r
                        locked = true
                        emptyHandFrames = 0
                        countdownFrames = 0
                    }
                } finally {
                    inFlight.set(false)
                }
            }
        }
    }

    fun selectModel(t: ModelType) {
        if (_selectedModel.value == t) return
        _selectedModel.value = t
        _result.value = null
        buffer.reset()
        _fillCount.value = 0
        locked = false
        emptyHandFrames = 0
        countdownFrames = 0
        _countdownRemainingFrames.value = 0
    }

    private companion object {
        const val DEAD_ZONE_CONFIDENCE = 0.10f
        const val EMPTY_HAND_RESET_FRAMES = 8
        const val COUNTDOWN_FRAMES = 30
    }
}
