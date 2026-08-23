# SLM Trainer Context Restoration & Master Project Index

This document acts as an immediate context restoration point for any developer or AI assistant (Antigravity, Claude, Cursor, Copilot, Gemini).

---

## 🏗️ Architecture & Specifications System
The project follows a **Specification-Driven System** (Spec-Kit + ADRs) located in [`specs/`](file:///c:/workspaceag/slmgpuv1/slm-tr/specs/):

1. **[`specs/01_ARCHITECTURE.md`](file:///c:/workspaceag/slmgpuv1/slm-tr/specs/01_ARCHITECTURE.md)**:
   * **Dual-Model SLM Architecture**: 44M Classifier (`deberta-v3-small`) evaluates 100% of telemetry at $\approx 1.1\text{ms}$; 1.5B/3.8B Generative Reasoner (`Qwen2.5` / `Phi-3`) is triggered on anomalies to generate JSON alerts with MITRE mappings.
2. **[`specs/02_PARADIGMS_V1_V2.md`](file:///c:/workspaceag/slmgpuv1/slm-tr/specs/02_PARADIGMS_V1_V2.md)**:
   * **Phase 1 (`v1_single_entry`, $K=1$)**: Single isolated Sysmon event lines.
   * **Phase 2 (`v2_sliding_window`, $K=3..5$)**: Stateful rolling ring buffer correlating multi-event attack chains to reduce false positives by $\approx 94\%$.
3. **[`specs/03_REASONING_ENGINE.md`](file:///c:/workspaceag/slmgpuv1/slm-tr/specs/03_REASONING_ENGINE.md)**:
   * **Central Reasoning Engine (`reasoning/`)**: Standalone taxonomy (`PsExec`, `WMIC`, `WinRM`, `Pass-the-Hash`, `LSASS`, `SAM`, `Kerberos`), MITRE ATT&CK catalog (`mitre_kb.py`), and ChatML prompt builders.
4. **[`specs/04_ARCHITECTURAL_DECISIONS.md`](file:///c:/workspaceag/slmgpuv1/slm-tr/specs/04_ARCHITECTURAL_DECISIONS.md)**:
   * Formal **Architecture Decision Records (ADRs 001-007)** covering dual SLMs, vocab synchronization, DirectML/CPU quantization, dynamic path resolution, and model folder suffixing.
5. **[`specs/05_BENCHMARKS_AND_DATASETS.md`](file:///c:/workspaceag/slmgpuv1/slm-tr/specs/05_BENCHMARKS_AND_DATASETS.md)**:
   * Dataset specifications for **LMD-2023** ($>1\text{M}$ events) and **DARPA OpTC** out-of-distribution benchmark.
6. **[`specs/06_DEV_WORKFLOW_AND_CLI.md`](file:///c:/workspaceag/slmgpuv1/slm-tr/specs/06_DEV_WORKFLOW_AND_CLI.md)**:
   * Execution playbook, `.venv` setup, and test commands.

---

## 🤖 Universal AI Assistant Entrypoints
* [`AGENTS.md`](file:///c:/workspaceag/slmgpuv1/slm-tr/AGENTS.md): Universal instructions for Antigravity, Gemini Code Assist, OpenAI agents.
* [`CLAUDE.md`](file:///c:/workspaceag/slmgpuv1/slm-tr/CLAUDE.md): Instructions for Claude Code CLI.
* [`.cursorrules`](file:///c:/workspaceag/slmgpuv1/slm-tr/.cursorrules): Instructions for Cursor IDE.
* [`.github/copilot-instructions.md`](file:///c:/workspaceag/slmgpuv1/slm-tr/.github/copilot-instructions.md): Instructions for GitHub Copilot.
