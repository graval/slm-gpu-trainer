# CLAUDE.md: Instructions for Claude Code & Anthropic Agents

## Project Overview
Lateral Movement Detection (LMD) using Small Language Models (SLMs) trained on Sysmon telemetry.
Dual-model architecture:
1. **Classifier SLM** (`deberta-v3-small` / `distilbert`, 44M) for ultra-fast filtering ($\approx 1.1\text{ms}$).
2. **Generative Reasoner SLM** (`Qwen2.5-1.5B` / `Phi-3-mini-3.8B`) for XAI explainability and MITRE ATT&CK mapping.

---

## Architectural Paradigms
* **Phase 1: `v1_single_entry/`**: Isolated single Sysmon event log detection ($K=1$).
* **Phase 2: `v2_sliding_window/`**: Temporal multi-event sliding window ($K=3..5$) for reducing False Positives.
* **Common: `reasoning/`**: Central reasoning engine, attack subtype taxonomy, and MITRE ATT&CK mappings.

---

## Common Commands
```bash
# Python Environment
.venv\Scripts\python.exe <script>

# Compare v1 vs v2 Side-by-Side
.venv\Scripts\python.exe scripts/compare_v1_v2.py --csv_path optc_test_benchmark.csv --num_samples 50

# Run Evaluation
.venv\Scripts\python.exe eval.py --variant v1 --csv_path data/optc_test_benchmark.csv
.venv\Scripts\python.exe eval.py --variant v2 --csv_path data/optc_test_benchmark.csv

# Threat Hunter CLI
.venv\Scripts\python.exe detect.py --variant v1 --cmd "psexec.exe \\CORP-DC01 cmd.exe"
.venv\Scripts\python.exe detect.py --variant v2 --simulate

# Streamlit UI
.venv\Scripts\python.exe -m streamlit run app.py
```

---

## Key References & Specs
See [`specs/`](file:///c:/workspaceag/slmgpuv1/slm-tr/specs/) for complete technical specifications and ADRs.
