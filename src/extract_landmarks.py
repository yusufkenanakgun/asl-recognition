"""
FAZ 4: MediaPipe Landmark Extraction
Tüm görüntülerden el landmark'larını çıkar ve kaydet
21 nokta × 3 koordinat = 63 boyutlu normalize vektör
"""

import cv2
import numpy as np
from pathlib import Path
from tqdm import tqdm
import json
import urllib.request
import os

# MediaPipe Tasks API
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# Sınıf isimleri
CLASSES = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M',
           'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
           'del', 'nothing', 'space']


def download_model():
    """Hand Landmarker modelini indir"""
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
        num_hands=1,
        min_hand_detection_confidence=0.5,
        min_hand_presence_confidence=0.5,
        min_tracking_confidence=0.5
    )
    return vision.HandLandmarker.create_from_options(options)


def normalize_landmarks(landmarks):
    """
    Landmark'ları normalize et (el boyutundan bağımsız hale getir)
    - Bilek noktasını (0) origin olarak al
    - Elin boyutuna göre scale et
    """
    coords = np.array([[lm.x, lm.y, lm.z] for lm in landmarks])

    # Bilek noktasını origin yap
    wrist = coords[0]
    coords = coords - wrist

    # Elin boyutuna göre normalize et (bilek-orta parmak MCP mesafesi)
    scale = np.linalg.norm(coords[9])
    if scale > 0:
        coords = coords / scale

    # 63 boyutlu vektör olarak düzleştir
    return coords.flatten()


def extract_landmarks_from_image(image_path, landmarker):
    """
    Tek bir görüntüden landmark çıkar
    Returns: 63 boyutlu vektör veya None (el bulunamazsa)
    """
    # MediaPipe Image formatında yükle
    mp_image = mp.Image.create_from_file(str(image_path))

    # El tespiti
    result = landmarker.detect(mp_image)

    if result.hand_landmarks and len(result.hand_landmarks) > 0:
        # İlk eli al
        hand_landmarks = result.hand_landmarks[0]
        return normalize_landmarks(hand_landmarks)

    return None


def process_split(split_dir, output_dir, landmarker):
    """
    Bir split klasöründeki tüm görüntüleri işle
    """
    split_name = split_dir.name
    print(f"\n{'='*60}")
    print(f"İşleniyor: {split_name}")
    print(f"{'='*60}")

    all_landmarks = []
    all_labels = []
    failed_images = []

    # Her sınıf için
    for cls_idx, cls_name in enumerate(CLASSES):
        cls_path = split_dir / cls_name
        if not cls_path.exists():
            continue

        images = list(cls_path.glob("*.jpg"))
        success_count = 0

        for img_path in tqdm(images, desc=f"{cls_name}", leave=False):
            landmarks = extract_landmarks_from_image(img_path, landmarker)

            if landmarks is not None:
                all_landmarks.append(landmarks)
                all_labels.append(cls_idx)
                success_count += 1
            else:
                failed_images.append(str(img_path))

        # Sınıf başarı oranı
        success_rate = (success_count / len(images)) * 100 if images else 0
        if success_rate < 100:
            print(f"  {cls_name}: {success_count}/{len(images)} ({success_rate:.1f}%)")

    # NumPy array'e çevir
    X = np.array(all_landmarks, dtype=np.float32)
    y = np.array(all_labels, dtype=np.int64)

    # Kaydet
    output_dir.mkdir(parents=True, exist_ok=True)
    np.save(output_dir / f"X_{split_name}.npy", X)
    np.save(output_dir / f"y_{split_name}.npy", y)

    # İstatistikler
    total_images = sum(len(list((split_dir / cls).glob("*.jpg")))
                       for cls in CLASSES if (split_dir / cls).exists())

    print(f"\nSonuç:")
    print(f"  Toplam görüntü: {total_images}")
    print(f"  Başarılı: {len(X)} ({len(X)/total_images*100:.1f}%)")
    print(f"  Başarısız: {len(failed_images)} ({len(failed_images)/total_images*100:.1f}%)")
    print(f"  Veri boyutu: X={X.shape}, y={y.shape}")

    return {
        "split": split_name,
        "total": total_images,
        "success": len(X),
        "failed": len(failed_images),
        "success_rate": round(len(X)/total_images*100, 2),
        "shape": list(X.shape)
    }, failed_images


def main():
    # Yollar
    data_root = Path("data/asl-split")
    output_dir = Path("data/landmarks")

    print("="*60)
    print("FAZ 4: MediaPipe Landmark Extraction")
    print("="*60)
    print(f"Kaynak: {data_root}")
    print(f"Çıktı: {output_dir}")

    # Model indir (ilk çalıştırmada)
    model_path = download_model()

    # Hand Landmarker oluştur
    print("\nHand Landmarker başlatılıyor...")
    landmarker = create_hand_landmarker(model_path)

    all_stats = []
    all_failed = []

    # Her split için
    for split in ["train", "val", "test"]:
        split_dir = data_root / split
        if split_dir.exists():
            stats, failed = process_split(split_dir, output_dir, landmarker)
            all_stats.append(stats)
            all_failed.extend(failed)

    landmarker.close()

    # Genel özet
    print("\n" + "="*60)
    print("GENEL ÖZET")
    print("="*60)

    total_all = sum(s["total"] for s in all_stats)
    success_all = sum(s["success"] for s in all_stats)
    failed_all = sum(s["failed"] for s in all_stats)

    print(f"Toplam görüntü: {total_all}")
    print(f"Başarılı extraction: {success_all} ({success_all/total_all*100:.2f}%)")
    print(f"Başarısız (el bulunamadı): {failed_all} ({failed_all/total_all*100:.2f}%)")

    # İstatistikleri kaydet
    stats_path = output_dir / "extraction_stats.json"
    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump({
            "splits": all_stats,
            "total_images": total_all,
            "total_success": success_all,
            "total_failed": failed_all,
            "detection_rate": round(success_all/total_all*100, 2)
        }, f, indent=2)
    print(f"\nİstatistikler kaydedildi: {stats_path}")

    # Başarısız görüntüleri kaydet (tezde analiz için)
    if all_failed:
        failed_path = output_dir / "failed_images.txt"
        with open(failed_path, "w", encoding="utf-8") as f:
            f.write("\n".join(all_failed))
        print(f"Başarısız görüntüler: {failed_path}")

    print("\n" + "="*60)
    print("LANDMARK EXTRACTION TAMAMLANDI!")
    print("="*60)
    print("\nSonraki adım: MLP modelini eğitmek için src/train_mlp.py çalıştırın")


if __name__ == "__main__":
    main()
