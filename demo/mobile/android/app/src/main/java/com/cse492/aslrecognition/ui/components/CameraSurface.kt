package com.cse492.aslrecognition.ui.components

import android.util.Log
import android.util.Size
import androidx.camera.core.CameraSelector
import androidx.camera.core.ImageAnalysis
import androidx.camera.core.Preview
import androidx.camera.core.resolutionselector.ResolutionSelector
import androidx.camera.core.resolutionselector.ResolutionStrategy
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.camera.view.PreviewView
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.viewinterop.AndroidView
import androidx.core.content.ContextCompat
import androidx.lifecycle.compose.LocalLifecycleOwner
import java.util.concurrent.Executors

/**
 * CameraX [PreviewView] + [ImageAnalysis] bağlama. Back camera,
 * RGBA_8888 çıkışı (FrameAnalyzer doğrudan Bitmap'e dönüştürür),
 * KEEP_ONLY_LATEST back-pressure, tek thread analyzer.
 */
@Composable
fun CameraSurface(
    analyzer: ImageAnalysis.Analyzer,
    modifier: Modifier = Modifier,
) {
    val ctx = LocalContext.current
    val owner = LocalLifecycleOwner.current
    val executor = remember { Executors.newSingleThreadExecutor() }
    val previewView = remember {
        PreviewView(ctx).apply {
            scaleType = PreviewView.ScaleType.FILL_CENTER
            implementationMode = PreviewView.ImplementationMode.COMPATIBLE
        }
    }

    DisposableEffect(Unit) {
        val future = ProcessCameraProvider.getInstance(ctx)
        future.addListener({
            try {
                val provider = future.get()
                val preview = Preview.Builder().build().apply {
                    setSurfaceProvider(previewView.surfaceProvider)
                }
                // 640×480 sensör (portrait'te 480×640) hand detection için
                // fazlasıyla yeter; toBitmap + matrix rotation maliyetini düşürür.
                val resolution = ResolutionSelector.Builder()
                    .setResolutionStrategy(
                        ResolutionStrategy(
                            Size(640, 480),
                            ResolutionStrategy.FALLBACK_RULE_CLOSEST_LOWER_THEN_HIGHER,
                        ),
                    )
                    .build()
                val analysis = ImageAnalysis.Builder()
                    .setBackpressureStrategy(ImageAnalysis.STRATEGY_KEEP_ONLY_LATEST)
                    .setOutputImageFormat(ImageAnalysis.OUTPUT_IMAGE_FORMAT_RGBA_8888)
                    .setResolutionSelector(resolution)
                    // CameraX'in kendi rotation pipeline'ı: ImageProxy.toBitmap()
                    // upright gelir. FrameAnalyzer'da Matrix.postRotate ile
                    // 1.2 MB/frame ekstra bitmap allocate etmeyiz.
                    .setOutputImageRotationEnabled(true)
                    .build()
                analysis.setAnalyzer(executor, analyzer)

                provider.unbindAll()
                provider.bindToLifecycle(
                    owner,
                    CameraSelector.DEFAULT_FRONT_CAMERA,
                    preview,
                    analysis,
                )
            } catch (e: Exception) {
                Log.e(TAG, "Camera bind failed", e)
            }
        }, ContextCompat.getMainExecutor(ctx))

        onDispose {
            // unbindAll burada KASITLI olarak çağrılmıyor.
            // Why: Letters↔Words tab geçişinde yeni ekran bind path'i zaten
            // başta `provider.unbindAll()` çağırıyor. Buradan async tekrar
            // çağırırsak race oluşuyor: yeni bind'den sonra bizim geç gelen
            // unbindAll yetişiyor ve yeni kamerayı kapatıyor → ekran donuyor.
            // Lifecycle owner DESTROYED'a giderse CameraX bağlamayı otomatik
            // temizliyor; biri yeni binding alıyorsa o da kendi unbindAll'ünü
            // yapıyor. Burada sadece analyzer executor'ı kapatmak yeterli.
            executor.shutdown()
        }
    }

    AndroidView(factory = { previewView }, modifier = modifier)
}

private const val TAG = "CameraSurface"
