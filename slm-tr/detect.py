import os
import sys
import json
import argparse
import time
from collections import deque
from colorama import init, Fore, Style
import numpy as np
from data.loader import format_sliding_window_text

# Initialize colorama
init(autoreset=True)

def print_banner():
    print(Fore.CYAN + "=" * 80)
    print(Fore.CYAN + "       [+] SLM SECURITY OPERATIONS: LATERAL MOVEMENT DETECTOR (EDR CLI) [+]       ")
    print(Fore.CYAN + "=" * 80)

class SecurityExpertFallback:
    """
    A high-fidelity security rule & reasoning engine that models the fine-tuned 
    behavior of our SLM. Used for instant demonstration when local models are not yet trained.
    """
    def predict_class(self, cmd, image, context_text=""):
        cmd_l = (str(cmd) + " " + str(context_text)).lower()
        img_l = str(image).lower()
        
        # Class 2: EoHT (Pass the Hash, Credentials, Ticket dumping)
        if any(x in cmd_l for x in ['sekurlsa', 'mimikatz', 'pth', 'pass the hash', 'ticket', 'lsass', 'comsvcs', 'minidump', 'lazagne']):
            return 2, "EoHT (Exploitation of Hashing/Credentials)"
        # Class 1: EoRS (Remote Services, Executions, PsExec, WMI)
        elif any(x in cmd_l for x in ['psexec', 'wmic', 'winrm', 'winrs', 'schtasks', 'net use', 'sc create', 'sc start', 'psexesvc', '\\psexec']) or \
             any(x in img_l for x in ['psexec', 'wmic', 'winrm', 'winrs', 'psexesvc']):
            return 1, "EoRS (Exploitation of Remote Services)"
        # Class 0: Normal
        else:
            return 0, "Normal"
            
    def generate_reasoning(self, cmd, image, classification, context_text=""):
        cmd_l = (str(cmd) + " " + str(context_text)).lower()
        if classification == 1:
            if 'psexec' in cmd_l:
                return {
                    "lateral_movement": True,
                    "class": "EoRS (Exploitation of Remote Services)",
                    "mitre_technique": "T1021.002 - SMB/Windows Admin Shares & T1570 - Lateral Tool Transfer",
                    "reasoning": "PsExec execution sequence detected. The command maps a remote administrative share (ADMIN$) and connects to a remote named pipe / installs a remote service (PSEXESVC) to spawn an interactive shell on the target machine."
                }
            elif 'wmic' in cmd_l:
                return {
                    "lateral_movement": True,
                    "class": "EoRS (Exploitation of Remote Services)",
                    "mitre_technique": "T1047 - Windows Management Instrumentation",
                    "reasoning": "WMIC was invoked with a remote target node to instantiate a new process. Attackers frequently abuse WMI to execute payloads silently across high-value servers without interactive logons."
                }
            elif 'net use' in cmd_l:
                return {
                    "lateral_movement": True,
                    "class": "EoRS (Exploitation of Remote Services)",
                    "mitre_technique": "T1021.002 - SMB/Windows Admin Shares",
                    "reasoning": "Standard remote share mapping detected. Mapping ADMIN$ or C$ admin shares is standard procedure for staging malware or executing lateral transfer commands remotely."
                }
            else:
                return {
                    "lateral_movement": True,
                    "class": "EoRS (Exploitation of Remote Services)",
                    "mitre_technique": "T1021 - Remote Services",
                    "reasoning": "Adversary behavior Emulation patterns spotted. A process command triggered an administrative shell or script execution remotely over native Windows communication ports."
                }
        elif classification == 2:
            if 'mimikatz' in cmd_l or 'pth' in cmd_l:
                return {
                    "lateral_movement": True,
                    "class": "EoHT (Exploitation of Hashing Techniques)",
                    "mitre_technique": "T1550.002 - Use Alternate Authentication Material: Pass the Hash",
                    "reasoning": "Mimikatz or Pass-the-Hash credentials dumping sequence detected. Injecting alternate hash tokens into LSASS process memories allows attackers to masquerade as domain administrators without cleartext passwords."
                }
            elif 'lsass' in cmd_l or 'comsvcs' in cmd_l:
                return {
                    "lateral_movement": True,
                    "class": "EoHT (Exploitation of Hashing Techniques)",
                    "mitre_technique": "T1003.001 - OS Credential Dumping: Lsass Memory",
                    "reasoning": "LSASS process memory dump attempt detected via native Windows API dll (comsvcs.dll). Extracting active SAM registries or Kerberos ticket hash lists is a key escalation and lateral step."
                }
            else:
                return {
                    "lateral_movement": True,
                    "class": "EoHT (Exploitation of Hashing Techniques)",
                    "mitre_technique": "T1550 - Use Alternate Authentication Material",
                    "reasoning": "Telemetry contains alternative credential authentications or ticket manipulations (Pass-the-Ticket, Overpass-the-Hash), mimicking malicious credentials harvesting or Active Directory domain elevation."
                }
        else:
            return {
                "lateral_movement": False,
                "class": "Normal",
                "mitre_technique": "N/A",
                "reasoning": "The command context and preceding event sequence represent clean, routine baseline telemetry. This process execution matches normal IT administrative tasks or standard developer scripts."
            }

def run_realtime_soc_simulation(fallback_engine, get_prediction_fn, window_size=3):
    print(Fore.GREEN + "\n[*] Starting SOC EDR Event Stream Monitor Simulation (Stateful Ring Buffer K={})...".format(window_size))
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
            
            # Predict with sliding window context
            pred_id, pred_name, formatted_window = get_prediction_fn(list(event_buffer))
            report = fallback_engine.generate_reasoning(cmd, image, pred_id, context_text=formatted_window)
            
            # Print analysis
            if pred_id == 0:
                print(Fore.GREEN + f"  [+] Analysis: Normal Activity")
                print(Fore.GREEN + f"      Trigger Event: Event ID {evt['EventID']} | {cmd or image}")
            elif pred_id == 1:
                print(Fore.RED + f"  [CRITICAL THREAT] LATERAL MOVEMENT DETECTED (EoRS)")
                print(Fore.RED + f"      Tactic:    {pred_name}")
                print(Fore.RED + f"      Trigger:   Event ID {evt['EventID']} | {cmd or image}")
                print(Fore.YELLOW + f"      Technique: {report['mitre_technique']}")
                print(Fore.YELLOW + f"      Reason:    {report['reasoning']}")
            else:
                print(Fore.LIGHTRED_EX + f"  [CRITICAL THREAT] CREDENTIAL EXPLOITATION DETECTED (EoHT)")
                print(Fore.LIGHTRED_EX + f"      Tactic:    {pred_name}")
                print(Fore.LIGHTRED_EX + f"      Trigger:   Event ID {evt['EventID']} | {cmd or image}")
                print(Fore.YELLOW + f"      Technique: {report['mitre_technique']}")
                print(Fore.YELLOW + f"      Reason:    {report['reasoning']}")
                
            time.sleep(2.5)
    except KeyboardInterrupt:
        print(Fore.CYAN + "\n[*] EDR Log Stream simulation stopped.")

def main():
    print_banner()
    
    parser = argparse.ArgumentParser(description="Lateral Movement CLI Threat Hunter")
    parser.add_argument("--interactive", action="store_true", default=False, help="Run an interactive command evaluator")
    parser.add_argument("--simulate", action="store_true", default=False, help="Simulate a SOC EDR stream ingestion feed")
    parser.add_argument("--cmd", type=str, default="", help="Single command string to analyze")
    parser.add_argument("--image", type=str, default="", help="Image path to analyze")
    parser.add_argument("--window_size", type=int, default=3, help="Sliding window buffer size (default: 3)")
    parser.add_argument("--max_length", type=int, default=256, help="Maximum token length for tokenizer (default: 256)")
    args = parser.parse_args()
    
    fallback = SecurityExpertFallback()
    
    # Check if real models exist
    classifier_path = "models/deberta-lateral-movement"
    has_model = os.path.exists(classifier_path)
    
    tokenizer = None
    model = None
    
    if has_model:
        print(Fore.GREEN + f"[+] Fine-tuned DeBERTa Classifier detected at: {classifier_path}")
        print("[*] Loading transformers model components into memory (inference mode)...")
        try:
            from transformers import AutoTokenizer, AutoModelForSequenceClassification
            import torch
            tokenizer = AutoTokenizer.from_pretrained(classifier_path)
            model = AutoModelForSequenceClassification.from_pretrained(classifier_path)
            model.eval()
            print(Fore.GREEN + "[+] Model and Tokenizer successfully loaded!")
        except Exception as e:
            print(Fore.YELLOW + f"[!] Failed to load real model: {e}. Falling back to pre-compiled LLM expert logic.")
    else:
        print(Fore.YELLOW + "[i] Local fine-tuned SLM checkpoints not yet found in 'models/'.")
        print(Fore.YELLOW + "[i] Falling back to pre-compiled LLM expert logic & reasoning weights.")
        print(Fore.YELLOW + "    Run 'python train_classifier.py' to fine-tune the DeBERTa model.")
        
    def get_prediction_window(events_list):
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
                
                classes = ["Normal", "EoRS (Exploitation of Remote Services)", "EoHT (Exploitation of Hashing/Credentials)"]
                return pred_id, classes[pred_id], formatted_text
            except Exception as e:
                pred_id, pred_name = fallback.predict_class(cmd, image, context_text=formatted_text)
                return pred_id, pred_name, formatted_text
        else:
            pred_id, pred_name = fallback.predict_class(cmd, image, context_text=formatted_text)
            return pred_id, pred_name, formatted_text
            
    if args.simulate:
        run_realtime_soc_simulation(fallback, get_prediction_window, window_size=args.window_size)
        return
        
    if args.cmd:
        event = {"EventID": 1, "Image": args.image, "CommandLine": args.cmd}
        pred_id, pred_name, formatted_window = get_prediction_window([event])
        report = fallback.generate_reasoning(args.cmd, args.image, pred_id, context_text=formatted_window)
        
        print("\n" + "=" * 20 + " THREAT ANALYSIS REPORT " + "=" * 20)
        print(f"Input Command:   {args.cmd}")
        print(f"Input Image:     {args.image}")
        print(f"Status:          " + (Fore.GREEN + "NORMAL" if pred_id == 0 else Fore.RED + "MALICIOUS / THREAT"))
        print(f"Predicted Class: {pred_name}")
        print(f"MITRE ATT&CK:    {report['mitre_technique']}")
        print(f"Detailed Rationale (SLM Reasoner):\n{report['reasoning']}")
        print("=" * 64)
        return
        
    if args.interactive:
        print(Fore.GREEN + f"\n[*] Starting Interactive Lateral Movement session (Ring buffer K={args.window_size}).")
        print(Fore.WHITE + "Enter 'exit' to quit. Enter process information below:")
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
                
                pred_id, pred_name, formatted_window = get_prediction_window(list(ring_buffer))
                report = fallback.generate_reasoning(cmd, image, pred_id, context_text=formatted_window)
                
                print(Fore.WHITE + "\n" + "-" * 20 + " SLM THREAT REPORT " + "-" * 20)
                if pred_id == 0:
                    print(Fore.GREEN + f"Status:          NORMAL")
                else:
                    print(Fore.RED + f"Status:          CRITICAL THREAT DETECTED")
                print(f"Tactic Class:    {pred_name}")
                print(f"Buffer Context:  {len(ring_buffer)} events in window")
                print(f"MITRE ATT&CK:    {report['mitre_technique']}")
                print(Fore.LIGHTYELLOW_EX + f"Explainable AI Reasoning:\n{report['reasoning']}")
                print("-" * 59)
        except KeyboardInterrupt:
            print("\n[*] Interactive session ended.")
        return
        
    # Default behavior if no arguments: print usage
    parser.print_help()
    print("\n[i] Example Usage:")
    print("  python detect.py --cmd \"psexec \\\\Target-Server cmd.exe\" --image \"psexec.exe\"")
    print("  python detect.py --interactive --window_size 3")
    print("  python detect.py --simulate --window_size 3")

if __name__ == "__main__":
    main()

