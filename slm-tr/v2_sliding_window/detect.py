"""
v2 - Sliding Window CLI SOC Stream Monitor & Real-Time EDR Simulator
Maintains a stateful sliding window ring buffer (deque maxlen=K) over an incoming stream
of Sysmon telemetry events, assessing chain-of-events context.
"""

import os
import sys
import json
import argparse
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from collections import deque
from colorama import init, Fore, Style
from v2_sliding_window.data_loader import format_sliding_window_text
from reasoning.engine import ReasoningEngine

init(autoreset=True)

def print_banner():
    print(Fore.CYAN + "=" * 80)
    print(Fore.CYAN + "   [+] v2 - SLIDING WINDOW LATERAL MOVEMENT STREAM DETECTOR (EDR CLI) [+]   ")
    print(Fore.CYAN + "=" * 80)

def main():
    print_banner()
    engine = ReasoningEngine()
    
    mock_events = [
        {"EventID": 3, "Image": "C:\\Windows\\System32\\svchost.exe", "SourceIp": "10.0.0.5", "DestinationIp": "10.0.0.12", "DestinationPort": 445, "User": "NT AUTHORITY\\SYSTEM", "Computer": "CORP-DC01"},
        {"EventID": 17, "PipeName": "\\psexec", "User": "CORP\\Administrator", "Computer": "CORP-DC01"},
        {"EventID": 1, "Image": "C:\\Windows\\System32\\cmd.exe", "CommandLine": "psexec.exe \\\\CORP-SRV04 -u CORP\\Administrator cmd.exe", "ParentImage": "C:\\Windows\\System32\\cmd.exe", "User": "CORP\\jdoe-admin", "Computer": "CORP-WKSTN32"},
        {"EventID": 1, "Image": "C:\\Program Files\\Git\\bin\\git.exe", "CommandLine": "git status", "ParentImage": "C:\\Windows\\System32\\cmd.exe", "User": "CORP\\jdoe", "Computer": "CORP-WKSTN32"},
        {"EventID": 3, "Image": "C:\\Windows\\System32\\wmic.exe", "SourceIp": "10.0.0.15", "DestinationIp": "10.0.0.8", "DestinationPort": 135, "User": "CORP\\jdoe-admin", "Computer": "CORP-WKSTN32"},
        {"EventID": 1, "Image": "C:\\Windows\\System32\\wmic.exe", "CommandLine": "wmic /node:\"CORP-SQL01\" process call create \"C:\\Windows\\Temp\\backdoor.exe\"", "ParentImage": "C:\\Windows\\System32\\cmd.exe", "User": "CORP\\jdoe-admin", "Computer": "CORP-WKSTN32"},
        {"EventID": 1, "Image": "C:\\Windows\\System32\\SearchIndexer.exe", "CommandLine": "SearchIndexer.exe /Embedding", "ParentImage": "C:\\Windows\\System32\\services.exe", "User": "NT AUTHORITY\\SYSTEM", "Computer": "CORP-SRV04"},
        {"EventID": 10, "TargetObject": "C:\\Windows\\System32\\lsass.exe", "GrantedAccess": "0x1FFFFF", "User": "NT AUTHORITY\\SYSTEM", "Computer": "CORP-SQL01"},
        {"EventID": 1, "Image": "C:\\Windows\\System32\\cmd.exe", "CommandLine": "rundll32.exe C:\\windows\\System32\\comsvcs.dll, MiniDump 624 C:\\Windows\\Temp\\lsass.dmp full", "ParentImage": "C:\\Windows\\System32\\cmd.exe", "User": "NT AUTHORITY\\SYSTEM", "Computer": "CORP-SQL01"},
        {"EventID": 1, "Image": "C:\\Windows\\System32\\ipconfig.exe", "CommandLine": "ipconfig /flushdns", "ParentImage": "C:\\Windows\\System32\\cmd.exe", "User": "CORP\\jdoe", "Computer": "CORP-WKSTN32"}
    ]
    
    window_size = 3
    print(Fore.GREEN + f"[*] Initializing SOC EDR Ring Buffer Stream Monitor (Window K={window_size})...")
    print(Fore.YELLOW + "[i] Analyzing event streams for multi-stage Lateral Movement...\n")
    
    event_buffer = deque(maxlen=window_size)
    
    for idx, evt in enumerate(mock_events, 1):
        event_buffer.append(evt)
        cmd = evt.get('CommandLine', evt.get('PipeName', evt.get('TargetObject', '')))
        image = evt.get('Image', '')
        
        print(Fore.WHITE + f"[{time.strftime('%H:%M:%S')}] 📥 Ingesting Sysmon Event ID {evt['EventID']} from {evt['Computer']} (Buffer size: {len(event_buffer)}/{window_size})...")
        time.sleep(0.3)
        
        formatted_window = format_sliding_window_text(list(event_buffer))
        pred_label, class_name = engine.predict_class(cmd=cmd, image=image, context_text=formatted_window)
        report = engine.generate_detailed_reasoning(cmd=cmd, image=image, classification=pred_label, context_text=formatted_window)
        
        if pred_label == 0:
            print(Fore.GREEN + f"  [+] Status: NORMAL")
            print(Fore.GREEN + f"      Trigger: Event ID {evt['EventID']} | {cmd or image}")
        elif pred_label == 1:
            print(Fore.RED + f"  [CRITICAL THREAT] LATERAL MOVEMENT DETECTED (EoRS)")
            print(Fore.RED + f"      Subtype:   {report['subtype_name']}")
            print(Fore.RED + f"      Technique: {report['mitre_technique']}")
            print(Fore.YELLOW + f"      Reasoning: {report['reasoning']}")
        else:
            print(Fore.LIGHTRED_EX + f"  [CRITICAL THREAT] CREDENTIAL EXPLOITATION / PTH DETECTED (EoHT)")
            print(Fore.LIGHTRED_EX + f"      Subtype:   {report['subtype_name']}")
            print(Fore.LIGHTRED_EX + f"      Technique: {report['mitre_technique']}")
            print(Fore.YELLOW + f"      Reasoning: {report['reasoning']}")
        print()

if __name__ == "__main__":
    main()
