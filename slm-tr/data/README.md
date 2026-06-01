# LMD-2023 Benchmark Threat Telemetry Data Folder

This directory contains the telemetry loaders, processed feature files, and instructions for managing the LMD-2023 dataset utilized to train the lateral movement SLMs.

---

## 📂 Data Directory Architecture

```
data/
├── loader.py              <-- Custom dataset loading, normalization, and balance pipeline
├── covenant_winrm.json     <-- Raw Sysmon JSON events (Credential Harvesting / WinRM Abuse)
├── covenant_wmi.json       <-- Raw Sysmon JSON events (WMI process executions / admin shares)
├── lmd_2023_dataset.csv   <-- Mapped and normalized CSV dataset (1.07 GB raw CSV file)
└── README.md              <-- This document
```

---

## 📊 Dataset Specifications & Features

The fine-tuning pipelines expect a labeled CSV dataset containing host security event telemetry. The peer-reviewed **LMD-2023** standard features are processed using the following schema:

1. **`Image`** *(e.g. `C:\Windows\System32\cmd.exe`)*: The full executable path executed.
2. **`CommandLine`** *(e.g. `wmic.exe /node:target process call create ...`)*: The command line arguments.
3. **`ParentImage`**: Executable path of parent trigger process.
4. **`User`**: Security context under which process was spawned (NT AUTHORITY\SYSTEM, DOMAIN\admin, etc.).
5. **`Label`**: Mapped classification target:
   - **`0` (Normal)**: Legitimate background OS operations, admin scripts, standard workflows.
   - **`1` (EoRS)**: Exploitation of Remote Services (Remote admin shares mapping, PSEXEC service launches, WMI remote spawns).
   - **`2` (EoHT)**: Exploitation of Hashing Techniques (Credential dumping, dumping LSASS memory via mini-dump DLLs, Pass-the-Hash manipulations).

---

## 🔄 Dynamic Balanced Downsampling (`loader.py`)

Sysmon security logs in enterprise environments are highly imbalanced, containing over 99% benign logs. Training models directly on raw logs leads to heavy classification bias and high false-negative rates for lateral movement.

To solve this, our custom dataset loader [loader.py](file:///c:/workspaceag/slmgpuv1/slm-tr/data/loader.py) automatically implements **balanced class downsampling**:
- Legitimate events (Class 0) are randomly downsampled to balance the active malicious target classes (Class 1 & 2).
- The dynamic loader formats the features into a single unified prompt layout (explainable textual representation) prior to tokenization:
  ```
  Event ID: 1 | Process Image: <Image> | CLI: <CommandLine> | Parent Image: <ParentImage> | Executed User: <User>
  ```

---

## 🛠️ Dataset Recovery

If `lmd_2023_dataset.csv` is missing from this directory, you can restore it using our automated setup script:
```powershell
# In PowerShell:
.\.venv\Scripts\python scripts/setup_dataset.py
```
This script downloads Empire and Covenant adversarial log telemetry and benign active directory baseline logs and compiles a balanced CSV dataset.

> **Note**: Standard raw `.csv` and `.json` telemetry datasets are excluded from Git version tracking via `.gitignore` to keep repository size lean. Checking in the python loaders and dataset configurations is highly recommended.
