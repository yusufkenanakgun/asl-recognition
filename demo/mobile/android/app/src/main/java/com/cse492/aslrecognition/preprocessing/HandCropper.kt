package com.cse492.aslrecognition.preprocessing

import android.graphics.Bitmap
import com.cse492.aslrecognition.mediapipe.HandsState
import kotlin.math.max
import kotlin.math.min
import kotlin.math.roundToInt

/**
 * 21 landmark'tan hand bbox hesapla, ±%30 padding, kare yap, kırp, 224×224
 * resize. Girdi bitmap upright (zaten döndürülmüş) varsayılır.
 *
 * @return 224×224 RGB Bitmap, ya da el frame dışındaysa null.
 */
private const val OUT_SIZE = 224
private const val PADDING_RATIO = 0.30f

fun cropHandTo224(source: Bitmap, hand: HandsState.Hand): Bitmap? {
    val lms = hand.landmarks
    if (lms.size < 21) return null

    val w = source.width.toFloat()
    val h = source.height.toFloat()

    var minX = Float.POSITIVE_INFINITY
    var maxX = Float.NEGATIVE_INFINITY
    var minY = Float.POSITIVE_INFINITY
    var maxY = Float.NEGATIVE_INFINITY
    for (lm in lms) {
        if (lm.x < minX) minX = lm.x
        if (lm.x > maxX) maxX = lm.x
        if (lm.y < minY) minY = lm.y
        if (lm.y > maxY) maxY = lm.y
    }

    // Normalize → piksel
    val bx = minX * w
    val by = minY * h
    val bw = (maxX - minX) * w
    val bh = (maxY - minY) * h

    // Kare bbox: uzun kenarı al
    val side = max(bw, bh) * (1f + 2f * PADDING_RATIO)
    val cx = bx + bw / 2f
    val cy = by + bh / 2f

    var left = (cx - side / 2f).roundToInt()
    var top = (cy - side / 2f).roundToInt()
    var sideInt = side.roundToInt()

    // Frame içinde tut (sınır taşmasını basit kırpma ile yönet)
    left = max(0, left)
    top = max(0, top)
    sideInt = min(sideInt, min(source.width - left, source.height - top))
    if (sideInt < 8) return null  // dejenere

    val cropped = Bitmap.createBitmap(source, left, top, sideInt, sideInt)
    return if (cropped.width == OUT_SIZE && cropped.height == OUT_SIZE) {
        cropped
    } else {
        val resized = Bitmap.createScaledBitmap(cropped, OUT_SIZE, OUT_SIZE, true)
        if (resized !== cropped) cropped.recycle()
        resized
    }
}
