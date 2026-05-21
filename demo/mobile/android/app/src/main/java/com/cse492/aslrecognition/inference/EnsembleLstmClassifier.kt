package com.cse492.aslrecognition.inference

import android.content.Context
import android.os.SystemClock
import com.cse492.aslrecognition.labels.WORD_CLASSES
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.async
import kotlinx.coroutines.awaitAll
import kotlinx.coroutines.coroutineScope
import java.io.Closeable

/**
 * 5 seed BiLSTM ensemble — paralel çalıştırır, softmax ortalaması ile combine.
 *
 * Her seed'in kendi [LstmClassifier] + Interpreter'ı var; concurrent çağrıda
 * çakışma yok. `Dispatchers.Default` thread pool'unda async ile yayılır.
 * Toplam latency ~ en yavaş seed (çekirdek sayısına göre 4-5 paralel).
 *
 * Memory: 5 × 5.6 MB = 28 MB (lazy, ilk Words inference'inde yüklenir).
 */
class EnsembleLstmClassifier(context: Context) : Closeable {

    private val seeds: List<LstmClassifier> = (0..4).map { s ->
        LstmClassifier(context, "models/lstm_seed$s.tflite")
    }

    suspend fun classify(
        seq: Array<Array<FloatArray>>,
        timestampMs: Long,
    ): ClassificationResult = coroutineScope {
        val t0 = SystemClock.uptimeMillis()
        val probsList = seeds.map { seed ->
            async(Dispatchers.Default) { seed.classifyToProbs(seq) }
        }.awaitAll()

        val avg = FloatArray(WORD_CLASSES.size)
        for (probs in probsList) {
            for (i in probs.indices) avg[i] += probs[i]
        }
        val inv = 1.0f / probsList.size
        for (i in avg.indices) avg[i] *= inv
        val latency = SystemClock.uptimeMillis() - t0

        ClassificationResult(
            model = ModelType.LSTM_ENSEMBLE_WORDS,
            top3 = topThreeWords(avg),
            inferenceMs = latency,
            timestampMs = timestampMs,
        )
    }

    override fun close() {
        for (seed in seeds) seed.close()
    }
}
