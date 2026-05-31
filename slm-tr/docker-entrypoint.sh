#!/bin/bash
set -e

# Path to the mounted external directory
EXTERNAL_DIR="/app/external"
LOCAL_CSV_DIR="/app/data"
LOCAL_CSV="${LOCAL_CSV_DIR}/lmd_2023_dataset.csv"

# Configure Hugging Face to cache all downloaded base models in the host-mounted external folder
export HF_HOME="${EXTERNAL_DIR}/base_models"
mkdir -p "$HF_HOME"

echo "=========================================================="
echo "      🚀 SLM Lateral Movement Docker Training Runner     "
echo "=========================================================="

# Dynamically locate the CSV dataset file in /app/external
if [ -n "$DATASET_FILE" ] && [ -f "${EXTERNAL_DIR}/${DATASET_FILE}" ]; then
    EXTERNAL_CSV="${EXTERNAL_DIR}/${DATASET_FILE}"
    echo "[*] Using dataset specified via environment variable: ${EXTERNAL_CSV}"
else
    # Automatically detect CSV files in the mounted folder
    CSV_FILES=($(find "$EXTERNAL_DIR" -maxdepth 1 -name "*.csv" -type f 2>/dev/null))
    if [ ${#CSV_FILES[@]} -eq 1 ]; then
        EXTERNAL_CSV="${CSV_FILES[0]}"
        echo "[*] Auto-detected single CSV dataset in external folder: ${EXTERNAL_CSV}"
    elif [ ${#CSV_FILES[@]} -gt 1 ]; then
        # If there are multiple, check if one matches 'lmd_2023_dataset.csv' or 'dataset.csv' as a preference
        PREF_FILE=""
        for f in "${CSV_FILES[@]}"; do
            basename_f=$(basename "$f")
            if [ "$basename_f" = "lmd_2023_dataset.csv" ] || [ "$basename_f" = "dataset.csv" ]; then
                PREF_FILE="$f"
                break
            fi
        done
        if [ -n "$PREF_FILE" ]; then
            EXTERNAL_CSV="$PREF_FILE"
            echo "[*] Multiple CSVs found. Selecting preferred dataset: ${EXTERNAL_CSV}"
        else
            EXTERNAL_CSV="${CSV_FILES[0]}"
            echo "[!] WARNING: Multiple CSV files found in mounted folder. Selecting the first one: ${EXTERNAL_CSV}"
            echo "    Tip: You can specify your exact file using: -e DATASET_FILE=your_file.csv"
        fi
    else
        EXTERNAL_CSV=""
    fi
fi

# Check if a CSV was located
if [ -z "$EXTERNAL_CSV" ] || [ ! -f "$EXTERNAL_CSV" ]; then
    echo "[!] ERROR: Could not find any CSV dataset in the mounted folder."
    echo "    Please place your dataset CSV file directly inside the mounted folder (/app/external)."
    echo "    Current files in /app/external:"
    ls -la "$EXTERNAL_DIR" 2>/dev/null || echo "    (Directory /app/external does not exist or is empty)"
    exit 1
fi

# Ensure local data directory exists and symlink the CSV
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

elif [ "$CHOICE" = "dashboard" ] || [ "$CHOICE" = "ui" ]; then
    echo "[*] Starting SLM EDR Security Console Dashboard inside container..."
    exec streamlit run app.py --server.port 8501 --server.address 0.0.0.0

else
    # Allow executing arbitrary command (e.g. bash, detect.py, etc.)
    echo "[*] Executing custom command: $CHOICE $@"
    exec "$CHOICE" "$@"
fi
