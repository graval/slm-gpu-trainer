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

def format_event_text(row):
    """Format key Sysmon log features into a structured text prompt for the SLM."""
    event_id = str(row.get('EventID', row.get('EventId', '1'))).split('.')[0]
    
    # Textual fields
    cmd = str(row.get('CommandLine', '')).strip()
    parent_cmd = str(row.get('ParentCommandLine', '')).strip()
    image = str(row.get('Image', '')).strip()
    parent_image = str(row.get('ParentImage', '')).strip()
    user = str(row.get('User', row.get('ParentUser', 'SYSTEM'))).strip()
    logon_type = str(row.get('LogonType', '')).strip()
    
    # Avoid printing empty fields
    lines = [f"Event ID: {event_id}"]
    if image and image != 'nan':
        lines.append(f"Image: {image}")
    if cmd and cmd != 'nan':
        lines.append(f"Command Line: {cmd}")
    if parent_image and parent_image != 'nan':
        lines.append(f"Parent Image: {parent_image}")
    if parent_cmd and parent_cmd != 'nan':
        lines.append(f"Parent Command Line: {parent_cmd}")
    if user and user != 'nan':
        lines.append(f"Execution User: {user}")
    if logon_type and logon_type != 'nan' and logon_type != '0' and logon_type != '':
        lines.append(f"Logon Type: {logon_type}")
        
    return "\n".join(lines)

def load_lmd_dataset(csv_path, balance_classes=True, test_size=0.2, random_state=42):
    """
    Loads LMD-2023 CSV file, cleans it, performs class-balancing,
    and returns train/validation splits.
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"LMD-2023 dataset CSV file not found at: {csv_path}")
        
    print(f"[*] Reading LMD-2023 dataset: {csv_path} ...")
    # Optimize memory usage by reading in chunks if necessary, but start with standard read
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
        # Find count of minority classes
        malicious_1 = df[df['normalized_label'] == 1]
        malicious_2 = df[df['normalized_label'] == 2]
        benign = df[df['normalized_label'] == 0]
        
        min_malicious_count = max(len(malicious_1), len(malicious_2), 1000)
        # Cap benign at twice the sum of malicious classes or at least 5000
        target_benign_count = min(len(benign), max(5000, 2 * (len(malicious_1) + len(malicious_2))))
        
        # Downsample benign
        benign_sampled = benign.sample(n=target_benign_count, random_state=random_state)
        df_balanced = pd.concat([benign_sampled, malicious_1, malicious_2]).sample(frac=1, random_state=random_state)
        df = df_balanced.reset_index(drop=True)
        
        balanced_counts = df['normalized_label'].value_counts()
        print("[*] Balanced class distribution:")
        for cls, count in balanced_counts.items():
            name = "Normal (0)" if cls == 0 else ("EoRS (1)" if cls == 1 else "EoHT (2)")
            print(f"  - {name}: {count:,} ({count/len(df)*100:.2f}%)")
            
    # Formulate inputs and labels
    print("[*] Preprocessing logs into structured text descriptions...")
    df['formatted_text'] = df.apply(format_event_text, axis=1)
    
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

def create_decoder_prompt(row):
    """Formats event text and response for decoder instructions."""
    text = format_event_text(row)
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

    prompt = f"<|im_start|>user\nAnalyze this Windows security log for potential lateral movement activity:\n\n{text}\n\nOutput a structured JSON analysis report.<|im_end|>\n<|im_start|>assistant\n"
    
    response = f'{{\n  "lateral_movement": {is_lm},\n  "class": "{category}",\n  "mitre_technique": "{tech}",\n  "reasoning": "{reason}"\n}}<|im_end|>'
    
    return {"prompt": prompt, "completion": response, "text": prompt + response}

def load_lmd_for_decoder(csv_path, balance_classes=True, test_size=0.1, random_state=42):
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
        
        # Sampling balanced dataset
        target_benign_count = min(len(benign), max(2000, 2 * (len(malicious_1) + len(malicious_2))))
        benign_sampled = benign.sample(n=target_benign_count, random_state=random_state)
        df = pd.concat([benign_sampled, malicious_1, malicious_2]).sample(frac=1, random_state=random_state).reset_index(drop=True)
        
    # Convert rows to prompts
    prompts_list = [create_decoder_prompt(row) for _, row in df.iterrows()]
    prompts_df = pd.DataFrame(prompts_list)
    
    train_df, val_df = train_test_split(prompts_df, test_size=test_size, random_state=random_state)
    
    train_dataset = Dataset.from_pandas(train_df.reset_index(drop=True))
    val_dataset = Dataset.from_pandas(val_df.reset_index(drop=True))
    
    return train_dataset, val_dataset
