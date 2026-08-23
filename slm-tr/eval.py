"""
Unified Evaluation Utility for Lateral Movement Detection SLMs
Evaluates model performance across v1 (Single Entry) or v2 (Sliding Window) variants.
"""

import os
import sys
import argparse
import numpy as np
import torch
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
from transformers import (
    AutoTokenizer, 
    AutoModelForSequenceClassification, 
    DataCollatorWithPadding
)
from data.loader import load_lmd_dataset

# Limit CPU threads to optimize context switching
torch.set_num_threads(2)

def parse_args():
    parser = argparse.ArgumentParser(description="Evaluate Lateral Movement SLM Classifier Performance")
    parser.add_argument("--variant", type=str, choices=["v1", "v2"], default="v2", help="Variant to evaluate: 'v1' (single entry) or 'v2' (sliding window)")
    parser.add_argument("--csv_path", type=str, default="data/lmd_2023_dataset.csv", help="Path to the LMD-2023 CSV file")
    parser.add_argument("--model_path", type=str, default="models/deberta-lateral-movement", help="Path to fine-tuned model directory")
    parser.add_argument("--base_model", type=str, default="microsoft/deberta-v3-small", help="Hugging Face base model name for raw evaluation")
    parser.add_argument("--is_raw", action="store_true", default=False, help="Set this flag to test the raw, untrained base model")
    parser.add_argument("--batch_size", type=int, default=16, help="Batch size for evaluation")
    parser.add_argument("--window_size", type=int, default=None, help="Sliding window size (defaults to 1 for v1, 3 for v2)")
    parser.add_argument("--max_length", type=int, default=None, help="Maximum token length for tokenizer")
    return parser.parse_args()

def main():
    args = parse_args()
    
    # Resolve window size and max length based on variant
    if args.window_size is None:
        args.window_size = 1 if args.variant == "v1" else 3
    if args.max_length is None:
        args.max_length = 128 if args.variant == "v1" else 256
        
    print("=" * 70)
    print(f"   [+] LATERAL MOVEMENT SLM EVALUATION UTILITY ({args.variant.upper()})   ")
    print("=" * 70)
    
    from v1_single_entry.data_loader import resolve_dataset_path
    args.csv_path = resolve_dataset_path(args.csv_path)
    
    if not os.path.exists(args.csv_path):
        print(f"[!] ERROR: Dataset not found at: {args.csv_path}")
        sys.exit(1)
        
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"[*] Evaluation Device: {device.upper()} (Variant: {args.variant}, Window K={args.window_size})")
    
    # 1. Load the split dataset
    print(f"[*] Loading dataset and isolating test partition (Window Size={args.window_size})...")
    try:
        _, test_dataset = load_lmd_dataset(
            args.csv_path, 
            window_size=args.window_size,
            balance_classes=True, 
            test_size=0.2, 
            random_state=42
        )
        print(f"[+] Isolated Test Partition: {len(test_dataset):,} event logs.")
    except Exception as e:
        print(f"[!] Error loading dataset: {e}")
        sys.exit(1)
        
    # 2. Select model path
    if args.is_raw:
        active_model_path = args.base_model
        print(f"[*] EVALUATION TARGET: Raw, Untrained Base Model ({active_model_path})")
    else:
        variant_suffix = "v1_single_entry" if args.variant == "v1" else "v2_sliding_window"
        candidate_paths = [
            args.model_path,
            f"models/deberta-lateral-movement-{variant_suffix}",
            f"models/deberta-lateral-movement-{args.variant}",
            "models/deberta-lateral-movement"
        ]
        active_model_path = next((p for p in candidate_paths if os.path.exists(p)), args.model_path)
        if not os.path.exists(active_model_path):
            print(f"[!] ERROR: Fine-tuned model directory not found at: {active_model_path}")
            sys.exit(1)
        print(f"[*] EVALUATION TARGET: Fine-Tuned Model Weights ({active_model_path})")
        
    # 3. Load tokenizer and tokenize dataset
    print(f"[*] Initializing Tokenizer for: {active_model_path}...")
    try:
        tokenizer = AutoTokenizer.from_pretrained(active_model_path, use_fast=True)
    except Exception:
        tokenizer = AutoTokenizer.from_pretrained(args.base_model, use_fast=True)
    
    def tokenize_function(examples):
        return tokenizer(
            examples['formatted_text'], 
            truncation=True, 
            max_length=args.max_length
        )
        
    print("[*] Tokenizing test dataset...")
    tokenized_test = test_dataset.map(tokenize_function, batched=True)
    tokenized_test = tokenized_test.rename_column("normalized_label", "label")
    tokenized_test.set_format(type="torch", columns=["input_ids", "attention_mask", "label"])
    
    # 4. Load Model
    print(f"[*] Loading model parameters into memory...")
    try:
        model = AutoModelForSequenceClassification.from_pretrained(
            active_model_path, 
            num_labels=3
        )
        model = model.to(device)
        model.eval()
    except Exception as e:
        print(f"[!] Failed to load model: {e}")
        sys.exit(1)
        
    # 5. Run Batch Inference
    data_collator = DataCollatorWithPadding(tokenizer=tokenizer)
    dataloader = torch.utils.data.DataLoader(
        tokenized_test, 
        batch_size=args.batch_size, 
        collate_fn=data_collator
    )
    
    all_preds = []
    all_labels = []
    
    print("[*] Running batch inference across test set...")
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
            
    # 6. Compute Metrics
    accuracy = accuracy_score(all_labels, all_preds)
    precision_macro, recall_macro, f1_macro, _ = precision_recall_fscore_support(
        all_labels, all_preds, average='macro', zero_division=0
    )
    precision_per_class, recall_per_class, f1_per_class, _ = precision_recall_fscore_support(
        all_labels, all_preds, average=None, labels=[0, 1, 2], zero_division=0
    )
    
    # 7. Print Performance Report
    print("\n" + "=" * 25 + f" EVALUATION PERFORMANCE REPORT ({args.variant.upper()}) " + "=" * 25)
    print(f"Variant:                   {args.variant.upper()} (Window K={args.window_size})")
    print(f"Target Model:              {active_model_path}")
    print(f"Test Partition Size:       {len(all_labels)} samples")
    print(f"Accuracy:                  {accuracy:.4f} ({accuracy*100:.2f}%)")
    print(f"Macro F1-Score:            {f1_macro:.4f}")
    print(f"Macro Precision:           {precision_macro:.4f}")
    print(f"Macro Recall:              {recall_macro:.4f}")
    print("-" * 75)
    print("Per-Class Metrics:")
    print(f"  [+] Normal (Class 0):      F1={f1_per_class[0]:.4f} | Precision={precision_per_class[0]:.4f} | Recall={recall_per_class[0]:.4f}")
    print(f"  [!] EoRS (Class 1 - WMI):  F1={f1_per_class[1]:.4f} | Precision={precision_per_class[1]:.4f} | Recall={recall_per_class[1]:.4f}")
    print(f"  [!] EoHT (Class 2 - PtH):  F1={f1_per_class[2]:.4f} | Precision={precision_per_class[2]:.4f} | Recall={recall_per_class[2]:.4f}")
    print("=" * 75)

if __name__ == "__main__":
    main()
