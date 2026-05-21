package com.cse492.aslrecognition.inference

import android.content.Context
import android.os.SystemClock
import com.cse492.aslrecognition.labels.WORD_CLASSES
import java.io.Closeable

/**
 * Tek bir BiLSTM word classifier wrapper'ı (5.6 MB).
 *
 * Input  : (1, 32, 128)  float32
 * Output : (1, 100)      float32 logits
 *
 * Lazy load — kullanıcı Words sekmesine ilk girdiğinde ~300 ms yüklenir.
 *
 * `classifyToProbs` ham softmax döner; ensemble bu API'yi kullanır.
 * `classify` doğrudan tek model sınıflandırması için top-3 döner.
 */
class LstmClassifier(
    private val context: Context,
    private val modelAsset: String,
) : Closeable {

    private var runner: TFLiteRunner? = null
    private val output = Array(1) { FloatArray(WORD_CLASSES.size) }

    @Synchronized
    private fun ensureLoaded(): TFLiteRunner {
        runner?.let { return it }
        val r = TFLiteRunner(context, modelAsset, numThreads = 2)
        runner = r
        return r
    }

    /** Ham softmax olasılıkları (100,). Ensemble için. */
    @Synchronized
    fun classifyToProbs(seq: Array<Array<FloatArray>>): FloatArray {
        val r = ensureLoaded()
        r.interpreter.run(seq, output)
        return softmax(output[0])
    }

    /** Tek model — top-3 + latency. */
    fun classify(
        seq: Array<Array<FloatArray>>,
        timestampMs: Long,
        modelType: ModelType,
    ): ClassificationResult {
        val t0 = SystemClock.uptimeMillis()
        val probs = classifyToProbs(seq)
        val latency = SystemClock.uptimeMillis() - t0
        return ClassificationResult(
            model = modelType,
            top3 = topThreeWords(probs),
            inferenceMs = latency,
            timestampMs = timestampMs,
        )
    }

    @Synchronized
    override fun close() {
        runner?.close()
        runner = null
    }
}
