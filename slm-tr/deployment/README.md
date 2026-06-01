# 🐳 Docker Deployment Guide: SLM Lateral Movement Training

Welcome to the deployment guide for the **SLM Lateral Movement Trainer**. This directory contains configurations to run training cycles for the **Classifier SLM** (DeBERTa-v3) and the **Generative SLM** (Qwen2.5-1.5B) inside a unified container environment.

With our updated architecture, we utilize a single **unified container image (`gauravraval/slm-trainer:gpucpu`)** that natively leverages NVIDIA GPUs when available, and automatically falls back to CPU-only mode otherwise.

---

## 🏗️ Volume Mapping & Mount Strategy (Crucial)

To keep datasets and model weights fully decoupled from the container environment, we utilize Docker volume mapping. This ensures your expensive model training outputs are written back directly to the host storage.

### Host and Container Directory Architecture

Here is how your host directories map to the container's environment:

```
host-project-root/ (slm-tr/)
├── deployment/
│   ├── docker-compose.yml   <-- Consolidated compose file
│   └── README.md
├── external/                <-- HOST DIRECTORY (YOUR MOUNT POINT)
│   ├── lmd_2023_dataset.csv <-- [INPUT] Place your raw dataset here!
│   ├── evaluation_summary.json <-- [TELEMETRY] Dynamic UI metrics
│   └── trainedoutput/       <-- [OUTPUT] Created automatically by training
│       ├── deberta-lateral-movement-YYYYMMDD_HHMMSS/
│       └── qwen-lateral-movement-YYYYMMDD_HHMMSS/
```

### Mount Path Configuration
In the `docker-compose.yml`, the mapping is defined as:
```yaml
volumes:
  - ${EXTERNAL_DATA_DIR:-../external}:/app/external
```

> [!IMPORTANT]
> - **Input Dataset Location:** The container's entrypoint script specifically looks for the dataset at `/app/external/lmd_2023_dataset.csv`. Therefore, you **MUST** place your `lmd_2023_dataset.csv` inside your host's `external/` folder before launching training.
> - **Custom Host Paths:** If you want to use a directory located elsewhere on your host (e.g., an external drive or a dedicated data disk), you can override the default path by defining the `EXTERNAL_DATA_DIR` environment variable:
>   * *Windows Powershell:* `$env:EXTERNAL_DATA_DIR="D:\datasets\slm_data"`
>   * *Linux Bash:* `export EXTERNAL_DATA_DIR="/mnt/datasets/slm_data"`

---

## ⚡ Unified Execution Pipeline: Dashboard + Training + Testing

Our consolidated Docker entrypoint orchestrates the **entire pipeline in a single execution sequence**. 
When you run a command like `classifier`, the container:
1. **Launches the Streamlit EDR UI** dashboard in the background inside the container (available at `http://localhost:8501`).
2. **Executes DeBERTa Classifier model training** in the foreground, dynamically streaming loss logs and training progress directly onto the dashboard *Live Training Monitor*.
3. **Automatically executes the post-training comparative testing suite** (`evaluate_comparison.py`) as soon as training finishes, evaluating raw vs. fine-tuned model performance.
4. **Saves all results** to unique timestamped directories and updates the dashboard dynamically with custom live metrics!

---

## ⚡ Execution Modes: GPU and CPU Fallback

A single image handles both modes. However, since the Docker Daemon requires hardware-level routing to access NVIDIA graphics adapters, you must select the appropriate runtime setting.

### Mode 1: High-Performance GPU Mode (NVIDIA CUDA)
*Recommended for full training cycles.*

#### Prerequisites:
1. **NVIDIA Host Drivers:** Installed on the host OS.
2. **NVIDIA Container Toolkit:** Installs the runtime hooks allowing Docker to expose the GPU to containers.
   * *Windows Hosts:* Docker Desktop with WSL2 backend supports CUDA out-of-the-box.
   * *Linux Hosts:* Install via your package manager:
     ```bash
     sudo apt-get install -y nvidia-container-toolkit
     sudo systemctl restart docker
     ```
3. **Hardware Support:** Optimized for PyTorch 2.7+ and CUDA 12.8 (with support for RTX 50-series Blackwell `sm_120` chips).

#### To Run:
1. Ensure the `deploy:` device reservation block is **active** (uncommented) in `docker-compose.yml`.
2. Start the unified pipeline:
   ```bash
   # Train DeBERTa Classifier, UI, and Evaluator in sequence:
   docker compose up slm-trainer
   ```

---

### Mode 2: CPU Fallback & Hardware Calibration Mode
*Ideal for lightweight validation, testing, or environments without discrete NVIDIA hardware.*

#### How the Fallback Works:
- **PyTorch Fallback:** The container uses a single CUDA-enabled runtime that executes perfectly on CPU when no GPU resources are exposed.
- **Dynamic Performance Auto-Calibration:** When running on CPU, the container automatically micro-benchmarks the host's CPU speeds and solves the training time equation to scale down the training partition to execute cleanly in under **35 minutes** (2100 seconds).
- **CALIBRATION_TARGET_SECONDS Parameter:** You can parameterize the target duration using this environment variable. For example, setting it to `10` runs an ultra-fast verification run with a minimum of 300 samples in under a minute to quickly validate UI updates:
  ```powershell
  # Powershell command for rapid CPU validation:
  docker run --rm -d -p 8501:8501 --name slm-trainer-cpu -e DATASET_FILE=lmd_2023_dataset.csv -e CALIBRATION_TARGET_SECONDS=10 -v "c:\workspaceag\slmgpuv1\slm-tr\external:/app/external" gauravraval/slm-trainer:gpucpu classifier --epochs 1 --batch_size 8
  ```

#### To Run:
1. **Comment out** the `deploy:` block inside `docker-compose.yml` to prevent Docker Compose from throwing a hardware driver exception on startup.
2. Start the pipeline:
   ```bash
   docker compose up slm-trainer
   ```

---

### Mode 3: Standalone Dashboard Mode
*Use this mode if you only want to spin up the Streamlit EDR UI dashboard to inspect prior training runs without executing any new training.*

#### To Run:
```bash
docker compose up -d slm-dashboard
```

#### Accessing the Dashboard:
Once running, open your web browser on your host machine to:
* **Dashboard URL:** [http://localhost:8501](http://localhost:8501)

To stop the standalone dashboard container:
```bash
docker compose down
```

---

## 🐳 Docker Hub Push Operations

If you build or modify the image locally and need to push it to a remote registry so it can be pulled easily on your remote NVIDIA tower:

### Step 1: Log in
```bash
docker login
```

### Step 2: Tag & Push using Helper Scripts
We provide automated helper scripts to easily tag the local unified image for your Docker Hub namespace and push it:

- **Windows Systems (PowerShell):**
  ```powershell
  & .\push_to_dockerhub.ps1
  ```
- **Linux Systems (Bash):**
  ```bash
  chmod +x push_to_dockerhub.sh
  ./push_to_dockerhub.sh
  ```

---

## 🛠️ Advanced Debugging & Interactive Command Shells

To explore files inside the container or manually test code:

```bash
# Open interactive bash shell
docker compose run --rm slm-trainer bash
```

Inside the container shell, you can run:
```bash
# Test PyTorch hardware access status
python -c "import torch; print('CUDA Available:', torch.cuda.is_available())"

# Execute a threat-hunting heuristics evaluation manually
python detect.py --cmd "wmic.exe process call create" --image "wmic.exe"
```
