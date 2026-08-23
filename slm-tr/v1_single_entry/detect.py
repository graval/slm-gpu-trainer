"""
v1 - Single Entry CLI Triage & Detector
Inspects isolated single Sysmon event log entries and performs instantaneous LMD classification
and detailed MITRE ATT&CK reasoning triage.
"""

import os
import sys
import json
import argparse
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from colorama import init, Fore, Style
from v1_single_entry.data_loader import format_single_event_text
from reasoning.engine import ReasoningEngine

init(autoreset=True)

def print_banner():
    print(Fore.CYAN + "=" * 80)
    print(Fore.CYAN + "   [+] v1 - SINGLE ENTRY LATERAL MOVEMENT DETECTOR (CLI TRIAGE) [+]   ")
    print(Fore.CYAN + "=" * 80)

def main():
    print_banner()
    engine = ReasoningEngine()
    
    sample_single_events = [
        {"EventID": 1, "Image": "C:\\Windows\\System32\\cmd.exe", "CommandLine": "psexec.exe \\\\CORP-SRV04 -u CORP\\Administrator cmd.exe", "User": "CORP\\jdoe-admin", "Computer": "CORP-WKSTN32"},
        {"EventID": 1, "Image": "C:\\Windows\\System32\\wmic.exe", "CommandLine": "wmic /node:\"CORP-SQL01\" process call create \"C:\\Windows\\Temp\\beacon.exe\"", "User": "CORP\\jdoe-admin", "Computer": "CORP-WKSTN32"},
        {"EventID": 1, "Image": "C:\\Windows\\System32\\rundll32.exe", "CommandLine": "rundll32.exe C:\\windows\\System32\\comsvcs.dll, MiniDump 624 C:\\Windows\\Temp\\lsass.dmp full", "User": "NT AUTHORITY\\SYSTEM", "Computer": "CORP-SQL01"},
        {"EventID": 1, "Image": "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe", "CommandLine": "chrome.exe --type=renderer", "User": "CORP\\jdoe", "Computer": "CORP-WKSTN32"},
        {"EventID": 1, "Image": "C:\\Windows\\System32\\ipconfig.exe", "CommandLine": "ipconfig /flushdns", "User": "CORP\\jdoe", "Computer": "CORP-WKSTN32"}
    ]
    
    print(Fore.WHITE + f"[*] Loaded {len(sample_single_events)} test single-log records for triage.\n")
    
    for idx, evt in enumerate(sample_single_events, 1):
        cmd = evt.get('CommandLine', '')
        image = evt.get('Image', '')
        formatted = format_single_event_text(evt)
        
        pred_label, class_name = engine.predict_class(cmd=cmd, image=image)
        report = engine.generate_detailed_reasoning(cmd=cmd, image=image, classification=pred_label, context_text=formatted)
        
        print(Fore.WHITE + f"--- [Event #{idx}] {image} ---")
        if pred_label == 0:
            print(Fore.GREEN + f"  [+] Status: NORMAL")
            print(Fore.GREEN + f"      Command: {cmd}")
            print(Fore.GREEN + f"      Rationale: {report['reasoning']}")
        elif pred_label == 1:
            print(Fore.RED + f"  [!] THREAT DETECTED: LATERAL MOVEMENT (EoRS)")
            print(Fore.RED + f"      Subtype:   {report['subtype_name']}")
            print(Fore.RED + f"      Technique: {report['mitre_technique']}")
            print(Fore.YELLOW + f"      Rationale: {report['reasoning']}")
        else:
            print(Fore.LIGHTRED_EX + f"  [!] THREAT DETECTED: CREDENTIAL DUMPING / PTH (EoHT)")
            print(Fore.LIGHTRED_EX + f"      Subtype:   {report['subtype_name']}")
            print(Fore.LIGHTRED_EX + f"      Technique: {report['mitre_technique']}")
            print(Fore.YELLOW + f"      Rationale: {report['reasoning']}")
        print()

if __name__ == "__main__":
    main()
