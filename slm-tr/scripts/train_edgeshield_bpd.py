"""
EdgeShield: BPD (Behavioral Pattern Detector) Training CLI Script
Trains the SLM backbone and Attention-Based Threat Scoring Head for Ransomware & Pre-Encryption detection.
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

from edgeshield.taxonomy import TECHNIQUE_TO_ID, ID_TO_TECHNIQUE, BPD_TECHNIQUES
from edgeshield.bpd.detector import AttentionThreatScoringHead, BehavioralPatternDetector
from edgeshield.data.loader import load_edgeshield_bpd_data

def parse_args():
    parser = argparse.ArgumentParser(description="Train EdgeShield Behavioral Pattern Detector (BPD)")
    parser.add_argument("--model_name", type=str, default="microsoft/deberta-v3-small", help="Base SLM model identifier")
    parser.add_argument("--dataset_path", type=str, default="data/ransomware_behavioral_traces.csv", help="Path to telemetry dataset")
    parser.add_argument("--output_dir", type=str, default="models/edgeshield_bpd", help="Directory to save trained weights")
    parser.add_argument("--epochs", type=int, default=3, help="Number of training epochs")
    parser.add_argument("--batch_size", type=int, default=16, help="Training batch size")
    parser.add_argument("--lr", type=float, default=3e-5, help="Learning rate")
    parser.add_argument("--num_samples", type=int, default=1200, help="Number of samples to train on")
    return parser.parse_args()

def main():
    args = parse_args()
    print("=" * 80)
    print("      [+] EDGESHIELD: BEHAVIORAL PATTERN DETECTOR (BPD) TRAINING PIPELINE      ")
    print("=" * 80)
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"[*] Target Hardware Device: {device.upper()}")
    
    # 1. Load Data
    print(f"[*] Loading ransomware behavioral traces from {args.dataset_path}...")
    train_ds, test_ds = load_edgeshield_bpd_data(csv_path=args.dataset_path, num_samples=args.num_samples)
    print(f"[+] Loaded {len(train_ds)} train samples, {len(test_ds)} test samples.")
    
    # 2. Tokenizer & Models
    print(f"[*] Initializing model backbone and attention scoring head: {args.model_name}...")
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
    
    scoring_head = AttentionThreatScoringHead(hidden_dim=model.config.hidden_size).to(device)
    
    # Tokenize dataset
    def tokenize_fn(batch):
        return tokenizer(batch["formatted_text"], truncation=True, max_length=512, padding="max_length")
        
    train_tokenized = train_ds.map(tokenize_fn, batched=True)
    train_tokenized.set_format(type="torch", columns=["input_ids", "attention_mask", "label"])
    
    train_loader = DataLoader(train_tokenized, batch_size=args.batch_size, shuffle=True)
    
    params = list(model.parameters()) + list(scoring_head.parameters())
    optimizer = torch.optim.AdamW(params, lr=args.lr, weight_decay=0.01)
    total_steps = len(train_loader) * args.epochs
    scheduler = get_linear_schedule_with_warmup(optimizer, num_warmup_steps=int(total_steps * 0.1), num_training_steps=total_steps)
    
    ce_loss_fn = nn.CrossEntropyLoss()
    bce_loss_fn = nn.BCELoss()
    
    print(f"[*] Beginning Training ({args.epochs} epochs, {total_steps} total steps)...")
    model.train()
    scoring_head.train()
    start_time = time.time()
    
    step = 0
    for epoch in range(1, args.epochs + 1):
        for batch in train_loader:
            step += 1
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels = batch["label"].to(device)
            
            # Binary threat target: 0 if benign, 1 if any ransomware technique
            threat_binary_target = (labels != TECHNIQUE_TO_ID.get("BENIGN_NORMAL", 0)).float().unsqueeze(1)
            
            optimizer.zero_grad()
            outputs = model(input_ids=input_ids, attention_mask=attention_mask, output_hidden_states=True)
            logits = outputs.logits
            
            ce_loss = ce_loss_fn(logits, labels)
            
            last_hidden = outputs.hidden_states[-1]
            threat_pred, _ = scoring_head(last_hidden, attention_mask)
            threat_loss = bce_loss_fn(threat_pred, threat_binary_target)
            
            total_loss = ce_loss + threat_loss
            total_loss.backward()
            
            torch.nn.utils.clip_grad_norm_(params, max_norm=1.0)
            optimizer.step()
            scheduler.step()
            
            if step % 20 == 0 or step == total_steps:
                print(f"  [Epoch {epoch}/{args.epochs} | Step {step}/{total_steps}] Loss: {total_loss.item():.4f} (CE: {ce_loss.item():.4f}, Threat: {threat_loss.item():.4f})")

    elapsed = time.time() - start_time
    print(f"[+] BPD Training finished in {elapsed:.2f} seconds.")
    
    # Save Model Checkpoints
    os.makedirs(args.output_dir, exist_ok=True)
    model.save_pretrained(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)
    torch.save(scoring_head.state_dict(), os.path.join(args.output_dir, "scoring_head.pt"))
    print(f"[+] BPD Model & Attention Scoring Head saved to: {args.output_dir}")

if __name__ == "__main__":
    main()
