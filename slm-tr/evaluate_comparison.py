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

# Limit CPU threads to optimize context switching
torch.set_num_threads(2)

def evaluate_model(model_path, base_model_name, test_dataset, tokenizer, device, batch_size=16):
    print(f"[*] Loading model parameters from: {model_path} ...")
    try:
        model = AutoModelForSequenceClassification.from_pretrained(model_path, num_labels=3)
        model = model.to(device)
        if device == "cpu":
            model = model.float()
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
            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            labels = batch['labels'].to(device)
            
            outputs = model(input_ids=input_ids, attention_mask=attention_mask)
            logits = outputs.logits
            
            preds = torch.argmax(logits, dim=-1).cpu().numpy()
            
            all_preds.extend(preds)
            all_labels.extend(labels.cpu().numpy())
            
    end_time = time.perf_counter()
    total_duration_ms = (end_time - start_time) * 1000.0
    avg_latency_ms = total_duration_ms / len(test_dataset)
    
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
    print("=" * 80)
    print("      [🔍] SLM COMPARATIVE METRICS EVALUATOR (RAW vs. FINE-TUNED)      ")
    print("=" * 80)
    
    csv_path = "data/lmd_2023_dataset.csv"
    base_model = "microsoft/deberta-v3-small"
    fine_tuned_path = "models/deberta-lateral-movement"
    
    if not os.path.exists(csv_path):
        print(f"[!] Dataset not found at: {csv_path}")
        print("[!] Please run environment setup or populate the dataset first!")
        sys.exit(1)
        
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"[*] Evaluation Device: {device.upper()}")
    
    # 1. Load dataset (10% test split)
    print("[*] Loading labeled dataset and isolating 10% test partition...")
    # We use a fixed random state to ensure exact reproducible test splits
    _, test_dataset = load_lmd_dataset(
        csv_path, 
        balance_classes=True,
        test_size=0.1,
        random_state=42
    )
    print(f"[+] Isolated Test Split: {len(test_dataset):,} samples.")
    
    # 2. Tokenize dataset
    print(f"[*] Initializing Tokenizer: {base_model}...")
    tokenizer = AutoTokenizer.from_pretrained(base_model, use_fast=True)
    
    def tokenize_function(examples):
        return tokenizer(
            examples['formatted_text'], 
            truncation=True, 
            max_length=64
        )
        
    print("[*] Tokenizing test dataset...")
    tokenized_test = test_dataset.map(tokenize_function, batched=True)
    tokenized_test = tokenized_test.rename_column("normalized_label", "label")
    tokenized_test.set_format(type="torch", columns=["input_ids", "attention_mask", "label"])
    
    # 3. Evaluate Raw Base Model
    print("\n" + "-" * 40 + " EVALUATING UNTRAINED / RAW BASE MODEL " + "-" * 40)
    raw_results = evaluate_model(base_model, base_model, tokenized_test, tokenizer, device)
    
    # 4. Evaluate Fine-Tuned Model
    print("\n" + "-" * 40 + " EVALUATING FINE-TUNED MODEL " + "-" * 40)
    if not os.path.exists(fine_tuned_path):
        print(f"[!] Fine-tuned model not found at: {fine_tuned_path}. Running training on CPU first to obtain checkpoints...")
        # Fallback to train on CPU to ensure we always have weights
        os.system(f"python train_classifier.py --epochs 3 --batch_size 8")
        
    trained_results = evaluate_model(fine_tuned_path, base_model, tokenized_test, tokenizer, device)
    
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
