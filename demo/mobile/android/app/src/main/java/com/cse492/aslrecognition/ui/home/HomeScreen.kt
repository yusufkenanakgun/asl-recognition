package com.cse492.aslrecognition.ui.home

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowForward
import androidx.compose.material.icons.outlined.BackHand
import androidx.compose.material.icons.outlined.ChatBubbleOutline
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import com.cse492.aslrecognition.R
import com.cse492.aslrecognition.ui.theme.AppColors
import com.cse492.aslrecognition.ui.theme.Dimens

@Composable
fun HomeScreen(
    onOpenLetters: () -> Unit = {},
    onOpenWords: () -> Unit = {},
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(AppColors.Background)
            .statusBarsPadding()
            .verticalScroll(rememberScrollState()),
    ) {
        HomeAppBar()

        Column(
            modifier = Modifier
                .padding(horizontal = Dimens.ScreenPadding)
                .padding(top = 4.dp, bottom = 24.dp),
        ) {
            // Header
            Column(modifier = Modifier.padding(vertical = 12.dp)) {
                Text(
                    text = stringResource(R.string.home_headline),
                    style = MaterialTheme.typography.headlineMedium,
                    color = AppColors.TextPrimary,
                )
                Spacer(Modifier.height(12.dp))
                Text(
                    text = stringResource(R.string.home_subtitle),
                    style = MaterialTheme.typography.bodyLarge,
                    color = AppColors.TextSecondary,
                )
            }

            Spacer(Modifier.height(12.dp))

            // Action cards
            ActionCard(
                primary = true,
                title = stringResource(R.string.home_action_letters_title),
                caption = stringResource(R.string.home_action_letters_caption),
                onClick = onOpenLetters,
                icon = { tint ->
                    Icon(Icons.Outlined.BackHand, contentDescription = null, tint = tint, modifier = Modifier.size(28.dp))
                },
            )
            Spacer(Modifier.height(12.dp))
            ActionCard(
                primary = false,
                title = stringResource(R.string.home_action_words_title),
                caption = stringResource(R.string.home_action_words_caption),
                onClick = onOpenWords,
                icon = { tint ->
                    Icon(Icons.Outlined.ChatBubbleOutline, contentDescription = null, tint = tint, modifier = Modifier.size(28.dp))
                },
            )

            Spacer(Modifier.height(24.dp))

            AboutCard()

            Spacer(Modifier.height(18.dp))

            ModelsTable()

            Spacer(Modifier.height(16.dp))

            Text(
                text = stringResource(R.string.home_datasets_footer),
                style = MaterialTheme.typography.bodySmall,
                color = AppColors.TextTertiary,
                modifier = Modifier.fillMaxWidth(),
            )
        }
    }
}

@Composable
private fun HomeAppBar() {
    Surface(color = AppColors.Background, shadowElevation = 0.dp, tonalElevation = 0.dp) {
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .height(56.dp)
                .padding(horizontal = 16.dp),
            contentAlignment = Alignment.CenterStart,
        ) {
            Text(
                text = stringResource(R.string.home_title),
                style = MaterialTheme.typography.titleLarge,
                color = AppColors.TextPrimary,
            )
        }
    }
}

@Composable
private fun ActionCard(
    primary: Boolean,
    title: String,
    caption: String,
    onClick: () -> Unit,
    icon: @Composable (tint: Color) -> Unit,
) {
    val bg = if (primary) AppColors.Teal else AppColors.Background
    val fg = if (primary) AppColors.OnTeal else AppColors.TextPrimary
    val captionColor = if (primary) AppColors.OnTeal.copy(alpha = 0.85f) else AppColors.TextSecondary
    val iconBoxBg = if (primary) Color.White.copy(alpha = 0.18f) else AppColors.TealSoft
    val iconTint = if (primary) AppColors.OnTeal else AppColors.Teal
    val arrowTint = if (primary) AppColors.OnTeal.copy(alpha = 0.9f) else AppColors.TextTertiary

    val modifier = Modifier
        .fillMaxWidth()
        .clip(RoundedCornerShape(Dimens.CardRadius))
        .background(bg)
        .then(
            if (!primary)
                Modifier.border(
                    width = 1.dp,
                    color = AppColors.CardBorder,
                    shape = RoundedCornerShape(Dimens.CardRadius),
                )
            else Modifier,
        )
        .clickable(onClick = onClick)
        .padding(horizontal = 20.dp, vertical = 20.dp)

    Row(modifier = modifier, verticalAlignment = Alignment.CenterVertically) {
        Box(
            modifier = Modifier
                .size(Dimens.IconBoxSize)
                .clip(RoundedCornerShape(Dimens.IconBoxRadius))
                .background(iconBoxBg),
            contentAlignment = Alignment.Center,
        ) {
            icon(iconTint)
        }
        Spacer(Modifier.width(18.dp))
        Column(modifier = Modifier.weight(1f)) {
            Text(
                text = title,
                style = MaterialTheme.typography.titleMedium,
                color = fg,
            )
            Spacer(Modifier.height(4.dp))
            Text(
                text = caption,
                style = MaterialTheme.typography.bodyMedium,
                color = captionColor,
            )
        }
        Spacer(Modifier.width(8.dp))
        Icon(
            imageVector = Icons.AutoMirrored.Filled.ArrowForward,
            contentDescription = null,
            tint = arrowTint,
            modifier = Modifier.size(20.dp),
        )
    }
}

private data class ModelRow(val name: String, val kind: String, val size: String)

private val ModelRows = listOf(
    ModelRow("EfficientNet-B0", "image · letters", "15.4 MB"),
    ModelRow("MLP Landmark", "landmark · letters", "0.23 MB"),
    ModelRow("BiLSTM Single", "landmark · words", "5.6 MB"),
    ModelRow("BiLSTM Ensemble (x5)", "landmark · words", "27.8 MB"),
)

@Composable
private fun ModelsTable() {
    Text(
        text = stringResource(R.string.home_models_title).uppercase(),
        style = MaterialTheme.typography.labelSmall,
        color = AppColors.TextTertiary,
        modifier = Modifier.padding(start = 4.dp, bottom = 8.dp),
    )
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(Dimens.CardRadius))
            .border(1.dp, AppColors.CardBorder, RoundedCornerShape(Dimens.CardRadius))
            .background(AppColors.Background),
    ) {
        ModelRows.forEachIndexed { idx, row ->
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 16.dp, vertical = 12.dp),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Column(modifier = Modifier.weight(1f)) {
                    Text(
                        text = row.name,
                        style = MaterialTheme.typography.bodyMedium,
                        color = AppColors.TextPrimary,
                    )
                    Spacer(Modifier.height(2.dp))
                    Text(
                        text = row.kind,
                        style = MaterialTheme.typography.bodySmall,
                        color = AppColors.TextSecondary,
                    )
                }
                Text(
                    text = row.size,
                    style = MaterialTheme.typography.bodyMedium,
                    color = AppColors.TextSecondary,
                )
            }
            if (idx < ModelRows.size - 1) {
                Spacer(
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(1.dp)
                        .background(AppColors.Divider),
                )
            }
        }
    }
}
