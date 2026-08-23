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
    num_samples: Optional[int] = None,
    test_size: float = 0.2,
    random_state: int = 42
) -> Tuple[Dataset, Dataset]:
    """
    Loads lateral movement data (LMD-2023 or OpTC) formatted for LSA training and evaluation.
    """
    if not os.path.exists(csv_path):
        for cand in ["data/optc_test_benchmark.csv", "external/lmd_2023_dataset.csv"]:
            if os.path.exists(cand):
                csv_path = cand
                break

    train_ds, test_ds = load_v2_dataset(csv_path, window_size=window_size, balance_classes=True, test_size=test_size, random_state=random_state)
    
    # Rename column normalized_label to label if needed
    if "normalized_label" in train_ds.column_names:
        train_ds = train_ds.rename_column("normalized_label", "label")
    if "normalized_label" in test_ds.column_names:
        test_ds = test_ds.rename_column("normalized_label", "label")
        
    if num_samples and len(test_ds) > num_samples:
        test_ds = test_ds.select(range(num_samples))
    if num_samples and len(train_ds) > num_samples * 2:
        train_ds = train_ds.select(range(num_samples * 2))

    return train_ds, test_ds


def load_edgeshield_bpd_data(
    csv_path: str = "data/ransomware_behavioral_traces.csv",
    num_samples: Optional[int] = None,
    test_size: float = 0.2,
    random_state: int = 42
) -> Tuple[Dataset, Dataset]:
    """
    Loads ransomware behavioral traces for BPD training and evaluation.
    """
    if not os.path.exists(csv_path):
        from edgeshield.data.synthetic_ransomware import generate_curated_ransomware_dataset
        df = generate_curated_ransomware_dataset(csv_path)
    else:
        df = pd.read_csv(csv_path, nrows=num_samples)

    normalizer = RansomwareTelemetryNormalizer()
    formatted_texts = [normalizer.normalize_behavior_event(row) for _, row in df.iterrows()]
    df["formatted_text"] = formatted_texts
    
    # Map technique to ID
    def map_tech(row):
        tid = str(row.get("TechniqueID", "BENIGN_NORMAL"))
        return TECHNIQUE_TO_ID.get(tid, TECHNIQUE_TO_ID.get("BENIGN_NORMAL", 0))

    df["label"] = df.apply(map_tech, axis=1)

    train_df, test_df = train_test_split(df, test_size=test_size, random_state=random_state, stratify=df["label"] if len(df["label"].unique()) > 1 else None)
    
    train_ds = Dataset.from_pandas(train_df[["formatted_text", "label"]])
    test_ds = Dataset.from_pandas(test_df[["formatted_text", "label"]])
    
    return train_ds, test_ds
