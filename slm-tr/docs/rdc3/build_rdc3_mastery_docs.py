"""
build_rdc3_mastery_docs.py
Generates the comprehensive Word document (DOCX) and converts to PDF if possible.
RDC3_Defense_Mastery_Guide.docx
"""

import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

def set_cell_background(cell, hex_color):
    shading_elm = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    cell._tc.get_or_add_tcPr().append(shading_elm)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def add_styled_heading(doc, text, level):
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.font.name = 'Calibri'
    r.font.bold = True
    if level == 1:
        r.font.size = Pt(17)
        r.font.color.rgb = RGBColor(15, 23, 42)
        p.space_before = Pt(18)
        p.space_after = Pt(6)
    elif level == 2:
        r.font.size = Pt(13.5)
        r.font.color.rgb = RGBColor(30, 41, 59)
        p.space_before = Pt(12)
        p.space_after = Pt(4)
    elif level == 3:
        r.font.size = Pt(11.5)
        r.font.color.rgb = RGBColor(71, 85, 105)
        p.space_before = Pt(8)
        p.space_after = Pt(2)
    return p

def add_body_p(doc, text, bold_prefix="", italic_suffix=""):
    p = doc.add_paragraph()
    p.space_after = Pt(5)
    p.line_spacing = 1.15
    if bold_prefix:
        r_b = p.add_run(bold_prefix)
        r_b.font.name = 'Calibri'
        r_b.font.size = Pt(10.5)
        r_b.font.bold = True
        r_b.font.color.rgb = RGBColor(15, 23, 42)
    r_t = p.add_run(text)
    r_t.font.name = 'Calibri'
    r_t.font.size = Pt(10.5)
    r_t.font.color.rgb = RGBColor(30, 41, 59)
    if italic_suffix:
        r_i = p.add_run(italic_suffix)
        r_i.font.name = 'Calibri'
        r_i.font.size = Pt(10.5)
        r_i.font.italic = True
        r_i.font.color.rgb = RGBColor(71, 85, 105)
    return p

def add_callout(doc, text, title="KEY DEFENSE TAKEAWAY"):
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = tbl.cell(0, 0)
    set_cell_background(cell, "F1F5F9")
    set_cell_margins(cell, top=140, bottom=140, left=200, right=200)
    
    p = cell.paragraphs[0]
    p.space_after = Pt(2)
    r_head = p.add_run(f"📌 {title}: ")
    r_head.font.name = 'Calibri'
    r_head.font.size = Pt(10)
    r_head.font.bold = True
    r_head.font.color.rgb = RGBColor(15, 23, 42)
    
    r_txt = p.add_run(text)
    r_txt.font.name = 'Calibri'
    r_txt.font.size = Pt(10)
    r_txt.font.color.rgb = RGBColor(51, 65, 85)
    doc.add_paragraph().space_after = Pt(4)

def format_table(tbl, col_widths, headers, data):
    # Set headers
    hdr_cells = tbl.rows[0].cells
    for i, h_txt in enumerate(headers):
        hdr_cells[i].text = h_txt
        p = hdr_cells[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        r = p.runs[0]
        r.font.name = 'Calibri'
        r.font.size = Pt(9.5)
        r.font.bold = True
        r.font.color.rgb = RGBColor(255, 255, 255)
        set_cell_background(hdr_cells[i], "1E293B")
        set_cell_margins(hdr_cells[i], top=100, bottom=100, left=120, right=120)

    # Set data rows
    for r_idx, row_vals in enumerate(data):
        row_cells = tbl.rows[r_idx + 1].cells
        bg_col = "F8FAFC" if r_idx % 2 == 1 else "FFFFFF"
        for c_idx, val in enumerate(row_vals):
            row_cells[c_idx].text = str(val)
            p = row_cells[c_idx].paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            if p.runs:
                r = p.runs[0]
                r.font.name = 'Calibri'
                r.font.size = Pt(9)
                r.font.color.rgb = RGBColor(30, 41, 59)
                if c_idx == 0:
                    r.font.bold = True
            set_cell_background(row_cells[c_idx], bg_col)
            set_cell_margins(row_cells[c_idx], top=80, bottom=80, left=120, right=120)

    # Apply column widths
    for row in tbl.rows:
        for i, w in enumerate(col_widths):
            row.cells[i].width = Inches(w)

def generate_doc():
    doc = docx.Document()
    for s in doc.sections:
        s.top_margin = Inches(0.8)
        s.bottom_margin = Inches(0.8)
        s.left_margin = Inches(0.8)
        s.right_margin = Inches(0.8)

    # Document Header
    p_title = doc.add_paragraph()
    r_title = p_title.add_run("Research Defense & Mastery Companion: EdgeShield (RDC 3)")
    r_title.font.name = 'Calibri'
    r_title.font.size = Pt(22)
    r_title.font.bold = True
    r_title.font.color.rgb = RGBColor(15, 23, 42)
    p_title.space_after = Pt(2)

    p_sub = doc.add_paragraph()
    r_sub = p_sub.add_run("Doctoral Progress Review Milestone (1.5 Years Progress) | GLS University, Ahmedabad\nCandidate: Gauravkumar Raval | Supervisor: Prof. Dr. Tejas Bhatt | Topic: Resource-Efficient AI for Threat Detection in Edge Systems\nAccepted Paper: 5th IEEE TEMSCON-ASPAC 2026 (Paper ID: #1571282183)")
    r_sub.font.name = 'Calibri'
    r_sub.font.size = Pt(10)
    r_sub.font.italic = True
    r_sub.font.color.rgb = RGBColor(71, 85, 105)
    p_sub.space_after = Pt(14)

    # -------------------------------------------------------------
    # SECTION 1: DOCTORAL TRAJECTORY
    # -------------------------------------------------------------
    add_styled_heading(doc, "1. Doctoral Progression & Strategic Defense Positioning", 1)
    add_body_p(doc, "In a 3rd Doctoral Committee Review (Month 18 milestone), examiners look for clear evidence that the candidate can formulate a rigorous problem, respond to prior feedback, execute reproducible experiments, and achieve peer-reviewed validation.")
    
    t1_headers = ["Milestone", "Core Paradigm / Proposed Scope", "Key Committee Feedback", "Tangible Deliverable Achieved"]
    t1_data = [
        ["RDC 1 (M6)", "Broad AI threat defense in Smart Mfg (Federated Learning + CNN-LSTM-MLP)", "Narrow scope to a single vector; eliminate broad claims; identify specialized datasets.", "Comprehensive literature survey & threat taxonomy."],
        ["RDC 2 (M12)", "Focused pivot to Lateral Movement (LM) via Small Language Models (SLMs)", "1. Broaden title at this stage.\n2. Audit dataset labeling integrity.\n3. Model multi-stage attack scenarios.", "Selected LMD-2023 & LANL; preliminary tokenization design."],
        ["RDC 3 (M18)", "EdgeShield: Decoupled Dual-Stream SLM with INT8 Quantization & ATT&CK Graph", "Demonstrate empirical models, baseline ablation, edge latency proof, and peer review.", "1. Accepted IEEE TEMSCON 2026 paper.\n2. Verified 11.71 ms INT8 edge latency.\n3. 99.38% Macro F1 over 1.75M logs.\n4. Extended journal draft."]
    ]
    t1 = doc.add_table(rows=len(t1_data)+1, cols=4)
    format_table(t1, [1.2, 2.0, 2.0, 1.8], t1_headers, t1_data)
    doc.add_paragraph().space_after = Pt(6)

    # -------------------------------------------------------------
    # SECTION 2: CORE CONCEPTS & LOGIC
    # -------------------------------------------------------------
    add_styled_heading(doc, "2. Core Architectural Concepts & System Logic", 1)
    add_body_p(doc, "Traditional cloud-hosted LLMs (GPT-4, Claude 3.5, LLaMA-70B) cannot be deployed in manufacturing environments due to the 'Privacy Paradox': factory telemetry contains proprietary CAD designs, PLC program timings, and internal network topographies that cannot leave the network perimeter.", "The Privacy Paradox: ")
    add_body_p(doc, "Fine-tuning compact models (44M DeBERTa-v3 / 66M DistilBERT) allows 100% on-premise execution directly on industrial PCs and multi-core edge servers, achieving 11.71 ms inference latency within a 50 MB RAM budget.", "Edge SLM Feasibility: ")
    
    add_callout(doc, "Feeding authentication logs (discrete, relational) and file-system logs (bursty, high-frequency) into a single unified SLM causes cross-domain token collisions, dropping Macro F1 from 99.38% to 91.20% and doubling latency. Decoupling into Stream A (LSA) and Stream B (BPD) resolves this semantic interference.", "WHY DECOUPLED DUAL-STREAM WINS")

    add_body_p(doc, "Operates over a 512-token sliding ring buffer of K=3 consecutive Windows events (4624, 4625, 4648, 4672, Kerberos) using a 44M DeBERTa-v3 encoder to classify Normal vs. Exploitation of Remote Services (EoRS: PsExec/WMI) vs. Exploitation of Hashing (EoHT: Pass-the-Hash).", "Stream A (Log Semantic Analyzer - LSA): ")
    add_body_p(doc, "Monitors file renames, shadow copy deletion (T1490), and defense impairment (T1562.001) using a 2,000-token ATT&CK vocabulary head to emit pre-encryption alerts before file encryption APIs (T1486) activate.", "Stream B (Behavioral Pattern Detector - BPD): ")
    add_body_p(doc, "Fuses Stream A and B detections across a 300-second window into cohesive MITRE ATT&CK v15 incident graphs, employing KNN collaborative filtering to forecast the adversary's next 3 most probable techniques.", "Layer 3 (ATT&CK Correlation Engine): ")

    # -------------------------------------------------------------
    # SECTION 3: MATHEMATICAL FOUNDATIONS
    # -------------------------------------------------------------
    add_styled_heading(doc, "3. Mathematical Foundations & Training Objectives", 1)
    add_body_p(doc, "Evaluating event logs in isolation (K=1) fails because administrative tools (e.g. wmic.exe process call create) are syntactically identical in benign maintenance and malicious intrusions. EdgeShield frames telemetry in a sliding window ring buffer of K=3 consecutive events: W_t = [e_{t-2}, e_{t-1}, e_t]. Preceding events (Network connection over port 445 -> Named pipe creation \\pipe\\psexec -> Process creation PSEXESVC.exe) provide the context needed to reduce False Positives from 2.00% to 0.40%.", "Sliding-Window Ring Buffer (K>=3): ")
    add_body_p(doc, "Unlike traditional transformers that sum content and position vectors, DeBERTa-v3 computes attention over disentangled content and relative-position matrices: A_{i,j} = c_i*c_j^T + c_i*p_{j|i}^T + p_{i|j}*c_j^T. This captures how relative token positions (e.g., an unmanaged source IP appearing near LogonType 3) signal privilege escalation.", "Disentangled Attention: ")
    add_body_p(doc, "Tier 1 is optimized using a joint multi-task objective combining Cross-Entropy with Supervised Contrastive Loss (SupCon): L_total = L_CE + 0.30 * L_SCL. SupCon explicitly pulls representations of identical attack techniques together while repelling routine sysadmin sessions by scaling with temperature tau = 0.07.", "Joint Contrastive Objective: ")

    # -------------------------------------------------------------
    # SECTION 4: EMPIRICAL BENCHMARKS
    # -------------------------------------------------------------
    add_styled_heading(doc, "4. Empirical Benchmarks & Hardware Profiling", 1)
    
    add_styled_heading(doc, "A. Baseline Accuracy Comparison (N=2,000 Blind Test Sequences)", 2)
    t2_headers = ["Defense Approach", "Macro F1", "Precision", "Recall", "Core Operational Limitation / Advantage"]
    t2_data = [
        ["Signature IDS (Snort Rules)", "52.40%", "91.20%", "36.80%", "Fails on LOLBins and command-line obfuscation; poor recall."],
        ["XGBoost Classifier", "55.50%", "58.20%", "53.10%", "Lacks sequential context across multi-event sliding windows."],
        ["LightGBM Classifier", "43.20%", "48.60%", "38.90%", "Gradient boosted trees suffer high false alarms on admin tools."],
        ["Random Forest Baseline", "58.48%", "58.49%", "58.50%", "Standard bag-of-words framing fails on dynamic pivoting."],
        ["LSTM Sequence Model", "78.60%", "81.40%", "76.00%", "RNN recurrent state struggles with long-range log dependencies."],
        ["EdgeShield Dual-Stream SLM", "99.38%", "99.51%", "99.25%", "+20.78 pp F1 gain over LSTM; zero missed attacks across test set."]
    ]
    t2 = doc.add_table(rows=len(t2_data)+1, cols=5)
    format_table(t2, [1.5, 0.8, 0.8, 0.8, 3.1], t2_headers, t2_data)
    doc.add_paragraph().space_after = Pt(6)

    add_styled_heading(doc, "B. 5-Trial Statistical Edge Latency Benchmark (N=1,000 Evaluations)", 2)
    add_body_p(doc, "Conducted over 5 independent trials x 200 consecutive forward passes on an 8-thread CPU with ONNX Runtime Dynamic INT8 Quantization:")
    t3_headers = ["Model Architecture", "Parameters", "Mean Latency", "p95 Latency", "Throughput", "RAM Footprint"]
    t3_data = [
        ["Phi-3 Mini (Instruct) CPU", "3.8B", "142.50 ms", "154.60 ms", "7.0 win/s", "4.80 GB"],
        ["Phi-3 Mini (Instruct) INT8", "3.8B", "28.40 ms", "31.50 ms", "35.2 win/s", "2.10 GB"],
        ["Gemma-2 IT (INT8)", "2.6B", "21.60 ms", "24.10 ms", "46.3 win/s", "1.50 GB"],
        ["TinyLlama Chat (INT8)", "1.1B", "9.80 ms", "11.20 ms", "102.0 win/s", "0.70 GB"],
        ["EdgeShield LSA (FP32 CPU)", "44M", "27.84 ms", "36.88 ms", "35.9 win/s", "185 MB"],
        ["EdgeShield LSA (INT8 ONNX)", "44M", "11.71 ± 0.62 ms", "12.72 ms", "85.4 win/s", "50 MB (0.05 GB)"]
    ]
    t3 = doc.add_table(rows=len(t3_data)+1, cols=6)
    format_table(t3, [1.8, 0.8, 1.2, 1.0, 1.1, 1.1], t3_headers, t3_data)
    doc.add_paragraph().space_after = Pt(6)

    # -------------------------------------------------------------
    # SECTION 5: VIVA & DEFENSE QUESTIONS
    # -------------------------------------------------------------
    add_styled_heading(doc, "5. Anticipated Viva & Defense Examination Questions", 1)
    
    qa_list = [
        ("Q1: Why did you choose DeBERTa-v3 Small over DistilBERT, RoBERTa, or a decoder like GPT-2?",
         "DeBERTa-v3 decouples content and relative position matrices. In security telemetry, relative token position (e.g., an unmanaged source IP adjacent to an administrative LogonType 3) carries critical semantic weight. Furthermore, an encoder allows bidirectional self-attention across the full 512-token sliding window simultaneously, whereas autoregressive decoders attend unidirectionally and suffer higher latency."),
        
        ("Q2: In Table III, why is 44M DeBERTa-v3 faster and more accurate than 3.8B Phi-3 Mini?",
         "This demonstrates the inductive bias of specialized domain models versus general foundation models. Phi-3 Mini is a generative decoder trained for broad NLP. Sequence classification over structured event logs requires extracting discriminative semantic boundaries, not text generation. A domain-adapted 44M encoder fine-tuned with Supervised Contrastive Loss focuses representational capacity entirely on security tokens, achieving higher F1 (99.38% vs 98.15%) with 42x less RAM and 12x faster inference on commodity CPUs."),
         
        ("Q3: What happens if an adversary deliberately slows their attack across days to evade your K=3 window?",
         "Stream A's sliding window is event-count-based (K=3), not purely wall-clock-bound. Three authentication events from a specific host or user session remain linked in the ring buffer regardless of elapsed time. Additionally, Layer 3 correlates events across a 300-second window, which can be expanded to multi-day session graphs using stateful graph tracking."),
         
        ("Q4: Did you test out-of-distribution performance or chronological splits? Does performance hold up over time?",
         "Yes, and this represents a key methodological disclosure in Section VIII of our paper. Under balanced stratified splits, EdgeShield attains 99.38% Macro F1. When tested under strict chronological 80/20 splits (training on early days, testing on later days with unfamiliar attack scripts), Macro F1 declined to 0.66, primarily due to reduced recall on Pass-the-Hash (EoHT). Our error analysis showed this is a supervision granularity challenge: the coarse EoHT label in LMD-2023 conflates distinct behaviors with only ~500 early-campaign examples. This finding motivates our Phase 3 roadmap: incorporating fine-grained MITRE sub-technique labels (T1550.002 vs T1003) and expanding training across DARPA OpTC and LANL."),
         
        ("Q5: How did you perform INT8 quantization without unacceptable accuracy loss?",
         "We used Dynamic Post-Training Quantization (PTQ) via ONNX Runtime (QuantType.QInt8), applying symmetric per-channel affine scaling: q = round(w/S) + Z. Because the 44M DeBERTa encoder has well-behaved weight distributions following contrastive training, dynamic quantization preserves 99.38% Macro F1 (accuracy degradation remained within 0.12 percentage points) while reducing disk footprint from 255 MB to 64.9 MB and cutting CPU latency by 2.38x.")
    ]

    for q, a in qa_list:
        add_body_p(doc, q, bold_prefix="❓ ")
        add_body_p(doc, a, bold_prefix="💡 Examiner Answer: ")
        doc.add_paragraph().space_after = Pt(4)

    # -------------------------------------------------------------
    # SECTION 6: GLOSSARY
    # -------------------------------------------------------------
    add_styled_heading(doc, "6. Essential Defense Glossary", 1)
    glossary_data = [
        ["Term", "Academic Definition & Practical Security Role"],
        ["SLM (Small Language Model)", "Transformer models with <8B parameters (typically 40M-3B) optimized for on-premise, low-latency edge deployment."],
        ["Lateral Movement (TA0008)", "Adversary tactics to extend network access across internal workstations after the initial compromise."],
        ["LOLBins (Living-off-the-Land)", "Legitimate system utilities (WMI, PsExec, PowerShell) repurposed by attackers to bypass static signatures."],
        ["Pass-the-Hash (T1550.002)", "Authenticating to a remote host using an extracted NTLM password hash without needing the plaintext password."],
        ["DeBERTa-v3", "Decoding-enhanced BERT featuring Disentangled Attention (separating content and relative position) and ELECTRA-style pre-training."],
        ["SupCon (Supervised Contrastive)", "A loss objective pulling identical attack embeddings together on a unit hypersphere while repelling benign administration."],
        ["PTQ (Post-Training Quantization)", "Converting 32-bit floating-point weights to 8-bit integers post-training to reduce model size and accelerate inference."],
        ["ONNX Runtime", "High-performance cross-platform execution engine optimized for low-latency edge inference on multi-core CPUs."]
    ]
    t4 = doc.add_table(rows=len(glossary_data), cols=2)
    format_table(t4, [2.2, 4.8], glossary_data[0], glossary_data[1:])

    doc.save("RDC3_Defense_Mastery_Guide.docx")
    print("Successfully generated RDC3_Defense_Mastery_Guide.docx!")

if __name__ == "__main__":
    generate_doc()
