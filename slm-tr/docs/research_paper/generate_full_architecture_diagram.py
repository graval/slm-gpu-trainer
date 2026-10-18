"""
generate_full_architecture_diagram.py
====================================
Generates comprehensive, publication-quality architectural diagrams for EdgeShield
covering BOTH Stream A (LSA), Stream B (BPD), the MITRE ATT&CK Correlation Engine,
and Tier 2 Generative XAI.

Outputs:
1. High-resolution SVG: edgeshield_architecture_full.svg
2. High-resolution PNG: edgeshield_architecture_full.png (300 DPI, 2800x2000)
"""

import os
import shutil
from PIL import Image, ImageDraw, ImageFont

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
SVG_PATH = os.path.join(OUTPUT_DIR, "edgeshield_architecture_full.svg")
PNG_PATH = os.path.join(OUTPUT_DIR, "edgeshield_architecture_full.png")
ARTIFACT_DIR = r"C:\Users\gaura\.gemini\antigravity\brain\7f69abc7-e0bb-4d2a-8d69-27a0ad984ed4"


def generate_svg():
    svg_content = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1440 1020" width="1440" height="1020">
  <defs>
    <style>
      .main-title { font-family: 'Segoe UI', Arial, sans-serif; font-size: 22px; font-weight: 800; fill: #0f172a; }
      .sub-title { font-family: 'Segoe UI', Arial, sans-serif; font-size: 13.5px; fill: #475569; font-weight: 500; }
      .box-title { font-family: 'Segoe UI', Arial, sans-serif; font-size: 15.5px; font-weight: 700; fill: #0f172a; }
      .box-desc { font-family: 'Segoe UI', Arial, sans-serif; font-size: 12.5px; fill: #334155; }
      .box-highlight { font-family: 'Segoe UI', Arial, sans-serif; font-size: 12.5px; font-weight: 700; fill: #0f172a; }
      .badge-text { font-family: 'Segoe UI', Arial, sans-serif; font-size: 11px; font-weight: 700; fill: #ffffff; letter-spacing: 0.5px; }
      .branch-text { font-family: 'Segoe UI', Arial, sans-serif; font-size: 12.5px; font-weight: 700; fill: #0f172a; }
      .arrow { stroke: #334155; stroke-width: 2.0; fill: none; marker-end: url(#arrowhead); }
      .arrow-blue { stroke: #0284c7; stroke-width: 2.2; fill: none; marker-end: url(#arrowhead-blue); }
      .arrow-purple { stroke: #7c3aed; stroke-width: 2.2; fill: none; marker-end: url(#arrowhead-purple); }
    </style>
    <marker id="arrowhead" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
      <polygon points="0 0, 8 3, 0 6" fill="#334155" />
    </marker>
    <marker id="arrowhead-blue" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
      <polygon points="0 0, 8 3, 0 6" fill="#0284c7" />
    </marker>
    <marker id="arrowhead-purple" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
      <polygon points="0 0, 8 3, 0 6" fill="#7c3aed" />
    </marker>
  </defs>

  <!-- Clean Background -->
  <rect width="1440" height="1020" fill="#ffffff" />
  <rect x="20" y="16" width="1400" height="988" fill="#ffffff" stroke="#cbd5e1" stroke-width="1.8" rx="8" />

  <!-- Header Banner -->
  <text x="50" y="52" class="main-title">EdgeShield End-to-End Architecture: Dual-Stream Inline Detection, Correlation &amp; Tier 2 XAI</text>
  <text x="50" y="74" class="sub-title">Decoupled Dual-Stream Detection (LSA + BPD) &#8226; MITRE ATT&amp;CK Threat Correlation &#8226; On-Demand Incident Triage &amp; Reporting</text>

  <!-- ========================================================================= -->
  <!-- 1. TOP: ENTERPRISE TELEMETRY INGESTION STREAM                             -->
  <!-- ========================================================================= -->
  <g>
    <rect x="340" y="94" width="760" height="66" rx="6" fill="#f8fafc" stroke="#475569" stroke-width="1.8" />
    <text x="720" y="120" text-anchor="middle" class="box-title">Enterprise Security Telemetry Ingestion Stream</text>
    <text x="720" y="142" text-anchor="middle" class="box-desc">Windows Sysmon (EIDs 1, 3, 7, 10, 11) &#8226; Security Event Log (EIDs 4624, 4625, 4672, Kerberos Auth Tickets)</text>
  </g>

  <!-- Branching Arrows from Top to Stream A and Stream B -->
  <path d="M 530 160 L 530 185 L 360 185 L 360 205" class="arrow-blue" />
  <path d="M 910 160 L 910 185 L 1080 185 L 1080 205" class="arrow-purple" />

  <!-- Stream Labels -->
  <rect x="220" y="172" width="280" height="26" rx="4" fill="#0284c7" />
  <text x="360" y="189" text-anchor="middle" class="badge-text">STREAM A: AUTHENTICATION &amp; IDENTITY</text>

  <rect x="940" y="172" width="280" height="26" rx="4" fill="#7c3aed" />
  <text x="1080" y="189" text-anchor="middle" class="badge-text">STREAM B: ENDPOINT BEHAVIOR &amp; PROCESSES</text>

  <!-- ========================================================================= -->
  <!-- 2. STREAM A & STREAM B TOKENIZERS                                         -->
  <!-- ========================================================================= -->
  <!-- Stream A Tokenizer -->
  <g>
    <rect x="70" y="205" width="580" height="74" rx="6" fill="#f0f9ff" stroke="#0284c7" stroke-width="1.6" />
    <text x="360" y="231" text-anchor="middle" class="box-title">Domain Security Tokenizer &amp; Sliding Window</text>
    <text x="360" y="251" text-anchor="middle" class="box-desc">Preserves Security IDs, IP Addresses, and Account Credentials</text>
    <text x="360" y="269" text-anchor="middle" class="box-desc">Temporal Sliding Window (Evaluates 3 to 5 Sequential Authentication Events)</text>
  </g>

  <!-- Stream B Tokenizer -->
  <g>
    <rect x="790" y="205" width="580" height="74" rx="6" fill="#faf5ff" stroke="#7c3aed" stroke-width="1.6" />
    <text x="1080" y="231" text-anchor="middle" class="box-title">Constrained Security Vocabulary Tokenizer</text>
    <text x="1080" y="251" text-anchor="middle" class="box-desc">Specialized Threat Vocabulary (Process Trees, System Calls, Command Flags)</text>
    <text x="1080" y="269" text-anchor="middle" class="box-desc">Filters Background Noise &#8226; Normalizes File &amp; Process Paths</text>
  </g>

  <!-- Arrows to Tier 1 Backbones -->
  <path d="M 360 279 L 360 305" class="arrow-blue" />
  <path d="M 1080 279 L 1080 305" class="arrow-purple" />

  <!-- ========================================================================= -->
  <!-- 3. TIER 1: SPECIALIZED SLM DETECTORS (LSA + BPD)                          -->
  <!-- ========================================================================= -->
  <!-- Tier 1A: LSA -->
  <g>
    <rect x="70" y="305" width="580" height="135" rx="8" fill="#f8fafc" stroke="#0f172a" stroke-width="2.2" />
    <rect x="90" y="318" width="80" height="22" rx="4" fill="#0284c7" />
    <text x="130" y="333" text-anchor="middle" class="badge-text">TIER 1A</text>
    <text x="380" y="335" text-anchor="middle" class="box-title">Log Semantic Analyzer (LSA)</text>
    <text x="360" y="364" text-anchor="middle" class="box-desc">Model Backbone: DeBERTa-v3 Small (44M Parameters)</text>
    <text x="360" y="386" text-anchor="middle" class="box-desc">Specialized Detection: Authentication Sequences &amp; Privilege Escalation</text>
    <text x="360" y="408" text-anchor="middle" class="box-desc">Detects Lateral Movement (Remote Services, Admin Shares, Pass-the-Hash)</text>
    <text x="360" y="428" text-anchor="middle" class="box-highlight">Ultra-Fast Edge Runtime: ~11.7 ms / window &#8226; Low Footprint (~50 MB RAM)</text>
  </g>

  <!-- Tier 1B: BPD -->
  <g>
    <rect x="790" y="305" width="580" height="135" rx="8" fill="#f8fafc" stroke="#0f172a" stroke-width="2.2" />
    <rect x="810" y="318" width="80" height="22" rx="4" fill="#7c3aed" />
    <text x="850" y="333" text-anchor="middle" class="badge-text">TIER 1B</text>
    <text x="1100" y="335" text-anchor="middle" class="box-title">Behavioral Pattern Detector (BPD)</text>
    <text x="1080" y="364" text-anchor="middle" class="box-desc">Model Backbone: Lightweight DistilBERT (66M Parameters)</text>
    <text x="1080" y="386" text-anchor="middle" class="box-desc">Specialized Detection: Real-Time Threat Scoring on Process &amp; File Activity</text>
    <text x="1080" y="408" text-anchor="middle" class="box-desc">Pre-Encryption Defense: Detects Shadow Copy Deletion &amp; Security Tool Tampering</text>
    <text x="1080" y="428" text-anchor="middle" class="box-highlight">Ultra-Fast Edge Runtime: &lt; 15 ms / window &#8226; Low Footprint (&lt; 50 MB RAM)</text>
  </g>

  <!-- Arrows from LSA and BPD to Correlation Engine -->
  <path d="M 360 440 L 360 475 L 600 475 L 600 495" class="arrow" />
  <path d="M 1080 440 L 1080 475 L 840 475 L 840 495" class="arrow" />

  <!-- ========================================================================= -->
  <!-- 4. MITRE ATT&CK DUAL-STREAM CORRELATION ENGINE                            -->
  <!-- ========================================================================= -->
  <g>
    <rect x="220" y="495" width="1000" height="96" rx="8" fill="#f1f5f9" stroke="#334155" stroke-width="2.0" />
    <rect x="240" y="508" width="140" height="22" rx="4" fill="#334155" />
    <text x="310" y="523" text-anchor="middle" class="badge-text">CORRELATION ENGINE</text>
    <text x="730" y="526" text-anchor="middle" class="box-title">MITRE ATT&amp;CK Knowledge Graph &amp; Temporal Threat Correlation</text>
    <text x="720" y="552" text-anchor="middle" class="box-desc">Coordinated Intrusion: Correlates Lateral Movement (Stream A) + Ransomware Staging (Stream B)</text>
    <text x="720" y="574" text-anchor="middle" class="box-highlight">Attack Progression Forecasting: Predicts Next Likely Attack Steps via ATT&amp;CK Graph</text>
  </g>

  <!-- ========================================================================= -->
  <!-- 5. DECISION BRANCHES                                                      -->
  <!-- ========================================================================= -->
  <!-- Branch Left: Clean Normal Stream -->
  <path d="M 400 591 L 400 645 L 260 645 L 260 675" class="arrow" />
  <rect x="130" y="630" width="260" height="28" rx="4" fill="#ffffff" stroke="#64748b" stroke-width="1.5" />
  <text x="260" y="649" text-anchor="middle" class="branch-text">[Normal Baseline Activity (&gt;99% events)]</text>

  <!-- Left Box: Fast Discard Engine -->
  <g>
    <rect x="70" y="675" width="380" height="110" rx="6" fill="#f8fafc" stroke="#64748b" stroke-width="1.8" />
    <text x="260" y="705" text-anchor="middle" class="box-title">Fast Discard &amp; Archive Engine</text>
    <text x="260" y="733" text-anchor="middle" class="box-desc">Zero Alert Fatigue &#8226; Silent Archival of Safe Events</text>
    <text x="260" y="755" text-anchor="middle" class="box-desc">&lt; 0.01 ms Overhead on Safe System Logs</text>
  </g>

  <!-- Branch Right: Confirmed Anomaly / Coordinated Intrusion -->
  <path d="M 1040 591 L 1040 645 L 1040 675" class="arrow" />
  <rect x="850" y="630" width="380" height="28" rx="4" fill="#ffffff" stroke="#b91c1c" stroke-width="1.8" />
  <text x="1040" y="649" text-anchor="middle" class="branch-text">[Confirmed Threat / Coordinated Intrusion Alert]</text>

  <!-- ========================================================================= -->
  <!-- 6. TIER 2: CAUSAL EXPLAINABLE REASONER (XAI)                              -->
  <!-- ========================================================================= -->
  <g>
    <rect x="580" y="675" width="790" height="135" rx="8" fill="#fef2f2" stroke="#b91c1c" stroke-width="2.2" />
    <rect x="600" y="688" width="80" height="22" rx="4" fill="#b91c1c" />
    <text x="640" y="703" text-anchor="middle" class="badge-text">TIER 2</text>
    <text x="980" y="706" text-anchor="middle" class="box-title">Causal Explainable Reasoner (On-Demand Incident Triage)</text>
    <text x="975" y="736" text-anchor="middle" class="box-desc">Model Backbone: Lightweight Generative Decoder (Qwen2.5 / Phi-3 Mini)</text>
    <text x="975" y="758" text-anchor="middle" class="box-desc">Specialized Capability: Security-Tuned Incident Analysis &amp; Root Cause Reasoning</text>
    <text x="975" y="780" text-anchor="middle" class="box-highlight">Fact-Grounded Analysis: Explanations Mapped to Verified ATT&amp;CK Knowledge</text>
  </g>

  <!-- Arrow from Tier 2 to Incident Output -->
  <path d="M 975 810 L 975 845" class="arrow" />

  <!-- ========================================================================= -->
  <!-- 7. TARGET STRUCTURED INCIDENT ALERT & SOAR PLAYBOOKS                       -->
  <!-- ========================================================================= -->
  <g>
    <rect x="580" y="845" width="790" height="125" rx="8" fill="#f8fafc" stroke="#334155" stroke-width="2.0" />
    <text x="975" y="875" text-anchor="middle" class="box-title">Structured Incident Alert &amp; Automated Response (SOAR)</text>
    <text x="975" y="901" text-anchor="middle" class="box-desc">Granular MITRE ATT&amp;CK Technique Mapping &#8226; Severity Scoring</text>
    <text x="975" y="923" text-anchor="middle" class="box-desc">Automated Response Actions: Isolate Compromised Host &#8226; Revoke Tokens &#8226; Protect Backups</text>
    <text x="975" y="945" text-anchor="middle" class="box-highlight">Generates Plain-English Forensic Incident Reports for Plant Operators &amp; Analysts</text>
  </g>

</svg>
"""
    with open(SVG_PATH, "w", encoding="utf-8") as f:
        f.write(svg_content)
    print(f"[+] Full Architecture SVG generated: {SVG_PATH}")


def generate_png():
    # Generate high-resolution publication PNG (2880 x 2040)
    w, h = 2880, 2040
    img = Image.new("RGB", (w, h), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    # Scale factor
    s = 2.0

    def load_font(size, bold=False):
        font_names = [
            "C:\\Windows\\Fonts\\segoeuib.ttf" if bold else "C:\\Windows\\Fonts\\segoeui.ttf",
            "C:\\Windows\\Fonts\\arialbd.ttf" if bold else "C:\\Windows\\Fonts\\arial.ttf"
        ]
        for fn in font_names:
            if os.path.exists(fn):
                try:
                    return ImageFont.truetype(fn, int(size * s))
                except Exception:
                    pass
        return ImageFont.load_default()

    font_main = load_font(22, bold=True)
    font_sub = load_font(13.5)
    font_title = load_font(15.5, bold=True)
    font_desc = load_font(12.5)
    font_highlight = load_font(12.5, bold=True)
    font_badge = load_font(11, bold=True)
    font_branch = load_font(12.5, bold=True)

    # Outer container
    draw.rounded_rectangle([int(20*s), int(16*s), int(1420*s), int(1004*s)], radius=int(8*s), fill=(255, 255, 255), outline=(203, 213, 225), width=int(2*s))

    # Header
    draw.text((int(50*s), int(35*s)), "EdgeShield End-to-End Architecture: Dual-Stream Inline Detection, Correlation & Tier 2 XAI", font=font_main, fill=(15, 23, 42))
    draw.text((int(50*s), int(64*s)), "Decoupled Dual-Stream Detection (LSA + BPD) • MITRE ATT&CK Threat Correlation • On-Demand Incident Triage & Reporting", font=font_sub, fill=(71, 85, 105))

    # Helper function for boxes
    def draw_box(x, y, w_box, h_box, title, lines, fill_c, stroke_c, badge=None, badge_c=(51, 65, 85)):
        bx, by = int(x*s), int(y*s)
        bw, bh = int(w_box*s), int(h_box*s)
        draw.rounded_rectangle([bx, by, bx+bw, by+bh], radius=int(8*s), fill=fill_c, outline=stroke_c, width=int(2*s))
        
        ty = by + int(14*s)
        if badge:
            badge_w = int(len(badge) * 8 * s + 16 * s)
            badge_h = int(22 * s)
            draw.rounded_rectangle([bx + int(16*s), by + int(12*s), bx + int(16*s) + badge_w, by + int(12*s) + badge_h], radius=int(4*s), fill=badge_c)
            draw.text((bx + int(24*s), by + int(15*s)), badge, font=font_badge, fill=(255, 255, 255))
            draw.text((bx + bw // 2 + int(20*s), ty), title, font=font_title, fill=(15, 23, 42), anchor="mt")
        else:
            draw.text((bx + bw // 2, ty), title, font=font_title, fill=(15, 23, 42), anchor="mt")

        line_y = by + int(42*s)
        for line, is_hl in lines:
            f = font_highlight if is_hl else font_desc
            c = (15, 23, 42) if is_hl else (51, 65, 85)
            draw.text((bx + bw // 2, line_y), line, font=f, fill=c, anchor="mt")
            line_y += int(21*s)

    # 1. Top Ingestion Stream
    draw_box(340, 94, 760, 66, "Enterprise Security Telemetry Ingestion Stream", [
        ("Windows Sysmon (EIDs 1, 3, 7, 10, 11) • Security Event Log (EIDs 4624, 4625, 4672, Kerberos Auth Tickets)", False)
    ], (248, 250, 252), (71, 85, 105))

    # Stream badges
    draw.rounded_rectangle([int(220*s), int(172*s), int(500*s), int(198*s)], radius=int(4*s), fill=(2, 132, 199))
    draw.text((int(360*s), int(177*s)), "STREAM A: AUTHENTICATION & IDENTITY", font=font_badge, fill=(255, 255, 255), anchor="mt")

    draw.rounded_rectangle([int(940*s), int(172*s), int(1220*s), int(198*s)], radius=int(4*s), fill=(124, 58, 237))
    draw.text((int(1080*s), int(177*s)), "STREAM B: ENDPOINT BEHAVIOR & PROCESSES", font=font_badge, fill=(255, 255, 255), anchor="mt")

    # 2. Tokenizers
    draw_box(70, 205, 580, 74, "Domain Security Tokenizer & Sliding Window", [
        ("Preserves Security IDs, IP Addresses, and Account Credentials", False),
        ("Temporal Sliding Window (Evaluates 3 to 5 Sequential Authentication Events)", False)
    ], (240, 249, 255), (2, 132, 199))

    draw_box(790, 205, 580, 74, "Constrained Security Vocabulary Tokenizer", [
        ("Specialized Threat Vocabulary (Process Trees, System Calls, Command Flags)", False),
        ("Filters Background Noise • Normalizes File & Process Paths", False)
    ], (250, 245, 255), (124, 58, 237))

    # 3. Tier 1 Detectors
    draw_box(70, 305, 580, 135, "Log Semantic Analyzer (LSA)", [
        ("Model Backbone: DeBERTa-v3 Small (44M Parameters)", False),
        ("Specialized Detection: Authentication Sequences & Privilege Escalation", False),
        ("Detects Lateral Movement (Remote Services, Admin Shares, Pass-the-Hash)", False),
        ("Ultra-Fast Edge Runtime: ~11.7 ms / window • Low Footprint (~50 MB RAM)", True)
    ], (248, 250, 252), (15, 23, 42), badge="TIER 1A", badge_c=(2, 132, 199))

    draw_box(790, 305, 580, 135, "Behavioral Pattern Detector (BPD)", [
        ("Model Backbone: Lightweight DistilBERT (66M Parameters)", False),
        ("Specialized Detection: Real-Time Threat Scoring on Process & File Activity", False),
        ("Pre-Encryption Defense: Detects Shadow Copy Deletion & Security Tool Tampering", False),
        ("Ultra-Fast Edge Runtime: < 15 ms / window • Low Footprint (< 50 MB RAM)", True)
    ], (248, 250, 252), (15, 23, 42), badge="TIER 1B", badge_c=(124, 58, 237))

    # 4. Correlation Engine
    draw_box(220, 495, 1000, 96, "MITRE ATT&CK Knowledge Graph & Temporal Threat Correlation", [
        ("Coordinated Intrusion: Correlates Lateral Movement (Stream A) + Ransomware Staging (Stream B)", False),
        ("Attack Progression Forecasting: Predicts Next Likely Attack Steps via ATT&CK Graph", True)
    ], (241, 245, 249), (51, 65, 85), badge="CORRELATION ENGINE", badge_c=(51, 65, 85))

    # Decision Badges
    draw.rounded_rectangle([int(130*s), int(630*s), int(390*s), int(658*s)], radius=int(4*s), fill=(255, 255, 255), outline=(100, 116, 139), width=int(1.5*s))
    draw.text((int(260*s), int(635*s)), "[Normal Baseline Activity (>99% events)]", font=font_branch, fill=(15, 23, 42), anchor="mt")

    draw.rounded_rectangle([int(850*s), int(630*s), int(1230*s), int(658*s)], radius=int(4*s), fill=(255, 255, 255), outline=(185, 28, 28), width=int(1.8*s))
    draw.text((int(1040*s), int(635*s)), "[Confirmed Threat / Coordinated Intrusion Alert]", font=font_branch, fill=(185, 28, 28), anchor="mt")

    # 5. Fast Discard Box
    draw_box(70, 675, 380, 110, "Fast Discard & Archive Engine", [
        ("Zero Alert Fatigue • Silent Archival of Safe Events", False),
        ("< 0.01 ms Overhead on Safe System Logs", False)
    ], (248, 250, 252), (100, 116, 139))

    # 6. Tier 2 XAI Reasoner
    draw_box(580, 675, 790, 135, "Causal Explainable Reasoner (On-Demand Incident Triage)", [
        ("Model Backbone: Lightweight Generative Decoder (Qwen2.5 / Phi-3 Mini)", False),
        ("Specialized Capability: Security-Tuned Incident Analysis & Root Cause Reasoning", False),
        ("Fact-Grounded Analysis: Explanations Mapped to Verified ATT&CK Knowledge", True)
    ], (254, 242, 242), (185, 28, 28), badge="TIER 2", badge_c=(185, 28, 28))

    # 7. Incident Alert & Playbooks
    draw_box(580, 845, 790, 125, "Structured Incident Alert & Automated Response (SOAR)", [
        ("Granular MITRE ATT&CK Technique Mapping • Threat Severity Scoring", False),
        ("Automated Response Actions: Isolate Compromised Host • Revoke Tokens • Protect Backups", False),
        ("Generates Plain-English Forensic Incident Reports for Plant Operators & Analysts", True)
    ], (248, 250, 252), (51, 65, 85))

    # Connective Arrows
    def draw_down_arrow(x, y1, y2, color=(51, 65, 85)):
        ax, ay1, ay2 = int(x*s), int(y1*s), int(y2*s)
        draw.line([(ax, ay1), (ax, ay2)], fill=color, width=int(2*s))
        draw.polygon([(ax - int(4*s), ay2 - int(6*s)), (ax + int(4*s), ay2 - int(6*s)), (ax, ay2)], fill=color)

    draw_down_arrow(360, 279, 305, (2, 132, 199))
    draw_down_arrow(1080, 279, 305, (124, 58, 237))
    draw_down_arrow(975, 810, 845, (51, 65, 85))
    draw_down_arrow(260, 658, 675, (100, 116, 139))
    draw_down_arrow(1040, 658, 675, (185, 28, 28))

    img.save(PNG_PATH, "PNG", dpi=(300, 300))
    print(f"[+] Full Architecture PNG generated: {PNG_PATH}")

    # Copy to artifact directory for instant viewing
    os.makedirs(ARTIFACT_DIR, exist_ok=True)
    artifact_png = os.path.join(ARTIFACT_DIR, "edgeshield_architecture_full.png")
    shutil.copy2(PNG_PATH, artifact_png)
    print(f"[+] Copied to artifacts: {artifact_png}")


if __name__ == "__main__":
    generate_svg()
    generate_png()
