# Specification: Central Reasoning Engine & Subtype Taxonomy

## 1. Objective & Scope
The `reasoning/` package is the centralized, standalone knowledge and reasoning core of the framework. It is decoupled from both `v1` and `v2` architectures so that:
1. Subtype heuristics, detection rules, and MITRE ATT&CK techniques are defined in **exactly one place**.
2. Both ML models (generative reasoners) and heuristic fallback evaluators share consistent taxonomy and security rationale.
3. Future updates to MITRE mappings or detection patterns apply immediately across both paradigms.

---

## 2. Attack Subtype Taxonomy & MITRE ATT&CK Mapping

| Subtype Key | Subtype Name | MITRE Technique | Threat Class | Key Indicators / Patterns |
| :--- | :--- | :--- | :--- | :--- |
| `PSEXEC_REMOTE_SERVICE` | PsExec Remote Service Execution | `T1021.002` (SMB/Windows Admin Shares) | 1 (EoRS) | `psexec`, `PSEXESVC`, `paexec`, `remcom`, named pipe `\psexec`, IPC$ |
| `WMI_REMOTE_EXEC` | WMI Remote Process Creation | `T1047` (Windows Management Instrumentation) | 1 (EoRS) | `wmic` `/node:`, `process call create`, `wmic.exe`, `wmiprvse.exe` |
| `WINRM_REMOTING` | WinRM / PowerShell Remoting | `T1021.006` (Windows Remote Management) | 1 (EoRS) | `Enter-PSSession`, `Invoke-Command`, `winrs.exe`, Port `5985`/`5986` |
| `REMOTE_SCHEDULED_TASK` | Remote Scheduled Task Scheduling | `T1053.005` (Scheduled Task) | 1 (EoRS) | `schtasks` `/create` `/s `, `at.exe`, `taskhostw.exe` |
| `SMB_ADMIN_SHARE_MAPPING`| SMB Admin Share Traversal | `T1021.002` (SMB Shares) | 1 (EoRS) | `net use` `\\*\ADMIN$`, `C$`, `IPC$`, `net.exe` |
| `MIMIKATZ_PTH` | Pass-the-Hash (PtH) Token Injection | `T1550.002` (Pass the Hash) | 2 (EoHT) | `sekurlsa::pth`, `mimikatz`, `sekurlsa`, `token::elevate` |
| `LSASS_MEMORY_DUMP` | LSASS Process Memory Dump | `T1003.001` (OS Credential Dumping: LSASS) | 2 (EoHT) | `comsvcs.dll` `MiniDump`, `procdump` `lsass`, `rundll32` |
| `SAM_REGISTRY_DUMP` | SAM / SYSTEM Registry Hive Dump | `T1003.002` (Security Account Manager) | 2 (EoHT) | `reg save` `HKLM\SAM`, `HKLM\SYSTEM`, `secretsdump` |
| `KERBEROS_FORGERY` | Kerberos Ticket Forgery / Abuse | `T1558` (Steal/Forge Kerberos Tickets) | 2 (EoHT) | `kerberos::golden`, `kerberos::silver`, `rubeus`, `asktgt` |
| `BENIGN_ADMIN_ACTIVITY` | Legitimate Administrative Activity | `None` | 0 (Normal) | Standard admin utilities without remote lateral flags |
| `BENIGN_USER_ACTIVITY` | Routine Benign Endpoint Activity | `None` | 0 (Normal) | Browsers, Office, developer tools (`git`, `node`, `python`) |

---

## 3. Module Interface (`reasoning/engine.py`)

### Core Class: `ReasoningEngine`
```python
from reasoning.engine import ReasoningEngine

engine = ReasoningEngine()

# 1. Class prediction from command & context:
class_id, class_name = engine.predict_class(cmd="psexec.exe \\\\SRV01 cmd.exe", image="cmd.exe")
# Returns: (1, "EoRS (Exploitation of Remote Services)")

# 2. Detailed technical report & MITRE mapping:
report = engine.generate_detailed_reasoning(
    cmd="psexec.exe \\\\SRV01 cmd.exe",
    image="cmd.exe",
    classification=1,
    context_text="[Single Event] Event ID: 1 ..."
)
# Returns structured dict:
# {
#     "classification": 1,
#     "class_name": "EoRS",
#     "is_lateral_movement": True,
#     "subtype": "PSEXEC_REMOTE_SERVICE",
#     "subtype_name": "PsExec Remote Service Execution",
#     "mitre_technique": "T1021.002 (SMB/Windows Admin Shares)",
#     "reasoning": "Observed execution of PsExec remote administration utility..."
# }
```

### Prompt Construction: `reasoning/prompt_builder.py`
Standardizes ChatML instruction format (`<|im_start|>user ... <|im_end|>\n<|im_start|>assistant ... <|im_end|>`) across all generative SLM fine-tuning scripts.
