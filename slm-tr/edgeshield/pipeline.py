"""
EdgeShield: Unified Dual-Stream End-to-End Pipeline
Orchestrates telemetry ingestion, dual-stream SLM inference (LSA + BPD),
ATT&CK correlation, predictive threat hunting, and on-premise edge deployment.
"""

import time
from typing import Dict, List, Any, Optional, Tuple, Union
import pandas as pd

from edgeshield.lsa.analyzer import LogSemanticAnalyzer
from edgeshield.bpd.detector import BehavioralPatternDetector
from edgeshield.correlation.engine import AttackCorrelationEngine
from edgeshield.edge_deploy.onnx_runtime import EdgeDeploymentEngine
from edgeshield.taxonomy import AttackKnowledgeGraph

class EdgeShieldPipeline:
    """
    Primary interface for the EdgeShield Dual-Stream Framework.
    """
    def __init__(
        self,
        lsa_model_path: str = "models/deberta-lateral-movement-v2_sliding_window-stable",
        bpd_model_path: str = "models/deberta-lateral-movement-v2_sliding_window-stable",
        bpd_threat_threshold: float = 0.70,
        correlation_window_sec: float = 300.0,
        device: Optional[str] = None
    ):
        print("[*] Initializing EdgeShield Dual-Stream SLM Architecture...")
        self.lsa = LogSemanticAnalyzer(model_name_or_path=lsa_model_path, device=device)
        self.bpd = BehavioralPatternDetector(model_name_or_path=bpd_model_path, threat_threshold=bpd_threat_threshold, device=device)
        self.correlator = AttackCorrelationEngine(correlation_window_sec=correlation_window_sec)
        self.edge_engine = EdgeDeploymentEngine()
        self.knowledge_graph = AttackKnowledgeGraph()
        print("[+] EdgeShield Pipeline successfully instantiated and ready for edge telemetry.")

    def process_telemetry_event(
        self,
        auth_log: Optional[Union[Dict[str, Any], str]] = None,
        behavior_log: Optional[Union[Dict[str, Any], str]] = None,
        source_host: str = "HOST-01",
        target_host: str = "DC-01",
        user: str = "admin"
    ) -> Dict[str, Any]:
        """
        Processes simultaneous or single telemetry feeds through the dual-stream architecture.
        """
        lsa_output = None
        bpd_output = None
        
        # 1. Execute Stream A (LSA) if auth log provided
        if auth_log is not None:
            lsa_output = self.lsa.analyze_window(
                events_or_text=auth_log,
                source_host=source_host,
                target_host=target_host,
                user=user
            )
            
        # 2. Execute Stream B (BPD) if behavioral telemetry provided
        if behavior_log is not None:
            bpd_output = self.bpd.analyze_behavior_window(
                events_or_text=behavior_log,
                host=target_host or source_host,
                user=user
            )

        # 3. Fuse & Correlate across streams
        if lsa_output and bpd_output:
            correlation_result = self.correlator.correlate_dual_stream(lsa_output, bpd_output)
        elif lsa_output:
            dummy_bpd = {
                "stream": "BPD", "threat_score": 0.10, "threat_threshold": self.bpd.threat_threshold,
                "pre_encryption_alert": False, "encryption_active": False, "technique_id": "BENIGN_NORMAL",
                "technique_name": "Clean Baseline", "tactic": "Normal Operations"
            }
            correlation_result = self.correlator.correlate_dual_stream(lsa_output, dummy_bpd)
        elif bpd_output:
            dummy_lsa = {
                "stream": "LSA", "is_lateral_movement": False, "technique_id": "BENIGN_NORMAL",
                "technique_name": "Clean Baseline", "tactic": "Normal Operations", "confidence": 0.95,
                "multi_hop_chains": []
            }
            correlation_result = self.correlator.correlate_dual_stream(dummy_lsa, bpd_output)
        else:
            return {"error": "No telemetry payload supplied to EdgeShield pipeline."}

        return {
            "lsa": lsa_output,
            "bpd": bpd_output,
            "correlation": correlation_result,
            "timestamp": time.time()
        }
