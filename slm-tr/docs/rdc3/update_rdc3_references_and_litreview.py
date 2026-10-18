"""
update_rdc3_references_and_litreview.py
Updates RDC3_EdgeShield_Final.pptx:
1. Updates Slide 4 (Literature Review) to link the 5 core thematic research threads directly to EdgeShield's paper references and methodology.
2. Updates Slide 19 (References) to contain the Top 25 peer-reviewed citations from the EdgeShield paper in an elegant 2-column academic layout.
"""

import pptx
from pptx.util import Pt, Inches
from pptx.dml.color import RGBColor

def update_presentation():
    pptx_path = "RDC3_EdgeShield_Final.pptx"
    prs = pptx.Presentation(pptx_path)
    print(f"Loaded {pptx_path}. Total slides: {len(prs.slides)}")

    # =========================================================================
    # 1. UPDATE SLIDE 4: LITERATURE REVIEW (THEMATIC MAPPING TABLE)
    # =========================================================================
    s4 = prs.slides[3]
    # Check that shapes[0] is the table
    tbl_shape = [s for s in s4.shapes if s.has_table][0]
    tbl = tbl_shape.table
    print(f"Slide 4 table: {len(tbl.rows)} rows x {len(tbl.columns)} cols")

    # Table columns: ['Thematic Research Thread & Refs', 'Representative Approaches', 'Datasets & Scope', 'Major Findings & EdgeShield Justification']
    lit_rows = [
        [
            "Thematic Research Area & Refs",
            "State-of-the-Art Approaches",
            "Evaluated Datasets",
            "Findings & Architectural Link to EdgeShield"
        ],
        [
            "1. Small Language Models (SLMs) in SecOps\n[6] Lu et al. (2024)\n[7] Tihanyi et al. (2025)\n[11] Lu et al. (ACL 2025)",
            "Specialized sub-8B models (CyberPal 2.0, 4B-20B) trained on SecKnowledge 2.0; edge benchmarking on consumer CPUs.",
            "SecKnowledge 2.0, enterprise SOC incident telemetry, hardware edge testbeds",
            "Proves compact SLMs match/exceed frontier LLMs in specialized SOC loops with lower compute. Directly motivates EdgeShield's 44M DeBERTa & 1.5B reasoner design."
        ],
        [
            "2. Lateral Movement Detection (TA0008)\n[13] MITRE ATT&CK (2025)\n[14] Carvajal et al. (2024)\n[15] Chen et al. (2023)\n[16] Okada et al. (2024)",
            "Systematic survey of 53 LMD works; Fuchikoma NLP + neural graph threat hunting; graph-based movement path extraction.",
            "Windows Event Logs (4624, 4672, Kerberos), DARPA OpTC, enterprise host logs",
            "Identifies critical research gap: zero prior works applied domain SLMs directly to raw authentication streams. Establishes EdgeShield Stream A (LSA) sliding-window design."
        ],
        [
            "3. Pre-Encryption Ransomware Defense\n[2] Kritika (2024)\n[8] UpSight Security (2024)\n[18] Boffa et al. (2024)\n[19] Xu et al. (2023)",
            "UpSight 2,000-token ATT&CK vocabulary head; LogPrecis LLM log triage; PE binary image conversion via LLaMA-7B.",
            "Curated multi-stage ransomware telemetry, ATT&CK Enterprise Matrix, host API logs",
            "Shows ransomware damage occurs post-lateral movement; early interception requires monitoring defense impairment & shadow deletion. Justifies EdgeShield Stream B (BPD)."
        ],
        [
            "4. Predictive Correlation & Threat Hunting\n[1] Alghamdi et al. (2025)\n[21] Khan et al. (2025)\n[22] Ki et al. (2023)\n[23] Kuwano et al. (2022)",
            "KNN collaborative filtering for ATT&CK TTP prediction; LLMs for SOC alert fusion; API call dynamic sequence alignment.",
            "MITRE ATT&CK v15 enterprise matrix, multi-stage attack scenarios (ALPHV, LockBit)",
            "Decoupled detect-then-decide paradigm: individual stream detections must be fused across temporal windows to forecast next-hop adversary TTPs (EdgeShield Layer 3 Engine)."
        ],
        [
            "5. On-Premise Edge & Zero-Trust Defense\n[5] Ferrag et al. (2024)\n[12] Palo Alto Networks (2025)\n[24] Saeed et al. (2025)\n[25] Lin et al. (2025)",
            "Zero Trust Architecture; edge inline SLM packet filters; jailbreak robustness evaluations of compact language models.",
            "Industrial IoT & edge systems, enterprise endpoint perimeters, OT telemetry",
            "Enforces that security telemetry must never egress the factory/enterprise boundary ('Privacy Paradox'). Validates EdgeShield's on-premise INT8 ONNX deployment."
        ],
        [
            "6. Explainable AI & Domain Tokenization\n[3] Li et al. (2025)\n[4] Papageorgiou et al. (2025)\n[20] Meftah et al. (2025)\n[26] Adewale et al. (2025)",
            "Explainable cybersecurity log analysis; fine-tuned compact encoders (codegen-mono 350M) for Top-25 CWE vulnerability detection.",
            "Security logs, CWE corpus, tokenization subword vocabularies",
            "Demonstrates that standard BPE fragmenting SIDs/hashes impairs accuracy; domain-adapted tokenization with causal JSON reasoning provides transparent operator triage."
        ],
        [
            "7. Industry Operational Baseline Trends\n[9] Xu & Wang (2024)\n[10] Zheng et al. (2025)\n[17] Akhtar et al. (2024)",
            "Systematic literature reviews screening >40,000 papers; evolutionary analysis of ransomware extortion narratives.",
            "Over 300 peer-reviewed security papers, global ransomware incident datasets",
            "Confirms exponential rise in AI-automated extortion and Living-off-the-Land abuse, setting the benchmark requirements for sub-15ms real-time edge response."
        ]
    ]

    # Populate Slide 4 Table
    for r_idx, row in enumerate(lit_rows):
        for c_idx, val in enumerate(row):
            cell = tbl.cell(r_idx, c_idx)
            cell.text = val
            p = cell.text_frame.paragraphs[0]
            p.font.name = "Calibri"
            if r_idx == 0:
                p.font.size = Pt(12)
                p.font.bold = True
                cell.fill.solid()
                cell.fill.fore_color.rgb = RGBColor(30, 41, 59)
                p.font.color.rgb = RGBColor(255, 255, 255)
            else:
                p.font.size = Pt(10.5)
                p.font.color.rgb = RGBColor(0x23, 0x1F, 0x20)
                if c_idx == 0:
                    p.font.bold = True
                else:
                    p.font.bold = False

    print("Slide 4 (Literature Review Table) updated successfully.")

    # =========================================================================
    # 2. UPDATE SLIDE 19: REFERENCES (TOP 25 EDGESHIELD PAPER CITATIONS)
    # =========================================================================
    s19 = prs.slides[18]
    # Remove existing long text box (shape index 3)
    s3_old = [s for s in s19.shapes if s.has_text_frame and len(s.text_frame.text) > 100][0]
    s19.shapes._spTree.remove(s3_old._element)

    top25_refs_col1 = [
        "[1] M. Alghamdi et al., \"MITRE ATT&CK Applications in Cybersecurity and The Way Forward,\" arXiv:2502.10825, Feb. 2025.",
        "[2] Er. Kritika, \"A comprehensive literature review on ransomware detection using deep learning,\" Computer Science and Applications, vol. 2, 2024.",
        "[3] W. Li et al., \"Exploring the Role of Large Language Models in Cybersecurity: A Systematic Survey,\" arXiv:2504.15622, Apr. 2025.",
        "[4] C. Papageorgiou et al., \"Leveraging Large Language Models for Scalable and Explainable Cybersecurity Log Analysis,\" J. Cybersecur. Priv., vol. 5, no. 3, 2025.",
        "[5] A. Ferrag et al., \"Harnessing the power of language models in cybersecurity: A comprehensive review,\" J. Netw. Comp. App., 2024.",
        "[6] Z. Lu et al., \"Small Language Models: Survey, Measurements, and Insights,\" arXiv:2409.15790, Sep. 2024, updated Feb. 2025.",
        "[7] S. Tihanyi et al., \"Toward Cybersecurity-Expert Small Language Models,\" arXiv:2510.14113, Oct. 2025.",
        "[8] UpSight Security, \"Small Language Models Against Ransomware,\" UpSight AI, 2024. Available: https://upsight.ai/small-language-models/",
        "[9] J. Xu and X. Wang, \"Large Language Models for Cyber Security: A Systematic Literature Review,\" arXiv:2405.04760, May 2024.",
        "[10] J. Zheng et al., \"When LLMs meet cybersecurity: a systematic literature review,\" Cybersecurity, Springer, Feb. 2025.",
        "[11] Z. Lu et al., \"Demystifying Small Language Models for Edge Deployment,\" in Proc. ACL 2025, Jul. 2025.",
        "[12] Palo Alto Networks, \"How Small Language Models are Quietly Revolutionizing Cybersecurity,\" Palo Alto Networks Community Blog, 2025.",
        "[13] MITRE Corporation, \"Lateral Movement, Tactic TA0008,\" MITRE ATT&CK Enterprise. Available: https://attack.mitre.org/tactics/TA0008/"
    ]

    top25_refs_col2 = [
        "[14] B. Carvajal et al., \"Detecting lateral movement: A systematic survey,\" Heliyon, vol. 10, 2024.",
        "[15] H. Chen et al., \"Fuchikoma: NLP and neural network-based autonomous threat hunting,\" in Proc. IEEE Symp. Security Privacy, 2023.",
        "[16] S. Okada et al., \"ATT&CK technique extraction from Windows logs for lateral movement path identification,\" in Proc. ACSAC, 2024.",
        "[17] A. Akhtar et al., \"A comprehensive literature review on ransomware detection using deep learning,\" Computer Science and Applications, 2024.",
        "[18] M. Boffa et al., \"LogPrecis: Unleashing language models for automated malicious log analysis,\" Computers & Security, vol. 137, 2024.",
        "[19] H. Xu et al., \"Efficient ransomware detection via portable executable file image analysis by LLaMA-7B,\" in Proc. AAAI Workshop, 2023.",
        "[20] S. Meftah et al., \"Fine-tuning Small Language Models for Accurate and Private CWE Detection in Python Code,\" arXiv:2504.16584, Apr. 2025.",
        "[21] M. Khan et al., \"Large Language Models for Security Operations Centers: A Comprehensive Survey,\" arXiv:2509.10858, Sep. 2025.",
        "[22] Y. Ki et al., \"Malware API call sequence analysis using dynamic behavioral signatures,\" J. Info. Security, 2023.",
        "[23] T. Kuwano et al., \"KNN-based collaborative filtering for ATT&CK TTP prediction,\" in Proc. CCSW, 2022.",
        "[24] A. Saeed et al., \"A Survey on Edge Computing Security Challenges: Classification, Threats, and Mitigation Strategies,\" Future Internet, vol. 17, no. 4, Apr. 2025.",
        "[25] Z. Lin et al., \"Can Small Language Models Reliably Resist Jailbreak Attacks? A Comprehensive Evaluation,\" arXiv:2503.06519, Mar. 2025."
    ]

    # Create two elegant side-by-side text boxes on Slide 19
    col1 = s19.shapes.add_textbox(1156591, 1350000, 8100000, 8400000)
    col2 = s19.shapes.add_textbox(9550000, 1350000, 8100000, 8400000)

    for col_box, ref_list in [(col1, top25_refs_col1), (col2, top25_refs_col2)]:
        tf = col_box.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
        for i, ref_text in enumerate(ref_list):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.text = ref_text
            p.font.name = "Calibri"
            p.font.size = Pt(9.5)
            p.font.color.rgb = RGBColor(0x23, 0x1F, 0x20)
            p.space_after = Pt(4)

    print("Slide 19 (References) updated with Top 25 citations in 2-column format.")

    prs.save("RDC3_EdgeShield_Final.pptx")
    print("All slides updated and saved successfully in RDC3_EdgeShield_Final.pptx!")

if __name__ == "__main__":
    update_presentation()
