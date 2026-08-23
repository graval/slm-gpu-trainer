import os
import re
from typing import Dict, Any, List, Optional, Union
from transformers import AutoTokenizer, PreTrainedTokenizerFast

class SecurityLogNormalizer:
    """
    Normalizes heterogeneous Windows Security Event Logs, Kerberos records,
    and NetFlow telemetry into standardized structured textual representations for SLMs.
    """
    def __init__(self):
        # Regex patterns for high-cardinality security identifiers
        self.guid_pattern = re.compile(r'\{?[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\}?')
        self.sid_pattern = re.compile(r'S-1-5-[0-9\-]+')
        self.hex_pattern = re.compile(r'0x[0-9a-fA-F]+')
        self.ip_pattern = re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}(?::\d+)?\b')

    def normalize_event(self, record: Union[Dict[str, Any], Any]) -> str:
        """
        Transforms raw event dictionary / pandas Series into a clean, token-efficient string.
        Handles Event IDs 4624, 4625, 4648, 4672, Kerberos, NetFlow, and Sysmon.
        """
        if hasattr(record, "to_dict"):
            data = record.to_dict()
        elif isinstance(record, dict):
            data = record
        else:
            data = {"raw": str(record)}

        event_id = str(data.get("EventID", data.get("event_id", "0"))).replace(".0", "")
        computer = str(data.get("Computer", data.get("computer", data.get("SourceHostname", "HOST_UNK"))))
        user = str(data.get("User", data.get("TargetUser", data.get("user", "UNKNOWN_USER"))))
        image = str(data.get("Image", data.get("image", data.get("SourceImage", "SYSTEM"))))
        cmd = str(data.get("CommandLine", data.get("command_line", data.get("Details", ""))))
        logon_type = str(data.get("LogonType", data.get("logon_type", "")))
        src_ip = str(data.get("SourceIp", data.get("src_ip", "-")))
        dst_ip = str(data.get("DestinationIp", data.get("dst_ip", "-")))
        dst_port = str(data.get("DestinationPort", data.get("dst_port", "-")))
        privs = str(data.get("GrantedAccess", data.get("PrivilegeList", "")))
        hashes = str(data.get("Hashes", data.get("Hash", "")))

        # Format based on event type
        tokens = [f"[EID:{event_id}]", f"[HOST:{computer}]", f"[USER:{user}]"]
        
        if logon_type and logon_type != "-" and logon_type != "nan":
            tokens.append(f"[LOGON_TYPE:{logon_type}]")
            
        if src_ip != "-" and src_ip != "nan" and dst_ip != "-" and dst_ip != "nan":
            tokens.append(f"[FLOW:{src_ip}->{dst_ip}:{dst_port}]")
        elif dst_ip != "-" and dst_ip != "nan":
            tokens.append(f"[DST:{dst_ip}:{dst_port}]")
            
        if image and image != "SYSTEM" and image != "nan":
            # Extract basename + clean image path
            img_clean = image.replace("\\", "/").split("/")[-1]
            tokens.append(f"[IMG:{img_clean}]")
            
        if cmd and cmd != "nan" and cmd != "None":
            # Sanitize and truncate command line
            cmd_clean = " ".join(cmd.strip().split()[:25])
            tokens.append(f"[CMD:{cmd_clean}]")
            
        if privs and privs != "nan":
            tokens.append(f"[ACCESS:{privs}]")
            
        if hashes and hashes != "nan" and len(hashes) > 5:
            tokens.append(f"[HASH:{hashes[:32]}]")

        return " ".join(tokens)

    def format_sliding_window(self, events: List[Dict[str, Any]], max_events: int = 5) -> str:
        """
        Combines chronological sequence of normalized events into a multi-event sliding window.
        """
        normalized_events = [self.normalize_event(ev) for ev in events[-max_events:]]
        window_parts = []
        for i, ev_str in enumerate(normalized_events):
            t_offset = len(normalized_events) - 1 - i
            tag = f"[T_0]" if t_offset == 0 else f"[T_-{t_offset}]"
            window_parts.append(f"{tag} {ev_str}")
        return " || ".join(window_parts)


class SecurityDomainTokenizer:
    """
    Wraps standard Hugging Face tokenizers with cybersecurity domain vocabulary.
    """
    def __init__(self, base_tokenizer_id: str = "microsoft/deberta-v3-small", max_length: int = 512):
        self.max_length = max_length
        candidates = [
            base_tokenizer_id,
            f"models/{base_tokenizer_id}",
            "models/deberta-lateral-movement-v2_sliding_window-stable",
            "microsoft/deberta-v3-small"
        ]
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
        self.normalizer = SecurityLogNormalizer()

    def tokenize_window(self, text_or_events: Union[str, List[Dict[str, Any]]]):
        if isinstance(text_or_events, list):
            text = self.normalizer.format_sliding_window(text_or_events)
        else:
            text = str(text_or_events)
        return self.tokenizer(
            text,
            max_length=self.max_length,
            truncation=True,
            padding="max_length",
            return_tensors="pt"
        )
