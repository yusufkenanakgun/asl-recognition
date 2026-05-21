"""
FAZ 6: Kaggle WLASL Dataset - Landmark Extraction
Hazır videolardan landmark çıkarma
"""

import cv2
import numpy as np
from pathlib import Path
from tqdm import tqdm
import json
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision


def download_model():
    """Hand Landmarker modelini indir"""
    import urllib.request
    model_path = Path("models/hand_landmarker.task")

    if not model_path.exists():
        print("Hand Landmarker modeli indiriliyor...")
        url = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
        model_path.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(url, model_path)

    return str(model_path)


def create_hand_landmarker(model_path):
    """Hand Landmarker oluştur"""
    base_options = python.BaseOptions(model_asset_path=model_path)
    options = vision.HandLandmarkerOptions(
        base_options=base_options,
        num_hands=2,
        min_hand_detection_confidence=0.5,
        min_hand_presence_confidence=0.5,
        min_tracking_confidence=0.5
    )
    return vision.HandLandmarker.create_from_options(options)


def normalize_landmarks(landmarks):
    """Landmark'ları normalize et"""
    coords = np.array([[lm.x, lm.y, lm.z] for lm in landmarks])
    wrist = coords[0]
    coords = coords - wrist
    scale = np.linalg.norm(coords[9])
    if scale > 0:
        coords = coords / scale
    return coords.flatten()


def extract_frames(video_path, max_frames=30, target_fps=10):
    """Videodan frame çıkar"""
    cap = cv2.VideoCapture(str(video_path))

    if not cap.isOpened():
        return None

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    if fps <= 0 or total_frames <= 0:
        cap.release()
        return None

    frame_interval = max(1, int(fps / target_fps))
    frames = []

    frame_idx = 0
    while len(frames) < max_frames:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_idx % frame_interval == 0:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frames.append(frame_rgb)

        frame_idx += 1

    cap.release()
    return frames


def extract_landmarks_from_video(video_path, landmarker, max_frames=30):
    """Videodan landmark sequence çıkar"""
    frames = extract_frames(video_path, max_frames)

    if frames is None or len(frames) == 0:
        return None

    landmarks_sequence = []

    for frame in frames:
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
        result = landmarker.detect(mp_image)

        if result.hand_landmarks and len(result.hand_landmarks) > 0:
            hand_landmarks = result.hand_landmarks[0]
            normalized = normalize_landmarks(hand_landmarks)
            landmarks_sequence.append(normalized)
        else:
            landmarks_sequence.append(np.zeros(63))

    if len(landmarks_sequence) == 0:
        return None

    return np.array(landmarks_sequence, dtype=np.float32)


def pad_sequence(sequence, max_len=30):
    """Sequence'ı sabit uzunluğa getir"""
    if len(sequence) > max_len:
        return sequence[:max_len]
    elif len(sequence) < max_len:
        padding = np.zeros((max_len - len(sequence), 63), dtype=np.float32)
        return np.vstack([sequence, padding])
    return sequence


def load_kaggle_data(data_dir, num_classes=100):
    """Kaggle WLASL verisini yükle"""
    data_dir = Path(data_dir)

    # JSON dosyasını seç
    if num_classes <= 100:
        json_file = "nslt_100.json"
    elif num_classes <= 300:
        json_file = "nslt_300.json"
    elif num_classes <= 1000:
        json_file = "nslt_1000.json"
    else:
        json_file = "nslt_2000.json"

    with open(data_dir / json_file, 'r') as f:
        video_labels = json.load(f)

    # Sınıf listesini yükle
    class_list = {}
    with open(data_dir / "wlasl_class_list.txt", 'r') as f:
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) == 2:
                class_list[int(parts[0])] = parts[1]

    return video_labels, class_list


def process_kaggle_dataset(data_dir, output_dir, num_classes=100, max_frames=30):
    """Kaggle WLASL dataseti işle"""
    data_dir = Path(data_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    videos_dir = data_dir / "videos"

    # Veriyi yükle
    print("Veri yükleniyor...")
    video_labels, class_list = load_kaggle_data(data_dir, num_classes)
    print(f"  Toplam video: {len(video_labels)}")
    print(f"  Sınıf sayısı: {num_classes}")

    # Model yükle
    model_path = download_model()
    landmarker = create_hand_landmarker(model_path)

    # Split'lere göre ayır
    train_data = {'X': [], 'y': []}
    val_data = {'X': [], 'y': []}
    test_data = {'X': [], 'y': []}

    stats = {"total": 0, "success": 0, "failed": 0}

    for video_id, info in tqdm(video_labels.items(), desc="Videolar"):
        video_path = videos_dir / f"{video_id}.mp4"

        if not video_path.exists():
            stats["failed"] += 1
            continue

        stats["total"] += 1
        class_id = info['action'][0]
        subset = info['subset']

        # Sadece ilgili sınıfları al
        if class_id >= num_classes:
            continue

        sequence = extract_landmarks_from_video(video_path, landmarker, max_frames)

        if sequence is not None and len(sequence) > 0:
            sequence = pad_sequence(sequence, max_frames)

            if subset == 'train':
                train_data['X'].append(sequence)
                train_data['y'].append(class_id)
            elif subset == 'val':
                val_data['X'].append(sequence)
                val_data['y'].append(class_id)
            elif subset == 'test':
                test_data['X'].append(sequence)
                test_data['y'].append(class_id)

            stats["success"] += 1
        else:
            stats["failed"] += 1

    landmarker.close()

    # NumPy array'e çevir
    X_train = np.array(train_data['X'], dtype=np.float32)
    y_train = np.array(train_data['y'], dtype=np.int64)
    X_val = np.array(val_data['X'], dtype=np.float32)
    y_val = np.array(val_data['y'], dtype=np.int64)
    X_test = np.array(test_data['X'], dtype=np.float32)
    y_test = np.array(test_data['y'], dtype=np.int64)

    print(f"\n{'='*60}")
    print("EXTRACTION TAMAMLANDI")
    print(f"{'='*60}")
    print(f"İşlenen video: {stats['total']}")
    print(f"Başarılı: {stats['success']}")
    print(f"Başarısız: {stats['failed']}")
    print(f"\nSplit:")
    print(f"  Train: {len(X_train)}")
    print(f"  Val: {len(X_val)}")
    print(f"  Test: {len(X_test)}")

    # Kaydet
    np.save(output_dir / "X_train.npy", X_train)
    np.save(output_dir / "y_train.npy", y_train)
    np.save(output_dir / "X_val.npy", X_val)
    np.save(output_dir / "y_val.npy", y_val)
    np.save(output_dir / "X_test.npy", X_test)
    np.save(output_dir / "y_test.npy", y_test)

    # Sınıf listesi kaydet (sadece kullanılan sınıflar)
    gloss_to_idx = {class_list[i]: i for i in range(num_classes) if i in class_list}
    with open(output_dir / "gloss_to_idx.json", "w") as f:
        json.dump(gloss_to_idx, f, indent=2)

    # Stats kaydet
    with open(output_dir / "extraction_stats.json", "w") as f:
        json.dump({
            "total_videos": stats["total"],
            "success": stats["success"],
            "failed": stats["failed"],
            "num_classes": num_classes,
            "train_size": len(X_train),
            "val_size": len(X_val),
            "test_size": len(X_test)
        }, f, indent=2)

    print(f"\nVeriler kaydedildi: {output_dir}")
    print(f"Veri boyutları:")
    print(f"  X: (N, {max_frames}, 63) - N video, {max_frames} frame, 63 landmark koordinatı")
    print(f"\nSonraki adım: python src/train_lstm.py")


def main():
    data_dir = Path("data/wlasl-kaggle")
    output_dir = Path("data/wlasl-kaggle/landmarks")

    print("="*60)
    print("FAZ 6: Kaggle WLASL Landmark Extraction")
    print("="*60)

    # WLASL100 ile başla (100 kelime)
    process_kaggle_dataset(data_dir, output_dir, num_classes=100, max_frames=30)


if __name__ == "__main__":
    main()
