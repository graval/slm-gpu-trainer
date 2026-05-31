# SLM Trainer Context Restoration & Resume Guide

This local guide captures the exact state of our pair-programming session as of **May 31, 2026**. Use this snapshot to quickly bring any future developer or AI coding assistant up to speed on the codebase, Docker setups, and recent architectural changes.

---

## 🎯 High-Level Goal achieved

We successfully resolved the dashboard metrics sync issue where the **SLM Training & Performance Analytics** page was locked to cached pre-trained baselines. We configured the training container to run a unified sequence (Dashboard background -> model training -> post-training comparison metrics) and to save the compiled model files inside unique host-mounted timestamped directories.

---

## 🛠️ Implemented Architectural Fixes

### 1. Missing Evaluator Copied to Container
- **Problem**: `evaluate_comparison.py` was missing from the Docker image's `COPY` statement in the `Dockerfile`. Post-training comparative testing was failing inside the container, preventing the generation of `evaluation_summary.json`.
- **Solution**: Added `evaluate_comparison.py` to the primary COPY statement in the [Dockerfile](file:///c:/workspaceag/slmgpuv1/slm-tr/Dockerfile).

### 2. Windows CRLF Line Endings Protection
- **Problem**: Windows carriage return characters (`\r`) in [docker-entrypoint.sh](file:///c:/workspaceag/slmgpuv1/slm-tr/docker-entrypoint.sh) caused Linux execution errors inside the container.
- **Solution**: Integrated an automatic `sed` utility statement inside the [Dockerfile](file:///c:/workspaceag/slmgpuv1/slm-tr/Dockerfile) to sanitize CRLF into LF line endings at image build-time:
  ```dockerfile
  RUN sed -i 's/\r$//' /app/docker-entrypoint.sh && chmod +x /app/docker-entrypoint.sh
  ```

### 3. Robust Dynamic Summary Parser
- **Problem**: Raw Hugging Face training summaries (which have mismatched metric structures) could overwrite or share names with the comparative `evaluation_summary.json`, crashing the UI with a `KeyError`.
- **Solution**: Implemented a structural validator function `is_valid_summary(s)` in [app.py](file:///c:/workspaceag/slmgpuv1/slm-tr/app.py) verifying the presence of key comparative keys (`"raw_model"` and `"trained_model"`) prior to ingestion, assuring graceful fallback.

---

## 📂 Active Repository & Deployment State

- **Active GitHub Branch**: `feature/evaluation-metrics-dashboard`
- **Remote Git Repository**: `github.com:graval/slm-gpu-trainer.git`
- **Docker Registry Image Tag**: `gauravraval/slm-trainer:gpucpu` (Successfully built and pushed to Docker Hub)
- **Modified & Synced Files**:
  - [slm-tr/app.py](file:///c:/workspaceag/slmgpuv1/slm-tr/app.py) — Robust comparative metrics loading & fallbacks
  - [slm-tr/Dockerfile](file:///c:/workspaceag/slmgpuv1/slm-tr/Dockerfile) — Integrated missing scripts and auto CRLF-to-LF conversion
  - [slm-tr/deployment/docker-compose.yml](file:///c:/workspaceag/slmgpuv1/slm-tr/deployment/docker-compose.yml) — Unified compose exposure
  - [slm-tr/docker-entrypoint.sh](file:///c:/workspaceag/slmgpuv1/slm-tr/docker-entrypoint.sh) — Multi-process background/foreground sequential runner

---

## 🚀 Commands & Verification Playbook

### To Run Locally on Your GPU Tower (with NVIDIA RTX sm_120 Support):
This launches the UI dashboard on port 8501 in the background, trains the DeBERTa model on the GPU, executes evaluation, and saves the output to a local timestamped host directory:
```bash
docker run --gpus all --rm -d -p 8501:8501 --name slm-trainer-gpu -e DATASET_FILE=lmd_2023_dataset.csv -v "c:\workspaceag\slmgpuv1\slm-tr\external:/app/external" gauravraval/slm-trainer:gpucpu classifier
```

### To Run Qwen LoRA Generator Fine-Tuning:
```bash
docker run --gpus all --rm -d -p 8501:8501 --name slm-trainer-gpu -e DATASET_FILE=lmd_2023_dataset.csv -v "c:\workspaceag\slmgpuv1\slm-tr\external:/app/external" gauravraval/slm-trainer:gpucpu generator
```

### Useful Diagnostics Checklist:
- **Inspect Streamlit logs inside the container**: `docker exec slm-trainer-gpu cat /app/streamlit.log`
- **Check training printouts**: `docker logs slm-trainer-gpu`
- **Verify host output directories**: Check [external/trainedoutput/](file:///c:/workspaceag/slmgpuv1/slm-tr/external/trainedoutput/) for the generated `deberta-lateral-movement-YYYYMMDD_HHMMSS` timestamped directories containing final weights, configurations, and evaluation logs.
