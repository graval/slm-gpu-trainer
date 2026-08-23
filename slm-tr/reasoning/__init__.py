"""
Reasoning Module Package
Exposes ReasoningEngine, MITRE knowledgebase, and prompt builders.
"""

from reasoning.mitre_kb import MITRE_TECHNIQUES, get_technique_details
from reasoning.engine import ReasoningEngine
from reasoning.prompt_builder import (
    build_instruction_prompt, 
    build_completion_response, 
    create_decoder_sample
)

__all__ = [
    "MITRE_TECHNIQUES",
    "get_technique_details",
    "ReasoningEngine",
    "build_instruction_prompt",
    "build_completion_response",
    "create_decoder_sample"
]
