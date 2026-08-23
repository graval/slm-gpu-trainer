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

# Maximize multi-threaded performance across all CPU cores (Intel Core Ultra 7 255H - 16 Cores)
cpu_cores = os.cpu_count() or 16
torch.set_num_threads(cpu_cores)
os.environ["OMP_NUM_THREADS"] = str(cpu_cores)
os.environ["MKL_NUM_THREADS"] = str(cpu_cores)

from torch.utils.data import DataLoader
from transformers import AutoTokenizer, AutoModelForSequenceClassification, get_linear_schedule_with_warmup

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from edgeshield.taxonomy import TECHNIQUE_TO_ID, ID_TO_TECHNIQUE, BPD_TECHNIQUES
from edgeshield.bpd.detector import AttentionThreatScoringHead, BehavioralPatternDetector
from edgeshield.data.loader import load_edgeshield_bpd_data

def parse_args():
    parser = argparse.ArgumentParser(description="Train EdgeShield Behavioral Pattern Detector (BPD)")
    parser.add_argument("--model_name", type=str, default="distilbert-base-uncased", help="Base SLM model identifier")
    parser.add_argument("--dataset_path", type=str, default="data/ransomware_behavioral_traces.csv", help="Path to telemetry dataset")
    parser.add_argument("--output_dir", type=str, default="models/edgeshield_bpd", help="Directory to save trained weights")
    parser.add_argument("--epochs", type=int, default=3, help="Number of training epochs")
    parser.add_argument("--batch_size", type=int, default=16, help="Training batch size")
    parser.add_argument("--lr", type=float, default=5e-5, help="Learning rate")
    parser.add_argument("--num_samples", type=int, default=5000, help="Number of samples to train on")
    parser.add_argument("--test_samples", type=int, default=1000, help="Number of test samples to evaluate on")
    parser.add_argument("--max_length", type=int, default=256, help="Maximum sequence length")
    parser.add_argument("--threat_weight", type=float, default=0.5, help="Weight for threat score MSE loss")
    parser.add_argument("--device", type=str, default="auto", choices=["auto", "cuda", "dml", "cpu"], help="Hardware device")
    return parser.parse_args()

def main():
    args = parse_args()
    print("=" * 80)
    print("      [+] EDGESHIELD: BEHAVIORAL PATTERN DETECTOR (BPD) TRAINING PIPELINE      ")
    print("=" * 80)
    
    if args.device == "auto":
        if torch.cuda.is_available():
            device = torch.device("cuda")
            device_name = f"NVIDIA CUDA ({torch.cuda.get_device_name(0)})"
        else:
            try:
                import torch_directml
                if torch_directml.is_available() and torch_directml.device_count() > 0:
                    device = torch_directml.device(0)
                    dml_name = torch_directml.device_name(0).strip()
                    device_name = f"DirectML GPU ({dml_name})"
                else:
                    device = torch.device("cpu")
                    device_name = f"CPU ({cpu_cores} Cores)"
            except Exception:
                device = torch.device("cpu")
                device_name = f"CPU ({cpu_cores} Cores)"
    elif args.device == "dml":
        import torch_directml
        device = torch_directml.device(0)
        dml_name = torch_directml.device_name(0).strip()
        device_name = f"DirectML GPU ({dml_name})"
    elif args.device == "cuda":
        device = torch.device("cuda")
        device_name = f"NVIDIA CUDA ({torch.cuda.get_device_name(0)})"
    else:
        device = torch.device("cpu")
        device_name = f"CPU ({cpu_cores} Cores)"
        
    print(f"[*] Target Hardware Device: {device_name}", flush=True)
    
    # 1. Load Data
    print(f"[*] Loading ransomware behavioral traces from {args.dataset_path}...")
    train_ds, test_ds = load_edgeshield_bpd_data(
        csv_path=args.dataset_path, 
        train_samples=args.num_samples, 
        test_samples=args.test_samples
    )
    print(f"[+] Loaded {len(train_ds)} train samples, {len(test_ds)} test samples.")
    
    # 2. Tokenizer & Models
    print(f"[*] Initializing model backbone and attention scoring head: {args.model_name}...")
    try:
        tokenizer = AutoTokenizer.from_pretrained(args.model_name, use_fast=True)
    except Exception:
        tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased", use_fast=True)
        
    num_labels = len(TECHNIQUE_TO_ID)
    try:
        model = AutoModelForSequenceClassification.from_pretrained(
            args.model_name, 
            num_labels=num_labels,
            ignore_mismatched_sizes=True
        ).to(device)
    except Exception:
        model = AutoModelForSequenceClassification.from_pretrained(
            "distilbert-base-uncased", 
            num_labels=num_labels,
            ignore_mismatched_sizes=True
        ).to(device)
    
    scoring_head = AttentionThreatScoringHead(hidden_dim=getattr(model.config, "hidden_size", getattr(model.config, "dim", 768))).to(device)
    
    # Dynamic tokenization and batch padding
    def tokenize_fn(batch):
        return tokenizer(batch["formatted_text"], truncation=True, max_length=args.max_length)
        
    train_tokenized = train_ds.map(tokenize_fn, batched=True)
    test_tokenized = test_ds.map(tokenize_fn, batched=True)
    
    def collate_fn(batch):
        input_ids = [torch.tensor(item["input_ids"]) for item in batch]
        attention_mask = [torch.tensor(item["attention_mask"]) for item in batch]
        labels = torch.tensor([item["label"] for item in batch], dtype=torch.long)
        
        pad_id = tokenizer.pad_token_id if tokenizer.pad_token_id is not None else 0
        padded_inputs = torch.nn.utils.rnn.pad_sequence(input_ids, batch_first=True, padding_value=pad_id)
        padded_mask = torch.nn.utils.rnn.pad_sequence(attention_mask, batch_first=True, padding_value=0)
        return {
            "input_ids": padded_inputs,
            "attention_mask": padded_mask,
            "labels": labels
        }
    
    train_loader = DataLoader(
        train_tokenized, 
        batch_size=args.batch_size, 
        shuffle=True, 
        collate_fn=collate_fn
    )
    
    params = list(model.parameters()) + list(scoring_head.parameters())
    optimizer = torch.optim.AdamW(params, lr=args.lr, weight_decay=0.01, foreach=False)
    total_steps = len(train_loader) * args.epochs
    scheduler = get_linear_schedule_with_warmup(optimizer, num_warmup_steps=int(total_steps * 0.1), num_training_steps=total_steps)
    
    ce_loss_fn = nn.CrossEntropyLoss()
    bce_loss_fn = nn.BCELoss()
    
    print(f"[*] Beginning Training ({args.epochs} epochs, {total_steps} total steps)...", flush=True)
    model.train()
    scoring_head.train()
    start_time = time.time()
    
    step = 0
    for epoch in range(1, args.epochs + 1):
        for batch in train_loader:
            step += 1
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels = batch["labels"].to(device)
            
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
            
            if step % 10 == 0 or step == total_steps:
                print(f"  [Epoch {epoch}/{args.epochs} | Step {step}/{total_steps}] Loss: {total_loss.item():.4f} (CE: {ce_loss.item():.4f}, Threat: {threat_loss.item():.4f})", flush=True)
                
                # Write live progress JSON for UI monitor
                prog_data = {
                    "status": "training" if step < total_steps else "completed",
                    "model_name": "EdgeShield-BPD (DistilBERT + Attention Scoring)",
                    "variant_label": "Stream B: Behavioral Pattern Detector (Ransomware Multi-Stage)",
                    "current_epoch": epoch,
                    "total_epochs": args.epochs,
                    "current_step": step,
                    "total_steps": total_steps,
                    "loss": round(total_loss.item(), 4),
                    "ce_loss": round(ce_loss.item(), 4),
                    "threat_loss": round(threat_loss.item(), 4),
                    "learning_rate": scheduler.get_last_lr()[0],
                    "timestamp": time.time(),
                    "device": str(device)
                }
                for out_f in ["training_progress.json", os.path.join(args.output_dir, "training_progress.json")]:
                    try:
                        os.makedirs(os.path.dirname(out_f) or ".", exist_ok=True)
                        with open(out_f, "w") as pf:
                            json.dump(prog_data, pf, indent=2)
                    except Exception:
                        pass

    elapsed = time.time() - start_time
    print(f"[+] BPD Training finished in {elapsed:.2f} seconds.", flush=True)
    
    # Save Model Checkpoints
    os.makedirs(args.output_dir, exist_ok=True)
    model.cpu().save_pretrained(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)
    torch.save(scoring_head.cpu().state_dict(), os.path.join(args.output_dir, "scoring_head.pt"))
    print(f"[+] BPD Model & Attention Scoring Head saved to: {args.output_dir}")
    
    # Write final completed status
    final_prog = {
        "status": "completed",
        "model_name": "EdgeShield-BPD (DistilBERT + Attention Scoring)",
        "variant_label": "Stream B: Behavioral Pattern Detector (Ransomware Multi-Stage)",
        "current_epoch": args.epochs,
        "total_epochs": args.epochs,
        "current_step": total_steps,
        "total_steps": total_steps,
        "elapsed_seconds": round(elapsed, 2),
        "timestamp": time.time()
    }
    for out_f in ["training_progress.json", os.path.join(args.output_dir, "training_progress.json")]:
        try:
            with open(out_f, "w") as pf:
                json.dump(final_prog, pf, indent=2)
        except Exception:
            pass

if __name__ == "__main__":
    main()
