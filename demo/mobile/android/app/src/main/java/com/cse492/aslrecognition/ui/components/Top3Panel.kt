package com.cse492.aslrecognition.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.cse492.aslrecognition.inference.ClassificationResult
import com.cse492.aslrecognition.ui.theme.AppColors
import kotlin.math.roundToInt

@Composable
fun Top3Panel(
    rows: List<ClassificationResult.Prediction>,
    caption: String? = "TOP-3 PREDICTIONS",
    modifier: Modifier = Modifier,
) {
    Column(modifier = modifier) {
        if (caption != null) {
            Text(
                text = caption,
                style = MaterialTheme.typography.labelSmall,
                color = AppColors.TextTertiary,
            )
            Spacer(Modifier.height(12.dp))
        }
        Column(verticalArrangement = Arrangement.spacedBy(14.dp)) {
            rows.forEachIndexed { i, p -> Top3Row(rank = i + 1, prediction = p) }
        }
    }
}

@Composable
private fun Top3Row(rank: Int, prediction: ClassificationResult.Prediction) {
    val top = rank == 1
    val labelStyle = if (top) {
        TextStyle(fontSize = 22.sp, fontWeight = FontWeight.SemiBold, color = AppColors.TextPrimary, letterSpacing = (-0.2).sp)
    } else {
        TextStyle(fontSize = 16.sp, fontWeight = FontWeight.Medium, color = AppColors.TextSecondary)
    }
    val pctStyle = TextStyle(
        fontSize = if (top) 14.sp else 12.sp,
        fontWeight = FontWeight.Medium,
        fontFamily = FontFamily.Monospace,
        color = if (top) AppColors.TextPrimary else AppColors.TextSecondary,
    )

    Row(verticalAlignment = Alignment.CenterVertically) {
        Text(
            text = prediction.label,
            style = labelStyle,
            modifier = Modifier.width(if (top) 92.dp else 76.dp),
        )
        Box(
            modifier = Modifier
                .weight(1f)
                .height(if (top) 10.dp else 6.dp)
                .clip(RoundedCornerShape(100))
                .background(AppColors.TealSoft),
        ) {
            Box(
                modifier = Modifier
                    .fillMaxWidth(fraction = prediction.confidence.coerceIn(0f, 1f))
                    .height(if (top) 10.dp else 6.dp)
                    .clip(RoundedCornerShape(100))
                    .background(if (top) AppColors.Teal else AppColors.TealContainer),
            )
        }
        Spacer(Modifier.width(14.dp))
        Text(
            text = "${(prediction.confidence * 100f).roundToInt()}%",
            style = pctStyle,
            modifier = Modifier.width(44.dp),
        )
    }
}
