package com.cse492.aslrecognition

import android.graphics.Color
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.core.view.WindowCompat
import com.cse492.aslrecognition.ui.navigation.AppNav
import com.cse492.aslrecognition.ui.theme.ASLDemoTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        // Edge-to-edge: kamera ekranlarında preview status bar arkasına da uzansın.
        WindowCompat.setDecorFitsSystemWindows(window, false)
        window.statusBarColor = Color.TRANSPARENT
        setContent {
            ASLDemoTheme {
                AppNav()
            }
        }
    }
}
