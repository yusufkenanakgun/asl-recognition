package com.cse492.aslrecognition.inference

import com.cse492.aslrecognition.labels.LETTER_CLASSES
import com.cse492.aslrecognition.labels.WORD_CLASSES
import kotlin.math.exp

/** Numerik stabil softmax (logits → olasılık). In-place değil. */
fun softmax(logits: FloatArray): FloatArray {
    var max = Float.NEGATIVE_INFINITY
    for (v in logits) if (v > max) max = v
    var sum = 0.0
    val out = FloatArray(logits.size)
    for (i in logits.indices) {
        val e = exp((logits[i] - max).toDouble())
        out[i] = e.toFloat()
        sum += e
    }
    val invSum = (1.0 / sum).toFloat()
    for (i in out.indices) out[i] *= invSum
    return out
}

/** Top-3 (label, conf) ASL letters için. */
fun topThreeLetters(probs: FloatArray): List<ClassificationResult.Prediction> =
    topThree(probs, LETTER_CLASSES)

/** Top-3 (label, conf) WLASL words için. */
fun topThreeWords(probs: FloatArray): List<ClassificationResult.Prediction> =
    topThree(probs, WORD_CLASSES)

private fun topThree(
    probs: FloatArray,
    classes: List<String>,
): List<ClassificationResult.Prediction> {
    require(probs.size == classes.size) {
        "probs size ${probs.size} != classes size ${classes.size}"
    }
    val idxs = probs.indices.sortedByDescending { probs[it] }
    return idxs.take(3).map { i ->
        ClassificationResult.Prediction(label = classes[i], confidence = probs[i])
    }
}
