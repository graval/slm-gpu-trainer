"""
EdgeShield: Standalone PyTorch to ONNX Exporter & INT8 Quantizer
Usage:
    .\.venv\Scripts\python.exe scripts/export_onnx.py --checkpoint models/edgeshield_lsa --quantize
    .\.venv\Scripts\python.exe scripts/export_onnx.py --checkpoint models/edgeshield_bpd --quantize
"""

import os
import sys
import argparse
from pathlib import Path

# Ensure slm-tr root is on sys.path
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from transformers import AutoModelForSequenceClassification, AutoTokenizer
from edgeshield.edge_deploy.onnx_runtime import EdgeDeploymentEngine


def main():
    parser = argparse.ArgumentParser(description="Export trained EdgeShield models to ONNX and INT8")
    parser.add_argument("--checkpoint", type=str, default="models/edgeshield_lsa", help="Path to trained PyTorch model directory")
    parser.add_argument("--out-dir", type=str, default="models/onnx_edgeshield", help="Output directory for ONNX models")
    parser.add_argument("--name", type=str, default=None, help="Base name for exported model (default: checkpoint directory name)")
    parser.add_argument("--seq-len", type=int, default=128, help="Max sequence length")
    parser.add_argument("--quantize", action="store_true", default=True, help="Automatically perform INT8 Dynamic Quantization")
    args = parser.parse_args()

    ckpt_path = Path(args.checkpoint)
    if not ckpt_path.exists():
        if (PROJECT_ROOT / args.checkpoint).exists():
            ckpt_path = PROJECT_ROOT / args.checkpoint
        else:
            print(f"[!] ERROR: Checkpoint not found at: {ckpt_path}")
            sys.exit(1)

    out_dir = Path(args.out_dir)
    if not out_dir.is_absolute():
        out_dir = PROJECT_ROOT / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    model_name = args.name or ckpt_path.name

    print("=" * 78)
    print("      [+] EDGESHIELD ONNX EXPORT & QUANTIZATION")
    print("=" * 78)
    print(f"  • Source Checkpoint: {ckpt_path}")
    print(f"  • Target Directory:  {out_dir}")
    print(f"  • Model Base Name:   {model_name}")
    print(f"  • Sequence Length:   {args.seq_len}")
    print("-" * 78)

    print("[*] Loading PyTorch model and tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(str(ckpt_path))
    model = AutoModelForSequenceClassification.from_pretrained(str(ckpt_path))

    engine = EdgeDeploymentEngine(str(out_dir))
    
    print("[*] Exporting to standard ONNX FP32 format...")
    fp32_path = engine.export_to_onnx(model, tokenizer, model_name=model_name, seq_len=args.seq_len)
    fp32_size_mb = Path(fp32_path).stat().st_size / (1024 * 1024)
    print(f"[+] FP32 ONNX exported: {fp32_path} ({fp32_size_mb:.2f} MB)")

    if args.quantize:
        print("[*] Performing Dynamic INT8 Post-Training Quantization (PTQ)...")
        int8_path = engine.quantize_int8(fp32_path)
        int8_size_mb = Path(int8_path).stat().st_size / (1024 * 1024)
        print(f"[+] INT8 ONNX exported: {int8_path} ({int8_size_mb:.2f} MB)")
        compression_ratio = (1.0 - (int8_size_mb / fp32_size_mb)) * 100.0
        print(f"[+] Footprint Reduction: {compression_ratio:.1f}% reduction ({(fp32_size_mb / int8_size_mb):.1f}x smaller)")

    print("=" * 78)
    print("  [+] ONNX Edge Deployment artifacts successfully created!")
    print("=" * 78)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    main()
