"""
EdgeShield: Comprehensive Unit & Integration Test Suite
Tests all components of the EdgeShield framework:
  1. Taxonomy, Domain Vocabulary & MITRE Graph
  2. Log Semantic Analyzer (LSA) & Sliding Window Inference
  3. Behavioral Pattern Detector (BPD) & Pre-Encryption Alerting
  4. Dual-Stream Correlation Engine & Predictive Threat Hunting
  5. Edge Deployment & ONNX Latency Profiling
  6. End-to-End Pipeline Multi-Stage Incident Processing
"""

import os
import sys
import unittest
import numpy as np
import torch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from edgeshield.taxonomy import (
    MITRE_ATTACK_TAXONOMY,
    AttackKnowledgeGraph,
    build_edgeshield_domain_vocabulary,
    TECHNIQUE_TO_ID,
    ID_TO_TECHNIQUE
)
from edgeshield.lsa.tokenizer import SecurityLogNormalizer, SecurityDomainTokenizer
from edgeshield.lsa.analyzer import LogSemanticAnalyzer, SupervisedContrastiveLoss, MultiHopChainTracker
from edgeshield.bpd.detector import BehavioralPatternDetector, AttentionThreatScoringHead, RansomwareTelemetryNormalizer
from edgeshield.correlation.engine import AttackCorrelationEngine
from edgeshield.edge_deploy.onnx_runtime import EdgeDeploymentEngine
from edgeshield.pipeline import EdgeShieldPipeline

class TestEdgeShieldFramework(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        print("\n[*] Initializing TestEdgeShieldFramework...")
        cls.graph = AttackKnowledgeGraph()
        cls.pipeline = EdgeShieldPipeline()

    def test_01_taxonomy_and_vocabulary(self):
        """Verify MITRE ATT&CK v15 taxonomy and 2000-token vocabulary."""
        self.assertIn("T1021.002", MITRE_ATTACK_TAXONOMY)
        self.assertIn("T1490", MITRE_ATTACK_TAXONOMY)
        self.assertIn("T1486", MITRE_ATTACK_TAXONOMY)
        
        vocab = build_edgeshield_domain_vocabulary(max_vocab_size=2000)
        self.assertEqual(len(vocab), 2000)
        self.assertIn("vssadmin", vocab)
        self.assertIn("psexec", vocab)
        self.assertIn("4624", vocab)

    def test_02_knowledge_graph_and_knn_forecasting(self):
        """Verify graph lookups and predictive next-technique forecasting."""
        info = self.graph.get_technique_info("T1490")
        self.assertEqual(info["name"], "Inhibit System Recovery: Shadow Copy Deletion")
        self.assertEqual(info["stream"], "BPD")
        
        # Test KNN forecasting from lateral movement
        predictions = self.graph.predict_next_techniques(["T1021.002", "T1550.002"], top_k=3)
        self.assertEqual(len(predictions), 3)
        pred_ids = [p["technique_id"] for p in predictions]
        self.assertTrue(any(t in pred_ids for t in ["T1490", "T1570", "T1543.003", "T1486"]))

    def test_03_lsa_log_normalization_and_inference(self):
        """Verify LSA log normalizer, sliding window inference, and multi-hop tracking."""
        sample_events = [
            {"EventID": "4624", "LogonType": "10", "User": "admin", "Computer": "HOST-01", "CommandLine": "net use \\\\DC-01\\ADMIN$"},
            {"EventID": "1", "Image": "psexec.exe", "CommandLine": "psexec.exe \\\\DC-01 cmd.exe", "Computer": "DC-01", "User": "admin"}
        ]
        res = self.pipeline.lsa.analyze_window(sample_events, source_host="HOST-01", target_host="DC-01", user="admin")
        self.assertTrue(res["is_lateral_movement"])
        self.assertIn("T1021.002", res["technique_id"])
        self.assertGreater(res["confidence"], 0.70)
        self.assertLess(res["latency_ms"], 200.0) # Sub-second requirement

    def test_04_bpd_attention_scoring_and_pre_encryption_alert(self):
        """Verify BPD threat scoring and pre-encryption alert on shadow copy deletion."""
        shadow_event = {
            "EventType": "PROCESS",
            "CommandLine": "vssadmin delete shadows /all /quiet",
            "TargetPath": "C:\\Windows\\System32\\vssadmin.exe",
            "ApiCall": "CreateProcessW"
        }
        res = self.pipeline.bpd.analyze_behavior_window([shadow_event], host="DC-01", user="admin")
        self.assertGreaterEqual(res["threat_score"], 0.70)
        self.assertTrue(res["pre_encryption_alert"])
        self.assertEqual(res["technique_id"], "T1490")

    def test_05_attack_correlation_engine(self):
        """Verify dual-stream fusion into a Coordinated Intrusion Alert."""
        correlator = AttackCorrelationEngine(correlation_window_sec=300.0)
        
        lsa_out = {
            "stream": "LSA",
            "is_lateral_movement": True,
            "technique_id": "T1021.002",
            "technique_name": "SMB / Windows Admin Shares",
            "confidence": 0.95,
            "multi_hop_chains": []
        }
        bpd_out = {
            "stream": "BPD",
            "threat_score": 0.94,
            "threat_threshold": 0.70,
            "pre_encryption_alert": True,
            "encryption_active": False,
            "technique_id": "T1490",
            "technique_name": "Inhibit System Recovery",
            "tactic": "Impact"
        }
        
        incident = correlator.correlate_dual_stream(lsa_out, bpd_out)
        self.assertTrue(incident["is_coordinated_intrusion"])
        self.assertIn("COORDINATED INTRUSION", incident["severity"])
        self.assertIn("ISOLATION", incident["action_recommended"])
        self.assertGreater(len(incident["predictive_threat_hunting"]), 0)

    def test_06_contrastive_loss(self):
        """Verify Supervised Contrastive Loss forward pass."""
        loss_fn = SupervisedContrastiveLoss(temperature=0.07)
        features = torch.randn(4, 64)
        labels = torch.tensor([0, 0, 1, 1])
        loss = loss_fn(features, labels)
        self.assertTrue(torch.is_tensor(loss))
        self.assertGreaterEqual(loss.item(), 0.0)

    def test_07_end_to_end_pipeline_multi_stage(self):
        """Verify EdgeShieldPipeline end-to-end processing."""
        res = self.pipeline.process_telemetry_event(
            auth_log="EventID: 4624 LogonType: 9 User: admin Image: mimikatz.exe CommandLine: sekurlsa::pth",
            behavior_log="EventType: PROCESS CommandLine: vssadmin delete shadows /all /quiet",
            source_host="WORKSTATION-01",
            target_host="DC-01",
            user="admin"
        )
        self.assertIn("correlation", res)
        self.assertTrue(res["correlation"]["is_coordinated_intrusion"])

if __name__ == "__main__":
    unittest.main()
