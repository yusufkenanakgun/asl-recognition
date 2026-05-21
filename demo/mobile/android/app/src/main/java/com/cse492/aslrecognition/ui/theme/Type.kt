package com.cse492.aslrecognition.ui.theme

import androidx.compose.material3.Typography
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.sp

private val Default = TextStyle(fontWeight = FontWeight.Normal)

val AppTypography = Typography(
    // Mockup başlık: 26sp / 500
    headlineMedium = Default.copy(
        fontSize = 26.sp, fontWeight = FontWeight.Medium, lineHeight = 32.sp, letterSpacing = (-0.3).sp,
    ),
    titleLarge = Default.copy(
        fontSize = 20.sp, fontWeight = FontWeight.Medium, lineHeight = 26.sp,
    ),
    // Action card başlığı: 17sp / 500
    titleMedium = Default.copy(
        fontSize = 17.sp, fontWeight = FontWeight.Medium, lineHeight = 22.sp,
    ),
    // About kart başlığı: 14sp / 500
    titleSmall = Default.copy(
        fontSize = 14.sp, fontWeight = FontWeight.Medium, lineHeight = 20.sp,
    ),
    // Gövde / 14sp
    bodyLarge = Default.copy(
        fontSize = 14.sp, lineHeight = 22.sp,
    ),
    // 13sp caption
    bodyMedium = Default.copy(
        fontSize = 13.sp, lineHeight = 18.sp,
    ),
    // 12sp ufak
    bodySmall = Default.copy(
        fontSize = 12.sp, lineHeight = 16.sp,
    ),
    // Bottom nav label (12sp)
    labelMedium = Default.copy(
        fontSize = 12.sp, fontWeight = FontWeight.Normal, letterSpacing = 0.3.sp,
    ),
    // ALL-CAPS label (11sp, 0.4sp)
    labelSmall = Default.copy(
        fontSize = 11.sp, fontWeight = FontWeight.Medium, letterSpacing = 0.4.sp,
    ),
)
