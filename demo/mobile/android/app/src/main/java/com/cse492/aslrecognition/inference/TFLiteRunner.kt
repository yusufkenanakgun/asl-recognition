package com.cse492.aslrecognition.inference

import android.content.Context
import android.util.Log
import com.cse492.aslrecognition.util.loadModelFile
import org.tensorflow.lite.Interpreter
import org.tensorflow.lite.gpu.CompatibilityList
import org.tensorflow.lite.gpu.GpuDelegate
import java.io.Closeable

/**
 * Tek bir TFLite modelinin yaşam döngüsünü yönetir.
 *
 * Delegate seçimi:
 *  - [useGpu] = true ise cihaz uyumluysa GpuDelegate kullanılır, init
 *    başarısızsa otomatik CPU+XNNPACK'e düşer.
 *  - [useGpu] = false (varsayılan) → XNNPACK CPU delegate (multi-thread).
 *
 * GPU yolu özellikle EfficientNet (conv-heavy) için 3-4x hızlanma sağlar;
 * MLP ve LSTM küçük olduğundan GPU overhead'i fayda etmez → CPU kalsın.
 */
class TFLiteRunner(
    context: Context,
    modelAssetPath: String,
    numThreads: Int = 2,
    useGpu: Boolean = false,
) : Closeable {

    val interpreter: Interpreter
    private var gpuDelegate: GpuDelegate? = null
    val usingGpu: Boolean

    init {
        val modelBuffer = context.loadModelFile(modelAssetPath)

        var gpu: GpuDelegate? = null
        if (useGpu) {
            try {
                val compat = CompatibilityList()
                if (compat.isDelegateSupportedOnThisDevice) {
                    val gpuOpts = compat.bestOptionsForThisDevice
                    gpu = GpuDelegate(gpuOpts)
                } else {
                    Log.w(TAG, "GPU delegate cihazda desteklenmiyor: $modelAssetPath")
                }
            } catch (e: Throwable) {
                Log.w(TAG, "GPU compat check başarısız: $modelAssetPath", e)
            }
        }

        var built: Interpreter? = null
        if (gpu != null) {
            val opts = Interpreter.Options().apply {
                setNumThreads(numThreads)
                addDelegate(gpu)
            }
            try {
                built = Interpreter(modelBuffer, opts)
            } catch (e: Throwable) {
                Log.w(TAG, "GPU init başarısız, CPU'ya düşülüyor: $modelAssetPath", e)
                gpu.close()
                gpu = null
            }
        }

        if (built == null) {
            val opts = Interpreter.Options().apply { setNumThreads(numThreads) }
            built = Interpreter(modelBuffer, opts)
        }

        interpreter = built
        gpuDelegate = gpu
        usingGpu = gpu != null
        Log.i(TAG, "$modelAssetPath -> delegate=${if (usingGpu) "GPU" else "CPU"}")
    }

    override fun close() {
        interpreter.close()
        gpuDelegate?.close()
        gpuDelegate = null
    }

    companion object {
        private const val TAG = "TFLiteRunner"
    }
}
