package com.cse492.aslrecognition.preprocessing

import com.cse492.aslrecognition.mediapipe.HandsState

/**
 * LSTM word classifier için frame başı 128-dim feature vektörü.
 *
 * Yapı (eğitimle birebir, `src/faz6/extract_v2.py:50-51, 133-151`):
 *   left  slot (64): [presence(1), x0,y0,z0, ..., x20,y20,z20]   (normalize edilmiş)
 *   right slot (64): [presence(1), x0,y0,z0, ..., x20,y20,z20]
 *   concat → 128
 *
 * El yoksa veya dejenere ise ilgili slot tamamen sıfır kalır (presence=0).
 * Handedness MediaPipe'tan ham gelir ("Left" / "Right"); arka kamerada ayna
 * yok, training pipeline ile aynı semantiği taşıyor.
 */
private const val HAND_FEAT_DIM = 64    // 1 presence + 21*3 coords
const val WORD_FEATURE_DIM = 128        // left + right

fun frameWordFeature(hands: List<HandsState.Hand>): FloatArray {
    val out = FloatArray(WORD_FEATURE_DIM)  // all zeros
    for (hand in hands) {
        val coords = normalizeLandmarks(hand) ?: continue
        val offset = if (hand.handedness == "Left") 0 else HAND_FEAT_DIM
        out[offset] = 1.0f                  // presence
        coords.copyInto(out, offset + 1)    // 63 normalize coords
    }
    return out
}
