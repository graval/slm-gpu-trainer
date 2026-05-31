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
│   └── trainedoutput/       <-- [OUTPUT] Created automatically by training
│       ├── deberta-lateral-movement/
│       └── qwen-lateral-movement/
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
2. Start training using:
   ```bash
   # Option A: Train DeBERTa Classifier SLM
   docker compose run --rm slm-trainer classifier
   
   # Option B: Train Qwen Generative SLM (with 4-bit VRAM optimization)
   docker compose run --rm slm-trainer generator --epochs 3 --batch_size 2 --qlora
   ```

---

### Mode 2: CPU Fallback Mode
*Ideal for lightweight validation, testing, or environments without discrete NVIDIA hardware.*

#### How the Fallback Works:
- **PyTorch Fallback:** The container uses a single CUDA-enabled runtime that executes perfectly on CPU when no GPU resources are exposed.
- **Auto-Downsampling:** When running the classifier on CPU, the container automatically downsamples the dataset to a balanced subset to run the entire training and validation cycle in seconds rather than hours.

#### To Run:
1. **Comment out** the `deploy:` block inside `docker-compose.yml` to prevent Docker Compose from throwing a hardware driver exception on startup:
   ```yaml
   # deploy:
   #   resources:
   #     reservations:
   #       devices:
   #         - driver: nvidia
   #           count: all
   #           capabilities: [gpu]
   ```
2. Start training:
   ```bash
   docker compose run --rm slm-trainer classifier
   ```

---

### Mode 3: Containerized EDR Dashboard Console
*Highly recommended to monitor and visualize training progress directly inside Docker.*

#### To Run:
Expose port `8501` and launch the Streamlit server completely inside Docker by running:
```bash
docker compose up -d slm-dashboard
```

#### Accessing the Dashboard:
Once running, open your web browser on your host machine to:
* **Dashboard URL:** [http://localhost:8501](http://localhost:8501)

The containerized dashboard will automatically read `/app/external/training_progress.json` through the shared volume and render your training run's stats, loss curves, and ETAs live!

To stop the dashboard container:
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
