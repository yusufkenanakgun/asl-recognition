package com.cse492.aslrecognition.ui.letters

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.cse492.aslrecognition.App
import com.cse492.aslrecognition.R
import com.cse492.aslrecognition.camera.FrameAnalyzer
import com.cse492.aslrecognition.inference.ClassificationResult
import com.cse492.aslrecognition.inference.ModelType
import com.cse492.aslrecognition.ui.components.CameraSurface
import com.cse492.aslrecognition.ui.components.CameraTabScaffold
import com.cse492.aslrecognition.ui.components.FpsBadge
import com.cse492.aslrecognition.ui.components.LandmarkOverlay
import com.cse492.aslrecognition.ui.components.ModelToggle
import com.cse492.aslrecognition.ui.components.NoHandPlaceholder
import com.cse492.aslrecognition.ui.components.PermissionGate
import com.cse492.aslrecognition.ui.components.Top3Panel
import com.cse492.aslrecognition.ui.theme.AppColors

private val PanelHeight = 170.dp
private val PanelTopRadius = 24.dp
private val OverlayTopPadding = 10.dp

@Composable
fun LettersScreen() {
    CameraTabScaffold(titleRes = R.string.tab_letters) {
        PermissionGate { LettersStage() }
    }
}

@Composable
private fun LettersStage() {
    val container = (LocalContext.current.applicationContext as App).container
    val vm: LettersViewModel = viewModel {
        LettersViewModel(container.handLandmarkerSource, container.inferenceManager)
    }
    val analyzer = remember {
        FrameAnalyzer(container.handLandmarkerSource, container.fpsMeter)
    }
    val handsState by container.handLandmarkerSource.state.collectAsState()
    val fps by container.fpsMeter.fps.collectAsState()
    val result by vm.result.collectAsState()
    val selectedModel by vm.selectedModel.collectAsState()

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(Color.Black),
    ) {
        CameraSurface(
            analyzer = analyzer,
            modifier = Modifier.fillMaxSize(),
        )
        LandmarkOverlay(
            state = handsState,
            modifier = Modifier.fillMaxSize(),
        )

        // Top-left toggle
        ModelToggle(
            options = listOf(
                ModelType.EFFICIENTNET_LETTERS to "EfficientNet",
                ModelType.MLP_LETTERS to "MLP",
            ),
            selected = selectedModel,
            onSelect = { vm.selectModel(it) },
            modifier = Modifier
                .align(Alignment.TopStart)
                .statusBarsPadding()
                .padding(start = 14.dp, top = OverlayTopPadding),
        )

        // Top-right FPS badge (uses inference latency if available, else MediaPipe latency)
        FpsBadge(
            fps = fps,
            latencyMs = result?.inferenceMs ?: handsState.inferenceLatencyMs,
            modifier = Modifier
                .align(Alignment.TopEnd)
                .statusBarsPadding()
                .padding(end = 14.dp, top = OverlayTopPadding),
        )

        // Bottom result panel
        ResultPanel(
            handDetected = handsState.hands.isNotEmpty(),
            result = result,
            modifier = Modifier
                .align(Alignment.BottomCenter)
                .fillMaxWidth()
                .height(PanelHeight),
        )
    }
}

@Composable
private fun ResultPanel(
    handDetected: Boolean,
    result: ClassificationResult?,
    modifier: Modifier = Modifier,
) {
    Box(
        modifier = modifier
            .clip(RoundedCornerShape(topStart = PanelTopRadius, topEnd = PanelTopRadius))
            .background(AppColors.Background)
            .padding(horizontal = 20.dp, vertical = 16.dp),
    ) {
        when {
            !handDetected -> NoHandPlaceholder()
            result == null || result.top3.isEmpty() -> {
                // İlk frame henüz inference üretmedi; el var ama sonuç yok.
                // Boş bırakıyoruz (kısa süreli durum).
            }
            else -> Top3Panel(
                rows = result.top3,
                modifier = Modifier.fillMaxSize(),
            )
        }
    }
}
