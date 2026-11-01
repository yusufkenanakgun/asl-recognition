# On-Device American Sign Language Recognition

### Image- vs Landmark-Based Approaches

B.Sc. thesis, Yeditepe University Computer Engineering, 2026.

The study is framed as a **deployability comparison rather than an accuracy race**. Every architectural decision is measured on two axes at once: how accurately it classifies, and what it costs in size and latency on the phone that has to run it. The conclusion the work argues for is that *competitive on a server* and *usable on a phone* are not the same property.

Two tasks, two model families, all four models converted through ONNX to TensorFlow Lite and measured on real hardware through a Kotlin Android app that is also in this repository.

---

## Letter task — 29-class fingerspelling

An image network against a landmark network over MediaPipe hand joints, trained on the same split.

| | EfficientNet-B0 | Landmark MLP |
|---|---|---|
| Checkpoint | 46.75 MB | **0.24 MB** |
| Held-out accuracy | **100.00%** (13,050 images) | 99.38% (9,610 samples) |
| Independent external set | **59.77%** (520 / 870) | **90.72%** (714 / 787 detected) |

### The 100% was the finding, not the result

A perfect score on 13,050 held-out images is not a success, it is a signal that the test split is not independent of the training data. Both models were therefore retested — without retraining — on an external set of 870 photographs with different capturers, backgrounds and lighting.

EfficientNet-B0 fell from 100% to **59.77%**. The landmark model went from 99.38% to **90.72%**. The collapse is concentrated and legible: the image network scored 0/30 on **S** and 2/30 on **T** — two fists that differ only in thumb placement, which the network had apparently been separating on capture conditions rather than on hand shape.

The explanation is that the landmark front end throws away exactly the information that was being memorised. Feeding the network 21 normalised joint coordinates instead of raw pixels removes lighting, background and skin tone before the classifier ever sees the frame.

### The counter-evidence

Reported because it argues against the conclusion above. MediaPipe detected a hand in only **93.69%** of the external images. The 90.72% figure is accuracy *on frames where detection succeeded*; counting the 53 detection failures as errors puts the landmark path at **85.00%** across all hand classes. A missed detection is a real failure for a user, so when the two models are framed as drop-in alternatives, part of the landmark model's advantage is paid back here.

The `nothing` class is the one unambiguous result: 30/30 correct, zero false positives.

---

## Word task — WLASL-100

A bidirectional LSTM over MediaPipe joint sequences from short video, 100 classes, 201 test clips.

| | Top-1 | Top-5 | Macro F1 |
|---|:-:|:-:|:-:|
| Five seeds, mean | 52.14% (sd 2.97) | — | — |
| Best single seed | 56.22% | 79.10% | 0.524 |
| **Logit-averaged ensemble** | **56.22%** | **81.09%** | 0.521 |

### Was the ensemble gain real?

A 201-clip test set is small enough that a few points can be noise, so the gain was tested with a **10,000-sample paired bootstrap** (`src/faz6/stat_analysis.py`, seed 42):

| Comparison | Difference | 95% CI | p |
|---|:-:|:-:|:-:|
| Ensemble vs. per-clip seed mean | **+4.09 pp** | [+0.80, +7.46] | **0.015** |
| Ensemble vs. best single seed | +0.02 pp | [−4.48, +4.98] | ≈1.0 |

The honest reading is both rows together. Ensembling reliably beats *picking a seed at random*, which is the decision you actually face. It does **not** beat *the best seed chosen in hindsight* — that difference is indistinguishable from zero. Reporting only the first row would have overstated the result.

Errors are structural rather than random: the most-confused pairs share hand shape, body position or motion trajectory, which says the model learned the coarse structure of a sign and stopped before the fine detail that separates near neighbours.

---

## Deployment

All models were exported PyTorch → ONNX → TensorFlow Lite, with numerical equivalence verified rather than assumed. For the six LSTM conversions (`models/tflite/tflite_report.json`):

- ONNX 5.52 MB → TFLite 5.56 MB
- Maximum absolute output difference **1.2 – 1.9 × 10⁻⁶**
- Top-1 prediction identical to the PyTorch model on every check

The Android app in `demo/mobile/android/` runs the exported models live: CameraX frame analysis, MediaPipe `HandLandmarker`, a sequence buffer for the word models, a runtime toggle between the four classifiers, and an on-screen FPS meter so throughput is visible while signing rather than only in a benchmark.

---

## Repository layout

```
thesis/            LaTeX source - 6 chapters, figures, bibliography
src/               training, evaluation, landmark extraction, ONNX/TFLite conversion,
                   statistical analysis, figure generation
  faz6/            word-task pipeline: class selection, extraction, training, stats
models/            trained checkpoints (.pth), converted .tflite, evaluation JSON
  faz6_v2/         per-seed training histories + ablation runs
demo/mobile/       Kotlin / Jetpack Compose Android app
docs/              requirements analysis, proposal, progress notes, manual test results
sunum/             defence presentation
alphabet-goruntu/  reference figures for the ASL alphabet and word set
```

Every number quoted above is reproducible from the JSON files under `models/` — they are committed, not summarised.

## Running

```bash
pip install -r requirements.txt
```

Training and evaluation entry points live in `src/` (`train.py`, `train_mlp.py`, `train_lstm.py`, `evaluate.py`, `evaluate_external.py`, `src/faz6/train_v2.py`). Datasets are not committed; `src/download_wlasl.py` fetches the word-level corpus, and the letter task uses the public ASL Alphabet dataset.

The Android app opens as a standard Gradle project in `demo/mobile/android/` and loads the `.tflite` files from `models/tflite/`.
