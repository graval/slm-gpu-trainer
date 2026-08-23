# Specification: Datasets, Schemas & Benchmark Evaluations

## 1. Primary Datasets

### A. LMD-2023 (`data/lmd_2023_dataset.csv`)
* **Source**: Authentic peer-reviewed Windows host Lateral Movement benchmark dataset.
* **Volume**: Over 1,000,000 Sysmon security events.
* **Threat Classes**:
  * `0`: Normal / Benign Traffic
  * `1`: Exploitation of Remote Services (EoRS - PsExec, WMI)
  * `2`: Exploitation of Hashing Techniques (EoHT - Pass-the-Hash, Mimikatz)
* **Sampling Strategy**: Class-balanced downsampling (benign sampled at max $2 \times (\text{malicious}_1 + \text{malicious}_2)$) to prevent the majority class trap.

### B. DARPA OpTC Benchmark (`data/optc_test_benchmark.csv`)
* **Source**: Synthesized from DARPA Operationally Transparent Cyber (OpTC) red team evaluation logs and eCAR host event schema.
* **Purpose**: Out-of-Distribution (OOD) testing to evaluate generalization beyond laboratory training data.
* **Characteristics**: Contains dual-use administrative commands (`taskhostw.exe`, `smartscreen.exe`, obfuscated PowerShell, DCOM).
* **Generator Utility**: `scripts/prepare_optc_benchmark.py`

---

## 2. Dynamic Path Resolution Contract (`resolve_dataset_path`)
All loaders and evaluators implement `resolve_dataset_path(csv_path)` which searches:
1. `csv_path` as-is (exact path)
2. `<project_root>/data/<filename>`
3. `<project_root>/external/<filename>`
4. `<project_root>/scratch/<filename>`
5. `/app/external/<filename>` & `/app/data/<filename>` (inside Docker)

---

## 3. Benchmark Evaluation Metrics
* **Accuracy**: Overall classification correctness across all test events.
* **Macro F1-Score**: Unweighted mean of per-class F1-scores ($\frac{F1_0 + F1_1 + F1_2}{3}$).
* **False Positive Rate (FPR)**: Percentage of benign events incorrectly classified as Class 1 or 2.
* **False Negative Rate (FNR)**: Percentage of lateral movement attacks missed (classified as Class 0).
* **Latency**: Average inference time per sample in milliseconds.
