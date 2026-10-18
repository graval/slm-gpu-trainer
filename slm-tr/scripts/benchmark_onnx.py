r"""
EdgeShield: Standalone ONNX Runtime Benchmark & INT8 Profiler
Usage:
    .\.venv\Scripts\python.exe scripts/benchmark_onnx.py --model models/onnx_edgeshield/edgeshield_lsa_int8.onnx --runs 100
    .\.venv\Scripts\python.exe scripts/benchmark_onnx.py --export-from models/edgeshield_lsa --runs 100
"""

import os
import sys
import time
import json
import argparse
from pathlib import Path
import numpy as np

# Ensure slm-tr root is on sys.path regardless of where command is launched from
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def parse_args():
    parser = argparse.ArgumentParser(description="EdgeShield ONNX Latency & Performance Benchmarker")
    parser.add_argument(
        "--model",
        type=str,
        default="models/onnx_edgeshield/edgeshield_lsa_int8.onnx",
        help="Path to the ONNX or INT8 ONNX model file."
    )
    parser.add_argument(
        "--export-from",
        type=str,
        default=None,
        help="Optional: PyTorch checkpoint directory to export and quantize before benchmarking."
    )
    parser.add_argument(
        "--providers",
        type=str,
        default="CPUExecutionProvider",
        help="Comma-separated execution providers (e.g. CPUExecutionProvider, DmlExecutionProvider, CUDAExecutionProvider)."
    )
    parser.add_argument("--runs", type=int, default=100, help="Number of benchmark iterations.")
    parser.add_argument("--warmup", type=int, default=10, help="Number of warmup iterations.")
    parser.add_argument("--batch", type=int, default=1, help="Batch size for benchmarking.")
    parser.add_argument("--seq-len", type=int, default=128, help="Sequence length for tokenized inputs.")
    parser.add_argument("--export_summary", action="store_true", help="Save benchmark results to JSON.")
    return parser.parse_args()


def main():
    args = parse_args()
    
    try:
        import onnxruntime as ort
    except ImportError:
        print("[!] ERROR: onnxruntime is not installed. Run: pip install onnxruntime")
        sys.exit(1)

    model_path = Path(args.model)
    if not model_path.exists():
        if (PROJECT_ROOT / args.model).exists():
            model_path = PROJECT_ROOT / args.model
        elif (PROJECT_ROOT / "models" / "onnx_edgeshield" / args.model).exists():
            model_path = PROJECT_ROOT / "models" / "onnx_edgeshield" / args.model

    # Check if user requested on-the-fly export and quantization
    if args.export_from:
        from transformers import AutoModelForSequenceClassification, AutoTokenizer
        from edgeshield.edge_deploy.onnx_runtime import EdgeDeploymentEngine

        checkpoint_path = Path(args.export_from)
        if not checkpoint_path.is_absolute():
            checkpoint_path = PROJECT_ROOT / checkpoint_path
        
        print(f"[*] Exporting PyTorch model from '{checkpoint_path}' to ONNX...")
        tokenizer = AutoTokenizer.from_pretrained(str(checkpoint_path))
        pytorch_model = AutoModelForSequenceClassification.from_pretrained(str(checkpoint_path))
        
        engine = EdgeDeploymentEngine(str(PROJECT_ROOT / "models" / "onnx_edgeshield"))
        fp32_onnx = engine.export_to_onnx(pytorch_model, tokenizer, model_name=checkpoint_path.name, seq_len=args.seq_len)
        print(f"[+] Exported FP32 ONNX model: {fp32_onnx}")
        
        print("[*] Quantizing to INT8...")
        int8_onnx = engine.quantize_int8(fp32_onnx)
        print(f"[+] Dynamic INT8 Quantized model: {int8_onnx}")
        model_path = Path(int8_onnx)

    if not model_path.exists():
        print(f"[!] ERROR: ONNX model file not found at: {model_path}")
        print("    Tip: Run with '--export-from models/edgeshield_lsa' to export and quantize from weights.")
        sys.exit(1)

    # Resolve providers
    requested_providers = [p.strip() for p in args.providers.split(",") if p.strip()]
    available_providers = ort.get_available_providers()
    active_providers = [p for p in requested_providers if p in available_providers]
    if not active_providers:
        active_providers = ["CPUExecutionProvider"]

    file_size_mb = model_path.stat().st_size / (1024 * 1024)

    print("=" * 78)
    print("      [+] EDGESHIELD ONNX RUNTIME INFERENCE BENCHMARK")
    print("=" * 78)
    print(f"  • Model File:       {model_path.name} ({file_size_mb:.2f} MB)")
    print(f"  • Full Path:        {model_path}")
    print(f"  • Active Providers: {active_providers}")
    print(f"  • Benchmark Runs:   {args.runs} (Warmup: {args.warmup})")
    print(f"  • Batch / Seq-Len:  Batch={args.batch}, SeqLen={args.seq_len}")
    print("-" * 78)

    sess_options = ort.SessionOptions()
    sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    sess_options.intra_op_num_threads = os.cpu_count() or 8

    session = ort.InferenceSession(str(model_path), sess_options, providers=active_providers)
    in_names = [i.name for i in session.get_inputs()]
    
    # Formulate feed inputs matching actual model signature
    rng = np.random.default_rng(42)
    inputs = {}
    for nm in in_names:
        if "mask" in nm.lower():
            inputs[nm] = np.ones((args.batch, args.seq_len), dtype=np.int64)
        elif "token_type" in nm.lower():
            inputs[nm] = np.zeros((args.batch, args.seq_len), dtype=np.int64)
        else:
            inputs[nm] = rng.integers(1, 1000, size=(args.batch, args.seq_len)).astype(np.int64)

    # Warmup
    for _ in range(args.warmup):
        _ = session.run(None, inputs)

    # Benchmark loop
    latencies_ms = []
    for _ in range(args.runs):
        t0 = time.perf_counter()
        _ = session.run(None, inputs)
        t1 = time.perf_counter()
        latencies_ms.append((t1 - t0) * 1000.0)

    latencies_ms = np.array(latencies_ms)
    mean_lat = float(np.mean(latencies_ms))
    median_lat = float(np.median(latencies_ms))
    p95_lat = float(np.percentile(latencies_ms, 95))
    min_lat = float(np.min(latencies_ms))
    max_lat = float(np.max(latencies_ms))
    std_lat = float(np.std(latencies_ms))
    throughput = (args.batch * 1000.0) / mean_lat if mean_lat > 0 else 0.0

    print("\n" + "=" * 78)
    print("                    [ONNX BENCHMARK RESULTS]")
    print("=" * 78)
    print(f"  - Mean Latency:       {mean_lat:.2f} ms +- {std_lat:.2f} ms")
    print(f"  - Median Latency:     {median_lat:.2f} ms")
    print(f"  - P95 Latency:        {p95_lat:.2f} ms")
    print(f"  - Min / Max Latency:  {min_lat:.2f} ms / {max_lat:.2f} ms")
    print(f"  - Throughput:         {throughput:.1f} inferences/sec ({throughput * 60:.0f} per min)")
    print(f"  - Paper SLA Status:   {'PASSED (<200ms target)' if mean_lat < 200.0 else 'EXCEEDED'}")
    print("=" * 78)

    summary = {
        "model": str(model_path),
        "model_size_mb": round(file_size_mb, 2),
        "providers": session.get_providers(),
        "runs": args.runs,
        "batch_size": args.batch,
        "sequence_length": args.seq_len,
        "mean_ms": round(mean_lat, 2),
        "median_ms": round(median_lat, 2),
        "p95_ms": round(p95_lat, 2),
        "min_ms": round(min_lat, 2),
        "max_ms": round(max_lat, 2),
        "std_ms": round(std_lat, 2),
        "throughput_per_sec": round(throughput, 1)
    }

    if args.export_summary:
        out_json = PROJECT_ROOT / "external" / "edgeshield_onnx_benchmark.json"
        out_json.parent.mkdir(parents=True, exist_ok=True)
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)
        print(f"[+] Summary saved to: {out_json}")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    main()
