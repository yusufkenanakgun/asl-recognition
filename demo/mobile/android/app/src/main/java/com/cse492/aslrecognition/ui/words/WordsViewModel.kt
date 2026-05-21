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
 * Her HandLandmarker state'inde 128-dim feature çıkarılır ve
 * 32-frame sliding window'a push edilir. Buffer dolunca her yeni frame'de
 * LSTM (single veya ensemble) inference koşturulur — [inFlight] guard
 * back-pressure için (ensemble ~50-100ms, MediaPipe ~30fps).
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

    private val buffer = SequenceBuffer()
    val seqLen: Int get() = buffer.seqLen

    private val inFlight = AtomicBoolean(false)

    init {
        // HandLandmarker'ı arka planda ısıt — GPU shader compile + memory alloc
        // 1-3 sn sürer. Kamera frame göndermeden hazır olsun, yoksa ilk frame
        // analyzer thread'inde bloklar ve FPS/detection birkaç saniye gelmez.
        viewModelScope.launch(Dispatchers.IO) {
            source.ensureInitialized()
        }

        viewModelScope.launch {
            source.state.collect { state ->
                // Feature extract + push: ucuz, doğrudan collect thread'inde yap.
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
                    _result.value = r
                } finally {
                    inFlight.set(false)
                }
            }
        }
    }

    fun selectModel(t: ModelType) {
        if (_selectedModel.value == t) return
        _selectedModel.value = t
        // Model değişti — eski tahminin yanıltıcı kalmaması için temizle.
        // Buffer aynı kalıyor; bir sonraki frame'de yeni model ile inference koşacak.
        _result.value = null
    }
}
