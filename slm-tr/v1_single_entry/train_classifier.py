"""
v1 - Single Entry Sequence Classification Training Pipeline
Fine-tunes encoder SLMs (DeBERTa-v3-small / DistilBERT) on isolated single event logs (K=1).
"""

import os
import sys
import argparse
import time
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import numpy as np
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
import torch
from torch.utils.data import DataLoader
from transformers import (
    AutoTokenizer, 
    AutoModelForSequenceClassification, 
    TrainingArguments, 
    Trainer,
    DataCollatorWithPadding
)
from v1_single_entry.data_loader import load_v1_dataset

def parse_args():
    parser = argparse.ArgumentParser(description="Train v1 (Single Entry) SLM Classifier")
    parser.add_argument("--csv_path", type=str, default="data/lmd_2023_dataset.csv", help="Dataset CSV path")
    parser.add_argument("--base_model", type=str, default="microsoft/deberta-v3-small", help="Pretrained base model")
    parser.add_argument("--output_dir", type=str, default="models/deberta-lateral-movement-v1_single_entry", help="Save directory")
    parser.add_argument("--epochs", type=int, default=3, help="Training epochs")
    parser.add_argument("--batch_size", type=int, default=16, help="Batch size")
    parser.add_argument("--lr", type=float, default=2e-5, help="Learning rate")
    parser.add_argument("--max_length", type=int, default=128, help="Max token length")
    parser.add_argument("--max_train_samples", type=int, default=None, help="Cap training dataset size for rapid testing")
    parser.add_argument("--max_val_samples", type=int, default=None, help="Cap validation dataset size for rapid testing")
    return parser.parse_args()

def compute_metrics(eval_pred):
    logits, labels = eval_pred
    preds = np.argmax(logits, axis=-1)
    acc = accuracy_score(labels, preds)
    precision, recall, f1, _ = precision_recall_fscore_support(labels, preds, average='macro', zero_division=0)
    return {"accuracy": acc, "f1_macro": f1, "precision": precision, "recall": recall}

def main():
    args = parse_args()
    print("=" * 70)
    print("   [v1 - SINGLE ENTRY] SLM SEQUENCE CLASSIFIER TRAINING PIPELINE   ")
    print("=" * 70)
    
    os.makedirs(args.output_dir, exist_ok=True)
    train_dataset, val_dataset = load_v1_dataset(args.csv_path, balance_classes=True)
    
    if args.max_train_samples and len(train_dataset) > args.max_train_samples:
        train_dataset = train_dataset.select(range(args.max_train_samples))
    if args.max_val_samples and len(val_dataset) > args.max_val_samples:
        val_dataset = val_dataset.select(range(args.max_val_samples))
        
    tokenizer = AutoTokenizer.from_pretrained(args.base_model, use_fast=True)
    
    def tokenize_fn(examples):
        return tokenizer(examples['formatted_text'], truncation=True, max_length=args.max_length)
        
    tokenized_train = train_dataset.map(tokenize_fn, batched=True).rename_column("normalized_label", "label")
    tokenized_val = val_dataset.map(tokenize_fn, batched=True).rename_column("normalized_label", "label")
    
    model = AutoModelForSequenceClassification.from_pretrained(args.base_model, num_labels=3)
    
    training_args = TrainingArguments(
        output_dir=args.output_dir,
        learning_rate=args.lr,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        num_train_epochs=args.epochs,
        weight_decay=0.01,
        eval_strategy="epoch",
        save_strategy="epoch",
        logging_steps=10,
        load_best_model_at_end=True,
        report_to="none"
    )
    
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_train,
        eval_dataset=tokenized_val,
        tokenizer=tokenizer,
        data_collator=DataCollatorWithPadding(tokenizer=tokenizer),
        compute_metrics=compute_metrics
    )
    
    print("[*] Starting v1 fine-tuning...")
    trainer.train()
    trainer.save_model(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)
    print(f"[+] v1 Model saved successfully to: {args.output_dir}")

if __name__ == "__main__":
    main()
