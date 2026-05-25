package com.cse492.aslrecognition.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.unit.dp
import com.cse492.aslrecognition.R
import com.cse492.aslrecognition.ui.theme.AppColors
import kotlin.math.ceil

/**
 * Frame toplamaya başlamadan önceki "hazır olun" geri sayım göstergesi.
 * El kameraya gelince [remainingFrames] [totalFrames]'den 0'a sayar.
 */
@Composable
fun CountdownOverlay(
    remainingFrames: Int,
    totalFrames: Int,
    modifier: Modifier = Modifier,
) {
    val elapsed = (totalFrames - remainingFrames).coerceIn(0, totalFrames)
    val fraction = if (totalFrames <= 0) 0f else elapsed.toFloat() / totalFrames
    val remainingSeconds = ceil(remainingFrames / 30f).toInt().coerceAtLeast(0)
    Column(
        modifier = modifier
            .fillMaxSize()
            .background(AppColors.Background),
        verticalArrangement = Arrangement.Center,
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Text(
            text = stringResource(R.string.words_get_ready_title),
            style = MaterialTheme.typography.titleSmall,
            color = AppColors.TextSecondary,
        )
        Spacer(Modifier.height(6.dp))
        Text(
            text = "${remainingSeconds}s",
            style = MaterialTheme.typography.bodySmall.copy(fontFamily = FontFamily.Monospace),
            color = AppColors.TextTertiary,
        )
        Spacer(Modifier.height(14.dp))
        Box(
            modifier = Modifier
                .fillMaxWidth(0.65f)
                .height(8.dp)
                .clip(RoundedCornerShape(100))
                .background(AppColors.TealSoft),
        ) {
            Box(
                modifier = Modifier
                    .fillMaxWidth(fraction = fraction)
                    .height(8.dp)
                    .clip(RoundedCornerShape(100))
                    .background(AppColors.Teal),
            )
        }
        Spacer(Modifier.height(10.dp))
        Text(
            text = stringResource(R.string.words_get_ready_subtitle),
            style = MaterialTheme.typography.bodySmall,
            color = AppColors.TextTertiary,
        )
    }
}
