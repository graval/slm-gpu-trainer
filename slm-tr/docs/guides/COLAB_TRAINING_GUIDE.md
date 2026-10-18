# 🛡️ EdgeShield: Google Colab Training & Retraining Guide

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/graval/slm-gpu-trainer/blob/feat/edgeshield-slm-framework/EdgeShield_Colab_Training.ipynb)

This guide provides instructions for training and evaluating the **EdgeShield Small Language Model (SLM)** framework on [Google Colab](https://colab.research.google.com/) using NVIDIA GPU acceleration (Tesla T4, A100, or V100).

---

## 🚀 Quick Start: 3 Ways to Open in Colab

### Option 1: Direct GitHub Open (Fastest)
1. Open Google Colab: [https://colab.research.google.com/](https://colab.research.google.com/)
2. Click **File** ➔ **Open notebook** ➔ Select the **GitHub** tab.
3. Enter repository URL: `https://github.com/graval/slm-gpu-trainer`
4. Select Branch: `feat/edgeshield-slm-framework`
5. Click on `EdgeShield_Colab_Training.ipynb`.

### Option 2: Upload Pre-Built Notebook
1. In Google Colab, click **File** ➔ **Upload notebook**.
2. Select [`EdgeShield_Colab_Training.ipynb`](../../EdgeShield_Colab_Training.ipynb) from your local repository folder (`c:\workspaceag\slmgpuv1\EdgeShield_Colab_Training.ipynb`).

### Option 3: Manual Execution in Any New Colab Notebook
Create a new notebook in Colab and execute the cells sequentially as outlined below.

---

## ⚡ Step-by-Step Training Workflow

### 1. Enable Hardware Acceleration (NVIDIA CUDA GPU)
In Google Colab:
- Navigate to: **Runtime** ➔ **Change runtime type**
- Hardware accelerator: **T4 GPU** (free tier) or **A100 GPU** (Colab Pro)
- Click **Save**

Verify GPU allocation:
```python
!nvidia-smi
import torch
print(f"CUDA Available: {torch.cuda.is_available()}")
print(f"GPU Device: {torch.cuda.get_device_name(0)}")
```

---

### 2. Clone the Repository & Navigate to Working Directory
```python
import os
!git clone -b feat/edgeshield-slm-framework https://github.com/graval/slm-gpu-trainer.git
os.chdir("/content/slm-gpu-trainer/slm-tr")
!pwd
```

---

### 3. Install Dependencies
```python
!pip install -q --upgrade pip
!pip install -q transformers>=4.38.0 datasets>=2.14.0 accelerate>=0.28.0 peft>=0.9.0 trl>=0.8.0
!pip install -q scikit-learn pandas numpy onnx onnxruntime bitsandbytes optimum-quanto
!pip install -q sentencepiece tiktoken safetensors altair colorama
```

---

### 4. Setup Telemetry & Datasets
EdgeShield operates on two decoupled telemetry streams:
- **Stream A (LSA)**: Authentication telemetry (`data/lmd_2023_dataset.csv`).
- **Stream B (BPD)**: Ransomware behavioral traces (`data/ransomware_behavioral_traces.csv`).

#### Instant Setup (Zero-Upload Quickstart):
```python
# 1. Generate Curated Ransomware Behavioral Traces for BPD
from edgeshield.data.synthetic_ransomware import generate_curated_ransomware_dataset
generate_curated_ransomware_dataset("data/ransomware_behavioral_traces.csv", num_samples=12000)

# 2. Generate DARPA OpTC Out-of-Distribution Benchmark
from scripts.prepare_optc_benchmark import generate_optc_test_benchmark
generate_optc_test_benchmark("data/optc_test_benchmark.csv", total_samples=1500)

# 3. Compile authentic security telemetry fallback from OTRF Mordor
from scripts.setup_dataset import generate_fallback_dataset
generate_fallback_dataset()
```

#### Loading the Full 1.75M Records LMD-2023 Dataset:
You can provide the 1.07 GB dataset using either method:

**Method 1 (Fastest): From your Personal Google Drive**
If you uploaded `lmd_2023_dataset.csv` to your Google Drive:
```python
from google.colab import drive
drive.mount('/content/drive')
!cp /content/drive/MyDrive/lmd_2023_dataset.csv data/lmd_2023_dataset.csv
```

**Method 2: Direct Download via `gdown` from Author's Public Drive Link**
Downloads directly from the published author folder (`1PkJiGpD0Kn1rV8GC9m2b_eWvqQTSa1eH`):
```bash
!pip install -q gdown
!gdown --folder "https://drive.google.com/drive/folders/1PkJiGpD0Kn1rV8GC9m2b_eWvqQTSa1eH?usp=sharing" -O data/
!mv data/LMD-2023-labeled.csv data/lmd_2023_dataset.csv 2>/dev/null || true
```

---

### 5. Training Executions

#### A. Train Stream A: Log Semantic Analyzer (LSA)
Trains DeBERTa-v3-small with Joint Supervised Contrastive Loss & Cross-Entropy:
```bash
!python scripts/train_edgeshield_lsa.py \
    --model_name "microsoft/deberta-v3-small" \
    --dataset_path "data/lmd_2023_dataset.csv" \
    --device "cuda" \
    --epochs 3 \
    --batch_size 16 \
    --lr 5e-5 \
    --use_contrastive \
    --output_dir "models/edgeshield_lsa_deberta"
```

#### B. Train Stream B: Behavioral Pattern Detector (BPD)
Trains DistilBERT sequence classifier and Attention Threat Scoring Head:
```bash
!python scripts/train_edgeshield_bpd.py \
    --model_name "distilbert-base-uncased" \
    --dataset_path "data/ransomware_behavioral_traces.csv" \
    --device "cuda" \
    --epochs 3 \
    --batch_size 16 \
    --threat_weight 0.5 \
    --output_dir "models/edgeshield_bpd"
```

#### C. Train Sequence Classifier (v2 Sliding Window, K=3)
Trains temporal sliding window sequence classifier with Hugging Face Trainer:
```bash
!python train_classifier.py \
    --variant v2 \
    --window_size 3 \
    --device cuda \
    --epochs 3 \
    --batch_size 16 \
    --model_name "microsoft/deberta-v3-small" \
    --csv_path "data/lmd_2023_dataset.csv" \
    --output_dir "models/deberta-lateral-movement-v2_sliding_window"
```

#### D. Train Tier 2 Generative Reasoner (LoRA / QLoRA)
Fine-tunes Qwen2.5-1.5B-Instruct to generate causal incident reports:
```bash
$env:PYTHONUTF8="1" # or in bash: export PYTHONUTF8=1
!python train_generator.py \
    --model_name "Qwen/Qwen2.5-1.5B-Instruct" \
    --variant v2 \
    --window_size 3 \
    --csv_path "data/lmd_2023_dataset.csv" \
    --epochs 1 \
    --batch_size 2 \
    --gradient_accumulation_steps 4 \
    --learning_rate 2e-4 \
    --qlora \
    --output_dir "models/qwen-lateral-movement-v2_sliding_window"
```

---

### 6. ONNX Dynamic INT8 Quantization & Latency Benchmark
```bash
# Export trained model to ONNX & quantize to INT8
!python scripts/export_onnx.py \
    --checkpoint "models/edgeshield_lsa_deberta" \
    --out-dir "models/onnx_edgeshield" \
    --name "edgeshield_lsa" \
    --quantize

# Benchmark edge runtime latency across 500 evaluations
!python scripts/benchmark_onnx.py \
    --model "models/onnx_edgeshield/edgeshield_lsa_int8.onnx" \
    --runs 500 \
    --export_summary
```

---

### 7. Statistical Evaluation & Comparison Against Baselines
```bash
!python scripts/benchmark_edgeshield.py --samples 500 --export_summary
```

---

### 8. Persist Checkpoints to Google Drive
Ensure your trained models and artifacts are saved permanently:
```python
from google.colab import drive
import os

drive.mount('/content/drive')
SAVE_DIR = "/content/drive/MyDrive/EdgeShield_Colab_Artifacts"
os.makedirs(SAVE_DIR, exist_ok=True)

!cp -r models/* "{SAVE_DIR}/"
!cp -r external/*.json "{SAVE_DIR}/" 2>/dev/null || true
print(f"[+] All artifacts preserved at: {SAVE_DIR}")
```
