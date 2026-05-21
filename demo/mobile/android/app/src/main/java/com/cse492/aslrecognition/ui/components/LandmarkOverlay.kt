package com.cse492.aslrecognition.ui.components

import androidx.compose.foundation.Canvas
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.StrokeCap
import com.cse492.aslrecognition.mediapipe.HandsState
import com.cse492.aslrecognition.ui.theme.AppColors

/** MediaPipe 21-landmark `HAND_CONNECTIONS` listesi. */
private val HandConnections = listOf(
    // Thumb
    0 to 1, 1 to 2, 2 to 3, 3 to 4,
    // Index
    0 to 5, 5 to 6, 6 to 7, 7 to 8,
    // Middle
    5 to 9, 9 to 10, 10 to 11, 11 to 12,
    // Ring
    9 to 13, 13 to 14, 14 to 15, 15 to 16,
    // Pinky
    13 to 17, 17 to 18, 18 to 19, 19 to 20,
    // Palm
    0 to 17,
)

@Composable
fun LandmarkOverlay(
    state: HandsState,
    modifier: Modifier = Modifier,
) {
    val line = AppColors.Teal
    val dot = AppColors.Teal
    val halo = AppColors.Teal.copy(alpha = 0.20f)

    Canvas(modifier = modifier) {
        // Ön kamera PreviewView'da yatay aynalanmış görünür ama MediaPipe
        // ham (aynalanmamış) bitmap'i işliyor → landmark x'lerini ters çevir.
        for (hand in state.hands) {
            val lms = hand.landmarks
            if (lms.size < 21) continue
            // Connections
            for ((a, b) in HandConnections) {
                val pa = lms[a]
                val pb = lms[b]
                drawLine(
                    color = line,
                    start = Offset((1f - pa.x) * size.width, pa.y * size.height),
                    end = Offset((1f - pb.x) * size.width, pb.y * size.height),
                    strokeWidth = 5f,
                    cap = StrokeCap.Round,
                )
            }
            // Points (wrist büyük, diğerleri küçük)
            for ((i, lm) in lms.withIndex()) {
                val center = Offset((1f - lm.x) * size.width, lm.y * size.height)
                val r = if (i == 0) 7.5f else 5f
                drawCircle(color = halo, radius = r * 1.6f, center = center)
                drawCircle(color = dot, radius = r, center = center)
            }
        }
    }
}

