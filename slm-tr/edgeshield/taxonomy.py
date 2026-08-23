"""
EdgeShield: MITRE ATT&CK v15 Taxonomy, Vocabulary & Threat Knowledge Graph
Defines structured mappings for Lateral Movement (TA0008) and Ransomware (TA0040, TA0005, TA0007, TA0002),
along with a 2,000-token domain-specific cybersecurity vocabulary and co-occurrence graphs.
"""

from typing import Dict, List, Any, Optional, Set, Tuple

# ---------------------------------------------------------------------------
# MITRE ATT&CK v15 Enterprise Taxonomy Definition
# ---------------------------------------------------------------------------

MITRE_ATTACK_TAXONOMY: Dict[str, Dict[str, Any]] = {
    # ------------------ LATERAL MOVEMENT (TA0008) ------------------
    "T1021.001": {
        "name": "Remote Desktop Protocol (RDP)",
        "tactic": "Lateral Movement (TA0008)",
        "tactic_id": "TA0008",
        "description": "Adversaries may use Valid Accounts to log into remote machines using RDP for lateral movement.",
        "stream": "LSA",
        "category": "lateral_movement",
        "telemetry_indicators": ["Event ID 4624 (Logon Type 10)", "mstsc.exe", "Port 3389 (RDP)", "rdpclip.exe"],
        "co_occurring_techniques": ["T1550.002", "T1078", "T1570", "T1490"]
    },
    "T1021.002": {
        "name": "SMB / Windows Admin Shares",
        "tactic": "Lateral Movement (TA0008)",
        "tactic_id": "TA0008",
        "description": "Adversaries may use SMB and Windows administrative shares (ADMIN$, C$, IPC$) to remotely interact with target systems.",
        "stream": "LSA",
        "category": "lateral_movement",
        "telemetry_indicators": ["Event ID 1 (psexec.exe / paexec.exe)", "Event ID 17 (Named Pipe \\psexec)", "Event ID 3 (Port 445 SMB)", "net use \\\\<ip>\\<share>"],
        "co_occurring_techniques": ["T1570", "T1543.003", "T1550.002", "T1490", "T1486"]
    },
    "T1021.006": {
        "name": "Windows Remote Management (WinRM)",
        "tactic": "Lateral Movement (TA0008)",
        "tactic_id": "TA0008",
        "description": "Adversaries may use WinRM and PowerShell Remoting (WinRS / Enter-PSSession) to execute commands across remote hosts.",
        "stream": "LSA",
        "category": "lateral_movement",
        "telemetry_indicators": ["wsmprovhost.exe", "winrs.exe", "Port 5985/5986 HTTP/HTTPS", "Invoke-Command -ComputerName"],
        "co_occurring_techniques": ["T1059.001", "T1550.002", "T1570", "T1490"]
    },
    "T1047": {
        "name": "Windows Management Instrumentation (WMI)",
        "tactic": "Execution (TA0002) / Lateral Movement (TA0008)",
        "tactic_id": "TA0008",
        "description": "Adversaries may abuse WMI to execute malicious commands and scripts remotely over RPC/DCOM on network endpoints.",
        "stream": "LSA",
        "category": "lateral_movement",
        "telemetry_indicators": ["wmic.exe process call create /node:", "WmiPrvSE.exe spawning cmd.exe / powershell.exe", "Port 135 RPC"],
        "co_occurring_techniques": ["T1059.001", "T1083", "T1490", "T1486"]
    },
    "T1053.005": {
        "name": "Scheduled Task / Job: Scheduled Task",
        "tactic": "Execution (TA0002) / Lateral Movement (TA0008)",
        "tactic_id": "TA0008",
        "description": "Adversaries may abuse task scheduling APIs or schtasks.exe to execute tasks on remote hosts (/s parameter).",
        "stream": "LSA",
        "category": "lateral_movement",
        "telemetry_indicators": ["schtasks.exe /create /s <remote_host>", "schtasks.exe /run /s <remote_host>"],
        "co_occurring_techniques": ["T1021.002", "T1570", "T1490"]
    },
    "T1543.003": {
        "name": "Create or Modify System Process: Windows Service",
        "tactic": "Persistence (TA0003) / Privilege Escalation (TA0004) / Lateral Movement (TA0008)",
        "tactic_id": "TA0008",
        "description": "Adversaries may create or modify Windows services (e.g. via sc.exe) on remote machines to execute payloads as SYSTEM.",
        "stream": "LSA",
        "category": "lateral_movement",
        "telemetry_indicators": ["sc.exe \\\\<remote_host> create", "sc.exe \\\\<remote_host> start", "PSEXESVC service creation"],
        "co_occurring_techniques": ["T1021.002", "T1570", "T1490"]
    },
    "T1550.002": {
        "name": "Pass the Hash / Alternate Auth Material",
        "tactic": "Lateral Movement (TA0008) / Defense Evasion (TA0005)",
        "tactic_id": "TA0008",
        "description": "Adversaries may 'Pass the Hash' using stolen NTLM hashes or Kerberos tickets to authenticate to remote hosts without cleartext passwords.",
        "stream": "LSA",
        "category": "lateral_movement",
        "telemetry_indicators": ["sekurlsa::pth", "LogonType 9 (NewCredentials)", "Event ID 4624 (LogonType 9 / NTLM V2)", "Mimikatz"],
        "co_occurring_techniques": ["T1021.002", "T1021.001", "T1003.001", "T1570", "T1490"]
    },
    "T1558": {
        "name": "Steal or Forge Kerberos Tickets",
        "tactic": "Credential Access (TA0006) / Lateral Movement (TA0008)",
        "tactic_id": "TA0008",
        "description": "Adversaries may forge Kerberos tickets (Golden/Silver Ticket, Kerberoasting) to traverse Active Directory domain trusts.",
        "stream": "LSA",
        "category": "lateral_movement",
        "telemetry_indicators": ["Event ID 4768 / 4769 (Kerberos TGT/TGS)", "RC4 Kerberos encryption type 0x17", "Rubeus", "Invoke-Kerberoast"],
        "co_occurring_techniques": ["T1550.002", "T1021.002", "T1490"]
    },
    "T1570": {
        "name": "Lateral Tool Transfer",
        "tactic": "Lateral Movement (TA0008)",
        "tactic_id": "TA0008",
        "description": "Adversaries may transfer tools or files between systems in an enterprise network to support lateral movement.",
        "stream": "LSA",
        "category": "lateral_movement",
        "telemetry_indicators": ["net.exe use \\\\<ip>\\<share>", "copy / xcopy over administrative shares", "bitsadmin /transfer", "certutil.exe -urlcache"],
        "co_occurring_techniques": ["T1021.002", "T1490", "T1486"]
    },

    # ------------------ RANSOMWARE & PRE-ENCRYPTION BEHAVIORS ------------------
    "T1490": {
        "name": "Inhibit System Recovery: Shadow Copy Deletion",
        "tactic": "Impact (TA0040) / Defense Evasion (TA0005)",
        "tactic_id": "TA0040",
        "description": "Adversaries delete or disable Volume Shadow Copies, backup catalogs, and recovery configurations to prevent recovery.",
        "stream": "BPD",
        "category": "ransomware_pre_encryption",
        "telemetry_indicators": [
            "vssadmin delete shadows /all /quiet",
            "wmic shadowcopy delete",
            "wbadmin delete catalog -quiet",
            "bcdedit /set {default} recoveryenabled No",
            "bcdedit /set {default} bootstatuspolicy ignoreallfailures"
        ],
        "co_occurring_techniques": ["T1486", "T1083", "T1021.002", "T1562.001"]
    },
    "T1486": {
        "name": "Data Encrypted for Impact",
        "tactic": "Impact (TA0040)",
        "tactic_id": "TA0040",
        "description": "Adversaries encrypt data on target systems to interrupt availability of system and network resources.",
        "stream": "BPD",
        "category": "ransomware_encryption",
        "telemetry_indicators": [
            "Mass file renames with new extension (.locked, .enc, .ransom)",
            "High-entropy file write burst",
            "Drop of ransom note (README.txt, HOW_TO_DECRYPT.html)",
            "CryptEncrypt / BCryptEncrypt API call chains"
        ],
        "co_occurring_techniques": ["T1490", "T1083", "T1071.001"]
    },
    "T1083": {
        "name": "File and Directory Discovery (Pre-Encryption Enumeration)",
        "tactic": "Discovery (TA0007)",
        "tactic_id": "TA0007",
        "description": "Adversaries enumerate files, directories, network shares, and connected volumes prior to encryption staging.",
        "stream": "BPD",
        "category": "ransomware_pre_encryption",
        "telemetry_indicators": [
            "Rapid recursive traversal of C:\\, D:\\, network shares",
            "FindFirstFileW / FindNextFileW loops",
            "GetLogicalDriveStringsW / GetDriveTypeW inspection"
        ],
        "co_occurring_techniques": ["T1490", "T1486", "T1021.002"]
    },
    "T1562.001": {
        "name": "Impair Defenses: Disable or Modify Tools",
        "tactic": "Defense Evasion (TA0005)",
        "tactic_id": "TA0005",
        "description": "Adversaries disable or tamper with security software, antivirus, EDR agents, and event logging prior to encryption.",
        "stream": "BPD",
        "category": "ransomware_pre_encryption",
        "telemetry_indicators": [
            "sc stop WinDefend",
            "net stop \"Windows Defender Service\"",
            "fltmc unload",
            "taskkill /f /im edr_agent.exe",
            "Set-MpPreference -DisableRealtimeMonitoring $true"
        ],
        "co_occurring_techniques": ["T1490", "T1486"]
    },
    "T1071.001": {
        "name": "Application Layer Protocol: Web Protocols (C2 / Exfiltration)",
        "tactic": "Command and Control (TA0011) / Exfiltration (TA0010)",
        "tactic_id": "TA0011",
        "description": "Adversaries communicate with command and control infrastructure or exfiltrate sensitive files prior to encryption (double extortion).",
        "stream": "BPD",
        "category": "ransomware_pre_encryption",
        "telemetry_indicators": [
            "Unexpected high-volume outbound POST / PUT requests",
            "Encrypted TLS beaconing on non-standard ports",
            "Mega.nz / Dropbox / WebDAV upload scripts (rclone.exe)"
        ],
        "co_occurring_techniques": ["T1490", "T1486", "T1570"]
    },
    "T1003.001": {
        "name": "OS Credential Dumping: LSASS Memory",
        "tactic": "Credential Access (TA0006)",
        "tactic_id": "TA0006",
        "description": "Adversaries dump LSASS memory to extract password hashes, Kerberos tickets, and cleartext credentials.",
        "stream": "LSA",
        "category": "lateral_movement",
        "telemetry_indicators": ["rundll32.exe comsvcs.dll MiniDump", "procdump.exe -ma lsass.exe", "Event ID 10 LSASS handle access 0x1FFFFF"],
        "co_occurring_techniques": ["T1550.002", "T1021.002", "T1558"]
    }
}

# Technique lists by stream
LSA_TECHNIQUES = [k for k, v in MITRE_ATTACK_TAXONOMY.items() if v["stream"] == "LSA"]
BPD_TECHNIQUES = [k for k, v in MITRE_ATTACK_TAXONOMY.items() if v["stream"] == "BPD"]

# Technique labels to integer indices
TECHNIQUE_TO_ID = {k: idx for idx, k in enumerate(sorted(MITRE_ATTACK_TAXONOMY.keys()))}
TECHNIQUE_TO_ID["BENIGN_NORMAL"] = len(TECHNIQUE_TO_ID)
ID_TO_TECHNIQUE = {v: k for k, v in TECHNIQUE_TO_ID.items()}

# ---------------------------------------------------------------------------
# 2,000-Token Constrained Cybersecurity Domain Vocabulary (UpSight Design)
# ---------------------------------------------------------------------------

BASE_CYBER_DOMAIN_TERMS: List[str] = [
    # MITRE ATT&CK tactics & techniques
    "TA0001", "TA0002", "TA0003", "TA0004", "TA0005", "TA0006", "TA0007", "TA0008", "TA0009", "TA0010", "TA0011", "TA0040",
    "T1021", "T1021.001", "T1021.002", "T1021.006", "T1047", "T1053", "T1053.005", "T1543", "T1543.003",
    "T1550", "T1550.002", "T1558", "T1570", "T1490", "T1486", "T1083", "T1562", "T1562.001", "T1071", "T1071.001", "T1003", "T1003.001",
    
    # Windows Security Event IDs & Channels
    "4624", "4625", "4648", "4672", "4768", "4769", "4776", "4720", "4726", "4738", "7045", "4688", "4689",
    "Sysmon", "Security", "System", "Microsoft-Windows-Sysmon/Operational", "Microsoft-Windows-Security-Auditing",
    "EventID", "SystemTime", "UtcTime", "Computer", "User", "LogonType", "LogonId", "LogonGuid", "ProcessId", "ProcessGuid",
    "ParentProcessId", "ParentProcessGuid", "Image", "CommandLine", "ParentImage", "ParentCommandLine", "CurrentDirectory",
    "GrantedAccess", "CallTrace", "PipeName", "SourceIp", "SourcePort", "DestinationIp", "DestinationPort", "Protocol",
    
    # Logon Types
    "LogonType=2", "LogonType=3", "LogonType=4", "LogonType=5", "LogonType=7", "LogonType=8", "LogonType=9", "LogonType=10", "LogonType=11",
    "Interactive", "Network", "Batch", "Service", "Unlock", "NetworkCleartext", "NewCredentials", "RemoteInteractive", "CachedInteractive",
    
    # Execution & Lateral Movement Binaries / Tools
    "psexec", "psexec.exe", "psexesvc", "psexesvc.exe", "paexec", "paexec.exe", "wmic", "wmic.exe", "wmiprvse.exe",
    "winrs", "winrs.exe", "wsmprovhost.exe", "powershell.exe", "pwsh.exe", "cmd.exe", "schtasks.exe", "sc.exe",
    "net.exe", "net1.exe", "rundll32.exe", "reg.exe", "regsvr32.exe", "mshta.exe", "cscript.exe", "wscript.exe",
    "certutil.exe", "bitsadmin.exe", "curl.exe", "wget.exe", "rclone.exe", "7z.exe", "rar.exe", "winrar.exe",
    "mimikatz", "mimikatz.exe", "rubeus.exe", "procdump.exe", "nanodump.exe", "lazagne.exe", "secretsdump.py",
    "impacket", "wmiexec.py", "psexec.py", "smbexec.py", "atexec.py", "dcomexec.py",
    
    # Ransomware & Impact Commands
    "vssadmin", "delete", "shadows", "shadowcopy", "wbadmin", "catalog", "bcdedit", "recoveryenabled", "bootstatuspolicy",
    "ignoreallfailures", "fltmc", "unload", "taskkill", "WinDefend", "DisableRealtimeMonitoring",
    "Set-MpPreference", "CryptEncrypt", "BCryptEncrypt", "FindFirstFileW", "FindNextFileW",
    ".locked", ".enc", ".ransom", ".crypted", ".crypto", "README.txt", "HOW_TO_DECRYPT.html", "DECRYPT_FILES.txt",
    "GetLogicalDriveStringsW", "GetDriveTypeW", "volume", "backup", "snapshot", "encryption", "entropy",
    
    # Network Protocols, Shares & Ports
    "SMB", "RDP", "WinRM", "WMI", "RPC", "Kerberos", "NTLM", "DCOM", "LDAP", "LDAPS", "DNS", "HTTP", "HTTPS",
    "Port:445", "Port:3389", "Port:5985", "Port:5986", "Port:135", "Port:88", "Port:389", "Port:636", "Port:80", "Port:443",
    "ADMIN$", "C$", "IPC$", "SYSVOL", "NETLOGON", "\\\\*\\ADMIN$", "\\\\*\\C$", "\\\\*\\IPC$",
    "\\pipe\\psexec", "\\pipe\\paexec", "\\pipe\\svcctl", "\\pipe\\wkssvc", "\\pipe\\samr", "\\pipe\\lsarpc",
    
    # Security Descriptors & Well-Known SIDs / GUIDs
    "S-1-5-18", "S-1-5-19", "S-1-5-20", "S-1-5-21", "S-1-5-32-544", "S-1-5-32-545", "NT AUTHORITY\\SYSTEM",
    "NT AUTHORITY\\NETWORK SERVICE", "NT AUTHORITY\\LOCAL SERVICE", "BUILTIN\\Administrators", "Domain Admins",
    "0x1FFFFF", "0x1000", "0x1400", "0x00000000", "0x17", "0x12", "0x40", "0x80",
    "SeDebugPrivilege", "SeTcbPrivilege", "SeImpersonatePrivilege", "SeBackupPrivilege", "SeRestorePrivilege",
    
    # Common Attack Arguments & Tokens
    "sekurlsa::pth", "sekurlsa::logonpasswords", "kerberos::golden", "kerberos::silver", "lsadump::sam",
    "comsvcs.dll,#24", "comsvcs.dll,MiniDump", "/node:", "process call create", "Enter-PSSession",
    "Invoke-Command", "-ComputerName", "-ScriptBlock", "/create", "/run", "/s", "/tn", "/tr", "/sc",
    "save", "HKLM\\SAM", "HKLM\\SYSTEM", "HKLM\\SECURITY", "rc4_hmac", "aes256_cts_hmac_sha1"
]

def build_edgeshield_domain_vocabulary(max_vocab_size: int = 2000) -> List[str]:
    """
    Constructs the exact ~2,000-token constrained security vocabulary
    drawn from the MITRE ATT&CK Enterprise Matrix, Windows telemetry fields,
    hex hashes, GUIDs, SIDs, and ransomware behavioral keywords (UpSight method).
    """
    vocab = list(dict.fromkeys(BASE_CYBER_DOMAIN_TERMS)) # preserve order & dedup
    
    # Generate structured sub-tokens for IP subnets, hex patterns, ports, and EventIDs
    for eid in [4624, 4625, 4648, 4672, 4768, 4769, 4776, 7045, 1, 2, 3, 5, 7, 8, 10, 11, 12, 13, 17, 18, 22]:
        vocab.append(f"EventID:{eid}")
    
    for port in [21, 22, 23, 25, 53, 80, 88, 135, 137, 138, 139, 389, 443, 445, 636, 1433, 3389, 4444, 5985, 5986, 8080, 8443, 9001]:
        vocab.append(f"Port:{port}")
        
    for pfx in ["192.168.", "10.0.", "172.16.", "127.0.0.1", "0.0.0.0"]:
        vocab.append(pfx)
        
    # Hex byte tokens (0x00 to 0xFF) for unfragmented hash and memory address tokenization
    for b in range(256):
        vocab.append(f"0x{b:02x}")
        
    # Common file extensions
    for ext in [".exe", ".dll", ".ps1", ".vbs", ".bat", ".cmd", ".dmp", ".sys", ".tmp", ".log", ".txt", ".csv", ".json", ".zip", ".tar.gz"]:
        vocab.append(ext)
        
    # Pad or truncate to max_vocab_size with structured placeholders
    idx = 1
    while len(vocab) < max_vocab_size:
        vocab.append(f"<sec_token_{idx}>")
        idx += 1
        
    return vocab[:max_vocab_size]

# ---------------------------------------------------------------------------
# MITRE ATT&CK v15 Knowledge Graph & Co-occurrence Transitions
# ---------------------------------------------------------------------------

class AttackKnowledgeGraph:
    """
    Hierarchical Knowledge Graph built from MITRE ATT&CK v15.
    Encodes:
      1. Tactic -> Technique -> Sub-technique hierarchies.
      2. Co-occurrence transition probabilities between lateral movement and ransomware.
      3. KNN / Graph query forecasting for the next most probable attacker steps.
    """
    def __init__(self):
        self.taxonomy = MITRE_ATTACK_TAXONOMY
        self._build_cooccurrence_matrix()

    def _build_cooccurrence_matrix(self):
        """Constructs adjacency weights representing empirical multi-stage attack transitions."""
        self.transition_weights: Dict[str, Dict[str, float]] = {}
        for tech_id, meta in self.taxonomy.items():
            self.transition_weights[tech_id] = {}
            co_occurring = meta.get("co_occurring_techniques", [])
            for target in co_occurring:
                if target in self.taxonomy:
                    # Give higher weight to cross-stream progression (e.g. Lateral Movement -> Inhibit System Recovery -> Encryption)
                    source_stream = meta.get("stream")
                    target_stream = self.taxonomy[target].get("stream")
                    weight = 0.85 if source_stream != target_stream else 0.65
                    self.transition_weights[tech_id][target] = weight

    def get_technique_info(self, technique_id: str) -> Dict[str, Any]:
        """Returns metadata for a given MITRE ATT&CK technique."""
        return self.taxonomy.get(technique_id, {
            "name": "Unknown Technique",
            "tactic": "General Adversary Activity",
            "tactic_id": "TA0000",
            "description": "Unclassified security event telemetry.",
            "stream": "Unknown",
            "category": "unknown",
            "telemetry_indicators": [],
            "co_occurring_techniques": []
        })

    def predict_next_techniques(self, observed_techniques: List[str], top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Collaborative filtering / Graph Query for Predictive Threat Hunting:
        Given an observed chronological sequence of techniques {T_1, T_2, ... T_k},
        computes the highest probability next techniques.
        """
        if not observed_techniques:
            # Default prior: Most common early stage techniques
            return [
                {"technique_id": "T1021.002", "name": self.taxonomy["T1021.002"]["name"], "probability": 0.45, "tactic": self.taxonomy["T1021.002"]["tactic"]},
                {"technique_id": "T1550.002", "name": self.taxonomy["T1550.002"]["name"], "probability": 0.35, "tactic": self.taxonomy["T1550.002"]["tactic"]},
                {"technique_id": "T1047", "name": self.taxonomy["T1047"]["name"], "probability": 0.20, "tactic": self.taxonomy["T1047"]["tactic"]}
            ][:top_k]

        score_map: Dict[str, float] = {}
        decay_factor = 1.0
        
        # Traverse observed techniques in reverse chronological order with temporal decay
        for tech in reversed(observed_techniques):
            if tech in self.transition_weights:
                for nxt, weight in self.transition_weights[tech].items():
                    if nxt not in observed_techniques: # Forecast future steps not yet observed
                        score_map[nxt] = score_map.get(nxt, 0.0) + (weight * decay_factor)
            decay_factor *= 0.75

        if not score_map:
            # Fallback if all transitions exhausted or unmapped
            for tech in ["T1490", "T1486", "T1071.001"]:
                if tech not in observed_techniques and tech in self.taxonomy:
                    score_map[tech] = 0.50

        # Normalize probabilities
        total = sum(score_map.values()) if score_map else 1.0
        sorted_preds = sorted(score_map.items(), key=lambda x: x[1], reverse=True)
        
        results = []
        for tid, raw_score in sorted_preds[:top_k]:
            meta = self.get_technique_info(tid)
            prob = round(float(raw_score / max(1e-5, total)), 4)
            results.append({
                "technique_id": tid,
                "name": meta["name"],
                "probability": prob,
                "tactic": meta["tactic"],
                "stream": meta["stream"],
                "description": meta["description"]
            })
        return results
