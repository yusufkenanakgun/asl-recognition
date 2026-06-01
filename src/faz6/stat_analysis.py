"""
FAZ 6 V2 - Ek: İstatistiksel anlamlılık analizi.

Tez Bölüm 5.3'teki "+4.08 puan ensemble kazancı" iddiasının test seti
gürültüsünden ayırt edilip edilemediğini test eder. Yeni eğitim yok;
yalnızca mevcut 5 seed checkpoint'i + ensemble üzerinde:

  - Wilson 95% binomial CI (her model için Top-1)
  - Paired bootstrap (10k resample) ile fark CI'leri:
      ensemble - seed_mean
      ensemble - best_seed
      ensemble - each_seed_i
  - McNemar's test: ensemble vs en iyi seed (paired predictions)

Çıktı:
  models/faz6_v2/stat_analysis.json
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import torch
from scipy import stats

from train_v2 import LSTMClassifier, BATCH_SIZE


ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data" / "faz6_v2" / "landmarks_wlasl100"
MODEL_DIR = ROOT / "models" / "faz6_v2"

BOOTSTRAP_N = 10_000
RNG_SEED = 42


def load_model(ckpt_path: Path, device: torch.device) -> LSTMClassifier:
    chk = torch.load(ckpt_path, map_location=device)
    hp = chk["hyperparameters"]
    model = LSTMClassifier(
        input_size=hp["input_size"], hidden_size=hp["hidden_size"],
        num_layers=hp["num_layers"], num_classes=hp["num_classes"],
        dropout=hp["dropout"], bidirectional=hp["bidirectional"],
    ).to(device)
    model.load_state_dict(chk["model_state_dict"])
    model.eval()
    return model


def predict_logits(model: LSTMClassifier, X: torch.Tensor, device: torch.device) -> np.ndarray:
    out = []
    with torch.no_grad():
        for i in range(0, len(X), BATCH_SIZE):
            xb = X[i:i + BATCH_SIZE].to(device)
            out.append(model(xb).cpu())
    return torch.cat(out, dim=0).numpy()


def wilson_ci(k: int, n: int, z: float = 1.959963984540054) -> tuple[float, float]:
    """Wilson score 95% CI for a binomial proportion. Returns (lo, hi) in [0, 1]."""
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = (z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))


def paired_bootstrap_diff(
    correct_a: np.ndarray, correct_b: np.ndarray,
    n_resample: int, rng: np.random.Generator,
) -> dict:
    """Bootstrap CI for (acc_a - acc_b) using paired resampling of test clips."""
    n = len(correct_a)
    assert len(correct_b) == n
    diffs = np.empty(n_resample, dtype=np.float64)
    for i in range(n_resample):
        idx = rng.integers(0, n, size=n)
        diffs[i] = correct_a[idx].mean() - correct_b[idx].mean()
    p_raw = 2 * min((diffs <= 0).mean(), (diffs >= 0).mean())
    return {
        "mean_diff_pp": float(diffs.mean() * 100),
        "ci95_lo_pp": float(np.percentile(diffs, 2.5) * 100),
        "ci95_hi_pp": float(np.percentile(diffs, 97.5) * 100),
        "p_two_sided": float(min(p_raw, 1.0)),
    }


def mcnemar(correct_a: np.ndarray, correct_b: np.ndarray) -> dict:
    """Exact McNemar (binomial) on paired binary outcomes.
    b = a correct, b wrong;  c = a wrong, b correct."""
    b = int(((correct_a == 1) & (correct_b == 0)).sum())
    c = int(((correct_a == 0) & (correct_b == 1)).sum())
    n_disc = b + c
    if n_disc == 0:
        return {"b": 0, "c": 0, "n_discordant": 0, "p_value": 1.0}
    # Exact two-sided binomial test: P(X <= min(b,c) | n=b+c, p=0.5) * 2
    k = min(b, c)
    p = float(2 * stats.binom.cdf(k, n_disc, 0.5))
    p = min(p, 1.0)
    return {"b": b, "c": c, "n_discordant": n_disc, "p_value": p}


def main() -> None:
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")

    X_test = np.load(DATA_DIR / "X_test.npy")
    y_test = np.load(DATA_DIR / "y_test.npy")
    n_test = len(y_test)
    print(f"Test: {X_test.shape}  ({n_test} clip)")

    X_t = torch.from_numpy(X_test).float()
    ckpts = sorted(MODEL_DIR.glob("best_lstm_seed*.pth"))
    assert len(ckpts) == 5, f"5 seed bekleniyor, {len(ckpts)} bulundu"

    per_seed_logits: list[np.ndarray] = []
    per_seed_correct: list[np.ndarray] = []
    per_seed_top1: list[float] = []

    print("\n--- Seed-by-seed inference ---")
    for p in ckpts:
        model = load_model(p, device)
        logits = predict_logits(model, X_t, device)
        preds = logits.argmax(axis=1)
        correct = (preds == y_test).astype(np.int8)
        top1 = float(correct.mean() * 100)
        per_seed_logits.append(logits)
        per_seed_correct.append(correct)
        per_seed_top1.append(top1)
        print(f"  {p.name}: Top-1 = {top1:.2f}%  ({int(correct.sum())}/{n_test})")

    ens_logits = np.mean(np.stack(per_seed_logits, axis=0), axis=0)
    ens_preds = ens_logits.argmax(axis=1)
    ens_correct = (ens_preds == y_test).astype(np.int8)
    ens_top1 = float(ens_correct.mean() * 100)
    print(f"\n  ENSEMBLE:    Top-1 = {ens_top1:.2f}%  ({int(ens_correct.sum())}/{n_test})")

    seed_mean = float(np.mean(per_seed_top1))
    seed_range_half = float((max(per_seed_top1) - min(per_seed_top1)) / 2)
    seed_std = float(np.std(per_seed_top1, ddof=1))
    best_seed_idx = int(np.argmax(per_seed_top1))
    print(f"\n  Seed mean:   {seed_mean:.2f}%  (std={seed_std:.2f}, half-range=±{seed_range_half:.2f})")
    print(f"  Best seed:   seed {best_seed_idx}  ({per_seed_top1[best_seed_idx]:.2f}%)")

    # Wilson CI per model
    print("\n--- Wilson 95% binomial CI (her model) ---")
    ci_per_model: list[dict] = []
    for i, (top1, correct) in enumerate(zip(per_seed_top1, per_seed_correct)):
        k = int(correct.sum())
        lo, hi = wilson_ci(k, n_test)
        ci_per_model.append({"seed": i, "top1_pct": top1,
                              "ci95_lo_pct": lo * 100, "ci95_hi_pct": hi * 100})
        print(f"  seed {i}: {top1:5.2f}%  [{lo*100:5.2f}, {hi*100:5.2f}]")
    lo_e, hi_e = wilson_ci(int(ens_correct.sum()), n_test)
    print(f"  ENS   : {ens_top1:5.2f}%  [{lo_e*100:5.2f}, {hi_e*100:5.2f}]")

    # Paired bootstrap differences
    print(f"\n--- Paired bootstrap (n_resample={BOOTSTRAP_N}, seed={RNG_SEED}) ---")
    rng = np.random.default_rng(RNG_SEED)

    # ensemble - best_seed
    diff_best = paired_bootstrap_diff(ens_correct, per_seed_correct[best_seed_idx], BOOTSTRAP_N, rng)
    print(f"  ENS - best_seed (seed {best_seed_idx}):")
    print(f"    mean Δ = {diff_best['mean_diff_pp']:+.2f}pp  "
          f"95% CI [{diff_best['ci95_lo_pp']:+.2f}, {diff_best['ci95_hi_pp']:+.2f}]  "
          f"p={diff_best['p_two_sided']:.3f}")

    # ensemble - seed_i for each i
    diff_each = []
    for i, c in enumerate(per_seed_correct):
        d = paired_bootstrap_diff(ens_correct, c, BOOTSTRAP_N, rng)
        d["vs_seed"] = i
        diff_each.append(d)
        print(f"  ENS - seed {i}:  Δ = {d['mean_diff_pp']:+.2f}pp  "
              f"CI [{d['ci95_lo_pp']:+.2f}, {d['ci95_hi_pp']:+.2f}]  "
              f"p={d['p_two_sided']:.3f}")

    # ensemble - "synthetic seed mean" correctness vector
    #   per-clip empirical seed-mean accuracy across the 5 seeds
    seed_mean_correct = np.stack(per_seed_correct, axis=0).mean(axis=0)  # in [0,1]
    # bootstrap on a continuous "expected correctness" vector — sample clips paired
    diffs = np.empty(BOOTSTRAP_N, dtype=np.float64)
    for i in range(BOOTSTRAP_N):
        idx = rng.integers(0, n_test, size=n_test)
        diffs[i] = ens_correct[idx].mean() - seed_mean_correct[idx].mean()
    p_raw_smean = 2 * min((diffs <= 0).mean(), (diffs >= 0).mean())
    diff_smean = {
        "mean_diff_pp": float(diffs.mean() * 100),
        "ci95_lo_pp": float(np.percentile(diffs, 2.5) * 100),
        "ci95_hi_pp": float(np.percentile(diffs, 97.5) * 100),
        "p_two_sided": float(min(p_raw_smean, 1.0)),
    }
    print(f"  ENS - seed_mean (per-clip):  Δ = {diff_smean['mean_diff_pp']:+.2f}pp  "
          f"CI [{diff_smean['ci95_lo_pp']:+.2f}, {diff_smean['ci95_hi_pp']:+.2f}]  "
          f"p={diff_smean['p_two_sided']:.3f}")

    # McNemar's test: ensemble vs best seed
    mc = mcnemar(ens_correct, per_seed_correct[best_seed_idx])
    print(f"\n--- McNemar (ENS vs best_seed seed {best_seed_idx}) ---")
    print(f"  b (ENS✓ best✗) = {mc['b']}")
    print(f"  c (ENS✗ best✓) = {mc['c']}")
    print(f"  n_discordant   = {mc['n_discordant']}")
    print(f"  exact two-sided p = {mc['p_value']:.4f}")

    out = {
        "n_test_clips": int(n_test),
        "bootstrap_resamples": BOOTSTRAP_N,
        "rng_seed": RNG_SEED,
        "per_seed": {
            f"seed_{i}": {
                "top1_pct": per_seed_top1[i],
                "n_correct": int(per_seed_correct[i].sum()),
                "wilson_ci95_pct": [ci_per_model[i]["ci95_lo_pct"], ci_per_model[i]["ci95_hi_pct"]],
            }
            for i in range(5)
        },
        "ensemble": {
            "top1_pct": ens_top1,
            "n_correct": int(ens_correct.sum()),
            "wilson_ci95_pct": [lo_e * 100, hi_e * 100],
        },
        "summary": {
            "seed_mean_pct": seed_mean,
            "seed_std_pct": seed_std,
            "seed_half_range_pct": seed_range_half,
            "best_seed_index": best_seed_idx,
            "best_seed_top1_pct": per_seed_top1[best_seed_idx],
        },
        "bootstrap_diff_pp": {
            "ens_minus_best_seed": diff_best,
            "ens_minus_seed_mean_per_clip": diff_smean,
            "ens_minus_each_seed": diff_each,
        },
        "mcnemar_ens_vs_best_seed": mc,
    }

    out_path = MODEL_DIR / "stat_analysis.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print(f"\nKaydedildi: {out_path}")


if __name__ == "__main__":
    main()
