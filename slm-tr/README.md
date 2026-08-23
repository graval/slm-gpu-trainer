# SLM Threat Ingestion & Training Framework (LMD-2023)

An end-to-end security engineering and Small Language Model (SLM) training framework built to detect **Lateral Movement** using the authentic, peer-reviewed **LMD-2023** threat telemetry dataset and **DARPA OpTC** out-of-distribution benchmark.

The project features a **two-phase architecture** supporting both **Single-Entry triage** and **Temporal Sliding Window** sequence analysis, combined with a centralized, decoupled **Reasoning Engine** for MITRE ATT&CK mapping and subtype explainability.

---

## 🏗️ Architecture Variants & Modularity

### 1. Phase 1: `v1_single_entry/` (Single Log Line Paradigm, $K=1$)
* **Concept:** Analyzes isolated, single Sysmon event log entries without prior history.
* **Latency:** Ultra-fast (~1-5 ms / event), minimal memory footprint.
* **Use-Case:** High-speed stateless log triage and immediate endpoint host filtering.

### 2. Phase 2: `v2_sliding_window/` (Temporal Sliding Window Paradigm, $K=3..5$)
* **Concept:** Packages chronological multi-event sequences (`[Event T-2] ... [Target Event T_0]`) using a stateful ring buffer.
* **Accuracy:** Correlates multi-stage attack actions (Network connection ➔ Named pipe ➔ Remote process execution), reducing False Positives by ~94%.
* **Use-Case:** Stateful EDR stream ingestion and Active Directory domain lateral movement detection.

### 3. Common: `reasoning/` (Central Reasoning & MITRE Engine)
* **Concept:** Dedicated module identifying granular attack sub-types (`PsExec`, `WMIC`, `WinRM`, `Pass-the-Hash`, `LSASS MiniDump`, `Registry SAM dump`, `Kerberos ticket forgery`).
* **Explainability:** Maps each event/window to official MITRE ATT&CK techniques (`T1021.002`, `T1047`, `T1550.002`, `T1003.001`) and generates explainable security reports.

---

## 📂 Project Directory Structure

*   `reasoning/`: Central reasoning engine, subtype catalog, and MITRE ATT&CK mapping database.
*   `v1_single_entry/`: Standalone loaders, trainers, detector, and evaluator for Single-Entry analysis.
*   `v2_sliding_window/`: Standalone loaders, trainers, detector, and evaluator for Sliding-Window analysis.
*   `scripts/compare_v1_v2.py`: Side-by-side benchmark comparison tool for evaluating v1 vs v2 across datasets.
*   `scripts/prepare_optc_benchmark.py`: Out-of-distribution DARPA OpTC test set synthesizer.
*   `data/`: LMD-2023 logs, OpTC benchmark, and unified loader wrappers.
*   `deployment/`: Docker Compose files for building and executing GPU and CPU containers.
*   `models/`: Output directory where trained model checkpoints and configurations are saved.
*   `detect.py`: Unified root CLI threat hunter supporting `--variant v1|v2`.
*   `eval.py`: Unified evaluation script supporting `--variant v1|v2`.
*   `app.py`: High-fidelity Streamlit SOC operations dashboard with Architecture Variant selector.

---

## ⚡ Option 1: Unified Container Training & UI Ingest (Docker)

This project features a unified container sequence utilizing a single image (`gauravraval/slm-trainer:gpucpu`) and a centralized `docker-compose.yml` to run the entire pipeline: starts the Streamlit EDR UI in the background, trains the model in the foreground, executes comparative testing, and updates the metrics automatically.

### 1. Place your Dataset
Create a folder called `external/` in the project root and place your `lmd_2023_dataset.csv` inside it.

### 2. Navigate and Run (Full GPU Acceleration)
To launch DeBERTa Sequence Classifier training on an **NVIDIA GPU** tower (supporting sm_120 Blackwell architectures natively):
```bash
cd deployment/
docker compose up slm-trainer
```
*To run the generative Qwen LoRA Decoder fine-tuning instead, open `deployment/docker-compose.yml` and change the `command` target to `["generator"]`.*

### 3. Run on CPU Fallback (Dynamic Calibration)
If you are running on a standard CPU system without an NVIDIA GPU, comment out the `deploy` CUDA devices block in `docker-compose.yml` and run:
```bash
docker compose up slm-trainer
```
- PyTorch will fall back to CPU execution, and the **Dynamic Hardware Performance Calibration** engine will automatically profile the CPU speed and calibrate the downsampling training size to complete cleanly in under **35 minutes** (defaulting to 2100 seconds).

### 4. Dynamic Run controls (Rapid UI & Testing Validation)
You can parameterize the target duration for the CPU calibration by passing `CALIBRATION_TARGET_SECONDS` as an environment variable (e.g. setting it to 10 seconds runs a rapid 300-sample verification loop in under a minute to validate your UI):
```bash
# Run in PowerShell or Bash with custom duration limit:
docker run --rm -d -p 8501:8501 --name slm-trainer-cpu -e DATASET_FILE=lmd_2023_dataset.csv -e CALIBRATION_TARGET_SECONDS=10 -v "c:\workspaceag\slmgpuv1\slm-tr\external:/app/external" gauravraval/slm-trainer:gpucpu classifier --epochs 1 --batch_size 8
```

### 5. Outputs Persistence
- Fine-tuned weights, adapters, tokenizers, checkpoints, and evaluation summaries will automatically be written directly to your host's `./external/trainedoutput/deberta-lateral-movement-YYYYMMDD_HHMMSS/` directory (timestamped at container startup).
- `evaluation_summary.json` is written directly to the host's root `./external/` folder to be ingested instantly by any active Streamlit EDR dashboard!

> See the [Deployment README](deployment/README.md) for full compose parameterizations.

---

## 💻 Option 2: Local Windows Development Setup

If you want to run the code directly on your Windows host:

### 1. Automated Environment Setup
Requires **Python 3.10+** on your PATH (this project is configured for **Python 3.13** locally).

Open PowerShell in the project root (`slm-tr/`) and run:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
.\setup_env.ps1
```
The script recreates `.venv` for your current Python, installs dependencies from `requirements.txt`, and runs the dataset setup utility to populate `data/lmd_2023_dataset.csv` when needed.

For **4-bit QLoRA on Linux + NVIDIA GPU**, use `requirements-qlora.txt` instead (includes `bitsandbytes`; not supported on Windows).

### 2. Run the Streamlit SOC Web Dashboard
Launch the gorgeous Streamlit web dashboard:
```powershell
.\.venv\Scripts\streamlit run app.py
```
This will open `http://localhost:8501`, featuring:
* Live SOC simulated alert log feeds.
* Interactive text classification and generative explanation playground.
* Dataset explorer and model performance charts.

### 3. Run the Interactive EDR CLI Detector
To evaluate threat logs directly via the terminal:
* **Interactive Scan Playground:**
  ```powershell
  .\.venv\Scripts\python detect.py --interactive
  ```
* **Log Stream Simulation:**
  ```powershell
  .\.venv\Scripts\python detect.py --simulate
  ```
* **Single Command Scan:**
  ```powershell
  .\.venv\Scripts\python detect.py --cmd "wmic /node:CORP-DC process call create 'cmd.exe'" --image "wmic.exe"
  ```

---

## 🧪 Training & Metrics Evaluation

### 1. Labeled Dataset Specifications
To train the classifier and generator, the labeled dataset must be provided as a CSV file placed at `data/lmd_2023_dataset.csv`.
The CSV dataset must contain at least the following standard host-security columns:
* `Image`: Full path of the executable image (e.g. `C:\Windows\System32\cmd.exe`)
* `CommandLine`: Command line arguments executed (e.g. `wmic /node:"target" process call create ...`)
* `ParentImage`: Parent process executable image path
* `ParentCommandLine`: Command line arguments of the parent process
* `User`: Executing security context user name (e.g. `NT AUTHORITY\SYSTEM` or `DOMAIN\jdoe`)
* `Label`: Threat classification label. Legitimate events must be labeled as `Normal` (or `0`). Lateral movement service events must be labeled as `EoRS` (or `1`). Credential harvesting and alternate token usage events must be labeled as `EoHT` (or `2`).

> **Automatic Label Normalization:** The loader dynamically resolves standard threat columns and normalizes labels (`Normal` -> 0, `EoRS` -> 1, `EoHT` -> 2).

### 2. Dataset Initialization & Download Scripts
If the dataset is not present, you can run the built-in initializer script to download authentic public lateral movement telemetry and baseline benign Windows logs:
```powershell
# Auto-download covenant & empire attack zips and compile fallback dataset:
.\.venv\Scripts\python scripts/setup_dataset.py
```
*(All large non-code datasets, raw JSON logs, and trained weights are excluded from Git repository tracking via `.gitignore`).*

### 3. Model Training
To train DeBERTa and Qwen models locally on CPU:
* **Train DeBERTa Classifier:**
  ```powershell
  $env:PYTHONUTF8="1"; .\.venv\Scripts\python train_classifier.py --epochs 3 --batch_size 8
  ```
* **Train Qwen LoRA Generator:**
  ```powershell
  $env:PYTHONUTF8="1"; .\.venv\Scripts\python train_generator.py --epochs 1 --batch_size 1 --gradient_accumulation_steps 1
  ```
* **Train Phi-3-mini LoRA Generator (INT8 CPU Quantized):**
  ```powershell
  $env:PYTHONUTF8="1"; .\.venv\Scripts\python train_generator.py --model_name microsoft/Phi-3-mini-4k-instruct --int8 --epochs 1 --batch_size 1 --gradient_accumulation_steps 1 --output_dir models/phi3-lateral-movement
  ```


### 4. Running Raw vs. Fine-Tuned Metrics Evaluation
To run comparative metrics (accuracy, macro precision/recall/F1, False Positives, False Negatives, and inference durations) on a 10% test split:
```powershell
$env:PYTHONUTF8="1"; .\.venv\Scripts\python evaluate_comparison.py
```
This script runs inference on both the raw base model and your locally fine-tuned model and:
1. Generates `evaluation_summary.json` (consumed dynamically by the Streamlit dashboard).
2. Appends timestamped comparison blocks to `evaluation_summary.log` in the project root.

> **💡 Best Practice:** It is highly recommended to **check in `evaluation_summary.log`** to your repository to preserve historic records of model training quality!

