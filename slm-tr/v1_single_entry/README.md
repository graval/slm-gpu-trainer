# Phase 1: v1 - Single Entry Lateral Movement Detection

## Overview
**v1 - Single Entry** represents the baseline architectural variant where each Windows Sysmon log event is analyzed in **isolation** ($K=1$). The model receives an individual process creation, network connection, or registry event and determines whether it exhibits indicators of Lateral Movement (EoRS) or Credential Access / Pass-the-Hash (EoHT).

---

## Key Characteristics
- **Context Size ($K$)**: 1 event per inference sample.
- **Inference Latency**: Fast (~5-12 ms on CPU / DirectML).
- **Strengths**: Ultra-low memory overhead, instant single-line triage, ideal for stateless log processing pipelines.
- **Limitations**: Higher false positives when an isolated benign event (e.g. `sc.exe query`) lacks preceding context, or missed multi-stage attacks where a lateral command is only suspicious following an SMB network share connection.

---

## Directory Structure
```
v1_single_entry/
├── __init__.py
├── data_loader.py       # Single-event log formatter & balanced dataset splitters
├── train_classifier.py  # DeBERTa / DistilBERT sequence classifier trainer
├── train_generator.py   # Phi-3 / Qwen LoRA instruction reasoner trainer
├── detect.py            # CLI single-event triage tool
├── eval.py              # Single-event evaluation harness
└── README.md            # Documentation
```

---

## Quick Usage

### 1. Evaluate Model on Single Entries
```bash
python v1_single_entry/eval.py --csv_path data/lmd_2023_dataset.csv --model_path models/deberta-lateral-movement
```

### 2. Run CLI Single Log Triage
```bash
python v1_single_entry/detect.py
```

### 3. Train Classifier on Single Event Logs
```bash
python v1_single_entry/train_classifier.py --epochs 3 --batch_size 16 --output_dir models/deberta-lateral-movement-v1
```
