"""
v1 - Single Entry Data Loader
Processes Windows Sysmon event logs as isolated single log entries (Window Size K=1).
Formats individual log lines into structured textual representations for classification and generation.
"""

import os
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from datasets import Dataset
from reasoning.prompt_builder import create_decoder_sample

def find_label_column(df):
    """Dynamically search for the label column in the dataframe."""
    possible_columns = ['label', 'class', 'traffic_type', 'type', 'target', 'category', 'attack_type', 'lbl']
    for col in df.columns:
        if col.lower() in possible_columns:
            return col
    for col in df.columns:
        if df[col].dtype == 'object':
            unique_vals = set(df[col].dropna().unique())
            if any(val in unique_vals for val in ['Normal', 'EoRS', 'EoHT', 'Normal traffic']):
                return col
    return None

def normalize_label(label):
    """Normalize labels into integers (0: Normal, 1: EoRS, 2: EoHT)"""
    if pd.isna(label):
        return 0
    label_str = str(label).strip().lower()
    if 'eors' in label_str or 'remote service' in label_str or 'exploitation_of_remote_services' in label_str or label_str == '1':
        return 1
    elif 'eoht' in label_str or 'hash' in label_str or 'credential' in label_str or 'exploitation_of_hashing_techniques' in label_str or label_str == '2':
        return 2
    else:
        return 0

def format_single_event_text(row):
    """
    Format a single Sysmon event log into a structured text prompt for the SLM.
    v1 strictly analyzes this isolated single event without prior temporal history.
    """
    event_id = str(row.get('EventID', row.get('EventId', '1'))).split('.')[0]
    
    cmd = str(row.get('CommandLine', '')).strip()
    parent_cmd = str(row.get('ParentCommandLine', '')).strip()
    image = str(row.get('Image', '')).strip()
    parent_image = str(row.get('ParentImage', '')).strip()
    user = str(row.get('User', row.get('ParentUser', 'SYSTEM'))).strip()
    logon_type = str(row.get('LogonType', '')).strip()
    pipe_name = str(row.get('PipeName', '')).strip()
    src_ip = str(row.get('SourceIp', '')).strip()
    dest_ip = str(row.get('DestinationIp', '')).strip()
    dest_port = str(row.get('DestinationPort', '')).strip()
    target_obj = str(row.get('TargetObject', '')).strip()
    
    lines = [f"[Single Event] Event ID: {event_id}"]
    if image and image not in ('nan', '0', 'None', ''):
        lines.append(f"Image: {image}")
    if cmd and cmd not in ('nan', '0', 'None', ''):
        lines.append(f"Command Line: {cmd}")
    if parent_image and parent_image not in ('nan', '0', 'None', ''):
        lines.append(f"Parent Image: {parent_image}")
    if parent_cmd and parent_cmd not in ('nan', '0', 'None', ''):
        lines.append(f"Parent Command Line: {parent_cmd}")
    if user and user not in ('nan', '0', 'None', ''):
        lines.append(f"Execution User: {user}")
    if logon_type and logon_type not in ('nan', '0', 'None', ''):
        lines.append(f"Logon Type: {logon_type}")
    if pipe_name and pipe_name not in ('nan', '0', 'None', ''):
        lines.append(f"Pipe Name: {pipe_name}")
    if dest_ip and dest_ip not in ('nan', '0', 'None', '', '0.0.0.0') and src_ip not in ('nan', '0', 'None', ''):
        port_str = f":{dest_port}" if dest_port not in ('nan', '0', '0.0', '') else ""
        lines.append(f"Network: {src_ip} -> {dest_ip}{port_str}")
    if target_obj and target_obj not in ('nan', '0', 'None', ''):
        lines.append(f"Target Object: {target_obj}")
        
    return "\n".join(lines)

def resolve_dataset_path(csv_path):
    """
    Robustly resolves a dataset CSV file path across local folders (data/, external/, scratch/)
    and absolute paths inside Docker or host systems.
    """
    if os.path.exists(csv_path):
        return os.path.abspath(csv_path)
        
    base_name = os.path.basename(csv_path)
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    
    candidates = [
        os.path.join(root_dir, csv_path),
        os.path.join(root_dir, "data", base_name),
        os.path.join(root_dir, "external", base_name),
        os.path.join(root_dir, "scratch", base_name),
        os.path.join("data", base_name),
        os.path.join("external", base_name),
        os.path.join("scratch", base_name),
        os.path.join("/app", "external", base_name),
        os.path.join("/app", "data", base_name),
        base_name
    ]
    
    for cand in candidates:
        if os.path.exists(cand):
            return os.path.abspath(cand)
            
    return csv_path

def load_v1_dataset(csv_path, balance_classes=True, test_size=0.2, random_state=42):
    """
    Loads dataset CSV, normalizes labels, formats each line as a single event,
    and returns Hugging Face train/validation datasets for v1.
    """
    resolved_path = resolve_dataset_path(csv_path)
    if not os.path.exists(resolved_path):
        raise FileNotFoundError(f"Dataset CSV file not found at: {csv_path} (resolved search: {resolved_path})")
        
    print(f"[*] [v1 - Single Entry] Loading dataset: {resolved_path} ...")
    df = pd.read_csv(resolved_path, low_memory=False)
    print(f"[+] Loaded {len(df):,} events successfully.")
    
    label_col = find_label_column(df)
    if not label_col:
        raise ValueError("[!] Could not automatically identify the label column in the CSV.")
    df['normalized_label'] = df[label_col].apply(normalize_label)
    
    if balance_classes:
        malicious_1 = df[df['normalized_label'] == 1]
        malicious_2 = df[df['normalized_label'] == 2]
        benign = df[df['normalized_label'] == 0]
        
        target_benign_count = min(len(benign), max(5000, 2 * (len(malicious_1) + len(malicious_2))))
        benign_sampled = benign.sample(n=target_benign_count, random_state=random_state)
        df = pd.concat([benign_sampled, malicious_1, malicious_2]).sort_index().reset_index(drop=True)
        
    print("[*] [v1] Preprocessing logs into single-event text representations...")
    df['formatted_text'] = df.apply(format_single_event_text, axis=1)
    
    train_df, val_df = train_test_split(
        df[['formatted_text', 'normalized_label']], 
        test_size=test_size, 
        stratify=df['normalized_label'],
        random_state=random_state
    )
    
    train_dataset = Dataset.from_pandas(train_df.reset_index(drop=True))
    val_dataset = Dataset.from_pandas(val_df.reset_index(drop=True))
    
    return train_dataset, val_dataset

def load_v1_for_decoder(csv_path, balance_classes=True, test_size=0.1, random_state=42):
    """
    Loads dataset and formats each single-event record into instruction prompts for decoder training.
    """
    resolved_path = resolve_dataset_path(csv_path)
    if not os.path.exists(resolved_path):
        raise FileNotFoundError(f"Dataset CSV file not found at: {csv_path} (resolved search: {resolved_path})")
        
    df = pd.read_csv(resolved_path, low_memory=False)
    label_col = find_label_column(df)
    df['normalized_label'] = df[label_col].apply(normalize_label)
    
    if balance_classes:
        malicious_1 = df[df['normalized_label'] == 1]
        malicious_2 = df[df['normalized_label'] == 2]
        benign = df[df['normalized_label'] == 0]
        
        target_benign_count = min(len(benign), max(2000, 2 * (len(malicious_1) + len(malicious_2))))
        benign_sampled = benign.sample(n=target_benign_count, random_state=random_state)
        df = pd.concat([benign_sampled, malicious_1, malicious_2]).sort_index().reset_index(drop=True)
        
    df['formatted_text'] = df.apply(format_single_event_text, axis=1)
    
    prompts_list = [
        create_decoder_sample(
            row_or_text=row['formatted_text'],
            label=row['normalized_label'],
            variant_tag="v1_single_entry",
            cmd=str(row.get('CommandLine', '')),
            image=str(row.get('Image', ''))
        )
        for _, row in df.iterrows()
    ]
    prompts_df = pd.DataFrame(prompts_list)
    
    train_df, val_df = train_test_split(prompts_df, test_size=test_size, random_state=random_state)
    
    train_dataset = Dataset.from_pandas(train_df.reset_index(drop=True))
    val_dataset = Dataset.from_pandas(val_df.reset_index(drop=True))
    
    return train_dataset, val_dataset
