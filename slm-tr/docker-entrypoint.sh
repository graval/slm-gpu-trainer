#!/bin/bash
set -e

# Path to the mounted external directory
EXTERNAL_DIR="/app/external"
EXTERNAL_CSV="${EXTERNAL_DIR}/lmd_2023_dataset.csv"
LOCAL_CSV_DIR="/app/data"
LOCAL_CSV="${LOCAL_CSV_DIR}/lmd_2023_dataset.csv"

echo "=========================================================="
echo "      🚀 SLM Lateral Movement Docker Training Runner     "
echo "=========================================================="

# Check if the external folder is mounted and contains the CSV
if [ ! -f "$EXTERNAL_CSV" ]; then
    echo "[!] ERROR: Could not find 'lmd_2023_dataset.csv' in the mounted folder."
    echo "    Please mount a folder containing the dataset CSV to /app/external."
    echo "    Example:"
    echo "      docker run --gpus all -v /path/to/my/data:/app/external slm-trainer <command>"
    echo "    Current files in /app/external:"
    ls -la "$EXTERNAL_DIR" 2>/dev/null || echo "    (Directory /app/external does not exist or is empty)"
    exit 1
fi

# Ensure local data directory exists and symlink or copy the CSV
mkdir -p "$LOCAL_CSV_DIR"
if [ -f "$LOCAL_CSV" ] || [ -L "$LOCAL_CSV" ]; then
    rm -f "$LOCAL_CSV"
fi
echo "[*] Mapping dataset: ${EXTERNAL_CSV} -> ${LOCAL_CSV}"
ln -s "$EXTERNAL_CSV" "$LOCAL_CSV"

# Check GPU availability (RTX 50-series needs PyTorch 2.7+ with CUDA 12.8 / sm_120)
echo "[*] Checking NVIDIA GPU availability inside container..."
python -c "
import sys
import torch
print(f'    PyTorch version: {torch.__version__}')
print(f'    CUDA version: {torch.version.cuda}')
print(f'    CUDA Available: {torch.cuda.is_available()}')
if not torch.cuda.is_available():
    print('    [!] NO CUDA GPU FOUND! Falling back to CPU execution mode...')
else:
    name = torch.cuda.get_device_name(0)
    cap = torch.cuda.get_device_capability(0)
    print(f'    Device Name: {name}')
    print(f'    Compute Capability: sm_{cap[0]}{cap[1]}')
    try:
        x = torch.randn(4, 4, device='cuda')
        y = x @ x
        print(f'    GPU tensor test: OK (shape={tuple(y.shape)})')
    except Exception as e:
        print(f'    [!] GPU tensor test FAILED: {e}')
        print('    [!] Falling back to CPU execution mode...')
"

# Default action if no argument is provided
if [ $# -eq 0 ]; then
    echo "[*] No command specified. Defaulting to running the DeBERTa Classifier training."
    CHOICE="classifier"
else
    CHOICE="$1"
    shift # Remove the first argument, leaving any additional custom arguments (like --epochs, etc.)
fi

OUTPUT_MOUNT_DIR="${EXTERNAL_DIR}/trainedoutput"
mkdir -p "$OUTPUT_MOUNT_DIR"

if [ "$CHOICE" = "classifier" ]; then
    echo "[*] Starting DeBERTa Classifier training (Full training cycle)..."
    python train_classifier.py --csv_path "$LOCAL_CSV" --output_dir "/app/models/deberta-lateral-movement" "$@"
    
    echo "[*] Copying trained model weights to host mount point: ${OUTPUT_MOUNT_DIR}/deberta-lateral-movement"
    mkdir -p "${OUTPUT_MOUNT_DIR}/deberta-lateral-movement"
    cp -rf /app/models/deberta-lateral-movement/* "${OUTPUT_MOUNT_DIR}/deberta-lateral-movement/"
    echo "[+] SUCCESS: Classifier model successfully created at host folder: ${OUTPUT_MOUNT_DIR}/deberta-lateral-movement"

elif [ "$CHOICE" = "generator" ]; then
    echo "[*] Starting Qwen LoRA Generator training (Full training cycle)..."
    # Run LoRA training. Enable QLoRA to conserve VRAM if needed.
    python train_generator.py --csv_path "$LOCAL_CSV" --output_dir "/app/models/qwen-lateral-movement" "$@"
    
    echo "[*] Copying trained LoRA adapters to host mount point: ${OUTPUT_MOUNT_DIR}/qwen-lateral-movement"
    mkdir -p "${OUTPUT_MOUNT_DIR}/qwen-lateral-movement"
    cp -rf /app/models/qwen-lateral-movement/* "${OUTPUT_MOUNT_DIR}/qwen-lateral-movement/"
    echo "[+] SUCCESS: LoRA adapters successfully created at host folder: ${OUTPUT_MOUNT_DIR}/qwen-lateral-movement"

else
    # Allow executing arbitrary command (e.g. bash, detect.py, etc.)
    echo "[*] Executing custom command: $CHOICE $@"
    exec "$CHOICE" "$@"
fi
