package com.cse492.aslrecognition.inference

data class ClassificationResult(
    val model: ModelType,
    val top3: List<Prediction>,
    val inferenceMs: Long,
    val timestampMs: Long,
) {
    data class Prediction(val label: String, val confidence: Float)

    companion object {
        fun empty(model: ModelType) = ClassificationResult(model, emptyList(), 0L, 0L)
    }
}
