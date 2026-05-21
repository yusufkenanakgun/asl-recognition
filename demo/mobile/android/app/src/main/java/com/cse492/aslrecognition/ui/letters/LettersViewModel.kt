package com.cse492.aslrecognition.ui.letters

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.cse492.aslrecognition.inference.ClassificationResult
import com.cse492.aslrecognition.inference.InferenceManager
import com.cse492.aslrecognition.inference.ModelType
import com.cse492.aslrecognition.mediapipe.HandLandmarkerSource
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.collect
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.util.concurrent.atomic.AtomicBoolean

/**
 * Letters sekmesinin sınıflandırma orkestrasyonu.
 *
 * `HandLandmarkerSource.state` her güncellendiğinde, [_selectedModel] ile
 * inference koşar. EfficientNet yavaş olabileceği için [inFlight] guard'ı
 * önceki inference bitmeden yeni iş tetiklemez (KEEP_ONLY_LATEST analog).
 */
class LettersViewModel(
    private val source: HandLandmarkerSource,
    private val inferenceManager: InferenceManager,
) : ViewModel() {

    private val _selectedModel = MutableStateFlow(ModelType.MLP_LETTERS)
    val selectedModel: StateFlow<ModelType> = _selectedModel.asStateFlow()

    private val _result = MutableStateFlow<ClassificationResult?>(null)
    val result: StateFlow<ClassificationResult?> = _result.asStateFlow()

    private val inFlight = AtomicBoolean(false)

    init {
        // MLP eager preload — UI ilk MLP frame'inde takılmasın.
        inferenceManager.preloadMlp()

        // HandLandmarker'ı arka planda ısıt — GPU shader compile + memory alloc
        // 1-3 sn sürer. Kamera frame göndermeden hazır olsun, yoksa ilk frame
        // analyzer thread'inde bloklar ve FPS/detection birkaç saniye gelmez.
        viewModelScope.launch(Dispatchers.IO) {
            source.ensureInitialized()
        }

        viewModelScope.launch {
            source.state.collect { state ->
                if (!inFlight.compareAndSet(false, true)) return@collect
                try {
                    val model = _selectedModel.value
                    val hand = state.hands.firstOrNull()
                    val bmp = if (model == ModelType.EFFICIENTNET_LETTERS) source.latestBitmap else null
                    val r = withContext(Dispatchers.Default) {
                        inferenceManager.classifyLetters(model, hand, bmp, state.timestampMs)
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
        _result.value = null
    }
}
