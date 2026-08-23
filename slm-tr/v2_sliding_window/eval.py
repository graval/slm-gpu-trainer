"""
v2 - Sliding Window Model Evaluation Utility
Evaluates classification performance (Accuracy, F1, Precision, Recall, FP/FN, Latency)
on multi-event temporal context sequences (K=3..5 events).
"""

import os
import sys
import argparse
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import torch
import numpy as np
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
from transformers import (
    AutoTokenizer, 
    AutoModelForSequenceClassification, 
    DataCollatorWithPadding
)
from v2_sliding_window.data_loader import load_v2_dataset
from reasoning.engine import ReasoningEngine

def parse_args():
    parser = argparse.ArgumentParser(description="Evaluate v2 (Sliding Window) SLM Classifier")
    parser.add_argument("--csv_path", type=str, default="data/lmd_2023_dataset.csv", help="Path to dataset CSV file")
    parser.add_argument("--model_path", type=str, default="models/deberta-lateral-movement", help="Path to model directory")
    parser.add_argument("--base_model", type=str, default="microsoft/deberta-v3-small", help="Hugging Face base model name")
    parser.add_argument("--window_size", type=int, default=3, help="Sliding window size (events per sample)")
    parser.add_argument("--is_raw", action="store_true", default=False, help="Test raw untrained base model")
    parser.add_argument("--batch_size", type=int, default=16, help="Batch size")
    parser.add_argument("--max_length", type=int, default=256, help="Max token length for multi-event window")
    parser.add_argument("--num_samples", type=int, default=1000, help="Number of test samples to evaluate")
    return parser.parse_args()

def main():
    args = parse_args()
    engine = ReasoningEngine()
    
    print("=" * 70)
    print(f"   [v2 - SLIDING WINDOW] SLM EVALUATION HARNESS (K={args.window_size})   ")
    print("=" * 70)
    
    from v2_sliding_window.data_loader import resolve_dataset_path
    args.csv_path = resolve_dataset_path(args.csv_path)
    
    if not os.path.exists(args.csv_path):
        print(f"[!] Dataset not found at: {args.csv_path}")
        sys.exit(1)
        
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"[*] Evaluation Device: {device.upper()} (Sliding Window Mode, K={args.window_size})")
    
    # Load dataset
    _, test_dataset = load_v2_dataset(
        args.csv_path, 
        window_size=args.window_size,
        balance_classes=True, 
        test_size=0.2, 
        random_state=42
    )
    
    if args.num_samples and len(test_dataset) > args.num_samples:
        test_dataset = test_dataset.select(range(args.num_samples))
    print(f"[+] Evaluating on {len(test_dataset):,} windowed sequence samples.")
    
    active_path = args.base_model if args.is_raw else args.model_path
    if not args.is_raw and not os.path.exists(active_path):
        for cand in [
            f"{active_path}-stable",
            f"{active_path}-v2_sliding_window-stable",
            f"{active_path}-v2_sliding_window",
            "models/deberta-lateral-movement-v2_sliding_window-stable",
            "models/deberta-lateral-movement-v2_sliding_window"
        ]:
            if os.path.exists(cand):
                active_path = cand
                break
    print(f"[*] Loading Tokenizer & Model: {active_path}...")
    
    try:
        tokenizer = AutoTokenizer.from_pretrained(active_path, use_fast=True)
    except Exception:
        tokenizer = AutoTokenizer.from_pretrained(args.base_model, use_fast=True)
    
    def tokenize_fn(examples):
        return tokenizer(examples['formatted_text'], truncation=True, max_length=args.max_length)
        
    tokenized_test = test_dataset.map(tokenize_fn, batched=True)
    tokenized_test = tokenized_test.rename_column("normalized_label", "label")
    tokenized_test.set_format(type="torch", columns=["input_ids", "attention_mask", "label"])
    
    model = AutoModelForSequenceClassification.from_pretrained(active_path, num_labels=3)
    model = model.to(device)
    model.eval()
    
    data_collator = DataCollatorWithPadding(tokenizer=tokenizer)
    dataloader = torch.utils.data.DataLoader(
        tokenized_test, 
        batch_size=args.batch_size, 
        collate_fn=data_collator
    )
    
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
    avg_latency = total_time_ms / max(1, len(test_dataset))
    
    acc = accuracy_score(all_labels, all_preds)
    p_macro, r_macro, f1_macro, _ = precision_recall_fscore_support(all_labels, all_preds, average='macro', zero_division=0)
    
    fp = sum(1 for act, pred in zip(all_labels, all_preds) if act == 0 and pred in (1, 2))
    fn = sum(1 for act, pred in zip(all_labels, all_preds) if act in (1, 2) and pred == 0)
    
    print("\n" + "=" * 70)
    print("                     [v2 EVALUATION METRICS REPORT]                    ")
    print("=" * 70)
    print(f"  • Architecture Mode:      v2 - Sliding Window (K={args.window_size})")
    print(f"  • Target Model:           {active_path}")
    print(f"  • Test Dataset Size:      {len(test_dataset):,} samples")
    print(f"  • Overall Accuracy:       {acc * 100:.2f}%")
    print(f"  • Macro F1-Score:         {f1_macro * 100:.2f}%")
    print(f"  • Macro Precision:        {p_macro * 100:.2f}%")
    print(f"  • Macro Recall:           {r_macro * 100:.2f}%")
    print(f"  • False Positives (FP):   {fp} ({fp/max(1, len(all_labels))*100:.2f}%)")
    print(f"  • False Negatives (FN):   {fn} ({fn/max(1, len(all_labels))*100:.2f}%)")
    print(f"  • Avg Inference Latency:  {avg_latency:.2f} ms / sequence")
    print("=" * 70)

if __name__ == "__main__":
    main()
