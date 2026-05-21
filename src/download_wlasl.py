"""
FAZ 6: WLASL Dataset İndirme
Word-Level American Sign Language Dataset
Başlangıç için WLASL100 (100 kelime) kullanılacak
"""

import json
import os
import subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib.request
import time

# WLASL100 için en popüler 100 kelime
WLASL_JSON_URL = "https://raw.githubusercontent.com/dxli94/WLASL/master/start_kit/WLASL_v0.3.json"


def download_wlasl_json(output_dir):
    """WLASL metadata JSON dosyasını indir"""
    json_path = output_dir / "WLASL_v0.3.json"

    if not json_path.exists():
        print("WLASL metadata indiriliyor...")
        urllib.request.urlretrieve(WLASL_JSON_URL, json_path)
        print(f"İndirildi: {json_path}")
    else:
        print(f"Metadata zaten mevcut: {json_path}")

    return json_path


def load_wlasl_data(json_path, num_classes=100):
    """
    WLASL JSON'dan video bilgilerini yükle
    num_classes: Kaç kelime/sınıf kullanılacak (100, 300, 1000, 2000)
    """
    with open(json_path, 'r') as f:
        data = json.load(f)

    # İlk num_classes kelimeyi al
    selected_data = data[:num_classes]

    print(f"\nSeçilen sınıf sayısı: {len(selected_data)}")

    # Video bilgilerini topla
    videos = []
    for entry in selected_data:
        gloss = entry['gloss']  # Kelime
        for instance in entry['instances']:
            videos.append({
                'gloss': gloss,
                'video_id': instance['video_id'],
                'url': instance.get('url', ''),
                'start_time': instance.get('start_time', 0),
                'end_time': instance.get('end_time', 0),
                'split': instance.get('split', 'train')
            })

    print(f"Toplam video sayısı: {len(videos)}")
    return videos, selected_data


def download_video(video_info, output_dir, timeout=30):
    """Tek bir videoyu indir"""
    gloss = video_info['gloss']
    video_id = video_info['video_id']
    url = video_info['url']

    if not url:
        return None, f"URL yok: {video_id}"

    # Klasör oluştur
    gloss_dir = output_dir / gloss
    gloss_dir.mkdir(parents=True, exist_ok=True)

    output_path = gloss_dir / f"{video_id}.mp4"

    # Zaten varsa atla
    if output_path.exists():
        return output_path, "Zaten mevcut"

    try:
        # yt-dlp ile indir
        cmd = [
            'yt-dlp',
            '-f', 'best[height<=480]',  # Max 480p (daha hızlı indirme)
            '-o', str(output_path),
            '--no-playlist',
            '--socket-timeout', str(timeout),
            '--retries', '2',
            '-q',  # Quiet mode
            url
        ]

        result = subprocess.run(cmd, capture_output=True, timeout=timeout+10)

        if output_path.exists():
            return output_path, "Başarılı"
        else:
            return None, "İndirilemedi"

    except subprocess.TimeoutExpired:
        return None, "Timeout"
    except Exception as e:
        return None, str(e)


def download_dataset(videos, output_dir, max_workers=4, max_per_class=50):
    """
    Tüm videoları indir
    max_per_class: Her sınıf için maksimum video sayısı
    """
    print(f"\n{'='*60}")
    print("Video indirme başlıyor...")
    print(f"{'='*60}")

    # Her sınıf için video sayısını sınırla
    class_counts = {}
    filtered_videos = []

    for video in videos:
        gloss = video['gloss']
        if gloss not in class_counts:
            class_counts[gloss] = 0

        if class_counts[gloss] < max_per_class:
            filtered_videos.append(video)
            class_counts[gloss] += 1

    print(f"İndirilecek video sayısı: {len(filtered_videos)}")

    success_count = 0
    fail_count = 0

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(download_video, video, output_dir): video
            for video in filtered_videos
        }

        for i, future in enumerate(as_completed(futures)):
            video = futures[future]
            result, msg = future.result()

            if result:
                success_count += 1
            else:
                fail_count += 1

            # Progress
            if (i + 1) % 10 == 0:
                print(f"İlerleme: {i+1}/{len(filtered_videos)} | Başarılı: {success_count} | Başarısız: {fail_count}")

    print(f"\n{'='*60}")
    print(f"İndirme tamamlandı!")
    print(f"Başarılı: {success_count}")
    print(f"Başarısız: {fail_count}")
    print(f"{'='*60}")

    return success_count, fail_count


def check_yt_dlp():
    """yt-dlp kurulu mu kontrol et"""
    try:
        result = subprocess.run(['yt-dlp', '--version'], capture_output=True)
        print(f"yt-dlp version: {result.stdout.decode().strip()}")
        return True
    except FileNotFoundError:
        print("HATA: yt-dlp kurulu değil!")
        print("Kurmak için: pip install yt-dlp")
        return False


def main():
    # Ayarlar
    output_dir = Path("data/wlasl")
    num_classes = 100  # WLASL100 ile başla
    max_per_class = 80  # Her kelime için max 80 video (daha fazla şans)

    print("="*60)
    print("FAZ 6: WLASL Dataset İndirme")
    print("="*60)
    print(f"Hedef: WLASL{num_classes}")
    print(f"Çıktı klasörü: {output_dir}")

    # yt-dlp kontrol
    if not check_yt_dlp():
        return

    # Klasör oluştur
    output_dir.mkdir(parents=True, exist_ok=True)

    # Metadata indir
    json_path = download_wlasl_json(output_dir)

    # Video bilgilerini yükle
    videos, glosses = load_wlasl_data(json_path, num_classes)

    # Kelime listesini kaydet
    gloss_list = [g['gloss'] for g in glosses]
    with open(output_dir / "glosses.json", 'w') as f:
        json.dump(gloss_list, f, indent=2)
    print(f"\nKelime listesi kaydedildi: {output_dir / 'glosses.json'}")

    # Videoları indir
    videos_dir = output_dir / "videos"
    videos_dir.mkdir(exist_ok=True)

    success, fail = download_dataset(videos, videos_dir, max_workers=4, max_per_class=max_per_class)

    # Özet
    print(f"\nSonraki adımlar:")
    print(f"1. Video frame extraction: python src/extract_video_landmarks.py")
    print(f"2. LSTM model eğitimi: python src/train_lstm.py")


if __name__ == "__main__":
    main()
