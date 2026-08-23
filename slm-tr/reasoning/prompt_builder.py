"""
Generative SLM Prompt Builder & JSON Formatter
Builds instruction prompts and structured JSON completions for instruction tuning (SFT)
and runtime generative reasoning across both v1 (Single Entry) and v2 (Sliding Window).
"""

import json
from typing import Dict, Any, Optional
from reasoning.engine import ReasoningEngine

_engine = ReasoningEngine()

def build_instruction_prompt(
    text_telemetry: str, 
    variant_tag: str = "v2_sliding_window"
) -> str:
    """
    Constructs an instruction prompt for generative SLMs (ChatML / Instruct format).
    """
    prefix = (
        "Analyze this Windows security telemetry sequence (temporal sliding window) for potential lateral movement activity:"
        if variant_tag == "v2_sliding_window"
        else "Analyze this single Windows security log event for potential lateral movement activity:"
    )
    
    prompt = (
        f"<|im_start|>user\n"
        f"{prefix}\n\n"
        f"{text_telemetry}\n\n"
        f"Output a structured JSON analysis report.<|im_end|>\n"
        f"<|im_start|>assistant\n"
    )
    return prompt

def build_completion_response(
    report_dict: Dict[str, Any]
) -> str:
    """
    Formats an analytical reasoning report into a clean JSON string completion.
    """
    clean_report = {
        "lateral_movement": report_dict.get("lateral_movement", False),
        "class": report_dict.get("class", "Normal"),
        "mitre_technique": report_dict.get("mitre_technique", "N/A"),
        "reasoning": report_dict.get("reasoning", "")
    }
    json_str = json.dumps(clean_report, indent=2)
    return f"{json_str}<|im_end|>"

def create_decoder_sample(
    row_or_text: Any, 
    label: int, 
    variant_tag: str = "v2_sliding_window",
    cmd: str = "",
    image: str = ""
) -> Dict[str, str]:
    """
    Generates a full prompt + completion sample ready for Hugging Face SFTTrainer.
    """
    text_content = str(row_or_text)
    report = _engine.generate_detailed_reasoning(
        cmd=cmd, 
        image=image, 
        classification=label, 
        context_text=text_content
    )
    
    prompt = build_instruction_prompt(text_content, variant_tag=variant_tag)
    completion = build_completion_response(report)
    
    return {
        "prompt": prompt,
        "completion": completion,
        "text": prompt + completion,
        "label": label,
        "class": report["class"],
        "mitre_technique": report["mitre_technique"]
    }
