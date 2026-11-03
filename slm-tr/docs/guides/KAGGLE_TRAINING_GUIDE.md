# 🛡️ EdgeShield SLM Training Guide: Kaggle Environment

This guide details how to leverage **Kaggle's 30 Hours/Week Free GPU** infrastructure (Dual Tesla T4 or Tesla P100) with **30 GB System RAM** to train the EdgeShield Small Language Model (SLM) framework using the authentic **1.75M Element LMD-2023** Lateral Movement dataset.

---

## 🚀 Key Advantages of Kaggle vs Google Colab

| Feature | Google Colab (Free) | Kaggle Notebooks (Free) | Advantage for EdgeShield |
| :--- | :--- | :--- | :--- |
| **GPU Time** | Dynamic (~12-15 hrs/wk, unpredictable) | **30 Hours / Week** guaranteed reset | Predictable, guaranteed quota |
| **GPU Hardware** | Single T4 (15 GB VRAM) | **Dual T4 x 2** (30 GB aggregate) or **P100** | Faster batch throughput & higher VRAM |
| **System RAM** | 12.7 GB (OOM risk on large CSVs) | **30.0 GB System RAM** | **Zero OOM risk** loading 1.07GB real LMD-2023 dataset |
| **Session Timeout** | Drops after idle / ~3-4 hours | **12-Hour Continuous Run** | Allows full multi-stream training + Qwen SFT |
| **Disk Space** | Ephemeral, easily wiped | **73 GB Disk Space** | Store FP32, INT8 ONNX, and Sysmon datasets |
| **Artifact Persistence** | Needs Google Drive mount | Direct **Output Tab** download or Kaggle Model export | Seamless 1-click zip download |

---

## ⚙️ Step 1: Create a Kaggle Notebook

1. Navigate to [kaggle.com/code](https://www.kaggle.com/code).
2. Click **"New Notebook"**.
3. In the top toolbar, click **File** $\rightarrow$ **Import Notebook** $\rightarrow$ upload [`EdgeShield_Kaggle_Training.ipynb`](../../EdgeShield_Kaggle_Training.ipynb).
   - Alternatively, you can copy-paste cells into a blank notebook.

---

## 🛠️ Step 2: Configure Essential Settings (Right-Hand Panel)

In the right-hand sidebar under **Notebook options**:

1. **Accelerator**:
   - Select **`GPU T4 x 2`** (or `GPU P100`).
2. **Internet**:
   - Toggle to **`Internet on`** *(Crucial: required to clone the repo, install pip dependencies, download HuggingFace base weights, and download LMD-2023 via gdown)*.
   - *Note: If this is your first time using internet in Kaggle, Kaggle may ask for a quick SMS phone verification.*
3. **Environment**:
   - `Always use latest environment` (Default).

---

## 📊 Step 3: Dataset Acquisition (Real LMD-2023 Telemetry)

The authentic LMD-2023 dataset is peer-reviewed research telemetry containing **1.75 million Sysmon event logs** (1.07 GB uncompressed CSV).

The notebook automatically handles downloading and extracting it from the official Google Drive repository:
```bash
# Downloads official archives
!gdown --folder "https://drive.google.com/drive/folders/1PkJiGpD0Kn1rV8GC9m2b_eWvqQTSa1eH?usp=sharing" -O data/

# Uncompresses the nested RAR archives
!unrar x -o+ "data/Lateral-Movement-Dataset--LMD_Collections/LMD-2023/LMD-2023.rar" data/
!unrar x -o+ "data/LMD-2023 [1.75M Elements].rar" data/

# Activates the authentic 1.75M Sysmon CSV
!cp "data/LMD-2023 [1.75M Elements]/LMD-2023 [1.75M Elements] Checked/Labelled LMD-2023/LMD-2023 [1.75M Elements][Labelled]checked.csv" data/lmd_2023_dataset.csv
```

---

## 🏋️ Step 4: Execute the Pipeline

Run the notebook cells sequentially:

1. **Stream A (LSA - DeBERTa-v3-small)**:
   - Detects MITRE ATT&CK TA0008 lateral movement (EoRS, EoHT) using Supervised Contrastive Loss.
   - `python scripts/train_edgeshield_lsa.py --model_name "microsoft/deberta-v3-small" --device cuda --num_samples 12000`
2. **Stream B (BPD - DistilBERT)**:
   - Evaluates multi-event ransomware behavior sequences (T1490, T1562.001, T1486) with the Attention Threat Scoring Head.
   - `python scripts/train_edgeshield_bpd.py --device cuda --num_samples 8000`
3. **Tier 2 (Qwen2.5-1.5B LoRA / QLoRA)**:
   - Fine-tunes the generative reasoner to emit structured JSON incident alerts.
   - Thanks to Kaggle's 30GB RAM, this executes without any memory bottleneck.
4. **ONNX FP32 & INT8 Dynamic Quantization**:
   - `python scripts/export_onnx.py --checkpoint models/edgeshield_lsa_deberta --quantize`
   - `python scripts/benchmark_onnx.py --model models/onnx_edgeshield/edgeshield_lsa_int8.onnx`

---

## 💾 Step 5: Download Artifacts

Run the final cell:
```python
!zip -r /kaggle/working/edgeshield_trained_models.zip models/ benchmark_results.json
```
On the right-hand panel, go to **Output** $\rightarrow$ click the three dots next to `edgeshield_trained_models.zip` $\rightarrow$ **Download**.
