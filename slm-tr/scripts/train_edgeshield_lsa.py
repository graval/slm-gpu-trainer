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

# Maximize multi-threaded performance across all CPU cores (Intel Core Ultra 7 255H - 16 Cores)
cpu_cores = os.cpu_count() or 16
torch.set_num_threads(cpu_cores)
os.environ["OMP_NUM_THREADS"] = str(cpu_cores)
os.environ["MKL_NUM_THREADS"] = str(cpu_cores)

from torch.utils.data import DataLoader
from transformers import AutoTokenizer, AutoModelForSequenceClassification, get_linear_schedule_with_warmup

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from edgeshield.taxonomy import TECHNIQUE_TO_ID, ID_TO_TECHNIQUE, LSA_TECHNIQUES
from edgeshield.lsa.analyzer import SupervisedContrastiveLoss, LogSemanticAnalyzer
from edgeshield.data.loader import load_edgeshield_lsa_data

def parse_args():
    parser = argparse.ArgumentParser(description="Train EdgeShield Log Semantic Analyzer (LSA)")
    parser.add_argument("--model_name", type=str, default="distilbert-base-uncased", help="Base SLM model identifier")
    parser.add_argument("--dataset_path", type=str, default="data/lmd_2023_dataset.csv", help="Path to telemetry dataset")
    parser.add_argument("--output_dir", type=str, default="models/edgeshield_lsa", help="Directory to save trained weights")
    parser.add_argument("--epochs", type=int, default=3, help="Number of training epochs")
    parser.add_argument("--batch_size", type=int, default=16, help="Training batch size")
    parser.add_argument("--lr", type=float, default=5e-5, help="Learning rate")
    parser.add_argument("--num_samples", type=int, default=12000, help="Number of samples to train on")
    parser.add_argument("--test_samples", type=int, default=2000, help="Number of test samples to evaluate on")
    parser.add_argument("--max_length", type=int, default=256, help="Maximum sequence length")
    parser.add_argument("--use_contrastive", action="store_true", default=True, help="Enable Phase 2 Contrastive Loss")
    parser.add_argument("--device", type=str, default="auto", choices=["auto", "cuda", "dml", "cpu"], help="Hardware device")
    return parser.parse_args()

def main():
    args = parse_args()
    print("=" * 80)
    print("      [+] EDGESHIELD: LOG SEMANTIC ANALYZER (LSA) TRAINING PIPELINE      ")
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
    print(f"[*] Loading telemetry data from {args.dataset_path}...")
    train_ds, test_ds = load_edgeshield_lsa_data(
        csv_path=args.dataset_path, 
        train_samples=args.num_samples, 
        test_samples=args.test_samples
    )
    print(f"[+] Loaded {len(train_ds)} train samples, {len(test_ds)} test samples.")
    
    # 2. Tokenizer & Model
    print(f"[*] Initializing model backbone: {args.model_name}...")
    try:
        tokenizer = AutoTokenizer.from_pretrained(args.model_name, use_fast=True)
    except Exception:
        tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased", use_fast=True)
        
    num_labels = 3
    id2label = {0: "Normal", 1: "EoRS", 2: "EoHT"}
    label2id = {"Normal": 0, "EoRS": 1, "EoHT": 2}
    try:
        model = AutoModelForSequenceClassification.from_pretrained(
            args.model_name, 
            num_labels=num_labels,
            id2label=id2label,
            label2id=label2id,
            ignore_mismatched_sizes=True
        ).to(device)
    except Exception:
        model = AutoModelForSequenceClassification.from_pretrained(
            "distilbert-base-uncased", 
            num_labels=num_labels,
            id2label=id2label,
            label2id=label2id,
            ignore_mismatched_sizes=True
        ).to(device)
    
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
    
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=0.01, foreach=False)
    total_steps = len(train_loader) * args.epochs
    scheduler = get_linear_schedule_with_warmup(optimizer, num_warmup_steps=int(total_steps * 0.1), num_training_steps=total_steps)
    
    ce_loss_fn = nn.CrossEntropyLoss()
    contrastive_fn = SupervisedContrastiveLoss(temperature=0.07) if args.use_contrastive else None
    
    use_amp = (device.type == "cuda")
    scaler = torch.cuda.amp.GradScaler(enabled=use_amp)
    
    print(f"[*] Beginning Training ({args.epochs} epochs, {total_steps} total steps, AMP={use_amp})...", flush=True)
    model.train()
    start_time = time.time()
    
    log_interval = max(20, total_steps // 40)
    step = 0
    for epoch in range(1, args.epochs + 1):
        epoch_loss = 0.0
        for batch in train_loader:
            step += 1
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels = batch["labels"].to(device)
            
            optimizer.zero_grad()
            with torch.cuda.amp.autocast(enabled=use_amp):
                outputs = model(input_ids=input_ids, attention_mask=attention_mask, output_hidden_states=True)
                logits = outputs.logits
                ce_loss = ce_loss_fn(logits, labels)
                
                if contrastive_fn and hasattr(outputs, "hidden_states") and outputs.hidden_states is not None:
                    pooled_embeds = outputs.hidden_states[-1][:, 0, :] # [CLS] embedding
                    cl_loss = contrastive_fn(pooled_embeds, labels)
                    cl_loss = torch.nan_to_num(cl_loss, nan=0.0, posinf=0.0, neginf=0.0)
                    total_loss = ce_loss + 0.3 * cl_loss
                else:
                    total_loss = ce_loss
                
            if use_amp:
                scaler.scale(total_loss).backward()
                scaler.unscale_(optimizer)
                torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
                scaler.step(optimizer)
                scaler.update()
            else:
                total_loss.backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
                optimizer.step()
                
            scheduler.step()
            epoch_loss += total_loss.item()
            
            if step % log_interval == 0 or step == total_steps:
                print(f"  [Epoch {epoch}/{args.epochs} | Step {step}/{total_steps}] Loss: {total_loss.item():.4f} | LR: {scheduler.get_last_lr()[0]:.2e}", flush=True)

    elapsed = time.time() - start_time
    print(f"[+] LSA Training finished in {elapsed:.2f} seconds.", flush=True)
    
    # Save Model Checkpoint
    os.makedirs(args.output_dir, exist_ok=True)
    model.cpu().save_pretrained(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)
    print(f"[+] Model checkpoint and tokenizer saved to: {args.output_dir}")
    
    # 4. Evaluation on Held-Out Test Set
    print("\n[*] Evaluating LSA Model on Balanced Held-Out Test Split...", flush=True)
    model.to(device)
    model.eval()
    test_loader = DataLoader(
        test_tokenized,
        batch_size=args.batch_size * 2,
        shuffle=False,
        collate_fn=collate_fn
    )
    
    all_preds = []
    all_targets = []
    with torch.no_grad():
        for batch in test_loader:
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels = batch["labels"].to(device)
            
            with torch.cuda.amp.autocast(enabled=use_amp):
                outputs = model(input_ids=input_ids, attention_mask=attention_mask)
            preds = torch.argmax(outputs.logits, dim=-1)
            all_preds.extend(preds.cpu().numpy().tolist())
            all_targets.extend(labels.cpu().numpy().tolist())
            
    from sklearn.metrics import accuracy_score, precision_recall_fscore_support
    acc = accuracy_score(all_targets, all_preds)
    p_macro, r_macro, f1_macro, _ = precision_recall_fscore_support(all_targets, all_preds, average="macro", zero_division=0)
    p_cls, r_cls, f1_cls, _ = precision_recall_fscore_support(all_targets, all_preds, average=None, labels=[0, 1, 2], zero_division=0)
    
    normal_indices = [i for i, t in enumerate(all_targets) if t == 0]
    fp_count = sum(1 for i in normal_indices if all_preds[i] != 0)
    fpr = (fp_count / len(normal_indices)) * 100.0 if normal_indices else 0.0
    
    attack_indices = [i for i, t in enumerate(all_targets) if t in (1, 2)]
    attack_detected = sum(1 for i in attack_indices if all_preds[i] in (1, 2))
    attack_recall = (attack_detected / len(attack_indices)) * 100.0 if attack_indices else 0.0
    
    print("=" * 70)
    print("           [+] LSA EVALUATION RESULTS (HELD-OUT BALANCED TEST SET)")
    print("=" * 70)
    print(f"  Overall Accuracy:            {acc * 100:.2f}%")
    print(f"  Macro F1-Score:              {f1_macro * 100:.2f}%")
    print(f"  Lateral Movement Recall:     {attack_recall:.2f}%  (Target: >96%)")
    print(f"  False Positive Rate (FPR):   {fpr:.2f}%  (Target: <0.20%)")
    print("-" * 70)
    print(f"  Class 0 [Normal]:            Precision={p_cls[0]*100:.2f}% | Recall={r_cls[0]*100:.2f}% | F1={f1_cls[0]*100:.2f}%")
    print(f"  Class 1 [EoRS]:              Precision={p_cls[1]*100:.2f}% | Recall={r_cls[1]*100:.2f}% | F1={f1_cls[1]*100:.2f}%")
    print(f"  Class 2 [EoHT]:              Precision={p_cls[2]*100:.2f}% | Recall={r_cls[2]*100:.2f}% | F1={f1_cls[2]*100:.2f}%")
    print("=" * 70)
    
    metrics = {
        "accuracy": round(float(acc * 100), 2),
        "macro_f1": round(float(f1_macro * 100), 2),
        "macro_precision": round(float(p_macro * 100), 2),
        "macro_recall": round(float(r_macro * 100), 2),
        "lateral_movement_recall": round(float(attack_recall), 2),
        "false_positive_rate": round(float(fpr), 2),
        "class_metrics": {
            "Normal": {"precision": round(float(p_cls[0]*100), 2), "recall": round(float(r_cls[0]*100), 2), "f1": round(float(f1_cls[0]*100), 2)},
            "EoRS": {"precision": round(float(p_cls[1]*100), 2), "recall": round(float(r_cls[1]*100), 2), "f1": round(float(f1_cls[1]*100), 2)},
            "EoHT": {"precision": round(float(p_cls[2]*100), 2), "recall": round(float(r_cls[2]*100), 2), "f1": round(float(f1_cls[2]*100), 2)},
        },
        "training_time_seconds": round(elapsed, 2)
    }
    with open(os.path.join(args.output_dir, "eval_metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"[+] LSA Evaluation metrics written to: {os.path.join(args.output_dir, 'eval_metrics.json')}")

if __name__ == "__main__":
    main()
