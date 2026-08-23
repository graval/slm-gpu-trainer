# Project Specifications & Architecture Decision System (Spec-Kit)

Welcome to the central specification and context repository for the **SLM Lateral Movement Detection** codebase. This directory provides structured, authoritative documentation for developers and AI assistants (Antigravity, Cursor, Claude Code, GitHub Copilot).

---

## 📑 Specification Index

| Document | Description |
| :--- | :--- |
| [**`01_ARCHITECTURE.md`**](file:///c:/workspaceag/slmgpuv1/slm-tr/specs/01_ARCHITECTURE.md) | High-level system architecture, dual-model SLM design, and directory layout. |
| [**`02_PARADIGMS_V1_V2.md`**](file:///c:/workspaceag/slmgpuv1/slm-tr/specs/02_PARADIGMS_V1_V2.md) | Detailed specifications for **Phase 1: `v1_single_entry` ($K=1$)** vs. **Phase 2: `v2_sliding_window` ($K=3..5$)**. |
| [**`03_REASONING_ENGINE.md`**](file:///c:/workspaceag/slmgpuv1/slm-tr/specs/03_REASONING_ENGINE.md) | Centralized `reasoning/` engine, attack subtype taxonomy, and MITRE ATT&CK mapping database. |
| [**`04_ARCHITECTURAL_DECISIONS.md`**](file:///c:/workspaceag/slmgpuv1/slm-tr/specs/04_ARCHITECTURAL_DECISIONS.md) | Formal **Architecture Decision Records (ADRs)** documenting design trade-offs and rationale. |
| [**`05_BENCHMARKS_AND_DATASETS.md`**](file:///c:/workspaceag/slmgpuv1/slm-tr/specs/05_BENCHMARKS_AND_DATASETS.md) | Dataset schemas, downsampling contracts, and out-of-distribution DARPA OpTC benchmarking. |
| [**`06_DEV_WORKFLOW_AND_CLI.md`**](file:///c:/workspaceag/slmgpuv1/slm-tr/specs/06_DEV_WORKFLOW_AND_CLI.md) | Virtual environment instructions, CLI threat hunting, and model evaluation commands. |
