# GitHub Copilot Instructions

This repository implements a Dual-Model Small Language Model (SLM) framework for Lateral Movement Detection in Windows Sysmon logs.

## Architecture
- Dual Models: High-speed 44M Classifier (DeBERTa / DistilBERT) + 1.5B/3.8B Generative Reasoner (Qwen / Phi-3).
- Paradigms: `v1_single_entry` ($K=1$, stateless single-event log lines) vs `v2_sliding_window` ($K=3..5$, multi-event temporal sequences).
- Central Reasoning: All subtype heuristics and MITRE ATT&CK mappings live in `reasoning/`.
- Specifications: Complete Architecture Decision Records and specs are located in `specs/`.

## Coding Conventions
- Python environment: `.venv\Scripts\python.exe`
- Always call `resolve_dataset_path()` when reading datasets.
- Ensure ASCII-only console logging on Windows.
