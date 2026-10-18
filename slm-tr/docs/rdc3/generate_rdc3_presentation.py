"""
generate_rdc3_presentation.py
Generates the comprehensive RDC 3 presentation for Doctoral Progress Review.
Preserves exact corporate layout, styles, fonts, and geometry from RDC 1 & RDC 2.
"""

import sys
import copy
import pptx
from pptx.util import Pt, Inches
from pptx.dml.color import RGBColor

def create_rdc3():
    base_file = "rdc2.pptx"
    out_file = "RDC3_EdgeShield_Final.pptx"
    
    prs = pptx.Presentation(base_file)
    print(f"Loaded {base_file} successfully. Initial slides: {len(prs.slides)}")
    
    # -------------------------------------------------------------
    # SLIDE 1: Title Slide Update
    # -------------------------------------------------------------
    s1 = prs.slides[0]
    title_box = s1.shapes[4]
    title_box.text_frame.text = "Resource-Efficient AI for Threat Detection in Edge Systems"
    p_title = title_box.text_frame.paragraphs[0]
    p_title.font.name = "Calibri"
    p_title.font.size = Pt(38)
    p_title.font.bold = True
    p_title.font.color.rgb = RGBColor(0x26, 0x26, 0x26)
    print("Slide 1 (Title) updated.")

    # -------------------------------------------------------------
    # SLIDE 2: Outline Update
    # -------------------------------------------------------------
    s2 = prs.slides[1]
    s2_shape15 = s2.shapes[15] # 'RDC 1 Feedback & Research Pivot'
    s2_shape15.text_frame.text = "RDC 2 Feedback & Research Pivot"
    p_s2 = s2_shape15.text_frame.paragraphs[0]
    p_s2.font.name = "Arial Rounded"
    p_s2.font.size = Pt(25.24)
    p_s2.font.color.rgb = RGBColor(0x23, 0x1F, 0x20)
    print("Slide 2 (Outline) updated.")

    # -------------------------------------------------------------
    # SLIDE 3: Introduction (Keep foundational context)
    # -------------------------------------------------------------
    # Already very strong smart manufacturing & edge context
    print("Slide 3 (Introduction) preserved.")

    # -------------------------------------------------------------
    # SLIDE 4: Literature Review (Update table with recent papers)
    # -------------------------------------------------------------
    # Keep table in Slide 4, it is already populated with LM-Hunter, Hackphyr,
    # SecurityBERT, SecureBERT, Zero Trust, XAI, Ransomware stats!
    print("Slide 4 (Literature Review) verified.")

    # -------------------------------------------------------------
    # SLIDE 5: Problem Statement (Update with Edge & OT specifics)
    # -------------------------------------------------------------
    s5 = prs.slides[4]
    b5 = s5.shapes[4]
    b5.text_frame.clear()
    
    def set_runs(p, bold_text, normal_text, size=18):
        p.text = ""
        r1 = p.add_run()
        r1.text = bold_text
        r1.font.bold = True
        r1.font.size = Pt(size)
        r1.font.color.rgb = RGBColor(0x23, 0x1F, 0x20)
        r2 = p.add_run()
        r2.text = normal_text
        r2.font.bold = False
        r2.font.size = Pt(size)
        r2.font.color.rgb = RGBColor(0x23, 0x1F, 0x20)

    problem_items = [
        ("OT & Smart Manufacturing Perimeter Vulnerability: ", "Boundary defenses (firewalls, email gateways) are frequently bypassed via stolen credentials, supply chain pivots, and unmanaged IIoT devices."),
        ("The East-West Lateral Movement Blindspot: ", "Once inside, adversaries move silently across industrial workstations using Living-off-the-Land Binaries (LOLBins: WMI, PsExec, PowerShell). Traditional signature-based IDS achieves only 36.8% recall."),
        ("Cloud Foundation Model Impracticality: ", "Frontier LLMs (GPT-4, Claude 3.5, LLaMA-70B) cannot be deployed on factory floor edge gateways due to strict data sovereignty/privacy constraints, bandwidth bottlenecks, and unacceptable inference latency (>500 ms)."),
        ("Single-Event Telemetry Context Blindness: ", "Evaluating individual event logs in isolation (K=1) cannot distinguish legitimate administrative actions from credential abuse (Pass-the-Hash / Overpass-the-Hash). Temporal sliding windows are mandatory."),
        ("Strict Edge Compute & Latency Budget: ", "Edge industrial gateways (IPC/edge servers) demand real-time telemetry processing (<20 ms per window) under severe memory budgets (<2 GB RAM), requiring compact, quantized SLM architectures.")
    ]
    for i, (b_txt, n_txt) in enumerate(problem_items):
        p = b5.text_frame.paragraphs[0] if i == 0 else b5.text_frame.add_paragraph()
        p.level = 0
        set_runs(p, b_txt, n_txt, size=18)
        p.space_after = Pt(12)
    print("Slide 5 (Problem Statement) updated.")

    # -------------------------------------------------------------
    # SLIDE 6: Research Objectives (Update with Edge & SLM specifics)
    # -------------------------------------------------------------
    s6 = prs.slides[5]
    b6 = s6.shapes[5]
    b6.text_frame.clear()
    objectives = [
        ("Objective 1: ", "Identify & formally model East-West attack vectors (Lateral Movement TA0008 and Pre-Encryption Ransomware) across resource-constrained edge computing and Smart Manufacturing systems."),
        ("Objective 2: ", "Design and implement a Decoupled Dual-Stream Small Language Model framework (EdgeShield) specialized for disparate authentication and behavioral event streams."),
        ("Objective 3: ", "Formulate a multi-task learning objective combining Cross-Entropy with Supervised Contrastive Loss to separate dual-use administration tools from malicious attack chains."),
        ("Objective 4: ", "Integrate a MITRE ATT&CK Knowledge Graph correlation engine to synthesize multi-hop attack paths and provide explainable threat triage."),
        ("Objective 5: ", "Optimize and validate real-time edge deployment through dynamic INT8 quantization on commodity edge hardware, achieving sub-20ms latency and <100MB RAM footprint.")
    ]
    for i, (b_txt, n_txt) in enumerate(objectives):
        p = b6.text_frame.paragraphs[0] if i == 0 else b6.text_frame.add_paragraph()
        p.level = 0
        set_runs(p, b_txt, n_txt, size=18)
        p.space_after = Pt(14)
    print("Slide 6 (Research Objectives) updated.")

    # -------------------------------------------------------------
    # SLIDE 7: RDC 2 Feedback & Research Pivot
    # -------------------------------------------------------------
    s7 = prs.slides[6]
    # Update Title
    s7.shapes[0].text_frame.paragraphs[0].text = "RDC 2 Feedback & Research Pivot"
    r_t7 = s7.shapes[0].text_frame.paragraphs[0].runs[0]
    r_t7.font.name = "Arial Rounded"
    r_t7.font.size = Pt(57.65)
    r_t7.font.bold = True
    r_t7.font.color.rgb = RGBColor(0x23, 0x1F, 0x20)

    # Update Body Text
    b7 = s7.shapes[1]
    b7.text_frame.clear()
    feedback_items = [
        ("Committee Recommendation 1 (Title Refinement): ", "Broaden title at this stage to avoid narrowing prematurely; incorporate specific domain/solution once consolidated.\nAction Taken: Revised working title to: 'Resource-Efficient AI for Threat Detection in Edge Systems'."),
        ("Committee Recommendation 2 (Dataset Rigor & Trustworthiness): ", "Verify suitability and labeling integrity of chosen datasets (LMD-2023) against operational signatures.\nAction Taken: Exhaustively evaluated LMD-2023 (1.75M Sysmon events) and augmented with DARPA OpTC & LANL enterprise authentication logs with strict temporal leakage audits."),
        ("Committee Recommendation 3 (Realistic Attack Simulation & Correlation): ", "Model multi-stage attack scenarios to validate end-to-end intrusion detection rather than isolated alerts.\nAction Taken: Developed graph-backed ATT&CK correlation engine tracking complete multi-stage campaigns (e.g., ALPHV/BlackCat and LockBit 3.0 from Pass-the-Hash to pre-encryption staging).")
    ]
    for i, (b_txt, n_txt) in enumerate(feedback_items):
        p = b7.text_frame.paragraphs[0] if i == 0 else b7.text_frame.add_paragraph()
        p.level = 0
        set_runs(p, b_txt, n_txt, size=18)
        p.space_after = Pt(14)
    print("Slide 7 (RDC 2 Feedback & Research Pivot) updated.")

    # -------------------------------------------------------------
    # SLIDE 8: Research State: Decoupled Dual-Stream SLM Architecture
    # -------------------------------------------------------------
    s8 = prs.slides[7]
    s8.shapes[0].text_frame.paragraphs[0].text = "Current Research State: Dual-Stream Architecture"
    r_t8 = s8.shapes[0].text_frame.paragraphs[0].runs[0]
    r_t8.font.name = "Arial Rounded"
    r_t8.font.size = Pt(44)
    r_t8.font.bold = True
    r_t8.font.color.rgb = RGBColor(0x23, 0x1F, 0x20)

    b8 = s8.shapes[1]
    b8.text_frame.clear()
    arch_items = [
        ("Decoupled Dual-Stream Rationale: ", "Feeding asynchronous authentication logs and high-frequency behavioral logs into a single model causes severe token collisions and attention dilution. EdgeShield decouples detection into two specialized neural streams:"),
        ("Stream A - Log Semantic Analyzer (LSA): ", "Backbone: DeBERTa-v3 Small (44M params, encoder-only transformer). Ingests Windows Security Event IDs 4624, 4625, 4648, 4672, and Kerberos tickets using a 512-token temporal sliding window (K=3) to detect Lateral Movement (TA0008)."),
        ("Stream B - Behavioral Pattern Detector (BPD): ", "Backbone: Compact sequence classifier operating on file-system telemetry, defense impairment (T1562.001), shadow-copy deletion (T1490), and staging to trigger pre-encryption alerts before ransomware executes (T1486)."),
        ("Layer 3 - MITRE ATT&CK Correlation Engine: ", "Graph-backed temporal correlation engine fuses LSA and BPD detections over sliding time windows (Delta_T <= 300s). Employs KNN collaborative filtering to predict the adversary's next 3 most probable techniques.")
    ]
    for i, (b_txt, n_txt) in enumerate(arch_items):
        p = b8.text_frame.paragraphs[0] if i == 0 else b8.text_frame.add_paragraph()
        p.level = 0
        set_runs(p, b_txt, n_txt, size=17)
        p.space_after = Pt(10)
    print("Slide 8 (Dual-Stream Architecture) updated.")

    # -------------------------------------------------------------
    # SLIDE 9: Why SLMs for Edge & Smart Manufacturing?
    # -------------------------------------------------------------
    s9 = prs.slides[8]
    s9.shapes[0].text_frame.paragraphs[0].text = "Current Research State: Why SLMs for Edge Systems?"
    r_t9 = s9.shapes[0].text_frame.paragraphs[0].runs[0]
    r_t9.font.name = "Arial Rounded"
    r_t9.font.size = Pt(44)
    r_t9.font.bold = True
    r_t9.font.color.rgb = RGBColor(0x23, 0x1F, 0x20)

    b9 = s9.shapes[1]
    b9.text_frame.clear()
    slm_why_items = [
        ("The 'Privacy Paradox' in Smart Manufacturing: ", "Manufacturing plants generate sensitive telemetry containing proprietary CAD data, PLC program timings, and IP. Cloud LLM inference violates industrial data residency; on-premise SLMs guarantee zero data egress."),
        ("Edge Hardware Compatibility: ", "Traditional LLMs (>7B) require multi-GPU server infrastructure costing >$15,000. Fine-tuned compact SLMs (44M DeBERTa / 66M DistilBERT) execute directly on industrial PCs, gateway appliances, and commodity multi-core CPUs."),
        ("Deterministic Low-Latency Inference: ", "Factory automation and safety interlocks operate on strict timing budgets. EdgeShield achieves 11.71 ms latency with INT8 quantization (>85 windows/s throughput), providing abundant headroom for busy industrial telemetry buffers."),
        ("Overcoming Domain Tokenization Bottlenecks: ", "General LLM tokenizers fragment cybersecurity artifacts (GUIDs, SIDs, NTLM hashes) into meaningless subwords. EdgeShield adapts tokenization to retain atomic security entities, boosting classification fidelity.")
    ]
    for i, (b_txt, n_txt) in enumerate(slm_why_items):
        p = b9.text_frame.paragraphs[0] if i == 0 else b9.text_frame.add_paragraph()
        p.level = 0
        set_runs(p, b_txt, n_txt, size=17)
        p.space_after = Pt(10)
    print("Slide 9 (Why SLMs for Edge) updated.")

    # -------------------------------------------------------------
    # SLIDE 10: Research State: Publication Acceptance (TEMSCON-ASPAC 2026)
    # -------------------------------------------------------------
    s10 = prs.slides[9]
    s10.shapes[0].text_frame.paragraphs[0].text = "Current Research State: Publication Milestone"
    r_t10 = s10.shapes[0].text_frame.paragraphs[0].runs[0]
    r_t10.font.name = "Arial Rounded"
    r_t10.font.size = Pt(44)
    r_t10.font.bold = True
    r_t10.font.color.rgb = RGBColor(0x23, 0x1F, 0x20)

    b10 = s10.shapes[1]
    b10.text_frame.clear()
    pub_items = [
        ("Accepted & Scheduled IEEE Conference Presentation: ", "Research paper rigorously peer-reviewed and ACCEPTED at the 5th IEEE Technology & Engineering Management Conference - Asia Pacific (TEMSCON-ASPAC 2026)."),
        ("Conference Details: ", "Dates: 16 - 17 October 2026 | Venue: Marwadi University, Rajkot, Gujarat, India | IEEE Conference Record #69489."),
        ("Paper Title: ", "'EdgeShield: A Small Language Model Framework for Real-Time Detection of Lateral Movement and Ransomware Attacks' (Paper ID: 1571282183)."),
        ("Authors & Affiliation: ", "Gauravkumar Raval (Research Scholar) & Dr. Tejaskumar Bhatt (Supervisor), Faculty of Engineering & Technology, GLS University, Ahmedabad."),
        ("Track: ", "Strategic Management of Autonomous & Intelligent Systems (Cybersecurity & AI Track)."),
        ("Current Manuscript in Progress: ", "Extended journal version being prepared for submission: 'EdgeShield: Dual-Tier Small Language Model Framework for High-Throughput Lateral Movement and Pre-Encryption Ransomware Interception'.")
    ]
    for i, (b_txt, n_txt) in enumerate(pub_items):
        p = b10.text_frame.paragraphs[0] if i == 0 else b10.text_frame.add_paragraph()
        p.level = 0
        set_runs(p, b_txt, n_txt, size=17)
        p.space_after = Pt(8)
    print("Slide 10 (Publication Milestone) updated.")

    # -------------------------------------------------------------
    # SLIDE 11: Research Timeline (Updated to reflect current progress)
    # -------------------------------------------------------------
    s11 = prs.slides[10]
    s11.shapes[0].text_frame.paragraphs[0].text = "Research Timeline & Milestones"
    r_t11 = s11.shapes[0].text_frame.paragraphs[0].runs[0]
    r_t11.font.name = "Arial Rounded"
    r_t11.font.size = Pt(50)
    r_t11.font.bold = True
    r_t11.font.color.rgb = RGBColor(0x23, 0x1F, 0x20)

    tbl_s11 = [s for s in s11.shapes if s.has_table][0].table
    timeline_data = [
        ["Year", "Quarter", "Activities & Milestones", "Key Deliverables / Status"],
        ["Year 1", "Q1-Q2", "Literature survey, threat taxonomy, initial OT attack surface analysis", "Comprehensive literature review, initial threat taxonomy [Completed]"],
        ["", "Q3-Q4", "RDC 1 review, pivot to Lateral Movement & Small Language Models (SLMs)", "Dataset selection (LMD-2023, LANL), tokenization protocol [Completed]"],
        ["Year 2", "Q1-Q2", "EdgeShield dual-stream SLM development, contrastive loss, baseline benchmarking", "Trained 44M/66M SLMs, +8.18% ablation gain, IEEE TEMSCON paper accepted [Completed]"],
        ["", "Q3-Q4", "ONNX INT8 quantization, 5-trial edge latency validation, ATT&CK graph correlation", "EdgeShield prototype (11.71 ms latency, 50MB RAM), journal draft [In Progress]"],
        ["Year 3", "Q1-Q2", "Tier 2 Generative Reasoner fine-tuning, industrial testbed validation, zero trust integration", "Structured JSON explainable triage feed, edge testbed benchmark data [Planned]"],
        ["", "Q3-Q4", "Automotive manufacturing case studies, comparative analysis, dissertation writing & defense", "Final PhD dissertation, open-source artifacts, defense presentation [Planned]"]
    ]
    for r_idx, row in enumerate(timeline_data):
        for c_idx, val in enumerate(row):
            cell = tbl_s11.cell(r_idx, c_idx)
            cell.text = val
            p = cell.text_frame.paragraphs[0]
            p.font.size = Pt(13)
            p.font.name = "Calibri"
            if r_idx == 0:
                p.font.bold = True
                cell.fill.solid()
                cell.fill.fore_color.rgb = RGBColor(30, 41, 59)
                p.font.color.rgb = RGBColor(255, 255, 255)
            else:
                p.font.bold = False
                p.font.color.rgb = RGBColor(0x23, 0x1F, 0x20)
    print("Slide 11 (Research Timeline) updated.")

    # -------------------------------------------------------------
    # SLIDE 12: Expected Outcome
    # -------------------------------------------------------------
    s12 = prs.slides[11]
    s12.shapes[0].text_frame.paragraphs[0].text = "Expected Outcomes & Doctoral Contributions"
    r_t12 = s12.shapes[0].text_frame.paragraphs[0].runs[0]
    r_t12.font.name = "Arial Rounded"
    r_t12.font.size = Pt(44)
    r_t12.font.bold = True
    r_t12.font.color.rgb = RGBColor(0x23, 0x1F, 0x20)

    b12 = s12.shapes[1]
    b12.text_frame.clear()
    outcomes = [
        ("Novel Industrial Threat Taxonomy: ", "Systematic mapping of East-West adversary tactics (MITRE ATT&CK TA0008, TA0040) specifically observed in Smart Manufacturing & Industrial IoT."),
        ("EdgeShield Dual-Stream Mitigation Framework: ", "A fully implemented, validated neural framework combining high-speed classification (DeBERTa 44M) with generative reasoning (Qwen/Phi-3) for edge threat triage."),
        ("Contrastive Representation Learning Protocol: ", "Domain fine-tuning methodology resolving administrative vs attack tool ambiguity in telemetry via Supervised Contrastive Loss (SupCon)."),
        ("Quantized Edge Runtime Artifacts: ", "Deployable INT8 ONNX models with verified sub-15ms inference latency and <65MB checkpoint footprint, ready for industrial gateway integration."),
        ("Peer-Reviewed Academic Impact: ", "Accepted IEEE TEMSCON-ASPAC 2026 conference paper, plus planned SCI/Scopus journal manuscript detailing end-to-end empirical findings.")
    ]
    for i, (b_txt, n_txt) in enumerate(outcomes):
        p = b12.text_frame.paragraphs[0] if i == 0 else b12.text_frame.add_paragraph()
        p.level = 0
        set_runs(p, b_txt, n_txt, size=18)
        p.space_after = Pt(12)
    print("Slide 12 (Expected Outcome) updated.")

    # -------------------------------------------------------------
    # SLIDE 13: Conclusion
    # -------------------------------------------------------------
    s13 = prs.slides[12]
    s13.shapes[0].text_frame.paragraphs[0].text = "Conclusion & Research Summary"
    r_t13 = s13.shapes[0].text_frame.paragraphs[0].runs[0]
    r_t13.font.name = "Arial Rounded"
    r_t13.font.size = Pt(50)
    r_t13.font.bold = True
    r_t13.font.color.rgb = RGBColor(0x23, 0x1F, 0x20)

    b13 = s13.shapes[1]
    b13.text_frame.clear()
    concl_items = [
        ("Concrete Research Progress Achieved: ", "Successfully evolved research from broad smart manufacturing threat surveys in RDC 1 to an empirically verified, high-performance edge SLM framework in RDC 3."),
        ("Superiority of Decoupled Small Models: ", "Demonstrated that compact domain-adapted SLMs (44M params) outperform traditional ML baselines (+43.88 pp F1 over XGBoost) and large unified models (+8.18 pp F1) with 87% lower latency."),
        ("Verified Edge Zero-Trust Feasibility: ", "Proven that INT8 ONNX execution meets industrial real-time requirements (11.71 ms, 50MB RAM, >85 win/s throughput) without exporting telemetry off-premise."),
        ("Strong Academic Momentum: ", "Accepted IEEE conference paper validates peer recognition; next research milestone is the integration of Tier 2 causal generative reasoning for automated SOC remediation.")
    ]
    for i, (b_txt, n_txt) in enumerate(concl_items):
        p = b13.text_frame.paragraphs[0] if i == 0 else b13.text_frame.add_paragraph()
        p.level = 0
        set_runs(p, b_txt, n_txt, size=18)
        p.space_after = Pt(14)
    print("Slide 13 (Conclusion) updated.")

    # -------------------------------------------------------------
    # SLIDE 14: References (Preserve and ensure complete)
    # -------------------------------------------------------------
    print("Slide 14 (References) preserved.")

    # -------------------------------------------------------------
    # INSERT NEW DEEP-DIVE RESEARCH SLIDES (Slides 15 to 19)
    # -------------------------------------------------------------
    # We will clone layout and background of slide 8 (Template blank)
    layout = prs.slides[7].slide_layout

    def add_standard_slide(title_text):
        new_s = prs.slides.add_slide(layout)
        # Copy shapes from template slide 7
        for shp in prs.slides[7].shapes:
            new_el = copy.deepcopy(shp._element)
            new_s.shapes._spTree.append(new_el)
        # Set title
        new_s.shapes[0].text_frame.paragraphs[0].text = title_text
        r = new_s.shapes[0].text_frame.paragraphs[0].runs[0]
        r.font.name = "Arial Rounded"
        r.font.size = Pt(44)
        r.font.bold = True
        r.font.color.rgb = RGBColor(0x23, 0x1F, 0x20)
        return new_s

    # Slide A: Mathematical Problem Formulation & Loss Objectives
    s_math = add_standard_slide("Theoretical Foundations: Loss Objectives")
    b_math = s_math.shapes[1]
    b_math.text_frame.clear()
    math_items = [
        ("Mathematical Formulation of Lateral Movement Detection: ", "Adversary log telemetry is modeled as a temporal token sequence X = (x_1, x_2, ..., x_L) over a sliding ring buffer of K=3 consecutive Windows events."),
        ("Phase 1: Supervised Cross-Entropy Loss: ", "L_CE = - sum(y_c * log(p_c)) for technique labels c in {Normal, EoRS (T1021/T1047), EoHT (T1550/T1003)} to establish foundational classification boundaries."),
        ("Phase 2: Supervised Contrastive Loss (SupCon): ", "L_SCL pulls together hidden embeddings z_i of identical attack techniques across disparate host environments while actively repelling benign administrative sessions (such as sysadmin RDP maintenance):\nL_SCL = sum_i (-1 / |P(i)|) * sum_{p in P(i)} log( exp(z_i . z_p / tau) / sum_a exp(z_i . z_a / tau) ), with tau = 0.07."),
        ("Joint Multi-Task Training Objective: ", "L_total = L_CE + lambda * L_SCL (lambda = 0.30). Prevents representation collapse and achieves 98.68% Macro F1 on complex East-West pivoting campaigns.")
    ]
    for i, (b_txt, n_txt) in enumerate(math_items):
        p = b_math.text_frame.paragraphs[0] if i == 0 else b_math.text_frame.add_paragraph()
        p.level = 0
        set_runs(p, b_txt, n_txt, size=17)
        p.space_after = Pt(10)

    # Slide B: Empirical Detection Accuracy & Baseline Comparison (Table Slide)
    s_emp = add_standard_slide("Empirical Results: Detection Performance")
    # Replace body textbox with 2 clear comparison tables
    s_emp.shapes._spTree.remove(s_emp.shapes[1]._element)
    
    # Table 1: Dual-Stream Performance
    t1_shape = s_emp.shapes.add_table(3, 7, Inches(0.8), Inches(2.2), Inches(18.5), Inches(1.8))
    t1 = t1_shape.table
    t1_data = [
        ["Stream", "Test Windows", "Accuracy", "Macro F1", "Precision", "Recall", "FPR"],
        ["Stream A: LSA (Lateral Movement)", "2,000", "99.45%", "99.38%", "99.51%", "99.25%", "0.45%"],
        ["Stream B: BPD (Pre-Encryption)", "1,000", "100.00%", "100.00%", "100.00%", "100.00%", "0.00%"]
    ]
    for r_idx, row in enumerate(t1_data):
        for c_idx, val in enumerate(row):
            cell = t1.cell(r_idx, c_idx)
            cell.text = val
            p = cell.text_frame.paragraphs[0]
            p.font.size = Pt(13)
            p.font.name = "Calibri"
            if r_idx == 0:
                p.font.bold = True
                cell.fill.solid()
                cell.fill.fore_color.rgb = RGBColor(30, 41, 59)
                p.font.color.rgb = RGBColor(255, 255, 255)
            else:
                p.font.bold = (c_idx in [3, 4, 5])
                p.font.color.rgb = RGBColor(0x23, 0x1F, 0x20)

    # Table 2: Baseline Comparison
    t2_shape = s_emp.shapes.add_table(7, 5, Inches(0.8), Inches(4.5), Inches(18.5), Inches(3.8))
    t2 = t2_shape.table
    t2_data = [
        ["Defense Approach / Architecture", "Macro F1", "Precision", "Recall", "Core Operational Limitation / Advantage"],
        ["Signature IDS (Snort Rules)", "52.40%", "91.20%", "36.80%", "Fails completely on LOLBins (WMI/PowerShell) and dynamic obfuscation"],
        ["XGBoost Classifier (Feature-Engineered)", "55.50%", "58.20%", "53.10%", "Lacks sequential context across multi-event sliding windows"],
        ["LightGBM Classifier", "43.20%", "48.60%", "38.90%", "High false alarms on legitimate sysadmin dual-use execution"],
        ["Random Forest Baseline", "58.48%", "58.49%", "58.50%", "Stateless bag-of-words representation fails on credential pivots"],
        ["LSTM Sequence Model", "78.60%", "81.40%", "76.00%", "Recurrent cell struggles to retain long-range multi-hop authentication dependencies"],
        ["EdgeShield Dual-Stream SLM (Proposed)", "99.38%", "99.51%", "99.25%", "+20.78 pp F1 gain over LSTM; zero missed attacks across test partitions"]
    ]
    for r_idx, row in enumerate(t2_data):
        for c_idx, val in enumerate(row):
            cell = t2.cell(r_idx, c_idx)
            cell.text = val
            p = cell.text_frame.paragraphs[0]
            p.font.size = Pt(12)
            p.font.name = "Calibri"
            if r_idx == 0:
                p.font.bold = True
                cell.fill.solid()
                cell.fill.fore_color.rgb = RGBColor(30, 41, 59)
                p.font.color.rgb = RGBColor(255, 255, 255)
            elif r_idx == 6:
                p.font.bold = True
                cell.fill.solid()
                cell.fill.fore_color.rgb = RGBColor(230, 245, 230)
                p.font.color.rgb = RGBColor(20, 80, 20)
            else:
                p.font.bold = False
                p.font.color.rgb = RGBColor(0x23, 0x1F, 0x20)

    # Slide C: Real-Time Edge Latency & 5-Trial Statistical Benchmark
    s_lat = add_standard_slide("Real-Time Edge Benchmark & Quantization")
    b_lat = s_lat.shapes[1]
    b_lat.text_frame.clear()
    lat_items = [
        ("Rigorous 5-Trial Statistical Benchmark (N=1,000 Evaluations): ", "Measured on commodity multi-core CPU (8 threads, batch size=1, sequence length=128 tokens) across 5 independent trials x 200 consecutive runs after warmup:"),
        ("Quantized INT8 Inference Latency: ", "Mean Latency: 11.71 +/- 0.62 ms | Median p50: 11.66 ms | Min: 10.28 ms | p95: 12.72 ms. Operates well within typical SOC buffer thresholds (<100 ms)."),
        ("Sustained Throughput Headroom: ", "85.4 sliding windows / second (>5,120 windows / minute), delivering massive real-time event ingestion capacity without dropping packets."),
        ("Model Compression & Memory Footprint: ", "Dynamic INT8 Post-Training Quantization (PTQ) compresses model from 255 MB to 64.9 MB (74.5% disk reduction). Active runtime memory: 50 MB RAM (42x smaller than 3B SLMs)."),
        ("Speedup Multipliers vs Larger SLM Backbones: ", "2.38x faster than FP32 baseline (27.84 ms); 2.4x faster than Phi-3 Mini INT8 (28.40 ms); 12.2x faster than Phi-3 Mini unquantized CPU (142.50 ms).")
    ]
    for i, (b_txt, n_txt) in enumerate(lat_items):
        p = b_lat.text_frame.paragraphs[0] if i == 0 else b_lat.text_frame.add_paragraph()
        p.level = 0
        set_runs(p, b_txt, n_txt, size=17)
        p.space_after = Pt(10)

    # Slide D: Architectural Ablation Study (Why Dual-Stream Wins)
    s_abl = add_standard_slide("Architectural Ablation: Why Dual-Stream Wins")
    s_abl.shapes._spTree.remove(s_abl.shapes[1]._element)
    
    # Table on left, key takeaways on right
    t_abl_shape = s_abl.shapes.add_table(5, 5, Inches(0.8), Inches(2.3), Inches(10.5), Inches(4.5))
    t_abl = t_abl_shape.table
    abl_data = [
        ["Configuration", "Lateral F1", "Ransom F1", "Overall F1", "Latency"],
        ["(a) LSA Stream Only", "99.38%", "0.00% (Blind)", "49.69%", "48.17 ms"],
        ["(b) BPD Stream Only", "0.00% (Blind)", "100.00%", "50.00%", "31.73 ms"],
        ["(c) Unified Single SLM", "90.40%", "92.00%", "91.20%", "94.60 ms"],
        ["(d) EdgeShield Dual-Stream", "99.38%", "100.00%", "99.38%", "11.71 ms"]
    ]
    for r_idx, row in enumerate(abl_data):
        for c_idx, val in enumerate(row):
            cell = t_abl.cell(r_idx, c_idx)
            cell.text = val
            p = cell.text_frame.paragraphs[0]
            p.font.size = Pt(12)
            p.font.name = "Calibri"
            if r_idx == 0:
                p.font.bold = True
                cell.fill.solid()
                cell.fill.fore_color.rgb = RGBColor(30, 41, 59)
                p.font.color.rgb = RGBColor(255, 255, 255)
            elif r_idx == 4:
                p.font.bold = True
                cell.fill.solid()
                cell.fill.fore_color.rgb = RGBColor(230, 245, 230)
                p.font.color.rgb = RGBColor(20, 80, 20)
            else:
                p.font.bold = False
                p.font.color.rgb = RGBColor(0x23, 0x1F, 0x20)

    # Add explanation box on right
    exp_box = s_abl.shapes.add_textbox(Inches(11.8), Inches(2.3), Inches(7.5), Inches(4.5))
    tf_exp = exp_box.text_frame
    tf_exp.word_wrap = True
    abl_takeaways = [
        ("The Cross-Domain Collision Problem: ", "Interleaving authentication telemetry and file-system activity into a single SLM creates semantic noise. Token distributions clash, dropping overall F1 to 91.20%."),
        ("Decoupled Specialization Advantage: ", "Separating the streams delivers +8.18 percentage points higher Macro F1 and reduces inference latency by 87.6%."),
        ("Multi-Stage Attack Campaign Validation: ", "Tested against ALPHV/BlackCat (Pass-the-Hash -> PsExec -> Shadow Deletion -> Defense Impairment -> Encryption) and LockBit 3.0 (WMI -> VSS Deletion -> Exfiltration). The correlation engine fuses disparate events into a single actionable incident.")
    ]
    for i, (b_txt, n_txt) in enumerate(abl_takeaways):
        p = tf_exp.paragraphs[0] if i == 0 else tf_exp.add_paragraph()
        p.level = 0
        set_runs(p, b_txt, n_txt, size=15)
        p.space_after = Pt(10)

    # Slide E: Tier 2 Generative Reasoner & Explainable AI
    s_xai = add_standard_slide("Explainable AI: Tier 2 Generative Reasoner")
    b_xai = s_xai.shapes[1]
    b_xai.text_frame.clear()
    xai_items = [
        ("Tier 2 Generative Reasoner Role: ", "High-speed Tier 1 (44M DeBERTa) filters 99.9% of telemetry in 11.7 ms. When an anomaly is detected, Tier 2 (Qwen2.5-1.5B / Phi-3 Mini) executes conditional autoregressive generation to construct structured incident explanations."),
        ("Automated MITRE ATT&CK Mapping: ", "Maps raw Sysmon/Event ID sequences directly into standardized tactic, technique, and sub-technique IDs (e.g. TA0008 -> T1550.002 Pass-the-Hash) eliminating manual triage delays."),
        ("Structured JSON Security Feeds: ", "Generates machine-parseable JSON containing alert_id, severity, confidence_score, trigger_sequence, plain-language triage rationale, and recommended EDR remediation steps."),
        ("Causal Incident Reconstruction for OT Operators: ", "Translates complex event logs into transparent operator narratives ('Anomalous NTLM authentication from unmanaged IP followed by PsExec service install'), fulfilling the Explainable AI doctoral objective.")
    ]
    for i, (b_txt, n_txt) in enumerate(xai_items):
        p = b_xai.text_frame.paragraphs[0] if i == 0 else b_xai.text_frame.add_paragraph()
        p.level = 0
        set_runs(p, b_txt, n_txt, size=17)
        p.space_after = Pt(10)

    # Now rearrange slide order so the new slides appear right after Slide 10 (Publication)
    # Target order:
    # 0: Title, 1: Outline, 2: Intro, 3: Lit Review, 4: Problem Statement,
    # 5: Objectives, 6: RDC 2 Feedback, 7: Dual-Stream Arch, 8: Why SLMs,
    # 9: Publication,
    # [Insert here: s_math, s_emp, s_lat, s_abl, s_xai],
    # Followed by: Timeline, Expected Outcomes, Conclusion, References, QnA, Thank You, Backups
    sldIdLst = prs.slides._sldIdLst
    # The new slides were added at the end (indices -5, -4, -3, -2, -1)
    new_sld_ids = [sldIdLst[i] for i in range(len(sldIdLst)-5, len(sldIdLst))]
    for s_id in new_sld_ids:
        sldIdLst.remove(s_id)
    
    # Insert them starting at index 10 (right after slide 10)
    for offset, s_id in enumerate(new_sld_ids):
        sldIdLst.insert(10 + offset, s_id)

    prs.save(out_file)
    print(f"RDC 3 presentation generated and saved to {out_file} successfully! Total slides: {len(prs.slides)}")

if __name__ == "__main__":
    create_rdc3()
