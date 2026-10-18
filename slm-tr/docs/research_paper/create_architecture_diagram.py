"""
create_architecture_diagram.py
==============================
Generates publication-quality, printer-friendly (light background, B&W readable, high-contrast)
diagrams for EdgeShield:
1. High-resolution PNG diagram (2600x1900 @ 300 DPI) formatted for IEEE/ACM/Elsevier journals.
2. Clean SVG vector diagram.
"""

import os
from PIL import Image, ImageDraw, ImageFont

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
PNG_PATH = os.path.join(OUTPUT_DIR, "edgeshield_architecture.png")
SVG_PATH = os.path.join(OUTPUT_DIR, "edgeshield_architecture.svg")

def generate_svg():
    svg_content = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1300 920" width="1300" height="920">
  <defs>
    <style>
      .main-title { font-family: 'Segoe UI', Arial, sans-serif; font-size: 22px; font-weight: bold; fill: #111827; }
      .box-title { font-family: 'Segoe UI', Arial, sans-serif; font-size: 16px; font-weight: bold; fill: #111827; }
      .box-desc { font-family: 'Segoe UI', Arial, sans-serif; font-size: 13.5px; fill: #374151; }
      .box-highlight { font-family: 'Segoe UI', Arial, sans-serif; font-size: 13px; font-weight: bold; fill: #1f2937; }
      .badge-text { font-family: 'Segoe UI', Arial, sans-serif; font-size: 12px; font-weight: bold; fill: #ffffff; }
      .branch-text { font-family: 'Segoe UI', Arial, sans-serif; font-size: 13px; font-weight: bold; fill: #111827; }
      .arrow { stroke: #374151; stroke-width: 2.2; fill: none; marker-end: url(#arrowhead); }
      .arrow-dash { stroke: #4b5563; stroke-width: 2.2; stroke-dasharray: 6 4; fill: none; marker-end: url(#arrowhead); }
    </style>
    <marker id="arrowhead" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
      <polygon points="0 0, 8 3, 0 6" fill="#374151" />
    </marker>
  </defs>

  <!-- Clean White Background (Printer-friendly) -->
  <rect width="1300" height="920" fill="#ffffff" />

  <!-- Outer Boundary Container with light gray border -->
  <rect x="25" y="20" width="1250" height="880" fill="#ffffff" stroke="#9ca3af" stroke-width="1.8" rx="8" />
  <text x="55" y="58" class="main-title">EdgeShield Dual-Tier Architecture: Inline Stream Detection &amp; Explainable Triage</text>

  <!-- 1. Enterprise Telemetry Stream -->
  <g>
    <rect x="360" y="85" width="580" height="70" rx="6" fill="#f9fafb" stroke="#374151" stroke-width="1.8" />
    <text x="650" y="113" text-anchor="middle" class="box-title">Enterprise Security Telemetry Stream</text>
    <text x="650" y="137" text-anchor="middle" class="box-desc">Windows Sysmon (EIDs 1, 3, 7, 10, 11) &#8226; Security Event Log (EIDs 4624, 4672)</text>
  </g>

  <!-- Arrow 1 -->
  <path d="M 650 155 L 650 185" class="arrow" />

  <!-- 2. Domain-Specialized Tokenizer -->
  <g>
    <rect x="360" y="185" width="580" height="70" rx="6" fill="#f9fafb" stroke="#374151" stroke-width="1.8" />
    <text x="650" y="213" text-anchor="middle" class="box-title">Domain-Specialized Security Tokenizer</text>
    <text x="650" y="237" text-anchor="middle" class="box-desc">Preserves Atomic SIDs, GUIDs, Hashes, IPv4 CIDRs (-38.4% Token Fragmentation)</text>
  </g>

  <!-- Arrow 2 -->
  <path d="M 650 255 L 650 285" class="arrow" />

  <!-- 3. Temporal Sliding Ring Buffer -->
  <g>
    <rect x="360" y="285" width="580" height="70" rx="6" fill="#f9fafb" stroke="#374151" stroke-width="1.8" />
    <text x="650" y="313" text-anchor="middle" class="box-title">Temporal Sliding-Window Ring Buffer (K = 3..5)</text>
    <text x="650" y="337" text-anchor="middle" class="box-desc">Multi-Step Kill-Chain Correlation &#8226; Resolves Dual-Use LOLBin Ambiguity</text>
  </g>

  <!-- Arrow 3 -->
  <path d="M 650 355 L 650 385" class="arrow" />

  <!-- 4. Tier 1: Log Semantic Analyzer (Double Border for prominence) -->
  <g>
    <rect x="300" y="385" width="700" height="125" rx="8" fill="#f3f4f6" stroke="#111827" stroke-width="2.2" />
    <rect x="320" y="398" width="76" height="24" rx="4" fill="#374151" />
    <text x="358" y="415" text-anchor="middle" class="badge-text">TIER 1</text>
    <text x="660" y="417" text-anchor="middle" class="box-title">Inline Log Semantic Analyzer (LSA)</text>
    <text x="650" y="450" text-anchor="middle" class="box-desc">Backbone: DeBERTa-v3 Small (44M Parameters) &#8226; Disentangled Relative Attention</text>
    <text x="650" y="480" text-anchor="middle" class="box-highlight">INT8 ONNX Runtime: 11.71 &#177; 0.62 ms / window &#8226; 85.40 win/s &#8226; 51.1 MB RAM Footprint</text>
  </g>

  <!-- Decision Branches -->
  <!-- Branch Left: Class 0 Normal -->
  <path d="M 430 510 L 430 550 L 260 550 L 260 600" class="arrow" />
  <rect x="145" y="535" width="230" height="28" rx="4" fill="#ffffff" stroke="#4b5563" stroke-width="1.5" />
  <text x="260" y="554" text-anchor="middle" class="branch-text">[Class 0: Normal (&gt;99% stream)]</text>

  <!-- Normal Discard Engine -->
  <g>
    <rect x="110" y="600" width="300" height="110" rx="6" fill="#f9fafb" stroke="#4b5563" stroke-width="1.8" />
    <text x="260" y="638" text-anchor="middle" class="box-title">Fast Discard / Archive Engine</text>
    <text x="260" y="666" text-anchor="middle" class="box-desc">Zero Alert Flooding</text>
    <text x="260" y="688" text-anchor="middle" class="box-desc">&lt; 0.01 ms Overhead on Safe Logs</text>
  </g>

  <!-- Branch Right: Class 1 / 2 Malicious -->
  <path d="M 870 510 L 870 550 L 950 550 L 950 600" class="arrow" />
  <rect x="800" y="535" width="300" height="28" rx="4" fill="#ffffff" stroke="#111827" stroke-width="1.8" />
  <text x="950" y="554" text-anchor="middle" class="branch-text">[Class 1/2: Malicious / Anomalous Window]</text>

  <!-- 5. Tier 2: Causal Reasoner (Proposed / Future Work Extension) -->
  <g>
    <rect x="630" y="600" width="640" height="125" rx="8" fill="#f3f4f6" stroke="#111827" stroke-width="2.2" />
    <rect x="650" y="613" width="76" height="24" rx="4" fill="#4b5563" />
    <text x="688" y="630" text-anchor="middle" class="badge-text">TIER 2</text>
    <text x="960" y="632" text-anchor="middle" class="box-title">Causal Explainable Reasoner (On-Demand Triage Architecture)</text>
    <text x="950" y="665" text-anchor="middle" class="box-desc">Target Backbone: Qwen2.5-1.5B-Instruct / Phi-3-mini (1.5B–3.8B Weights)</text>
    <text x="950" y="695" text-anchor="middle" class="box-highlight">Proposed Architecture: SFT Structured JSON Prompting &#8226; LoRA (r=16, alpha=32)</text>
  </g>

  <!-- Arrow Tier 2 to Output -->
  <path d="M 950 725 L 950 755" class="arrow" />

  <!-- 6. Structured SOC Output -->
  <g>
    <rect x="630" y="755" width="640" height="105" rx="6" fill="#f9fafb" stroke="#374151" stroke-width="1.8" />
    <text x="950" y="785" text-anchor="middle" class="box-title">Target Structured Incident Alert &#8226; SIEM / SOAR Playbooks</text>
    <text x="950" y="812" text-anchor="middle" class="box-desc">Granular MITRE ATT&amp;CK Mapping (T1021, T1550) &#8226; Automated Host Isolation</text>
    <text x="950" y="836" text-anchor="middle" class="box-highlight">Synthesizes Human-Readable Forensic Narrative for Level-1 SOC Analysts</text>
  </g>

</svg>"""
    with open(SVG_PATH, "w", encoding="utf-8") as f:
        f.write(svg_content)
    print(f"[+] Clean, printer-friendly SVG generated: {SVG_PATH}")

def generate_png():
    width = 2600
    height = 1900
    
    # White background for pure printer friendliness
    img = Image.new("RGB", (width, height), color="#FFFFFF")
    draw = ImageDraw.Draw(img)

    # Fonts
    try:
        font_header = ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf", 44)
        font_box_title = ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf", 32)
        font_box_desc = ImageFont.truetype(r"C:\Windows\Fonts\segoeui.ttf", 25)
        font_box_desc_bold = ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf", 25)
        font_badge = ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf", 22)
        font_label = ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf", 24)
    except:
        font_header = font_box_title = font_box_desc = font_box_desc_bold = font_badge = font_label = ImageFont.load_default()

    # Outer Container
    draw.rounded_rectangle([40, 35, width - 40, height - 35], radius=20, fill="#FFFFFF", outline="#9CA3AF", width=3)
    draw.text((90, 75), "EdgeShield Dual-Tier Architecture: Inline Stream Detection & Explainable Triage", fill="#111827", font=font_header)

    def draw_box(x, y, w, h, fill, outline, title, desc_lines, badge_text=None, badge_color=None, highlight=None, outline_width=3):
        draw.rounded_rectangle([x, y, x + w, y + h], radius=16, fill=fill, outline=outline, width=outline_width)
        
        # Header area
        if badge_text and badge_color:
            b_w = 120
            draw.rounded_rectangle([x + 30, y + 25, x + 30 + b_w, y + 67], radius=8, fill=badge_color)
            t_bb = font_badge.getbbox(badge_text)
            tw = t_bb[2] - t_bb[0]
            draw.text((x + 30 + (b_w - tw) // 2, y + 33), badge_text, fill="#FFFFFF", font=font_badge)
            
            t_bbox = font_box_title.getbbox(title)
            t_w = t_bbox[2] - t_bbox[0]
            draw.text((x + 180 + (w - 210 - t_w) // 2, y + 27), title, fill="#111827", font=font_box_title)
        else:
            t_bbox = font_box_title.getbbox(title)
            t_w = t_bbox[2] - t_bbox[0]
            draw.text((x + (w - t_w) // 2, y + 28), title, fill="#111827", font=font_box_title)
        
        curr_y = y + 84
        for line in desc_lines:
            d_bbox = font_box_desc.getbbox(line)
            d_w = d_bbox[2] - d_bbox[0]
            draw.text((x + (w - d_w) // 2, curr_y), line, fill="#374151", font=font_box_desc)
            curr_y += 42
            
        if highlight:
            curr_y += 6
            h_bbox = font_box_desc_bold.getbbox(highlight)
            h_w = h_bbox[2] - h_bbox[0]
            draw.text((x + (w - h_w) // 2, curr_y), highlight, fill="#111827", font=font_box_desc_bold)

    def draw_arrow(x1, y1, x2, y2, color="#374151"):
        draw.line([x1, y1, x2, y2], fill=color, width=5)
        arrow_size = 14
        if x1 == x2: # vertical down
            draw.polygon([(x2 - arrow_size, y2 - arrow_size * 1.5), (x2 + arrow_size, y2 - arrow_size * 1.5), (x2, y2)], fill=color)

    # 1. Telemetry Stream (Light gray box, dark gray border)
    draw_box(720, 160, 1160, 140, "#F9FAFB", "#374151", "Enterprise Security Telemetry Stream",
             ["Windows Sysmon (EIDs 1, 3, 7, 10, 11)  •  Security Event Log (EIDs 4624, 4672)"])

    draw_arrow(1300, 300, 1300, 360)

    # 2. Specialized Tokenizer
    draw_box(720, 360, 1160, 140, "#F9FAFB", "#374151", "Domain-Specialized Security Tokenizer",
             ["Preserves Atomic SIDs, GUIDs, Hashes, IPv4 CIDRs  •  -38.4% Token Fragmentation"])

    draw_arrow(1300, 500, 1300, 560)

    # 3. Sliding Ring Buffer
    draw_box(720, 560, 1160, 140, "#F9FAFB", "#374151", "Temporal Sliding-Window Ring Buffer (K = 3..5)",
             ["Multi-Step Temporal Correlation  •  Resolves Dual-Use LOLBin Administrative Ambiguity"])

    draw_arrow(1300, 700, 1300, 760)

    # 4. Tier 1 LSA (Slightly darker tint for hierarchy, thick border)
    draw_box(600, 760, 1400, 240, "#F3F4F6", "#111827", "Inline Log Semantic Analyzer (LSA)",
             ["Backbone: DeBERTa-v3 Small (44M Parameters)  •  Disentangled Content-Position Relative Attention"],
             badge_text="TIER 1", badge_color="#374151",
             highlight="INT8 ONNX Runtime: 11.71 ± 0.62 ms / window  •  85.40 win/s  •  51.1 MB RAM Footprint",
             outline_width=4)

    # Flow Left to Normal
    draw.line([950, 1000, 950, 1070], fill="#374151", width=5)
    draw.line([950, 1070, 480, 1070], fill="#374151", width=5)
    draw_arrow(480, 1070, 480, 1180, color="#374151")

    # Normal Badge
    draw.rounded_rectangle([200, 1100, 760, 1150], radius=10, fill="#FFFFFF", outline="#4B5563", width=2)
    draw.text((225, 1111), "Class 0: Normal (>99% of telemetry stream)", fill="#111827", font=font_label)

    # Discard Box
    draw_box(180, 1180, 600, 200, "#F9FAFB", "#4B5563", "Fast Discard / Archive Engine",
             ["Zero SOC Alert Flooding", "< 0.01 ms Overhead on Benign System Events"])

    # Flow Right to Tier 2
    draw.line([1650, 1000, 1650, 1070], fill="#111827", width=5)
    draw.line([1650, 1070, 1900, 1070], fill="#111827", width=5)
    draw_arrow(1900, 1070, 1900, 1180, color="#111827")

    # Malicious Badge
    draw.rounded_rectangle([1590, 1100, 2210, 1150], radius=10, fill="#FFFFFF", outline="#111827", width=3)
    draw.text((1615, 1111), "Class 1/2: Malicious / Anomalous Window", fill="#111827", font=font_label)

    # 5. Tier 2 Causal Reasoner (Proposed architecture)
    draw_box(1250, 1180, 1220, 250, "#F3F4F6", "#111827", "Causal Explainable Reasoner (On-Demand Triage Architecture)",
             ["Target Backbone: Qwen2.5-1.5B-Instruct / Phi-3-mini-4k-instruct (1.5B–3.8B Weights)"],
             badge_text="TIER 2", badge_color="#4B5563",
             highlight="Proposed Architecture: SFT Structured JSON Prompting  •  LoRA (r=16, alpha=32)",
             outline_width=4)

    draw_arrow(1860, 1430, 1860, 1490)

    # 6. Structured SOC Output
    draw_box(1250, 1490, 1220, 210, "#F9FAFB", "#374151", "Target Structured Incident Alert  •  SIEM / SOAR Playbooks",
             ["Granular MITRE ATT&CK Mapping (T1021, T1550)  •  Automated Host Isolation"],
             highlight="Synthesizes Human-Readable Forensic Narrative for Level-1 SOC Analysts")

    img.save(PNG_PATH, "PNG", dpi=(300, 300))
    print(f"[+] Printer-friendly high-resolution PNG generated: {PNG_PATH}")

if __name__ == "__main__":
    generate_svg()
    generate_png()
