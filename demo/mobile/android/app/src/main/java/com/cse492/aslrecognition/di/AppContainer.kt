package com.cse492.aslrecognition.di

import android.content.Context
import com.cse492.aslrecognition.inference.InferenceManager
import com.cse492.aslrecognition.mediapipe.HandLandmarkerSource
import com.cse492.aslrecognition.util.FpsMeter

class AppContainer(private val appContext: Context) {

    val handLandmarkerSource: HandLandmarkerSource by lazy {
        HandLandmarkerSource(appContext)
    }

    val fpsMeter: FpsMeter by lazy { FpsMeter() }

    val inferenceManager: InferenceManager by lazy {
        InferenceManager(appContext)
    }
}
