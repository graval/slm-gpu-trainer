import os
import sys
from copy import deepcopy
import pptx
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

def create_deck():
    template_path = "TEMSCON-ASPAC-2026-Cover.pptx"
    output_path = "EdgeShield_TEMSCON_ASPAC_2026.pptx"
    conf_naming_path = "1571282183_EdgeShield.pptx"
    
    prs = Presentation(template_path)
    
    # ─── COLOR PALETTE ──────────────────────────────────────────────────────
    NAVY = RGBColor(25, 74, 141)         # #194A8D (IEEE / Conference Navy)
    SLATE = RGBColor(40, 44, 52)         # #282C34
    DARK_GRAY = RGBColor(60, 64, 67)     # #3C4043
    LIGHT_BG = RGBColor(248, 250, 252)   # #F8FAFC
    BORDER_COL = RGBColor(218, 224, 233) # #DAE0E9
    ACCENT_BLUE = RGBColor(43, 120, 197) # #2B78C5
    GREEN = RGBColor(46, 125, 50)        # #2E7D32
    RED = RGBColor(198, 40, 40)          # #C62828
    WHITE = RGBColor(255, 255, 255)
    
    # ─── SLIDE 1: COVER SLIDE ───────────────────────────────────────────────
    slide1 = prs.slides[0]
    for shp in slide1.shapes:
        if shp.name == "TextBox 7": # Title
            tf = shp.text_frame
            tf.word_wrap = True
            tf.clear()
            p = tf.paragraphs[0]
            p.text = "EdgeShield: A Small Language Model Framework for Real-Time Detection of Lateral Movement and Ransomware Attacks"
            p.font.name = "Arial"
            p.font.size = Pt(36)
            p.font.bold = True
            p.font.color.rgb = NAVY
            shp.left = Inches(1.37)
            shp.top = Inches(3.60)
            shp.width = Inches(15.5)
            shp.height = Inches(1.8)
            
        elif shp.name == "TextBox 15": # Authors
            tf = shp.text_frame
            tf.word_wrap = True
            tf.clear()
            
            p1 = tf.paragraphs[0]
            p1.text = "Gauravkumar Raval"
            p1.font.name = "Arial"
            p1.font.size = Pt(20)
            p1.font.bold = True
            p1.font.color.rgb = NAVY
            
            p1_aff = tf.add_paragraph()
            p1_aff.text = "Research Scholar, Faculty of Engineering & Technology, GLS University, Ahmedabad, India | gaurav.raval@hotmail.com"
            p1_aff.font.name = "Arial"
            p1_aff.font.size = Pt(15)
            p1_aff.font.color.rgb = DARK_GRAY
            
            p_space = tf.add_paragraph()
            p_space.text = ""
            p_space.font.size = Pt(6)
            
            p2 = tf.add_paragraph()
            p2.text = "Dr. Tejaskumar Bhatt"
            p2.font.name = "Arial"
            p2.font.size = Pt(20)
            p2.font.bold = True
            p2.font.color.rgb = NAVY
            
            p2_aff = tf.add_paragraph()
            p2_aff.text = "Assistant Professor, Faculty of Engineering & Technology, GLS University, Ahmedabad, India | tejas.bhatt@glsuniversity.ac.in"
            p2_aff.font.name = "Arial"
            p2_aff.font.size = Pt(15)
            p2_aff.font.color.rgb = DARK_GRAY
            
            shp.top = Inches(5.60)
            shp.width = Inches(16.0)
            shp.height = Inches(2.6)
            
        elif shp.name == "TextBox 16": # Paper ID
            tf = shp.text_frame
            tf.word_wrap = True
            tf.clear()
            p = tf.paragraphs[0]
            p.text = "Paper ID: 1571282183"
            p.font.name = "Arial"
            p.font.size = Pt(18)
            p.font.bold = True
            p.font.color.rgb = ACCENT_BLUE
            shp.top = Inches(3.10)
            shp.width = Inches(12.0)
            
        elif shp.name == "TextBox 26": # Track
            tf = shp.text_frame
            tf.word_wrap = True
            tf.clear()
            p = tf.paragraphs[0]
            p.text = "5th IEEE TEMSCON-ASPAC 2026  |  Track: Strategic Management of Autonomous & Intelligent Systems (Cybersecurity & AI)"
            p.font.name = "Arial"
            p.font.size = Pt(16)
            p.font.bold = True
            p.font.color.rgb = DARK_GRAY
            shp.top = Inches(2.35)
            shp.width = Inches(17.5)

    # Base template for content slides: Slide 2
    slide2_template = prs.slides[1]

    def create_content_slide(title_text):
        """Duplicates slide2 background elements, maps image relationships correctly, and adds title."""
        new_slide = prs.slides.add_slide(slide2_template.slide_layout)
        
        # Clear default placeholders created by layout
        for shp in list(new_slide.shapes):
            sp = shp._element
            sp.getparent().remove(sp)
            
        # Map all image relationships from slide2 to new_slide so PowerPoint displays images properly
        rId_map = {}
        for rel in slide2_template.part.rels.values():
            if 'image' in rel.reltype:
                new_rId = new_slide.part.relate_to(rel.target_part, rel.reltype)
                rId_map[rel.rId] = new_rId

        # Copy background shapes from slide 2 and remap blip references
        for shp in slide2_template.shapes:
            if shp.name == "Content Placeholder 17":
                continue # We build custom structured cards instead of generic placeholder
            new_sp = deepcopy(shp._element)
            for blip in new_sp.xpath('.//a:blip'):
                old_rId = blip.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed')
                if old_rId in rId_map:
                    blip.set('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed', rId_map[old_rId])
            new_slide.shapes._spTree.append(new_sp)
                
        # Find Title shape and set text
        for shp in new_slide.shapes:
            if "Title" in shp.name:
                tf = shp.text_frame
                tf.word_wrap = True
                tf.clear()
                p = tf.paragraphs[0]
                p.text = title_text
                p.font.name = "Arial"
                p.font.size = Pt(32)
                p.font.bold = True
                p.font.color.rgb = NAVY
                shp.left = Inches(0.8)
                shp.top = Inches(0.55)
                shp.width = Inches(13.8)
                shp.height = Inches(1.1)
                break
        return new_slide

    def add_card(slide, left, top, width, height, bg_color=WHITE, border_color=BORDER_COL):
        """Adds a clean solid card for structured presentation blocks (avoids background bleed)."""
        shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        shape.fill.solid()
        shape.fill.fore_color.rgb = bg_color
        shape.line.color.rgb = border_color
        shape.line.width = Pt(1.5)
        return shape

    # ─── SLIDE 2: EXECUTIVE SUMMARY & CORE CONTRIBUTIONS ────────────────────
    s2 = create_content_slide("Executive Summary & Core Contributions")
    
    # Left Card: Executive Summary
    c1 = add_card(s2, Inches(0.8), Inches(1.9), Inches(8.8), Inches(7.8), bg_color=WHITE)
    tf1 = c1.text_frame
    tf1.word_wrap = True
    p = tf1.paragraphs[0]
    p.text = "Enterprise Problem & Proposed Vision"
    p.font.name = "Arial"
    p.font.size = Pt(22)
    p.font.bold = True
    p.font.color.rgb = NAVY
    
    bullets1 = [
        ("The Dual Threat Reality", "Modern enterprise ransomware does not begin with encryption; it begins with days or weeks of silent lateral movement across domain hosts."),
        ("The Defense Trade-off", "Heuristic signatures miss obfuscated living-off-the-land techniques (36.8% recall), while cloud-hosted LLMs (>70B) are too slow and violate data-residency compliance."),
        ("EdgeShield Core Vision", "A purpose-built, dual-stream Small Language Model (SLM, 44M) framework operating 100% on-premise at the network edge with sub-15ms latency.")
    ]
    for b_title, b_desc in bullets1:
        p_t = tf1.add_paragraph()
        p_t.text = f"• {b_title}: "
        p_t.font.name = "Arial"
        p_t.font.size = Pt(17)
        p_t.font.bold = True
        p_t.font.color.rgb = SLATE
        p_d = tf1.add_paragraph()
        p_d.text = f"   {b_desc}"
        p_d.font.name = "Arial"
        p_d.font.size = Pt(15)
        p_d.font.color.rgb = DARK_GRAY

    # Right Card: Three Major Contributions
    c2 = add_card(s2, Inches(10.0), Inches(1.9), Inches(9.2), Inches(7.8), bg_color=WHITE)
    tf2 = c2.text_frame
    tf2.word_wrap = True
    p = tf2.paragraphs[0]
    p.text = "Key Research Contributions"
    p.font.name = "Arial"
    p.font.size = Pt(22)
    p.font.bold = True
    p.font.color.rgb = NAVY
    
    contribs = [
        ("1. Decoupled Dual-Stream SLM Architecture", "Separates asynchronous Windows authentication logs (Stream A: LSA) from high-frequency process/file telemetry (Stream B: BPD), completely preventing cross-domain token collisions."),
        ("2. ATT&CK Technique Mapping & Contrastive Loss", "Multi-task sliding-window fine-tuning (K=3) with Supervised Contrastive Loss; maps raw event streams directly to MITRE ATT&CK technique IDs with 100% pre-encryption lead time."),
        ("3. Rigorous Empirical & Edge Evaluation", "Benchmarked across 1.75M enterprise events (LMD-2023) and multi-stage attack scenarios: achieves 99.38% Macro F1, 87.6% latency reduction over unified models, and 11.7 ms INT8 edge runtime (>85 win/s).")
    ]
    for c_title, c_desc in contribs:
        p_t = tf2.add_paragraph()
        p_t.text = f"• {c_title}: "
        p_t.font.name = "Arial"
        p_t.font.size = Pt(17)
        p_t.font.bold = True
        p_t.font.color.rgb = ACCENT_BLUE
        p_d = tf2.add_paragraph()
        p_d.text = f"   {c_desc}"
        p_d.font.name = "Arial"
        p_d.font.size = Pt(15)
        p_d.font.color.rgb = DARK_GRAY

    # ─── SLIDE 3: THREAT LANDSCAPE & PROBLEM STATEMENT ──────────────────────
    s3 = create_content_slide("Threat Landscape: Why Existing Defenses Fail")
    
    col_w = Inches(5.8)
    b1 = add_card(s3, Inches(0.8), Inches(1.9), col_w, Inches(7.8), bg_color=WHITE)
    tf_b1 = b1.text_frame
    tf_b1.word_wrap = True
    p = tf_b1.paragraphs[0]
    p.text = "Traditional Signature IDS / EDR"
    p.font.name = "Arial"
    p.font.size = Pt(20)
    p.font.bold = True
    p.font.color.rgb = RED
    items_b1 = [
        "Rule-based detection (Snort, Zeek, static heuristic signatures).",
        "Severe blind spot against Living-off-the-Land Binaries (LOLBins: WMI, PsExec, WinRM).",
        "Command-line obfuscation and credential hopping bypass static regex.",
        "Empirical Result: Low recall capped at 36.80% in our evaluation.",
        "High alert volume without correlated attack context."
    ]
    for it in items_b1:
        p_it = tf_b1.add_paragraph()
        p_it.text = f"• {it}"
        p_it.font.name = "Arial"
        p_it.font.size = Pt(15)
        p_it.font.color.rgb = DARK_GRAY

    b2 = add_card(s3, Inches(7.1), Inches(1.9), col_w, Inches(7.8), bg_color=WHITE)
    tf_b2 = b2.text_frame
    tf_b2.word_wrap = True
    p = tf_b2.paragraphs[0]
    p.text = "Tree-Based Classical ML"
    p.font.name = "Arial"
    p.font.size = Pt(20)
    p.font.bold = True
    p.font.color.rgb = SLATE
    items_b2 = [
        "Feature engineering (XGBoost, LightGBM, Random Forest).",
        "Relies on isolated event-level features or tabular frequency bags.",
        "Lacks sequential contextualization across time-series event windows.",
        "Empirical Result: Poor generalization across sequences (XGBoost F1: 55.50%, LightGBM F1: 43.20%).",
        "Easily fooled when administrative tools mimic baseline behaviors."
    ]
    for it in items_b2:
        p_it = tf_b2.add_paragraph()
        p_it.text = f"• {it}"
        p_it.font.name = "Arial"
        p_it.font.size = Pt(15)
        p_it.font.color.rgb = DARK_GRAY

    b3 = add_card(s3, Inches(13.4), Inches(1.9), col_w, Inches(7.8), bg_color=WHITE)
    tf_b3 = b3.text_frame
    tf_b3.word_wrap = True
    p = tf_b3.paragraphs[0]
    p.text = "Cloud-Hosted Frontier LLMs"
    p.font.name = "Arial"
    p.font.size = Pt(20)
    p.font.bold = True
    p.font.color.rgb = SLATE
    items_b3 = [
        "70B+ parameter generative LLMs (GPT-4, LLaMA-3 70B).",
        "High Semantic Power but severe deployment barriers:",
        "1. Privacy & Zero-Trust: Raw enterprise security logs & Kerberos tickets cannot leave perimeter.",
        "2. Unacceptable Latency: Cloud API calls add 300–800 ms per window.",
        "3. Massive Cost: Continuous multi-billion token streaming requires multi-million GPU clusters."
    ]
    for it in items_b3:
        p_it = tf_b3.add_paragraph()
        p_it.text = f"• {it}"
        p_it.font.name = "Arial"
        p_it.font.size = Pt(15)
        p_it.font.color.rgb = DARK_GRAY

    # ─── SLIDE 4: PROPOSED EDGESHIELD ARCHITECTURE (CLEAN REDESIGN) ─────────
    s4 = create_content_slide("Proposed Framework: EdgeShield Architecture")
    
    # Left Side: Prominent, perfectly framed Architecture Diagram
    img_path = "page_2_img_1.png"
    if os.path.exists(img_path):
        # Framed container card for diagram
        diag_card = add_card(s4, Inches(0.8), Inches(1.9), Inches(10.6), Inches(7.8), bg_color=WHITE, border_color=BORDER_COL)
        # Embed diagram perfectly centered inside card
        s4.shapes.add_picture(img_path, Inches(1.1), Inches(2.2), Inches(10.0), Inches(7.2))
        
    # Right Side: 3 Dedicated, neatly stacked Layer Breakdown Cards (aligning with the 3 layers in diagram)
    right_x = Inches(11.8)
    right_w = Inches(7.4)
    
    # Card Layer 1
    c4_l1 = add_card(s4, right_x, Inches(1.9), right_w, Inches(2.35), bg_color=WHITE)
    tf_l1 = c4_l1.text_frame
    tf_l1.word_wrap = True
    p = tf_l1.paragraphs[0]
    p.text = "Layer 1: Telemetry Ingestion & Normalization"
    p.font.name = "Arial"
    p.font.size = Pt(17)
    p.font.bold = True
    p.font.color.rgb = NAVY
    p1 = tf_l1.add_paragraph()
    p1.text = "• Collects Windows Security Event IDs (4624, 4625, 4648, 4672), Sysmon process creation, Kerberos tickets, and file-system events.\n• Custom SecKnowledge 2.0 tokenizer maps hex hashes, SIDs, and GUIDs into unified tokens without subword fragmentation."
    p1.font.name = "Arial"
    p1.font.size = Pt(13)
    p1.font.color.rgb = DARK_GRAY
    
    # Card Layer 2
    c4_l2 = add_card(s4, right_x, Inches(4.55), right_w, Inches(2.6), bg_color=WHITE)
    tf_l2 = c4_l2.text_frame
    tf_l2.word_wrap = True
    p = tf_l2.paragraphs[0]
    p.text = "Layer 2: Decoupled Dual-Stream SLMs (44M)"
    p.font.name = "Arial"
    p.font.size = Pt(17)
    p.font.bold = True
    p.font.color.rgb = ACCENT_BLUE
    p2 = tf_l2.add_paragraph()
    p2.text = "• Stream A: Log Semantic Analyzer (LSA) tracks authentication pivots across hosts using temporal sliding windows (K=3).\n• Stream B: Behavioral Pattern Detector (BPD) monitors file/process anomalies for pre-encryption ransomware behaviors.\n• Decoupling eliminates cross-domain token collisions (+8.18 pp F1 gain)."
    p2.font.name = "Arial"
    p2.font.size = Pt(13)
    p2.font.color.rgb = DARK_GRAY

    # Card Layer 3
    c4_l3 = add_card(s4, right_x, Inches(7.45), right_w, Inches(2.25), bg_color=WHITE)
    tf_l3 = c4_l3.text_frame
    tf_l3.word_wrap = True
    p = tf_l3.paragraphs[0]
    p.text = "Layer 3: ATT&CK Correlation Engine"
    p.font.name = "Arial"
    p.font.size = Pt(17)
    p.font.bold = True
    p.font.color.rgb = GREEN
    p3 = tf_l3.add_paragraph()
    p3.text = "• Fuses LSA & BPD detections across correlated time windows (Delta_T <= 300s).\n• Maps combined signals to MITRE ATT&CK v15 attack graphs, generating unified high-confidence incident alerts for SOC response."
    p3.font.name = "Arial"
    p3.font.size = Pt(13)
    p3.font.color.rgb = DARK_GRAY

    # ─── SLIDE 5: STREAM A - LOG SEMANTIC ANALYZER (LSA) ────────────────────
    s5 = create_content_slide("Stream A: Log Semantic Analyzer (LSA) for Lateral Movement")
    
    c5_l = add_card(s5, Inches(0.8), Inches(1.9), Inches(9.0), Inches(7.8), bg_color=WHITE)
    tf5_l = c5_l.text_frame
    tf5_l.word_wrap = True
    p = tf5_l.paragraphs[0]
    p.text = "Targeted Telemetry & Tokenization"
    p.font.name = "Arial"
    p.font.size = Pt(21)
    p.font.bold = True
    p.font.color.rgb = NAVY
    
    lsa_points = [
        ("Ingested Log Channels", "Windows Security Event IDs: 4624 (Successful Logon), 4625 (Failed Logon), 4648 (Explicit Credential Logon), 4672 (Special Privileges Assigned)."),
        ("Kerberos & NetFlow Context", "Monitors Kerberos TGS/TGT ticket requests and Active Directory replication activity to catch Pass-the-Ticket / Golden Ticket operations."),
        ("Security-Adapted Tokenizer", "Trained on SecKnowledge 2.0; retains hex hashes, SIDs, and GUIDs as unified tokens instead of fragmented general BPE subwords."),
        ("Sliding Window Formulation", "Temporal windows of K=3 sequential events capture multi-step adversary movement chains (Auth -> Session -> Command).")
    ]
    for pt, desc in lsa_points:
        p_t = tf5_l.add_paragraph()
        p_t.text = f"• {pt}:"
        p_t.font.name = "Arial"
        p_t.font.size = Pt(16)
        p_t.font.bold = True
        p_t.font.color.rgb = SLATE
        p_d = tf5_l.add_paragraph()
        p_d.text = f"   {desc}"
        p_d.font.name = "Arial"
        p_d.font.size = Pt(14)
        p_d.font.color.rgb = DARK_GRAY

    c5_r = add_card(s5, Inches(10.2), Inches(1.9), Inches(9.0), Inches(7.8), bg_color=WHITE)
    tf5_r = c5_r.text_frame
    tf5_r.word_wrap = True
    p = tf5_r.paragraphs[0]
    p.text = "Two-Phase Fine-Tuning Strategy"
    p.font.name = "Arial"
    p.font.size = Pt(21)
    p.font.bold = True
    p.font.color.rgb = NAVY
    
    ft_points = [
        ("Phase 1: Supervised Cross-Entropy", "Trains the 44M DeBERTa-v3 Small encoder over labeled MITRE ATT&CK technique sequences: T1021 (Remote Services), T1550 (Alternate Auth), and T1570 (Tool Transfer)."),
        ("Phase 2: Supervised Contrastive Loss", "Separates legitimate administrative actions (e.g., scheduled admin RDP maintenance) from adversary lateral movement in the embedding space."),
        ("Loss Objective Formulation", "L_total = L_CE + lambda_1 * L_SupCon + lambda_2 * L_MSE\nEnsures well-calibrated confidence boundaries for high-precision alerting."),
        ("Empirical Performance", "Achieves 99.45% Accuracy, 99.38% Macro F1, and a low False Positive Rate of only 0.45% on real-world enterprise telemetry.")
    ]
    for pt, desc in ft_points:
        p_t = tf5_r.add_paragraph()
        p_t.text = f"• {pt}:"
        p_t.font.name = "Arial"
        p_t.font.size = Pt(16)
        p_t.font.bold = True
        p_t.font.color.rgb = ACCENT_BLUE
        p_d = tf5_r.add_paragraph()
        p_d.text = f"   {desc}"
        p_d.font.name = "Arial"
        p_d.font.size = Pt(14)
        p_d.font.color.rgb = DARK_GRAY

    # ─── SLIDE 6: STREAM B - BEHAVIORAL PATTERN DETECTOR (BPD) ──────────────
    s6 = create_content_slide("Stream B: Behavioral Pattern Detector (BPD) for Ransomware")
    
    c6_l = add_card(s6, Inches(0.8), Inches(1.9), Inches(9.0), Inches(7.8), bg_color=WHITE)
    tf6_l = c6_l.text_frame
    tf6_l.word_wrap = True
    p = tf6_l.paragraphs[0]
    p.text = "Pre-Encryption Kill-Chain Detection"
    p.font.name = "Arial"
    p.font.size = Pt(21)
    p.font.bold = True
    p.font.color.rgb = NAVY
    
    bpd_points = [
        ("Objective", "Catch ransomware during staging and defense impairment, well before file encryption APIs are triggered."),
        ("Channel 1: File-System Telemetry", "Detects file enumeration (T1083), mass rename bursts, and shadow-copy deletion (T1490: vssadmin delete shadows)."),
        ("Channel 2: Process & API Signals", "Monitors defense impairment (T1562.001: stopping Defender/EDR services via sc.exe) and abnormal API call chains."),
        ("Channel 3: Staging Network Telemetry", "Flags outbound C2 command beaconing and pre-encryption staging connections (T1071.001).")
    ]
    for pt, desc in bpd_points:
        p_t = tf6_l.add_paragraph()
        p_t.text = f"• {pt}:"
        p_t.font.name = "Arial"
        p_t.font.size = Pt(16)
        p_t.font.bold = True
        p_t.font.color.rgb = SLATE
        p_d = tf6_l.add_paragraph()
        p_d.text = f"   {desc}"
        p_d.font.name = "Arial"
        p_d.font.size = Pt(14)
        p_d.font.color.rgb = DARK_GRAY

    c6_r = add_card(s6, Inches(10.2), Inches(1.9), Inches(9.0), Inches(7.8), bg_color=WHITE)
    tf6_r = c6_r.text_frame
    tf6_r.word_wrap = True
    p = tf6_r.paragraphs[0]
    p.text = "Constrained Edge Modeling & Lead Time"
    p.font.name = "Arial"
    p.font.size = Pt(21)
    p.font.bold = True
    p.font.color.rgb = NAVY
    
    bpd_mech = [
        ("Constrained Domain Vocabulary", "Vocabulary strictly restricted to ~2,000 domain tokens (MITRE ATT&CK terms + OS telemetry primitives), minimizing parameter bloat and compute latency."),
        ("Lightweight Threat Attention Layer", "An attention-based scoring head placed over the SLM hidden states produces a continuous running threat score per event window."),
        ("100% Pre-Encryption Lead Time", "Successfully triggered high-confidence pre-encryption alerts before any encryption API calls were invoked across evaluated ransomware traces."),
        ("Curated Trace Performance", "Attained 100.0% Precision and 0.00% FPR against administrative baseline activity on deterministic ransomware traces.")
    ]
    for pt, desc in bpd_mech:
        p_t = tf6_r.add_paragraph()
        p_t.text = f"• {pt}:"
        p_t.font.name = "Arial"
        p_t.font.size = Pt(16)
        p_t.font.bold = True
        p_t.font.color.rgb = ACCENT_BLUE
        p_d = tf6_r.add_paragraph()
        p_d.text = f"   {desc}"
        p_d.font.name = "Arial"
        p_d.font.size = Pt(14)
        p_d.font.color.rgb = DARK_GRAY

    # ─── SLIDE 7: ATT&CK CORRELATION & THREAT HUNTING ───────────────────────
    s7 = create_content_slide("ATT&CK Knowledge Graph & Threat Correlation")
    
    c7_1 = add_card(s7, Inches(0.8), Inches(1.9), Inches(18.4), Inches(2.3), bg_color=WHITE)
    tf7_1 = c7_1.text_frame
    tf7_1.word_wrap = True
    p = tf7_1.paragraphs[0]
    p.text = "1. Graph-Backed Knowledge Representation"
    p.font.name = "Arial"
    p.font.size = Pt(19)
    p.font.bold = True
    p.font.color.rgb = NAVY
    p1 = tf7_1.add_paragraph()
    p1.text = "• Built upon the MITRE ATT&CK v15 enterprise matrix, mapping tactic -> technique -> sub-technique hierarchies.\n• Encodes empirical transition priors between authentication movement (TA0008) and ransomware execution (TA0040)."
    p1.font.name = "Arial"
    p1.font.size = Pt(15)
    p1.font.color.rgb = DARK_GRAY

    c7_2 = add_card(s7, Inches(0.8), Inches(4.5), Inches(9.0), Inches(5.2), bg_color=WHITE)
    tf7_2 = c7_2.text_frame
    tf7_2.word_wrap = True
    p = tf7_2.paragraphs[0]
    p.text = "2. Cross-Stream Temporal Correlation"
    p.font.name = "Arial"
    p.font.size = Pt(19)
    p.font.bold = True
    p.font.color.rgb = ACCENT_BLUE
    p2 = tf7_2.add_paragraph()
    p2.text = "• Correlated Time Window: Delta_T <= 300 seconds.\n• Fuses Stream A detections (e.g. LogonType 9 / PsExec execution) with Stream B alerts (e.g. vssadmin shadow deletion).\n• Merges two disparate signals into a single coordinated attack chain incident.\n• Eliminates single-stream alert fatigue and isolates compromised host endpoints automatically."
    p2.font.name = "Arial"
    p2.font.size = Pt(15)
    p2.font.color.rgb = DARK_GRAY

    c7_3 = add_card(s7, Inches(10.2), Inches(4.5), Inches(9.0), Inches(5.2), bg_color=WHITE)
    tf7_3 = c7_3.text_frame
    tf7_3.word_wrap = True
    p = tf7_3.paragraphs[0]
    p.text = "3. Predictive Threat Hunting"
    p.font.name = "Arial"
    p.font.size = Pt(19)
    p.font.bold = True
    p.font.color.rgb = ACCENT_BLUE
    p3 = tf7_3.add_paragraph()
    p3.text = "• Employs KNN-based collaborative filtering across the ATT&CK graph.\n• Given the sequence of techniques observed so far, queries the graph to forecast the adversary's next 3 most probable moves.\n• Shifts defense from reactive incident response to proactive edge threat isolation."
    p3.font.name = "Arial"
    p3.font.size = Pt(15)
    p3.font.color.rgb = DARK_GRAY

    # ─── SLIDE 8: EDGE DEPLOYMENT & INT8 ONNX PIPELINE ──────────────────────
    s8 = create_content_slide("Edge Deployment Strategy & ONNX INT8 Pipeline")
    
    stages = [
        ("Step 1: PyTorch Graph Export", "Exports fine-tuned 44M DeBERTa-v3 Small models to standardized ONNX graph format using dynamic sequence axes."),
        ("Step 2: Post-Training Quantization", "Applies dynamic INT8 post-training quantization (PTQ), compressing model weights from 255 MB to 64.9 MB (~75% reduction)."),
        ("Step 3: ONNX Runtime Engine", "Leverages Microsoft ONNX Runtime (built natively into modern OS) with automated accelerator dispatch (CPU, NPU, DirectML GPU)."),
        ("Step 4: Zero-Trust Endpoint SLA", "Inference runs 100% locally with a 50 MB RAM footprint; sensitive enterprise logs never cross the network perimeter.")
    ]
    card_w = Inches(4.3)
    card_h = Inches(7.6)
    for idx, (st, sd) in enumerate(stages):
        x = Inches(0.8 + idx * 4.7)
        c = add_card(s8, x, Inches(2.1), card_w, card_h, bg_color=WHITE)
        tf = c.text_frame
        tf.word_wrap = True
        p_num = tf.paragraphs[0]
        p_num.text = f"0{idx+1}"
        p_num.font.name = "Arial"
        p_num.font.size = Pt(36)
        p_num.font.bold = True
        p_num.font.color.rgb = ACCENT_BLUE
        
        p_st = tf.add_paragraph()
        p_st.text = st
        p_st.font.name = "Arial"
        p_st.font.size = Pt(18)
        p_st.font.bold = True
        p_st.font.color.rgb = NAVY
        
        p_sd = tf.add_paragraph()
        p_sd.text = f"\n{sd}"
        p_sd.font.name = "Arial"
        p_sd.font.size = Pt(15)
        p_sd.font.color.rgb = DARK_GRAY

    # ─── SLIDE 9: EXPERIMENTAL SETUP & DATASETS ─────────────────────────────
    s9 = create_content_slide("Experimental Setup & Evaluation Datasets")
    
    c9_1 = add_card(s9, Inches(0.8), Inches(1.9), Inches(11.0), Inches(7.8), bg_color=WHITE)
    tf9_1 = c9_1.text_frame
    tf9_1.word_wrap = True
    p = tf9_1.paragraphs[0]
    p.text = "Ingested Datasets & Class Distributions"
    p.font.name = "Arial"
    p.font.size = Pt(21)
    p.font.bold = True
    p.font.color.rgb = NAVY
    
    dsets = [
        ("Primary Lateral Movement Dataset (LMD-2023)", "1,752,836 real-world enterprise event logs (1.07 GB total):\n• Benign Baseline Activity (Class 0): 1,611,619 events (91.95%)\n• Remote Services (EoRS, Class 1): 110,710 events (6.32%)\n• Pass-the-Hash / Credential Dumping (EoHT, Class 2): 30,507 events (1.74%)\n• Balanced stratified partition: 12,000 train / 2,000 test sliding windows (K=3)."),
        ("Curated Multi-Stage Ransomware Telemetry", "6,000 multi-phase attack traces across 5 ATT&CK kill-chain stages:\n• T1083 File Discovery, T1562.001 Impairment, T1490 Shadow Deletion, T1071.001 C2 Staging, T1486 Mass Encryption."),
        ("Out-of-Distribution Validation Dataset", "Evaluated on DARPA OpTC enterprise host events to stress-test domain transfer.")
    ]
    for dt, dd in dsets:
        p_t = tf9_1.add_paragraph()
        p_t.text = f"• {dt}:"
        p_t.font.name = "Arial"
        p_t.font.size = Pt(16)
        p_t.font.bold = True
        p_t.font.color.rgb = SLATE
        p_d = tf9_1.add_paragraph()
        p_d.text = f"   {dd}"
        p_d.font.name = "Arial"
        p_d.font.size = Pt(14)
        p_d.font.color.rgb = DARK_GRAY

    c9_2 = add_card(s9, Inches(12.2), Inches(1.9), Inches(7.0), Inches(7.8), bg_color=WHITE)
    tf9_2 = c9_2.text_frame
    tf9_2.word_wrap = True
    p = tf9_2.paragraphs[0]
    p.text = "Training & Hardware Config"
    p.font.name = "Arial"
    p.font.size = Pt(21)
    p.font.bold = True
    p.font.color.rgb = NAVY
    
    hw_info = [
        ("Accelerator", "Intel Arc 140T GPU (16 GB VRAM) with DirectML acceleration."),
        ("Host Environment", "Intel Core Ultra 7 processor (Windows 11 / Linux compatible)."),
        ("Optimizer", "AdamW (lr = 2e-5, weight decay = 0.01, linear decay schedule)."),
        ("Batch & Epochs", "Batch size = 16, 3 training epochs per stream."),
        ("Inference Runtime", "ONNX Runtime 1.24.4 (CPU / DirectML execution providers).")
    ]
    for ht, hd in hw_info:
        p_t = tf9_2.add_paragraph()
        p_t.text = f"• {ht}:"
        p_t.font.name = "Arial"
        p_t.font.size = Pt(16)
        p_t.font.bold = True
        p_t.font.color.rgb = ACCENT_BLUE
        p_d = tf9_2.add_paragraph()
        p_d.text = f"   {hd}"
        p_d.font.name = "Arial"
        p_d.font.size = Pt(14)
        p_d.font.color.rgb = DARK_GRAY

    # ─── SLIDE 10: EMPIRICAL RESULTS - ACCURACY VS BASELINES ─────────────────
    s10 = create_content_slide("Empirical Results: Detection Accuracy vs. Baselines")
    
    c10_1 = add_card(s10, Inches(0.8), Inches(1.8), Inches(18.4), Inches(2.8), bg_color=WHITE)
    tf10_1 = c10_1.text_frame
    tf10_1.word_wrap = True
    p = tf10_1.paragraphs[0]
    p.text = "Table I: EdgeShield Dual-Stream Performance (Stratified Splits)"
    p.font.name = "Arial"
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = NAVY
    
    tbl_shape1 = s10.shapes.add_table(3, 7, Inches(1.2), Inches(2.4), Inches(17.6), Inches(2.0))
    tbl1 = tbl_shape1.table
    tbl_cols1 = ["Stream", "Test Samples", "Accuracy", "Macro F1", "Precision", "Recall", "FPR"]
    for c_idx, col_name in enumerate(tbl_cols1):
        cell = tbl1.cell(0, c_idx)
        cell.text = col_name
        cell.fill.solid()
        cell.fill.fore_color.rgb = NAVY
        for p in cell.text_frame.paragraphs:
            p.alignment = PP_ALIGN.CENTER
            p.font.name = "Arial"
            p.font.size = Pt(14)
            p.font.bold = True
            p.font.color.rgb = WHITE
            
    rows1 = [
        ["Stream A: LSA (Lateral Movement)", "2,000", "99.45%", "99.38%", "99.51%", "99.25%", "0.45%"],
        ["Stream B: BPD (Ransomware)", "1,000", "100.00%", "100.00%", "100.00%", "100.00%", "0.00%"]
    ]
    for r_idx, row in enumerate(rows1):
        for c_idx, val in enumerate(row):
            cell = tbl1.cell(r_idx + 1, c_idx)
            cell.text = val
            cell.fill.solid()
            cell.fill.fore_color.rgb = WHITE if r_idx % 2 == 0 else LIGHT_BG
            for p in cell.text_frame.paragraphs:
                p.alignment = PP_ALIGN.CENTER if c_idx > 0 else PP_ALIGN.LEFT
                p.font.name = "Arial"
                p.font.size = Pt(13)
                p.font.bold = (c_idx in [2, 3])
                p.font.color.rgb = SLATE

    c10_2 = add_card(s10, Inches(0.8), Inches(4.8), Inches(18.4), Inches(5.0), bg_color=WHITE)
    tf10_2 = c10_2.text_frame
    tf10_2.word_wrap = True
    p = tf10_2.paragraphs[0]
    p.text = "Table II: Comparison Against Traditional Security & ML Baselines"
    p.font.name = "Arial"
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = NAVY
    
    tbl_shape2 = s10.shapes.add_table(7, 5, Inches(1.2), Inches(5.4), Inches(17.6), Inches(4.2))
    tbl2 = tbl_shape2.table
    tbl_cols2 = ["Defense Approach", "Macro F1", "Precision", "Recall", "Core Limitation / Advantage"]
    for c_idx, col_name in enumerate(tbl_cols2):
        cell = tbl2.cell(0, c_idx)
        cell.text = col_name
        cell.fill.solid()
        cell.fill.fore_color.rgb = NAVY
        for p in cell.text_frame.paragraphs:
            p.alignment = PP_ALIGN.CENTER if c_idx in [1, 2, 3] else PP_ALIGN.LEFT
            p.font.name = "Arial"
            p.font.size = Pt(14)
            p.font.bold = True
            p.font.color.rgb = WHITE
            
    rows2 = [
        ["Signature IDS (Snort Rules)", "52.40%", "91.20%", "36.80%", "Fails on LOLBins and command-line obfuscation; poor recall."],
        ["XGBoost Classifier", "55.50%", "58.20%", "53.10%", "Lacks temporal sequential context across multi-event windows."],
        ["LightGBM Classifier", "43.20%", "48.60%", "38.90%", "Gradient boosted trees suffer high false alarms on admin tools."],
        ["Random Forest Baseline", "58.48%", "58.49%", "58.50%", "Standard bag-of-words framing fails on dynamic pivoting."],
        ["LSTM Sequence Model", "78.60%", "81.40%", "76.00%", "RNN recurrent state struggles with long-range log dependencies."],
        ["EdgeShield Dual-Stream SLM", "99.38%", "99.51%", "99.25%", "+20.78 pp F1 gain over LSTM; rich multi-task threat attention."]
    ]
    for r_idx, row in enumerate(rows2):
        for c_idx, val in enumerate(row):
            cell = tbl2.cell(r_idx + 1, c_idx)
            cell.text = val
            cell.fill.solid()
            if r_idx == 5:
                cell.fill.fore_color.rgb = RGBColor(232, 245, 233)
            else:
                cell.fill.fore_color.rgb = WHITE if r_idx % 2 == 0 else LIGHT_BG
            for p in cell.text_frame.paragraphs:
                p.alignment = PP_ALIGN.CENTER if c_idx in [1, 2, 3] else PP_ALIGN.LEFT
                p.font.name = "Arial"
                p.font.size = Pt(13)
                p.font.bold = (r_idx == 5)
                p.font.color.rgb = GREEN if r_idx == 5 and c_idx in [1, 2, 3] else SLATE

    # ─── SLIDE 11: REAL-TIME EDGE LATENCY & STATISTICAL BENCHMARKS ──────────
    s11 = create_content_slide("Real-Time Edge Performance & Statistical Verification")
    
    c11_l = add_card(s11, Inches(0.8), Inches(1.9), Inches(8.8), Inches(7.8), bg_color=WHITE)
    tf11_l = c11_l.text_frame
    tf11_l.word_wrap = True
    p = tf11_l.paragraphs[0]
    p.text = "Rigorous 5-Trial Statistical Benchmark"
    p.font.name = "Arial"
    p.font.size = Pt(21)
    p.font.bold = True
    p.font.color.rgb = NAVY
    
    stat_pts = [
        ("Sample Size", "5 independent trials x 200 runs = 1,000 total inference evaluations on commodity CPU (8 threads)."),
        ("Quantized INT8 Latency", "11.71 ± 0.62 ms per window (Median p50: 11.66 ms, Min: 10.28 ms, p95: 12.72 ms)."),
        ("Sustained Throughput", "85.4 windows / second (>5,100 windows / minute), delivering massive real-time headroom for busy SOC buffers."),
        ("Quantization Speedup", "2.38x execution speedup over unquantized FP32 (27.84 ms -> 11.71 ms)."),
        ("Memory Footprint", "50 MB active RAM footprint (checkpoint compressed from 255 MB to 64.9 MB).")
    ]
    for pt, desc in stat_pts:
        p_t = tf11_l.add_paragraph()
        p_t.text = f"• {pt}:"
        p_t.font.name = "Arial"
        p_t.font.size = Pt(16)
        p_t.font.bold = True
        p_t.font.color.rgb = ACCENT_BLUE
        p_d = tf11_l.add_paragraph()
        p_d.text = f"   {desc}"
        p_d.font.name = "Arial"
        p_d.font.size = Pt(14)
        p_d.font.color.rgb = DARK_GRAY

    c11_r = add_card(s11, Inches(10.0), Inches(1.9), Inches(9.2), Inches(7.8), bg_color=WHITE)
    tf11_r = c11_r.text_frame
    tf11_r.word_wrap = True
    p = tf11_r.paragraphs[0]
    p.text = "Model Backbone Head-to-Head Comparison"
    p.font.name = "Arial"
    p.font.size = Pt(21)
    p.font.bold = True
    p.font.color.rgb = NAVY
    
    tbl_shape3 = s11.shapes.add_table(5, 6, Inches(10.2), Inches(2.7), Inches(8.8), Inches(4.5))
    tbl3 = tbl_shape3.table
    tbl_cols3 = ["Model Backbone", "Params", "Macro F1", "CPU (ms)", "INT8 (ms)", "RAM"]
    for c_idx, col_name in enumerate(tbl_cols3):
        cell = tbl3.cell(0, c_idx)
        cell.text = col_name
        cell.fill.solid()
        cell.fill.fore_color.rgb = NAVY
        for p in cell.text_frame.paragraphs:
            p.alignment = PP_ALIGN.CENTER if c_idx > 0 else PP_ALIGN.LEFT
            p.font.name = "Arial"
            p.font.size = Pt(13)
            p.font.bold = True
            p.font.color.rgb = WHITE
            
    rows3 = [
        ["Phi-3 Mini (Instruct)", "3.8B", "98.15%", "142.50", "28.40", "2.10 GB"],
        ["Gemma-2 IT", "2.6B", "97.45%", "98.20", "21.60", "1.50 GB"],
        ["TinyLlama Chat", "1.1B", "93.80%", "42.10", "9.80", "0.70 GB"],
        ["DeBERTa-v3 (EdgeShield)", "44M", "99.38%", "48.17", "11.71", "0.05 GB (50MB)"]
    ]
    for r_idx, row in enumerate(rows3):
        for c_idx, val in enumerate(row):
            cell = tbl3.cell(r_idx + 1, c_idx)
            cell.text = val
            cell.fill.solid()
            if r_idx == 3:
                cell.fill.fore_color.rgb = RGBColor(232, 245, 233)
            else:
                cell.fill.fore_color.rgb = WHITE if r_idx % 2 == 0 else LIGHT_BG
            for p in cell.text_frame.paragraphs:
                p.alignment = PP_ALIGN.CENTER if c_idx > 0 else PP_ALIGN.LEFT
                p.font.name = "Arial"
                p.font.size = Pt(12)
                p.font.bold = (r_idx == 3)
                p.font.color.rgb = GREEN if r_idx == 3 and c_idx in [2, 4, 5] else SLATE

    p_summary = tf11_r.add_paragraph()
    p_summary.text = "\nKey Deployment Advantage:\n• 2.4x speedup over Phi-3 Mini INT8 (4.1x over own CPU baseline).\n• 42x smaller memory footprint (50 MB vs 2.10 GB) enables true edge sensor deployment."
    p_summary.font.name = "Arial"
    p_summary.font.size = Pt(14)
    p_summary.font.bold = True
    p_summary.font.color.rgb = SLATE

    # ─── SLIDE 12: ARCHITECTURAL ABLATION & MULTI-STAGE CAMPAIGNS ────────────
    s12 = create_content_slide("Architectural Ablation & Multi-Stage Attack Scenarios")
    
    c12_l = add_card(s12, Inches(0.8), Inches(1.9), Inches(10.0), Inches(7.8), bg_color=WHITE)
    tf12_l = c12_l.text_frame
    tf12_l.word_wrap = True
    p = tf12_l.paragraphs[0]
    p.text = "Table IV: Architectural Ablation Configurations"
    p.font.name = "Arial"
    p.font.size = Pt(19)
    p.font.bold = True
    p.font.color.rgb = NAVY
    
    tbl_shape4 = s12.shapes.add_table(5, 5, Inches(1.0), Inches(2.6), Inches(9.6), Inches(4.2))
    tbl4 = tbl_shape4.table
    tbl_cols4 = ["Configuration", "Lateral F1", "Ransom F1", "Overall F1", "Latency"]
    for c_idx, col_name in enumerate(tbl_cols4):
        cell = tbl4.cell(0, c_idx)
        cell.text = col_name
        cell.fill.solid()
        cell.fill.fore_color.rgb = NAVY
        for p in cell.text_frame.paragraphs:
            p.alignment = PP_ALIGN.CENTER if c_idx > 0 else PP_ALIGN.LEFT
            p.font.name = "Arial"
            p.font.size = Pt(13)
            p.font.bold = True
            p.font.color.rgb = WHITE
            
    rows4 = [
        ["(a) LSA Stream Only", "99.38%", "0.00% (Blind)", "49.69%", "48.17 ms"],
        ["(b) BPD Stream Only", "0.00% (Blind)", "100.00%", "50.00%", "31.73 ms"],
        ["(c) Unified Single SLM", "90.40%", "92.00%", "91.20%", "94.60 ms"],
        ["(d) EdgeShield Dual-Stream", "99.38%", "100.00%", "99.38%", "11.71 ms"]
    ]
    for r_idx, row in enumerate(rows4):
        for c_idx, val in enumerate(row):
            cell = tbl4.cell(r_idx + 1, c_idx)
            cell.text = val
            cell.fill.solid()
            if r_idx == 3:
                cell.fill.fore_color.rgb = RGBColor(232, 245, 233)
            else:
                cell.fill.fore_color.rgb = WHITE if r_idx % 2 == 0 else LIGHT_BG
            for p in cell.text_frame.paragraphs:
                p.alignment = PP_ALIGN.CENTER if c_idx > 0 else PP_ALIGN.LEFT
                p.font.name = "Arial"
                p.font.size = Pt(12)
                p.font.bold = (r_idx == 3)
                p.font.color.rgb = GREEN if r_idx == 3 and c_idx in [1, 2, 3, 4] else SLATE

    p_ab_note = tf12_l.add_paragraph()
    p_ab_note.text = "\n• Why Dual-Stream Wins: Feeding all telemetry to a single unified SLM causes cross-domain token collisions and attention dilution (dropping F1 to 91.20%).\n• Decoupled streams yield +8.18 pp higher F1 and 87.6% lower latency."
    p_ab_note.font.name = "Arial"
    p_ab_note.font.size = Pt(13)
    p_ab_note.font.color.rgb = DARK_GRAY

    c12_r = add_card(s12, Inches(11.2), Inches(1.9), Inches(8.0), Inches(7.8), bg_color=WHITE)
    tf12_r = c12_r.text_frame
    tf12_r.word_wrap = True
    p = tf12_r.paragraphs[0]
    p.text = "Simulated Multi-Stage Campaigns"
    p.font.name = "Arial"
    p.font.size = Pt(20)
    p.font.bold = True
    p.font.color.rgb = NAVY
    
    scen_pts = [
        ("ALPHV / BlackCat Scenario", "5 sequential attack stages:\n1. T1550.002 Pass-the-Hash\n2. T1021.002 PsExec remote execution\n3. T1490 Shadow copy deletion\n4. T1562.001 Defender service termination\n5. T1486 Active file encryption"),
        ("LockBit 3.0 Intrusion", "3 coordinated stages:\n1. T1047 WMI remote execution\n2. T1490 Volume shadow manipulation\n3. T1071.001 Exfiltration & encryption"),
        ("100% Pre-Encryption Lead Time", "The correlation engine generated high-confidence alerts at Stage 3 & 4 in both scenarios, providing automated response hooks to isolate hosts before T1486 mass encryption began.")
    ]
    for st, sd in scen_pts:
        p_t = tf12_r.add_paragraph()
        p_t.text = f"• {st}:"
        p_t.font.name = "Arial"
        p_t.font.size = Pt(15)
        p_t.font.bold = True
        p_t.font.color.rgb = ACCENT_BLUE
        p_d = tf12_r.add_paragraph()
        p_d.text = f"   {sd}"
        p_d.font.name = "Arial"
        p_d.font.size = Pt(13)
        p_d.font.color.rgb = DARK_GRAY

    # ─── SLIDE 13: ACADEMIC RIGOR, LIMITATIONS & ROADMAP ────────────────────
    s13 = create_content_slide("Methodological Rigor, Limitations & Future Roadmap")
    
    c13_l = add_card(s13, Inches(0.8), Inches(1.9), Inches(9.0), Inches(7.8), bg_color=WHITE)
    tf13_l = c13_l.text_frame
    tf13_l.word_wrap = True
    p = tf13_l.paragraphs[0]
    p.text = "Academic Rigor & Honest Limitations"
    p.font.name = "Arial"
    p.font.size = Pt(21)
    p.font.bold = True
    p.font.color.rgb = NAVY
    
    lim_pts = [
        ("Chronological Split Stress-Testing", "Under strict chronological 80/20 splits with duplicate removal, Macro F1 drops from 0.99 to 0.66. Pass-the-Hash (EoHT) recall collapses due to extreme sparsity (~500 early-campaign examples)."),
        ("Supervision Granularity Insight", "Analysis proves this is a supervision granularity problem (coarse EoHT label conflates disparate tools), rather than an architectural flaw. Technique-level sub-labels (T1550 vs T1003) are prescribed."),
        ("Deterministic Curated Traces", "100% precision on BPD reflects the deterministic nature of curated ransomware templates; deployment to noisier live enterprise telemetry remains an open challenge."),
        ("Adversarial Robustness", "Adversaries with knowledge of the tokenizer could attempt field manipulation or benign-mimicking sliding windows; triple-layer correlation mitigates single-point-of-failure risk.")
    ]
    for lt, ld in lim_pts:
        p_t = tf13_l.add_paragraph()
        p_t.text = f"• {lt}:"
        p_t.font.name = "Arial"
        p_t.font.size = Pt(16)
        p_t.font.bold = True
        p_t.font.color.rgb = RED
        p_d = tf13_l.add_paragraph()
        p_d.text = f"   {ld}"
        p_d.font.name = "Arial"
        p_d.font.size = Pt(14)
        p_d.font.color.rgb = DARK_GRAY

    c13_r = add_card(s13, Inches(10.2), Inches(1.9), Inches(9.0), Inches(7.8), bg_color=WHITE)
    tf13_r = c13_r.text_frame
    tf13_r.word_wrap = True
    p = tf13_r.paragraphs[0]
    p.text = "Future Technical Roadmap"
    p.font.name = "Arial"
    p.font.size = Pt(21)
    p.font.bold = True
    p.font.color.rgb = NAVY
    
    road_pts = [
        ("Federated Edge Learning", "Deploying privacy-preserving federated aggregation across distributed enterprise branch nodes to update LoRA adapters without centralizing raw telemetry."),
        ("Retrieval-Augmented Generation (RAG)", "Coupling the classification layer to a dynamic MITRE ATT&CK knowledge index to absorb zero-day techniques without model retraining."),
        ("Multi-Tactic Pipeline Expansion", "Extending the dual-stream concept to bracket the entire kill chain: Initial Access (TA0001), Persistence (TA0003), and Data Exfiltration (TA0010)."),
        ("Hardware Accelerator Micro-Kernels", "Custom DirectML / NPU operator graph optimizations to unlock sub-5ms inference on dedicated neural processing units.")
    ]
    for rt, rd in road_pts:
        p_t = tf13_r.add_paragraph()
        p_t.text = f"• {rt}:"
        p_t.font.name = "Arial"
        p_t.font.size = Pt(16)
        p_t.font.bold = True
        p_t.font.color.rgb = GREEN
        p_d = tf13_r.add_paragraph()
        p_d.text = f"   {rd}"
        p_d.font.name = "Arial"
        p_d.font.size = Pt(14)
        p_d.font.color.rgb = DARK_GRAY

    # ─── SLIDE 14: CONCLUSION & Q&A ─────────────────────────────────────────
    s14 = create_content_slide("Conclusion & Key Takeaways")
    
    c14_main = add_card(s14, Inches(0.8), Inches(1.9), Inches(18.4), Inches(7.8), bg_color=WHITE)
    tf14 = c14_main.text_frame
    tf14.word_wrap = True
    p = tf14.paragraphs[0]
    p.text = "Summary of Key Findings"
    p.font.name = "Arial"
    p.font.size = Pt(22)
    p.font.bold = True
    p.font.color.rgb = NAVY
    
    concl_pts = [
        ("Specialized SLMs Outperform General Monoliths", "Small, domain-adapted models (44M) match or exceed multi-billion parameter models in specialized SOC tasks while maintaining over 24x lower compute cost."),
        ("Decoupled Dual-Stream Architecture is Essential", "Separating authentication (LSA) and behavioral telemetry (BPD) prevents token collisions, achieving +8.18 pp higher F1 and 87.6% latency reduction over unified models."),
        ("Proven Real-Time Zero-Trust Edge Viability", "INT8 ONNX Runtime executes in 11.71 ± 0.62 ms with a 50 MB memory footprint, delivering >85 windows/s throughput on commodity enterprise endpoints."),
        ("Strategic Alignment with TEMSCON-ASPAC 2026", "Demonstrates how intelligent, autonomous threat detection can be operationalized responsibly in critical sectors without cloud dependencies or telemetry privacy leaks.")
    ]
    for ct, cd in concl_pts:
        p_t = tf14.add_paragraph()
        p_t.text = f"• {ct}:"
        p_t.font.name = "Arial"
        p_t.font.size = Pt(17)
        p_t.font.bold = True
        p_t.font.color.rgb = ACCENT_BLUE
        p_d = tf14.add_paragraph()
        p_d.text = f"   {cd}"
        p_d.font.name = "Arial"
        p_d.font.size = Pt(15)
        p_d.font.color.rgb = DARK_GRAY
        
    p_qa = tf14.add_paragraph()
    p_qa.text = "\nThank you for your time!\nQuestions & Discussion: gaurav.raval@hotmail.com | tejas.bhatt@glsuniversity.ac.in"
    p_qa.font.name = "Arial"
    p_qa.font.size = Pt(18)
    p_qa.font.bold = True
    p_qa.font.color.rgb = NAVY
    p_qa.alignment = PP_ALIGN.CENTER

    # Delete the empty template slide 2 (index 1) so presentation starts immediately after cover
    rId = prs.slides._sldIdLst[1].rId
    prs.part.drop_rel(rId)
    del prs.slides._sldIdLst[1]

    prs.save(output_path)
    prs.save(conf_naming_path)
    print(f"[+] Presentation successfully created at {output_path} and {conf_naming_path}!")

if __name__ == "__main__":
    create_deck()
