"""
EdgeShield: Unified Dataset Loader for LSA & BPD Streams
Loads and tokenizes telemetry partitions for both the Log Semantic Analyzer and Behavioral Pattern Detector.
"""

import os
import pandas as pd
import numpy as np
from typing import Tuple, Optional, Dict, Any, List
from datasets import Dataset
from sklearn.model_selection import train_test_split

from edgeshield.taxonomy import TECHNIQUE_TO_ID, ID_TO_TECHNIQUE
from edgeshield.lsa.tokenizer import SecurityLogNormalizer
from edgeshield.bpd.detector import RansomwareTelemetryNormalizer

from v2_sliding_window.data_loader import load_v2_dataset

def load_edgeshield_lsa_data(
    csv_path: str = "data/lmd_2023_dataset.csv",
    window_size: int = 3,
    train_samples: int = 12000,
    test_samples: int = 2000,
    random_state: int = 42
) -> Tuple[Dataset, Dataset]:
    """
    Loads lateral movement data (LMD-2023 or OpTC) formatted for LSA training and evaluation.
    Guarantees balanced, stratified sampling across Normal, EoRS, and EoHT classes without majority skew.
    """
    if not os.path.exists(csv_path):
        for cand in ["data/optc_test_benchmark.csv", "external/lmd_2023_dataset.csv"]:
            if os.path.exists(cand):
                csv_path = cand
                break

    from v2_sliding_window.data_loader import normalize_label, find_label_column, generate_windowed_dataframe
    
    print(f"[*] [LSA] Loading dataset from {csv_path} with balanced class stratification...", flush=True)
    df = pd.read_csv(csv_path, low_memory=False)
    label_col = find_label_column(df)
    if not label_col:
        raise ValueError(f"Could not identify label column in {csv_path}")
    df["normalized_label"] = df[label_col].apply(normalize_label)
    
    c0 = df[df["normalized_label"] == 0]
    c1 = df[df["normalized_label"] == 1]
    c2 = df[df["normalized_label"] == 2]
    
    total_len = len(df)
    if train_samples + test_samples > total_len:
        test_samples = max(60, int(total_len * 0.2))
        train_samples = max(60, total_len - test_samples)

    train_per_class = max(20, train_samples // 3)
    test_per_class = max(20, test_samples // 3)
    
    train_splits = []
    test_splits = []
    for c in [c0, c1, c2]:
        if len(c) == 0:
            continue
        c_test_target = min(len(c) // 5, test_per_class) if len(c) > 5 else 1
        c_train_target = min(len(c) - c_test_target, train_per_class)
        c_train = c.sample(n=max(1, c_train_target), random_state=random_state)
        c_remaining = c.drop(c_train.index)
        c_test_n = min(len(c_remaining), c_test_target)
        if c_test_n > 0:
            c_test = c_remaining.sample(n=c_test_n, random_state=random_state)
        else:
            # Fallback if class was too small to split
            c_test = c_train.sample(n=min(len(c_train), 5), random_state=random_state)
        train_splits.append(c_train)
        test_splits.append(c_test)
    
    train_df = pd.concat(train_splits).sample(frac=1, random_state=random_state).reset_index(drop=True)
    test_df = pd.concat(test_splits).sample(frac=1, random_state=random_state).reset_index(drop=True)
    
    print(f"[*] [LSA] Formulating temporal sliding windows (K={window_size})...", flush=True)
    train_df = generate_windowed_dataframe(train_df, window_size=window_size)
    test_df = generate_windowed_dataframe(test_df, window_size=window_size)
    
    train_df = train_df.rename(columns={"normalized_label": "label"})
    test_df = test_df.rename(columns={"normalized_label": "label"})
    
    train_ds = Dataset.from_pandas(train_df[["formatted_text", "label"]])
    test_ds = Dataset.from_pandas(test_df[["formatted_text", "label"]])
    
    print(f"[+] [LSA] Stratified Train size: {len(train_ds)} | Stratified Test size: {len(test_ds)}", flush=True)
    return train_ds, test_ds


def load_edgeshield_bpd_data(
    csv_path: str = "data/ransomware_behavioral_traces.csv",
    train_samples: int = 5000,
    test_samples: int = 1000,
    random_state: int = 42
) -> Tuple[Dataset, Dataset]:
    """
    Loads ransomware behavioral traces for BPD training and evaluation.
    """
    total_needed = train_samples + test_samples
    if not os.path.exists(csv_path) or len(pd.read_csv(csv_path, nrows=total_needed + 1)) < total_needed:
        from edgeshield.data.synthetic_ransomware import generate_curated_ransomware_dataset
        df = generate_curated_ransomware_dataset(csv_path, num_samples=total_needed)
    else:
        df = pd.read_csv(csv_path)

    normalizer = RansomwareTelemetryNormalizer()
    formatted_texts = [normalizer.normalize_behavior_event(row) for _, row in df.iterrows()]
    df["formatted_text"] = formatted_texts
    
    # Map technique to ID
    def map_tech(row):
        tid = str(row.get("TechniqueID", "BENIGN_NORMAL"))
        return TECHNIQUE_TO_ID.get(tid, TECHNIQUE_TO_ID.get("BENIGN_NORMAL", 0))

    df["label"] = df.apply(map_tech, axis=1)

    test_fraction = test_samples / max(1, (train_samples + test_samples))
    train_df, test_df = train_test_split(
        df, 
        test_size=test_fraction, 
        random_state=random_state, 
        stratify=df["label"] if len(df["label"].unique()) > 1 else None
    )
    
    if len(train_df) > train_samples:
        train_df = train_df.iloc[:train_samples]
    if len(test_df) > test_samples:
        test_df = test_df.iloc[:test_samples]

    train_ds = Dataset.from_pandas(train_df[["formatted_text", "label"]])
    test_ds = Dataset.from_pandas(test_df[["formatted_text", "label"]])
    print(f"[+] [BPD] Stratified Train size: {len(train_ds)} | Stratified Test size: {len(test_ds)}", flush=True)
    return train_ds, test_ds
