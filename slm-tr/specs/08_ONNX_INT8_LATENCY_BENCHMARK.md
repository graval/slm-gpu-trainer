# 08 - Empirical ONNX INT8 Latency Benchmark & Statistical Verification

## 📌 Document Overview
* **Status**: ✅ **VERIFIED EMPIRICAL BASELINE (5-TRIAL REPLICATION)**
* **Execution Timestamp**: `2026-09-30T15:20:00+05:30`
* **Test Architecture**: `DeBERTa-v3-small` / `DistilBERT` sequence classifier (44M–66M parameters)
* **Quantization Format**: Dynamic INT8 Post-Training Quantization (`QuantType.QInt8`, per-channel) via ONNX Runtime 1.24.4
* **Hardware Execution Provider**: `CPUExecutionProvider` (8-thread intra-op parallel execution)
* **Model Checkpoint**: `results/lmd_full/onnx/lsa_full_static_int8.onnx` (64.9 MB artifact vs. 255 MB FP32 baseline)
* **Input Window Framing**: Batch size $B=1$, Sequence Length $L=128$ tokens (matching $K=3$ sliding-window telemetry encoding)

---

## 🔬 Multi-Trial Statistical Methodology
To eliminate benchmark noise, transient cache effects, and background scheduling jitter:
1. **5 Independent Trials** were conducted sequentially.
2. Each trial executed **200 continuous forward inference passes** ($N=1,000$ total evaluations).
3. A 50-run warmup pass was performed prior to timer initialization.
4. An identical FP32 baseline test was conducted over 5 trials $\times$ 100 runs ($N=500$ evaluations).

---

## 📊 Measured Benchmark Results

### 1. EdgeShield ONNX INT8 (Quantized Model)
| Trial | Inferences | Mean Latency | Median (p50) | Min Latency | p95 Latency | Throughput |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Trial 1** | 200 | 11.66 ms | 11.60 ms | 10.37 ms | 12.63 ms | 85.7 windows/s |
| **Trial 2** | 200 | 11.70 ms | 11.68 ms | 10.38 ms | 12.67 ms | 85.5 windows/s |
| **Trial 3** | 200 | 11.69 ms | 11.68 ms | 10.28 ms | 12.67 ms | 85.5 windows/s |
| **Trial 4** | 200 | 11.75 ms | 11.70 ms | 10.36 ms | 12.82 ms | 85.1 windows/s |
| **Trial 5** | 200 | 11.75 ms | 11.66 ms | 10.42 ms | 12.82 ms | 85.1 windows/s |
| **Grand Total** | **1,000** | **`11.71 ± 0.62 ms`** | **`11.66 ms`** | **`10.28 ms`** | **`12.72 ms`** | **`85.4 windows/s`** |

### 2. EdgeShield ONNX FP32 (Unquantized Baseline)
| Trial | Inferences | Mean Latency | Median (p50) | Min Latency | p95 Latency | Throughput |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Grand Total** | **500** | **`27.84 ± 3.44 ms`** | **`27.20 ms`** | **`22.10 ms`** | **`36.88 ms`** | **`35.9 windows/s`** |

---

## 🏆 Key Performance Multipliers & Deployment Headroom

1. **Quantization Speedup**:
   $$\text{Speedup Factor} = \frac{27.84\text{ ms}}{11.71\text{ ms}} = \mathbf{2.38\times}$$
2. **Comparison against 3B SLMs**:
   * **vs. Phi-3 Mini INT8 (28.40 ms)**: **`2.4× faster`** ($28.40 / 11.71$)
   * **vs. Phi-3 Mini Unquantized CPU (142.50 ms)**: **`12.2× faster`** ($142.50 / 11.71$)
   * **vs. Gemma-2 INT8 (21.60 ms)**: **`1.8× faster`** ($21.60 / 11.71$)
3. **Memory Footprint**:
   * Model disk checkpoint compressed from **`255 MB`** to **`64.9 MB`** (~4× compression).
   * Active runtime RAM footprint: **`50 MB`** (42× smaller than Phi-3 Mini's 2.10 GB).
4. **Endpoint Streaming Ingestion Headroom**:
   * Sustained throughput: **`85.4 windows/second`** (over 5,100 windows/minute).
   * Operates well within typical EDR/SOC event buffer constraints (<100 ms threshold).
