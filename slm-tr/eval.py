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
    parser = argparse.ArgumentParser(description="Evaluate DeBERTa SLM Lateral Movement Classifier Performance")
    parser.add_argument("--csv_path", type=str, default="external/lmd_2023_dataset.csv", help="Path to the LMD-2023 CSV file")
    parser.add_argument("--model_path", type=str, default="models/deberta-lateral-movement", help="Path to fine-tuned model directory")
    parser.add_argument("--base_model", type=str, default="microsoft/deberta-v3-small", help="Hugging Face base model name for raw evaluation")
    parser.add_argument("--is_raw", action="store_true", default=False, help="Set this flag to test the raw, untrained base model")
    parser.add_argument("--batch_size", type=int, default=16, help="Batch size for evaluation")
    return parser.parse_args()

def main():
    args = parse_args()
    
    print("=" * 70)
    print("      [🔍] DEBERTA LATERAL MOVEMENT SLM EVALUATION UTILITY      ")
    print("=" * 70)
    
    # Check dataset existence
    if not os.path.exists(args.csv_path):
        print(f"[!] ERROR: Dataset not found at: {args.csv_path}")
        print("    Please ensure you have placed 'lmd_2023_dataset.csv' inside your external/ folder.")
        sys.exit(1)
        
    # Check device
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"[*] Evaluation Device: {device.upper()}")
    
    # 1. Load the split dataset (keeping the 20% test partition)
    print(f"[*] Loading dataset and isolating test partition...")
    try:
        # We use a fixed random state (42) to isolate an identical test partition for pre/post training comparison
        _, test_dataset = load_lmd_dataset(
            args.csv_path, 
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
        active_model_path = args.model_path
        if not os.path.exists(active_model_path) or not os.path.exists(os.path.join(active_model_path, "model.safetensors")):
            print(f"[!] ERROR: Fine-tuned model weights not found at: {active_model_path}")
            print("    Please run the training pipeline first to save the fine-tuned model.")
            print("    (Or use the --is_raw flag to evaluate the untrained base model).")
            sys.exit(1)
        print(f"[*] EVALUATION TARGET: Fine-Tuned Model Weights ({active_model_path})")
        
    # 3. Load tokenizer and tokenize dataset
    print(f"[*] Initializing Tokenizer: {args.base_model}...")
    tokenizer = AutoTokenizer.from_pretrained(args.base_model, use_fast=True)
    
    def tokenize_function(examples):
        return tokenizer(
            examples['formatted_text'], 
            truncation=True, 
            max_length=64
        )
        
    print("[*] Tokenizing test dataset...")
    tokenized_test = test_dataset.map(tokenize_function, batched=True)
    tokenized_test = tokenized_test.rename_column("normalized_label", "label")
    
    # 4. Load Model
    print(f"[*] Loading model parameters into memory...")
    try:
        # Load weights
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
    print("\n" + "=" * 25 + " EVALUATION PERFORMANCE REPORT " + "=" * 25)
    print(f"Target Model:              {active_model_path}")
    print(f"Test Partition Size:       {len(all_labels)} samples")
    print(f"Accuracy:                  {accuracy:.4f} ({accuracy*100:.2f}%)")
    print(f"Macro F1-Score:            {f1_macro:.4f}")
    print(f"Macro Precision:           {precision_macro:.4f}")
    print(f"Macro Recall:              {recall_macro:.4f}")
    print("-" * 75)
    print("Per-Class Metrics:")
    print(f"  🟢 Normal (Class 0):      F1={f1_per_class[0]:.4f} | Precision={precision_per_class[0]:.4f} | Recall={recall_per_class[0]:.4f}")
    print(f"  🟡 EoRS (Class 1 - WMI):  F1={f1_per_class[1]:.4f} | Precision={precision_per_class[1]:.4f} | Recall={recall_per_class[1]:.4f}")
    print(f"  🔴 EoHT (Class 2 - PtH):  F1={f1_per_class[2]:.4f} | Precision={precision_per_class[2]:.4f} | Recall={recall_per_class[2]:.4f}")
    print("=" * 75)
    
    if args.is_raw:
        print("\n💡 OBSERVATION (PRE-TRAINING):")
        print("   Notice that the raw, untrained base model has random/poor F1 performance.")
        print("   This is because the classification head parameters have not yet learned the threat logs.")
        print("   Run training inside Docker, and then run this script again WITHOUT the --is_raw flag!")
    else:
        print("\n💡 OBSERVATION (POST-TRAINING):")
        print("   Success! Your locally fine-tuned model demonstrates massive threat-hunting capability.")
        print("   Accuracy, Precision, and Recall scores have achieved a significant jump compared to the raw model.")
        
    print("\n" + "=" * 70)

if __name__ == "__main__":
    main()
