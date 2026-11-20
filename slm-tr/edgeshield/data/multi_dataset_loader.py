"""
EdgeShield: Multi-Dataset Hierarchical Data Loader
Fuses LMD-2023, Windows-APT 2025/2026 (CALDERA), and Mordor Covenant (LotL)
into a unified Hierarchical Dual-Head training and evaluation partition:
  - Level 1 (Primary): Binary Threat Interception (0: Normal, 1: Attack / Lateral Movement)
  - Level 2 (Auxiliary): TTP Attribution (0: Normal, 1: EoRS, 2: EoHT, 3: LotL/Script, 4: Tool Transfer, 5: Remote Exploit)
"""

import os
import json
import pandas as pd
import numpy as np
from typing import Tuple, Dict, Any, List
from datasets import Dataset
from v2_sliding_window.data_loader import format_sliding_window_text, generate_windowed_dataframe

SUBTYPE_MAP = {
    "NORMAL": 0,
    "EORS": 1,
    "EOHT": 2,
    "LOTL": 3,
    "TOOL_TRANSFER": 4,
    "REMOTE_EXPLOIT": 5
}

def load_hierarchical_multi_dataset(
    lmd_path: str = "data/lmd_2023_dataset.csv",
    windows_apt_dir: str = "data/windows_apt",
    mordor_dir: str = "data",
    window_size: int = 3,
    total_train_samples: int = 15000,
    total_test_samples: int = 3000,
    random_state: int = 42
) -> Tuple[Dataset, Dataset]:
    all_events = []

    # 1. Ingest LMD-2023
    if os.path.exists(lmd_path):
        print(f"[*] Ingesting LMD-2023 from {lmd_path}...")
        df_lmd = pd.read_csv(lmd_path, low_memory=False)
        from v2_sliding_window.data_loader import find_label_column, normalize_label
        lbl_col = find_label_column(df_lmd)
        df_lmd["norm_lbl"] = df_lmd[lbl_col].apply(normalize_label)
        
        # Sample balanced subset from LMD (e.g. 4000 Normal, 4000 EoRS, 4000 EoHT)
        for cls_id, subtype_name in [(0, "NORMAL"), (1, "EORS"), (2, "EOHT")]:
            sub_df = df_lmd[df_lmd["norm_lbl"] == cls_id]
            sample_n = min(len(sub_df), 4000)
            if sample_n > 0:
                sampled = sub_df.sample(n=sample_n, random_state=random_state)
                for _, r in sampled.iterrows():
                    all_events.append({
                        "EventID": str(r.get("EventID", "1")).split(".")[0],
                        "Image": str(r.get("Image", "")),
                        "CommandLine": str(r.get("CommandLine", "")),
                        "ParentImage": str(r.get("ParentImage", "")),
                        "ParentCommandLine": str(r.get("ParentCommandLine", "")),
                        "User": str(r.get("User", "")),
                        "SourceIp": str(r.get("SourceIp", "")),
                        "DestinationIp": str(r.get("DestinationIp", "")),
                        "threat_label": 0 if cls_id == 0 else 1,
                        "subtype_label": SUBTYPE_MAP[subtype_name],
                        "source_dataset": "LMD-2023"
                    })
        print(f"    [+] Ingested {len(all_events)} events from LMD-2023")

    # 2. Ingest Windows-APT 2025/2026 (Mendeley Data v4)
    if os.path.exists(windows_apt_dir):
        print(f"[*] Ingesting Windows-APT scenarios from {windows_apt_dir}...")
        apt_count = 0
        for fn in sorted(os.listdir(windows_apt_dir)):
            if fn.endswith(".csv") and not fn.startswith("scenario_manifest") and not fn.startswith("validation"):
                fp = os.path.join(windows_apt_dir, fn)
                df_apt = pd.read_csv(fp, low_memory=False)
                for _, r in df_apt.iterrows():
                    mitre_id = str(r.get("_source.rule.mitre.id", "")).strip()
                    desc = str(r.get("_source.rule.description", "")).lower()
                    is_attack = (mitre_id not in ("", "nan", "[]"))
                    
                    subtype = SUBTYPE_MAP["NORMAL"]
                    if is_attack:
                        if "t1570" in mitre_id.lower() or "dropped" in desc:
                            subtype = SUBTYPE_MAP["TOOL_TRANSFER"]
                        elif "t1210" in mitre_id.lower() or "printnightmare" in desc:
                            subtype = SUBTYPE_MAP["REMOTE_EXPLOIT"]
                        elif any(k in mitre_id.lower() for k in ["t1059", "t1087", "t1070"]) or "powershell" in desc or "script" in desc:
                            subtype = SUBTYPE_MAP["LOTL"]
                        elif "t1078" in mitre_id.lower() or "logon" in desc:
                            subtype = SUBTYPE_MAP["EOHT"]
                        else:
                            subtype = SUBTYPE_MAP["EORS"]
                            
                    all_events.append({
                        "EventID": str(r.get("_source.data.win.system.eventID", "1")).split(".")[0],
                        "Image": str(r.get("_source.data.win.eventdata.image", "")),
                        "CommandLine": str(r.get("_source.data.win.eventdata.commandLine", "")),
                        "ParentImage": str(r.get("_source.data.win.eventdata.parentImage", "")),
                        "ParentCommandLine": str(r.get("_source.data.win.eventdata.parentCommandLine", "")),
                        "User": str(r.get("_source.data.win.eventdata.user", "")),
                        "SourceIp": str(r.get("_source.data.win.eventdata.ipAddress", "")),
                        "DestinationIp": str(r.get("_source.data.win.eventdata.destinationIp", "")),
                        "threat_label": 1 if is_attack else 0,
                        "subtype_label": subtype,
                        "source_dataset": "Windows-APT"
                    })
                    apt_count += 1
        print(f"    [+] Ingested {apt_count} events from Windows-APT scenarios")

    # 3. Ingest Mordor Covenant (WinRM & WMI)
    for m_fn, sub_type in [("covenant_winrm.json", "EORS"), ("covenant_wmi.json", "LOTL")]:
        mp = os.path.join(mordor_dir, m_fn)
        if os.path.exists(mp):
            print(f"[*] Ingesting Mordor {m_fn}...")
            mordor_count = 0
            with open(mp, "r", encoding="utf-8") as f:
                for line in f:
                    e = json.loads(line)
                    cmd = str(e.get("CommandLine", e.get("ProcessCommandLine", "")))
                    img = str(e.get("Image", e.get("ProcessName", "")))
                    is_attack = any(k in cmd.lower() for k in ["movewmi", "grunt", "wsmprovhost", "powershell", "wmic", "scrcons", "covenant"]) or \
                                any(k in img.lower() for k in ["movewmi", "grunt", "wsmprovhost", "wmic", "scrcons"])
                    all_events.append({
                        "EventID": str(e.get("EventID", "1")).split(".")[0],
                        "Image": img,
                        "CommandLine": cmd,
                        "ParentImage": str(e.get("ParentImage", "")),
                        "ParentCommandLine": "",
                        "User": str(e.get("User", e.get("SubjectUserName", ""))),
                        "SourceIp": str(e.get("SourceIp", "")),
                        "DestinationIp": str(e.get("DestinationIp", "")),
                        "threat_label": 1 if is_attack else 0,
                        "subtype_label": SUBTYPE_MAP[sub_type] if is_attack else SUBTYPE_MAP["NORMAL"],
                        "source_dataset": "Mordor"
                    })
                    mordor_count += 1
            print(f"    [+] Ingested {mordor_count} events from {m_fn}")

    df_all = pd.DataFrame(all_events)
    print(f"\n[+] Total Unified Corpus: {len(df_all)} events across {df_all['source_dataset'].nunique()} datasets")
    print(f"    Threat Breakdown: Attack={sum(df_all['threat_label']==1)} | Normal={sum(df_all['threat_label']==0)}")
    print(f"    Subtype Breakdown:\n{df_all['subtype_label'].value_counts()}")

    # Generate Sliding Windows (K=3)
    print(f"[*] Generating temporal multi-event sliding windows (K={window_size})...")
    windows = []
    threat_labels = []
    subtype_labels = []
    total = len(df_all)

    # Convert dataframe rows to list of dicts for sliding window
    records = df_all.to_dict("records")
    for i in range(total):
        start_idx = max(0, i - window_size + 1)
        win_rows = records[start_idx : i + 1]
        win_text = format_sliding_window_text(win_rows)
        windows.append(win_text)
        threat_labels.append(records[i]["threat_label"])
        subtype_labels.append(records[i]["subtype_label"])

    df_windowed = pd.DataFrame({
        "formatted_text": windows,
        "threat_label": threat_labels,
        "subtype_label": subtype_labels
    })

    # Stratified Train/Test Split on threat_label
    total_needed = total_train_samples + total_test_samples
    if len(df_windowed) > total_needed:
        df_windowed = df_windowed.sample(n=total_needed, random_state=random_state).reset_index(drop=True)

    test_frac = total_test_samples / max(1, len(df_windowed))
    from sklearn.model_selection import train_test_split
    train_df, test_df = train_test_split(
        df_windowed, 
        test_size=test_frac, 
        random_state=random_state, 
        stratify=df_windowed["threat_label"]
    )

    train_ds = Dataset.from_pandas(train_df.reset_index(drop=True))
    test_ds = Dataset.from_pandas(test_df.reset_index(drop=True))
    print(f"[+] Final Train Windows: {len(train_ds)} | Final Test Windows: {len(test_ds)}")
    return train_ds, test_ds
