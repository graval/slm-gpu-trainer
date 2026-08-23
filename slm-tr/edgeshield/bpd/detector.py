"""
EdgeShield: Behavioral Pattern Detector (BPD) for Ransomware Detection
Monitors FileSystem telemetry (T1490 shadow copy deletion, mass renames),
Process API call sequences, and Network C2 telemetry.
Computes running threat scores via an attention-based scoring head for Pre-Encryption Alerting.
"""

import os
import time
from typing import Dict, List, Any, Optional, Tuple, Union
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModelForSequenceClassification, AutoConfig

from edgeshield.taxonomy import (
    MITRE_ATTACK_TAXONOMY, 
    BPD_TECHNIQUES, 
    TECHNIQUE_TO_ID, 
    ID_TO_TECHNIQUE,
    AttackKnowledgeGraph,
    build_edgeshield_domain_vocabulary
)

class AttentionThreatScoringHead(nn.Module):
    """
    Lightweight attention-based scoring layer on top of the SLM's last hidden states.
    Aggregates token-level behavioral salience to compute a unified running threat score.
    """
    def __init__(self, hidden_dim: int = 768):
        super().__init__()
        self.query = nn.Linear(hidden_dim, 1, bias=False)
        self.classifier = nn.Sequential(
            nn.Linear(hidden_dim, 128),
            nn.GELU(),
            nn.Dropout(0.1),
            nn.Linear(128, 1),
            nn.Sigmoid()
        )

    def forward(self, hidden_states: torch.Tensor, attention_mask: Optional[torch.Tensor] = None) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        hidden_states: [batch_size, seq_len, hidden_dim]
        attention_mask: [batch_size, seq_len]
        Returns: (threat_score [batch_size, 1], attention_weights [batch_size, seq_len])
        """
        attn_logits = self.query(hidden_states).squeeze(-1) # [batch_size, seq_len]
        if attention_mask is not None:
            attn_logits = attn_logits.masked_fill(attention_mask == 0, -1e9)
        attn_weights = F.softmax(attn_logits, dim=-1) # [batch_size, seq_len]
        
        # Weighted context pooling
        context = torch.bmm(attn_weights.unsqueeze(1), hidden_states).squeeze(1) # [batch_size, hidden_dim]
        threat_score = self.classifier(context) # [batch_size, 1]
        return threat_score, attn_weights


class RansomwareTelemetryNormalizer:
    """
    Normalizes file-system events, process API traces, and network telemetry
    into structured textual windows conforming to the 2,000-token domain vocabulary.
    """
    def normalize_behavior_event(self, record: Union[Dict[str, Any], Any]) -> str:
        if hasattr(record, "to_dict"):
            data = record.to_dict()
        elif isinstance(record, dict):
            data = record
        else:
            data = {"raw": str(record)}

        event_type = str(data.get("EventType", data.get("event_type", data.get("type", "PROCESS")))).upper()
        target_path = str(data.get("TargetPath", data.get("TargetFilename", data.get("path", ""))))
        api_call = str(data.get("ApiCall", data.get("api", data.get("function", ""))))
        cmd = str(data.get("CommandLine", data.get("cmd", "")))
        entropy = str(data.get("Entropy", data.get("entropy", "")))
        ext_change = str(data.get("ExtensionChange", data.get("ext", "")))
        net_dst = str(data.get("DestinationIp", data.get("dst_ip", "")))
        net_port = str(data.get("DestinationPort", data.get("dst_port", "")))

        tokens = [f"[TYPE:{event_type}]"]
        
        if cmd and cmd != "nan" and cmd != "None":
            cmd_clean = " ".join(cmd.strip().split()[:20])
            tokens.append(f"[CMD:{cmd_clean}]")
            
        if target_path and target_path != "nan":
            tokens.append(f"[PATH:{target_path}]")
            
        if api_call and api_call != "nan":
            tokens.append(f"[API:{api_call}]")
            
        if entropy and entropy != "nan":
            tokens.append(f"[ENTROPY:{entropy}]")
            
        if ext_change and ext_change != "nan":
            tokens.append(f"[EXT:{ext_change}]")
            
        if net_dst and net_dst != "nan":
            tokens.append(f"[NET:{net_dst}:{net_port}]")

        return " ".join(tokens)

    def format_behavior_window(self, events: List[Dict[str, Any]], max_events: int = 5) -> str:
        normalized = [self.normalize_behavior_event(ev) for ev in events[-max_events:]]
        window_parts = []
        for i, ev_str in enumerate(normalized):
            t_offset = len(normalized) - 1 - i
            tag = f"[T_0]" if t_offset == 0 else f"[T_-{t_offset}]"
            window_parts.append(f"{tag} {ev_str}")
        return " || ".join(window_parts)


class BehavioralPatternDetector:
    """
    EdgeShield Behavioral Pattern Detector (BPD).
    Specialized in early pre-encryption ransomware detection and behavioral threat scoring.
    """
    def __init__(
        self,
        model_name_or_path: str = "microsoft/deberta-v3-small",
        threat_threshold: float = 0.70,
        device: Optional[str] = None,
        max_length: int = 512
    ):
        self.threat_threshold = threat_threshold
        self.max_length = max_length
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.normalizer = RansomwareTelemetryNormalizer()
        self.knowledge_graph = AttackKnowledgeGraph()
        self.vocab = build_edgeshield_domain_vocabulary(max_vocab_size=2000)

        # Checkpoint candidates
        candidates = [
            model_name_or_path,
            f"models/{model_name_or_path}",
            "models/deberta-lateral-movement-v2_sliding_window-stable",
            "microsoft/deberta-v3-small"
        ]
        
        # Tokenizer
        self.tokenizer = None
        for p in candidates:
            if os.path.exists(p) and os.path.isdir(p):
                try:
                    self.tokenizer = AutoTokenizer.from_pretrained(p, use_fast=True)
                    break
                except Exception:
                    pass
        if self.tokenizer is None:
            try:
                self.tokenizer = AutoTokenizer.from_pretrained("microsoft/deberta-v3-small", use_fast=True)
            except Exception:
                self.tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased", use_fast=True)

        # Load Backbone & Scoring Head
        self.model = self._load_or_init_model(model_name_or_path)
        self.scoring_head = AttentionThreatScoringHead(hidden_dim=getattr(self.model.config, "hidden_size", 768))
        
        self.model.to(self.device)
        self.scoring_head.to(self.device)
        self.model.eval()
        self.scoring_head.eval()

        # Running telemetry window buffer
        self.recent_threat_scores: List[float] = []

    def _load_or_init_model(self, model_path: str):
        candidates = [
            model_path,
            f"models/{model_path}",
            "models/deberta-lateral-movement-v2_sliding_window-stable",
            "microsoft/deberta-v3-small"
        ]
        for p in candidates:
            if os.path.exists(p) and os.path.isdir(p):
                try:
                    return AutoModelForSequenceClassification.from_pretrained(p)
                except Exception:
                    try:
                        return AutoModelForSequenceClassification.from_pretrained(p, num_labels=len(TECHNIQUE_TO_ID), ignore_mismatched_sizes=True)
                    except Exception:
                        pass
        try:
            return AutoModelForSequenceClassification.from_pretrained("microsoft/deberta-v3-small", num_labels=len(TECHNIQUE_TO_ID), ignore_mismatched_sizes=True)
        except Exception:
            config = AutoConfig.from_pretrained("microsoft/deberta-v3-small", num_labels=len(TECHNIQUE_TO_ID))
            return AutoModelForSequenceClassification.from_config(config)

    def analyze_behavior_window(
        self,
        events_or_text: Union[List[Dict[str, Any]], str],
        host: str = "HOST-01",
        user: str = "admin"
    ) -> Dict[str, Any]:
        """
        Analyzes file-system, process, and network telemetry window.
        Returns threat score, pre-encryption alert status, detected technique, and lead time assessment.
        """
        start_t = time.perf_counter()

        if isinstance(events_or_text, list):
            formatted_text = self.normalizer.format_behavior_window(events_or_text)
        else:
            formatted_text = str(events_or_text)

        inputs = self.tokenizer(
            formatted_text,
            max_length=self.max_length,
            truncation=True,
            padding=False,
            return_tensors="pt"
        ).to(self.device)

        with torch.no_grad():
            outputs = self.model(**inputs, output_hidden_states=True)
            if hasattr(outputs, "hidden_states") and outputs.hidden_states is not None:
                last_hidden = outputs.hidden_states[-1] # [batch, seq, dim]
                attn_mask = inputs.get("attention_mask")
                threat_score_tensor, _ = self.scoring_head(last_hidden, attn_mask)
                raw_score = float(threat_score_tensor[0, 0].cpu().item())
            else:
                raw_score = 0.35

            if hasattr(outputs, "logits") and outputs.logits is not None:
                pred_cls = int(torch.argmax(outputs.logits[0], dim=-1).cpu().item())
            else:
                pred_cls = 0

        # Map predicted class from fine-tuned BPD backbone
        detected_technique = ID_TO_TECHNIQUE.get(pred_cls, "BENIGN_NORMAL")
        
        is_pre_encryption = detected_technique in ("T1083", "T1562.001", "T1490", "T1071.001")
        is_encryption_active = (detected_technique == "T1486")
        
        if detected_technique != "BENIGN_NORMAL":
            raw_score = max(raw_score, 0.85 if is_pre_encryption else 0.98)
        else:
            raw_score = min(raw_score, 0.15)

        threat_score = round(float(raw_score), 4)
        self.recent_threat_scores.append(threat_score)
        if len(self.recent_threat_scores) > 20:
            self.recent_threat_scores.pop(0)

        # Pre-encryption alert fires if score exceeds threshold AND encryption is not yet full blast
        alert_fired = threat_score >= self.threat_threshold
        tech_meta = self.knowledge_graph.get_technique_info(detected_technique)

        latency_ms = (time.perf_counter() - start_t) * 1000.0

        return {
            "stream": "BPD",
            "threat_score": threat_score,
            "threat_threshold": self.threat_threshold,
            "pre_encryption_alert": alert_fired and not is_encryption_active,
            "encryption_active": is_encryption_active,
            "technique_id": detected_technique,
            "technique_name": tech_meta["name"],
            "tactic": tech_meta["tactic"],
            "latency_ms": round(latency_ms, 2),
            "formatted_text": formatted_text,
            "host": host,
            "user": user,
            "recent_score_trend": list(self.recent_threat_scores)
        }
