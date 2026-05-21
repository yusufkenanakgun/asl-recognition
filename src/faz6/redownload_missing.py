"""
FAZ 6 V2 — Veri zenginleştirme #1: WLASL eksik videoları yt-dlp ile yeniden indir.

WLASL_v0.3.json'daki `url` alanı kullanılarak, diskte olmayan WLASL-100 videoları
tüm orijinal kaynaklardan (youtube, aslbrick.org, handspeak, signingsavvy, vb.)
yeniden indirilmeye çalışılır. Resume destekli, paralel, log'lu.

Kullanım:
  # Önce kuru deneme (kaç video denenecek?)
  python src/faz6/redownload_missing.py --dry-run

  # Test: ilk 10 video
  python src/faz6/redownload_missing.py --limit 10

  # Tam çalıştır (WLASL-100, 4 thread)
  python src/faz6/redownload_missing.py

  # Önceden başarısız olanları yeniden dene
  python src/faz6/redownload_missing.py --retry-failed

Çıktı:
  data/wlasl-kaggle/videos/<video_id>.mp4   (başarılı indirmeler)
  data/faz6_v2/redownload_log.json          (her instance için durum)
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "wlasl-kaggle"
VIDEOS_DIR = DATA / "videos"
WLASL_JSON = DATA / "WLASL_v0.3.json"
CLASS_LIST = DATA / "wlasl_class_list.txt"
OUT_DIR = ROOT / "data" / "faz6_v2"
LOG_FILE = OUT_DIR / "redownload_log.json"


# ---------------------------------------------------------------------------
# Yükleme
# ---------------------------------------------------------------------------
def load_class_ids() -> dict[str, int]:
    out = {}
    with CLASS_LIST.open() as f:
        for line in f:
            parts = line.strip().split("\t")
            if len(parts) == 2:
                out[parts[1]] = int(parts[0])
    return out


def gather_targets(max_class_id: int) -> list[dict]:
    """Hedef sınıflardaki tüm instance'ları döndür (split/url/source dahil)."""
    gloss_to_id = load_class_ids()
    with WLASL_JSON.open() as f:
        wlasl = json.load(f)

    targets: list[dict] = []
    for entry in wlasl:
        cls_id = gloss_to_id.get(entry["gloss"])
        if cls_id is None or cls_id >= max_class_id:
            continue
        for inst in entry["instances"]:
            targets.append({
                "video_id": inst["video_id"],
                "url": inst["url"],
                "gloss": entry["gloss"],
                "class_id": cls_id,
                "source": inst["source"],
                "split": inst["split"],
                "signer_id": inst["signer_id"],
            })
    return targets


def load_log() -> dict[str, dict]:
    if LOG_FILE.exists():
        with LOG_FILE.open() as f:
            return json.load(f)
    return {}


def save_log(log: dict[str, dict]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    tmp = LOG_FILE.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(log, f, indent=2, ensure_ascii=False)
    tmp.replace(LOG_FILE)


# ---------------------------------------------------------------------------
# İndirme
# ---------------------------------------------------------------------------
def try_download(item: dict, timeout: int, cookies_browser: str | None) -> tuple[str, str | None]:
    """Tek bir instance için yt-dlp çağrısı. (status, error) döndür."""
    video_id = item["video_id"]
    url = item["url"]

    # yt-dlp çıktı şablonu (uzantı yt-dlp tarafından eklenir)
    out_template = str(VIDEOS_DIR / f"{video_id}.%(ext)s")

    cmd = [
        sys.executable, "-m", "yt_dlp",
        "-f", "best[ext=mp4]/mp4/best",
        "-o", out_template,
        "--merge-output-format", "mp4",
        "--no-warnings",
        "--no-playlist",
        "--no-progress",
        "--no-check-certificate",
        "--user-agent",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "--socket-timeout", "20",
        "--retries", "3",
        "--fragment-retries", "3",
        # YouTube bot detection azaltmak için her istek arasına küçük random bekleme
        "--sleep-interval", "1",
        "--max-sleep-interval", "3",
    ]
    if cookies_browser:
        cmd += ["--cookies-from-browser", cookies_browser]
    cmd.append(url)

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace",
        )
    except subprocess.TimeoutExpired:
        return "timeout", None
    except Exception as exc:  # noqa: BLE001
        return "error", str(exc)[:300]

    # Başarı kontrolü: dosya gerçekten oluştu mu?
    expected = VIDEOS_DIR / f"{video_id}.mp4"
    if proc.returncode == 0 and expected.exists() and expected.stat().st_size > 1024:
        return "success", None

    # Olmadıysa: kalan parçalı dosyaları temizle
    for stray in VIDEOS_DIR.glob(f"{video_id}.*"):
        if stray != expected or stray.stat().st_size <= 1024:
            try:
                stray.unlink()
            except OSError:
                pass

    err = (proc.stderr or proc.stdout or "").strip().splitlines()
    last = err[-1][:300] if err else f"returncode={proc.returncode}"
    return "failed", last


# ---------------------------------------------------------------------------
# Ana akış
# ---------------------------------------------------------------------------
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-class-id", type=int, default=100,
                    help="Sınıf id < bu (default 100 = WLASL-100)")
    ap.add_argument("--limit", type=int, default=None,
                    help="Test için ilk N denemeyi yap")
    ap.add_argument("--workers", type=int, default=4,
                    help="Paralel iş sayısı")
    ap.add_argument("--per-video-timeout", type=int, default=180,
                    help="Her video için max süre (sn)")
    ap.add_argument("--retry-failed", action="store_true",
                    help="Önceden 'failed/timeout/error' olanları tekrar dene")
    ap.add_argument("--dry-run", action="store_true",
                    help="Sadece kaç video deneneceğini göster")
    ap.add_argument("--source", type=str, default=None,
                    help="Sadece tek kaynaktan dene (aslu, handspeak, aslpro, vs.)")
    ap.add_argument("--sample-per-source", type=int, default=None,
                    help="Her kaynaktan en fazla N tane dene (kaynak çeşitliliği testi)")
    ap.add_argument(
        "--cookies-browser",
        type=str,
        default=None,
        choices=["firefox", "chrome", "edge", "brave", "opera", "vivaldi", "safari", "chromium"],
        help="Tarayıcıdan YouTube cookie'lerini kullan (bot detection bypass). "
             "İlgili tarayıcıda YouTube'a giriş yapmış olmalısın.",
    )
    args = ap.parse_args()

    VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Diskte olanlar
    on_disk = {p.stem for p in VIDEOS_DIR.glob("*.mp4")}

    # Önceki log
    log = load_log()

    # Hedefler
    targets = gather_targets(args.max_class_id)
    print(f"WLASL-{args.max_class_id} toplam instance: {len(targets)}")
    print(f"Diskte hâlihazırda var: {sum(1 for t in targets if t['video_id'] in on_disk)}")

    # Filtre: diskte yoksa VE (log'da yoksa VEYA --retry-failed varsa)
    todo: list[dict] = []
    for t in targets:
        vid = t["video_id"]
        if vid in on_disk:
            # Zaten var, log'u güncelle
            log[vid] = {**t, "status": "already_on_disk"}
            continue
        prev = log.get(vid, {}).get("status")
        if prev == "success":
            # Daha önce indirildi, ama disk'te yok? log'u temizle
            continue
        if prev in {"failed", "timeout", "error"} and not args.retry_failed:
            continue
        todo.append(t)

    # Kaynak dağılımı
    src_counts = Counter(t["source"] for t in todo)
    print(f"\nİndirilecek aday sayısı: {len(todo)}")
    print("Kaynak dağılımı:")
    for src, n in sorted(src_counts.items(), key=lambda x: -x[1]):
        print(f"  {src:<20} {n:>5}")

    if args.source:
        before = len(todo)
        todo = [t for t in todo if t["source"] == args.source]
        print(f"\n--source {args.source}: {before} → {len(todo)}")

    if args.sample_per_source:
        per_src: dict[str, list[dict]] = {}
        for t in todo:
            per_src.setdefault(t["source"], []).append(t)
        sampled = []
        for src, items in per_src.items():
            sampled.extend(items[: args.sample_per_source])
        print(f"\n--sample-per-source {args.sample_per_source}: "
              f"{len(todo)} → {len(sampled)} (kaynak başına en fazla {args.sample_per_source})")
        todo = sampled

    if args.limit:
        todo = todo[: args.limit]
        print(f"\n--limit {args.limit} aktif, {len(todo)} deneme yapılacak.")

    if args.dry_run:
        print("\n[dry-run] Çıkıyorum, indirme yok.")
        return

    if not todo:
        print("\nİndirilecek video yok. Çıkıyorum.")
        return

    print(f"\nİndirme başlıyor: {len(todo)} video, {args.workers} thread\n")
    save_log(log)  # ilk snapshot

    counts = Counter()
    t0 = time.time()
    save_every = max(10, len(todo) // 20)

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {
            pool.submit(try_download, item, args.per_video_timeout, args.cookies_browser): item
            for item in todo
        }

        for i, fut in enumerate(as_completed(futures), 1):
            item = futures[fut]
            try:
                status, err = fut.result()
            except Exception as exc:  # noqa: BLE001
                status, err = "error", str(exc)[:300]

            counts[status] += 1
            log[item["video_id"]] = {
                **item,
                "status": status,
                "error": err,
                "ts": int(time.time()),
            }

            elapsed = time.time() - t0
            rate = i / elapsed if elapsed > 0 else 0
            eta = (len(todo) - i) / rate if rate > 0 else 0
            print(
                f"[{i:>5}/{len(todo)}] {status:<8} "
                f"{item['gloss']:<15} {item['source']:<15} "
                f"vid={item['video_id']:<8} "
                f"({counts['success']} ok / {sum(counts.values())} tried, "
                f"rate {rate:.1f}/s, eta {eta/60:.1f}min)"
                + (f" -- {err[:80]}" if err else "")
            )

            if i % save_every == 0:
                save_log(log)

    save_log(log)

    elapsed = time.time() - t0
    print("\n" + "=" * 60)
    print("İNDİRME TAMAMLANDI")
    print("=" * 60)
    print(f"Toplam deneme: {sum(counts.values())}")
    for s in ("success", "failed", "timeout", "error"):
        print(f"  {s:<8}: {counts[s]}")
    print(f"Geçen süre: {elapsed/60:.1f} dakika")
    if counts["success"]:
        print(f"\n✓ {counts['success']} yeni video data/wlasl-kaggle/videos/'a eklendi")
        print("Sonraki adım: src/faz6/select_classes.py'yi tekrar çalıştır,")
        print("yeni video sayılarını gör.")


if __name__ == "__main__":
    main()
