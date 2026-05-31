# SLM Trainer Context Restoration & Resume Guide

This local guide captures the exact state of our pair-programming session as of **May 31, 2026**. Use this snapshot to quickly bring any future developer or AI coding assistant up to speed on the codebase, Docker setups, and recent architectural changes.

---

## 🎯 High-Level Goal Achieved

We successfully resolved the dashboard metrics sync issue where the **SLM Training & Performance Analytics** page was locked to cached pre-trained baselines. We configured the training container to run a unified sequence (Dashboard background -> model training -> post-training comparison metrics) and to save the compiled model files inside unique host-mounted timestamped directories. 

We successfully validated the entire pipeline's end-to-end telemetry and UI dynamic updates using a rapid CPU test run, which has now transitioned to a full-scale normal production run in your background.

---

## 🛠️ Implemented Architectural & UI Fixes

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

### 4. ETA Visual Zero-Out & Lighter Est. Color
- **Problem**: Once training completed, the remaining time (ETA) would fall back to `"Estimating..."` with color `#889`, which appeared black and unreadable on the dark cards.
- **Solution**: Refactored [app.py](file:///c:/workspaceag/slmgpuv1/slm-tr/app.py#L689) to detect if `current_step >= max_steps` and immediately display **`00:00:00`** in bright green (`#10b981`). Used a lighter, readable grey (`#aab`) during startup estimations.

### 5. Post-Training Testing Status Notice Banner
- **Problem**: Training completes quickly, but comparative evaluation takes another 8-10 minutes on CPU. Users were confused why training completed but metrics still showed reference baselines.
- **Solution**: Added a warning banner in [app.py](file:///c:/workspaceag/slmgpuv1/slm-tr/app.py#L425) indicating that training was successful and the post-training tester is actively compiling metrics inside the container.

### 6. Parameterized Trainer Auto-Calibration
- **Problem**: Calibration duration was hardcoded to 35 minutes, making rapid testing difficult.
- **Solution**: Updated [train_classifier.py](file:///c:/workspaceag/slmgpuv1/slm-tr/train_classifier.py#L205) to read target duration via the environment variable `CALIBRATION_TARGET_SECONDS` (defaulting to 2100.0 seconds). Setting this to 10 seconds runs a rapid 300-sample verification in under a minute!

---

## 📂 Active Repository & Deployment State

- **Active GitHub Branch**: `feature/evaluation-metrics-dashboard`
- **Remote Git Repository**: `github.com:graval/slm-gpu-trainer.git`
- **Docker Registry Image Tag**: `gauravraval/slm-trainer:gpucpu` (Successfully built and pushed to Docker Hub)
- **Modified & Synced Files**:
  - [slm-tr/app.py](file:///c:/workspaceag/slmgpuv1/slm-tr/app.py) — Dynamic notice banners, ETA zero-out, and robust summary loaders
  - [slm-tr/Dockerfile](file:///c:/workspaceag/slmgpuv1/slm-tr/Dockerfile) — Integrated scripts and line-endings conversion
  - [slm-tr/train_classifier.py](file:///c:/workspaceag/slmgpuv1/slm-tr/train_classifier.py) — Dynamic calibration environment variable
  - [slm-tr/evaluate_comparison.py](file:///c:/workspaceag/slmgpuv1/slm-tr/evaluate_comparison.py) — Comparative evaluator
  - [slm-tr/deployment/docker-compose.yml](file:///c:/workspaceag/slmgpuv1/slm-tr/deployment/docker-compose.yml) — Exposes ports
  - [slm-tr/docker-entrypoint.sh](file:///c:/workspaceag/slmgpuv1/slm-tr/docker-entrypoint.sh) — Multi-process background/foreground sequential runner

---

## 🚀 Commands & Playbook

### Normal Production GPU Execution:
This launches the UI, trains DeBERTa on GPU, executes testing, and outputs timestamped folders:
```bash
docker run --gpus all --rm -d -p 8501:8501 --name slm-trainer-gpu -e DATASET_FILE=lmd_2023_dataset.csv -v "c:\workspaceag\slmgpuv1\slm-tr\external:/app/external" gauravraval/slm-trainer:gpucpu classifier
```

### Rapid Verification CPU Execution (For testing purposes):
Runs training and testing sequence in under 1 minute:
```bash
docker run --rm -d -p 8501:8501 --name slm-trainer-cpu -e DATASET_FILE=lmd_2023_dataset.csv -e CALIBRATION_TARGET_SECONDS=10 -v "c:\workspaceag\slmgpuv1\slm-tr\external:/app/external" gauravraval/slm-trainer:gpucpu classifier --epochs 1 --batch_size 8
```
*(Note: Cap test split in `evaluate_comparison.py` to 100 samples if verifying this quickly on CPU).*
