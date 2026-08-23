"""
v2 - Sliding Window Data Loader
Processes Windows Sysmon event logs using temporal multi-event sliding windows (K=3..5 events).
Preserves chronological event sequences:
  [Event T-2] ...
  [Event T-1] ...
  [Target Event T_0] ...
"""

import os
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from datasets import Dataset
from reasoning.prompt_builder import create_decoder_sample

def find_label_column(df):
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
    if pd.isna(label):
        return 0
    label_str = str(label).strip().lower()
    if 'eors' in label_str or 'remote service' in label_str or 'exploitation_of_remote_services' in label_str or label_str == '1':
        return 1
    elif 'eoht' in label_str or 'hash' in label_str or 'credential' in label_str or 'exploitation_of_hashing_techniques' in label_str or label_str == '2':
        return 2
    else:
        return 0

def format_event_text(row, step_prefix=""):
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
    
    header = f"{step_prefix}Event ID: {event_id}".strip()
    lines = [header]
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

def format_sliding_window_text(window_rows):
    """
    Combines a list of consecutive event rows into a single multi-event temporal context.
    """
    if len(window_rows) == 1:
        return format_event_text(window_rows[0])
    
    k = len(window_rows)
    formatted_events = []
    for idx, row in enumerate(window_rows):
        if idx == k - 1:
            prefix = "[Target Event T_0] "
        else:
            offset = (k - 1) - idx
            prefix = f"[Event T-{offset}] "
        formatted_events.append(format_event_text(row, step_prefix=prefix))
        
    return "\n---\n".join(formatted_events)

def generate_windowed_dataframe(df, window_size=3):
    """Generates sliding window formatted text for dataframe rows."""
    if window_size <= 1:
        df['formatted_text'] = df.apply(format_event_text, axis=1)
        return df
    
    records = df.to_dict('records')
    total = len(records)
    formatted_texts = []
    
    for i in range(total):
        start_idx = max(0, i - window_size + 1)
        window = records[start_idx : i + 1]
        formatted_texts.append(format_sliding_window_text(window))
        
    df['formatted_text'] = formatted_texts
    return df

def resolve_dataset_path(csv_path):
    """
    Robustly resolves a dataset CSV file path across local folders (data/, external/, scratch/)
    and absolute paths inside Docker or host systems. Supports comma-separated paths.
    """
    if "," in str(csv_path):
        resolved = [resolve_dataset_path(p.strip()) for p in str(csv_path).split(",") if p.strip()]
        return ",".join(resolved)

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

def load_v2_dataset(csv_path, window_size=3, balance_classes=True, test_size=0.2, random_state=42):
    """
    Loads dataset CSV(s), applies temporal sliding window (K=window_size),
    and returns Hugging Face train/validation datasets.
    Supports single path, list of paths, or comma-separated paths.
    """
    if isinstance(csv_path, (list, tuple)):
        paths = csv_path
    elif "," in str(csv_path):
        paths = [p.strip() for p in str(csv_path).split(",") if p.strip()]
    else:
        paths = [csv_path]
        
    dfs = []
    for p in paths:
        resolved_path = resolve_dataset_path(p)
        if not os.path.exists(resolved_path):
            raise FileNotFoundError(f"Dataset CSV file not found at: {p} (resolved search: {resolved_path})")
            
        print(f"[*] [v2 - Sliding Window] Loading dataset: {resolved_path} (Window K={window_size})...")
        df_part = pd.read_csv(resolved_path, low_memory=False)
        print(f"[+] Loaded {len(df_part):,} events from {os.path.basename(resolved_path)}.")
        
        label_col = find_label_column(df_part)
        if not label_col:
            raise ValueError(f"[!] Could not automatically identify label column in {resolved_path}.")
        df_part['normalized_label'] = df_part[label_col].apply(normalize_label)
        dfs.append(df_part)
        
    df = pd.concat(dfs, ignore_index=True)
    print(f"[+] Total combined dataset size: {len(df):,} events across {len(paths)} source(s).")
    
    if balance_classes:
        malicious_1 = df[df['normalized_label'] == 1]
        malicious_2 = df[df['normalized_label'] == 2]
        benign = df[df['normalized_label'] == 0]
        
        target_benign_count = min(len(benign), max(5000, 2 * (len(malicious_1) + len(malicious_2))))
        benign_sampled = benign.sample(n=target_benign_count, random_state=random_state)
        df = pd.concat([benign_sampled, malicious_1, malicious_2]).sort_index().reset_index(drop=True)
        
    print(f"[*] [v2] Formulating temporal sliding window sequences (K={window_size})...")
    df = generate_windowed_dataframe(df, window_size=window_size)
    
    train_df, val_df = train_test_split(
        df[['formatted_text', 'normalized_label']], 
        test_size=test_size, 
        stratify=df['normalized_label'],
        random_state=random_state
    )
    
    train_dataset = Dataset.from_pandas(train_df.reset_index(drop=True))
    val_dataset = Dataset.from_pandas(val_df.reset_index(drop=True))
    
    return train_dataset, val_dataset

def load_v2_for_decoder(csv_path, window_size=3, balance_classes=True, test_size=0.1, random_state=42):
    """
    Loads dataset and formats multi-event sequences into instruction prompts for decoder training.
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
        
    df = generate_windowed_dataframe(df, window_size=window_size)
    
    prompts_list = [
        create_decoder_sample(
            row_or_text=row['formatted_text'],
            label=row['normalized_label'],
            variant_tag="v2_sliding_window",
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
