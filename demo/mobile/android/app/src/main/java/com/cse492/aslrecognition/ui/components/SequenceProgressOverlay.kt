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

/**
 * LSTM sliding window dolarken bottom panel'de gösterilen ilerleme indikator'ı.
 * 32 frame dolunca kaybolur, yerini Top3Panel alır.
 */
@Composable
fun SequenceProgressOverlay(
    filled: Int,
    total: Int,
    modifier: Modifier = Modifier,
) {
    val fraction = (filled.toFloat() / total).coerceIn(0f, 1f)
    Column(
        modifier = modifier
            .fillMaxSize()
            .background(AppColors.Background),
        verticalArrangement = Arrangement.Center,
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Text(
            text = stringResource(R.string.words_collecting_title),
            style = MaterialTheme.typography.titleSmall,
            color = AppColors.TextSecondary,
        )
        Spacer(Modifier.height(6.dp))
        Text(
            text = "$filled / $total",
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
            text = stringResource(R.string.words_collecting_subtitle),
            style = MaterialTheme.typography.bodySmall,
            color = AppColors.TextTertiary,
        )
    }
}
