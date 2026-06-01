"""
FAZ 6 V2 - Adım 2: Landmark Extraction Pipeline (proposal'a sadık, sade sürüm).

V1'e göre değişiklikler:
- 2 el (left + right) ayrı kanallar, her el için presence_flag
- WLASL frame_start/frame_end kırpma
- Adaptif frame örnekleme (sabit SEQ_LEN frame)
- Her el ayrı normalize (wrist origin + orta parmak MCP ölçek)

Feature kompozisyonu (per frame):
  left  hand: 1 (presence) + 21*3 (xyz) = 64
  right hand: 1 (presence) + 21*3       = 64
  TOPLAM    : 128

Çıktı:
  data/faz6_v2/landmarks_wlasl100/
    X_train.npy, y_train.npy
    X_val.npy,   y_val.npy
    X_test.npy,  y_test.npy
    meta_<split>.json  (her örnek için video_id, signer_id, source)
    extraction_stats.json
"""
from __future__ import annotations

import json
import urllib.request
from pathlib import Path

import cv2
import numpy as np
from tqdm import tqdm

import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision as mp_vision


# ---------------------------------------------------------------------------
# Yapılandırma
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data" / "wlasl-kaggle"
SELECTED_FILE = ROOT / "data" / "faz6_v2" / "selected_classes.json"
OUT_DIR = ROOT / "data" / "faz6_v2" / "landmarks_wlasl100"
MODELS_DIR = ROOT / "models"

SEQ_LEN = 32
HAND_MODEL_URL = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"

HAND_FEAT_DIM = 1 + 21 * 3   # presence + xyz = 64
FEATURE_DIM = HAND_FEAT_DIM * 2  # left + right = 128


# ---------------------------------------------------------------------------
# Model yükleme
# ---------------------------------------------------------------------------
def ensure_model(url: str, target: Path) -> Path:
    if not target.exists():
        print(f"İndiriliyor: {target.name} ...")
        target.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(url, target)
    return target


def make_hand_landmarker(model_path: Path, num_hands: int = 2) -> mp_vision.HandLandmarker:
    opts = mp_vision.HandLandmarkerOptions(
        base_options=mp_python.BaseOptions(model_asset_path=str(model_path)),
        num_hands=num_hands,
        min_hand_detection_confidence=0.5,
        min_hand_presence_confidence=0.5,
        min_tracking_confidence=0.5,
    )
    return mp_vision.HandLandmarker.create_from_options(opts)


# ---------------------------------------------------------------------------
# Frame örnekleme
# ---------------------------------------------------------------------------
def sample_frames(video_path: Path, frame_start: int, frame_end: int, seq_len: int) -> list[np.ndarray] | None:
    """frame_start..frame_end aralığından seq_len kadar uniform örnek al (1-indexed WLASL)."""
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        return None

    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if total <= 0:
        cap.release()
        return None

    # WLASL 1-indexed; frame_end=-1 → tüm video
    fs = max(0, frame_start - 1)
    fe = total if frame_end == -1 else min(total, frame_end)
    if fe <= fs:
        fs, fe = 0, total

    # seq_len uniform örnek
    if fe - fs <= seq_len:
        indices = list(range(fs, fe))
    else:
        indices = np.linspace(fs, fe - 1, seq_len).astype(int).tolist()

    frames: list[np.ndarray] = []
    idx_set = set(indices)
    cur = 0
    while cur < fe:
        ret, frame = cap.read()
        if not ret:
            break
        if cur in idx_set:
            frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        cur += 1

    cap.release()
    return frames if frames else None


# ---------------------------------------------------------------------------
# Landmark normalize
# ---------------------------------------------------------------------------
def normalize_hand(landmarks) -> np.ndarray:
    """Wrist'e göre origin, orta parmak MCP (idx 9) uzunluğuna göre ölçek. (21, 3)."""
    coords = np.array([[lm.x, lm.y, lm.z] for lm in landmarks], dtype=np.float32)
    coords -= coords[0]  # wrist origin
    scale = float(np.linalg.norm(coords[9]))
    if scale > 1e-6:
        coords /= scale
    return coords


# ---------------------------------------------------------------------------
# Tek frame -> feature vektörü
# ---------------------------------------------------------------------------
def frame_features(frame_rgb: np.ndarray, hand: mp_vision.HandLandmarker,
                   single_hand: bool = False) -> np.ndarray:
    """Tek bir RGB frame'i feature vektörüne çevir.

    single_hand=False: V2 modu (128-d, sol+sağ presence+coords).
    single_hand=True : V1 modu (63-d, tek el, presence flag yok).
    """
    mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
    hand_res = hand.detect(mp_img)

    if single_hand:
        # V1 mimarisi: ilk algılanan el, 63-d (presence flag yok)
        feat = np.zeros(21 * 3, dtype=np.float32)
        if hand_res.hand_landmarks:
            feat = normalize_hand(hand_res.hand_landmarks[0]).flatten().astype(np.float32)
        return feat

    left_feat = np.zeros(HAND_FEAT_DIM, dtype=np.float32)   # presence=0, coords=0
    right_feat = np.zeros(HAND_FEAT_DIM, dtype=np.float32)

    if hand_res.hand_landmarks:
        for lmks, handedness in zip(hand_res.hand_landmarks, hand_res.handedness):
            label = handedness[0].category_name  # 'Left' veya 'Right'
            coords = normalize_hand(lmks).flatten()  # 63
            feat = np.concatenate([[1.0], coords])   # presence + coords = 64
            if label == "Left":
                left_feat = feat.astype(np.float32)
            else:
                right_feat = feat.astype(np.float32)

    return np.concatenate([left_feat, right_feat])  # (128,)


# ---------------------------------------------------------------------------
# Video -> sequence
# ---------------------------------------------------------------------------
def video_to_sequence(
    video_path: Path,
    frame_start: int,
    frame_end: int,
    hand: mp_vision.HandLandmarker,
    single_hand: bool = False,
    no_crop: bool = False,
) -> np.ndarray | None:
    if no_crop:
        frame_start, frame_end = 1, -1
    frames = sample_frames(video_path, frame_start, frame_end, SEQ_LEN)
    if not frames:
        return None

    feat_dim = 21 * 3 if single_hand else FEATURE_DIM
    feats = [frame_features(f, hand, single_hand=single_hand) for f in frames]
    seq = np.stack(feats, axis=0)  # (T, feat_dim)

    # Pad veya kırp
    if seq.shape[0] >= SEQ_LEN:
        seq = seq[:SEQ_LEN]
    else:
        pad = np.zeros((SEQ_LEN - seq.shape[0], feat_dim), dtype=np.float32)
        seq = np.vstack([seq, pad])

    return seq.astype(np.float32)


# ---------------------------------------------------------------------------
# Ana çalıştırma
# ---------------------------------------------------------------------------
def main(limit: int | None = None, out_dir: Path = OUT_DIR,
         single_hand: bool = False, no_crop: bool = False) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    feat_dim = 21 * 3 if single_hand else FEATURE_DIM
    print(f"Konfig: single_hand={single_hand}, no_crop={no_crop}, feature_dim={feat_dim}")
    print(f"Çıktı klasörü: {out_dir}")

    # Seçilen sınıfları yükle
    with SELECTED_FILE.open() as f:
        sel = json.load(f)
    gloss_to_idx = sel["gloss_to_idx"]
    target_class_ids = {entry["class_id"] for entry in sel["selected"]}
    cls_id_to_local = {entry["class_id"]: i for i, entry in enumerate(sel["selected"])}

    print(f"Seçilen sınıf sayısı: {len(gloss_to_idx)}")

    # WLASL JSON
    with (DATA_DIR / "WLASL_v0.3.json").open() as f:
        wlasl = json.load(f)
    with (DATA_DIR / "wlasl_class_list.txt").open() as f:
        orig = {}
        for line in f:
            parts = line.strip().split("\t")
            if len(parts) == 2:
                orig[parts[1]] = int(parts[0])

    # Diskte hangi video_id'ler var
    videos_dir = DATA_DIR / "videos"
    on_disk = {p.stem for p in videos_dir.glob("*.mp4")}

    # Toplanacak instance listesi (sadece hedef sınıflara dahil ve diskte olan)
    work_items: list[dict] = []
    for entry in wlasl:
        gloss = entry["gloss"]
        cls_id = orig.get(gloss)
        if cls_id is None or cls_id not in target_class_ids:
            continue
        local_idx = cls_id_to_local[cls_id]
        for inst in entry["instances"]:
            if inst["video_id"] not in on_disk:
                continue
            work_items.append({
                "video_id": inst["video_id"],
                "gloss": gloss,
                "class_id": cls_id,
                "local_idx": local_idx,
                "split": inst["split"],
                "frame_start": inst["frame_start"],
                "frame_end": inst["frame_end"],
                "signer_id": inst["signer_id"],
                "source": inst["source"],
            })

    if limit:
        work_items = work_items[:limit]

    print(f"Toplam işlenecek video: {len(work_items)}")
    print(f"  train: {sum(1 for w in work_items if w['split']=='train')}")
    print(f"  val:   {sum(1 for w in work_items if w['split']=='val')}")
    print(f"  test:  {sum(1 for w in work_items if w['split']=='test')}")

    # Modeller
    hand_model = ensure_model(HAND_MODEL_URL, MODELS_DIR / "hand_landmarker.task")
    hand_lm = make_hand_landmarker(hand_model, num_hands=1 if single_hand else 2)

    # Toplama
    bins = {"train": {"X": [], "y": [], "meta": []},
            "val":   {"X": [], "y": [], "meta": []},
            "test":  {"X": [], "y": [], "meta": []}}

    stats = {"total": 0, "success": 0, "failed": 0, "by_split": {}}

    for w in tqdm(work_items, desc="Videolar"):
        video_path = videos_dir / f"{w['video_id']}.mp4"
        stats["total"] += 1
        try:
            seq = video_to_sequence(
                video_path, w["frame_start"], w["frame_end"], hand_lm,
                single_hand=single_hand, no_crop=no_crop,
            )
        except Exception as exc:  # noqa: BLE001
            print(f"  HATA {w['video_id']}: {exc}")
            seq = None

        if seq is None:
            stats["failed"] += 1
            continue

        bin_ = bins[w["split"]]
        bin_["X"].append(seq)
        bin_["y"].append(w["local_idx"])
        bin_["meta"].append({
            "video_id": w["video_id"],
            "gloss": w["gloss"],
            "signer_id": w["signer_id"],
            "source": w["source"],
        })
        stats["success"] += 1

    hand_lm.close()

    # Kaydet
    for split, b in bins.items():
        if not b["X"]:
            print(f"UYARI: {split} setinde örnek yok!")
            continue
        X = np.stack(b["X"]).astype(np.float32)
        y = np.array(b["y"], dtype=np.int64)
        np.save(out_dir / f"X_{split}.npy", X)
        np.save(out_dir / f"y_{split}.npy", y)
        with (out_dir / f"meta_{split}.json").open("w", encoding="utf-8") as f:
            json.dump(b["meta"], f, indent=2, ensure_ascii=False)
        stats["by_split"][split] = {"size": len(X), "shape": list(X.shape)}
        print(f"  {split}: {X.shape}")

    # gloss_to_idx
    with (out_dir / "gloss_to_idx.json").open("w", encoding="utf-8") as f:
        json.dump(gloss_to_idx, f, indent=2, ensure_ascii=False)

    stats["feature_dim"] = feat_dim
    stats["seq_len"] = SEQ_LEN
    stats["num_classes"] = len(gloss_to_idx)
    stats["single_hand"] = single_hand
    stats["no_crop"] = no_crop
    with (out_dir / "extraction_stats.json").open("w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)

    print("\n" + "=" * 60)
    print("EXTRACTION TAMAMLANDI")
    print("=" * 60)
    print(json.dumps(stats, indent=2))
    print(f"\nÇıktı: {out_dir}")


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--limit", type=int, default=None, help="Test için sadece N video işle")
    p.add_argument("--out-dir", type=str, default=None,
                   help="Çıktı klasörü (varsayılan: data/faz6_v2/landmarks_wlasl100)")
    p.add_argument("--single-hand", action="store_true",
                   help="V1 modu — tek el, 63-d, presence flag yok")
    p.add_argument("--no-crop", action="store_true",
                   help="WLASL frame_start/frame_end yok say, tüm video kullanılır")
    args = p.parse_args()
    out_dir = Path(args.out_dir) if args.out_dir else OUT_DIR
    main(limit=args.limit, out_dir=out_dir,
         single_hand=args.single_hand, no_crop=args.no_crop)
