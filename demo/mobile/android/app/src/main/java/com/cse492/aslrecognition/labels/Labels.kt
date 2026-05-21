package com.cse492.aslrecognition.labels

/**
 * MLP / EfficientNet için ASL Alphabet sınıf isimleri (idx → label).
 * Sıra `src/train_mlp.py:16-18` ile birebir aynı; değiştirilemez.
 */
val LETTER_CLASSES: List<String> = listOf(
    "A", "B", "C", "D", "E", "F", "G", "H", "I", "J",
    "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T",
    "U", "V", "W", "X", "Y", "Z",
    "del", "nothing", "space",
)
