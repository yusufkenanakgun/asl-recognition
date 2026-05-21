package com.cse492.aslrecognition.ui.components

import androidx.annotation.StringRes
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color

/**
 * Letters/Words sekmelerinin paylaştığı iskelet: başlık çubuğu yok,
 * doğrudan tam ekran kamera + overlay. (titleRes geriye dönük uyumluluk
 * için tutuldu, kullanılmıyor.)
 */
@Suppress("UNUSED_PARAMETER")
@Composable
fun CameraTabScaffold(
    @StringRes titleRes: Int,
    content: @Composable () -> Unit,
) {
    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(Color.Black),
    ) {
        content()
    }
}
