package com.cse492.aslrecognition.preprocessing

import com.cse492.aslrecognition.mediapipe.HandsState
import kotlin.math.sqrt

/**
 * MLP girdisi için landmark normalizasyonu. Eğitimle birebir:
 *   1) coords[i] -= coords[0]  (wrist origin)
 *   2) scale = ||coords[9]||   (middle finger MCP)
 *   3) coords /= scale
 *   4) flatten [x0,y0,z0, ..., x20,y20,z20]  → 63 dim
 *
 * Referans: `src/extract_landmarks.py:53-71`.
 *
 * @return 63 elemanlı FloatArray, ya da scale=0 ise null (dejenere el).
 */
fun normalizeLandmarks(hand: HandsState.Hand): FloatArray? {
    val lms = hand.landmarks
    if (lms.size < 21) return null

    val wx = lms[0].x; val wy = lms[0].y; val wz = lms[0].z
    val mx = lms[9].x - wx
    val my = lms[9].y - wy
    val mz = lms[9].z - wz
    val scale = sqrt(mx * mx + my * my + mz * mz)
    if (scale <= 0f || !scale.isFinite()) return null

    val out = FloatArray(63)
    var i = 0
    for (lm in lms) {
        out[i++] = (lm.x - wx) / scale
        out[i++] = (lm.y - wy) / scale
        out[i++] = (lm.z - wz) / scale
    }
    return out
}
