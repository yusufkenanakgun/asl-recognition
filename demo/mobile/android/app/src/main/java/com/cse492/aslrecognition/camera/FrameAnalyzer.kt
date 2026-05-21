package com.cse492.aslrecognition.camera

import android.os.SystemClock
import androidx.camera.core.ImageAnalysis
import androidx.camera.core.ImageProxy
import com.cse492.aslrecognition.mediapipe.HandLandmarkerSource
import com.cse492.aslrecognition.util.FpsMeter
import com.google.mediapipe.framework.image.BitmapImageBuilder

/**
 * CameraX [ImageAnalysis.Analyzer]. CameraSurface tarafında
 * [ImageAnalysis.Builder.setOutputImageRotationEnabled] açık olduğu için
 * ImageProxy zaten upright gelir — buradaki [ImageProxy.toBitmap] dönüşümü
 * dışında bitmap allocation yok.
 */
class FrameAnalyzer(
    private val source: HandLandmarkerSource,
    private val fpsMeter: FpsMeter,
) : ImageAnalysis.Analyzer {

    override fun analyze(image: ImageProxy) {
        val now = SystemClock.uptimeMillis()
        try {
            source.ensureInitialized()
            val upright = image.toBitmap()
            source.latestBitmap = upright
            val mpImage = BitmapImageBuilder(upright).build()
            source.detectAsync(mpImage, timestampMs = now)
            fpsMeter.tick(now)
        } finally {
            image.close()
        }
    }
}
