import os
import sys
import argparse
import numpy as np
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
import torch
torch.set_num_threads(2) # Limit CPU threads to optimize context switching
import time
import json
from transformers import (
    AutoTokenizer, 
    AutoModelForSequenceClassification, 
    TrainingArguments, 
    Trainer,
    DataCollatorWithPadding,
    TrainerCallback
)
from data.loader import load_lmd_dataset

class ProgressCallback(TrainerCallback):
    def __init__(self, output_dir, model_name):
        self.output_dir = output_dir
        self.model_name = model_name
        self.start_time = time.time()
        self.history = []
        
        # Primary progress file inside model directory
        self.progress_file = os.path.join(output_dir, "training_progress.json")
        
        # Secondary progress file inside external folder (for shared access in Docker / Dashboard)
        self.external_progress_file = "external/training_progress.json"

    def on_log(self, args, state, control, logs=None, **kwargs):
        if state.is_world_process_zero:
            logs = logs or {}
            current_loss = logs.get("loss", 0.0)
            current_lr = logs.get("learning_rate", 0.0)
            
            # Record log state in history
            step_record = {
                "step": state.global_step,
                "loss": current_loss,
                "learning_rate": current_lr,
                "epoch": state.epoch
            }
            if state.global_step > 0:
                self.history.append(step_record)
                
            elapsed_time = time.time() - self.start_time
            
            # Calculate ETA
            eta_seconds = 0.0
            if state.global_step > 0:
                steps_per_sec = state.global_step / elapsed_time
                remaining_steps = state.max_steps - state.global_step
                eta_seconds = remaining_steps / steps_per_sec
                
            progress = {
                "model_name": self.model_name,
                "status": "training",
                "current_step": state.global_step,
                "max_steps": state.max_steps,
                "epoch": round(state.epoch, 2) if state.epoch else 0.0,
                "loss": current_loss,
                "learning_rate": current_lr,
                "elapsed_time": round(elapsed_time, 2),
                "eta_seconds": round(eta_seconds, 2),
                "history": self.history
            }
            
            self._save_progress(progress)
            
    def on_train_end(self, args, state, control, **kwargs):
        if state.is_world_process_zero:
            elapsed_time = time.time() - self.start_time
            progress = {
                "model_name": self.model_name,
                "status": "completed",
                "current_step": state.global_step,
                "max_steps": state.max_steps,
                "epoch": round(state.epoch, 2) if state.epoch else 3.0,
                "loss": self.history[-1]["loss"] if self.history else 0.0,
                "learning_rate": 0.0,
                "elapsed_time": round(elapsed_time, 2),
                "eta_seconds": 0.0,
                "history": self.history
            }
            self._save_progress(progress)
            
    def _save_progress(self, progress):
        try:
            # Save to model directory
            os.makedirs(os.path.dirname(self.progress_file), exist_ok=True)
            with open(self.progress_file, "w") as f:
                json.dump(progress, f, indent=4)
                
            # Save to external folder if exists
            ext_dir = os.path.dirname(self.external_progress_file)
            if os.path.exists(ext_dir):
                with open(self.external_progress_file, "w") as f:
                    json.dump(progress, f, indent=4)
        except Exception as e:
            pass

def parse_args():
    parser = argparse.ArgumentParser(description="Train DeBERTa SLM for Lateral Movement Classification")
    parser.add_argument("--csv_path", type=str, default="data/lmd_2023_dataset.csv", help="Path to the LMD-2023 CSV file")
    parser.add_argument("--model_name", type=str, default="microsoft/deberta-v3-small", help="Hugging Face base model")
    parser.add_argument("--output_dir", type=str, default="models/deberta-lateral-movement", help="Where to save the trained model")
    parser.add_argument("--epochs", type=int, default=3, help="Number of training epochs")
    parser.add_argument("--batch_size", type=int, default=8, help="Batch size for training")
    parser.add_argument("--learning_rate", type=float, default=2e-5, help="Learning rate")
    parser.add_argument("--balance_classes", action="store_true", default=True, help="Balance dataset classes via downsampling")
    return parser.parse_args()

def compute_metrics(eval_pred):
    """Computes precision, recall, F1, and accuracy for evaluation."""
    logits, labels = eval_pred
    predictions = np.argmax(logits, axis=-1)
    
    # Calculate global metrics
    accuracy = accuracy_score(labels, predictions)
    precision_macro, recall_macro, f1_macro, _ = precision_recall_fscore_support(
        labels, predictions, average='macro', zero_division=0
    )
    precision_weighted, recall_weighted, f1_weighted, _ = precision_recall_fscore_support(
        labels, predictions, average='weighted', zero_division=0
    )
    
    # Calculate per-class metrics
    precision_per_class, recall_per_class, f1_per_class, _ = precision_recall_fscore_support(
        labels, predictions, average=None, labels=[0, 1, 2], zero_division=0
    )
    
    metrics = {
        'accuracy': accuracy,
        'f1_macro': f1_macro,
        'precision_macro': precision_macro,
        'recall_macro': recall_macro,
        'f1_weighted': f1_weighted,
        'precision_weighted': precision_weighted,
        'recall_weighted': recall_weighted,
        # Per-class scores
        'class_0_f1': f1_per_class[0],
        'class_1_f1': f1_per_class[1],
        'class_2_f1': f1_per_class[2]
    }
    
    return metrics

def main():
    args = parse_args()
    
    print("=" * 70)
    print("      [+] DEBERTA-V3 LATERAL MOVEMENT CLASSIFIER TRAINING [+]      ")
    print("=" * 70)
    
    # Verify dataset exists
    if not os.path.exists(args.csv_path):
        print(f"[!] Dataset not found at: {args.csv_path}")
        print("[!] Please run 'python scripts/setup_dataset.py' first to initialize the dataset!")
        sys.exit(1)
        
    # Check GPU availability
    device = "cuda" if torch.cuda.is_available() else "cpu"
    use_bf16 = device == "cuda" and torch.cuda.is_bf16_supported()
    print(f"[*] Training Device: {device.upper()}")
    if device == "cuda":
        print(f"    GPU: {torch.cuda.get_device_name(0)}")
        print(f"    Mixed precision: {'bf16' if use_bf16 else 'fp16'}")
    else:
        print("    [!] No GPU found. Training on CPU might be slow.")
        
    # Load dataset
    try:
        train_dataset, val_dataset = load_lmd_dataset(
            args.csv_path, 
            balance_classes=args.balance_classes
        )
    except Exception as e:
        print(f"[!] Error loading dataset: {e}")
        sys.exit(1)
        
    # Downsample for quick CPU training demonstration
    if device == "cpu":
        print("\n[*] OPTIMIZING FOR CPU: Downsampling dataset to a balanced subset for ultra-fast training...")
        train_df = train_dataset.to_pandas()
        val_df = val_dataset.to_pandas()
        
        train_sampled = []
        val_sampled = []
        for label in [0, 1, 2]:
            sub_train = train_df[train_df['normalized_label'] == label]
            sub_val = val_df[val_df['normalized_label'] == label]
            
            # 3 train, 1 validation per class for lightning-fast local CPU demonstration
            train_sampled.append(sub_train.sample(n=min(len(sub_train), 3), random_state=42))
            val_sampled.append(sub_val.sample(n=min(len(sub_val), 1), random_state=42))
            
        import pandas as pd
        from datasets import Dataset
        train_df_new = pd.concat(train_sampled).sample(frac=1, random_state=42).reset_index(drop=True)
        val_df_new = pd.concat(val_sampled).sample(frac=1, random_state=42).reset_index(drop=True)
        
        train_dataset = Dataset.from_pandas(train_df_new)
        val_dataset = Dataset.from_pandas(val_df_new)
        
        print(f"[+] CPU Balanced Dataset: Train size={len(train_dataset)}, Val size={len(val_dataset)}")
        
    print(f"\n[*] Initializing Tokenizer: {args.model_name}...")
    # DeBERTa-v3 tokenizer requires transformers>=4.30 and sentencepiece
    tokenizer = AutoTokenizer.from_pretrained(args.model_name, use_fast=True)
    
    def tokenize_function(examples):
        return tokenizer(
            examples['formatted_text'], 
            truncation=True, 
            max_length=64
        )
        
    print("[*] Tokenizing datasets...")
    tokenized_train = train_dataset.map(tokenize_function, batched=True)
    tokenized_val = val_dataset.map(tokenize_function, batched=True)
    
    # Prepare datasets for trainer by renaming target column
    tokenized_train = tokenized_train.rename_column("normalized_label", "label")
    tokenized_val = tokenized_val.rename_column("normalized_label", "label")
    
    print(f"[*] Loading Pre-trained Encoder SLM: {args.model_name}...")
    # 3 classes: 0 (Normal), 1 (EoRS), 2 (EoHT)
    model = AutoModelForSequenceClassification.from_pretrained(
        args.model_name, 
        num_labels=3
    )
    if device == "cpu":
        print("[*] Casting model parameters to float32 for CPU compatibility...")
        model = model.float()
    
    # Define training arguments
    training_args = TrainingArguments(
        output_dir=os.path.join(args.output_dir, "checkpoints"),
        learning_rate=args.learning_rate,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        num_train_epochs=args.epochs,
        weight_decay=0.01,
        eval_strategy="epoch",
        save_strategy="epoch",
        logging_steps=50,
        load_best_model_at_end=True,
        metric_for_best_model="f1_macro",
        greater_is_better=True,
        fp16=(device == "cuda" and not use_bf16),
        bf16=use_bf16,
        report_to="none" # Disable W&B logging for clean local run
    )
    
    data_collator = DataCollatorWithPadding(tokenizer=tokenizer)
    
    print("\n[*] Initializing Hugging Face Trainer...")
    progress_callback = ProgressCallback(args.output_dir, f"DeBERTa Classifier ({args.model_name})")
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_train,
        eval_dataset=tokenized_val,
        processing_class=tokenizer,
        data_collator=data_collator,
        compute_metrics=compute_metrics,
        callbacks=[progress_callback]
    )
    
    print("\n" + "=" * 30 + " STARTING TRAINING " + "=" * 30)
    train_result = trainer.train()
    print("=" * 30 + " TRAINING COMPLETE " + "=" * 30 + "\n")
    
    # Save the best model and tokenizer
    print(f"[*] Saving fine-tuned classifier and tokenizer to: {args.output_dir}")
    os.makedirs(args.output_dir, exist_ok=True)
    trainer.save_model(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)
    
    # Evaluate model
    print("[*] Running final model evaluation on validation set...")
    metrics = trainer.evaluate()
    
    print("\n" + "=" * 25 + " FINAL PERFORMANCE REPORT " + "=" * 25)
    print(f"Accuracy:                  {metrics['eval_accuracy']:.4f}")
    print(f"Macro F1-Score:            {metrics['eval_f1_macro']:.4f}")
    print(f"Macro Precision:           {metrics['eval_precision_macro']:.4f}")
    print(f"Macro Recall:              {metrics['eval_recall_macro']:.4f}")
    print("-" * 70)
    print(f"Normal (Class 0) F1-Score: {metrics['eval_class_0_f1']:.4f}")
    print(f"EoRS (Class 1) F1-Score:   {metrics['eval_class_1_f1']:.4f}")
    print(f"EoHT (Class 2) F1-Score:   {metrics['eval_class_2_f1']:.4f}")
    print("=" * 76)
    
    # Write summary file
    summary_path = os.path.join(args.output_dir, "training_summary.json")
    with open(summary_path, "w") as f:
        import json
        json.dump(metrics, f, indent=4)
    print(f"[+] Summary written to: {summary_path}")

if __name__ == "__main__":
    main()
