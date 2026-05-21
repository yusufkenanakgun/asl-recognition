"""
FAZ 6: Video Landmark Extraction
WLASL videolarından frame çıkarıp landmark extraction yapma
Her video için: [T frames × 63 landmarks] sequence
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
    """Hand Landmarker modelini indir (zaten varsa atla)"""
    import urllib.request
    model_path = Path("models/hand_landmarker.task")

    if not model_path.exists():
        print("Hand Landmarker modeli indiriliyor...")
        url = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
        model_path.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(url, model_path)
        print(f"Model indirildi: {model_path}")

    return str(model_path)


def create_hand_landmarker(model_path):
    """Hand Landmarker oluştur"""
    base_options = python.BaseOptions(model_asset_path=model_path)
    options = vision.HandLandmarkerOptions(
        base_options=base_options,
        num_hands=2,  # İki el de olabilir
        min_hand_detection_confidence=0.5,
        min_hand_presence_confidence=0.5,
        min_tracking_confidence=0.5
    )
    return vision.HandLandmarker.create_from_options(options)


def normalize_landmarks(landmarks):
    """Landmark'ları normalize et"""
    coords = np.array([[lm.x, lm.y, lm.z] for lm in landmarks])

    # Bilek noktasını origin yap
    wrist = coords[0]
    coords = coords - wrist

    # Elin boyutuna göre normalize et
    scale = np.linalg.norm(coords[9])
    if scale > 0:
        coords = coords / scale

    return coords.flatten()  # 63 boyutlu


def extract_frames(video_path, max_frames=30, target_fps=10, start_time=None, end_time=None):
    """
    Videodan frame çıkar
    max_frames: Maksimum frame sayısı
    target_fps: Hedef FPS
    start_time: Başlangıç zamanı (saniye)
    end_time: Bitiş zamanı (saniye)
    """
    cap = cv2.VideoCapture(str(video_path))

    if not cap.isOpened():
        return None

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    if fps <= 0 or total_frames <= 0:
        cap.release()
        return None

    # Başlangıç ve bitiş frame'lerini hesapla
    start_frame = 0
    end_frame = total_frames

    if start_time is not None and start_time > 0:
        start_frame = int(start_time * fps)
    if end_time is not None and end_time > 0:
        end_frame = int(end_time * fps)

    # Geçerli aralık kontrolü
    start_frame = max(0, min(start_frame, total_frames - 1))
    end_frame = max(start_frame + 1, min(end_frame, total_frames))

    # Başlangıç frame'ine git
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

    # Frame seçim aralığı
    frame_interval = max(1, int(fps / target_fps))
    frames = []

    frame_idx = start_frame
    while len(frames) < max_frames and frame_idx < end_frame:
        ret, frame = cap.read()
        if not ret:
            break

        if (frame_idx - start_frame) % frame_interval == 0:
            # BGR -> RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frames.append(frame_rgb)

        frame_idx += 1

    cap.release()
    return frames


def extract_landmarks_from_video(video_path, landmarker, max_frames=30, start_time=None, end_time=None):
    """
    Bir videodan tüm frame'lerin landmark'larını çıkar
    Returns: (T, 63) şeklinde numpy array veya None
    """
    frames = extract_frames(video_path, max_frames, start_time=start_time, end_time=end_time)

    if frames is None or len(frames) == 0:
        return None

    landmarks_sequence = []

    for frame in frames:
        # MediaPipe Image formatına çevir
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)

        # El tespiti
        result = landmarker.detect(mp_image)

        if result.hand_landmarks and len(result.hand_landmarks) > 0:
            # İlk eli al ve normalize et
            hand_landmarks = result.hand_landmarks[0]
            normalized = normalize_landmarks(hand_landmarks)
            landmarks_sequence.append(normalized)
        else:
            # El bulunamadı - zero vector ekle
            landmarks_sequence.append(np.zeros(63))

    if len(landmarks_sequence) == 0:
        return None

    return np.array(landmarks_sequence, dtype=np.float32)


def pad_sequence(sequence, max_len=30):
    """Sequence'ı sabit uzunluğa getir (padding/truncation)"""
    if len(sequence) > max_len:
        # Truncate
        return sequence[:max_len]
    elif len(sequence) < max_len:
        # Pad with zeros
        padding = np.zeros((max_len - len(sequence), 63), dtype=np.float32)
        return np.vstack([sequence, padding])
    return sequence


def load_video_metadata(wlasl_json_path):
    """WLASL JSON'dan video timing bilgilerini yükle"""
    with open(wlasl_json_path, 'r') as f:
        data = json.load(f)

    video_info = {}
    for entry in data:
        gloss = entry['gloss']
        for instance in entry['instances']:
            video_id = instance['video_id']
            video_info[video_id] = {
                'gloss': gloss,
                'start_time': instance.get('start_time', 0),
                'end_time': instance.get('end_time', 0)
            }
    return video_info


def process_dataset(videos_dir, output_dir, max_frames=30):
    """Tüm videoları işle"""
    videos_dir = Path(videos_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # WLASL JSON'dan timing bilgilerini yükle
    wlasl_json = videos_dir.parent / "WLASL_v0.3.json"
    video_metadata = {}
    if wlasl_json.exists():
        print("Video timing bilgileri yükleniyor...")
        video_metadata = load_video_metadata(wlasl_json)
        print(f"  {len(video_metadata)} video için timing bilgisi bulundu")

    # Model yükle
    model_path = download_model()
    landmarker = create_hand_landmarker(model_path)

    # Kelime klasörlerini bul
    gloss_dirs = [d for d in videos_dir.iterdir() if d.is_dir()]
    print(f"Bulunan kelime sayısı: {len(gloss_dirs)}")

    all_sequences = []
    all_labels = []
    gloss_to_idx = {}
    stats = {"total": 0, "success": 0, "failed": 0}

    for gloss_idx, gloss_dir in enumerate(tqdm(gloss_dirs, desc="Kelimeler")):
        gloss = gloss_dir.name
        gloss_to_idx[gloss] = gloss_idx

        videos = list(gloss_dir.glob("*.mp4"))

        for video_path in videos:
            stats["total"] += 1

            # Video ID'den timing bilgisi al
            video_id = video_path.stem
            start_time = None
            end_time = None

            if video_id in video_metadata:
                start_time = video_metadata[video_id].get('start_time')
                end_time = video_metadata[video_id].get('end_time')

            sequence = extract_landmarks_from_video(
                video_path, landmarker, max_frames,
                start_time=start_time, end_time=end_time
            )

            if sequence is not None and len(sequence) > 0:
                # Padding/truncation
                sequence = pad_sequence(sequence, max_frames)
                all_sequences.append(sequence)
                all_labels.append(gloss_idx)
                stats["success"] += 1
            else:
                stats["failed"] += 1

    landmarker.close()

    # NumPy array'e çevir
    X = np.array(all_sequences, dtype=np.float32)  # (N, T, 63)
    y = np.array(all_labels, dtype=np.int64)  # (N,)

    print(f"\n{'='*60}")
    print("EXTRACTION TAMAMLANDI")
    print(f"{'='*60}")
    print(f"Toplam video: {stats['total']}")
    print(f"Başarılı: {stats['success']} ({stats['success']/stats['total']*100:.1f}%)")
    print(f"Başarısız: {stats['failed']}")
    print(f"Veri boyutu: X={X.shape}, y={y.shape}")

    # Az örnekli sınıfları filtrele (en az 5 örnek gerekli - train/val/test için)
    from collections import Counter
    label_counts = Counter(y)
    valid_labels = {label for label, count in label_counts.items() if count >= 5}

    # Filtreleme
    mask = np.array([label in valid_labels for label in y])
    X_filtered = X[mask]
    y_filtered = y[mask]

    # Label'ları yeniden numaralandır
    old_to_new = {old: new for new, old in enumerate(sorted(valid_labels))}
    y_remapped = np.array([old_to_new[label] for label in y_filtered], dtype=np.int64)

    # gloss_to_idx güncelle
    idx_to_gloss = {v: k for k, v in gloss_to_idx.items()}
    new_gloss_to_idx = {}
    for old_label in sorted(valid_labels):
        gloss = idx_to_gloss[old_label]
        new_gloss_to_idx[gloss] = old_to_new[old_label]

    removed_classes = len(gloss_to_idx) - len(new_gloss_to_idx)
    if removed_classes > 0:
        print(f"\n{removed_classes} sınıf filtrelendi (< 3 örnek)")
        print(f"Kalan sınıf sayısı: {len(new_gloss_to_idx)}")
        print(f"Kalan örnek sayısı: {len(X_filtered)}")

    gloss_to_idx = new_gloss_to_idx
    X = X_filtered
    y = y_remapped

    # Train/Val/Test split (%70/%15/%15)
    from sklearn.model_selection import train_test_split

    try:
        X_train, X_temp, y_train, y_temp = train_test_split(
            X, y, test_size=0.3, random_state=42, stratify=y
        )
        X_val, X_test, y_val, y_test = train_test_split(
            X_temp, y_temp, test_size=0.5, random_state=42, stratify=y_temp
        )
    except ValueError:
        # Stratify başarısız olursa stratify olmadan dene
        print("Stratified split başarısız, random split kullanılıyor...")
        X_train, X_temp, y_train, y_temp = train_test_split(
            X, y, test_size=0.3, random_state=42
        )
        X_val, X_test, y_val, y_test = train_test_split(
            X_temp, y_temp, test_size=0.5, random_state=42
        )

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

    # Gloss mapping kaydet
    with open(output_dir / "gloss_to_idx.json", "w") as f:
        json.dump(gloss_to_idx, f, indent=2)

    # Stats kaydet
    with open(output_dir / "extraction_stats.json", "w") as f:
        json.dump({
            "total_videos": stats["total"],
            "success": stats["success"],
            "failed": stats["failed"],
            "num_classes": len(gloss_to_idx),
            "sequence_length": max_frames,
            "feature_dim": 63,
            "train_size": len(X_train),
            "val_size": len(X_val),
            "test_size": len(X_test)
        }, f, indent=2)

    print(f"\nVeriler kaydedildi: {output_dir}")
    print(f"Sonraki adım: python src/train_lstm.py")


def main():
    videos_dir = Path("data/wlasl/videos")
    output_dir = Path("data/wlasl/landmarks")

    print("="*60)
    print("FAZ 6: Video Landmark Extraction")
    print("="*60)

    if not videos_dir.exists():
        print(f"HATA: Video klasörü bulunamadı: {videos_dir}")
        print("Önce download_wlasl.py çalıştırın.")
        return

    process_dataset(videos_dir, output_dir, max_frames=30)


if __name__ == "__main__":
    main()
