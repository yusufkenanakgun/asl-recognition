package com.cse492.aslrecognition.util

import android.content.Context
import java.io.FileInputStream
import java.nio.ByteBuffer
import java.nio.MappedByteBuffer
import java.nio.channels.FileChannel

/**
 * Asset'teki .tflite dosyasını memory-map ile yükle. Interpreter
 * `MappedByteBuffer` üzerinden okurken kopya yapmaz.
 */
fun Context.loadModelFile(assetPath: String): MappedByteBuffer {
    assets.openFd(assetPath).use { afd ->
        FileInputStream(afd.fileDescriptor).channel.use { ch ->
            return ch.map(FileChannel.MapMode.READ_ONLY, afd.startOffset, afd.declaredLength)
        }
    }
}

/** ByteBuffer için native-order yeni allocate (TFLite NHWC tensor için). */
fun newDirectByteBuffer(bytes: Int): ByteBuffer =
    ByteBuffer.allocateDirect(bytes).apply { order(java.nio.ByteOrder.nativeOrder()) }
