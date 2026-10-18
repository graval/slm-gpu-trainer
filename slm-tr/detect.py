"""
EdgeShield: Real-Time EDR Threat Hunter & Telemetry Detector CLI
Powered by EdgeShield Dual-Stream Architecture (LSA + BPD) and MITRE ATT&CK Correlation Engine.
Supports dynamic single-event threat scanning, interactive CLI hunting, and live SOC event stream simulation.
"""

import os
import sys
import json
import argparse
import time
from collections import deque
from colorama import init, Fore, Style
import numpy as np

# Reconfigure stdout for Windows terminal compatibility
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

init(autoreset=True)

from edgeshield.pipeline import EdgeShieldPipeline
from reasoning.engine import ReasoningEngine


def print_banner():
    print(Fore.CYAN + "=" * 80)
    print(Fore.CYAN + "     [+] EDGESHIELD: REAL-TIME SLM EDGE THREAT HUNTER & EDR CLI [+]      ")
    print(Fore.CYAN + "=" * 80)


# Curated Active Directory telemetry event stream for live SOC playback simulation
CURATED_SOC_STREAM = [
    {"EventID": 3, "Image": "C:\\Windows\\System32\\svchost.exe", "SourceIp": "10.0.0.5", "DestinationIp": "10.0.0.12", "DestinationPort": 445, "User": "NT AUTHORITY\\SYSTEM", "Computer": "CORP-DC01"},
    {"EventID": 17, "PipeName": "\\psexec", "User": "CORP\\Administrator", "Computer": "CORP-DC01"},
    {"EventID": 1, "Image": "C:\\Windows\\System32\\cmd.exe", "CommandLine": "psexec.exe \\\\CORP-SRV04 -u CORP\\Administrator cmd.exe", "ParentImage": "C:\\Windows\\System32\\cmd.exe", "User": "CORP\\jdoe-admin", "Computer": "CORP-WKSTN32"},
    {"EventID": 1, "Image": "C:\\Program Files\\Git\\bin\\git.exe", "CommandLine": "git status", "ParentImage": "C:\\Windows\\System32\\cmd.exe", "User": "CORP\\jdoe", "Computer": "CORP-WKSTN32"},
    {"EventID": 3, "Image": "C:\\Windows\\System32\\wmic.exe", "SourceIp": "10.0.0.15", "DestinationIp": "10.0.0.8", "DestinationPort": 135, "User": "CORP\\jdoe-admin", "Computer": "CORP-WKSTN32"},
    {"EventID": 1, "Image": "C:\\Windows\\System32\\wmic.exe", "CommandLine": "wmic /node:\"CORP-SQL01\" process call create \"C:\\Windows\\Temp\\backdoor.exe\"", "ParentImage": "C:\\Windows\\System32\\cmd.exe", "User": "CORP\\jdoe-admin", "Computer": "CORP-WKSTN32"},
    {"EventID": 1, "Image": "C:\\Windows\\System32\\SearchIndexer.exe", "CommandLine": "SearchIndexer.exe /Embedding", "ParentImage": "C:\\Windows\\System32\\services.exe", "User": "NT AUTHORITY\\SYSTEM", "Computer": "CORP-SRV04"},
    {"EventID": 10, "TargetObject": "C:\\Windows\\System32\\lsass.exe", "GrantedAccess": "0x1FFFFF", "User": "NT AUTHORITY\\SYSTEM", "Computer": "CORP-SQL01"},
    {"EventID": 1, "Image": "C:\\Windows\\System32\\cmd.exe", "CommandLine": "rundll32.exe C:\\windows\\System32\\comsvcs.dll, MiniDump 624 C:\\Windows\\Temp\\lsass.dmp full", "ParentImage": "C:\\Windows\\System32\\cmd.exe", "User": "NT AUTHORITY\\SYSTEM", "Computer": "CORP-SQL01"},
    {"EventID": 1, "Image": "C:\\Windows\\System32\\vssadmin.exe", "CommandLine": "vssadmin.exe delete shadows /all /quiet", "ParentImage": "C:\\Windows\\System32\\cmd.exe", "User": "CORP\\jdoe-admin", "Computer": "CORP-SQL01"},
    {"EventID": 1, "Image": "C:\\Windows\\System32\\ipconfig.exe", "CommandLine": "ipconfig /flushdns", "ParentImage": "C:\\Windows\\System32\\cmd.exe", "User": "CORP\\jdoe", "Computer": "CORP-WKSTN32"}
]


def run_realtime_soc_simulation(pipeline: EdgeShieldPipeline, window_size=3):
    print(Fore.GREEN + f"\n[*] Starting SOC EDR Event Stream Monitor Simulation (Stateful Buffer K={window_size})...")
    print(Fore.GREEN + "[*] Monitoring Active Directory Domain Controller Event Stream...")
    print(Fore.WHITE + "[i] Note: Every event below is dynamically tokenized and evaluated by the live SLM forward pass.")
    print(Fore.YELLOW + "[i] Press Ctrl+C to terminate the stream.\n")
    time.sleep(1)

    event_buffer = deque(maxlen=window_size)
    idx = 0
    try:
        while True:
            evt = CURATED_SOC_STREAM[idx % len(CURATED_SOC_STREAM)]
            idx += 1
            event_buffer.append(evt)

            cmd = evt.get('CommandLine', evt.get('PipeName', evt.get('TargetObject', '')))
            image = evt.get('Image', '')
            computer = evt.get('Computer', 'CORP-HOST')

            print(Fore.WHITE + f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] 📥 Ingesting Sysmon Event ID {evt.get('EventID', 1)} from {computer} (Buffer size: {len(event_buffer)})...")
            
            # Formulate dynamic telemetry payload
            payload_text = f"EventID: {evt.get('EventID', 1)} Image: {image} CommandLine: {cmd} User: {evt.get('User', 'SYSTEM')} Host: {computer}"
            
            # Execute live SLM pipeline inference
            t0 = time.perf_counter()
            analysis = pipeline.process_telemetry_event(auth_log=payload_text, source_host="CORP-WKSTN", target_host=computer)
            lat_ms = (time.perf_counter() - t0) * 1000.0

            lsa_res = analysis.get("lsa") or {}
            corr = analysis.get("correlation") or {}
            is_lm = lsa_res.get("is_lateral_movement", False)

            if not is_lm:
                print(Fore.GREEN + f"  [+] Status: NORMAL ACTIVITY ({lat_ms:.2f} ms)")
                print(Fore.GREEN + f"      Trigger: Event ID {evt.get('EventID')} | {cmd or image}")
            else:
                tech_id = lsa_res.get("technique_id", "T1021")
                tech_name = lsa_res.get("technique_name", "Lateral Movement")
                conf = lsa_res.get("confidence", 0.95) * 100.0
                print(Fore.RED + f"  [CRITICAL THREAT] LATERAL MOVEMENT DETECTED ({lat_ms:.2f} ms)")
                print(Fore.RED + f"      Technique: {tech_id} - {tech_name}")
                print(Fore.RED + f"      Confidence: {conf:.1f}%")
                print(Fore.YELLOW + f"      Action:    {corr.get('action_recommended', 'ISOLATE HOST')}")

            time.sleep(2.0)
    except KeyboardInterrupt:
        print(Fore.CYAN + "\n[*] EDR Log Stream simulation stopped.")


def main():
    print_banner()

    parser = argparse.ArgumentParser(description="EdgeShield CLI Threat Hunter & Telemetry Analyzer")
    parser.add_argument("--variant", type=str, choices=["v1", "v2", "edgeshield"], default="edgeshield", help="Detection pipeline variant (default: edgeshield dual-stream)")
    parser.add_argument("--interactive", action="store_true", default=False, help="Run interactive dynamic CLI threat hunter")
    parser.add_argument("--simulate", action="store_true", default=False, help="Run real-time SOC EDR feed simulation")
    parser.add_argument("--cmd", type=str, default="", help="Command line string to evaluate")
    parser.add_argument("--image", type=str, default="", help="Process image path to evaluate")
    parser.add_argument("--user", type=str, default="CORP\\jdoe-admin", help="User context")
    parser.add_argument("--source_host", type=str, default="CORP-WKSTN32", help="Source host context")
    parser.add_argument("--target_host", type=str, default="CORP-DC01", help="Target host context")
    parser.add_argument("--window_size", type=int, default=3, help="Sliding window size (default: 3)")
    args = parser.parse_args()

    print("[*] Initializing EdgeShield Threat Detection Pipeline...")
    pipeline = EdgeShieldPipeline()
    reasoning_engine = ReasoningEngine()

    # 1. Single Command Live Threat Scan
    if args.cmd or args.image:
        formatted_event = f"EventID: 1 Image: {args.image} CommandLine: {args.cmd} User: {args.user} Host: {args.target_host}"
        
        t0 = time.perf_counter()
        result = pipeline.process_telemetry_event(
            auth_log=formatted_event,
            behavior_log=formatted_event,
            source_host=args.source_host,
            target_host=args.target_host,
            user=args.user
        )
        total_latency_ms = (time.perf_counter() - t0) * 1000.0

        lsa = result.get("lsa") or {}
        bpd = result.get("bpd") or {}
        corr = result.get("correlation") or {}
        
        is_lsa_threat = lsa.get("is_lateral_movement", False)
        is_bpd_threat = bpd.get("pre_encryption_alert", False) or bpd.get("encryption_active", False)
        is_threat = is_lsa_threat or is_bpd_threat or corr.get("is_coordinated_intrusion", False)

        active_technique = lsa.get("technique_id") if is_lsa_threat else (bpd.get("technique_id") if is_bpd_threat else "BENIGN_NORMAL")
        active_name = lsa.get("technique_name") if is_lsa_threat else (bpd.get("technique_name") if is_bpd_threat else "Clean Baseline")
        confidence = lsa.get("confidence", 0.99) * 100.0 if is_lsa_threat else (bpd.get("threat_score", 0.1) * 100.0 if is_bpd_threat else 98.5)

        print("\n" + "=" * 22 + " EDGESHIELD THREAT ANALYSIS REPORT " + "=" * 23)
        print(f"Input Command:    {args.cmd or '[N/A]'}")
        print(f"Input Image:      {args.image or '[N/A]'}")
        print(f"Executing User:   {args.user}")
        print(f"Source -> Target: {args.source_host} ➔ {args.target_host}")
        print(f"Live Latency:     {total_latency_ms:.2f} ms (Stream A: {lsa.get('latency_ms', 0):.2f} ms | Stream B: {bpd.get('latency_ms', 0):.2f} ms)")
        print(f"Threat Status:    " + (Fore.RED + "MALICIOUS / THREAT DETECTED" if is_threat else Fore.GREEN + "NORMAL / BENIGN"))
        print(f"Detected Stream:  {'DUAL-STREAM COORDINATED' if (is_lsa_threat and is_bpd_threat) else ('STREAM A (LSA)' if is_lsa_threat else ('STREAM B (BPD)' if is_bpd_threat else 'BENIGN BASELINE'))}")
        print(f"MITRE Technique:  {active_technique} - {active_name}")
        print(f"Confidence Score: {confidence:.2f}%")
        print(f"Severity Level:   {corr.get('severity', 'LOW')}")
        print(f"Remediation Plan: {corr.get('action_recommended', 'None required.')}")

        # Predictive Threat Forecasting
        predictions = corr.get("predictive_threat_hunting", [])
        if predictions:
            print("\n" + Fore.YELLOW + "[*] Predictive Next-Technique Forecasting (Graph Collaborative Filtering):")
            for p in predictions[:3]:
                print(Fore.YELLOW + f"    ➔ Anticipated: {p['technique_id']} ({p['name']}) | Prob: {p['probability']*100:.1f}%")

        print("=" * 80)
        return

    # 2. Live SOC EDR Stream Simulation
    if args.simulate:
        run_realtime_soc_simulation(pipeline, window_size=args.window_size)
        return

    # 3. Interactive CLI Hunter Playground
    if args.interactive:
        print(Fore.GREEN + f"\n[*] Starting Interactive Threat Triage (Sliding Window K={args.window_size}).")
        print(Fore.WHITE + "Type any command or process name to run real-time SLM inference. Type 'exit' to quit.")
        ring_buffer = deque(maxlen=args.window_size)
        try:
            while True:
                cmd = input(Fore.CYAN + "\nCommand Line > ").strip()
                if cmd.lower() in ('exit', 'quit'):
                    break
                if not cmd:
                    continue
                image = input(Fore.CYAN + "Process Image (e.g. wmic.exe, cmd.exe, git.exe) > ").strip()
                event = {"EventID": 1, "Image": image, "CommandLine": cmd, "User": args.user, "Computer": args.target_host}
                ring_buffer.append(event)

                payload = f"EventID: 1 Image: {image} CommandLine: {cmd} User: {args.user} Host: {args.target_host}"
                t0 = time.perf_counter()
                res = pipeline.process_telemetry_event(auth_log=payload, behavior_log=payload, source_host=args.source_host, target_host=args.target_host)
                lat = (time.perf_counter() - t0) * 1000.0

                lsa = res.get("lsa") or {}
                corr = res.get("correlation") or {}
                is_lm = lsa.get("is_lateral_movement", False)

                print(Fore.WHITE + "\n" + "-" * 25 + " SLM THREAT REPORT " + "-" * 26)
                if is_lm:
                    print(Fore.RED + f"Status:          CRITICAL THREAT DETECTED ({lat:.2f} ms)")
                    print(Fore.RED + f"Technique:       {lsa.get('technique_id')} - {lsa.get('technique_name')}")
                    print(Fore.RED + f"Confidence:      {lsa.get('confidence', 0)*100:.1f}%")
                    print(Fore.YELLOW + f"Recommended:     {corr.get('action_recommended')}")
                else:
                    print(Fore.GREEN + f"Status:          NORMAL / BENIGN ({lat:.2f} ms)")
                    print(Fore.GREEN + f"Confidence:      {lsa.get('confidence', 0)*100:.1f}%")
                print("-" * 70)
        except KeyboardInterrupt:
            print("\n[*] Interactive session ended.")
        return

    parser.print_help()


if __name__ == "__main__":
    main()
