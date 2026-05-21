package com.cse492.aslrecognition.util

import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

/**
 * EMA tabanlı FPS sayacı. Son [WINDOW] frame'in zaman damgalarını tutar,
 * pencerenin uçtan uca süresinden FPS hesaplar ve [EMA_ALPHA] ile yumuşatır.
 */
class FpsMeter {
    private val _fps = MutableStateFlow(0f)
    val fps: StateFlow<Float> = _fps.asStateFlow()

    private val timestamps = ArrayDeque<Long>(WINDOW)
    private var ema: Float = 0f

    @Synchronized
    fun tick(nowMs: Long) {
        timestamps.addLast(nowMs)
        while (timestamps.size > WINDOW) timestamps.removeFirst()
        if (timestamps.size < 2) return
        val span = (timestamps.last() - timestamps.first()).coerceAtLeast(1L)
        val instant = (timestamps.size - 1) * 1000f / span
        ema = if (ema == 0f) instant else EMA_ALPHA * instant + (1f - EMA_ALPHA) * ema
        _fps.value = ema
    }

    @Synchronized
    fun reset() {
        timestamps.clear()
        ema = 0f
        _fps.value = 0f
    }

    companion object {
        private const val WINDOW = 60
        private const val EMA_ALPHA = 0.15f
    }
}
