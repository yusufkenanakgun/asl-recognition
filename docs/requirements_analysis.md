# Requirements Analysis

## AI-Powered Sign Language Recognition System: A Comparative Study of Image-Based and Landmark-Based Approaches

**Course:** CSE492 — Engineering Project
**Student:** Yusuf Kenan Akgün (20210702010)
**Date:** April 2026

---

## 1. Introduction

### 1.1 Problem Statement

Sign language is the primary communication method for hearing-impaired individuals, yet the majority of the general population cannot understand it. This creates a significant communication barrier in daily life, education, healthcare, and public services. Current solutions either require a human interpreter — which is costly and not always available — or rely on specialized hardware that limits accessibility.

### 1.2 Project Objective

This project aims to develop an AI-powered real-time sign language recognition system that translates hand gestures into text. The system compares two fundamentally different classification approaches for static letter recognition (image-based vs. landmark-based) and extends into dynamic word-level recognition using temporal sequence modeling.

### 1.3 Scope

The system covers:

- **Static sign recognition:** Classification of ASL alphabet letters (A–Z) and control signs (delete, nothing, space) from single images.
- **Dynamic sign recognition:** Classification of ASL words from video sequences using temporal modeling.
- **Real-time mobile demo application:** An Android application (per proposal) that captures the device camera feed, performs on-device inference via TensorFlow Lite, and displays recognized letters/words on screen.
- **Comparative analysis:** A structured evaluation of multiple model architectures across accuracy, speed, and resource consumption metrics.

### 1.4 Stakeholders

| Stakeholder | Role |
|---|---|
| Hearing-impaired individuals | Primary end users who communicate via sign language |
| General public / non-signers | Users who need to understand sign language output |
| Researchers / developers | May extend or adapt the system for other sign languages |
| Project advisor | Evaluates academic rigor and methodology |

---

## 2. Functional Requirements

### FR-01: Static Letter Recognition (Image-Based)

| Field | Description |
|---|---|
| **ID** | FR-01 |
| **Priority** | High |
| **Description** | The system shall classify a single RGB image of a hand gesture into one of 29 ASL classes (A–Z, delete, nothing, space) using a CNN-based transfer learning approach (EfficientNet-B0). |
| **Input** | A 224×224 RGB image |
| **Output** | Predicted class label with confidence score |
| **Acceptance Criteria** | Top-1 accuracy ≥ 95% on the test set |

### FR-02: Static Letter Recognition (Landmark-Based)

| Field | Description |
|---|---|
| **ID** | FR-02 |
| **Priority** | High |
| **Description** | The system shall extract 21 hand landmarks (63-dimensional feature vector) from an input image using MediaPipe Hands, then classify the gesture using an MLP model. |
| **Input** | A 200×200 RGB image |
| **Output** | Predicted class label with confidence score, or a "hand not detected" signal |
| **Acceptance Criteria** | Top-1 accuracy ≥ 90% on successfully detected hands |

### FR-03: Dynamic Word Recognition

| Field | Description |
|---|---|
| **ID** | FR-03 |
| **Priority** | Medium |
| **Description** | The system shall classify video sequences of ASL word-level signs into their corresponding word labels using an LSTM/GRU network over landmark sequences. |
| **Input** | A video clip (variable length) containing a single word-level sign |
| **Output** | Predicted word label with confidence score |
| **Acceptance Criteria** | Top-1 accuracy ≥ 40% on WLASL-100 test set (baseline); target ≥ 60% with sufficient data |

### FR-04: Real-Time Mobile Demo

| Field | Description |
|---|---|
| **ID** | FR-04 |
| **Priority** | High |
| **Description** | The system shall provide a real-time mobile demo application (Android per proposal) that captures the device camera feed, runs on-device inference via TensorFlow Lite on each frame, and displays the recognized letter or word as on-screen text. |
| **Input** | Live mobile camera video stream |
| **Output** | Visual overlay showing predicted sign and confidence |
| **Acceptance Criteria** | Inference latency ≤ 100 ms per frame (≥ 10 FPS) on the target mobile device with visible output |

### FR-05: Model Comparison and Reporting

| Field | Description |
|---|---|
| **ID** | FR-05 |
| **Priority** | High |
| **Description** | The system shall produce a structured comparative analysis of all trained models, evaluated on a common test set using standardized metrics. |
| **Output** | Comparison tables and visualizations (confusion matrices, accuracy/loss curves, bar charts) |
| **Metrics** | Top-1 accuracy, Top-5 accuracy, per-class F1 score, confusion matrix, model size (MB), inference speed (FPS), training time |

### FR-06: Data Preprocessing Pipeline

| Field | Description |
|---|---|
| **ID** | FR-06 |
| **Priority** | High |
| **Description** | The system shall implement a reproducible data preprocessing pipeline that handles image loading, augmentation, normalization, landmark extraction, and train/validation/test splitting. |
| **Sub-requirements** | |
| FR-06a | Apply data augmentation to training data (rotation, flip, color jitter) |
| FR-06b | Normalize images using ImageNet statistics for CNN input |
| FR-06c | Extract and normalize hand landmarks for MLP input |
| FR-06d | Split data into train (70%), validation (15%), and test (15%) sets |
| FR-06e | Handle video-to-frame extraction and sequence padding for LSTM input |

---

## 3. Non-Functional Requirements

### 3.1 Performance

| ID | Requirement | Target |
|---|---|---|
| NFR-01 | Letter recognition accuracy (image-based) | ≥ 95% Top-1 |
| NFR-02 | Letter recognition accuracy (landmark-based) | ≥ 90% Top-1 |
| NFR-03 | Word recognition accuracy | ≥ 40% Top-1 (baseline) |
| NFR-04 | Real-time inference speed | ≥ 10 FPS on consumer GPU |
| NFR-05 | Inference latency per image (CNN) | ≤ 10 ms |
| NFR-06 | Inference latency per sample (MLP) | ≤ 1 ms |

### 3.2 Scalability

| ID | Requirement |
|---|---|
| NFR-07 | The landmark-based model shall be lightweight enough (< 1 MB) for potential deployment on mobile/edge devices. |
| NFR-08 | The system architecture shall allow adding new sign classes without rewriting the pipeline — only retraining is needed. |

### 3.3 Usability

| ID | Requirement |
|---|---|
| NFR-09 | The mobile demo application shall provide clear visual feedback (predicted sign and confidence) without requiring technical knowledge from the user. |
| NFR-10 | The system shall handle cases where no hand is detected gracefully, displaying an appropriate message instead of crashing. |

### 3.4 Reliability

| ID | Requirement |
|---|---|
| NFR-11 | The system shall report hand detection failure rate as a metric and handle detection failures without system interruption. |
| NFR-12 | Model training shall implement early stopping to prevent overfitting and ensure reproducible results. |

### 3.5 Portability

| ID | Requirement |
|---|---|
| NFR-13 | All code shall run on Python 3.x with documented dependencies in `requirements.txt`. |
| NFR-14 | Training shall support both local GPU (NVIDIA CUDA) and cloud GPU (Google Colab) environments. |

---

## 4. System Requirements

### 4.1 Hardware Requirements

| Component | Minimum | Recommended |
|---|---|---|
| GPU | NVIDIA GPU with CUDA support (4 GB VRAM) | NVIDIA RTX 3050 or higher |
| RAM | 8 GB | 16 GB |
| Storage | 20 GB free (datasets + models) | 50 GB free |
| Mobile device | Android phone (API 24+) with rear camera | Mid-range or higher Android device for FPS measurement |

### 4.2 Software Requirements

| Component | Version / Details |
|---|---|
| Operating System | Windows 10/11 or Linux (Ubuntu 20.04+) |
| Python | 3.10+ |
| PyTorch | 2.x with CUDA support |
| torchvision | 0.21+ (pretrained EfficientNet-B0) |
| MediaPipe | 0.10+ (Hand Landmarker Tasks API) |
| OpenCV | 4.x (image/video processing on the training/preprocessing side) |
| TensorFlow Lite | Mobile inference runtime (Android) |
| MediaPipe Tasks (Android) | On-device hand landmark extraction for mobile demo |
| scikit-learn | Metrics computation, data splitting |
| NumPy | Array operations |
| matplotlib / seaborn | Visualization and plotting |
| yt-dlp | Video downloading (for WLASL dataset) |

---

## 5. Dataset Requirements

### 5.1 Static Letter Recognition — ASL Alphabet

| Property | Value |
|---|---|
| Source | ASL Alphabet dataset (Kaggle) |
| Total images | ~87,000 |
| Classes | 29 (A–Z + delete, nothing, space) |
| Images per class | ~3,000 (balanced) |
| Image size | 200×200 pixels |
| Split strategy | Random stratified: 70/15/15 |

### 5.2 Dynamic Word Recognition — WLASL

| Property | Value |
|---|---|
| Source | WLASL-Processed (Kaggle) |
| Total videos | ~12,000 |
| Subset used | WLASL-100 (100 word classes) |
| Format | MP4 video clips |
| Split strategy | Predefined train/val/test from JSON metadata |
| Known limitation | Some YouTube source videos may be unavailable; Kaggle-hosted version mitigates this |

---

## 6. Model Architecture Requirements

### 6.1 Model 1 — EfficientNet-B0 (Image-Based)

| Property | Specification |
|---|---|
| Base architecture | EfficientNet-B0 (pretrained on ImageNet) |
| Training strategy | Two-phase: (1) feature extraction (frozen backbone), (2) full fine-tuning |
| Input | 224×224×3 RGB image |
| Output | 29-class softmax probability distribution |
| Optimizer | Adam |
| Regularization | Early stopping, learning rate scheduling |

### 6.2 Model 2 — MLP (Landmark-Based)

| Property | Specification |
|---|---|
| Preprocessing | MediaPipe Hands → 21 landmarks × 3 coordinates = 63-dim vector |
| Architecture | Input(63) → Hidden layers with ReLU → Output(num_classes) |
| Regularization | Dropout, batch normalization |
| Input | 63-dimensional normalized landmark vector |
| Output | Class softmax probability distribution |

### 6.3 Model 3 — LSTM (Temporal Sequence)

| Property | Specification |
|---|---|
| Preprocessing | Video → frames → per-frame landmarks → sequence of 63-dim vectors |
| Architecture | LSTM/GRU layers → fully connected → output |
| Sequence handling | Padding/truncation to fixed length |
| Input | Sequence of 63-dim landmark vectors (T × 63) |
| Output | Word-class softmax probability distribution |

---

## 7. Evaluation Criteria

All models shall be evaluated using the following metrics on held-out test sets:

| Metric | Description | Purpose |
|---|---|---|
| Top-1 Accuracy | Percentage of correctly classified samples | Primary performance measure |
| Top-5 Accuracy | Target class within top 5 predictions | Useful for word recognition with many classes |
| Per-class F1 Score | Precision-recall balance per class | Identifies weak classes |
| Confusion Matrix | Class-by-class error distribution | Reveals systematic misclassifications (e.g., M↔N) |
| Model Size (MB) | Serialized model file size | Deployability on resource-constrained devices |
| Inference Speed (FPS) | Frames processed per second on GPU | Real-time feasibility |
| Training Time | Wall-clock time for full training | Reproducibility and resource planning |
| Detection Rate | Percentage of images where hand is successfully detected (landmark-based only) | Measures preprocessing reliability |

---

## 8. Constraints and Assumptions

### 8.1 Constraints

| ID | Constraint |
|---|---|
| C-01 | The project is limited to American Sign Language (ASL). Other sign languages are out of scope. |
| C-02 | Static recognition handles single-hand gestures only; two-hand signs are not supported. |
| C-03 | Word-level recognition depends on the availability of the WLASL video dataset, which has known data loss from deleted YouTube videos. |
| C-04 | GPU resources are limited to a single NVIDIA RTX 3050 (4 GB VRAM), constraining batch sizes and model complexity. |
| C-05 | The project timeline is bounded by the CSE492 course schedule (~16–20 weeks). |

### 8.2 Assumptions

| ID | Assumption |
|---|---|
| A-01 | Input images contain a clearly visible hand against a relatively uncluttered background. |
| A-02 | The mobile demo operates in reasonable indoor lighting conditions. |
| A-03 | The ASL Alphabet dataset from Kaggle is correctly labeled and class-balanced. |
| A-04 | MediaPipe Hands provides sufficiently accurate landmark estimates for classification purposes. |
| A-05 | Person-wise data splitting is not possible with the ASL Alphabet dataset; random splitting is used, and this limitation is acknowledged. |

---

## 9. Risk Analysis

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Low word-recognition accuracy due to limited training data | High | Medium | Use Kaggle-hosted WLASL with ~12K videos; reduce class count if needed; report as future work |
| MediaPipe fails to detect hands in certain frames | Medium | Medium | Log and report detection failure rate; fall back to image-based model in demo |
| GPU memory insufficient for large batch training | Medium | Low | Reduce batch size; use gradient accumulation; leverage mixed precision training |
| Dataset bias (single background, lighting) reduces real-world generalization | High | Medium | Apply data augmentation; test live on the mobile demo with unseen hands; discuss in limitations |
| Dependency version conflicts between PyTorch and MediaPipe | Low | Low | Pin all versions in `requirements.txt`; use virtual environment |

---

## 10. Deliverables

| # | Deliverable | Format |
|---|---|---|
| 1 | Trained EfficientNet-B0 model for letter recognition | `.pth` file |
| 2 | Trained MLP model for landmark-based letter recognition | `.pth` file |
| 3 | Trained LSTM model for word-level recognition | `.pth` file |
| 4 | Comparative analysis report with metrics, tables, and visualizations | Embedded in thesis |
| 5 | Real-time mobile demo application (Android, TFLite) | Android APK / project sources |
| 6 | Source code repository with documented pipeline | GitHub repository |
| 7 | Final thesis document | PDF (LaTeX) |
| 8 | Presentation slides with live demo | PowerPoint / PDF |

---

## 11. Impact Areas

| Area | Relevance |
|---|---|
| **Health** | Enables communication between hearing-impaired patients and healthcare providers |
| **Social / Ethical** | Promotes accessibility and inclusion for the deaf and hard-of-hearing community |

---

*Document version: 1.0 — April 2026*
