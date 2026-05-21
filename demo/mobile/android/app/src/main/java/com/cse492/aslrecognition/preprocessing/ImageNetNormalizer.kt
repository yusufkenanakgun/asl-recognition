package com.cse492.aslrecognition.preprocessing

import android.graphics.Bitmap
import com.cse492.aslrecognition.util.newDirectByteBuffer
import java.nio.ByteBuffer

/**
 * 224×224 ARGB_8888 Bitmap'i 1×224×224×3 NHWC RGB FloatBuffer'a yazar,
 * ImageNet mean/std ile normalize eder. Eğitimle birebir
 * (`src/dataset.py:55-83`).
 *
 * Reuse: aynı buffer'ı her inference'ta yeniden kullanmak için
 * `target` parametresi geçirilebilir; verilmezse yeni allocate edilir.
 */
private const val SIZE = 224
private const val PIXELS = SIZE * SIZE
private const val BYTES = 1 * PIXELS * 3 * 4  // float32 NHWC

private val MEAN = floatArrayOf(0.485f, 0.456f, 0.406f)
private val STD = floatArrayOf(0.229f, 0.224f, 0.225f)

private val INV_STD_R = 1f / STD[0]
private val INV_STD_G = 1f / STD[1]
private val INV_STD_B = 1f / STD[2]

fun bitmapToImageNetBuffer(bmp: Bitmap, target: ByteBuffer? = null): ByteBuffer {
    require(bmp.width == SIZE && bmp.height == SIZE) { "Beklenen ${SIZE}x${SIZE}, gelen ${bmp.width}x${bmp.height}" }
    val buf = (target ?: newDirectByteBuffer(BYTES)).apply { rewind() }

    val pixels = IntArray(PIXELS)
    bmp.getPixels(pixels, 0, SIZE, 0, 0, SIZE, SIZE)

    // ARGB_8888 → RGB float (NHWC: H,W,C sırası)
    for (p in pixels) {
        val r = ((p shr 16) and 0xFF) / 255f
        val g = ((p shr 8) and 0xFF) / 255f
        val b = (p and 0xFF) / 255f
        buf.putFloat((r - MEAN[0]) * INV_STD_R)
        buf.putFloat((g - MEAN[1]) * INV_STD_G)
        buf.putFloat((b - MEAN[2]) * INV_STD_B)
    }
    buf.rewind()
    return buf
}
