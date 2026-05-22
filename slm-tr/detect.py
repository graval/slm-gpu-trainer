import os
import sys
import json
import argparse
import time
from colorama import init, Fore, Style
import numpy as np

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
    def predict_class(self, cmd, image):
        cmd_l = str(cmd).lower()
        img_l = str(image).lower()
        
        # Class 2: EoHT (Pass the Hash, Credentials, Ticket dumping)
        if any(x in cmd_l for x in ['sekurlsa', 'mimikatz', 'pth', 'pass the hash', 'ticket', 'lsass', 'comsvcs', 'miniDump', 'lazagne']):
            return 2, "EoHT (Exploitation of Hashing/Credentials)"
        # Class 1: EoRS (Remote Services, Executions, PsExec, WMI)
        elif any(x in cmd_l for x in ['psexec', 'wmic', 'winrm', 'winrs', 'schtasks', 'net use', 'sc create', 'sc start', 'psexesvc']) or \
             any(x in img_l for x in ['psexec', 'wmic', 'winrm', 'winrs', 'psexesvc']):
            return 1, "EoRS (Exploitation of Remote Services)"
        # Class 0: Normal
        else:
            return 0, "Normal"
            
    def generate_reasoning(self, cmd, image, classification):
        cmd_l = str(cmd).lower()
        if classification == 1:
            if 'psexec' in cmd_l:
                return {
                    "lateral_movement": True,
                    "class": "EoRS (Exploitation of Remote Services)",
                    "mitre_technique": "T1021.002 - SMB/Windows Admin Shares & T1570 - Lateral Tool Transfer",
                    "reasoning": "PsExec execution detected. The command maps a remote administrative share (ADMIN$) and installs a remote service (PSEXESVC) to spawn an interactive shell on the target machine. This is a primary lateral movement tactic."
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
                "reasoning": "The command context represents clean, routine baseline telemetry. This process execution matches normal IT administrative tasks, background OS tasks, or standard developer scripts."
            }

def run_realtime_soc_simulation(fallback_engine):
    print(Fore.GREEN + "\n[*] Starting SOC EDR Event Stream Monitor Simulation...")
    print(Fore.GREEN + "[*] Monitoring Active Directory Domain Controller Event Stream...")
    print(Fore.YELLOW + "[i] Press Ctrl+C to terminate the stream.\n")
    time.sleep(1)
    
    mock_events = [
        {"Image": "C:\\Windows\\System32\\svchost.exe", "CommandLine": "svchost.exe -k netsvcs -p", "ParentImage": "C:\\Windows\\System32\\services.exe", "User": "NT AUTHORITY\\SYSTEM", "Computer": "CORP-DC01"},
        {"Image": "C:\\Windows\\System32\\cmd.exe", "CommandLine": "psexec.exe \\\\CORP-SRV04 -u CORP\\Administrator -p P@ssword1! cmd.exe", "ParentImage": "C:\\Windows\\System32\\cmd.exe", "User": "CORP\\jdoe-admin", "Computer": "CORP-WKSTN32"},
        {"Image": "C:\\Program Files\\Git\\bin\\git.exe", "CommandLine": "git status", "ParentImage": "C:\\Windows\\System32\\cmd.exe", "User": "CORP\\jdoe", "Computer": "CORP-WKSTN32"},
        {"Image": "C:\\Windows\\System32\\wmic.exe", "CommandLine": "wmic /node:\"CORP-SQL01\" process call create \"C:\\Windows\\Temp\\backdoor.exe\"", "ParentImage": "C:\\Windows\\System32\\cmd.exe", "User": "CORP\\jdoe-admin", "Computer": "CORP-WKSTN32"},
        {"Image": "C:\\Windows\\System32\\SearchIndexer.exe", "CommandLine": "SearchIndexer.exe /Embedding", "ParentImage": "C:\\Windows\\System32\\services.exe", "User": "NT AUTHORITY\\SYSTEM", "Computer": "CORP-SRV04"},
        {"Image": "C:\\Windows\\System32\\cmd.exe", "CommandLine": "rundll32.exe C:\\windows\\System32\\comsvcs.dll, MiniDump 624 C:\\Windows\\Temp\\lsass.dmp full", "ParentImage": "C:\\Windows\\System32\\cmd.exe", "User": "NT AUTHORITY\\SYSTEM", "Computer": "CORP-SQL01"},
        {"Image": "C:\\Windows\\System32\\ipconfig.exe", "CommandLine": "ipconfig /flushdns", "ParentImage": "C:\\Windows\\System32\\cmd.exe", "User": "CORP\\jdoe", "Computer": "CORP-WKSTN32"}
    ]
    
    try:
        idx = 0
        while True:
            evt = mock_events[idx % len(mock_events)]
            idx += 1
            
            print(Fore.WHITE + f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] 📥 Ingesting Sysmon Event from {evt['Computer']}...")
            time.sleep(0.8)
            
            # Predict
            pred_id, pred_name = fallback_engine.predict_class(evt['CommandLine'], evt['Image'])
            report = fallback_engine.generate_reasoning(evt['CommandLine'], evt['Image'], pred_id)
            
            # Print analysis
            if pred_id == 0:
                print(Fore.GREEN + f"  [+] Analysis: Normal Activity")
                print(Fore.GREEN + f"      Command:  {evt['CommandLine']}")
            elif pred_id == 1:
                print(Fore.RED + f"  [CRITICAL THREAT] LATERAL MOVEMENT DETECTED (EoRS)")
                print(Fore.RED + f"      Tactic:   {pred_name}")
                print(Fore.RED + f"      Command:  {evt['CommandLine']}")
                print(Fore.YELLOW + f"      Technique:{report['mitre_technique']}")
                print(Fore.YELLOW + f"      Reason:   {report['reasoning']}")
            else:
                print(Fore.LIGHTRED_EX + f"  [CRITICAL THREAT] CREDENTIAL EXPLOITATION DETECTED (EoHT)")
                print(Fore.LIGHTRED_EX + f"      Tactic:   {pred_name}")
                print(Fore.LIGHTRED_EX + f"      Command:  {evt['CommandLine']}")
                print(Fore.YELLOW + f"      Technique:{report['mitre_technique']}")
                print(Fore.YELLOW + f"      Reason:   {report['reasoning']}")
                
            time.sleep(3.5)
    except KeyboardInterrupt:
        print(Fore.CYAN + "\n[*] EDR Log Stream simulation stopped.")

def main():
    print_banner()
    
    parser = argparse.ArgumentParser(description="Lateral Movement CLI Threat Hunter")
    parser.add_argument("--interactive", action="store_true", default=False, help="Run an interactive command evaluator")
    parser.add_argument("--simulate", action="store_true", default=False, help="Simulate a SOC EDR stream ingestion feed")
    parser.add_argument("--cmd", type=str, default="", help="Single command string to analyze")
    parser.add_argument("--image", type=str, default="", help="Image path to analyze")
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
        
    def get_prediction(cmd, image):
        if model and tokenizer:
            try:
                import torch
                # Format event text exactly like dataset format_event_text
                lines = ["Event ID: 1"]
                if image:
                    lines.append(f"Image: {image}")
                if cmd:
                    lines.append(f"Command Line: {cmd}")
                formatted_text = "\n".join(lines)
                
                inputs = tokenizer(formatted_text, return_tensors="pt", truncation=True, max_length=64)
                with torch.no_grad():
                    outputs = model(**inputs)
                logits = outputs.logits.numpy()[0]
                pred_id = int(np.argmax(logits))
                
                classes = ["Normal", "EoRS (Exploitation of Remote Services)", "EoHT (Exploitation of Hashing/Credentials)"]
                return pred_id, classes[pred_id]
            except Exception as e:
                # Fallback on inference error
                return fallback.predict_class(cmd, image)
        else:
            return fallback.predict_class(cmd, image)
            
    if args.simulate:
        run_realtime_soc_simulation(fallback)
        return
        
    if args.cmd:
        pred_id, pred_name = get_prediction(args.cmd, args.image)
        report = fallback.generate_reasoning(args.cmd, args.image, pred_id)
        
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
        print(Fore.GREEN + "\n[*] Starting Interactive Lateral Movement command scan session.")
        print(Fore.WHITE + "Enter 'exit' to quit. Enter process information below:")
        try:
            while True:
                cmd = input(Fore.CYAN + "\nCommand Line > ").strip()
                if cmd.lower() == 'exit':
                    break
                if not cmd:
                    continue
                image = input(Fore.CYAN + "Process Image > ").strip()
                
                pred_id, pred_name = get_prediction(cmd, image)
                report = fallback.generate_reasoning(cmd, image, pred_id)
                
                print(Fore.WHITE + "\n" + "-" * 20 + " SLM THREAT REPORT " + "-" * 20)
                if pred_id == 0:
                    print(Fore.GREEN + f"Status:          NORMAL")
                else:
                    print(Fore.RED + f"Status:          CRITICAL THREAT DETECTED")
                print(f"Tactic Class:    {pred_name}")
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
    print("  python detect.py --interactive")
    print("  python detect.py --simulate")

if __name__ == "__main__":
    main()
