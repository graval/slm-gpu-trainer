"""
EdgeShield: LSA (Log Semantic Analyzer) Fine-Tuning CLI Script
Trains the SLM backbone for Windows authentication & Lateral Movement detection (MITRE ATT&CK TA0008)
with Supervised Cross-Entropy and Contrastive Loss.
"""

import os
import sys
import argparse
import time
import json
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from transformers import AutoTokenizer, AutoModelForSequenceClassification, get_linear_schedule_with_warmup

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from edgeshield.taxonomy import TECHNIQUE_TO_ID, ID_TO_TECHNIQUE, LSA_TECHNIQUES
from edgeshield.lsa.analyzer import SupervisedContrastiveLoss, LogSemanticAnalyzer
from edgeshield.data.loader import load_edgeshield_lsa_data

def parse_args():
    parser = argparse.ArgumentParser(description="Train EdgeShield Log Semantic Analyzer (LSA)")
    parser.add_argument("--model_name", type=str, default="microsoft/deberta-v3-small", help="Base SLM model identifier")
    parser.add_argument("--dataset_path", type=str, default="data/lmd_2023_dataset.csv", help="Path to telemetry dataset")
    parser.add_argument("--output_dir", type=str, default="models/edgeshield_lsa", help="Directory to save trained weights")
    parser.add_argument("--epochs", type=int, default=3, help="Number of training epochs")
    parser.add_argument("--batch_size", type=int, default=16, help="Training batch size")
    parser.add_argument("--lr", type=float, default=3e-5, help="Learning rate")
    parser.add_argument("--num_samples", type=int, default=2000, help="Number of samples to train on")
    parser.add_argument("--use_contrastive", action="store_true", default=True, help="Enable Phase 2 Contrastive Loss")
    return parser.parse_args()

def main():
    args = parse_args()
    print("=" * 80)
    print("      [+] EDGESHIELD: LOG SEMANTIC ANALYZER (LSA) TRAINING PIPELINE      ")
    print("=" * 80)
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"[*] Target Hardware Device: {device.upper()}")
    
    # 1. Load Data
    print(f"[*] Loading telemetry data from {args.dataset_path}...")
    train_ds, test_ds = load_edgeshield_lsa_data(csv_path=args.dataset_path, num_samples=args.num_samples)
    print(f"[+] Loaded {len(train_ds)} train samples, {len(test_ds)} test samples.")
    
    # 2. Tokenizer & Model
    print(f"[*] Initializing model backbone: {args.model_name}...")
    try:
        tokenizer = AutoTokenizer.from_pretrained(args.model_name, use_fast=True)
    except Exception:
        tokenizer = AutoTokenizer.from_pretrained("microsoft/deberta-v3-small", use_fast=True)
        
    num_labels = len(TECHNIQUE_TO_ID)
    model = AutoModelForSequenceClassification.from_pretrained(
        "microsoft/deberta-v3-small", 
        num_labels=num_labels,
        ignore_mismatched_sizes=True
    ).to(device)
    
    # Tokenize dataset
    def tokenize_fn(batch):
        return tokenizer(batch["formatted_text"], truncation=True, max_length=512, padding="max_length")
        
    train_tokenized = train_ds.map(tokenize_fn, batched=True)
    train_tokenized.set_format(type="torch", columns=["input_ids", "attention_mask", "label"])
    
    train_loader = DataLoader(train_tokenized, batch_size=args.batch_size, shuffle=True)
    
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=0.01)
    total_steps = len(train_loader) * args.epochs
    scheduler = get_linear_schedule_with_warmup(optimizer, num_warmup_steps=int(total_steps * 0.1), num_training_steps=total_steps)
    
    ce_loss_fn = nn.CrossEntropyLoss()
    contrastive_fn = SupervisedContrastiveLoss(temperature=0.07) if args.use_contrastive else None
    
    print(f"[*] Beginning Training ({args.epochs} epochs, {total_steps} total steps)...")
    model.train()
    start_time = time.time()
    
    step = 0
    for epoch in range(1, args.epochs + 1):
        epoch_loss = 0.0
        for batch in train_loader:
            step += 1
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels = batch["label"].to(device)
            
            optimizer.zero_grad()
            outputs = model(input_ids=input_ids, attention_mask=attention_mask, output_hidden_states=True)
            logits = outputs.logits
            
            ce_loss = ce_loss_fn(logits, labels)
            
            if contrastive_fn and hasattr(outputs, "hidden_states") and outputs.hidden_states is not None:
                pooled_embeds = outputs.hidden_states[-1][:, 0, :] # [CLS] embedding
                cl_loss = contrastive_fn(pooled_embeds, labels)
                total_loss = ce_loss + 0.3 * cl_loss
            else:
                total_loss = ce_loss
                
            total_loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()
            scheduler.step()
            
            epoch_loss += total_loss.item()
            
            if step % 20 == 0 or step == total_steps:
                print(f"  [Epoch {epoch}/{args.epochs} | Step {step}/{total_steps}] Loss: {total_loss.item():.4f} | LR: {scheduler.get_last_lr()[0]:.2e}")

    elapsed = time.time() - start_time
    print(f"[+] LSA Training finished in {elapsed:.2f} seconds.")
    
    # Save Model Checkpoint
    os.makedirs(args.output_dir, exist_ok=True)
    model.save_pretrained(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)
    print(f"[+] Model checkpoint and tokenizer saved to: {args.output_dir}")

if __name__ == "__main__":
    main()
