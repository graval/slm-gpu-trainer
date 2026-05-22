# Docker Deployment Guide for SLM Lateral Movement Training

This directory contains Docker Compose configurations to run the full, high-performance training cycles for the **Classifier SLM** (DeBERTa-v3) and the **Generative SLM** (Qwen2.5-1.5B) inside containerized environments. 

We provide two variants:
1. **GPU (NVIDIA/CUDA) Variant:** Recommended for running full, high-performance training cycles.
2. **CPU-Only Variant:** Useful for fast validation tests or system testing where no NVIDIA graphics card is present.

---

## 🏗️ Folder Structure & Volume Mapping

To keep datasets and model weights fully decoupled from the Docker image, the containers use volume mapping. 

The default local volume path is mapping a folder named `external/` in the parent directory:
```
slm-tr/
├── data/
├── deployment/
│   ├── docker-compose-gpu.yml
│   ├── docker-compose-cpu.yml
│   └── README.md
├── external/                <-- YOUR MOUNTED DIRECTORY (e.g. from USB / local drive)
│   ├── lmd_2023_dataset.csv <-- Input Dataset (Place here)
│   └── trainedoutput/       <-- Output Models (Created automatically here)
│       ├── deberta-lateral-movement/
│       └── qwen-lateral-movement/
├── Dockerfile
└── ...
```

> [!TIP]
> You can override this default `external/` folder path by defining the `EXTERNAL_DATA_DIR` environment variable in your terminal (e.g., `EXTERNAL_DATA_DIR=E:\my_usb_drive`).

---

## ⚡ Variant 1: GPU Training (NVIDIA/CUDA)

### Prerequisites on the Host Tower:
1. **NVIDIA Graphics Card Drivers:** Installed on the host OS.
2. **Docker Engine / Docker Desktop:** Running on the host.
3. **NVIDIA Container Toolkit:** Installs the NVIDIA driver runtime hooks into Docker.

> **RTX 5090 / 5080 (Blackwell):** The GPU image uses `pytorch/pytorch:2.11.0-cuda12.8-cudnn9-runtime` (PyTorch 2.7+ with CUDA 12.8 for `sm_120`). Older images built on CUDA 12.1 / PyTorch 2.2 will not run on RTX 50-series GPUs.
   * *Windows Hosts:* If using Docker Desktop with WSL2 backend, this works out-of-the-box!
   * *Linux Hosts:* Install it via your package manager:
     ```bash
     sudo apt-get install -y nvidia-container-toolkit
     sudo systemctl restart docker
     ```

### Step 1: Place your Dataset CSV
Create the `external/` folder in the project root and copy `lmd_2023_dataset.csv` inside it. Alternatively, point `EXTERNAL_DATA_DIR` to the folder containing your dataset CSV.

### Step 2: Build the GPU Image
Navigate to this deployment folder and run (pulls ~13GB PyTorch CUDA 12.8 base on first build):
```bash
docker compose -f docker-compose-gpu.yml build
```

Push to Docker Hub after building:
```bash
docker tag slm-trainer:gpu YOUR_USER/slm-trainer:gpu
docker push YOUR_USER/slm-trainer:gpu
```
Or use `push_to_dockerhub.ps1` from this folder.

### Step 3: Run the Training Cycles

#### **Option A: Train the DeBERTa Classifier SLM (Full GPU Cycle)**
```bash
docker compose -f docker-compose-gpu.yml run --rm slm-trainer-gpu classifier
```
*Customization:* You can override hyper-parameters (such as epochs or batch size) by passing them at the end of the command:
```bash
docker compose -f docker-compose-gpu.yml run --rm slm-trainer-gpu classifier --epochs 3 --batch_size 16
```

#### **Option B: Train the Qwen Generative LoRA Reasoner (Full GPU Cycle)**
```bash
docker compose -f docker-compose-gpu.yml run --rm slm-trainer-gpu generator --epochs 3 --batch_size 2 --qlora
```
*(By passing `generator --qlora`, the model uses Parameter-Efficient Fine-Tuning with 4-bit quantization, running comfortably under 6GB VRAM on consumer GPUs!)*

### Step 4: Access your Models
Once the training cycle finishes, you will immediately see your fine-tuned weights inside the mounted directory:
* `external/trainedoutput/deberta-lateral-movement/`
* `external/trainedoutput/qwen-lateral-movement/`

---

## 🐚 Variant 2: CPU-Only Training

Useful for lightweight testing, environment diagnostics, or if you don't have an NVIDIA GPU available.

### Step 1: Build the CPU Image
```bash
docker compose -f docker-compose-cpu.yml build
```

### Step 2: Run DeBERTa Classifier verification (Automatically Downsampled)
On CPU, the container automatically downsamples the dataset to a balanced subset to run the entire pipeline end-to-end in seconds:
```bash
docker compose -f docker-compose-cpu.yml run --rm slm-trainer-cpu classifier
```

---

## 🛠️ Advanced Commands & Manual Operations

If you want to open a shell inside the container to inspect variables or run tools manually:
```bash
docker compose -f docker-compose-gpu.yml run --rm slm-trainer-gpu bash
```
Inside the container, you can run diagnostic tools:
```bash
# Verify PyTorch sees your GPU
python -c "import torch; print(torch.cuda.is_available())"

# Run a manual threat-hunting scan with the fallback EDR heuristics engine
python detect.py --cmd "wmic.exe process call create" --image "wmic.exe"
```

---

## 🐳 Pushing to Docker Hub (Remote Deployment)

If you are building the images on one machine (e.g. locally) and pushing them to your remote Docker Hub registry so they can be easily pulled on your target NVIDIA graphics card tower:

### Step 1: Log in to Docker Hub in your Terminal
Authenticate your terminal session using the Docker CLI command:
```bash
docker login
```
*(Enter your Docker Hub username and password or Personal Access Token when prompted)*

### Step 2: Tag & Push using Automated Helper Scripts
We provide two helper scripts inside this directory to automate tagging and pushing your local images:

* **Windows Systems (PowerShell):**
  ```powershell
  & .\push_to_dockerhub.ps1
  ```
* **Linux Systems (Bash):**
  ```bash
  chmod +x push_to_dockerhub.sh
  ./push_to_dockerhub.sh
  ```
The scripts will prompt you for your **Docker Hub username** and ask which variant (`gpu`, `cpu`, or `both`) you wish to deploy. They automatically map your local tag `slm-trainer` to `<username>/slm-trainer` and push them up to the cloud repository.

### Step 3: Pull on your NVIDIA Tower
Once uploaded, you can pull the image onto your GPU-equipped tower by executing:
```bash
docker pull <your_dockerhub_username>/slm-trainer:gpu
```
