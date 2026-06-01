# External Mounted Workspace Directory Guide

This folder (`external/`) serves as your persistent host-mounted workspace. It is mounted inside the Docker container to share input datasets, cache base models, and persist trained output models.

---

## 📂 Directory Structure

Once running, your `external/` folder will be structured as follows:

```text
external/
├── README.md               # This configuration guide
├── *.csv                   # Your input dataset files (e.g. lmd_2023_dataset.csv)
├── evaluation_summary.json # Active telemetry comparison file read by dashboard UI
├── evaluation_summary.log  # Append-only logs showing raw vs fine-tuned historic runs
├── base_models/            # Persistent Hugging Face cache (Auto-created)
└── trainedoutput/          # Fine-tuned model checkpoints (Auto-created)
    ├── deberta-lateral-movement-YYYYMMDD_HHMMSS/ # Timestamped Classifier folder
    └── qwen-lateral-movement-YYYYMMDD_HHMMSS/    # Timestamped LoRA Generator folder
```

---

## 📋 1. Dataset Preparation & Auto-Detection

The container features **smart auto-detection** for loading your CSV datasets. You do not need to rename your files!

* **Standard Placement**: Simply place your `.csv` dataset file (e.g., `lmd_2023_dataset.csv` or any custom CSV file) directly into this `external/` directory.
* **Auto-Discovery**:
  * If exactly **one CSV file** exists in this folder, the container will automatically locate and ingest it for training.
  * If multiple CSVs are present, it prefers files named `lmd_2023_dataset.csv` or `dataset.csv`.
* **Explicit Targeting**: You can explicitly instruct the container to train on a specific CSV by passing the `DATASET_FILE` environment variable:
  ```cmd
  -e DATASET_FILE=your_custom_dataset.csv
  ```

---

## 💾 2. Persistent Base Model Cache (`base_models/`)

To prevent downloading massive base models (like DeBERTa or Qwen) repeatedly and losing them every time the container exits, we automatically route the Hugging Face Hub cache directly to this host directory:
* **Location**: `external/base_models/`
* **Benefit**: The first time you train, the models are downloaded and cached permanently on your host machine. Future training runs will load the base models **instantaneously (<10 seconds)** without consuming internet bandwidth or disk write overhead.

---

## 📦 3. Model Training Outputs & Telemetry Logs (`trainedoutput/`)

Upon successful completion of a training loop, the container automatically preserves your results on your host disk:
1. **Timestamped Classifier Run (`trainedoutput/deberta-lateral-movement-YYYYMMDD_HHMMSS/`)**: Contains the fully fine-tuned classifier weights, configuration files, checkpoint records, and the specific comparative metrics files (`evaluation_summary.json` / `.log`).
2. **Timestamped Generator Run (`trainedoutput/qwen-lateral-movement-YYYYMMDD_HHMMSS/`)**: Contains the Low-Rank Adaptation (LoRA) weights and configuration files for explainable causal security reasoning.
3. **Dynamic Dashboard Metrics (`external/evaluation_summary.json`)**: Formulated by the post-training tester, this file is written to the root of the mounted host folder at the end of training. Any active Streamlit SOC Web Dashboard immediately consumes it, refreshing to show live custom fine-tuned results!
4. **Historical Quality Logs (`external/evaluation_summary.log`)**: An append-only log recording model metrics comparison deltas. Checking in this file keeps a historical audit trail of security model improvements!
