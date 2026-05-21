package com.cse492.aslrecognition.mediapipe

import com.google.mediapipe.tasks.vision.handlandmarker.HandLandmarkerResult

/** MediaPipe HandLandmarker'dan Compose'a akan tek tip durum. */
data class HandsState(
    val hands: List<Hand>,
    val timestampMs: Long,
    val inferenceLatencyMs: Long,
) {
    data class Hand(
        val landmarks: List<Landmark>,
        val handedness: String, // "Left" or "Right"
    )

    data class Landmark(val x: Float, val y: Float, val z: Float)

    companion object {
        val Empty = HandsState(emptyList(), 0L, 0L)

        fun from(result: HandLandmarkerResult, inferenceLatencyMs: Long): HandsState {
            val landmarksPerHand = result.landmarks()
            val handednesses = result.handednesses()
            val hands = landmarksPerHand.indices.map { i ->
                val lms = landmarksPerHand[i].map { Landmark(it.x(), it.y(), it.z()) }
                val handed = handednesses.getOrNull(i)?.firstOrNull()?.categoryName() ?: "Unknown"
                Hand(lms, handed)
            }
            return HandsState(
                hands = hands,
                timestampMs = result.timestampMs(),
                inferenceLatencyMs = inferenceLatencyMs,
            )
        }
    }
}
