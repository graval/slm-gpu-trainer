# External Mounted Workspace Directory Guide

This folder (`external/`) serves as your persistent host-mounted workspace. It is mounted inside the Docker container to share input datasets, cache base models, and persist trained output models.

---

## 📂 Directory Structure

Once running, your `external/` folder will be structured as follows:

```text
external/
├── README.md               # This configuration guide
├── *.csv                   # Your input dataset files (e.g. lmd_2023_dataset.csv)
├── base_models/            # Persistent Hugging Face cache (Auto-created)
└── trainedoutput/          # Fine-tuned model checkpoints (Auto-created)
    ├── deberta-lateral-movement/   # Fine-tuned Encoder Classifier
    └── qwen-lateral-movement/      # Fine-tuned Causal Decoder LoRA adapters
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

## 📦 3. Model Training Outputs (`trainedoutput/`)

Upon successful completion of a training loop, the container automatically preserves your results on your host disk:
1. **Classifier Model (`trainedoutput/deberta-lateral-movement/`)**: Contains the fully trained weights, tokenizer config, and evaluation logs for the sequence classifier.
2. **Generator Model (`trainedoutput/qwen-lateral-movement/`)**: Contains the trained Low-Rank Adaptation (LoRA) weights and configuration files for causal security event explanations.
