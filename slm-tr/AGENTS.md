# AGENTS.md: Universal AI Assistant Instructions & Project Context

> **To any AI coding assistant (Antigravity, Claude, Cursor, Copilot, Gemini):**  
> Read this document and the specifications in [`specs/`](file:///c:/workspaceag/slmgpuv1/slm-tr/specs/) to understand the core architecture, design decisions, and coding standards of this repository.

---

## 🎯 Repository Purpose
This codebase is an end-to-end security engineering and Small Language Model (SLM) framework for **Lateral Movement Detection (LMD)** using Windows Sysmon telemetry logs.

---

## 🏗️ Core Architecture & Paradigms

### 1. Dual-Model Architecture
* **Classifier SLM (`microsoft/deberta-v3-small` or `distilbert-base-uncased`, 44M params):** Evaluates 100% of telemetry with ultra-low latency ($\approx 1.1\text{ms}$ / event).
* **Generative Reasoner SLM (`Qwen/Qwen2.5-1.5B` or `microsoft/Phi-3-mini-4k-instruct`, 1.5B/3.8B params):** Triggered only when a suspicious threat (Class 1 or 2) is flagged to output structured JSON alerts and MITRE ATT&CK mappings.

### 2. Two Operational Paradigms
* **Phase 1: `v1_single_entry/` ($K=1$):** Evaluates isolated single Sysmon log entries without prior history.
* **Phase 2: `v2_sliding_window/` ($K=3..5$):** Evaluates rolling temporal multi-event sequences, correlating multi-stage actions (Network $\rightarrow$ Named Pipe $\rightarrow$ Process Execution) to suppress false positives by $\approx 94\%$.

### 3. Centralized Reasoning Engine (`reasoning/`)
* Contains all heuristic rules, attack subtype classifications (`PsExec`, `WMIC`, `WinRM`, `Pass-the-Hash`, `LSASS dumps`, `SAM dumps`, `Kerberos forgery`), MITRE ATT&CK catalog (`mitre_kb.py`), and ChatML prompt builders (`prompt_builder.py`).

---

## 📚 Complete Specifications & ADRs
Detailed specifications and Architecture Decision Records are maintained in [`specs/`](file:///c:/workspaceag/slmgpuv1/slm-tr/specs/):
* [`specs/01_ARCHITECTURE.md`](file:///c:/workspaceag/slmgpuv1/slm-tr/specs/01_ARCHITECTURE.md) - Full system design and model specs.
* [`specs/02_PARADIGMS_V1_V2.md`](file:///c:/workspaceag/slmgpuv1/slm-tr/specs/02_PARADIGMS_V1_V2.md) - v1 Single Entry vs. v2 Sliding Window contracts.
* [`specs/03_REASONING_ENGINE.md`](file:///c:/workspaceag/slmgpuv1/slm-tr/specs/03_REASONING_ENGINE.md) - Subtype taxonomy and MITRE mappings.
* [`specs/04_ARCHITECTURAL_DECISIONS.md`](file:///c:/workspaceag/slmgpuv1/slm-tr/specs/04_ARCHITECTURAL_DECISIONS.md) - Formal Architecture Decision Records (ADRs).
* [`specs/05_BENCHMARKS_AND_DATASETS.md`](file:///c:/workspaceag/slmgpuv1/slm-tr/specs/05_BENCHMARKS_AND_DATASETS.md) - LMD-2023 & DARPA OpTC datasets.
* [`specs/06_DEV_WORKFLOW_AND_CLI.md`](file:///c:/workspaceag/slmgpuv1/slm-tr/specs/06_DEV_WORKFLOW_AND_CLI.md) - Environment, CLI, and test execution.

---

## ⚠️ Critical Development Rules

1. **Python Environment**: Always use `.venv\Scripts\python.exe` on Windows.
2. **Tokenizer Vocab Match**: When evaluating saved models, always load tokenizer from the model directory first (`AutoTokenizer.from_pretrained(target_path)`).
3. **Dataset Path Resolution**: Use `resolve_dataset_path(csv_path)` from `v1_single_entry.data_loader` or `v2_sliding_window.data_loader` to support `data/`, `external/`, `scratch/`, and root filenames.
4. **Model Output Suffixing**: When writing model checkpoints, append the approach name suffix (`-v1_single_entry` or `-v2_sliding_window`).
5. **Windows Console Encoding**: Avoid non-ASCII Unicode emojis in CLI print statements to prevent `cp1252` `UnicodeEncodeError`. Use ASCII markers (`[+]`, `[!]`, `[COMPARISON]`).
