# Specification: Developer Workflow, Python Environment & CLI Guide

## 1. Python Environment & Execution Rules

> [!IMPORTANT]
> Always execute commands using the virtual environment Python interpreter:
> **Windows**: `.venv\Scripts\python.exe <script>`  
> **Linux / Docker**: `python <script>`

The `.venv` environment contains all required packages (`torch`, `torch-directml`, `transformers`, `datasets`, `trl`, `peft`, `optimum-quanto`, `streamlit`, `altair`, `colorama`).

---

## 2. Common CLI Commands & Operations

### A. Side-by-Side Architectural Benchmark Comparison
```bash
# Compare v1 vs v2 on OpTC out-of-distribution benchmark (50 samples)
.venv\Scripts\python.exe scripts/compare_v1_v2.py --csv_path optc_test_benchmark.csv --num_samples 50

# Comprehensive 1000-sample comparison on LMD-2023
.venv\Scripts\python.exe scripts/compare_v1_v2.py --csv_path data/lmd_2023_dataset.csv --num_samples 1000
```

### B. Interactive Threat Hunter CLI
```bash
# Phase 1: Single-event CLI triage
.venv\Scripts\python.exe detect.py --variant v1 --cmd "psexec.exe \\CORP-DC01 cmd.exe"

# Phase 2: Sliding-window SOC stream simulation
.venv\Scripts\python.exe detect.py --variant v2 --simulate

# Phase 2: Interactive multi-event shell
.venv\Scripts\python.exe detect.py --variant v2 --interactive
```

### C. Training Models
```bash
# Phase 1: Train v1 Single Entry classifier
.venv\Scripts\python.exe v1_single_entry/train_classifier.py --epochs 3 --batch_size 16

# Phase 2: Train v2 Sliding Window classifier
.venv\Scripts\python.exe v2_sliding_window/train_classifier.py --window_size 3 --epochs 3 --batch_size 16

# Unified Root Trainer (automatically appends variant suffix)
.venv\Scripts\python.exe train_classifier.py --variant v2 --epochs 3
```

### D. Streamlit SOC EDR UI
```bash
.venv\Scripts\python.exe -m streamlit run app.py
```

### E. Docker Execution
```bash
# Launch unified container with GPU acceleration
cd deployment/
docker compose up slm-trainer
```
