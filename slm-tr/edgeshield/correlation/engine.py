"""
EdgeShield: ATT&CK-Aligned Correlation & Predictive Threat Hunting Engine
Correlates dual-stream outputs (LSA + BPD) across temporal windows into Coordinated Intrusion Alerts,
and uses KNN-based Collaborative Filtering over MITRE ATT&CK v15 graphs for predictive threat hunting.
"""

import time
from typing import Dict, List, Any, Optional, Tuple, Union
from edgeshield.taxonomy import AttackKnowledgeGraph, MITRE_ATTACK_TAXONOMY

class AttackCorrelationEngine:
    """
    Coordinates and fuses real-time telemetry from both the Log Semantic Analyzer (LSA)
    and Behavioral Pattern Detector (BPD) to detect synchronized multi-stage enterprise breaches.
    """
    def __init__(self, correlation_window_sec: float = 300.0):
        self.correlation_window_sec = correlation_window_sec
        self.knowledge_graph = AttackKnowledgeGraph()
        
        # Buffer of recent stream events
        self.lsa_history: List[Dict[str, Any]] = []
        self.bpd_history: List[Dict[str, Any]] = []
        self.active_incidents: List[Dict[str, Any]] = []

    def ingest_lsa_event(self, lsa_result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Ingests an event from the LSA lateral movement stream and checks for correlation."""
        lsa_result["received_at"] = time.time()
        self.lsa_history.append(lsa_result)
        self._prune_history()
        return self._evaluate_correlation()

    def ingest_bpd_event(self, bpd_result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Ingests an event from the BPD ransomware behavioral stream and checks for correlation."""
        bpd_result["received_at"] = time.time()
        self.bpd_history.append(bpd_result)
        self._prune_history()
        return self._evaluate_correlation()

    def correlate_dual_stream(self, lsa_result: Dict[str, Any], bpd_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Direct synchronous correlation between an LSA window and a BPD window.
        """
        now = time.time()
        is_lm = lsa_result.get("is_lateral_movement", False)
        is_ransomware = bpd_result.get("pre_encryption_alert", False) or bpd_result.get("encryption_active", False)
        threat_score = bpd_result.get("threat_score", 0.0)
        
        observed_techniques = []
        if is_lm and lsa_result.get("technique_id") != "BENIGN_NORMAL":
            observed_techniques.append(lsa_result["technique_id"])
        if is_ransomware and bpd_result.get("technique_id") != "BENIGN_NORMAL":
            observed_techniques.append(bpd_result["technique_id"])

        # Check for Coordinated Intrusion: Both Lateral Movement AND Ransomware behavioral signals
        is_coordinated = is_lm and is_ransomware
        
        # Determine Severity Level
        if is_coordinated:
            severity = "CRITICAL (COORDINATED INTRUSION)"
            incident_type = "MULTI-STAGE LATERAL MOVEMENT -> RANSOMWARE KILL CHAIN"
            action_recommended = "IMMEDIATE HOST ISOLATION & DOMAIN-WIDE CREDENTIAL REVOCATION"
        elif is_ransomware:
            severity = "HIGH (PRE-ENCRYPTION THREAT)" if bpd_result.get("pre_encryption_alert") else "CRITICAL (ENCRYPTION ACTIVE)"
            incident_type = "RANSOMWARE PRE-ENCRYPTION BEHAVIOR DETECTED"
            action_recommended = "TERMINATE SUSPECT PROCESSES & RESTORE VOLUME SHADOW COPIES"
        elif is_lm:
            severity = "HIGH (LATERAL PIVOT DETECTED)"
            incident_type = "ACTIVE AD DOMAIN LATERAL MOVEMENT"
            action_recommended = "ISOLATE PIVOT HOST & AUDIT KERBEROS TICKET ISSUANCE"
        else:
            severity = "LOW (BENIGN BASELINE)"
            incident_type = "NORMAL OPERATING TELEMETRY"
            action_recommended = "ROUTINE MONITORING"

        # Query next technique predictions
        next_predicted_techniques = self.knowledge_graph.predict_next_techniques(observed_techniques, top_k=3)

        # Build Incident Record
        incident = {
            "timestamp": now,
            "is_coordinated_intrusion": is_coordinated,
            "severity": severity,
            "incident_type": incident_type,
            "action_recommended": action_recommended,
            "lsa_technique": lsa_result.get("technique_id", "N/A"),
            "lsa_technique_name": lsa_result.get("technique_name", "N/A"),
            "lsa_confidence": lsa_result.get("confidence", 0.0),
            "bpd_threat_score": threat_score,
            "bpd_technique": bpd_result.get("technique_id", "N/A"),
            "bpd_technique_name": bpd_result.get("technique_name", "N/A"),
            "observed_techniques": observed_techniques,
            "predictive_threat_hunting": next_predicted_techniques,
            "multi_hop_chains": lsa_result.get("multi_hop_chains", [])
        }

        if is_coordinated:
            self.active_incidents.append(incident)
            if len(self.active_incidents) > 50:
                self.active_incidents.pop(0)

        return incident

    def _evaluate_correlation(self) -> Optional[Dict[str, Any]]:
        """Evaluates buffered streams within the temporal correlation window."""
        now = time.time()
        recent_lm = [ev for ev in self.lsa_history if ev.get("is_lateral_movement", False) and (now - ev["received_at"]) <= self.correlation_window_sec]
        recent_rw = [ev for ev in self.bpd_history if (ev.get("pre_encryption_alert", False) or ev.get("encryption_active", False)) and (now - ev["received_at"]) <= self.correlation_window_sec]

        if recent_lm and recent_rw:
            latest_lsa = recent_lm[-1]
            latest_bpd = recent_rw[-1]
            return self.correlate_dual_stream(latest_lsa, latest_bpd)
        return None

    def _prune_history(self):
        now = time.time()
        self.lsa_history = [ev for ev in self.lsa_history if (now - ev.get("received_at", now)) <= (self.correlation_window_sec * 2)]
        self.bpd_history = [ev for ev in self.bpd_history if (now - ev.get("received_at", now)) <= (self.correlation_window_sec * 2)]
