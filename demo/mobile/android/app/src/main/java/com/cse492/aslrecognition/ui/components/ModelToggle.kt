package com.cse492.aslrecognition.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.cse492.aslrecognition.ui.theme.AppColors

/**
 * Camera overlay üzerinde teal-bordered pill segmented control.
 * 2 seçenek; seçili olan dolu teal, diğeri yarı saydam.
 */
@Composable
fun <T> ModelToggle(
    options: List<Pair<T, String>>,
    selected: T,
    onSelect: (T) -> Unit,
    modifier: Modifier = Modifier,
) {
    Row(
        modifier = modifier
            .clip(RoundedCornerShape(100))
            .background(AppColors.TextPrimary.copy(alpha = 0.55f))
            .border(1.dp, AppColors.Teal, RoundedCornerShape(100))
            .padding(3.dp),
    ) {
        options.forEach { (value, label) ->
            val isSelected = value == selected
            val bg = if (isSelected) AppColors.Teal else androidx.compose.ui.graphics.Color.Transparent
            val fg = if (isSelected) AppColors.OnTeal else AppColors.OnTeal.copy(alpha = 0.75f)
            Text(
                text = label,
                style = TextStyle(
                    fontSize = 11.5.sp,
                    fontWeight = FontWeight.Medium,
                    letterSpacing = 0.2.sp,
                    color = fg,
                ),
                modifier = Modifier
                    .clip(RoundedCornerShape(100))
                    .background(bg)
                    .clickable { onSelect(value) }
                    .padding(horizontal = 12.dp, vertical = 5.dp),
            )
        }
    }
}
