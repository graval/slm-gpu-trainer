"""
Hardware Performance Profiler & Benchmark:
Compares Intel Core Ultra 7 (16-Core CPU) vs Intel Arc 140T GPU (16GB via DirectML)
Measures forward, backward, optimizer step times, samples/sec throughput, and estimates training time.
"""

import os
import sys
import time
import json
import torch
import torch.nn as nn
from transformers import AutoModelForSequenceClassification, AutoTokenizer

def profile_device(device_type="cpu", num_steps=30, batch_size=32, seq_len=128):
    cpu_cores = os.cpu_count() or 16
    torch.set_num_threads(cpu_cores)
    os.environ["OMP_NUM_THREADS"] = str(cpu_cores)
    os.environ["MKL_NUM_THREADS"] = str(cpu_cores)
    
    if device_type == "cpu":
        dev = torch.device("cpu")
        dev_name = f"Intel Core Ultra 7 255H ({cpu_cores} Cores)"
    elif device_type == "dml":
        import torch_directml
        dev = torch_directml.device(0)
        dml_name = torch_directml.device_name(0).strip()
        dev_name = f"Intel Arc 140T GPU (DirectML, 16GB VRAM)"
    else:
        raise ValueError(f"Unknown device: {device_type}")
        
    print(f"\n[*] Profiling: {dev_name} | Batch: {batch_size} | Seq Len: {seq_len}...")
    
    # Initialize model
    model = AutoModelForSequenceClassification.from_pretrained("distilbert-base-uncased", num_labels=16).to(dev)
    optimizer = torch.optim.AdamW(model.parameters(), lr=5e-5)
    model.train()
    
    # Dummy tensors
    x = torch.randint(0, 1000, (batch_size, seq_len)).to(dev)
    mask = torch.ones((batch_size, seq_len)).to(dev)
    labels = torch.randint(0, 16, (batch_size,)).to(dev)
    
    # Warmup
    print("  -> Warmup (3 steps)...", flush=True)
    for _ in range(3):
        optimizer.zero_grad()
        out = model(input_ids=x, attention_mask=mask, labels=labels)
        loss = out.loss
        loss.backward()
        optimizer.step()
        
    # Timed benchmark loop
    print(f"  -> Running {num_steps} benchmark iterations...", flush=True)
    fwd_times, bwd_times, step_times = [], [], []
    
    start_total = time.perf_counter()
    for _ in range(num_steps):
        t0 = time.perf_counter()
        optimizer.zero_grad()
        out = model(input_ids=x, attention_mask=mask, labels=labels)
        loss = out.loss
        t1 = time.perf_counter()
        
        loss.backward()
        t2 = time.perf_counter()
        
        optimizer.step()
        t3 = time.perf_counter()
        
        fwd_times.append(t1 - t0)
        bwd_times.append(t2 - t1)
        step_times.append(t3 - t0)
        
    total_dur = time.perf_counter() - start_total
    avg_step_ms = (sum(step_times) / len(step_times)) * 1000.0
    avg_fwd_ms = (sum(fwd_times) / len(fwd_times)) * 1000.0
    avg_bwd_ms = (sum(bwd_times) / len(bwd_times)) * 1000.0
    samples_per_sec = (batch_size * num_steps) / total_dur
    
    return {
        "device_name": dev_name,
        "batch_size": batch_size,
        "seq_len": seq_len,
        "avg_step_ms": round(avg_step_ms, 2),
        "avg_fwd_ms": round(avg_fwd_ms, 2),
        "avg_bwd_ms": round(avg_bwd_ms, 2),
        "samples_per_sec": round(samples_per_sec, 2),
        "total_dur_sec": round(total_dur, 2)
    }

def main():
    print("=" * 80)
    print("       [+] HARDWARE TRAINING BENCHMARK: CPU vs INTEL ARC GPU (DIRECTML)      ")
    print("=" * 80)
    
    results = {}
    
    # 1. Benchmark CPU
    cpu_res = profile_device(device_type="cpu", num_steps=25, batch_size=32, seq_len=128)
    results["cpu"] = cpu_res
    
    # 2. Benchmark GPU (DirectML)
    try:
        gpu_res = profile_device(device_type="dml", num_steps=25, batch_size=32, seq_len=128)
        results["gpu_dml"] = gpu_res
    except Exception as e:
        results["gpu_dml"] = {"error": str(e)}
        
    print("\n" + "=" * 80)
    print("                       EMPIRICAL BENCHMARK RESULTS SUMMARY                   ")
    print("=" * 80)
    print(json.dumps(results, indent=2))
    
    # Projections for 3 epochs training under 45 minutes
    epochs = 3
    print("\n" + "=" * 80)
    print("      [*] PROJECTED TRAINING DURATION (3 EPOCHS) ACROSS DATASET SIZES       ")
    print("=" * 80)
    print(f"{'Dataset Size':<15} | {'Total Epoch Items':<18} | {'CPU Time (min)':<16} | {'GPU Time (min)':<16}")
    print("-" * 75)
    
    for n in [2000, 5000, 10000, 20000, 35000, 50000]:
        total_items = n * epochs
        cpu_sec = total_items / results["cpu"]["samples_per_sec"]
        cpu_min = cpu_sec / 60.0
        
        if "samples_per_sec" in results.get("gpu_dml", {}):
            gpu_sec = total_items / results["gpu_dml"]["samples_per_sec"]
            gpu_min = gpu_sec / 60.0
            gpu_str = f"{gpu_min:.2f} min" + (" [OK: <45m]" if gpu_min <= 45.0 else "")
        else:
            gpu_str = "N/A"
            
        cpu_str = f"{cpu_min:.2f} min" + (" [OK: <45m]" if cpu_min <= 45.0 else "")
        print(f"{n:<15} | {total_items:<18} | {cpu_str:<16} | {gpu_str:<16}")

if __name__ == "__main__":
    main()
