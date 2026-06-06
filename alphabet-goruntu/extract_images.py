"""Extract sample images for the 29 letters and 10 words PDF."""
import hashlib
import shutil
from pathlib import Path
import cv2

ROOT = Path(__file__).parent
DATA = ROOT.parent / "data"
LETTERS_OUT = ROOT / "images" / "letters"
WORDS_OUT = ROOT / "images" / "words"
LETTERS_OUT.mkdir(parents=True, exist_ok=True)
WORDS_OUT.mkdir(parents=True, exist_ok=True)

# --- Letters (29 classes) -------------------------------------------------
test_dir = DATA / "asl-alphabet" / "asl_alphabet_test" / "asl_alphabet_test"
train_dir = DATA / "asl-alphabet" / "asl_alphabet_train" / "asl_alphabet_train"

for L in list("ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
    shutil.copyfile(test_dir / f"{L}_test.jpg", LETTERS_OUT / f"{L}.jpg")

for cls in ("nothing", "space"):
    shutil.copyfile(test_dir / f"{cls}_test.jpg", LETTERS_OUT / f"{cls}.jpg")

shutil.copyfile(train_dir / "del" / "del1.jpg", LETTERS_OUT / "del.jpg")
print("letters: 29 images copied")

# --- Words (10 best-known): 3 frames per word ----------------------------
top10 = ["want", "paint", "bed", "paper", "same",
         "table", "dance", "drink", "son", "school"]

videos_root = DATA / "wlasl" / "videos"


def read_all_frames(video_path: str):
    cap = cv2.VideoCapture(video_path)
    frames = []
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        frames.append(frame)
    cap.release()
    return frames


def pick_three_frames(frames):
    """Pick 3 visually distinct frames spread across the central 20%-85%
    of the clip. In each of the 3 equal sub-ranges, choose the frame with
    the largest JPEG size (proxy for content density — black/title cards
    compress to tiny files)."""
    if not frames:
        return []
    n = len(frames)
    lo, hi = int(n * 0.20), int(n * 0.85)
    if hi - lo < 9:
        lo, hi = 0, n
    span = (hi - lo) // 3
    picks = []
    for k in range(3):
        a = lo + k * span
        b = lo + (k + 1) * span if k < 2 else hi
        step = max((b - a) // 12, 1)
        best_size, best_i = -1, a
        for i in range(a, b, step):
            ok, buf = cv2.imencode(".jpg", frames[i], [cv2.IMWRITE_JPEG_QUALITY, 90])
            if ok and buf.size > best_size:
                best_size, best_i = buf.size, i
        picks.append((best_i, frames[best_i]))
    return picks


seen_first_frame_hash = set()
for w in top10:
    word_dir = videos_root / w
    videos = sorted(word_dir.glob("*.mp4"))
    if not videos:
        print(f"!! no videos for {w}")
        continue
    chosen_video = None
    chosen_picks = None
    for vp in videos:
        frames = read_all_frames(str(vp))
        if not frames:
            continue
        picks = pick_three_frames(frames)
        if len(picks) < 3:
            continue
        # de-dup at video-level using the middle frame's hash
        ok, buf = cv2.imencode(".jpg", picks[1][1], [cv2.IMWRITE_JPEG_QUALITY, 90])
        if not ok:
            continue
        h = hashlib.md5(buf.tobytes()).hexdigest()
        if h in seen_first_frame_hash:
            print(f"   skip duplicate video {vp.name} for {w}")
            continue
        seen_first_frame_hash.add(h)
        chosen_video = vp
        chosen_picks = picks
        break
    if chosen_picks is None:
        print(f"!! no unique video found for {w}")
        continue
    for k, (idx, frame) in enumerate(chosen_picks, start=1):
        out_path = WORDS_OUT / f"{w}_{k}.jpg"
        cv2.imwrite(str(out_path), frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
    total = sum(1 for _ in [None])  # noqa
    idxs = [p[0] for p in chosen_picks]
    print(f"word {w}: {chosen_video.name} frames {idxs} -> {w}_1..3.jpg")

# Remove stale single-frame word images from previous runs
for old in WORDS_OUT.glob("*.jpg"):
    stem = old.stem
    if "_" not in stem:
        old.unlink()
        print(f"   removed stale {old.name}")

print("done.")
