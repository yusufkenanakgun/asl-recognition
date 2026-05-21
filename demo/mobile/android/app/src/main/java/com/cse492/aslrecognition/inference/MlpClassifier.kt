package com.cse492.aslrecognition.inference

import android.content.Context
import android.os.SystemClock
import com.cse492.aslrecognition.labels.LETTER_CLASSES
import java.io.Closeable

/**
 * 63-dim landmark → 29-class logits MLP. Eager-load (model 240 KB).
 */
class MlpClassifier(context: Context) : Closeable {

    private val runner = TFLiteRunner(context, MODEL_ASSET, numThreads = 2)
    private val input = Array(1) { FloatArray(63) }
    private val output = Array(1) { FloatArray(LETTER_CLASSES.size) }

    /**
     * @param features 63-dim normalize edilmiş landmark vektörü.
     * @return ClassificationResult (top-3 + latency).
     */
    fun classify(features: FloatArray, timestampMs: Long): ClassificationResult {
        require(features.size == 63) { "MLP girdisi 63 olmalı, ${features.size} geldi" }
        features.copyInto(input[0])
        val t0 = SystemClock.uptimeMillis()
        runner.interpreter.run(input, output)
        val latency = SystemClock.uptimeMillis() - t0
        val probs = softmax(output[0])
        return ClassificationResult(
            model = ModelType.MLP_LETTERS,
            top3 = topThreeLetters(probs),
            inferenceMs = latency,
            timestampMs = timestampMs,
        )
    }

    override fun close() = runner.close()

    companion object {
        private const val MODEL_ASSET = "models/mlp_landmark.tflite"
    }
}
