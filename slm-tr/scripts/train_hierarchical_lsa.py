"""
EdgeShield: Hierarchical Dual-Head Training CLI Script
Trains the Hierarchical SLM on Multi-Dataset Corpus (LMD-2023 + Windows-APT + Mordor):
  - Primary Level 1: Binary Threat Interception (Normal vs Malicious Lateral Movement)
  - Auxiliary Level 2: Granular ATT&CK Subtype Attribution (EoRS, EoHT, LotL, Tool Transfer, Remote Exploit)
"""

import os
import sys
import argparse
import time
import json
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from transformers import AutoTokenizer, get_linear_schedule_with_warmup
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from edgeshield.lsa.hierarchical_model import HierarchicalThreatDetector
from edgeshield.data.multi_dataset_loader import load_hierarchical_multi_dataset, SUBTYPE_MAP

def parse_args():
    parser = argparse.ArgumentParser(description="Train EdgeShield Hierarchical Dual-Head Threat Detector")
    parser.add_argument("--model_name", type=str, default="microsoft/deberta-v3-small", help="Base SLM model identifier")
    parser.add_argument("--lmd_path", type=str, default="data/lmd_2023_dataset.csv", help="Path to LMD-2023 CSV")
    parser.add_argument("--windows_apt_dir", type=str, default="data/windows_apt", help="Path to Windows-APT directory")
    parser.add_argument("--mordor_dir", type=str, default="data", help="Path to Mordor directory")
    parser.add_argument("--output_dir", type=str, default="models/edgeshield_hierarchical_lsa", help="Directory to save trained weights")
    parser.add_argument("--epochs", type=int, default=3, help="Number of training epochs")
    parser.add_argument("--batch_size", type=int, default=16, help="Training batch size")
    parser.add_argument("--lr", type=float, default=3e-5, help="Learning rate")
    parser.add_argument("--train_samples", type=int, default=15000, help="Number of training window samples")
    parser.add_argument("--test_samples", type=int, default=3000, help="Number of test window samples")
    parser.add_argument("--max_length", type=int, default=256, help="Maximum sequence length")
    parser.add_argument("--alpha", type=float, default=0.5, help="Weight for auxiliary subtype loss")
    parser.add_argument("--device", type=str, default="auto", choices=["auto", "cuda", "dml", "cpu"], help="Hardware device")
    return parser.parse_args()

def main():
    args = parse_args()
    print("=" * 80)
    print("   [+] EDGESHIELD: HIERARCHICAL DUAL-HEAD TRAINING PIPELINE (MULTI-DATASET)")
    print("   Primary: Binary Threat Interception | Auxiliary: MITRE TTP Attribution")
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
                    device_name = f"DirectML GPU ({torch_directml.device_name(0).strip()})"
                else:
                    device = torch.device("cpu")
                    device_name = f"CPU ({os.cpu_count() or 8} Cores)"
            except Exception:
                device = torch.device("cpu")
                device_name = f"CPU ({os.cpu_count() or 8} Cores)"
    elif args.device == "cuda":
        device = torch.device("cuda")
        device_name = f"NVIDIA CUDA ({torch.cuda.get_device_name(0)})"
    else:
        device = torch.device("cpu")
        device_name = f"CPU ({os.cpu_count() or 8} Cores)"
        
    print(f"[*] Target Hardware Device: {device_name}", flush=True)

    # 1. Load Multi-Dataset Unified Corpus
    print("[*] Loading and formulating multi-dataset sliding windows...")
    train_ds, test_ds = load_hierarchical_multi_dataset(
        lmd_path=args.lmd_path,
        windows_apt_dir=args.windows_apt_dir,
        mordor_dir=args.mordor_dir,
        total_train_samples=args.train_samples,
        total_test_samples=args.test_samples
    )
    print(f"[+] Multi-Dataset Train Windows: {len(train_ds)} | Test Windows: {len(test_ds)}")

    # 2. Tokenizer & Hierarchical Model
    print(f"[*] Initializing tokenizer and hierarchical backbone: {args.model_name}...")
    tokenizer = AutoTokenizer.from_pretrained(args.model_name, use_fast=True)
    model = HierarchicalThreatDetector(
        model_name_or_path=args.model_name,
        num_subtypes=len(SUBTYPE_MAP)
    ).to(device)

    def collate_fn(batch):
        texts = [item["formatted_text"] for item in batch]
        encoded = tokenizer(texts, padding=True, truncation=True, max_length=args.max_length, return_tensors="pt")
        threat_labels = torch.tensor([item["threat_label"] for item in batch], dtype=torch.long)
        subtype_labels = torch.tensor([item["subtype_label"] for item in batch], dtype=torch.long)
        return {
            "input_ids": encoded["input_ids"],
            "attention_mask": encoded["attention_mask"],
            "threat_labels": threat_labels,
            "subtype_labels": subtype_labels
        }

    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True, collate_fn=collate_fn)
    test_loader = DataLoader(test_ds, batch_size=args.batch_size, shuffle=False, collate_fn=collate_fn)

    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=0.01)
    total_steps = len(train_loader) * args.epochs
    scheduler = get_linear_schedule_with_warmup(optimizer, num_warmup_steps=int(total_steps * 0.1), num_training_steps=total_steps)

    print(f"[*] Commencing Training ({args.epochs} epochs, {total_steps} steps, batch_size={args.batch_size})...", flush=True)
    start_t = time.time()
    
    for epoch in range(1, args.epochs + 1):
        model.train()
        epoch_loss = 0.0
        for step, batch in enumerate(train_loader, start=1):
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            threat_labels = batch["threat_labels"].to(device)
            subtype_labels = batch["subtype_labels"].to(device)

            optimizer.zero_grad()
            out = model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                threat_labels=threat_labels,
                subtype_labels=subtype_labels,
                alpha=args.alpha
            )
            loss = out["loss"]
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()
            scheduler.step()

            epoch_loss += loss.item()
            global_step = (epoch - 1) * len(train_loader) + step

            if global_step % 25 == 0 or global_step == total_steps:
                ld = out["loss_dict"]
                print(f"  [Epoch {epoch}/{args.epochs} | Step {global_step}/{total_steps}] Loss: {ld['total_loss']:.4f} (Threat: {ld['ce_threat']:.4f}, Subtype: {ld['ce_subtype']:.4f}, SCL: {ld['scl_loss']:.4f})", flush=True)

    train_time = time.time() - start_t
    print(f"[+] Training completed in {train_time:.2f} seconds.")

    # 3. Live Empirical Evaluation on Held-Out Multi-Dataset Test Partition
    print("\n" + "=" * 80)
    print("   [+] EVALUATING HELD-OUT MULTI-DATASET TEST PARTITION")
    print("=" * 80)
    model.eval()
    
    all_threat_preds = []
    all_threat_targets = []
    all_subtype_preds = []
    all_subtype_targets = []
    eval_latencies = []

    with torch.no_grad():
        for batch in test_loader:
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            
            t0 = time.perf_counter()
            out = model(input_ids=input_ids, attention_mask=attention_mask)
            t_batch = (time.perf_counter() - t0) * 1000.0 / len(input_ids)
            eval_latencies.append(t_batch)

            t_preds = torch.argmax(out["threat_logits"], dim=-1).cpu().numpy()
            s_preds = torch.argmax(out["subtype_logits"], dim=-1).cpu().numpy()

            all_threat_preds.extend(t_preds)
            all_threat_targets.extend(batch["threat_labels"].numpy())
            all_subtype_preds.extend(s_preds)
            all_subtype_targets.extend(batch["subtype_labels"].numpy())

    # Level 1 Metrics: Binary Threat Interception
    t_acc = accuracy_score(all_threat_targets, all_threat_preds) * 100
    t_p, t_r, t_f1, _ = precision_recall_fscore_support(all_threat_targets, all_threat_preds, average="binary", zero_division=0)
    t_cm = confusion_matrix(all_threat_targets, all_threat_preds)
    tn, fp, fn, tp = t_cm.ravel()
    fpr = (fp / (fp + tn)) * 100.0 if (fp + tn) > 0 else 0.0

    # Level 2 Metrics: Subtype Attribution (on actual attacks)
    attack_mask = [t == 1 for t in all_threat_targets]
    sub_targets = [all_subtype_targets[i] for i, m in enumerate(attack_mask) if m]
    sub_preds = [all_subtype_preds[i] for i, m in enumerate(attack_mask) if m]
    sub_acc = accuracy_score(sub_targets, sub_preds) * 100 if len(sub_targets) > 0 else 0.0

    print("-" * 70)
    print("  [+] LEVEL 1 (PRIMARY): BINARY THREAT INTERCEPTION METRICS:")
    print(f"    • Threat Accuracy:                 {t_acc:.2f}%")
    print(f"    • Attack Recall (Sensitivity):     {t_r*100:.2f}% ({tp}/{tp+fn} attacks intercepted)")
    print(f"    • Threat Precision:                {t_p*100:.2f}%")
    print(f"    • Threat F1-Score:                 {t_f1*100:.2f}%")
    print(f"    • False Positive Rate (FPR):        {fpr:.2f}% ({fp}/{fp+tn} false alerts)")
    print(f"    • Confusion Matrix: [TN={tn}, FP={fp}, FN={fn}, TP={tp}]")
    print(f"    • Mean Inference Latency:          {float(torch.tensor(eval_latencies).mean()):.2f} ms")
    print("-" * 70)
    print("  [+] LEVEL 2 (AUXILIARY): MITRE TTP SUBTYPE ATTRIBUTION:")
    print(f"    • Subtype Classification Accuracy: {sub_acc:.2f}%")
    print("-" * 70)

    # 4. Save Trained Checkpoints
    os.makedirs(args.output_dir, exist_ok=True)
    torch.save(model.state_dict(), os.path.join(args.output_dir, "hierarchical_model.pt"))
    tokenizer.save_pretrained(args.output_dir)
    
    # Save evaluation summary JSON
    results = {
        "model_name": args.model_name,
        "train_samples": len(train_ds),
        "test_samples": len(test_ds),
        "level1_threat_accuracy": round(t_acc, 2),
        "level1_threat_recall": round(t_r * 100, 2),
        "level1_threat_precision": round(t_p * 100, 2),
        "level1_threat_f1": round(t_f1 * 100, 2),
        "level1_fpr": round(fpr, 2),
        "level2_subtype_accuracy": round(sub_acc, 2),
        "mean_latency_ms": round(float(torch.tensor(eval_latencies).mean()), 2),
        "confusion_matrix": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
        "train_seconds": round(train_time, 2)
    }
    with open(os.path.join(args.output_dir, "hierarchical_evaluation_summary.json"), "w") as f:
        json.dump(results, f, indent=2)
    print(f"[+] Saved model weights and evaluation summary to: {args.output_dir}")

if __name__ == "__main__":
    main()
