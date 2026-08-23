"""
generate_paper.py
=================
Generates SLM_Lateral_Movement_Paper.docx by using EdgeShield_v3.docx as
the *formatting* template (styles, columns, margins, author table layout)
and injecting our paper's *content* with humanified prose.

Strategy
--------
1. Copy EdgeShield_v3.docx   -> preserves styles, page layout, columns
2. Apply light humanification edits to sections I-IV (already in the template)
3. Remove everything from Section V onward (template's "Evaluation Plan")
4. Append our unique sections V-VIII plus References with proper styles
"""

import shutil
from copy import deepcopy

import docx
import os

# ── Paths ──────────────────────────────────────────────────────────
TEMPLATE = r"C:\Users\gaura\OneDrive\Documents\PhD\EdgeShield_v3.docx"
OUTPUT   = os.path.join(os.path.dirname(os.path.abspath(__file__)), "SLM_Lateral_Movement_Paper_v2.docx")

# ── Targeted phrase-level humanification ───────────────────────────
# Short, high-confidence rewrites that make the prose less uniform
# without changing meaning.  Each (old, new) pair is applied to every
# Normal-style paragraph whose text exceeds 80 characters.
REWRITES = [
    ("In the vast majority of",
     "In most"),
    ("a different point of view on this problem",
     "a fresh angle on this problem"),
    ("The trouble is practicality:",
     "The catch is practicality:"),
    ("sit in a useful middle ground",
     "occupy a promising middle ground"),
    ("Motivated by these observations, we propose",
     "Building on these observations, we propose"),
    ("A central question raised by all of these works is whether",
     "A recurring question across these works is whether"),
    ("have also been explored extensively",
     "have also drawn considerable attention"),
    ("several important limitations that we want to acknowledge openly",
     "several real limitations worth acknowledging openly"),
    ("Notably, none of the surveyed studies used a language model as the principal detection mechanism",
     "Strikingly, none of these studies used a language model as the primary detection engine"),
    ("In a different line of work",
     "Along a parallel track"),
    ("We use two distinct models, rather than a single multitask one, for principled reasons.",
     "We chose two specialist models over one multitask model for concrete reasons."),
    ("is designed to catch this sequence as early as possible",
     "aims to catch this sequence as early as it can"),
    ("for principled reasons",
     "for practical and principled reasons"),
    ("It is worth noting",
     "Notably"),
    ("It should be noted that",
     ""),
    ("We envisage three deployment tiers.",
     "Three deployment tiers make sense in practice."),
]


# ╔════════════════════════════════════════════════════════════════╗
# ║                       HELPER FUNCTIONS                        ║
# ╚════════════════════════════════════════════════════════════════╝

def elem_text(el):
    """Return the plain-text content of an XML <w:p> element."""
    return "".join(n.text or "" for n in el.iter() if n.tag.endswith("}t"))


def replace_para_text(para, new_text):
    """Swap all runs in *para* for a single run containing *new_text*,
    preserving the paragraph's style."""
    for ch in list(para._element):
        if ch.tag.endswith("}r"):
            para._element.remove(ch)
    para.add_run(new_text)


def humanify(text):
    """Apply the REWRITES table to *text* and return the result."""
    for old, new in REWRITES:
        text = text.replace(old, new)
    return text


def h1(doc, text):
    """Add a Heading 1 paragraph (major section header)."""
    return doc.add_paragraph(text, style="Heading 1")


def h2(doc, text):
    """Add a Heading 2 paragraph (subsection header)."""
    return doc.add_paragraph(text, style="Heading 2")


def body(doc, text):
    """Add a Normal-style body paragraph."""
    return doc.add_paragraph(text, style="Normal")


# ╔════════════════════════════════════════════════════════════════╗
# ║                    SECTION CONTENT BLOCKS                     ║
# ╚════════════════════════════════════════════════════════════════╝

def add_section_v(doc):
    """V.  THEORETICAL FOUNDATIONS — unique to our paper."""

    h1(doc, "V.  THEORETICAL FOUNDATIONS")
    body(doc,
        "This section lays out the mathematical machinery behind "
        "EdgeShield\u2019s classification and reasoning layers.  We cover "
        "the disentangled attention mechanism that drives the sequence "
        "classifier, the autoregressive objective used to train the "
        "generative reasoner, the LoRA adapters that keep fine-tuning "
        "affordable on edge hardware, and the auto-calibration loop that "
        "sizes the training workload for whatever device happens to be "
        "available.")

    # ---- A. DeBERTa attention ----
    h2(doc, "A.  Disentangled Attention in DeBERTa-v3")
    body(doc,
        "For sequence classification EdgeShield builds on the DeBERTa "
        "architecture, which departs from standard BERT in one important "
        "way: it decouples content and positional information into two "
        "independent representation streams.  Classic self-attention "
        "computes a single embedding per token by summing its content "
        "vector with an absolute position embedding.  DeBERTa instead "
        "maintains a content vector H_i and a relative position vector "
        "P_{i|j} for every pair of tokens i and j.  The attention score "
        "between them becomes:")
    body(doc,
        "Attn(i, j) = Q_i^c \u00b7 (K_j^c)^T  +  Q_i^c \u00b7 "
        "(K_{i,j}^p)^T  +  K_j^c \u00b7 (Q_{j,i}^p)^T")
    body(doc,
        "Why does this matter for security logs?  Consider a command line "
        "such as \u201cwmic.exe /node:TARGET shadowcopy delete\u201d.  The "
        "relative position of \u201c/node:\u201d after \u201cwmic.exe"
        "\u201d determines the execution semantics.  Decoupled attention "
        "lets the model learn that positional relationship directly, "
        "rather than encoding it implicitly through absolute indices that "
        "break whenever the surrounding log context changes length.  In "
        "practice this makes the classifier far better at generalising "
        "across syntactic variations in attacker commands.")

    # ---- B. CLM + SFT ----
    h2(doc, "B.  Causal Language Modelling and Supervised Fine-Tuning")
    body(doc,
        "The generative reasoner is an autoregressive transformer that "
        "models the probability of a token sequence T = (t_1, \u2026, t_n) "
        "as a product of conditional next-token probabilities:")
    body(doc,
        "P(T) = \u220f_{k=1}^{n}  P(t_k | t_1, \u2026, t_{k\u22121})")
    body(doc,
        "During supervised fine-tuning the cross-entropy loss is computed "
        "only over the target completion tokens\u2014the assistant\u2019s "
        "structured JSON response block\u2014while user and system prompt "
        "tokens are masked.  This forces the model\u2019s causal state "
        "space to align with valid JSON schema elements while still "
        "permitting natural-language security explanations inside the "
        "reasoning fields.  The practical upshot is that the model learns "
        "to emit well-formed, parseable alerts rather than free-form text.")

    # ---- C. LoRA ----
    h2(doc, "C.  Parameter-Efficient Fine-Tuning with LoRA")
    body(doc,
        "Full fine-tuning of a multi-billion-parameter model requires "
        "storing optimiser momentum states for every weight, which is "
        "prohibitively expensive on edge hardware.  Low-Rank Adaptation "
        "(LoRA) sidesteps this by freezing the original weight matrix "
        "W_0 \u2208 \u211d^{d\u00d7k} and learning a low-rank update "
        "\u0394W = (\u03b1/r) \u00b7 B \u00b7 A, where A \u2208 "
        "\u211d^{r\u00d7k} and B \u2208 \u211d^{d\u00d7r} with rank "
        "r \u226a min(d, k):")
    body(doc,
        "W = W_0 + \u0394W = W_0 + (\u03b1 / r) \u00b7 B \u00b7 A")
    body(doc,
        "We set r = 16 and \u03b1 = 32, targeting all linear projections "
        "in the self-attention blocks.  This cuts the number of trainable "
        "parameters by more than 99\u202f%, making it feasible to customise "
        "adapters on a standard workstation without any GPU.")

    # ---- D. Auto-calibration ----
    h2(doc, "D.  Hardware-Aware Dynamic Calibration")
    body(doc,
        "Edge training nodes vary enormously in compute power\u2014from "
        "rack servers with discrete GPUs to modest office workstations "
        "running on CPU alone.  To cope with this spread the training "
        "pipeline includes an auto-calibration step.  Before training "
        "begins the script runs a brief profiling pass (a handful of "
        "forward\u2013backward steps) to measure batch processing speed, "
        "then computes the largest dataset size that still guarantees "
        "completion within a user-specified time budget T_target:")
    body(doc,
        "N_train = clamp(N_min,  \u230a(T_target \u00b7 B) / "
        "(epochs \u00b7 (t_train + \u03b3 \u00b7 t_val))\u230b "
        "\u00b7 C,  N_full)")
    body(doc,
        "Here t_train and t_val are the measured forward\u2013backward and "
        "evaluation durations per step, B is the batch size, \u03b3 is "
        "the validation-to-training ratio, C is a class-alignment constant "
        "that keeps label proportions intact after downsampling, and N_min "
        "is the floor below which training would not converge reliably.  "
        "The net effect is that every deployment gets as much training data "
        "as its hardware can handle within the allotted time, with no "
        "manual tuning required.")


def add_section_vi(doc):
    """VI.  EXPERIMENTAL RESULTS AND DISCUSSION \u2014 TBD."""

    h1(doc, "VI.  EXPERIMENTAL RESULTS AND DISCUSSION")
    body(doc,
        "This section outlines the evaluation flow that will be executed "
        "once the training runs are complete.  The metrics and figures "
        "below are structured as placeholders; final numbers will replace "
        "them after active training.")

    h2(doc, "A.  Sequence Classifier Optimisation")
    body(doc,
        "The first validation step focuses on the DeBERTa-v3 classifier\u2019s "
        "training convergence.  We will track cross-entropy loss on both "
        "training and validation splits across epochs, alongside per-class "
        "precision, recall, and F1.  A raw (untrained) DeBERTa-v3 baseline "
        "provides the lower bound; we expect its F1 to hover near random "
        "chance.  The fine-tuned model should show rapid loss decay and "
        "converge within three epochs, with false-positive rates (benign "
        "events misclassified as malicious) tracked separately.")

    h2(doc, "B.  Generative SFT Model Validation")
    body(doc,
        "The causal reasoner (Qwen-2.5 or Phi-3 Mini) will be evaluated "
        "on two axes: structural correctness and semantic accuracy.  The "
        "JSON Schema Compliance Rate measures the fraction of outputs that "
        "parse as valid JSON without syntax errors.  MITRE ATT&CK Mapping "
        "Accuracy compares predicted technique labels against ground-truth "
        "annotations in the held-out test partition.  Any parsing failures "
        "will be examined individually to identify formatting drift during "
        "generation.")

    h2(doc, "C.  Latency and Ingest Throughput")
    body(doc,
        "A core promise of EdgeShield is fast inference at the network "
        "edge.  We will profile each component\u2019s latency on both CPU "
        "(fallback) and GPU (accelerated) hardware, measuring end-to-end "
        "lookup latency\u2014from log ingestion to final classification or "
        "reasoning alert\u2014across a range of batch sizes.  The key "
        "claim to validate is that the lightweight DeBERTa classifier can "
        "screen out the bulk of benign logs in roughly 1\u202fms, triggering "
        "the heavier generative reasoner only for flagged events.")

    h2(doc, "D.  Memory Footprint and Operational Sizing")
    body(doc,
        "We will log RAM and VRAM consumption during inference, breaking "
        "the total into static weight memory and dynamic Key-Value cache "
        "memory.  Sizing profiles will be produced for three quantisation "
        "levels (FP16, INT8, INT4), mapping out which hardware tier\u2014"
        "workstation, server, or distilled appliance\u2014each "
        "configuration requires.")


def add_section_vii(doc):
    """VII.  DISCUSSION, THREAT MODEL, AND LIMITATIONS."""

    h1(doc, "VII.  DISCUSSION, THREAT MODEL, AND LIMITATIONS")

    # ---- A. Model selection ----
    h2(doc, "A.  Model Selection")
    body(doc,
        "CyberPal 2.0 [7] suggests that the 4B-parameter range hits a "
        "sweet spot for security tasks, but that conclusion rests on a "
        "broad SOC benchmark rather than lateral-movement or ransomware "
        "logs specifically.  Our planned next step is therefore a "
        "head-to-head comparison of Phi-3 Mini (3.8\u202fB), Gemma-2 "
        "(2.6\u202fB), and TinyLlama (1.1\u202fB) on the DARPA OpTC and "
        "LANL datasets, supplemented with curated ransomware behavioural "
        "traces.  Until those numbers exist, model selection remains an "
        "open design decision; we have committed to the dual-stream "
        "architecture and the fine-tuning recipe but reserve the choice of "
        "backbone for the empirical phase.  We also intend to test whether "
        "mixing backbones across the two streams\u2014for instance, Phi-3 "
        "Mini for the LSA and a smaller distilled student for the BPD\u2014"
        "yields a better accuracy\u2013latency trade-off than a single "
        "backbone for both.")

    # ---- B. Threat model ----
    h2(doc, "B.  Threat Model")
    body(doc,
        "We assume an adversary who knows the EdgeShield architecture in "
        "detail: the choice of backbones, the constrained vocabulary of "
        "the BPD, the broad shape of the training data, and the deployment "
        "topology.  We do not assume direct access to the model weights, "
        "although we discuss the weight-extraction case as a worst-case "
        "scenario below.  Three classes of attack are considered.")
    body(doc,
        "Evasion attacks try to craft sequences that look benign to the "
        "model.  Because the LSA\u2019s tokeniser preserves identity-level "
        "fields, simply renaming hosts or rotating accounts is unlikely to "
        "succeed.  A more sophisticated attacker who paces lateral "
        "movement to mimic the timing distribution of legitimate "
        "administrative activity could, however, erode detection "
        "confidence.  We mitigate this by including such timing-perturbed "
        "traces as hard negatives during contrastive fine-tuning.")
    body(doc,
        "Poisoning attacks aim to corrupt the training data so that the "
        "deployed model learns to overlook certain attack signatures.  "
        "EdgeShield\u2019s training corpus draws primarily from public "
        "datasets (DARPA OpTC, LANL) and curated internal traces, so the "
        "dominant defence is upstream provenance control on the curated "
        "component.  We also plan to incorporate KL-divergence-based "
        "outlier detection between the fine-tuned model\u2019s output "
        "distribution and an untainted baseline, flagging suspicious "
        "behavioural shifts after each retraining cycle.")
    body(doc,
        "Recent adversarial-robustness work [15] tested 63 SLMs from 15 "
        "families against eight jailbreak methods and found nearly half to "
        "be highly vulnerable.  EdgeShield\u2019s constrained vocabulary "
        "partially mitigates this\u2014the model can only emit ATT&CK "
        "labels, not free-form text\u2014but a knowledgeable attacker "
        "could still craft log entries designed to suppress detection.  "
        "To counter this we plan adversarial training loops that inject "
        "poisoned log sequences during fine-tuning so that the model "
        "learns to flag rather than ignore them, plus runtime monitoring "
        "of embedding-space distance between new traces and the nearest "
        "training-time cluster as a tripwire for novel adversarial input.")

    # ---- C. Limitations ----
    h2(doc, "C.  Limitations")
    body(doc,
        "We want to be upfront about several real limitations.  First, "
        "EdgeShield is still at the design stage; the latency, accuracy, "
        "and robustness numbers cited throughout this paper come from "
        "published benchmarks of similar models on similar tasks, not from "
        "a complete EdgeShield prototype.  Second, the dual-stream design "
        "assumes lateral movement and ransomware are the two "
        "highest-priority attack phases; an organisation primarily worried "
        "about espionage, supply-chain compromise, or insider threat would "
        "need to retrain or extend the framework substantially.  Third, "
        "the constrained-vocabulary BPD gains interpretability at the cost "
        "of expressiveness; a sufficiently novel ransomware family "
        "operating outside the curated vocabulary might evade detection "
        "until the vocabulary is updated.  Fourth, the ATT&CK-aligned "
        "classification module depends on the public ATT&CK graph, which "
        "is maintained by humans and can lag the threat landscape by "
        "months.")

    # ---- D. Ethical considerations ----
    h2(doc, "D.  Ethical Considerations and Responsible Disclosure")
    body(doc,
        "Detection systems like EdgeShield carry a dual-use risk: the same "
        "techniques that help defenders recognise lateral movement could, "
        "in principle, let attackers test their tradecraft against a known "
        "detector and iterate until evasion succeeds.  We have weighed "
        "this risk and concluded that open publication is the more "
        "responsible course, because the underlying detection signals "
        "(Windows event IDs, vssadmin invocation, mass file rename) are "
        "already extensively documented in defensive literature.  "
        "EdgeShield\u2019s principal contribution is not the choice of "
        "signals but their integration with language-model reasoning, "
        "ATT&CK alignment, and edge deployment.  Withholding that "
        "integration would not deny attackers any meaningful capability "
        "while it would substantially impair defenders\u2019 ability to "
        "deploy better detection.")
    body(doc,
        "During the empirical phase we will follow standard "
        "responsible-disclosure practices for any vulnerabilities or "
        "evasion techniques discovered while evaluating EdgeShield against "
        "current ransomware families.  Privacy considerations are built "
        "into the design from the outset: telemetry never leaves the "
        "organisational perimeter, the LoRA-adapter feedback mechanism "
        "stores no raw log data, and all examples retained for retraining "
        "are anonymised at the SID and hostname level before storage.  "
        "Where the system processes personal data within the meaning of "
        "applicable privacy regulations, deployments will be expected to "
        "apply the same data-protection controls (retention limits, access "
        "logging, purpose limitation) that they apply to other security "
        "tooling.")

    # ---- E. Future work ----
    h2(doc, "E.  Future Work")
    body(doc,
        "Beyond the empirical validation already described, we see three "
        "natural extensions.  First, federated learning across distributed "
        "edge nodes would let each site contribute gradient updates "
        "without centralising raw logs\u2014important for multi-branch "
        "enterprises under heterogeneous regulatory regimes.  A federated "
        "EdgeShield would replace the central training pipeline with a "
        "secure aggregator that combines local LoRA updates while "
        "preserving differential privacy.")
    body(doc,
        "Second, the same dual-stream architecture could accommodate "
        "additional ATT&CK tactics; Initial Access (TA0001) and "
        "Exfiltration (TA0010) are the most obvious next targets, since "
        "they bracket the kill-chain segment that EdgeShield currently "
        "covers.  Third, we want to explore Retrieval-Augmented "
        "Generation (RAG) for the classification module: instead of "
        "baking all ATT&CK knowledge into model weights, we could query "
        "an up-to-date knowledge graph at inference time, making the "
        "system much easier to maintain as MITRE publishes new technique "
        "IDs.  A RAG-based variant would also support per-deployment "
        "customisation, since each organisation could attach its own "
        "private corpus of incident reports and tune the retrieval "
        "index accordingly.")


def add_section_viii(doc):
    """VIII.  CONCLUSION."""

    h1(doc, "VIII.  CONCLUSION")
    body(doc,
        "We have presented EdgeShield, a dual-stream detection framework "
        "built on fine-tuned Small Language Models that spots lateral "
        "movement and ransomware activity directly at the network edge.  "
        "The Log Semantic Analyser handles authentication and Kerberos "
        "telemetry; the Behavioural Pattern Detector watches file-system "
        "and process events; and an ATT&CK-aligned classifier ties both "
        "streams together so that coordinated, multi-stage intrusions "
        "surface as single, high-confidence alerts rather than isolated "
        "anomalies.  We described the tokeniser design, the two-phase "
        "fine-tuning recipe, the mathematical foundations of the "
        "classification and reasoning layers, the latency budget on "
        "commodity hardware, and the threat model under which the system "
        "is intended to operate.")
    body(doc,
        "The framework is still at the design stage\u2014empirical "
        "validation on the DARPA OpTC and LANL datasets, together with "
        "curated ransomware traces, is the immediate next step.  "
        "Nonetheless, the combination of published SLM benchmarks, "
        "successful industry deployments such as UpSight and Palo Alto, "
        "the maturity of the ONNX Runtime ecosystem on commodity "
        "hardware, and the practical benefits of edge-local inference "
        "together give us confidence that the approach is viable.  If the "
        "experimental results confirm what the design-time analysis "
        "suggests, EdgeShield could give SOCs a fast, private, and "
        "maintainable detection layer for two of the most damaging phases "
        "in the modern threat landscape\u2014closing a gap that current "
        "signature-based and cloud-only approaches cannot fill alone.")


def add_references(doc):
    """REFERENCES in IEEE format."""

    h1(doc, "REFERENCES")
    refs = [
        "[1]\tM. Alghamdi et al., \u201cMITRE ATT&CK applications in "
            "cybersecurity and the way forward,\u201d arXiv preprint "
            "arXiv:2502.10825, Feb. 2025.",

        "[2]\tA. Akhtar et al., \u201cA comprehensive literature review "
            "on ransomware detection using deep learning,\u201d Computer "
            "Science and Applications, vol. 2, 2024.",

        "[3]\tW. Li et al., \u201cExploring the role of large language "
            "models in cybersecurity: a systematic survey,\u201d arXiv "
            "preprint arXiv:2504.15622, Apr. 2025.",

        "[4]\tC. Papageorgiou et al., \u201cLeveraging large language "
            "models for scalable and explainable cybersecurity log "
            "analysis,\u201d J. Cybersecurity and Privacy, vol. 5, "
            "no. 3, 2025.",

        "[5]\tA. Ferrag et al., \u201cHarnessing the power of language "
            "models in cybersecurity: a comprehensive review,\u201d "
            "J. Network and Computer Applications, 2024.",

        "[6]\tZ. Lu et al., \u201cSmall language models: survey, "
            "measurements, and insights,\u201d arXiv preprint "
            "arXiv:2409.15790, Sep. 2024.",

        "[7]\tS. Tihanyi et al., \u201cToward cybersecurity-expert small "
            "language models,\u201d arXiv preprint arXiv:2510.14113, "
            "Oct. 2025.",

        "[8]\tUpSight Security, \u201cSmall language models against "
            "ransomware,\u201d UpSight AI, 2024. [Online]. Available: "
            "https://upsight.ai/small-language-models/",

        "[9]\tZ. Lu et al., \u201cDemystifying small language models for "
            "edge deployment,\u201d in Proc. ACL, Jul. 2025.",

        "[10]\tPalo Alto Networks, \u201cHow small language models are "
            "quietly revolutionizing cybersecurity,\u201d Palo Alto "
            "Networks Community Blog, 2025.",

        "[11]\tMITRE Corporation, \u201cLateral movement, tactic TA0008,"
            "\u201d MITRE ATT&CK Enterprise. [Online]. Available: "
            "https://attack.mitre.org/tactics/TA0008/",

        "[12]\tB. Carvajal et al., \u201cDetecting lateral movement: a "
            "systematic survey,\u201d Heliyon, vol. 10, no. 4, "
            "p. e26317, 2024.",

        "[13]\tH. Chen et al., \u201cFuchikoma: NLP and neural "
            "network-based autonomous threat hunting,\u201d in Proc. "
            "IEEE Symp. Security and Privacy, 2023.",

        "[14]\tS. Okada et al., \u201cATT&CK technique extraction from "
            "Windows logs for lateral movement path identification,"
            "\u201d in Proc. ACSAC, 2024.",

        "[15]\tZ. Lin et al., \u201cCan small language models reliably "
            "resist jailbreak attacks? A comprehensive evaluation,"
            "\u201d arXiv preprint arXiv:2503.06519, Mar. 2025.",

        "[16]\tC. Smiliotopoulos, G. Kambourakis, and K. Barmpatsalou, "
            "\u201cOn the detection of lateral movement through "
            "supervised machine learning and an open-source tool to "
            "create turnkey datasets from Sysmon logs,\u201d Int. J. "
            "Information Security, vol. 22, pp. 1893\u20131919, 2023.",

        "[17]\tC. Smiliotopoulos, K. Barmpatsalou, and G. Kambourakis, "
            "\u201cRevisiting the detection of lateral movement through "
            "Sysmon,\u201d Applied Sciences, vol. 12, no. 15, p. 7746, "
            "2022.",
    ]
    for ref in refs:
        p = body(doc, ref)
        # Apply hanging indent for IEEE reference style
        fmt = p.paragraph_format
        fmt.left_indent = Inches(0.25)
        fmt.first_line_indent = Inches(-0.25)
        fmt.space_after = Pt(2)


# ╔════════════════════════════════════════════════════════════════╗
# ║                         MAIN LOGIC                            ║
# ╚════════════════════════════════════════════════════════════════╝

def main():
    # ── 1. Copy template ──────────────────────────────────────────
    shutil.copy2(TEMPLATE, OUTPUT)
    doc = docx.Document(OUTPUT)
    body_el = doc.element.body

    # ── 2. Humanify existing paragraphs in sections I-IV ──────────
    for para in doc.paragraphs:
        if para.style and para.style.name == "Normal" and len(para.text.strip()) > 80:
            h = humanify(para.text)
            if h != para.text:
                replace_para_text(para, h)

    # ── 3. Locate Section V heading and save the sectPr ───────────
    # The template's Section V is "EVALUATION PLAN" which we replace
    # with our unique sections V-VIII.
    all_elems = list(body_el)
    cut_idx = None

    for i, el in enumerate(all_elems):
        if not el.tag.endswith("}p"):
            continue
        txt = elem_text(el).strip().upper()
        if txt.startswith("V.") and "EVALUATION" in txt:
            # Verify it's a heading
            pPr = el.find(qn("w:pPr"))
            if pPr is not None:
                pStyle = pPr.find(qn("w:pStyle"))
                if pStyle is not None:
                    style_val = (pStyle.get(qn("w:val")) or "").replace(" ", "")
                    if "Heading1" in style_val or "Heading2" in style_val:
                        cut_idx = i
                        break

    if cut_idx is None:
        # Fallback: search for any heading starting with "V."
        for i, el in enumerate(all_elems):
            if not el.tag.endswith("}p"):
                continue
            txt = elem_text(el).strip()
            if txt.startswith("V.") and len(txt) < 60:
                pPr = el.find(qn("w:pPr"))
                if pPr is not None:
                    pStyle = pPr.find(qn("w:pStyle"))
                    if pStyle is not None:
                        style_val = (pStyle.get(qn("w:val")) or "").replace(" ", "")
                        if "Heading" in style_val:
                            cut_idx = i
                            break

    if cut_idx is None:
        print("[!] WARNING: Could not find Section V heading. "
              "Appending new sections at end of document.")
    else:
        # Save the document's sectPr (last child of body)
        sect_pr = body_el.find(qn("w:sectPr"))
        sect_pr_copy = deepcopy(sect_pr) if sect_pr is not None else None

        # Remove everything from cut_idx onward
        for el in all_elems[cut_idx:]:
            body_el.remove(el)

        # Re-attach sectPr so the document keeps its page/column settings
        if sect_pr_copy is not None:
            body_el.append(sect_pr_copy)

    # ── 4. Append our sections V-VIII plus references ─────────────
    add_section_v(doc)
    add_section_vi(doc)
    add_section_vii(doc)
    add_section_viii(doc)
    add_references(doc)

    # ── 5. Make sure sectPr is the last body child ────────────────
    sect_pr = body_el.find(qn("w:sectPr"))
    if sect_pr is not None:
        body_el.remove(sect_pr)
        body_el.append(sect_pr)

    # ── 6. Save ───────────────────────────────────────────────────
    doc.save(OUTPUT)
    print(f"[+] SUCCESS: {OUTPUT} generated!")


if __name__ == "__main__":
    main()
