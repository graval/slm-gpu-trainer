"""
EdgeShield: A Small Language Model Framework for Real-Time Detection of Lateral Movement and Ransomware Attacks
Research Implementation based on Raval & Bhatt (GLS University).
"""

from edgeshield.taxonomy import MITRE_ATTACK_TAXONOMY, AttackKnowledgeGraph, build_edgeshield_domain_vocabulary
from edgeshield.lsa.analyzer import LogSemanticAnalyzer
from edgeshield.bpd.detector import BehavioralPatternDetector
from edgeshield.correlation.engine import AttackCorrelationEngine
from edgeshield.edge_deploy.onnx_runtime import EdgeDeploymentEngine
from edgeshield.pipeline import EdgeShieldPipeline

__version__ = "1.0.0"
__all__ = [
    "MITRE_ATTACK_TAXONOMY",
    "AttackKnowledgeGraph",
    "build_edgeshield_domain_vocabulary",
    "LogSemanticAnalyzer",
    "BehavioralPatternDetector",
    "AttackCorrelationEngine",
    "EdgeDeploymentEngine",
    "EdgeShieldPipeline"
]
