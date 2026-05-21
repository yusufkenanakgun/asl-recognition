"""
WLASL Eksik Videoları Tamamla
Her kelime için minimum 5 video olana kadar indir
"""

import json
import subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import Counter


def load_wlasl_json(json_path):
    """WLASL JSON yükle"""
    with open(json_path, 'r') as f:
        return json.load(f)


def count_existing_videos(videos_dir):
    """Mevcut videoları say"""
    videos_dir = Path(videos_dir)
    counts = {}

    for gloss_dir in videos_dir.iterdir():
        if gloss_dir.is_dir():
            gloss = gloss_dir.name
            video_count = len(list(gloss_dir.glob("*.mp4")))
            counts[gloss] = video_count

    return counts


def get_existing_video_ids(videos_dir):
    """Mevcut video ID'lerini al"""
    videos_dir = Path(videos_dir)
    existing = set()

    for gloss_dir in videos_dir.iterdir():
        if gloss_dir.is_dir():
            for video_file in gloss_dir.glob("*.mp4"):
                existing.add(video_file.stem)

    return existing


def download_video(video_info, output_dir, timeout=30):
    """Tek bir videoyu indir"""
    gloss = video_info['gloss']
    video_id = video_info['video_id']
    url = video_info['url']

    if not url:
        return None, "URL yok"

    # Klasör oluştur
    gloss_dir = output_dir / gloss
    gloss_dir.mkdir(parents=True, exist_ok=True)

    output_path = gloss_dir / f"{video_id}.mp4"

    if output_path.exists():
        return output_path, "Zaten mevcut"

    try:
        cmd = [
            'yt-dlp',
            '-f', 'best[height<=480]',
            '-o', str(output_path),
            '--no-playlist',
            '--socket-timeout', str(timeout),
            '--retries', '2',
            '-q',
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


def main():
    # Ayarlar
    min_videos_per_class = 5
    wlasl_dir = Path("data/wlasl")
    videos_dir = wlasl_dir / "videos"
    json_path = wlasl_dir / "WLASL_v0.3.json"

    print("="*60)
    print("WLASL Eksik Video Tamamlama")
    print(f"Hedef: Her kelime için minimum {min_videos_per_class} video")
    print("="*60)

    # Mevcut durumu kontrol et
    existing_counts = count_existing_videos(videos_dir)
    existing_ids = get_existing_video_ids(videos_dir)

    print(f"\nMevcut durum:")
    print(f"  Toplam kelime: {len(existing_counts)}")
    print(f"  Toplam video: {sum(existing_counts.values())}")

    # Eksik kelimeleri bul
    insufficient = {k: v for k, v in existing_counts.items() if v < min_videos_per_class}
    print(f"  Eksik kelime sayısı (< {min_videos_per_class} video): {len(insufficient)}")

    if not insufficient:
        print("\nTüm kelimeler yeterli videoya sahip!")
        return

    # WLASL JSON yükle
    wlasl_data = load_wlasl_json(json_path)

    # İndirilecek videoları topla
    videos_to_download = []

    for entry in wlasl_data:
        gloss = entry['gloss']

        if gloss not in insufficient:
            continue

        current_count = existing_counts.get(gloss, 0)
        needed = min_videos_per_class - current_count

        # Bu kelime için tüm videoları al
        for instance in entry['instances']:
            if instance['video_id'] in existing_ids:
                continue  # Zaten var

            if len([v for v in videos_to_download if v['gloss'] == gloss]) >= needed * 3:
                break  # Yeterince aday var (3x dene)

            videos_to_download.append({
                'gloss': gloss,
                'video_id': instance['video_id'],
                'url': instance.get('url', '')
            })

    print(f"\nİndirilecek aday video: {len(videos_to_download)}")

    if not videos_to_download:
        print("İndirilecek video yok!")
        return

    # İndirme
    print(f"\n{'='*60}")
    print("İndirme başlıyor...")
    print(f"{'='*60}")

    success_count = 0
    fail_count = 0

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {
            executor.submit(download_video, video, videos_dir): video
            for video in videos_to_download
        }

        for i, future in enumerate(as_completed(futures)):
            video = futures[future]
            result, msg = future.result()

            if result:
                success_count += 1
            else:
                fail_count += 1

            if (i + 1) % 10 == 0:
                print(f"İlerleme: {i+1}/{len(videos_to_download)} | Başarılı: {success_count} | Başarısız: {fail_count}")

    # Sonuç
    print(f"\n{'='*60}")
    print("TAMAMLANDI")
    print(f"{'='*60}")
    print(f"Yeni indirilen: {success_count}")
    print(f"Başarısız: {fail_count}")

    # Güncel durumu göster
    new_counts = count_existing_videos(videos_dir)
    still_insufficient = {k: v for k, v in new_counts.items() if v < min_videos_per_class}

    print(f"\nGüncel durum:")
    print(f"  Toplam video: {sum(new_counts.values())}")
    print(f"  Hala eksik kelime: {len(still_insufficient)}")

    if still_insufficient:
        print(f"\nEksik kelimeler:")
        for gloss, count in sorted(still_insufficient.items(), key=lambda x: x[1]):
            print(f"  {gloss}: {count} video")


if __name__ == "__main__":
    main()
