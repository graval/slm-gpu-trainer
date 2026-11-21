"""
Comprehensive Benchmark Execution Script for Unseen Datasets
Evaluates EdgeShield (ONNX INT8 / PyTorch DeBERTa-v3) across:
1. Windows-APT Dec-22 (Living-off-the-Land & AMSI Bypass)
2. Windows-APT Nov-30 (Lateral Tool Transfer & Unmanaged PowerShell)
3. Mordor WMI (Covenant C2 WMI process execution)
4. Mordor WinRM (Covenant C2 WinRM lateral movement)

Extracts Level-1 Binary Threat Interception metrics, Level-2 Attribution,
measures runtime latency, and outputs summary JSON & confusion matrices.
"""

import os
import sys
import time
import json
import numpy as np
import pandas as pd
from sklearn.metrics import classification_report, accuracy_score, precision_recall_fscore_support, confusion_matrix, roc_auc_score

def resolve_path(path_str):
    """Intelligently resolves data and model paths across local, subfolder, and Kaggle environments."""
    if not path_str or os.path.exists(path_str):
        return path_str
    # Check inside slm-tr/
    alt_slm = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), path_str)
    if os.path.exists(alt_slm):
        return alt_slm
    alt_slm_data = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", os.path.basename(path_str))
    if os.path.exists(alt_slm_data):
        return alt_slm_data
    # Check parent workspace
    alt_parent = os.path.join(os.getcwd(), path_str)
    if os.path.exists(alt_parent):
        return alt_parent
    # Check Kaggle input paths
    basename = os.path.basename(path_str)
    kaggle_paths = [
        f"/kaggle/input/lateral-movement-dataset-lmd-2023/{basename}",
        f"/kaggle/working/slm-gpu-trainer/slm-tr/{path_str}",
        f"/kaggle/working/slm-gpu-trainer/{path_str}"
    ]
    for kp in kaggle_paths:
        if os.path.exists(kp):
            return kp
    return path_str

# Ensure slm-tr is in path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if os.path.join(PROJECT_ROOT, 'slm-tr') not in sys.path:
    sys.path.insert(0, os.path.join(PROJECT_ROOT, 'slm-tr'))
sys.path.insert(0, 'slm-tr')

from v2_sliding_window.data_loader import generate_windowed_dataframe

def benchmark_dataset(
    dataset_name,
    file_path,
    model_path='slm-tr/models/edgeshield_lsa_deberta',
    onnx_path='slm-tr/models/onnx_edgeshield/edgeshield_lsa_int8.onnx',
    use_onnx=True,
    window_size=3,
    max_samples=1500
):
    print("=" * 80)
    print(f"[*] Benchmarking Dataset: {dataset_name} ({file_path})")
    print("=" * 80)

    # 1. Ingest Data
    if file_path.endswith('.json') or file_path.endswith('.jsonl'):
        records = []
        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                records = json.load(f)
            except Exception:
                f.seek(0)
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            records.append(json.loads(line))
                        except Exception:
                            pass
        df = pd.DataFrame(records)
    else:
        df = pd.read_csv(file_path, low_memory=False)

    print(f"[*] Ingested {len(df):,} raw events.")

    # 2. Standardize columns
    col_mappings = {
        'Image': ['image', 'ProcessName', 'process_name', 'SourceImage', '_source.data.win.eventdata.image'],
        'CommandLine': ['command_line', 'CommandLine', 'cmd', 'ProcessCommandLine', '_source.data.win.eventdata.commandLine'],
        'ParentImage': ['parent_image', 'ParentProcessName', 'ParentImage', '_source.data.win.eventdata.parentImage'],
        'ParentCommandLine': ['parent_command_line', 'ParentCommandLine', '_source.data.win.eventdata.parentCommandLine'],
        'User': ['user', 'TargetUserName', 'UserName', 'User', '_source.data.win.eventdata.user', '_source.data.win.eventdata.targetUserName'],
        'EventID': ['event_id', 'EventId', 'EventID', '_source.data.win.system.eventID'],
        'Label': ['label', 'Class', 'threat_label', 'traffic_type', 'norm_lbl']
    }
    for target_col, candidates in col_mappings.items():
        if target_col not in df.columns:
            for c in candidates:
                if c in df.columns:
                    df[target_col] = df[c]
                    break

    if 'EventID' not in df.columns: df['EventID'] = 1
    if 'Image' not in df.columns: df['Image'] = 'system.exe'
    if 'CommandLine' not in df.columns: df['CommandLine'] = ''
    if 'ParentImage' not in df.columns: df['ParentImage'] = ''
    if 'ParentCommandLine' not in df.columns: df['ParentCommandLine'] = ''
    if 'User' not in df.columns: df['User'] = 'NT AUTHORITY\\SYSTEM'

    # Determine ground-truth labels
    if 'Label' not in df.columns or df['Label'].isna().all():
        # Mordor dataset is pure adversary emulation (all events belong to attack campaign)
        df['UnifiedLabel'] = 'Attack'
    else:
        def map_label(val):
            s = str(val).lower().strip()
            if any(norm in s for norm in ['normal', 'benign', '0']):
                return 'Normal'
            elif any(eors in s for eors in ['eors', 'remote service', 't1021', 't1047']):
                return 'EoRS'
            elif any(eoht in s for eoht in ['eoht', 'hash', 'credential', 't1003', 'sam']):
                return 'EoHT'
            elif any(lotl in s for lotl in ['lotl', 't1059', 'powershell', 'wscript', 'bypass']):
                return 'LotL'
            else:
                return 'Attack'
        df['UnifiedLabel'] = df['Label'].apply(map_label)

    # Subsample if needed
    if max_samples and len(df) > max_samples:
        df = df.sample(n=max_samples, random_state=42).reset_index(drop=True)

    # Build sliding windows
    print(f"[*] Building temporal sliding windows (K={window_size})...")
    df = generate_windowed_dataframe(df, window_size=window_size)
    texts = df['formatted_text'].tolist()

    # 3. Model Inference Setup
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_path)

    batch_size = 64
    latencies = []
    predictions = []
    threat_probs = []

    if use_onnx and os.path.exists(onnx_path):
        import onnxruntime as ort
        sess_options = ort.SessionOptions()
        sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        sess_options.intra_op_num_threads = os.cpu_count() or 8
        session = ort.InferenceSession(onnx_path, sess_options, providers=['CPUExecutionProvider'])
        backend_name = "ONNX INT8"

        t_start = time.perf_counter()
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            inputs = tokenizer(batch, padding="max_length", truncation=True, max_length=128, return_tensors='np')
            ort_in = {
                "input_ids": inputs["input_ids"].astype(np.int64),
                "attention_mask": inputs["attention_mask"].astype(np.int64)
            }
            t0 = time.perf_counter()
            logits = session.run(None, ort_in)[0]
            t1 = time.perf_counter()
            latencies.extend([(t1 - t0) * 1000.0 / len(batch)] * len(batch))

            exp_l = np.exp(logits - np.max(logits, axis=-1, keepdims=True))
            probs = exp_l / np.sum(exp_l, axis=-1, keepdims=True)
            preds = np.argmax(logits, axis=-1)
            predictions.extend(preds)
            threat_probs.extend(1.0 - probs[:, 0])
        total_time = time.perf_counter() - t_start
    else:
        import torch
        from transformers import AutoModelForSequenceClassification
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        model = AutoModelForSequenceClassification.from_pretrained(model_path).to(device)
        model.eval()
        backend_name = f"PyTorch ({device})"

        t_start = time.perf_counter()
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            inputs = tokenizer(batch, padding=True, truncation=True, max_length=256, return_tensors='pt')
            inputs = {k: v.to(device) for k, v in inputs.items()}
            t0 = time.perf_counter()
            with torch.no_grad():
                logits = model(**inputs).logits.cpu().numpy()
            t1 = time.perf_counter()
            latencies.extend([(t1 - t0) * 1000.0 / len(batch)] * len(batch))

            exp_l = np.exp(logits - np.max(logits, axis=-1, keepdims=True))
            probs = exp_l / np.sum(exp_l, axis=-1, keepdims=True)
            preds = np.argmax(logits, axis=-1)
            predictions.extend(preds)
            threat_probs.extend(1.0 - probs[:, 0])
        total_time = time.perf_counter() - t_start

    mean_lat = np.mean(latencies)
    p95_lat = np.percentile(latencies, 95)
    fps = len(texts) / total_time

    # 4. Metrics Extraction
    id2label = {0: 'Normal', 1: 'EoRS', 2: 'EoHT'}
    pred_labels = [id2label.get(p, 'Attack') for p in predictions]

    # Binary Metrics
    y_true_binary = [0 if l == 'Normal' else 1 for l in df['UnifiedLabel']]
    y_pred_binary = [0 if p == 0 else 1 for p in predictions]

    has_both_classes = len(set(y_true_binary)) > 1
    if has_both_classes:
        acc = accuracy_score(y_true_binary, y_pred_binary)
        prec, rec, f1, _ = precision_recall_fscore_support(y_true_binary, y_pred_binary, average='binary', zero_division=0)
        cm = confusion_matrix(y_true_binary, y_pred_binary)
        if cm.shape == (2, 2):
            tn, fp, fn, tp = cm.ravel()
            fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
            specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0
        else:
            tn, fp, fn, tp = 0, 0, 0, 0
            fpr, specificity = 0.0, 0.0
        try:
            auc = roc_auc_score(y_true_binary, threat_probs)
        except Exception:
            auc = 0.5
    else:
        # All positive (pure attack evaluation)
        tp = sum(1 for p in y_pred_binary if p == 1)
        fn = sum(1 for p in y_pred_binary if p == 0)
        rec = tp / len(y_pred_binary) if len(y_pred_binary) > 0 else 0.0
        prec = 1.0
        acc = rec
        f1 = 2 * (prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0
        fpr = 0.0
        specificity = 1.0
        auc = 1.0
        cm = np.array([[0, 0], [fn, tp]])

    result = {
        "dataset": dataset_name,
        "backend": backend_name,
        "samples": len(texts),
        "accuracy": round(float(acc) * 100, 2),
        "threat_recall": round(float(rec) * 100, 2),
        "precision": round(float(prec) * 100, 2),
        "macro_f1": round(float(f1) * 100, 2),
        "fpr": round(float(fpr) * 100, 2),
        "mean_latency_ms": round(float(mean_lat), 2),
        "p95_latency_ms": round(float(p95_lat), 2),
        "throughput_fps": round(float(fps), 1),
        "confusion_matrix": cm.tolist()
    }

    print(f"\n[+] Results for {dataset_name}:")
    print(f"    Accuracy:                 {result['accuracy']}%")
    print(f"    Threat Recall (Sensitivity): {result['threat_recall']}%")
    print(f"    Precision:                {result['precision']}%")
    print(f"    Macro F1:                 {result['macro_f1']}%")
    print(f"    False Positive Rate:      {result['fpr']}%")
    print(f"    Mean Latency:             {result['mean_latency_ms']} ms/event (P95: {result['p95_latency_ms']} ms)")
    print(f"    Throughput:               {result['throughput_fps']} EPS")
    print(f"    Confusion Matrix:\n{cm}")
    return result

if __name__ == '__main__':
    datasets = [
        ("Windows-APT Dec-22 (LotL & AMSI Bypass)", resolve_path("data/windows_apt/22-December.csv")),
        ("Windows-APT Nov-30 (Tool Transfer & PowerShell)", resolve_path("data/windows_apt/30-November.csv")),
        ("The Mordor Project (Covenant WinRM)", resolve_path("data/covenant_winrm.json")),
        ("The Mordor Project (Covenant WMI)", resolve_path("data/covenant_wmi.json"))
    ]

    all_results = []
    for name, path in datasets:
        if os.path.exists(path):
            res = benchmark_dataset(name, path, use_onnx=True, max_samples=1000)
            all_results.append(res)
        else:
            print(f"[!] Path not found: {path}")

    # Output summary JSON
    with open('unseen_datasets_benchmark_results.json', 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2)
    print("\n[+] All unseen benchmark results written to unseen_datasets_benchmark_results.json")
