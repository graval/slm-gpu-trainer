import os
import sys
import time
import json
from datetime import datetime
import numpy as np
import torch
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
from transformers import AutoTokenizer, AutoModelForSequenceClassification, DataCollatorWithPadding
from data.loader import load_lmd_dataset

import argparse

# Try importing DirectML
try:
    import torch_directml
    DML_AVAILABLE = torch_directml.is_available()
except ImportError:
    torch_directml = None
    DML_AVAILABLE = False

def parse_args():
    parser = argparse.ArgumentParser(description="Evaluate Comparison (Raw vs Fine-Tuned SLM)")
    parser.add_argument("--csv_path", type=str, default="data/lmd_2023_dataset.csv", help="Path to the LMD-2023 CSV file")
    parser.add_argument("--base_model", type=str, default="auto", help="Hugging Face base model name or 'auto'")
    parser.add_argument("--model_path", type=str, default="models/deberta-lateral-movement", help="Path to fine-tuned model directory")
    parser.add_argument("--window_size", type=int, default=3, help="Sliding window size (number of consecutive events per sequence, default: 3)")
    parser.add_argument("--max_length", type=int, default=128, help="Maximum token length for tokenizer (default: 128)")
    parser.add_argument("--batch_size", type=int, default=32, help="Batch size for evaluation")
    parser.add_argument("--num_samples", type=int, default=1000, help="Number of test samples to evaluate (default: 1000)")
    return parser.parse_args()

def evaluate_model(model_path, base_model_name, test_dataset, tokenizer, device, batch_size=32):
    print(f"[*] Loading model parameters from: {model_path} ...")
    try:
        model = AutoModelForSequenceClassification.from_pretrained(model_path, num_labels=3)
        if str(device) == "cpu":
            model = model.float()
        model = model.to(device)
        model.eval()
    except Exception as e:
        print(f"[!] Failed to load model: {e}")
        return None

    data_collator = DataCollatorWithPadding(tokenizer=tokenizer)
    dataloader = torch.utils.data.DataLoader(
        test_dataset, 
        batch_size=batch_size, 
        collate_fn=data_collator
    )
    
    all_preds = []
    all_labels = []
    
    # Track inference duration
    start_time = time.perf_counter()
    
    with torch.no_grad():
        for batch in dataloader:
            batch = {k: v.to(device) for k, v in batch.items()}
            outputs = model(**batch)
            logits = outputs.logits
            preds = torch.argmax(logits, dim=-1).cpu().numpy()
            
            all_preds.extend(preds)
            all_labels.extend(batch['labels'].cpu().numpy())
            
    end_time = time.perf_counter()
    total_duration_ms = (end_time - start_time) * 1000.0
    avg_latency_ms = total_duration_ms / max(1, len(test_dataset))
    
    # Calculate classification metrics
    accuracy = accuracy_score(all_labels, all_preds)
    precision_macro, recall_macro, f1_macro, _ = precision_recall_fscore_support(
        all_labels, all_preds, average='macro', zero_division=0
    )
    
    # Calculate False Positives (FP) and False Negatives (FN)
    # Class 0: Normal (Benign)
    # Class 1: EoRS (Malicious)
    # Class 2: EoHT (Malicious)
    false_positives = 0
    false_negatives = 0
    
    for act, pred in zip(all_labels, all_preds):
        if act == 0 and pred in (1, 2):
            false_positives += 1
        elif act in (1, 2) and pred == 0:
            false_negatives += 1
            
    return {
        "accuracy": float(accuracy),
        "f1_macro": float(f1_macro),
        "precision_macro": float(precision_macro),
        "recall_macro": float(recall_macro),
        "false_positives": int(false_positives),
        "false_negatives": int(false_negatives),
        "avg_latency_ms": float(avg_latency_ms),
        "total_duration_ms": float(total_duration_ms)
    }

def main():
    args = parse_args()
    print("=" * 80)
    print("      [*] SLM COMPARATIVE METRICS EVALUATOR (RAW vs. FINE-TUNED)      ")
    print("=" * 80)
    
    csv_path = args.csv_path
    fine_tuned_path = args.model_path
    
    if not os.path.exists(csv_path):
        print(f"[!] Dataset not found at: {csv_path}")
        print("[!] Please run environment setup or populate the dataset first!")
        sys.exit(1)
        
    # Auto-resolve device
    if torch.cuda.is_available():
        device = torch.device("cuda")
        device_name = f"CUDA ({torch.cuda.get_device_name(0)})"
    elif DML_AVAILABLE and torch_directml.device_count() > 0:
        device = torch_directml.device()
        device_name = f"DirectML GPU ({torch_directml.device_name(0).strip()})"
    else:
        device = torch.device("cpu")
        device_name = f"CPU ({os.cpu_count() or 16} Cores)"
        
    print(f"[*] Active Evaluation Device: {device_name}")
    
    # Auto-resolve base model
    base_model = args.base_model
    if base_model == "auto":
        config_path = os.path.join(fine_tuned_path, "config.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    cfg = json.load(f)
                base_model = cfg.get("_name_or_path", "distilbert-base-uncased")
            except Exception:
                base_model = "distilbert-base-uncased"
        else:
            base_model = "distilbert-base-uncased"
            
    print(f"[*] Base Architecture: {base_model}")
    print(f"[*] Fine-Tuned Model:  {fine_tuned_path}")
    
    # 1. Load dataset (10% test split)
    print(f"\n[*] Loading labeled dataset and isolating 10% test partition (Window Size={args.window_size})...")
    _, test_dataset = load_lmd_dataset(
        csv_path, 
        window_size=args.window_size,
        balance_classes=True,
        test_size=0.1,
        random_state=42
    )
    
    # Sample balanced test evaluation set
    num_eval_samples = min(args.num_samples, len(test_dataset))
    test_df = test_dataset.to_pandas()
    per_class = num_eval_samples // 3
    sampled = []
    for lbl in [0, 1, 2]:
        sub = test_df[test_df['normalized_label'] == lbl]
        sampled.append(sub.sample(n=min(len(sub), per_class), random_state=42))
    
    import pandas as pd
    from datasets import Dataset
    test_df_sampled = pd.concat(sampled).sample(frac=1, random_state=42).reset_index(drop=True)
    test_dataset = Dataset.from_pandas(test_df_sampled)
    print(f"[+] Isolated Balanced Test Split: {len(test_dataset):,} samples.")
    
    # 2. Tokenize dataset
    print(f"[*] Initializing Tokenizer: {base_model}...")
    tokenizer = AutoTokenizer.from_pretrained(base_model, use_fast=True)
    
    def tokenize_function(examples):
        return tokenizer(
            examples['formatted_text'], 
            truncation=True, 
            max_length=args.max_length
        )
        
    print("[*] Tokenizing test dataset...")
    tokenized_test = test_dataset.map(tokenize_function, batched=True)
    tokenized_test = tokenized_test.rename_column("normalized_label", "label")
    tokenized_test = tokenized_test.remove_columns(["formatted_text"])
    
    # 3. Evaluate Raw Base Model (Untrained Random Head)
    print("\n" + "-" * 40 + " EVALUATING UNTRAINED / RAW BASE MODEL " + "-" * 40)
    raw_results = evaluate_model(base_model, base_model, tokenized_test, tokenizer, device, batch_size=args.batch_size)
    
    # 4. Evaluate Fine-Tuned Model
    print("\n" + "-" * 40 + " EVALUATING FINE-TUNED MODEL " + "-" * 40)
    if not os.path.exists(fine_tuned_path):
        print(f"[!] Fine-tuned model not found at: {fine_tuned_path}.")
        sys.exit(1)
        
    trained_results = evaluate_model(fine_tuned_path, base_model, tokenized_test, tokenizer, device, batch_size=args.batch_size)
    
    if not raw_results or not trained_results:
        print("[!] Evaluation failed.")
        sys.exit(1)
        
    # Get current timestamp with local timezone info
    local_time = datetime.now().astimezone()
    timestamp_str = local_time.isoformat()
    
    summary_data = {
        "timestamp": timestamp_str,
        "test_partition_size": len(test_dataset),
        "raw_model": raw_results,
        "trained_model": trained_results
    }
    
    # Save to JSON for Streamlit UI ingestion
    json_path = "evaluation_summary.json"
    with open(json_path, "w") as f:
        json.dump(summary_data, f, indent=4)
    print(f"\n[+] Structured summary successfully written to: {json_path}")
    
    ext_json = "external/evaluation_summary.json"
    if os.path.exists("external"):
        with open(ext_json, "w") as f:
            json.dump(summary_data, f, indent=4)
            
    # Formulate human-readable log entry
    log_entry = f"""======================================================================
TIMESTAMP: {timestamp_str}
======================================================================
SLM LATERAL MOVEMENT CLASSIFIER COMPARISON REPORT
----------------------------------------------------------------------
Test Partition Size: {len(test_dataset)} samples
Base Model Arch:     {base_model}
Fine-Tuned Weight:   {fine_tuned_path}

1. UNTRAINED / RAW MODEL METRICS:
   - Accuracy:                  {raw_results['accuracy'] * 100:.2f}%
   - Macro F1-Score:            {raw_results['f1_macro']:.4f}
   - Macro Precision:           {raw_results['precision_macro']:.4f}
   - Macro Recall:              {raw_results['recall_macro']:.4f}
   - Total False Positives:     {raw_results['false_positives']} samples
   - Total False Negatives:     {raw_results['false_negatives']} samples
   - Avg. Inference Latency:    {raw_results['avg_latency_ms']:.2f} ms / sample
   - Total Evaluation Duration: {raw_results['total_duration_ms'] / 1000.0:.2f} seconds

2. FINE-TUNED / UPDATED MODEL METRICS:
   - Accuracy:                  {trained_results['accuracy'] * 100:.2f}%
   - Macro F1-Score:            {trained_results['f1_macro']:.4f}
   - Macro Precision:           {trained_results['precision_macro']:.4f}
   - Macro Recall:              {trained_results['recall_macro']:.4f}
   - Total False Positives:     {trained_results['false_positives']} samples
   - Total False Negatives:     {trained_results['false_negatives']} samples
   - Avg. Inference Latency:    {trained_results['avg_latency_ms']:.2f} ms / sample
   - Total Evaluation Duration: {trained_results['total_duration_ms'] / 1000.0:.2f} seconds

3. PERFORMANCE IMPROVEMENT DELTAS:
   - Accuracy Increase:         +{(trained_results['accuracy'] - raw_results['accuracy']) * 100:.2f}%
   - F1-Score Improvement:      +{trained_results['f1_macro'] - raw_results['f1_macro']:.4f}
   - False Positives Reduced:   {raw_results['false_positives'] - trained_results['false_positives']} samples
   - False Negatives Reduced:   {raw_results['false_negatives'] - trained_results['false_negatives']} samples
======================================================================
"""
    
    # Save to summary log file
    log_path = "evaluation_summary.log"
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(log_entry + "\n")
    print(f"[+] Human-readable summary successfully written and appended to: {log_path}")
    print("=" * 80)

if __name__ == "__main__":
    main()
