"""
v1 vs v2 Comparative Benchmark Evaluation Script
Evaluates both v1 (Single Entry) and v2 (Sliding Window) across datasets (LMD-2023, OpTC Benchmark),
comparing:
  - Accuracy & Macro F1-Score
  - Precision & Recall
  - False Positive Rate (FPR) & False Negative Rate (FNR)
  - Avg Inference Latency (ms/event)
"""

import os
import sys
import argparse
import time
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import torch
import pandas as pd
import numpy as np
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
from transformers import AutoTokenizer, AutoModelForSequenceClassification, DataCollatorWithPadding

from v1_single_entry.data_loader import load_v1_dataset
from v2_sliding_window.data_loader import load_v2_dataset
from reasoning.engine import ReasoningEngine

def parse_args():
    parser = argparse.ArgumentParser(description="Compare v1 (Single Entry) vs v2 (Sliding Window)")
    parser.add_argument("--csv_path", type=str, default="data/lmd_2023_dataset.csv", help="Path to benchmark CSV")
    parser.add_argument("--model_path", type=str, default="models/deberta-lateral-movement", help="Path to model weights")
    parser.add_argument("--base_model", type=str, default="microsoft/deberta-v3-small", help="Base model identifier")
    parser.add_argument("--is_raw", action="store_true", default=False, help="Evaluate raw base model")
    parser.add_argument("--num_samples", type=int, default=500, help="Number of test samples to evaluate")
    parser.add_argument("--batch_size", type=int, default=16, help="Evaluation batch size")
    return parser.parse_args()

def evaluate_partition(dataset, model, tokenizer, device, max_length, batch_size=16):
    def tokenize_fn(examples):
        return tokenizer(examples['formatted_text'], truncation=True, max_length=max_length)
        
    tokenized = dataset.map(tokenize_fn, batched=True)
    tokenized = tokenized.rename_column("normalized_label", "label")
    tokenized.set_format(type="torch", columns=["input_ids", "attention_mask", "label"])
    
    data_collator = DataCollatorWithPadding(tokenizer=tokenizer)
    dataloader = torch.utils.data.DataLoader(tokenized, batch_size=batch_size, collate_fn=data_collator)
    
    all_preds, all_labels = [], []
    start_time = time.perf_counter()
    
    with torch.no_grad():
        for batch in dataloader:
            batch = {k: v.to(device) for k, v in batch.items()}
            outputs = model(**batch)
            preds = torch.argmax(outputs.logits, dim=-1).cpu().numpy()
            all_preds.extend(preds)
            all_labels.extend(batch['labels'].cpu().numpy())
            
    total_time_ms = (time.perf_counter() - start_time) * 1000.0
    avg_latency = total_time_ms / max(1, len(dataset))
    
    acc = accuracy_score(all_labels, all_preds)
    p_macro, r_macro, f1_macro, _ = precision_recall_fscore_support(all_labels, all_preds, average='macro', zero_division=0)
    
    fp = sum(1 for act, pred in zip(all_labels, all_preds) if act == 0 and pred in (1, 2))
    fn = sum(1 for act, pred in zip(all_labels, all_preds) if act in (1, 2) and pred == 0)
    
    return {
        "accuracy": acc * 100,
        "f1_macro": f1_macro * 100,
        "precision": p_macro * 100,
        "recall": r_macro * 100,
        "false_positives": fp,
        "false_negatives": fn,
        "fp_rate": (fp / max(1, len(all_labels))) * 100,
        "fn_rate": (fn / max(1, len(all_labels))) * 100,
        "avg_latency_ms": avg_latency
    }

def main():
    args = parse_args()
    print("=" * 80)
    print("      [+] LATERAL MOVEMENT SLM BENCHMARK: v1 vs v2 ARCHITECTURAL COMPARISON      ")
    print("=" * 80)
    
    from v1_single_entry.data_loader import resolve_dataset_path
    args.csv_path = resolve_dataset_path(args.csv_path)
    
    for p in args.csv_path.split(","):
        if not os.path.exists(p.strip()):
            print(f"[!] Dataset not found at: {p.strip()}")
            sys.exit(1)
        
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"[*] Evaluation Device: {device.upper()}")
    
    # 1. Load v1 dataset (Single Entry)
    print("\n[*] [Phase 1] Loading v1 Single Entry dataset partition...")
    _, v1_test = load_v1_dataset(args.csv_path, balance_classes=True, test_size=0.2, random_state=42)
    if args.num_samples and len(v1_test) > args.num_samples:
        v1_test = v1_test.select(range(args.num_samples))
        
    # 2. Load v2 dataset (Sliding Window K=3)
    print("[*] [Phase 2] Loading v2 Sliding Window (K=3) dataset partition...")
    _, v2_test = load_v2_dataset(args.csv_path, window_size=3, balance_classes=True, test_size=0.2, random_state=42)
    if args.num_samples and len(v2_test) > args.num_samples:
        v2_test = v2_test.select(range(args.num_samples))
        
    # Load Model & Tokenizer
    target_path = args.base_model if args.is_raw else args.model_path
    if not args.is_raw and not os.path.exists(target_path):
        for cand in [
            f"{target_path}-v2_sliding_window-stable",
            f"{target_path}-v2_sliding_window",
            f"{target_path}-v1_single_entry-stable",
            f"{target_path}-v1_single_entry",
            "models/deberta-lateral-movement-v2_sliding_window-stable",
            "models/deberta-lateral-movement-v2_sliding_window",
            "models/deberta-lateral-movement-v1_single_entry-stable",
            "models/deberta-lateral-movement-v1_single_entry"
        ]:
            if os.path.exists(cand):
                target_path = cand
                break
                
    print(f"\n[*] Loading Model Weights: {target_path}...")
    try:
        tokenizer = AutoTokenizer.from_pretrained(target_path, use_fast=True)
    except Exception:
        tokenizer = AutoTokenizer.from_pretrained(args.base_model, use_fast=True)
        
    model = AutoModelForSequenceClassification.from_pretrained(target_path, num_labels=3)
    model = model.to(device)
    model.eval()
    
    # Run v1 Evaluation
    print("[*] Benchmarking v1 (Single Entry)...")
    v1_results = evaluate_partition(v1_test, model, tokenizer, device, max_length=128, batch_size=args.batch_size)
    
    # Run v2 Evaluation
    print("[*] Benchmarking v2 (Sliding Window K=3)...")
    v2_results = evaluate_partition(v2_test, model, tokenizer, device, max_length=256, batch_size=args.batch_size)
    
    # Print Side-by-Side Comparison
    print("\n" + "=" * 80)
    print(f"       [COMPARISON SUMMARY TABLE: {os.path.basename(args.csv_path)}]       ")
    print("=" * 80)
    print(f"{'Metric':<30} | {'v1 - Single Entry (K=1)':<22} | {'v2 - Sliding Window (K=3)':<22}")
    print("-" * 80)
    print(f"{'Overall Accuracy':<30} | {v1_results['accuracy']:>20.2f}% | {v2_results['accuracy']:>20.2f}%")
    print(f"{'Macro F1-Score':<30} | {v1_results['f1_macro']:>20.2f}% | {v2_results['f1_macro']:>20.2f}%")
    print(f"{'Macro Precision':<30} | {v1_results['precision']:>20.2f}% | {v2_results['precision']:>20.2f}%")
    print(f"{'Macro Recall':<30} | {v1_results['recall']:>20.2f}% | {v2_results['recall']:>20.2f}%")
    print(f"{'False Positive Rate':<30} | {v1_results['fp_rate']:>20.2f}% | {v2_results['fp_rate']:>20.2f}%")
    print(f"{'False Negative Rate':<30} | {v1_results['fn_rate']:>20.2f}% | {v2_results['fn_rate']:>20.2f}%")
    print(f"{'Avg Latency / Sample':<30} | {v1_results['avg_latency_ms']:>18.2f} ms | {v2_results['avg_latency_ms']:>18.2f} ms")
    print("=" * 80)

if __name__ == "__main__":
    main()
