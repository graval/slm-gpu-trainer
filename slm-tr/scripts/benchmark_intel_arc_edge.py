"""
EdgeShield: Local Edge Acceleration Benchmark Suite
Hardware Target: Intel Core Ultra 7 255H (16 Cores) + Integrated Intel Arc GPU (DirectML)
Measures:
  1. Inference Latency (Mean, Median, P90, P95, P99, Min, Max, StdDev) across 500 iterations.
  2. Throughput (Inferences per second / FPS).
  3. Memory Footprint (Active Working Set RAM & Commit Charge).
  4. Comparative Acceleration: DirectML (Intel Arc GPU) vs. Multithreaded CPU Execution.
  5. Both Stream A (LSA INT8) and Stream B (BPD INT8).
"""

import os
import sys
import time
import json
import argparse
from pathlib import Path
import numpy as np
import psutil

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import onnxruntime as ort

def benchmark_session(session, dummy_inputs, runs=500, warmup=25):
    # Warmup
    for _ in range(warmup):
        session.run(None, dummy_inputs)
        
    latencies = []
    process = psutil.Process()
    ram_before_mb = process.memory_info().rss / (1024 ** 2)
    
    t0_total = time.perf_counter()
    for _ in range(runs):
        t0 = time.perf_counter()
        session.run(None, dummy_inputs)
        t1 = time.perf_counter()
        latencies.append((t1 - t0) * 1000.0)
    total_time_sec = time.perf_counter() - t0_total
    
    ram_after_mb = process.memory_info().rss / (1024 ** 2)
    
    arr = np.array(latencies)
    return {
        "runs": runs,
        "mean_ms": round(float(np.mean(arr)), 2),
        "std_ms": round(float(np.std(arr)), 2),
        "median_p50_ms": round(float(np.median(arr)), 2),
        "p90_ms": round(float(np.percentile(arr, 90)), 2),
        "p95_ms": round(float(np.percentile(arr, 95)), 2),
        "p99_ms": round(float(np.percentile(arr, 99)), 2),
        "min_ms": round(float(np.min(arr)), 2),
        "max_ms": round(float(np.max(arr)), 2),
        "throughput_fps": round(float(runs / total_time_sec), 1),
        "inferences_per_minute": round(float((runs / total_time_sec) * 60), 0),
        "working_set_ram_mb": round(float(ram_after_mb), 2)
    }

def main():
    parser = argparse.ArgumentParser(description="EdgeShield Intel Arc Edge Hardware Benchmark")
    parser.add_argument("--runs", type=int, default=500, help="Number of benchmark iterations")
    parser.add_argument("--export_json", type=str, default="slm-tr/external/intel_arc_edge_benchmark.json")
    args = parser.parse_args()

    print("=" * 85)
    print("      [+] EDGESHIELD: LOCAL INTEL ARC GPU & CPU EDGE ACCELERATION BENCHMARK      ")
    print("=" * 85)
    
    cpu_info = f"Intel Core Ultra 7 255H ({os.cpu_count()} logical cores)"
    gpu_info = "Integrated Intel Arc GPU (DirectX 12 / DirectML)"
    print(f"  • Host CPU:     {cpu_info}")
    print(f"  • Edge GPU:     {gpu_info}")
    print(f"  • Total RAM:    {psutil.virtual_memory().total / (1024**3):.2f} GB")
    print(f"  • Iterations:   {args.runs} per configuration (Warmup: 25)")
    print("=" * 85)

    base_dir = Path(__file__).resolve().parent.parent
    lsa_model_path = base_dir / "models" / "onnx_edgeshield" / "edgeshield_lsa_int8.onnx"
    bpd_model_path = base_dir / "models" / "onnx_edgeshield" / "edgeshield_bpd_int8.onnx"

    if not lsa_model_path.exists() or not bpd_model_path.exists():
        print(f"[!] Model files not found in {base_dir / 'models' / 'onnx_edgeshield'}")
        sys.exit(1)

    batch_size = 1
    seq_len = 128
    dummy_input_ids = np.ones((batch_size, seq_len), dtype=np.int64)
    dummy_attention_mask = np.ones((batch_size, seq_len), dtype=np.int64)

    results = {
        "hardware": {
            "cpu": cpu_info,
            "gpu": gpu_info,
            "system_ram_gb": round(psutil.virtual_memory().total / (1024**3), 2),
            "os": sys.platform
        },
        "configurations": {}
    }

    models_to_test = [
        ("Stream A: LSA (Lateral Movement INT8)", str(lsa_model_path)),
        ("Stream B: BPD (Ransomware INT8)", str(bpd_model_path))
    ]

    for model_name, path in models_to_test:
        print(f"\n[*] Benchmarking {model_name}...")
        file_size_mb = os.path.getsize(path) / (1024 ** 2)
        print(f"    ONNX Model File Size: {file_size_mb:.2f} MB")

        # 1. DirectML (Intel Arc GPU)
        sess_opt_dml = ort.SessionOptions()
        sess_opt_dml.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        sess_dml = ort.InferenceSession(path, sess_opt_dml, providers=["DmlExecutionProvider", "CPUExecutionProvider"])
        
        # Prepare inputs according to model inputs
        input_names = [inp.name for inp in sess_dml.get_inputs()]
        feed = {"input_ids": dummy_input_ids, "attention_mask": dummy_attention_mask}
        if "token_type_ids" in input_names:
            feed["token_type_ids"] = np.zeros((batch_size, seq_len), dtype=np.int64)
            
        print("    -> Running on Intel Arc GPU via DirectML...")
        metrics_dml = benchmark_session(sess_dml, feed, runs=args.runs)
        print(f"       Mean: {metrics_dml['mean_ms']} ms | P50: {metrics_dml['median_p50_ms']} ms | P95: {metrics_dml['p95_ms']} ms | Throughput: {metrics_dml['throughput_fps']} FPS")

        # 2. CPU Execution Provider (Core Ultra 7 255H)
        sess_opt_cpu = ort.SessionOptions()
        sess_opt_cpu.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        sess_opt_cpu.intra_op_num_threads = os.cpu_count() or 16
        sess_cpu = ort.InferenceSession(path, sess_opt_cpu, providers=["CPUExecutionProvider"])
        
        print("    -> Running on Intel Core Ultra 7 255H (CPU)...")
        metrics_cpu = benchmark_session(sess_cpu, feed, runs=args.runs)
        print(f"       Mean: {metrics_cpu['mean_ms']} ms | P50: {metrics_cpu['median_p50_ms']} ms | P95: {metrics_cpu['p95_ms']} ms | Throughput: {metrics_cpu['throughput_fps']} FPS")

        speedup = round(metrics_cpu["mean_ms"] / max(0.001, metrics_dml["mean_ms"]), 2)
        p95_stability = round(metrics_cpu["p95_ms"] / max(0.001, metrics_dml["p95_ms"]), 2)

        results["configurations"][model_name] = {
            "model_size_mb": round(file_size_mb, 2),
            "intel_arc_directml": metrics_dml,
            "intel_core_ultra_cpu": metrics_cpu,
            "acceleration_speedup_ratio": speedup,
            "p95_latency_stability_ratio": p95_stability
        }

    # Print Final Summary Table
    print("\n" + "=" * 95)
    print("                     [INTEL ARC GPU vs CPU EDGE ACCELERATION SUMMARY]")
    print("=" * 95)
    print(f"{'Stream / Model':<35} | {'DirectML (Arc)':<16} | {'CPU (Ultra 7)':<16} | {'Arc P95':<10} | {'Speedup':<8}")
    print("-" * 95)
    for name, data in results["configurations"].items():
        dml_str = f"{data['intel_arc_directml']['mean_ms']:.2f} ms ({data['intel_arc_directml']['throughput_fps']} fps)"
        cpu_str = f"{data['intel_core_ultra_cpu']['mean_ms']:.2f} ms ({data['intel_core_ultra_cpu']['throughput_fps']} fps)"
        p95_str = f"{data['intel_arc_directml']['p95_ms']:.2f} ms"
        speed_str = f"{data['acceleration_speedup_ratio']}x"
        print(f"{name:<35} | {dml_str:<16} | {cpu_str:<16} | {p95_str:<10} | {speed_str:<8}")
    print("=" * 95)

    # Save to JSON
    export_path = Path(args.export_json)
    if not export_path.is_absolute():
        export_path = base_dir / "external" / "intel_arc_edge_benchmark.json"
    export_path.parent.mkdir(parents=True, exist_ok=True)
    with open(export_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\n[+] Comprehensive hardware benchmark exported to: {export_path}")

if __name__ == "__main__":
    main()
