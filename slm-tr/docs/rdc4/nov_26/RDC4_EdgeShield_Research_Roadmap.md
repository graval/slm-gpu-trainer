# RDC-4 Doctoral Research Direction & Experiment Tracking: EdgeShield 2.0

**Milestone:** Research Advisory Committee Review 4 (RDC-4 / 2.0 Years)  
**Period:** November 2026 – April 2027  
**Candidate:** Gauravkumar Raval (GLS University)  
**Supervisor:** Dr. Tejaskumar Bhatt  
**Target Venue:** IEEE Transactions on Dependable and Secure Computing (TDSC) / IEEE Transactions on Information Forensics and Security (TIFS) / Elsevier Computers & Security  
**Preceding Milestone:** RDC-3 Completed (October 2026) | IEEE TEMSCON-ASPAC 2026 Conference Paper Accepted & Presented  

---

## 1. Executive Context & The "Why" of RDC-4

At RDC-3, the EdgeShield framework demonstrated the architectural viability of deploying dual decoupled Small Language Models (DeBERTa-v3-small for Log Semantic Analysis and DistilBERT for Behavioral Pattern Detection) with sub-15ms INT8 quantized latency on commodity CPUs.

However, transitioning from a conference milestone to a **doctoral thesis defense and Q1 journal publication** requires confronting three fundamental methodological challenges identified in our November 2026 audit:

```
+---------------------------------------------------------------------------------------------------+
|                                      THE RDC-4 STRATEGIC PIVOT                                    |
+-----------------------------------+---------------------------------------------------------------+
| RDC-3 Conference Scope            | RDC-4 Journal / Doctoral Dissertation Scope                   |
+-----------------------------------+---------------------------------------------------------------+
| Stratified random train/val split | Strict chronological 70/10/20 train/val/test partitioning      |
| Balanced downsampled subsets      | Natural prevalence evaluation on raw continuous telemetry      |
| Synthetic BPD traces              | Authentic RADAR multi-family ransomware dataset (413k events) |
| Post-encryption detection         | Prospective early warning (lead-time Delta t before T1486)    |
| Single-stream ONNX profiling      | Concurrent dual-stream throughput & tiered selective gating   |
+-----------------------------------+---------------------------------------------------------------+
```

---

## 2. Formal Research Questions & Hypotheses

* **RQ1 (Temporal Generalization & Rare-Class Robustness):** Does fine-tuning a compact Transformer (DeBERTa-v3-small) on authentic Sysmon telemetry using Supervised Contrastive Loss retain minority-class recall (`EoHT`) when tested on temporally future runs and external environments (Windows-APT 2025 v4), compared to LightGBM, Random Forest, and CNN-BiLSTM baselines?
  * *Null Hypothesis $H_{1,0}$:* DeBERTa achieves no statistically significant improvement in $\text{Recall}_{\text{EoHT}}$ at a fixed false positive budget ($\text{FPR} \le 0.1\%$) compared to LightGBM with 3-event temporal lags.
  * *Alternative Hypothesis $H_{1,1}$:* The semantic attention head in DeBERTa captures cross-event contextual anomalies that yield $\ge 15\%$ higher $\text{Recall}_{\text{EoHT}}$ at $\text{FPR} \le 0.1\%$.

* **RQ2 (Prospective Pre-Encryption Early Warning):** On continuous ransomware telemetry (RADAR benchmark), what is the empirical lead-time distribution ($\Delta t_{\text{alert}} = t_{\text{encryption}} - t_{\text{alert}}$) achieved by the Behavioral Pattern Detector when restricted strictly to pre-encryption prefix windows?
  * *Hypothesis:* BPD flags precursor behaviors (shadow copy deletion T1490, security tool disabling T1562.001) with a positive mean lead-time $\Delta t \ge 5.0\text{ seconds}$ before irreversible encryption ($T1486$) commences on $\ge 80\%$ of unseen ransomware incidents.

* **RQ3 (Resource-Constrained Selective Inference):** Does a tiered hybrid inference pipeline (lightweight Event-ID/entropy gate $\rightarrow$ selective SLM sequence inference) sustain $\ge 500$ events/sec on constrained commodity hardware while reducing mean CPU duty cycle by $\ge 60\%$ compared to always-on Transformer inference?

---

## 3. Dataset Matrix & Provenance Integrity

| Dataset Identifier | Telemetry Type | Verified Elements | Role in RDC-4 | Verification / Provenance Link |
| :--- | :--- | :--- | :--- | :--- |
| **LMD-2023** (Smiliotopoulos et al.) | Windows Sysmon EVTX & CSV | 1,752,890 events (1.07 GB CSV) | Primary Lateral Movement benchmark for Stream A (LSA) | [DOI: 10.1007/s10207-023-00725-8](https://doi.org/10.1007/s10207-023-00725-8) |
| **Windows-APT 2025 (v4)** | Wazuh & Sysmon host logs | 36 emulated APT scenarios | External zero-shot OOD evaluation | [Mendeley Data v4](https://data.mendeley.com/datasets/b8fmtzvpy8/4) |
| **RADAR 2025** (Springer) | Continuous Sysmon traces | 413,556 events (7 families) | Primary Early Warning benchmark for Stream B (BPD) | [DOI: 10.1186/s42400-025-00435-9](https://doi.org/10.1186/s42400-025-00435-9) |
| **DARPA OpTC / Corrected** | Host flow & endpoint logs | Enterprise host telemetry | Secondary noise injection benchmark | [DOI: 10.57745/UXCWOC](https://doi.org/10.57745/UXCWOC) |

---

## 4. Cloud Infrastructure Strategy: Kaggle & Colab Allocation

* **Kaggle Notebooks (Primary Workhorse)**:
  * **Quota**: 30.0 / 30 hours per week (NVIDIA Dual Tesla T4 x 2 — 32 GB aggregate VRAM).
  * **Memory**: 30.0 GB System RAM (Essential for handling 1.07 GB CSV without Pandas OOM).
  * **Execution Mode**: **Headless Batch ("Save & Run All")** to eliminate 20-minute interactive idle timeouts.
* **Google Colab (Secondary Prototyping)**:
  * **Role**: Fast smoke testing, DirectML/CUDA side-by-side latency checks, ONNX export verification, and Drive syncing.

---

## 5. Experiment Manifest & Tracking Ledger (Nov 2026)

| Run ID | Date | Target Component | Dataset & Split | Platform & Hardware | Target Metric / Decision Gate | Outcome & Notes |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `EXP-RDC4-001` | 2026-11-18 | Pipeline Ingestion & Multi-Stream Baseline (Version 3) | LMD-2023 (1.75M) + Mordor Baseline | Kaggle (Dual Tesla T4 x2, 30GB RAM) | Verify 1.75M rows loaded without OOM; clean multi-stream execution | **PASSED (Run in 653.9s)**. BPD loss converged from 3.4509 -> 0.0004. LSA DeBERTa-v3 completed 3 epochs (acc 56.54%, macro recall 33.33%, class 0 F1 0.7224). Exported ONNX & generated `edgeshield_trained_models.zip` (1.41 GB, total output 5.33 GB). Directly validates doctoral audit hypothesis regarding rare-class (`EoHT`) challenge under real sequences. |
| `EXP-RDC4-002` | 2026-11-20 | Stream A (LSA) | LMD-2023 Chronological | Kaggle (DeBERTa-v3-small) | $\text{Recall}_{\text{EoHT}} \ge 0.65$ @ $\text{FPR} \le 0.1\%$ | *Scheduled* |
| `EXP-RDC4-003` | 2026-11-23 | Stream B (BPD) | RADAR Sysmon | Kaggle (DistilBERT Sequence) | Lead-time $\Delta t \ge 5\text{s}$ before T1486 on $\ge 80\%$ runs | *Scheduled* |
| `EXP-RDC4-004` | 2026-11-26 | Selective Gating | LMD + Replay | Local CPU / Colab | Sustained throughput $\ge 500\text{ EPS}$; CPU $\le 25\%$ | *Scheduled* |

---

## 6. Directory Layout & Artifacts

All ongoing RDC-4 artifacts are systematically isolated under:
* `slm-tr/docs/rdc4/nov_26/`: Core research roadmaps, experiment summaries, and LaTeX draft sections.
* `rdc4/nov_26/`: Root-level quick access and tracking symlinks.
* `models/rdc4/`: Versioned model checkpoints tagged with `[RDC4-NOV2026]`.
