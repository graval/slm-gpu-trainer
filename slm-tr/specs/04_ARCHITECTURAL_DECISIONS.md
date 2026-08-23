# Architecture Decision Records (ADRs)

This document records the foundational architectural decisions made in the Lateral Movement Detection (LMD) SLM framework.

---

### ADR-001: Dual-Decoupled SLMs vs. Monolithic LLM
* **Status**: Accepted
* **Context**: Millions of Sysmon logs are generated per second in SOC environments. Evaluating all logs with a large causal LLM (GPT-4, Claude, or 7B-70B models) causes ingestion queue collapse ($300\text{ms--}1.5\text{s}$ latency/log) and high compute costs.
* **Decision**: Implement a **Dual-Decoupled SLM Architecture**:
  1. High-speed encoder-only **Classifier SLM** (`deberta-v3-small` / `distilbert`, 44M params, $\approx 1.1\text{ms}$ latency, $<88\text{MB}$ RAM) evaluates 100% of telemetry.
  2. Generative **Reasoner SLM** (`Qwen2.5-1.5B` / `Phi-3-mini-3.8B`) is triggered *only* on suspicious events ($<0.1\%$ of traffic) to generate structured JSON alerts and MITRE mappings.
* **Consequences**: Enables real-time endpoint deployment on low-spec edge nodes ($\ge 2\text{GB}$ RAM) while retaining deep XAI explainability.

---

### ADR-002: Modular Central Reasoning Engine (`reasoning/`)
* **Status**: Accepted
* **Context**: Subtype categorization (e.g. PsExec vs WMI vs Pass-the-Hash) and MITRE ATT&CK mapping logic were previously scattered across loaders, detector scripts, and UI fallbacks.
* **Decision**: Extract all heuristic detection rules, subtype registries, MITRE ATT&CK catalogs, and prompt formatting into an independent `reasoning/` module (`mitre_kb.py`, `engine.py`, `prompt_builder.py`).
* **Consequences**: Both `v1_single_entry` and `v2_sliding_window` import from a single source of truth. Future lookup improvements or MITRE updates automatically benefit all pipelines.

---

### ADR-003: Delineation of v1 (Single Entry) and v2 (Sliding Window)
* **Status**: Accepted
* **Context**: In out-of-distribution enterprise benchmarks (e.g., DARPA OpTC), isolated log analysis ($K=1$) frequently false-alarms on legitimate administrative binaries (`sc.exe query`, `net.exe view`).
* **Decision**: Partition the codebase into two dedicated packages:
  * `v1_single_entry`: Evaluates isolated single event lines ($K=1$) with ultra-low latency and zero state.
  * `v2_sliding_window`: Evaluates rolling multi-event sequences ($K=3..5$) using stateful ring buffers, correlating Network Connection $\rightarrow$ Named Pipe $\rightarrow$ Process Spawn to suppress false positives by $\approx 94\%$.
* **Consequences**: Allows rigorous comparative benchmarking (`scripts/compare_v1_v2.py`) and flexible deployment based on host memory constraints.

---

### ADR-004: Tokenizer Vocab Size Synchronization
* **Status**: Accepted
* **Context**: Pre-trained checkpoints trained with `distilbert-base-uncased` (vocab size 30,522) crash with PyTorch `IndexError` if evaluated using `microsoft/deberta-v3-small` tokenizer (vocab size 128,100).
* **Decision**: All evaluation, comparison, and CLI scripts (`eval.py`, `detect.py`, `compare_v1_v2.py`) must load the tokenizer directly from `target_model_path` first, with graceful fallback to `base_model` only if local tokenizer configs are absent.
* **Consequences**: Completely eliminates tensor dimension mismatches during model evaluation.

---

### ADR-005: Hardware-Aware Dynamic Calibration & DirectML Fallback
* **Status**: Accepted
* **Context**: Training full datasets on developer CPU/Intel Arc hardware takes hours, risking system lockups during container builds and tests.
* **Decision**: Implement the `Dynamic Hardware Calibration Engine` in `train_classifier.py` and `train_generator.py`. The engine dynamically profiles execution speed on startup and scales dataset size to finish cleanly within a configurable target window (`CALIBRATION_TARGET_SECONDS`).
* **Consequences**: Seamlessly supports NVIDIA CUDA GPUs, Intel Arc GPUs via DirectML (`torch-directml`), and CPU fallback with INT8 quantization (`optimum-quanto`).

---

### ADR-006: Approach-Suffixed Model Output Directories
* **Status**: Accepted
* **Context**: Running different variants risked overwriting checkpoints in `models/deberta-lateral-movement`.
* **Decision**: Training output directories automatically append the approach suffix:
  * `models/deberta-lateral-movement-v1_single_entry`
  * `models/deberta-lateral-movement-v2_sliding_window`
  * `external/trainedoutput/deberta-lateral-movement-<approach>-<timestamp>/`
* **Consequences**: Clean separation of checkpoints and effortless UI ingestion.

---

### ADR-007: Windows Console CP1252 ASCII Encoding Safety
* **Status**: Accepted
* **Context**: Windows PowerShell console uses `cp1252` encoding by default. Printing Unicode emojis (`🟢`, `🟡`, `🔴`) raises `UnicodeEncodeError` in standard Python scripts.
* **Decision**: Standardize all CLI terminal print statements on ASCII-safe symbols (`[+]`, `[!]`, `[COMPARISON]`, `[v1]`, `[v2]`).
* **Consequences**: Guaranteed crash-free execution on Windows terminals and CI/CD pipelines.
