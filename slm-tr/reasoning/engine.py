"""
Central Reasoning Engine for Lateral Movement Detection (LMD)
Identifies sub-types of LMD attacks, correlates telemetry artifacts,
resolves MITRE ATT&CK techniques, and generates structured analytical explanations.
"""

from typing import Dict, Any, Tuple, Optional
from reasoning.mitre_kb import MITRE_TECHNIQUES, get_technique_details

class ReasoningEngine:
    """
    Expert reasoning engine that analyzes telemetry (single log or windowed sequence),
    classifies lateral movement tactics, extracts subtypes, and compiles structured reports.
    """
    
    # Subtype definitions for granular threat categorization
    SUBTYPES = {
        "PSEXEC_REMOTE_SERVICE": "Remote Service Execution via PsExec/PaExec",
        "WMI_REMOTE_EXEC": "Remote Command Execution via WMI (Windows Management Instrumentation)",
        "WINRM_REMOTING": "PowerShell Remoting / WinRM Remote Execution",
        "REMOTE_SCHEDULED_TASK": "Remote Scheduled Task Creation & Execution",
        "REMOTE_SERVICE_CREATION": "Remote Windows Service Manipulation (sc.exe)",
        "SMB_ADMIN_SHARE_MAPPING": "Administrative File Share Access (ADMIN$ / C$ / IPC$)",
        "MIMIKATZ_PTH": "Pass-the-Hash / NTLM Alternate Credential Authentication",
        "LSASS_MEMORY_DUMP": "LSASS Memory Dump / In-Memory Credential Extraction",
        "SAM_REGISTRY_DUMP": "SAM & SYSTEM Registry Hive Extraction",
        "KERBEROS_FORGERY": "Kerberos Ticket Manipulation (Golden/Silver Ticket, Kerberoasting)",
        "BENIGN_ADMIN_ACTIVITY": "Standard System Administrative Telemetry",
        "BENIGN_USER_ACTIVITY": "Standard User / Endpoint Execution"
    }

    def __init__(self):
        pass

    def identify_subtype(self, cmd: str = "", image: str = "", context_text: str = "") -> Tuple[str, str, str]:
        """
        Extract the specific LMD subtype, primary MITRE Technique ID, and high-level class.
        Returns: (subtype_key, mitre_technique_id, class_name)
        """
        combined_text = f"{str(cmd)} {str(image)} {str(context_text)}".lower()
        
        # 1. Check for Exploitation of Hashing Techniques / Credential Access (EoHT - Class 2)
        if any(x in combined_text for x in ['lsass', 'comsvcs', 'minidump', 'lsass.dmp']):
            return "LSASS_MEMORY_DUMP", "T1003.001", "EoHT (Exploitation of Hashing Techniques)"
        elif any(x in combined_text for x in ['sekurlsa', 'mimikatz', 'pth', 'pass the hash', 'pass-the-hash']):
            return "MIMIKATZ_PTH", "T1550.002", "EoHT (Exploitation of Hashing Techniques)"
        elif any(x in combined_text for x in ['reg.exe save', 'sam.save', 'hklm\\sam', 'hklm\\system', 'hklm\\security']):
            return "SAM_REGISTRY_DUMP", "T1003.002", "EoHT (Exploitation of Hashing Techniques)"
        elif any(x in combined_text for x in ['golden ticket', 'kerberoast', 'rubeus', 'ticket::', 'overpass-the-hash']):
            return "KERBEROS_FORGERY", "T1558", "EoHT (Exploitation of Hashing Techniques)"
        elif any(x in combined_text for x in ['lazagne', 'nanodump', 'procdump']):
            return "LSASS_MEMORY_DUMP", "T1003.001", "EoHT (Exploitation of Hashing Techniques)"

        # 2. Check for Exploitation of Remote Services / Lateral Movement (EoRS - Class 1)
        elif any(x in combined_text for x in ['psexec', 'paexec', 'psexesvc', '\\psexec']):
            return "PSEXEC_REMOTE_SERVICE", "T1021.002", "EoRS (Exploitation of Remote Services)"
        elif any(x in combined_text for x in ['wmic', 'wmiprvse', 'process call create', 'win32_process']):
            return "WMI_REMOTE_EXEC", "T1047", "EoRS (Exploitation of Remote Services)"
        elif any(x in combined_text for x in ['winrm', 'winrs', 'wsmprovhost', 'enter-pssession', 'invoke-command']):
            return "WINRM_REMOTING", "T1021.006", "EoRS (Exploitation of Remote Services)"
        elif any(x in combined_text for x in ['schtasks', 'schtasks.exe /create /s', 'schtasks.exe /run /s']):
            return "REMOTE_SCHEDULED_TASK", "T1053.005", "EoRS (Exploitation of Remote Services)"
        elif any(x in combined_text for x in ['sc.exe \\\\', 'sc create', 'sc start', 'sc config']):
            return "REMOTE_SERVICE_CREATION", "T1543.003", "EoRS (Exploitation of Remote Services)"
        elif any(x in combined_text for x in ['net use', 'admin$', 'c$', 'ipc$']):
            return "SMB_ADMIN_SHARE_MAPPING", "T1021.002", "EoRS (Exploitation of Remote Services)"

        # 3. Benign Baseline (Normal - Class 0)
        else:
            return "BENIGN_USER_ACTIVITY", "N/A", "Normal"

    def predict_class(self, cmd: str = "", image: str = "", context_text: str = "") -> Tuple[int, str]:
        """
        Fast heuristic class prediction (0: Normal, 1: EoRS, 2: EoHT).
        """
        subtype_key, _, class_name = self.identify_subtype(cmd, image, context_text)
        if "EoRS" in class_name:
            return 1, class_name
        elif "EoHT" in class_name:
            return 2, class_name
        else:
            return 0, "Normal"

    def generate_detailed_reasoning(
        self, 
        cmd: str = "", 
        image: str = "", 
        classification: Optional[int] = None, 
        context_text: str = ""
    ) -> Dict[str, Any]:
        """
        Compiles a comprehensive analytical security assessment report.
        """
        subtype_key, mitre_id, class_name = self.identify_subtype(cmd, image, context_text)
        
        # Determine effective label
        if classification is None:
            if "EoRS" in class_name:
                effective_label = 1
            elif "EoHT" in class_name:
                effective_label = 2
            else:
                effective_label = 0
        else:
            effective_label = classification

        # If classification override conflicts with subtype, adjust gracefully
        if effective_label == 0:
            is_lm = False
            reported_class = "Normal"
            mitre_str = "N/A"
            tech_desc = "Clean Baseline"
            reasoning_text = (
                "The command execution and system telemetry correspond to standard background services, "
                "operating system maintenance tasks, or routine benign user activity. No unauthorized "
                "remote executions, share traversals, or credential extractions were observed."
            )
        elif effective_label == 1:
            is_lm = True
            reported_class = "EoRS (Exploitation of Remote Services)"
            tech_info = get_technique_details(mitre_id if mitre_id != "N/A" else "T1021.002")
            mitre_str = f"{mitre_id} - {tech_info['name']}" if mitre_id != "N/A" else "T1021 - Remote Services"
            tech_desc = tech_info['description']
            
            if subtype_key == "PSEXEC_REMOTE_SERVICE":
                reasoning_text = (
                    "PsExec remote execution sequence detected. The process connects across network shares (ADMIN$/IPC$) "
                    "and instantiates a remote execution service (PSEXESVC) to spawn an interactive shell on the target node."
                )
            elif subtype_key == "WMI_REMOTE_EXEC":
                reasoning_text = (
                    "WMIC process call detected targeting a remote node. Adversaries leverage WMI to execute stealthy "
                    "commands remotely without requiring an interactive logon session or leaving local service footprints."
                )
            elif subtype_key == "WINRM_REMOTING":
                reasoning_text = (
                    "WinRM / PowerShell Remoting activity detected. The adversary used remote management protocols "
                    "(wsmprovhost / WinRS) to execute arbitrary commands across network endpoints."
                )
            elif subtype_key == "REMOTE_SCHEDULED_TASK":
                reasoning_text = (
                    "Remote Scheduled Task manipulation observed (/s parameter). Task scheduling is abused to establish "
                    "execution triggers on remote domain machines."
                )
            elif subtype_key == "SMB_ADMIN_SHARE_MAPPING":
                reasoning_text = (
                    "Administrative network share mapping (ADMIN$, C$) detected via net.exe. Share traversal is a standard "
                    "prerequisite for staging remote binaries and staging lateral tool transfers."
                )
            else:
                reasoning_text = (
                    "A remote service invocation or network execution command was triggered across systems, characteristic "
                    "of adversary lateral movement in an Active Directory environment."
                )
        else: # effective_label == 2 (EoHT)
            is_lm = True
            reported_class = "EoHT (Exploitation of Hashing Techniques)"
            tech_info = get_technique_details(mitre_id if mitre_id != "N/A" else "T1550.002")
            mitre_str = f"{mitre_id} - {tech_info['name']}" if mitre_id != "N/A" else "T1550 - Use Alternate Authentication Material"
            tech_desc = tech_info['description']
            
            if subtype_key == "MIMIKATZ_PTH":
                reasoning_text = (
                    "Mimikatz / Pass-the-Hash sequence detected. Injecting alternate NTLM hash tokens into memory enables "
                    "adversaries to impersonate privileged domain accounts without needing cleartext credentials."
                )
            elif subtype_key == "LSASS_MEMORY_DUMP":
                reasoning_text = (
                    "LSASS process memory dump sequence detected (via comsvcs.dll MiniDump or direct handle access). "
                    "Attackers dump lsass.exe to harvest credentials, NTLM password hashes, and Kerberos tickets."
                )
            elif subtype_key == "SAM_REGISTRY_DUMP":
                reasoning_text = (
                    "SAM / SYSTEM registry hive export detected. Exporting registry hives allows attackers to decrypt "
                    "and crack local account hashes offline."
                )
            elif subtype_key == "KERBEROS_FORGERY":
                reasoning_text = (
                    "Kerberos ticket manipulation or forging detected (Golden/Silver Ticket, Kerberoasting), used to "
                    "gain unrestricted domain-wide authorization."
                )
            else:
                reasoning_text = (
                    "Telemetry reveals credential theft or authentication material manipulation (Pass-the-Ticket, "
                    "Overpass-the-Hash, or credential dumping), enabling domain privilege escalation."
                )

        return {
            "lateral_movement": is_lm,
            "class": reported_class,
            "subtype_key": subtype_key,
            "subtype_name": self.SUBTYPES.get(subtype_key, "Generic"),
            "mitre_technique": mitre_str,
            "technique_description": tech_desc,
            "reasoning": reasoning_text
        }
