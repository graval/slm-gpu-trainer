"""
MITRE ATT&CK Knowledge Base for Lateral Movement Detection (LMD)
Maps security events, tools, process arguments, and network indicators
to specific MITRE ATT&CK techniques, tactics, and sub-techniques.
"""

MITRE_TECHNIQUES = {
    # -------------------------------------------------------------
    # Exploitation of Remote Services (EoRS) / Lateral Movement
    # -------------------------------------------------------------
    "T1021.002": {
        "name": "Remote Services: SMB/Windows Admin Shares",
        "tactic": "Lateral Movement (TA0008)",
        "description": "Adversaries may use SMB and Windows administrative shares (e.g., C$, ADMIN$, IPC$) to remotely interact with target systems and execute commands.",
        "common_tools": ["PsExec", "PaExec", "Net.exe", "Impacket (psexec.py, smbexec.py)"],
        "telemetry_indicators": ["Event ID 1 (psexec.exe / paexec.exe)", "Event ID 17 (Named Pipe \\psexec)", "Event ID 3 (Port 445 SMB)"]
    },
    "T1047": {
        "name": "Windows Management Instrumentation (WMI)",
        "tactic": "Execution (TA0002) / Lateral Movement (TA0008)",
        "description": "Adversaries may abuse WMI to execute malicious commands and scripts remotely over RPC/DCOM on network endpoints.",
        "common_tools": ["wmic.exe", "WmiPrvSE.exe", "Impacket (wmiexec.py)", "Invoke-WmiMethod"],
        "telemetry_indicators": ["wmic.exe process call create /node:", "WmiPrvSE.exe spawning cmd.exe / powershell.exe", "Port 135 RPC traffic"]
    },
    "T1021.006": {
        "name": "Remote Services: Windows Remote Management (WinRM)",
        "tactic": "Lateral Movement (TA0008)",
        "description": "Adversaries may use WinRM and PowerShell Remoting (WinRS / Enter-PSSession) to execute commands across remote hosts.",
        "common_tools": ["winrs.exe", "wsmprovhost.exe", "Invoke-Command", "Enter-PSSession"],
        "telemetry_indicators": ["wsmprovhost.exe parent process", "Port 5985/5986 HTTP/HTTPS traffic", "Invoke-Command -ComputerName"]
    },
    "T1053.005": {
        "name": "Scheduled Task/Job: Scheduled Task",
        "tactic": "Execution (TA0002) / Lateral Movement (TA0008)",
        "description": "Adversaries may abuse task scheduling APIs or schtasks.exe to execute tasks on remote hosts (/s parameter) for lateral movement.",
        "common_tools": ["schtasks.exe", "at.exe"],
        "telemetry_indicators": ["schtasks.exe /create /s <remote_host>", "schtasks.exe /run /s <remote_host>"]
    },
    "T1543.003": {
        "name": "Create or Modify System Process: Windows Service",
        "tactic": "Persistence (TA0003) / Privilege Escalation (TA0004) / Lateral Movement (TA0008)",
        "description": "Adversaries may create or modify Windows services (e.g., via sc.exe) on remote machines to execute payloads as SYSTEM.",
        "common_tools": ["sc.exe", "PSEXESVC.exe"],
        "telemetry_indicators": ["sc.exe \\\\<remote_host> create", "sc.exe \\\\<remote_host> start", "PSEXESVC service creation"]
    },
    "T1570": {
        "name": "Lateral Tool Transfer",
        "tactic": "Lateral Movement (TA0008)",
        "description": "Adversaries may transfer tools or other files between systems in an enterprise network to support lateral movement operations.",
        "common_tools": ["SMB shares", "BITSAdmin", "certutil.exe", "PowerShell WebClient"],
        "telemetry_indicators": ["net.exe use \\\\<ip>\\<share>", "copy / xcopy over administrative shares"]
    },

    # -------------------------------------------------------------
    # Exploitation of Hashing Techniques (EoHT) / Credential Access
    # -------------------------------------------------------------
    "T1550.002": {
        "name": "Use Alternate Authentication Material: Pass the Hash",
        "tactic": "Lateral Movement (TA0008) / Defense Evasion (TA0005)",
        "description": "Adversaries may 'Pass the Hash' using stolen NTLM hashes or Kerberos tickets to authenticate to remote hosts without cracking cleartext passwords.",
        "common_tools": ["Mimikatz (sekurlsa::pth)", "Impacket", "Rubeus", "Pass-the-Ticket"],
        "telemetry_indicators": ["sekurlsa::pth", "LogonType 9 (NewCredentials)", "NTLM hash injection in memory"]
    },
    "T1003.001": {
        "name": "OS Credential Dumping: LSASS Memory",
        "tactic": "Credential Access (TA0006)",
        "description": "Adversaries may dump memory from the Local Security Authority Subsystem Service (LSASS) process to obtain plaintext passwords and hashes.",
        "common_tools": ["comsvcs.dll MiniDump", "procdump.exe", "Mimikatz (sekurlsa::logonpasswords)", "rundll32.exe"],
        "telemetry_indicators": ["rundll32.exe comsvcs.dll, MiniDump / #24", "Event ID 10 handle access to lsass.exe (0x1FFFFF)"]
    },
    "T1003.002": {
        "name": "OS Credential Dumping: Security Account Manager (SAM)",
        "tactic": "Credential Access (TA0006)",
        "description": "Adversaries may export or extract the SAM and SYSTEM registry hives to extract local account password hashes offline.",
        "common_tools": ["reg.exe save HKLM\\SAM", "reg.exe save HKLM\\SYSTEM", "vssadmin"],
        "telemetry_indicators": ["reg.exe save HKLM\\SAM", "reg.exe save HKLM\\SECURITY"]
    },
    "T1558": {
        "name": "Steal or Forge Kerberos Tickets",
        "tactic": "Credential Access (TA0006) / Lateral Movement (TA0008)",
        "description": "Adversaries may forge Kerberos tickets (Golden Ticket, Silver Ticket, Kerberoasting) to traverse Active Directory domain trusts.",
        "common_tools": ["Rubeus", "Mimikatz (kerberos::golden)", "Invoke-Kerberoast"],
        "telemetry_indicators": ["RC4 Kerberos ticket requests", "Kerberos ticket injection into sessions"]
    }
}

def get_technique_details(technique_id):
    """Retrieve detailed metadata for a given MITRE ATT&CK technique."""
    return MITRE_TECHNIQUES.get(technique_id, {
        "name": "Unknown / Generic Technique",
        "tactic": "Lateral Movement / Credential Access",
        "description": "Adversary behavior matching lateral movement or privilege escalation telemetry.",
        "common_tools": [],
        "telemetry_indicators": []
    })
