"""
FAZ 6 V2 - Adım 1: Sınıf seçimi
WLASL_v0.3.json'daki tüm sınıfları diskte var olan video sayısına göre sırala.
WLASL100 içinden en çok video sayısına sahip 30 sınıfı seç.

Çıktı:
- data/faz6_v2/class_stats.json   (tüm sınıfların istatistikleri)
- data/faz6_v2/selected_classes.json (seçilen 30 sınıf)
"""
import json
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data" / "wlasl-kaggle"
OUT_DIR = ROOT / "data" / "faz6_v2"
OUT_DIR.mkdir(parents=True, exist_ok=True)

WLASL_JSON = DATA_DIR / "WLASL_v0.3.json"
VIDEOS_DIR = DATA_DIR / "videos"
CLASS_LIST_FILE = DATA_DIR / "wlasl_class_list.txt"

# Sabitler — FAZ 6 V2 (proposal'a sadık: WLASL-100)
N_TOP_CLASSES = 100
WLASL_TIER = 100  # WLASL100 içinden seç (None ise tüm 2000)
MIN_VIDEOS_PER_CLASS = 1  # filtre yok, WLASL-100'ün tamamı alınır
MIN_PER_SPLIT = {"train": 1, "val": 0, "test": 0}


def main():
    print("=" * 60)
    print("FAZ 6 V2 — Sınıf Seçimi")
    print("=" * 60)

    # Diskte hangi video_id'ler var?
    on_disk = {p.stem for p in VIDEOS_DIR.glob("*.mp4")}
    print(f"\nDiskte toplam video: {len(on_disk):,}")

    # class_list (id -> gloss)
    id_to_gloss = {}
    with CLASS_LIST_FILE.open() as f:
        for line in f:
            parts = line.strip().split("\t")
            if len(parts) == 2:
                id_to_gloss[int(parts[0])] = parts[1]
    gloss_to_id = {g: i for i, g in id_to_gloss.items()}

    # WLASL ana JSON
    with WLASL_JSON.open() as f:
        wlasl = json.load(f)

    # Her sınıf için istatistik
    stats = []
    for entry in wlasl:
        gloss = entry["gloss"]
        cls_id = gloss_to_id.get(gloss)
        if cls_id is None:
            continue

        instances = entry["instances"]
        on_disk_instances = [i for i in instances if i["video_id"] in on_disk]

        split_count = Counter(i["split"] for i in on_disk_instances)
        signer_count = len({i["signer_id"] for i in on_disk_instances})

        stats.append({
            "class_id": cls_id,
            "gloss": gloss,
            "total_instances": len(instances),
            "on_disk": len(on_disk_instances),
            "train": split_count.get("train", 0),
            "val": split_count.get("val", 0),
            "test": split_count.get("test", 0),
            "unique_signers": signer_count,
        })

    stats.sort(key=lambda x: x["class_id"])

    # Genel bakış
    total_classes_with_video = sum(1 for s in stats if s["on_disk"] > 0)
    print(f"Toplam sınıf (class_list): {len(id_to_gloss):,}")
    print(f"Diskte en az 1 videosu olan: {total_classes_with_video:,}")

    # WLASL100 alt kümesi
    if WLASL_TIER:
        pool = [s for s in stats if s["class_id"] < WLASL_TIER]
        print(f"\nWLASL{WLASL_TIER} havuzu: {len(pool)} sınıf")
    else:
        pool = stats
        print(f"\nTüm sınıf havuzu: {len(pool)} sınıf")

    # Filtre: her split için minimum
    candidates = [
        s for s in pool
        if s["on_disk"] >= MIN_VIDEOS_PER_CLASS
        and s["train"] >= MIN_PER_SPLIT["train"]
        and s["val"] >= MIN_PER_SPLIT["val"]
        and s["test"] >= MIN_PER_SPLIT["test"]
    ]
    print(
        f"Filtre uyumlu (≥{MIN_VIDEOS_PER_CLASS} video, "
        f"train≥{MIN_PER_SPLIT['train']}, val≥{MIN_PER_SPLIT['val']}, "
        f"test≥{MIN_PER_SPLIT['test']}): {len(candidates)}"
    )

    # En çok videosu olanlardan başlayarak seç
    candidates.sort(key=lambda x: (-x["on_disk"], -x["train"], x["class_id"]))
    selected = candidates[:N_TOP_CLASSES]

    print(f"\n{'=' * 60}")
    print(f"SEÇİLEN {len(selected)} SINIF (WLASL{WLASL_TIER}'den top {N_TOP_CLASSES})")
    print(f"{'=' * 60}")
    print(f"{'#':>3} {'cls_id':>6}  {'gloss':<15} {'top':>4} {'tr':>3} {'val':>3} {'tst':>3} {'sgn':>3}")
    for i, s in enumerate(selected, 1):
        print(
            f"{i:>3} {s['class_id']:>6}  {s['gloss']:<15} "
            f"{s['on_disk']:>4} {s['train']:>3} {s['val']:>3} {s['test']:>3} "
            f"{s['unique_signers']:>3}"
        )

    # Özetler
    tot = sum(s["on_disk"] for s in selected)
    trn = sum(s["train"] for s in selected)
    val = sum(s["val"] for s in selected)
    tst = sum(s["test"] for s in selected)
    print(f"\nToplam video: {tot} | train: {trn} | val: {val} | test: {tst}")
    print(
        f"Sınıf başına ortalama: top={tot/len(selected):.1f}, "
        f"train={trn/len(selected):.1f}, val={val/len(selected):.1f}, test={tst/len(selected):.1f}"
    )

    # Kaydet
    with (OUT_DIR / "class_stats.json").open("w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    print(f"\nKaydedildi: {OUT_DIR / 'class_stats.json'}")

    selected_payload = {
        "criteria": {
            "wlasl_tier": WLASL_TIER,
            "n_top_classes": N_TOP_CLASSES,
            "min_videos_per_class": MIN_VIDEOS_PER_CLASS,
            "min_per_split": MIN_PER_SPLIT,
        },
        "selected": selected,
        "gloss_to_idx": {s["gloss"]: i for i, s in enumerate(selected)},
        "idx_to_class_id": {i: s["class_id"] for i, s in enumerate(selected)},
    }
    with (OUT_DIR / "selected_classes.json").open("w", encoding="utf-8") as f:
        json.dump(selected_payload, f, indent=2, ensure_ascii=False)
    print(f"Kaydedildi: {OUT_DIR / 'selected_classes.json'}")


if __name__ == "__main__":
    main()
