import os
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from datasets import Dataset

def find_label_column(df):
    """Dynamically search for the label column in the dataframe."""
    possible_columns = ['label', 'class', 'traffic_type', 'type', 'target', 'category', 'attack_type', 'lbl']
    for col in df.columns:
        if col.lower() in possible_columns:
            return col
    # Fallback to checking if any column contains 'Normal' or 'EoRS' or 'EoHT'
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

def format_event_text(row, step_prefix=""):
    """Format key Sysmon log features into a structured text prompt for the SLM."""
    event_id = str(row.get('EventID', row.get('EventId', '1'))).split('.')[0]
    
    # Textual fields
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
    
    # Avoid printing empty or placeholder fields
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
    Example:
      [Event T-2] Event ID: 3 | Network: 192.168.1.50 -> 192.168.1.10:445
      [Event T-1] Event ID: 17 | Pipe Name: \\psexec
      [Target Event T_0] Event ID: 1 | Image: PSEXESVC.exe | CommandLine: ...
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
    
    print(f"[*] Building temporal sliding window sequences (K={window_size} events per sample)...")
    formatted_texts = []
    # Pre-extract rows as list of dicts for fast iteration
    records = df.to_dict('records')
    total = len(records)
    
    for i in range(total):
        start_idx = max(0, i - window_size + 1)
        window = records[start_idx : i + 1]
        formatted_texts.append(format_sliding_window_text(window))
        
    df['formatted_text'] = formatted_texts
    return df

def load_lmd_dataset(csv_path, window_size=1, balance_classes=True, test_size=0.2, random_state=42):
    """
    Loads LMD-2023 CSV file, cleans it, applies temporal sliding window,
    performs class-balancing, and returns train/validation splits.
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"LMD-2023 dataset CSV file not found at: {csv_path}")
        
    print(f"[*] Reading LMD-2023 dataset: {csv_path} ...")
    df = pd.read_csv(csv_path, low_memory=False)
    print(f"[+] Loaded {len(df):,} events successfully.")
    
    # Locate label column
    label_col = find_label_column(df)
    if not label_col:
        raise ValueError("[!] Could not automatically identify the label column in the CSV.")
    print(f"[*] Identified label column: '{label_col}'")
    
    # Normalize labels
    df['normalized_label'] = df[label_col].apply(normalize_label)
    
    # Count original classes
    class_counts = df['normalized_label'].value_counts()
    print("[*] Original class distribution:")
    for cls, count in class_counts.items():
        name = "Normal (0)" if cls == 0 else ("EoRS (1)" if cls == 1 else "EoHT (2)")
        print(f"  - {name}: {count:,} ({count/len(df)*100:.2f}%)")
        
    # Class Balancing (Crucial for LMD-2023 which has ~92% normal logs)
    if balance_classes:
        print("[*] Applying downsampling to balance classes (normal vs. malicious)...")
        malicious_1 = df[df['normalized_label'] == 1]
        malicious_2 = df[df['normalized_label'] == 2]
        benign = df[df['normalized_label'] == 0]
        
        target_benign_count = min(len(benign), max(5000, 2 * (len(malicious_1) + len(malicious_2))))
        benign_sampled = benign.sample(n=target_benign_count, random_state=random_state)
        df_balanced = pd.concat([benign_sampled, malicious_1, malicious_2]).sort_index()
        df = df_balanced.reset_index(drop=True)
        
        balanced_counts = df['normalized_label'].value_counts()
        print("[*] Balanced class distribution:")
        for cls, count in balanced_counts.items():
            name = "Normal (0)" if cls == 0 else ("EoRS (1)" if cls == 1 else "EoHT (2)")
            print(f"  - {name}: {count:,} ({count/len(df)*100:.2f}%)")
            
    # Formulate sliding window text representations
    print(f"[*] Preprocessing logs into structured text descriptions (Window Size={window_size})...")
    df = generate_windowed_dataframe(df, window_size=window_size)
    
    # Split into train/validation sets
    train_df, val_df = train_test_split(
        df[['formatted_text', 'normalized_label']], 
        test_size=test_size, 
        stratify=df['normalized_label'],
        random_state=random_state
    )
    
    # Convert to Hugging Face datasets
    train_dataset = Dataset.from_pandas(train_df.reset_index(drop=True))
    val_dataset = Dataset.from_pandas(val_df.reset_index(drop=True))
    
    return train_dataset, val_dataset

def create_decoder_prompt(row, text=None):
    """Formats event text and response for decoder instructions."""
    if text is None:
        text = row.get('formatted_text', format_event_text(row))
    label = row['normalized_label']
    
    if label == 1:
        is_lm = "true"
        category = "EoRS (Exploitation of Remote Services)"
        tech = "T1021.002 - Remote Services: SMB/Windows Admin Shares or T1047 - WMI"
        reason = "A command or remote service execution (such as PsExec, WMIC, or WinRM) was triggered on a network asset, characteristic of lateral movement."
    elif label == 2:
        is_lm = "true"
        category = "EoHT (Exploitation of Hashing Techniques)"
        tech = "T1550.002 - Use Alternate Authentication Material: Pass the Hash"
        reason = "The telemetry reveals logon activities or credential mapping leveraging alternate hashing materials (Pass-the-Hash, Pass-the-Ticket, or ticket manipulation)."
    else:
        is_lm = "false"
        category = "Normal"
        tech = "N/A"
        reason = "The command execution and system telemetry correspond to standard background services, system administrative actions, or benign local user operations."

    prompt = f"<|im_start|>user\nAnalyze this Windows security telemetry sequence for potential lateral movement activity:\n\n{text}\n\nOutput a structured JSON analysis report.<|im_end|>\n<|im_start|>assistant\n"
    
    response = f'{{\n  "lateral_movement": {is_lm},\n  "class": "{category}",\n  "mitre_technique": "{tech}",\n  "reasoning": "{reason}"\n}}<|im_end|>'
    
    return {"prompt": prompt, "completion": response, "text": prompt + response}

def load_lmd_for_decoder(csv_path, window_size=1, balance_classes=True, test_size=0.1, random_state=42):
    """Loads LMD-2023 CSV and formats it into instructional prompts for Decoder LoRA training."""
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"LMD-2023 dataset CSV file not found at: {csv_path}")
        
    df = pd.read_csv(csv_path, low_memory=False)
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
    
    # Convert rows to prompts
    prompts_list = [create_decoder_prompt(row, text=row['formatted_text']) for _, row in df.iterrows()]
    prompts_df = pd.DataFrame(prompts_list)
    
    train_df, val_df = train_test_split(prompts_df, test_size=test_size, random_state=random_state)
    
    train_dataset = Dataset.from_pandas(train_df.reset_index(drop=True))
    val_dataset = Dataset.from_pandas(val_df.reset_index(drop=True))
    
    return train_dataset, val_dataset

