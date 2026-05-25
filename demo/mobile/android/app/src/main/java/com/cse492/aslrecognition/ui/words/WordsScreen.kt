package com.cse492.aslrecognition.ui.words

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
import com.cse492.aslrecognition.ui.components.CountdownOverlay
import com.cse492.aslrecognition.ui.components.FpsBadge
import com.cse492.aslrecognition.ui.components.LandmarkOverlay
import com.cse492.aslrecognition.ui.components.ModelToggle
import com.cse492.aslrecognition.ui.components.PermissionGate
import com.cse492.aslrecognition.ui.components.SequenceProgressOverlay
import com.cse492.aslrecognition.ui.components.Top3Panel
import com.cse492.aslrecognition.ui.theme.AppColors

private val PanelHeight = 170.dp
private val PanelTopRadius = 24.dp
private val OverlayTopPadding = 10.dp

@Composable
fun WordsScreen() {
    CameraTabScaffold(titleRes = R.string.tab_words) {
        PermissionGate { WordsStage() }
    }
}

@Composable
private fun WordsStage() {
    val container = (LocalContext.current.applicationContext as App).container
    val vm: WordsViewModel = viewModel {
        WordsViewModel(container.handLandmarkerSource, container.inferenceManager)
    }
    val analyzer = remember {
        FrameAnalyzer(container.handLandmarkerSource, container.fpsMeter)
    }
    val handsState by container.handLandmarkerSource.state.collectAsState()
    val fps by container.fpsMeter.fps.collectAsState()
    val result by vm.result.collectAsState()
    val selectedModel by vm.selectedModel.collectAsState()
    val fillCount by vm.fillCount.collectAsState()
    val countdownRemaining by vm.countdownRemainingFrames.collectAsState()

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

        ModelToggle(
            options = listOf(
                ModelType.LSTM_SINGLE_WORDS to "Single",
                ModelType.LSTM_ENSEMBLE_WORDS to "Ensemble",
            ),
            selected = selectedModel,
            onSelect = { vm.selectModel(it) },
            modifier = Modifier
                .align(Alignment.TopStart)
                .statusBarsPadding()
                .padding(start = 14.dp, top = OverlayTopPadding),
        )

        FpsBadge(
            fps = fps,
            latencyMs = result?.inferenceMs ?: handsState.inferenceLatencyMs,
            modifier = Modifier
                .align(Alignment.TopEnd)
                .statusBarsPadding()
                .padding(end = 14.dp, top = OverlayTopPadding),
        )

        WordsResultPanel(
            fillCount = fillCount,
            seqLen = vm.seqLen,
            countdownRemaining = countdownRemaining,
            countdownTotal = vm.countdownTotalFrames,
            result = result,
            modifier = Modifier
                .align(Alignment.BottomCenter)
                .fillMaxWidth()
                .height(PanelHeight),
        )
    }
}

@Composable
private fun WordsResultPanel(
    fillCount: Int,
    seqLen: Int,
    countdownRemaining: Int,
    countdownTotal: Int,
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
            countdownRemaining > 0 -> CountdownOverlay(
                remainingFrames = countdownRemaining,
                totalFrames = countdownTotal,
            )
            fillCount < seqLen -> SequenceProgressOverlay(filled = fillCount, total = seqLen)
            result == null || result.top3.isEmpty() -> {
                // Buffer doldu ama ilk inference daha gelmedi (kısa süreli).
            }
            else -> Top3Panel(
                rows = result.top3,
                modifier = Modifier.fillMaxSize(),
            )
        }
    }
}
