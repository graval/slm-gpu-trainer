# SLM Threat Ingestion & Training Framework (LMD-2023)

An end-to-end security engineering and Small Language Model (SLM) training framework built to detect **Lateral Movement** using the authentic, peer-reviewed **LMD-2023** threat telemetry benchmark dataset.

The project features a dual-model architecture designed for high-performance classification and explainable generative reasoning, an EDR CLI agent tool, a simulated live SOC operations dashboard, and containerized Docker pipelines with full NVIDIA GPU acceleration (CUDA) support.

---

## 🏗️ Core Architecture & Models

1. **Classifier SLM (`microsoft/deberta-v3-small` - 44M parameters):**
   * *Purpose:* Extremely fast classification (~1.1ms latency), low memory footprint.
   * *Use-case:* Host-level EDR agent detection and high-speed SIEM ingestion pipeline.
2. **Generative Reasoner SLM (`Qwen/Qwen2.5-1.5B-Instruct` - 1.5B parameters):**
   * *Purpose:* Fine-tuned via Parameter-Efficient LoRA (and 4-bit QLoRA) to output structured JSON threat alerts with corresponding MITRE ATT&CK technique mapping and human-readable security reasoning.
   * *Use-case:* High-fidelity threat explainability and automated SOC analyst triage.

---

## 📂 Project Structure

*   `data/`: Contains LMD-2023 logs and OTRF Mordor dataset loaders and preprocessors.
*   `deployment/`: Contains Docker Compose files for building and executing GPU and CPU containers.
*   `models/`: Output directory where trained model safetensors and config checkpoints are written.
*   `scripts/`: Automation utilities for setup and dataset retrieval.
*   `train_classifier.py`: Custom PyTorch & Hugging Face training script for the DeBERTa model.
*   `train_generator.py`: Fine-tuning script for Qwen LoRA instruction tuning using SFTTrainer.
*   `detect.py`: Interactive CLI threat hunter tool with a built-in pre-trained EDR heuristics fallback.
*   `app.py`: High-fidelity Streamlit SOC operations dashboard.

---

## ⚡ Option 1: GPU-Accelerated Container Training (Docker)

If you have a host tower with an NVIDIA graphics card and want to run the full training cycles while keeping datasets and outputs external, follow the Docker pipeline:

### 1. Place your Dataset
Create a folder called `external/` in the project root and place `lmd_2023_dataset.csv` inside it.

### 2. Navigate and Build
```bash
cd deployment/
docker compose -f docker-compose-gpu.yml build
```

### 3. Run Training (Full CUDA Acceleration)
* **Train DeBERTa Classifier:**
  ```bash
  docker compose -f docker-compose-gpu.yml run --rm slm-trainer-gpu classifier
  ```
* **Train Qwen LoRA Generator:**
  ```bash
  docker compose -f docker-compose-gpu.yml run --rm slm-trainer-gpu generator --epochs 3 --batch_size 2 --qlora
  ```

*The final model weights will automatically be created in your host folder at `./external/trainedoutput/`!*

> See the [Deployment README](deployment/README.md) for more details, including CPU-only container steps.

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

## 🧪 Training Locally
Once your dataset is active in `data/`:
* **Train Classifier SLM:**
  ```powershell
  .\.venv\Scripts\python train_classifier.py --epochs 3 --batch_size 8
  ```
* **Train Generative SLM:**
  ```powershell
  .\.venv\Scripts\python train_generator.py --epochs 3 --batch_size 2
  ```
  *(Add `--qlora` if you are running locally on a standard CUDA GPU to save memory).*
