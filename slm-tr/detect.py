"""
Lateral Movement Detection & Threat Hunter CLI
Unified entrypoint supporting both v1 (Single Entry) and v2 (Sliding Window) variants,
powered by the centralized Reasoning Engine and MITRE ATT&CK Knowledge Base.
"""

import os
import sys
import json
import argparse
import time
from collections import deque
from colorama import init, Fore, Style
import numpy as np

from reasoning.engine import ReasoningEngine
from v1_single_entry.data_loader import format_single_event_text
from v2_sliding_window.data_loader import format_sliding_window_text

init(autoreset=True)

def print_banner():
    print(Fore.CYAN + "=" * 80)
    print(Fore.CYAN + "       [+] SLM SECURITY OPERATIONS: LATERAL MOVEMENT DETECTOR (EDR CLI) [+]       ")
    print(Fore.CYAN + "=" * 80)

def run_realtime_soc_simulation(engine, get_prediction_fn, window_size=3):
    print(Fore.GREEN + f"\n[*] Starting SOC EDR Event Stream Monitor Simulation (Stateful Buffer K={window_size})...")
    print(Fore.GREEN + "[*] Monitoring Active Directory Domain Controller Event Stream...")
    print(Fore.YELLOW + "[i] Press Ctrl+C to terminate the stream.\n")
    time.sleep(1)
    
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
    
    event_buffer = deque(maxlen=window_size)
    
    try:
        idx = 0
        while True:
            evt = mock_events[idx % len(mock_events)]
            idx += 1
            event_buffer.append(evt)
            
            cmd = evt.get('CommandLine', evt.get('PipeName', evt.get('TargetObject', '')))
            image = evt.get('Image', '')
            
            print(Fore.WHITE + f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] 📥 Ingesting Sysmon Event ID {evt['EventID']} from {evt['Computer']} (Buffer size: {len(event_buffer)})...")
            time.sleep(0.6)
            
            pred_id, pred_name, formatted_window = get_prediction_fn(list(event_buffer))
            report = engine.generate_detailed_reasoning(cmd=cmd, image=image, classification=pred_id, context_text=formatted_window)
            
            if pred_id == 0:
                print(Fore.GREEN + f"  [+] Status: Normal Activity")
                print(Fore.GREEN + f"      Trigger: Event ID {evt['EventID']} | {cmd or image}")
            elif pred_id == 1:
                print(Fore.RED + f"  [CRITICAL THREAT] LATERAL MOVEMENT DETECTED (EoRS)")
                print(Fore.RED + f"      Subtype:   {report['subtype_name']}")
                print(Fore.RED + f"      Technique: {report['mitre_technique']}")
                print(Fore.YELLOW + f"      Reasoning: {report['reasoning']}")
            else:
                print(Fore.LIGHTRED_EX + f"  [CRITICAL THREAT] CREDENTIAL EXPLOITATION DETECTED (EoHT)")
                print(Fore.LIGHTRED_EX + f"      Subtype:   {report['subtype_name']}")
                print(Fore.LIGHTRED_EX + f"      Technique: {report['mitre_technique']}")
                print(Fore.YELLOW + f"      Reasoning: {report['reasoning']}")
                
            time.sleep(2.5)
    except KeyboardInterrupt:
        print(Fore.CYAN + "\n[*] EDR Log Stream simulation stopped.")

def main():
    print_banner()
    
    parser = argparse.ArgumentParser(description="Lateral Movement CLI Threat Hunter")
    parser.add_argument("--variant", type=str, choices=["v1", "v2"], default="v2", help="Variant mode: 'v1' (single entry) or 'v2' (sliding window)")
    parser.add_argument("--interactive", action="store_true", default=False, help="Run interactive evaluator")
    parser.add_argument("--simulate", action="store_true", default=False, help="Simulate SOC EDR feed")
    parser.add_argument("--cmd", type=str, default="", help="Single command to analyze")
    parser.add_argument("--image", type=str, default="", help="Image path to analyze")
    parser.add_argument("--window_size", type=int, default=3, help="Sliding window buffer size (default: 3 for v2, 1 for v1)")
    parser.add_argument("--max_length", type=int, default=256, help="Max token length")
    args = parser.parse_args()
    
    if args.variant == "v1":
        args.window_size = 1
        
    engine = ReasoningEngine()
    
    variant_suffix = "v1_single_entry" if args.variant == "v1" else "v2_sliding_window"
    candidate_paths = [
        f"models/deberta-lateral-movement-{variant_suffix}",
        f"models/deberta-lateral-movement-{args.variant}",
        "models/deberta-lateral-movement",
        "models/deberta-lateral-movement-v2_sliding_window",
        "models/deberta-lateral-movement-v1_single_entry"
    ]
    classifier_path = next((p for p in candidate_paths if os.path.exists(p)), candidate_paths[0])
    has_model = os.path.exists(classifier_path)
    
    tokenizer = None
    model = None
    
    if has_model:
        print(Fore.GREEN + f"[+] Fine-tuned Classifier detected at: {classifier_path}")
        try:
            from transformers import AutoTokenizer, AutoModelForSequenceClassification
            tokenizer = AutoTokenizer.from_pretrained(classifier_path)
            model = AutoModelForSequenceClassification.from_pretrained(classifier_path)
            model.eval()
            print(Fore.GREEN + "[+] Model successfully loaded!")
        except Exception as e:
            print(Fore.YELLOW + f"[!] Failed to load model: {e}. Using Reasoning Engine.")
    else:
        print(Fore.YELLOW + "[i] Local model checkpoint not found. Using central Reasoning Engine.")
        
    def get_prediction_window(events_list):
        if len(events_list) <= 1:
            formatted_text = format_single_event_text(events_list[0])
        else:
            formatted_text = format_sliding_window_text(events_list)
            
        last_event = events_list[-1]
        cmd = last_event.get('CommandLine', last_event.get('PipeName', ''))
        image = last_event.get('Image', '')
        
        if model and tokenizer:
            try:
                import torch
                inputs = tokenizer(formatted_text, return_tensors="pt", truncation=True, max_length=args.max_length)
                with torch.no_grad():
                    outputs = model(**inputs)
                logits = outputs.logits.numpy()[0]
                pred_id = int(np.argmax(logits))
                classes = ["Normal", "EoRS (Exploitation of Remote Services)", "EoHT (Exploitation of Hashing Techniques)"]
                return pred_id, classes[pred_id], formatted_text
            except Exception:
                pred_id, pred_name = engine.predict_class(cmd, image, context_text=formatted_text)
                return pred_id, pred_name, formatted_text
        else:
            pred_id, pred_name = engine.predict_class(cmd, image, context_text=formatted_text)
            return pred_id, pred_name, formatted_text

    if args.simulate:
        run_realtime_soc_simulation(engine, get_prediction_window, window_size=args.window_size)
        return
        
    if args.cmd:
        event = {"EventID": 1, "Image": args.image, "CommandLine": args.cmd}
        pred_id, pred_name, formatted = get_prediction_window([event])
        report = engine.generate_detailed_reasoning(cmd=args.cmd, image=args.image, classification=pred_id, context_text=formatted)
        
        print("\n" + "=" * 20 + f" THREAT ANALYSIS REPORT ({args.variant.upper()}) " + "=" * 20)
        print(f"Input Command:   {args.cmd}")
        print(f"Input Image:     {args.image}")
        print(f"Status:          " + (Fore.GREEN + "NORMAL" if pred_id == 0 else Fore.RED + "MALICIOUS / THREAT"))
        print(f"Predicted Class: {pred_name}")
        print(f"Subtype:         {report['subtype_name']}")
        print(f"MITRE ATT&CK:    {report['mitre_technique']}")
        print(f"Rationale:\n{report['reasoning']}")
        print("=" * 64)
        return

    if args.interactive:
        print(Fore.GREEN + f"\n[*] Starting Interactive Threat Triage ({args.variant.upper()}, Window K={args.window_size}).")
        ring_buffer = deque(maxlen=args.window_size)
        try:
            while True:
                cmd = input(Fore.CYAN + "\nCommand Line > ").strip()
                if cmd.lower() == 'exit':
                    break
                if not cmd:
                    continue
                image = input(Fore.CYAN + "Process Image > ").strip()
                event = {"EventID": 1, "Image": image, "CommandLine": cmd}
                ring_buffer.append(event)
                
                pred_id, pred_name, formatted = get_prediction_window(list(ring_buffer))
                report = engine.generate_detailed_reasoning(cmd=cmd, image=image, classification=pred_id, context_text=formatted)
                
                print(Fore.WHITE + "\n" + "-" * 20 + " SLM THREAT REPORT " + "-" * 20)
                if pred_id == 0:
                    print(Fore.GREEN + "Status:          NORMAL")
                else:
                    print(Fore.RED + "Status:          CRITICAL THREAT DETECTED")
                print(f"Subtype:         {report['subtype_name']}")
                print(f"MITRE ATT&CK:    {report['mitre_technique']}")
                print(Fore.LIGHTYELLOW_EX + f"Reasoning:\n{report['reasoning']}")
                print("-" * 59)
        except KeyboardInterrupt:
            print("\n[*] Interactive session ended.")
        return

    parser.print_help()

if __name__ == "__main__":
    main()
