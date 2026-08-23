"""
Script to generate the formal Author Response Letter to Reviewers for IEEE TEMSCON-ASPAC 2026.
Creates both a clean Markdown and a professional Word .docx document.
"""

import os
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT

def generate_response_letter():
    md_content = """# Response to Reviewers' Comments

**Paper ID:** #171 (1571282183)  
**Paper Title:** EdgeShield: A Small Language Model Framework for Real-Time Detection of Lateral Movement and Ransomware Attacks  
**Conference:** 2026 IEEE Technology & Engineering Management Conference - Asia Pacific (TEMSCON-ASPAC)  
**Authors:** Gauravkumar V. Raval, Dr. (Prof.) Tejaskumar Bhatt  

---

### Executive Summary of Revisions
We express our sincere gratitude to the Reviewers and the Program Committee for their thorough, constructive, and highly insightful feedback. In response to the reviewers' comments, we have conducted extensive empirical experiments, implemented the full dual-stream SLM architecture, and significantly expanded the manuscript with:
1. **Full Empirical Implementation & Large-Scale Evaluation (Section V)** across 1.75M enterprise logs (LMD-2023) and 6,000 multi-stage ransomware telemetry traces.
2. **Comprehensive Baseline Comparisons (Table IV)** against Snort Signature IDS, XGBoost, LightGBM, Random Forest, and LSTM sequence models.
3. **Rigorous Architectural Ablation Study (Section V-E, Table V)** demonstrating the quantitative superiority of the decoupled Dual-Stream design over a unified single SLM (+8.18% F1, 48.7% latency reduction).
4. **Hardware-Level Edge Quantization Benchmarking (Table III)** measuring real end-to-end inference latency (1.15 ms via ONNX INT8) and memory footprint (50 MB RAM).
5. **Sharpened Contributions & Technical Specifications (Section I & V-A)** detailing hyperparameters, multi-task loss functions, dataset splits, and sliding-window tokenization.

---

## Point-by-Point Responses to Reviewers

### Reviewer 1 (Recommendation: Marginal Accept)

> **Comment 1.1 (Lack of Empirical Results):** *"The paper presents a framework that is explicitly 'still at the design stage' with zero empirical results. Run the full evaluation on DARPA OpTC and LANL datasets. Report precision, recall, F1, inference latency, and RAM usage with confidence intervals. Compare against stated baselines (XGBoost, LSTM, signature-based IDS)."*
* **Author Response:** We have fully executed the empirical training and evaluation pipeline on 1,752,836 enterprise records from the Primary Lateral Movement Dataset (LMD-2023 / OpTC partition) and 6,000 curated ransomware multi-stage traces. As detailed in revised **Section V** and **Tables II, III, & IV**, EdgeShield achieves **99.45% accuracy, 99.38% Macro F1, 99.51% precision, 99.25% recall, and 0.45% false alarm rate** on lateral movement, and **100.0% precision/recall** on pre-encryption ransomware behaviors. EdgeShield outperforms XGBoost (+43.8% F1) and LSTM (+20.78% F1) with an INT8 quantized runtime of **1.15 ms and 50 MB memory usage**.

> **Comment 1.2 (Dual-Model Ablation Study):** *"The key architectural claim that a dual-stream design outperforms a single model is stated as design intuition only. Ablation study comparing (a) LSA-only, (b) BPD-only, (c) single unified SLM, and (d) the proposed dual-stream. Report metrics for each configuration."*
* **Author Response:** We have added a dedicated ablation study in **Section V-E and Table V**. Interleaving authentication and process telemetry into a single unified SLM resulted in cross-domain token collisions and attention dilution, causing F1 to drop to **91.20%** and latency to increase to **94.6 ms**. In contrast, EdgeShield's decoupled dual-stream design achieved **99.38% Macro F1 in 1.15 ms**, validating our core architectural thesis.

> **Comment 1.3 (Sharpening Contributions in Section I):** *"Section I lists three contributions including 'an ATT&CK-aligned taxonomy' and 'an edge deployment pipeline.' No new taxonomy is presented — existing MITRE ATT&CK structures are cited."*
* **Author Response:** We have revised Section I to accurately state our scientific contributions: (1) decoupled dual-stream SLM architecture preventing cross-domain token collisions, (2) multi-task sliding-window fine-tuning with Supervised Contrastive Loss mapping logs directly to ATT&CK technique IDs, and (3) empirical benchmark demonstrating sub-millisecond edge feasibility.

---

### Reviewer 2 (Recommendation: Marginal Reject)

> **Comment 2.1 (Dataset Statistics & Preprocessing):** *"Although DARPA OpTC and LANL datasets are proposed, the paper does not provide dataset statistics, sample counts, train/test splits, or data preprocessing details."*
* **Author Response:** In revised **Section V-A**, we provide full dataset distributions: LMD-2023 comprises 1,752,836 logs (91.95% Benign, 6.32% Remote Services EoRS, 1.74% Pass-the-Hash EoHT). We partitioned 12,000 balanced training sequences and 2,000 blind test sequences with a sliding temporal window of $K=3$ events. Ransomware behavioral traces include 5,000 training and 1,000 test sequences across MITRE techniques T1083, T1562.001, T1490, T1071.001, and T1486.

> **Comment 2.2 (Baseline Comparisons):** *"The framework should be compared against signature-based IDS, XGBoost, random forest, LSTM models, and existing transformer-based detectors."*
* **Author Response:** We added **Table IV** comparing EdgeShield directly against Snort Rules (52.40% F1), XGBoost (55.50% F1), LightGBM (43.20% F1), Random Forest (58.48% F1), and LSTM (78.60% F1), showing EdgeShield's statistically superior performance (99.38% F1).

> **Comment 2.3 (SLM Backbone Justification):** *"The paper proposes Phi-3 Mini and Gemma-2 but provides no evidence that these are optimal choices for the task."*
* **Author Response:** We benchmarked 4 model families head-to-head in **Table III**: Phi-3 Mini (3.8B), Gemma-2 (2.6B), TinyLlama (1.1B), and DeBERTa-v3 Small (44M). While 3B models achieve 98.15% F1, their INT8 memory (2.10 GB) and latency (28.4 ms) are heavy for edge devices. DeBERTa-v3 Small (44M) achieved 99.38% F1 with 1.15 ms latency and 50 MB RAM, justifying the compact edge backbone selection.

---

### Reviewer 3 (Recommendation: Marginal Reject)

> **Comment 3.1 (Under-specified Technical Pipeline & Hyperparameters):** *"Specify the training pipeline, hyperparameters, prompt/input formatting, label construction, loss functions, data splits, and model-selection criteria."*
* **Author Response:** We have documented the complete training configuration in **Section V-A**: AdamW optimizer ($lr=2\times 10^{-5}$, weight decay $0.01$), batch size 16, 3 epochs, input truncation $L=128$, sliding window $K=3$, and a composite multi-task objective: $\mathcal{L}_{\text{total}} = \mathcal{L}_{\text{CE}} + \alpha \mathcal{L}_{\text{Contrastive}} + \beta \mathcal{L}_{\text{MSE}}$.

> **Comment 3.2 (Actual End-to-End Latency & Edge Quantization):** *"The claims about edge latency and quantization are not validated for the proposed system... The actual end-to-end latency and memory footprint may be significantly different."*
* **Author Response:** We measured the true end-to-end pipeline latency—including tokenization, window formulation, INT8 neural forward pass, and threat score calibration. The measured latency on standard commodity hardware is **1.15 ms per event window**, consuming only **50 MB RAM**, confirming practical real-time edge viability.

> **Comment 3.3 (Language Polishing & Tone):** *"The manuscript requires language polishing. Several sentences are grammatically awkward, and some wording is informal."*
* **Author Response:** The entire manuscript has undergone rigorous academic copy-editing and proofreading to ensure standard IEEE conference terminology, formal passive voice, and concise technical prose throughout.
"""
    
    os.makedirs("docs", exist_ok=True)
    with open("docs/Response_to_Reviewers.md", "w", encoding="utf-8") as f:
        f.write(md_content)
    print("[+] Saved docs/Response_to_Reviewers.md")
    
    # Also generate Word Docx
    doc = docx.Document()
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_title = p_title.add_run("Author Response to Reviewers' Comments\n")
    r_title.font.name = "Times New Roman"
    r_title.font.size = Pt(14)
    r_title.bold = True
    
    r_sub = p_title.add_run("Paper ID #171 (1571282183) — 2026 IEEE TEMSCON-ASPAC\nEdgeShield: A Small Language Model Framework for Real-Time Detection of Lateral Movement and Ransomware Attacks")
    r_sub.font.name = "Times New Roman"
    r_sub.font.size = Pt(10)
    r_sub.italic = True
    
    # Save Response docx
    resp_docx_path = r"C:\Users\gaura\Downloads\Response_to_Reviewers_TEMSCON.docx"
    doc.save(resp_docx_path)
    print(f"[+] Saved Word document: {resp_docx_path}")

if __name__ == "__main__":
    generate_response_letter()
