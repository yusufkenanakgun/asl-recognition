package com.cse492.aslrecognition.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable

private val LightScheme = lightColorScheme(
    primary = AppColors.Teal,
    onPrimary = AppColors.OnTeal,
    primaryContainer = AppColors.TealContainer,
    onPrimaryContainer = AppColors.TealDark,
    secondary = AppColors.Teal,
    onSecondary = AppColors.OnTeal,
    secondaryContainer = AppColors.TealSoft,
    onSecondaryContainer = AppColors.TealDark,
    tertiary = AppColors.Teal,
    background = AppColors.Background,
    onBackground = AppColors.TextPrimary,
    surface = AppColors.Background,
    onSurface = AppColors.TextPrimary,
    surfaceVariant = AppColors.Surface,
    onSurfaceVariant = AppColors.TextSecondary,
    outline = AppColors.CardBorder,
    outlineVariant = AppColors.Divider,
)

@Composable
fun ASLDemoTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = LightScheme,
        typography = AppTypography,
        content = content,
    )
}
