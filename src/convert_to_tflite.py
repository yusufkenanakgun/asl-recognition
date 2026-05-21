"""
FAZ 7 - PyTorch -> ONNX -> TFLite dönüşümü.

Üç model ailesini Android demosu için TFLite formatına çevirir:
  1) EfficientNet-B0   (harf, image-based)       input (1, 3, 224, 224) -> (1, 29)
  2) MLP landmark      (harf, landmark-based)    input (1, 63)          -> (1, 29)
  3) BiLSTM x6         (kelime, single + 5 seed) input (1, 32, 128)     -> (1, 100)

Pipeline:
  .pth -> torch.onnx.export -> onnx2tf -> .tflite

Çıktı: models/tflite/*.tflite + boyut/sanity-check raporu (stdout + tflite_report.json).

Önkoşul (Windows için):
    pip install onnx onnx2tf tensorflow

Çalıştırma:
    python src/convert_to_tflite.py
    python src/convert_to_tflite.py --only mlp          # sadece MLP
    python src/convert_to_tflite.py --only efficientnet
    python src/convert_to_tflite.py --only lstm

Kritik risk: BiLSTM TFLite operatör desteği. Çevrilemezse stdout'ta net hata mesajı
ile rapor edilir; matrise "FAILED" olarak yazılır.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
import time
import traceback
from pathlib import Path

import numpy as np

# onnx2tf bazı modellerde object-dtype .npy yazıyor; NumPy varsayılan olarak pickle yüklemiyor.
# Bu süreç boyunca np.load default'u allow_pickle=True olsun (sadece bu script kapsamında).
_orig_np_load = np.load
def _np_load_pickle_ok(*args, **kwargs):
    kwargs.setdefault("allow_pickle", True)
    return _orig_np_load(*args, **kwargs)
np.load = _np_load_pickle_ok  # type: ignore[assignment]

import torch
import torch.nn as nn
from torchvision.models import efficientnet_b0

ROOT = Path(__file__).resolve().parents[1]
DEPLOY_DIR = ROOT / "models" / "deploy"
OUT_DIR = ROOT / "models" / "tflite"
OUT_DIR.mkdir(parents=True, exist_ok=True)
REPORT_PATH = OUT_DIR / "tflite_report.json"

ONNX_OPSET = 17
SANITY_TOL = 1e-3  # |torch - tflite| max fark eşiği (float32)


# ---------------------------------------------------------------------------
# Model mimarileri (eğitim kodundan kopyalandı — checkpoint yüklemek için)
# ---------------------------------------------------------------------------
class LandmarkMLP(nn.Module):
    def __init__(self, input_size=63, hidden_sizes=(256, 128, 64), num_classes=29, dropout=0.3):
        super().__init__()
        layers = []
        prev = input_size
        for h in hidden_sizes:
            layers += [nn.Linear(prev, h), nn.BatchNorm1d(h), nn.ReLU(), nn.Dropout(dropout)]
            prev = h
        layers.append(nn.Linear(prev, num_classes))
        self.network = nn.Sequential(*layers)

    def forward(self, x):
        return self.network(x)


class LSTMClassifier(nn.Module):
    def __init__(self, input_size=128, hidden_size=192, num_layers=2,
                 num_classes=100, dropout=0.5, bidirectional=True):
        super().__init__()
        self.bidirectional = bidirectional
        self.lstm = nn.LSTM(
            input_size=input_size, hidden_size=hidden_size, num_layers=num_layers,
            batch_first=True, dropout=dropout if num_layers > 1 else 0,
            bidirectional=bidirectional,
        )
        fc_in = hidden_size * 2 if bidirectional else hidden_size
        self.fc = nn.Sequential(
            nn.Linear(fc_in, 128), nn.ReLU(), nn.Dropout(dropout),
            nn.Linear(128, num_classes),
        )

    def forward(self, x):
        _, (h_n, _) = self.lstm(x)
        hidden = torch.cat((h_n[-2], h_n[-1]), dim=1) if self.bidirectional else h_n[-1]
        return self.fc(hidden)


def build_efficientnet(num_classes=29):
    model = efficientnet_b0(weights=None)
    in_features = model.classifier[1].in_features
    model.classifier[1] = nn.Linear(in_features, num_classes)
    return model


# ---------------------------------------------------------------------------
# Dönüşüm yardımcıları
# ---------------------------------------------------------------------------
def _extract_state_dict(ckpt):
    if isinstance(ckpt, dict) and "model_state_dict" in ckpt:
        return ckpt["model_state_dict"]
    if isinstance(ckpt, dict) and "state_dict" in ckpt:
        return ckpt["state_dict"]
    return ckpt  # raw state_dict olabilir


def _file_mb(path: Path) -> float:
    return path.stat().st_size / (1024 * 1024)


def _export_onnx(model: nn.Module, dummy_input: torch.Tensor, onnx_path: Path):
    torch.onnx.export(
        model, dummy_input, str(onnx_path),
        input_names=["input"], output_names=["logits"],
        opset_version=ONNX_OPSET, do_constant_folding=True,
        dynamic_axes=None,  # fixed shape — mobil için daha güvenli
    )


def _onnx_to_tflite(onnx_path: Path, out_tflite: Path, keep_input_shape: bool = False) -> None:
    """onnx2tf ile ONNX -> TFLite. Geçici dizin kullanır, sonra istenen tflite'ı kopyalar.

    keep_input_shape=True: onnx2tf'in input shape'i transpose etmesini engeller
    (3D LSTM input'ları için kritik; aksi halde (1, T, F) -> (1, F, T) yorumlayabilir).
    """
    import onnx2tf  # lazy import — kullanıcı çağırmazsa hata vermesin

    # onnx2tf, image modellerinde quantization calibration için internetten test_image
    # indirmeye çalışıyor; float32 dönüşümde gereksiz ve genelde başarısız oluyor.
    # Stub'ladığımızda random tensor döndürüyor — sadece validation aşaması için.
    _stub = lambda *a, **k: np.random.rand(1, 224, 224, 3).astype(np.float32)
    try:
        from onnx2tf.utils import common_functions as _cf  # type: ignore
        _cf.download_test_image_data = _stub
    except Exception:
        pass
    try:
        import onnx2tf.onnx2tf as _o2t_main  # type: ignore
        _o2t_main.download_test_image_data = _stub
    except Exception:
        pass

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_out = Path(tmpdir)
        convert_kwargs = dict(
            input_onnx_file_path=str(onnx_path),
            output_folder_path=str(tmp_out),
            copy_onnx_input_output_names_to_tflite=True,
            non_verbose=True,
        )
        if keep_input_shape:
            # LSTM (1, T, F) gibi 3D sekans inputları için axis transpose'u engelle
            convert_kwargs["keep_shape_absolutely_input_names"] = ["input"]
        onnx2tf.convert(**convert_kwargs)
        # onnx2tf birden çok tflite üretir (float32, dynamic_range, integer_quant...).
        # Float32 sürümü modelin temel adıyla kaydedilir, "<name>_float32.tflite".
        candidates = sorted(tmp_out.glob("*_float32.tflite"))
        if not candidates:
            candidates = sorted(tmp_out.glob("*.tflite"))
        if not candidates:
            raise RuntimeError("onnx2tf hiç .tflite çıktısı üretmedi")
        shutil.copy2(candidates[0], out_tflite)


def _sanity_check(model: nn.Module, tflite_path: Path, dummy_input: torch.Tensor) -> dict:
    """PyTorch çıktısı ile TFLite çıktısını karşılaştır."""
    # Try modern litert first, fall back to tflite_runtime / tensorflow.lite
    interpreter = None
    backend = None
    try:
        from ai_edge_litert.interpreter import Interpreter  # type: ignore
        interpreter = Interpreter(model_path=str(tflite_path))
        backend = "ai_edge_litert"
    except Exception:
        pass
    if interpreter is None:
        try:
            import tensorflow as tf  # type: ignore
            interpreter = tf.lite.Interpreter(model_path=str(tflite_path))
            backend = "tensorflow.lite"
        except Exception as e:
            return {"ok": False, "error": f"TFLite interpreter yüklenemedi: {e}"}

    interpreter.allocate_tensors()
    inp_detail = interpreter.get_input_details()[0]
    out_detail = interpreter.get_output_details()[0]

    np_input = dummy_input.detach().cpu().numpy().astype(np.float32)
    # onnx2tf NHWC'ye çevirir (image modelleri için). Shape uyuşmazlığı varsa transpose dene.
    if list(inp_detail["shape"]) != list(np_input.shape):
        if np_input.ndim == 4 and np_input.shape[1] in (1, 3):
            np_input = np.transpose(np_input, (0, 2, 3, 1))  # NCHW -> NHWC
    interpreter.set_tensor(inp_detail["index"], np_input)
    interpreter.invoke()
    tflite_out = interpreter.get_tensor(out_detail["index"])

    with torch.no_grad():
        torch_out = model(dummy_input).cpu().numpy()

    max_diff = float(np.abs(torch_out - tflite_out).max())
    torch_top1 = int(torch_out.argmax(axis=-1)[0])
    tflite_top1 = int(tflite_out.argmax(axis=-1)[0])

    return {
        "ok": True,
        "backend": backend,
        "max_abs_diff": max_diff,
        "within_tolerance": max_diff <= SANITY_TOL,
        "torch_top1": torch_top1,
        "tflite_top1": tflite_top1,
        "top1_match": torch_top1 == tflite_top1,
    }


def _convert_one(name: str, model: nn.Module, dummy_input: torch.Tensor,
                 out_tflite: Path, keep_input_shape: bool = False) -> dict:
    t0 = time.perf_counter()
    info: dict = {"name": name, "out": str(out_tflite.relative_to(ROOT))}
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            onnx_path = Path(tmpdir) / f"{name}.onnx"
            _export_onnx(model, dummy_input, onnx_path)
            info["onnx_mb"] = round(_file_mb(onnx_path), 3)
            _onnx_to_tflite(onnx_path, out_tflite, keep_input_shape=keep_input_shape)
        info["tflite_mb"] = round(_file_mb(out_tflite), 3)
        info["status"] = "OK"
        info["sanity"] = _sanity_check(model, out_tflite, dummy_input)
    except Exception as e:
        info["status"] = "FAILED"
        info["error"] = str(e)
        info["traceback"] = traceback.format_exc(limit=4)
    info["seconds"] = round(time.perf_counter() - t0, 2)
    return info


# ---------------------------------------------------------------------------
# Her model ailesi için dönüşüm
# ---------------------------------------------------------------------------
def convert_efficientnet() -> dict:
    ckpt_path = DEPLOY_DIR / "efficientnet_b0.pth"
    if not ckpt_path.exists():
        return {"name": "efficientnet_b0", "status": "SKIPPED",
                "error": f"Checkpoint bulunamadı: {ckpt_path}"}
    model = build_efficientnet(num_classes=29)
    sd = _extract_state_dict(torch.load(ckpt_path, map_location="cpu"))
    model.load_state_dict(sd, strict=True)
    model.eval()
    dummy = torch.randn(1, 3, 224, 224)
    return _convert_one("efficientnet_b0", model, dummy, OUT_DIR / "efficientnet_b0.tflite")


def convert_mlp() -> dict:
    ckpt_path = DEPLOY_DIR / "mlp_landmark.pth"
    if not ckpt_path.exists():
        return {"name": "mlp_landmark", "status": "SKIPPED",
                "error": f"Checkpoint bulunamadı: {ckpt_path}"}
    model = LandmarkMLP(input_size=63, hidden_sizes=(256, 128, 64), num_classes=29, dropout=0.3)
    sd = _extract_state_dict(torch.load(ckpt_path, map_location="cpu"))
    model.load_state_dict(sd, strict=True)
    model.eval()
    # MLP'de BatchNorm1d var; eval() çağrıldı, dummy input 2'lik batch verirsek BN sorun yaşamaz.
    # Ama mobil her zaman batch=1 göndereceği için fixed shape (1, 63) export ediyoruz.
    dummy = torch.randn(1, 63)
    return _convert_one("mlp_landmark", model, dummy, OUT_DIR / "mlp_landmark.tflite")


def convert_lstm_one(ckpt_name: str, out_name: str) -> dict:
    ckpt_path = DEPLOY_DIR / ckpt_name
    if not ckpt_path.exists():
        return {"name": out_name, "status": "SKIPPED",
                "error": f"Checkpoint bulunamadı: {ckpt_path}"}
    model = LSTMClassifier(input_size=128, hidden_size=192, num_layers=2,
                           num_classes=100, dropout=0.5, bidirectional=True)
    sd = _extract_state_dict(torch.load(ckpt_path, map_location="cpu"))
    model.load_state_dict(sd, strict=True)
    model.eval()
    dummy = torch.randn(1, 32, 128)
    return _convert_one(out_name, model, dummy, OUT_DIR / f"{out_name}.tflite",
                        keep_input_shape=True)


def convert_lstm_all() -> list[dict]:
    results = [convert_lstm_one("lstm_single_best.pth", "lstm_single_best")]
    for s in range(5):
        results.append(convert_lstm_one(f"lstm_seed{s}.pth", f"lstm_seed{s}"))
    return results


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def _print_row(r: dict) -> None:
    name = r.get("name", "?")
    status = r.get("status", "?")
    size = r.get("tflite_mb", "-")
    sanity = r.get("sanity", {})
    sanity_str = ""
    if sanity:
        if sanity.get("ok"):
            sanity_str = (f"top1_match={sanity['top1_match']} "
                          f"max_diff={sanity['max_abs_diff']:.2e} "
                          f"backend={sanity['backend']}")
        else:
            sanity_str = f"sanity_error={sanity.get('error', '?')}"
    err = r.get("error", "")
    secs = r.get("seconds", "-")
    print(f"  [{status:7s}] {name:24s} size={size!s:>8} MB  {secs}s  {sanity_str}")
    if err and status != "OK":
        print(f"           -> {err}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", choices=["efficientnet", "mlp", "lstm"], default=None,
                    help="Sadece belirli bir model ailesini dönüştür")
    args = ap.parse_args()

    print(f"PyTorch: {torch.__version__}")
    print(f"Deploy dir: {DEPLOY_DIR}")
    print(f"Output dir: {OUT_DIR}\n")

    results: list[dict] = []

    if args.only in (None, "efficientnet"):
        print("=> EfficientNet-B0 dönüşümü")
        results.append(convert_efficientnet())
        _print_row(results[-1])
        print()

    if args.only in (None, "mlp"):
        print("=> MLP landmark dönüşümü")
        results.append(convert_mlp())
        _print_row(results[-1])
        print()

    if args.only in (None, "lstm"):
        print("=> BiLSTM dönüşümü (single_best + 5 seed)")
        for r in convert_lstm_all():
            results.append(r)
            _print_row(r)
        print()

    # Özet
    ok = sum(1 for r in results if r.get("status") == "OK")
    failed = sum(1 for r in results if r.get("status") == "FAILED")
    skipped = sum(1 for r in results if r.get("status") == "SKIPPED")
    print(f"Sonuç: {ok} OK, {failed} FAILED, {skipped} SKIPPED")

    REPORT_PATH.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Rapor: {REPORT_PATH.relative_to(ROOT)}")

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
