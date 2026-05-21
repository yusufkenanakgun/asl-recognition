package com.cse492.aslrecognition.preprocessing

/**
 * LSTM girdisi için (seqLen × featDim) sliding window ring buffer.
 *
 * Dolana kadar [fillCount] artar; doldıktan sonra en eski frame düşer.
 * [snapshot] kronolojik (eski → yeni) sırada (1, seqLen, featDim) ile uyumlu
 * iç içe Array döner.
 *
 * Thread safety: tek thread (FrameAnalyzer + ViewModel collect) tarafından
 * kullanılmak üzere tasarlandı; ekstra senkronizasyon yok.
 */
class SequenceBuffer(
    val seqLen: Int = 32,
    val featDim: Int = WORD_FEATURE_DIM,
) {
    private val data: Array<FloatArray> = Array(seqLen) { FloatArray(featDim) }
    private var head: Int = 0          // bir sonraki yazılacak index
    var fillCount: Int = 0
        private set

    val isFull: Boolean get() = fillCount >= seqLen

    fun push(feat: FloatArray) {
        require(feat.size == featDim) { "feat size ${feat.size} != $featDim" }
        feat.copyInto(data[head])
        head = (head + 1) % seqLen
        if (fillCount < seqLen) fillCount++
    }

    /**
     * Mevcut buffer'ı kronolojik sırada (1, seqLen, featDim) şekline kopyala.
     * Doluyken: oldest = data[head], newest = data[head-1].
     * Dolmadıysa: ilk fillCount slot kullanılır, kalan padding sıfır.
     */
    fun snapshot(): Array<Array<FloatArray>> {
        val out = Array(1) { Array(seqLen) { FloatArray(featDim) } }
        if (isFull) {
            // head: oldest, sıralı kopyala
            for (i in 0 until seqLen) {
                data[(head + i) % seqLen].copyInto(out[0][i])
            }
        } else {
            // İlk fillCount frame ilk slotlara; geri kalan zaten 0.
            for (i in 0 until fillCount) {
                data[i].copyInto(out[0][i])
            }
        }
        return out
    }

    fun reset() {
        head = 0
        fillCount = 0
        for (row in data) row.fill(0f)
    }
}
