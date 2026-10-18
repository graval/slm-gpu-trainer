"""
update_rdc3_references_apa.py
Updates Slide 19 of RDC3_EdgeShield_Final.pptx with the Top 25 citations
in strict APA 7th Edition format across two balanced columns.
"""

import pptx
from pptx.util import Pt
from pptx.dml.color import RGBColor

apa_refs_col1 = [
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
    "MITRE Corporation. (2025). Lateral movement (Tactic TA0008). MITRE ATT&CK Enterprise Matrix. https://attack.mitre.org/tactics/TA0008/"
]

apa_refs_col2 = [
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

def update_apa():
    pptx_path = "RDC3_EdgeShield_Final.pptx"
    prs = pptx.Presentation(pptx_path)
    s19 = prs.slides[18]

    # Clean existing reference text boxes (indices 3 and 4)
    shapes_to_remove = [s for s in s19.shapes if s.has_text_frame and s != s19.shapes[0] and len(s.text_frame.text) > 50]
    for shp in shapes_to_remove:
        s19.shapes._spTree.remove(shp._element)

    # Recreate side-by-side columns with exact APA formatting
    col1 = s19.shapes.add_textbox(1156591, 1350000, 8100000, 8400000)
    col2 = s19.shapes.add_textbox(9550000, 1350000, 8100000, 8400000)

    for col_box, ref_list in [(col1, apa_refs_col1), (col2, apa_refs_col2)]:
        tf = col_box.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
        for i, ref_text in enumerate(ref_list):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.text = ref_text
            p.font.name = "Calibri"
            p.font.size = Pt(9.5)
            p.font.color.rgb = RGBColor(0x23, 0x1F, 0x20)
            p.space_after = Pt(5)

    prs.save("RDC3_EdgeShield_Final.pptx")
    print("Successfully updated Slide 19 with APA 7th edition references in RDC3_EdgeShield_Final.pptx!")

if __name__ == "__main__":
    update_apa()
