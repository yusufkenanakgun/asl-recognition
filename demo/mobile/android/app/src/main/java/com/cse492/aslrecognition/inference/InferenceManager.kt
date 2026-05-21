package com.cse492.aslrecognition.inference

import android.content.Context
import android.graphics.Bitmap
import com.cse492.aslrecognition.mediapipe.HandsState
import com.cse492.aslrecognition.preprocessing.cropHandTo224
import com.cse492.aslrecognition.preprocessing.normalizeLandmarks
import java.io.Closeable

/**
 * Sınıflandırıcılar için tek noktadan giriş. ModelType'a göre route eder.
 * MLP eager, EfficientNet/LSTM/Ensemble lazy (kullanıcı toggle ettiğinde
 * ilk çağrıda yüklenir).
 */
class InferenceManager(private val context: Context) : Closeable {

    private val mlpLazy = lazy { MlpClassifier(context) }
    private val efficientNetLazy = lazy { EfficientNetClassifier(context) }
    private val lstmSingleLazy = lazy {
        LstmClassifier(context, "models/lstm_single_best.tflite")
    }
    private val lstmEnsembleLazy = lazy { EnsembleLstmClassifier(context) }

    val mlp: MlpClassifier get() = mlpLazy.value
    val efficientNet: EfficientNetClassifier get() = efficientNetLazy.value
    val lstmSingle: LstmClassifier get() = lstmSingleLazy.value
    val lstmEnsemble: EnsembleLstmClassifier get() = lstmEnsembleLazy.value

    /** İlk frame'den önce MLP'yi sıcak başlat (modül ~240 KB, hızlıdır). */
    fun preloadMlp() {
        mlpLazy.value
    }

    /**
     * Letters sekmesinin sınıflandırması. El yoksa veya gerekli girdiler
     * eksikse null döner.
     */
    fun classifyLetters(
        modelType: ModelType,
        hand: HandsState.Hand?,
        bitmap: Bitmap?,
        timestampMs: Long,
    ): ClassificationResult? {
        if (hand == null) return null
        return when (modelType) {
            ModelType.MLP_LETTERS -> {
                val feats = normalizeLandmarks(hand) ?: return null
                mlp.classify(feats, timestampMs)
            }
            ModelType.EFFICIENTNET_LETTERS -> {
                if (bitmap == null) return null
                val cropped = cropHandTo224(bitmap, hand) ?: return null
                try {
                    efficientNet.classify(cropped, timestampMs)
                } finally {
                    cropped.recycle()
                }
            }
            else -> null
        }
    }

    /**
     * Words sekmesinin sınıflandırması. Sekans buffer dolu olduğunda
     * ViewModel çağırır. Ensemble paralel olduğu için suspend.
     */
    suspend fun classifyWords(
        modelType: ModelType,
        seq: Array<Array<FloatArray>>,
        timestampMs: Long,
    ): ClassificationResult? = when (modelType) {
        ModelType.LSTM_SINGLE_WORDS -> lstmSingle.classify(seq, timestampMs, modelType)
        ModelType.LSTM_ENSEMBLE_WORDS -> lstmEnsemble.classify(seq, timestampMs)
        else -> null
    }

    override fun close() {
        if (mlpLazy.isInitialized()) mlpLazy.value.close()
        if (efficientNetLazy.isInitialized()) efficientNetLazy.value.close()
        if (lstmSingleLazy.isInitialized()) lstmSingleLazy.value.close()
        if (lstmEnsembleLazy.isInitialized()) lstmEnsembleLazy.value.close()
    }
}
