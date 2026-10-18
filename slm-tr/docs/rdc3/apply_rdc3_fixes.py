"""
apply_rdc3_fixes.py
Applies all 6 visual and structural fixes to RDC3_EdgeShield_Final.pptx:
1. Slides 11-15: Replace broken freeform decor shapes with real pictures (extracted_decor.png)
   positioned at top-left (rot 180) and bottom-right, pushed to background.
2. Slide 18 (Conclusion & Research Summary): Widen title box to single line (15940200, top=581800, 40pt)
   and position body text below it (top=2200000) with full bullet hierarchy.
3. Slide 4 (Literature Review Table): Increase font size for the 3 right-hand columns (cols 1, 2, 3) to 20pt.
4. Slides 7, 8, 9, 10: Convert all paragraphs into true DrawingML bullet lists (• parent, ○ sub-bullet).
5. Slide 16 (Research Timeline & Milestones): Widen title box to single line (15940200, top=581800, 40pt)
   and position table cleanly below it (top=2200000).
6. Slide 19 (References): Convert references into a clean, full-width single-column numbered list (APA 7th).
"""

import pptx
from pptx.util import Pt
from pptx.dml.color import RGBColor
from pptx.oxml.xmlchemy import OxmlElement
from pptx.oxml.ns import qn
import os

def set_paragraph_bullet(p, text, level=0, is_bold=False, sz_pt=14.0, color_rgb=(0x23, 0x1F, 0x20), space_after_pt=4.0):
    p.text = text
    p.level = level
    pPr = p._p.get_or_add_pPr()
    
    # Remove any existing buNone or buChar
    for tag in ['a:buNone', 'a:buChar', 'a:buAutoNum', 'a:buBlip']:
        for el in pPr.findall(qn(tag)):
            pPr.remove(el)
            
    # Create buChar
    buChar = OxmlElement('a:buChar')
    if level == 0:
        buChar.set('char', '•')
        pPr.set('marL', '457200')
        pPr.set('indent', '-300000')
    else:
        buChar.set('char', '○')
        pPr.set('marL', '914400')
        pPr.set('indent', '-300000')
        
    pPr.insert(0, buChar)
    
    # Format runs
    for run in p.runs:
        run.font.name = "Calibri"
        run.font.size = Pt(sz_pt)
        run.font.bold = is_bold
        run.font.color.rgb = RGBColor(*color_rgb)
        
    p.space_after = Pt(space_after_pt)

def fix_presentation():
    input_pptx = "RDC3_EdgeShield_Final.pptx"
    output_pptx = "RDC3_EdgeShield_Final.pptx"
    decor_img = "extracted_decor.png"
    
    if not os.path.exists(decor_img):
        raise FileNotFoundError(f"Missing decor image {decor_img}")
        
    prs = pptx.Presentation(input_pptx)
    print(f"Loaded {input_pptx}. Total slides: {len(prs.slides)}")
    
    # =========================================================================
    # FIX 1: Slides 11 to 15 Corner Decor Images
    # =========================================================================
    print("\n--- Applying Fix 1: Slides 11 to 15 Corner Decor Images ---")
    for s_idx in range(10, 15): # Slides 11 to 15 (0-indexed 10 to 14)
        slide = prs.slides[s_idx]
        title_text = slide.shapes[0].text_frame.text.strip() if slide.shapes and slide.shapes[0].has_text_frame else "Unknown"
        print(f"Fixing Slide {s_idx+1}: {title_text}")
        
        # Remove broken freeform shapes (left < 0 or left > 15,000,000)
        broken_shapes = [sh for sh in slide.shapes if sh.left < 0 or sh.left > 15000000]
        for sh in broken_shapes:
            slide.shapes._spTree.remove(sh._element)
            
        # Add crisp corner decor images
        # 1. Top-Left: left=-2059222, top=-789427, w=4118443, h=3654183, rotation=180
        pic_tl = slide.shapes.add_picture(decor_img, -2059222, -789427, 4118443, 3654183)
        pic_tl.rotation = 180
        slide.shapes._spTree.remove(pic_tl._element)
        slide.shapes._spTree.insert(2, pic_tl._element)
        
        # 2. Bottom-Right: left=16322124, top=7754894, w=4118443, h=3654183, rotation=0
        pic_br = slide.shapes.add_picture(decor_img, 16322124, 7754894, 4118443, 3654183)
        pic_br.rotation = 0
        slide.shapes._spTree.remove(pic_br._element)
        slide.shapes._spTree.insert(2, pic_br._element)

    # =========================================================================
    # FIX 2: Slide 18 (Conclusion & Research Summary Title Collision)
    # =========================================================================
    print("\n--- Applying Fix 2: Slide 18 Title & Body Repositioning ---")
    s18 = prs.slides[17] # Slide 18
    title_s18 = s18.shapes[0]
    title_s18.left = 1998300
    title_s18.top = 581800
    title_s18.width = 15940200
    title_s18.height = 1200000
    title_p = title_s18.text_frame.paragraphs[0]
    title_p.text = "Conclusion & Research Summary"
    title_p.font.name = "Arial Rounded"
    title_p.font.size = Pt(40)
    title_p.font.bold = True
    title_p.font.color.rgb = RGBColor(0x23, 0x1F, 0x20)
    
    # Body text box
    body_s18 = s18.shapes[1]
    body_s18.left = 1998300
    body_s18.top = 2200000
    body_s18.width = 15070500
    body_s18.height = 7600000
    
    # Format body bullets cleanly
    conclusion_items = [
        ("Concrete Research Progress Achieved", "Successfully evolved research from broad smart manufacturing threat surveys in RDC 1 to an empirically verified, high-performance edge SLM framework in RDC 3."),
        ("Superiority of Decoupled Small Models", "Demonstrated that compact domain-adapted SLMs (44M params) outperform traditional ML baselines (+43.88 pp F1 over XGBoost) and large unified models (+8.18 pp F1) with 87% lower latency."),
        ("Verified Edge Zero-Trust Feasibility", "Proven that INT8 ONNX execution meets industrial real-time requirements (11.71 ms, 50MB RAM, >85 win/s throughput) without exporting telemetry off-premise."),
        ("Strong Academic Momentum", "Accepted IEEE conference paper validates peer recognition; next research milestone is the integration of Tier 2 causal generative reasoning for automated SOC remediation.")
    ]
    
    tf18 = body_s18.text_frame
    tf18.clear()
    first = True
    for heading, detail in conclusion_items:
        p1 = tf18.paragraphs[0] if first else tf18.add_paragraph()
        first = False
        set_paragraph_bullet(p1, heading, level=0, is_bold=True, sz_pt=15.0, color_rgb=(0x23, 0x1F, 0x20), space_after_pt=2.0)
        
        p2 = tf18.add_paragraph()
        set_paragraph_bullet(p2, detail, level=1, is_bold=False, sz_pt=13.5, color_rgb=(0x4B, 0x55, 0x63), space_after_pt=8.0)

    # =========================================================================
    # FIX 3: Slide 4 Literature Review Table Font Size
    # =========================================================================
    print("\n--- Applying Fix 3: Slide 4 Table Right Columns Font Size ---")
    s4 = prs.slides[3] # Slide 4
    tbl4 = [sh for sh in s4.shapes if sh.has_table][0].table
    
    # Header row
    for c in [1, 2, 3]:
        cell = tbl4.cell(0, c)
        for p in cell.text_frame.paragraphs:
            p.font.name = "Calibri"
            p.font.size = Pt(20)
            p.font.bold = True
            for r in p.runs:
                r.font.name = "Calibri"
                r.font.size = Pt(20)
                r.font.bold = True
                
    # Data rows (1 to 7)
    for r in range(1, len(tbl4.rows)):
        for c in [1, 2, 3]:
            cell = tbl4.cell(r, c)
            for p in cell.text_frame.paragraphs:
                p.font.name = "Calibri"
                p.font.size = Pt(20)
                p.font.bold = False
                for run in p.runs:
                    run.font.name = "Calibri"
                    run.font.size = Pt(20)
                    run.font.bold = False

    # =========================================================================
    # FIX 4: Slides 7, 8, 9, 10 Hierarchical Bullet Lists
    # =========================================================================
    print("\n--- Applying Fix 4: Slides 7, 8, 9, 10 Hierarchical Bullet Lists ---")
    
    # --- SLIDE 7: RDC 2 Feedback & Research Pivot ---
    s7 = prs.slides[6]
    body_s7 = s7.shapes[1]
    body_s7.left = 1998300
    body_s7.top = 2200000
    body_s7.width = 15394200
    body_s7.height = 7600000
    tf7 = body_s7.text_frame
    tf7.clear()
    
    s7_items = [
        ("Committee Recommendation 1 (Title Refinement):", 
         "Broaden title at this stage to avoid narrowing prematurely; incorporate specific domain/solution once consolidated.",
         "Action Taken: Revised working title to: 'Resource-Efficient AI for Threat Detection in Edge Systems'."),
        ("Committee Recommendation 2 (Dataset Rigor & Trustworthiness):", 
         "Verify suitability and labeling integrity of chosen datasets (LMD-2023) against operational signatures.",
         "Action Taken: Exhaustively evaluated LMD-2023 (1.75M Sysmon events) and augmented with DARPA OpTC & LANL enterprise authentication logs with strict temporal leakage audits."),
        ("Committee Recommendation 3 (Realistic Attack Simulation & Correlation):", 
         "Model multi-stage attack scenarios to validate end-to-end intrusion detection rather than isolated alerts.",
         "Action Taken: Developed graph-backed ATT&CK correlation engine tracking complete multi-stage campaigns (e.g., ALPHV/BlackCat and LockBit 3.0 from Pass-the-Hash to pre-encryption staging).")
    ]
    
    first = True
    for heading, detail, action in s7_items:
        p1 = tf7.paragraphs[0] if first else tf7.add_paragraph()
        first = False
        set_paragraph_bullet(p1, heading, level=0, is_bold=True, sz_pt=14.5, color_rgb=(0x23, 0x1F, 0x20), space_after_pt=2.0)
        p2 = tf7.add_paragraph()
        set_paragraph_bullet(p2, detail, level=1, is_bold=False, sz_pt=13.0, color_rgb=(0x4B, 0x55, 0x63), space_after_pt=2.0)
        p3 = tf7.add_paragraph()
        set_paragraph_bullet(p3, action, level=1, is_bold=False, sz_pt=13.0, color_rgb=(0x1E, 0x3A, 0x8A), space_after_pt=8.0)

    # --- SLIDE 8: Dual-Stream Architecture ---
    s8 = prs.slides[7]
    body_s8 = s8.shapes[1]
    body_s8.left = 1998300
    body_s8.top = 2200000
    body_s8.width = 15394200
    body_s8.height = 7600000
    tf8 = body_s8.text_frame
    tf8.clear()
    
    s8_items = [
        ("Decoupled Dual-Stream Architectural Rationale", [
            "Feeding asynchronous authentication logs and high-frequency behavioral logs into a single model causes severe token collisions and attention dilution.",
            "EdgeShield decouples detection into two specialized neural streams, synchronizing them at the temporal correlation layer."
        ]),
        ("Stream A - Log Semantic Analyzer (LSA)", [
            "Backbone: DeBERTa-v3 Small (44M parameters, encoder-only transformer).",
            "Target Telemetry: Ingests Windows Security Event IDs 4624, 4625, 4648, 4672, and Kerberos tickets using a 512-token temporal sliding window (K=3) to detect Lateral Movement (TA0008)."
        ]),
        ("Stream B - Behavioral Pattern Detector (BPD)", [
            "Backbone: Compact sequence classifier operating on file-system telemetry and audit trails.",
            "Target Telemetry: Identifies defense impairment (T1562.001), shadow-copy deletion (T1490), and staging to trigger pre-encryption alerts before ransomware executes (T1486)."
        ]),
        ("Layer 3 - MITRE ATT&CK Temporal Correlation Engine", [
            "Graph-backed temporal correlation engine fuses LSA and BPD detections over sliding time windows (ΔT ≤ 300s).",
            "Employs KNN collaborative filtering across the ATT&CK matrix to predict the adversary's next 3 most probable techniques."
        ])
    ]
    
    first = True
    for heading, sub_bullets in s8_items:
        p1 = tf8.paragraphs[0] if first else tf8.add_paragraph()
        first = False
        set_paragraph_bullet(p1, heading, level=0, is_bold=True, sz_pt=14.5, color_rgb=(0x23, 0x1F, 0x20), space_after_pt=2.0)
        for sub in sub_bullets:
            p_sub = tf8.add_paragraph()
            set_paragraph_bullet(p_sub, sub, level=1, is_bold=False, sz_pt=13.0, color_rgb=(0x4B, 0x55, 0x63), space_after_pt=3.0)
        p_sub.space_after = Pt(7.0)

    # --- SLIDE 9: Why SLMs for Edge Systems? ---
    s9 = prs.slides[8]
    body_s9 = s9.shapes[1]
    body_s9.left = 1998300
    body_s9.top = 2200000
    body_s9.width = 15394200
    body_s9.height = 7600000
    tf9 = body_s9.text_frame
    tf9.clear()
    
    s9_items = [
        ("The 'Privacy Paradox' in Smart Manufacturing & Critical Infrastructure", [
            "Manufacturing plants generate sensitive telemetry containing proprietary CAD data, PLC program timings, and trade secrets.",
            "Cloud LLM inference introduces critical data privacy violations and network egress latency; on-premise SLMs guarantee zero data egress."
        ]),
        ("Edge Hardware Compatibility & Cost Efficiency", [
            "Traditional LLMs (>7B parameters) require multi-GPU server infrastructure costing >$15,000 and drawing substantial power.",
            "Fine-tuned compact SLMs (44M DeBERTa / 66M DistilBERT) execute directly on industrial PCs, gateway appliances, and commodity multi-core CPUs (<50MB RAM footprint)."
        ]),
        ("Deterministic Low-Latency Inference for Real-Time OT Interlocks", [
            "Factory automation and industrial safety interlocks operate on strict timing budgets (<20 ms).",
            "EdgeShield achieves 11.71 ms latency with INT8 quantization (>85 windows/s throughput), providing abundant headroom for busy industrial telemetry buffers."
        ]),
        ("Overcoming Domain Tokenization Bottlenecks", [
            "General LLM tokenizers fragment cybersecurity artifacts (GUIDs, SIDs, NTLM hashes) into meaningless subwords.",
            "EdgeShield adapts tokenization to retain atomic security entities, eliminating representation drift and boosting classification fidelity."
        ])
    ]
    
    first = True
    for heading, sub_bullets in s9_items:
        p1 = tf9.paragraphs[0] if first else tf9.add_paragraph()
        first = False
        set_paragraph_bullet(p1, heading, level=0, is_bold=True, sz_pt=14.5, color_rgb=(0x23, 0x1F, 0x20), space_after_pt=2.0)
        for sub in sub_bullets:
            p_sub = tf9.add_paragraph()
            set_paragraph_bullet(p_sub, sub, level=1, is_bold=False, sz_pt=13.0, color_rgb=(0x4B, 0x55, 0x63), space_after_pt=3.0)
        p_sub.space_after = Pt(7.0)

    # --- SLIDE 10: Publication Milestone ---
    s10 = prs.slides[9]
    body_s10 = s10.shapes[1]
    # Keep body text in top portion (top=2000000, height=2400000) so it doesn't overlap pictures below (top=4562123)
    body_s10.left = 1998300
    body_s10.top = 2000000
    body_s10.width = 15394200
    body_s10.height = 2400000
    tf10 = body_s10.text_frame
    tf10.clear()
    
    s10_items = [
        ("Accepted & Scheduled IEEE Conference Presentation:", 
         "Paper peer-reviewed and ACCEPTED at the 5th IEEE Technology & Engineering Management Conference - Asia Pacific (TEMSCON-ASPAC 2026)."),
        ("Conference Schedule & Venue:", 
         "Dates: 16 - 17 October 2026 | Venue: Marwadi University, Rajkot, Gujarat, India | IEEE Conference Record #69489."),
        ("Accepted Paper Title & Authors:", 
         "'EdgeShield: A Small Language Model Framework for Real-Time Detection of Lateral Movement and Ransomware Attacks' (Paper ID: 1571282183) - Gauravkumar Raval & Dr. Tejaskumar Bhatt."),
        ("Track & Scope:", 
         "Track: Strategic Management of Autonomous & Intelligent Systems (Cybersecurity & AI Track)."),
        ("Current Manuscript in Progress:", 
         "Extended journal version being prepared for IEEE Transactions: 'EdgeShield: Dual-Tier Small Language Model Framework for High-Throughput Lateral Movement and Pre-Encryption Ransomware Interception'.")
    ]
    
    first = True
    for heading, detail in s10_items:
        p = tf10.paragraphs[0] if first else tf10.add_paragraph()
        first = False
        full_text = f"{heading} {detail}"
        set_paragraph_bullet(p, full_text, level=0, is_bold=False, sz_pt=11.5, color_rgb=(0x23, 0x1F, 0x20), space_after_pt=3.0)
        # Bold only the heading part
        if len(p.runs) > 0:
            p.runs[0].font.bold = False

    # =========================================================================
    # FIX 5: Slide 16 Table Overlapping Title
    # =========================================================================
    print("\n--- Applying Fix 5: Slide 16 Title & Table Separation ---")
    s16 = prs.slides[15] # Slide 16
    title_s16 = s16.shapes[0]
    title_s16.left = 1998300
    title_s16.top = 581800
    title_s16.width = 15940200
    title_s16.height = 1200000
    p16 = title_s16.text_frame.paragraphs[0]
    p16.text = "Research Timeline & Milestones"
    p16.font.name = "Arial Rounded"
    p16.font.size = Pt(40)
    p16.font.bold = True
    p16.font.color.rgb = RGBColor(0x23, 0x1F, 0x20)
    
    # Position table cleanly below title
    tbl_s16 = s16.shapes[3] # Table graphicFrame
    tbl_s16.left = 1998300
    tbl_s16.top = 2200000
    tbl_s16.width = 15394200
    tbl_s16.height = 7600000

    # =========================================================================
    # FIX 6: Slide 19 References (Single Column List)
    # =========================================================================
    print("\n--- Applying Fix 6: Slide 19 Single Column References List ---")
    s19 = prs.slides[18] # Slide 19
    
    # Title
    title_s19 = s19.shapes[0]
    title_s19.left = 1998300
    title_s19.top = 581800
    title_s19.width = 15940200
    title_s19.height = 900000
    p19 = title_s19.text_frame.paragraphs[0]
    p19.text = "References"
    p19.font.name = "Arial Rounded"
    p19.font.size = Pt(40)
    p19.font.bold = True
    p19.font.color.rgb = RGBColor(0x23, 0x1F, 0x20)
    
    # Remove existing text boxes (except title)
    shapes_to_del = [sh for sh in s19.shapes if sh.has_text_frame and sh != title_s19]
    for sh in shapes_to_del:
        s19.shapes._spTree.remove(sh._element)
        
    # Create single full-width text box
    ref_box = s19.shapes.add_textbox(1400000, 1600000, 16200000, 8500000)
    tf_ref = ref_box.text_frame
    tf_ref.word_wrap = True
    tf_ref.margin_left = tf_ref.margin_top = tf_ref.margin_right = tf_ref.margin_bottom = 0
    
    apa_refs = [
        "Alghamdi, M., et al. (2025). MITRE ATT&CK applications in cybersecurity and the way forward. arXiv preprint arXiv:2502.10825.",
        "Kritika, E. (2024). A comprehensive literature review on ransomware detection using deep learning. Computer Science and Applications, 2, pp. 1-14.",
        "Li, W., et al. (2025). Exploring the role of large language models in cybersecurity: A systematic survey. arXiv preprint arXiv:2504.15622.",
        "Papageorgiou, C., Karydas, A., & Schiliro, D. (2025). Leveraging large language models for scalable and explainable cybersecurity log analysis. Journal of Cybersecurity and Privacy, 5(3), pp. 412-431.",
        "Ferrag, M. A., Maglaras, L., & Janicke, H. (2024). Harnessing the power of language models in cybersecurity: A comprehensive review. Journal of Network and Computer Applications, 228, p. 103912.",
        "Lu, Z., et al. (2024). Small language models: Survey, measurements, and insights. arXiv preprint arXiv:2409.15790.",
        "Tihanyi, S., et al. (2025). Toward cybersecurity-expert small language models. arXiv preprint arXiv:2510.14113.",
        "UpSight Security. (2024). Small language models against ransomware. UpSight AI Whitepaper. https://upsight.ai/small-language-models/",
        "Xu, J., & Wang, X. (2024). Large language models for cyber security: A systematic literature review. arXiv preprint arXiv:2405.04760.",
        "Zheng, J., et al. (2025). When LLMs meet cybersecurity: A systematic literature review. Cybersecurity, 8(1), pp. 1-28.",
        "Lu, Z., et al. (2025). Demystifying small language models for edge deployment. In Proceedings of the 63rd Annual Meeting of the Association for Computational Linguistics (ACL 2025), pp. 1-15.",
        "Palo Alto Networks. (2025). How small language models are quietly revolutionizing cybersecurity. Palo Alto Networks Technical Insights.",
        "MITRE Corporation. (2025). Lateral movement (Tactic TA0008). MITRE ATT&CK Enterprise Matrix. https://attack.mitre.org/tactics/TA0008/",
        "Carvajal, B., et al. (2024). Detecting lateral movement: A systematic survey. Heliyon, 10(4), pp. e25841-e25858.",
        "Chen, H., et al. (2023). Fuchikoma: NLP and neural network-based autonomous threat hunting. In Proceedings of the IEEE Symposium on Security and Privacy (S&P 2023), pp. 1240-1256.",
        "Okada, S., et al. (2024). ATT&CK technique extraction from Windows logs for lateral movement path identification. In Proceedings of the 40th Annual Computer Security Applications Conference (ACSAC 2024), pp. 312-325.",
        "Akhtar, A., Baker, T., & Ray, P. (2024). A comprehensive literature review on ransomware detection using deep learning. Journal of Information Security and Applications, 81, p. 103714.",
        "Boffa, M., et al. (2024). LogPrecis: Unleashing language models for automated malicious log analysis. Computers & Security, 137, p. 103612.",
        "Xu, H., et al. (2023). Efficient ransomware detection via portable executable file image analysis by LLaMA-7B. In Proceedings of the AAAI Workshop on Artificial Intelligence for Cyber Security, pp. 45-52.",
        "Meftah, S., et al. (2025). Fine-tuning small language models for accurate and private CWE detection in Python code. arXiv preprint arXiv:2504.16584.",
        "Khan, M., et al. (2025). Large language models for Security Operations Centers: A comprehensive survey. arXiv preprint arXiv:2509.10858.",
        "Ki, Y., et al. (2023). Malware API call sequence analysis using dynamic behavioral signatures. Journal of Information Security, 14(2), pp. 115-132.",
        "Kuwano, T., et al. (2022). KNN-based collaborative filtering for ATT&CK TTP prediction. In Proceedings of the ACM Cloud Computing Security Workshop (CCSW 2022), pp. 55-66.",
        "Saeed, A., et al. (2025). A survey on edge computing security challenges: Classification, threats, and mitigation strategies. Future Internet, 17(4), pp. 142-168.",
        "Lin, Z., et al. (2025). Can small language models reliably resist jailbreak attacks? A comprehensive evaluation. arXiv preprint arXiv:2503.06519."
    ]
    
    for i, ref_text in enumerate(apa_refs):
        p = tf_ref.paragraphs[0] if i == 0 else tf_ref.add_paragraph()
        p.text = f"[{i+1}]  {ref_text}"
        p.font.name = "Calibri"
        p.font.size = Pt(8.5)
        p.font.color.rgb = RGBColor(0x23, 0x1F, 0x20)
        p.space_after = Pt(2.5)

    prs.save(output_pptx)
    print(f"\nSuccessfully applied all 6 fixes to {output_pptx}!")

if __name__ == "__main__":
    fix_presentation()
