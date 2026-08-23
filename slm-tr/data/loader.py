"""
Unified Data Loader for Lateral Movement Detection (LMD)
Provides unified interfaces for loading and preprocessing datasets across both
v1 (Single Entry) and v2 (Sliding Window), powered by the central Reasoning Engine.
"""

import os
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from datasets import Dataset

from reasoning.engine import ReasoningEngine
from reasoning.prompt_builder import create_decoder_sample, build_instruction_prompt, build_completion_response
from v1_single_entry.data_loader import format_single_event_text, load_v1_dataset, load_v1_for_decoder
from v2_sliding_window.data_loader import format_event_text, format_sliding_window_text, generate_windowed_dataframe, load_v2_dataset, load_v2_for_decoder

_engine = ReasoningEngine()

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

def load_lmd_dataset(csv_path, window_size=1, balance_classes=True, test_size=0.2, random_state=42):
    """
    Unified dataset loader delegating to v1 (when window_size=1) or v2 (when window_size > 1).
    """
    if window_size <= 1:
        return load_v1_dataset(csv_path, balance_classes=balance_classes, test_size=test_size, random_state=random_state)
    else:
        return load_v2_dataset(csv_path, window_size=window_size, balance_classes=balance_classes, test_size=test_size, random_state=random_state)

def create_decoder_prompt(row, text=None, window_size=1):
    """
    Formats event text and response using the unified reasoning engine.
    """
    if text is None:
        text = row.get('formatted_text', format_event_text(row))
    label = row.get('normalized_label', 0)
    variant_tag = "v1_single_entry" if window_size <= 1 else "v2_sliding_window"
    
    return create_decoder_sample(
        row_or_text=text,
        label=label,
        variant_tag=variant_tag,
        cmd=str(row.get('CommandLine', '')),
        image=str(row.get('Image', ''))
    )

def load_lmd_for_decoder(csv_path, window_size=1, balance_classes=True, test_size=0.1, random_state=42):
    """
    Unified decoder dataset loader delegating to v1 or v2 instruction tuning pipelines.
    """
    if window_size <= 1:
        return load_v1_for_decoder(csv_path, balance_classes=balance_classes, test_size=test_size, random_state=random_state)
    else:
        return load_v2_for_decoder(csv_path, window_size=window_size, balance_classes=balance_classes, test_size=test_size, random_state=random_state)
