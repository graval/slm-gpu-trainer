# Phase 2: v2 - Sliding Window Lateral Movement Detection

## Overview
**v2 - Sliding Window** is the temporal context-aware architectural variant. Rather than evaluating log events in isolation, v2 aggregates a sequence of $K$ consecutive Sysmon logs (typically $K=3$ to $5$) using a stateful ring buffer:
```
[Event T-2] Network: 192.168.10.50 -> 192.168.10.12:445 (SMB)
---
[Event T-1] Pipe Name: \psexec
---
[Target Event T_0] Image: C:\Windows\PSEXESVC.exe | User: NT AUTHORITY\SYSTEM
```

---

## Key Characteristics
- **Context Size ($K$)**: 3 to 5 chronological events per sample.
- **Inference Latency**: ~12-25 ms on CPU / DirectML.
- **Strengths**: Drastically reduces False Positives by correlating multi-stage attack actions (Network connection -> Named pipe -> Remote execution).
- **Limitations**: Requires stateful event stream ingestion buffers; slight increase in prompt token length (256-512 tokens).

---

## Directory Structure
```
v2_sliding_window/
├── __init__.py
├── data_loader.py       # Sliding window multi-event sequence builder & splitters
├── train_classifier.py  # DeBERTa sequence classifier trainer on temporal sequences
├── train_generator.py   # Phi-3 / Qwen LoRA instruction reasoner trainer on sequences
├── detect.py            # Real-time stateful ring buffer SOC stream monitor
├── eval.py              # Temporal sliding window evaluation harness
└── README.md            # Documentation
```

---

## Quick Usage

### 1. Evaluate Model on Sliding Window Sequences
```bash
python v2_sliding_window/eval.py --csv_path data/lmd_2023_dataset.csv --window_size 3
```

### 2. Run Real-Time SOC Stream Simulator
```bash
python v2_sliding_window/detect.py
```

### 3. Train Classifier on Temporal Sequences
```bash
python v2_sliding_window/train_classifier.py --window_size 3 --epochs 3 --batch_size 16 --output_dir models/deberta-lateral-movement-v2
```
