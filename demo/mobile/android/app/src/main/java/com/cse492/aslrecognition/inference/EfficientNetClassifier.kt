package com.cse492.aslrecognition.inference

import android.content.Context
import android.graphics.Bitmap
import android.os.SystemClock
import com.cse492.aslrecognition.labels.LETTER_CLASSES
import com.cse492.aslrecognition.preprocessing.bitmapToImageNetBuffer
import com.cse492.aslrecognition.util.newDirectByteBuffer
import java.io.Closeable
import java.nio.ByteBuffer

/**
 * 224×224 RGB Bitmap (zaten crop edilmiş) → 29-class logits EfficientNet-B0.
 * TFLite NHWC [1, 224, 224, 3] float32 girdi (onnx2tf NCHW→NHWC çevirisi yapıyor).
 *
 * Lazy load: ilk classify çağrısında interpreter oluşturulur (~500 ms).
 */
class EfficientNetClassifier(private val context: Context) : Closeable {

    private var runner: TFLiteRunner? = null
    private val inputBuffer: ByteBuffer = newDirectByteBuffer(1 * 224 * 224 * 3 * 4)
    private val output = Array(1) { FloatArray(LETTER_CLASSES.size) }

    @Synchronized
    private fun ensureLoaded(): TFLiteRunner {
        runner?.let { return it }
        // GPU dene; conv-heavy 4M parametreli model için en büyük kazanç.
        // Cihaz uyumsuzsa TFLiteRunner CPU+XNNPACK'e otomatik düşer.
        val r = TFLiteRunner(context, MODEL_ASSET, numThreads = 4, useGpu = true)
        runner = r
        return r
    }

    /**
     * @param bitmap 224×224 RGB (zaten crop edilmiş)
     */
    fun classify(bitmap: Bitmap, timestampMs: Long): ClassificationResult {
        val r = ensureLoaded()
        bitmapToImageNetBuffer(bitmap, inputBuffer)
        val t0 = SystemClock.uptimeMillis()
        r.interpreter.run(inputBuffer, output)
        val latency = SystemClock.uptimeMillis() - t0
        val probs = softmax(output[0])
        return ClassificationResult(
            model = ModelType.EFFICIENTNET_LETTERS,
            top3 = topThreeLetters(probs),
            inferenceMs = latency,
            timestampMs = timestampMs,
        )
    }

    @Synchronized
    override fun close() {
        runner?.close()
        runner = null
    }

    companion object {
        private const val MODEL_ASSET = "models/efficientnet_b0.tflite"
    }
}
