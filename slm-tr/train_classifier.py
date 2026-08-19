import os
import sys
import argparse
import time
import json
import numpy as np
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
import torch
from torch.utils.data import DataLoader

# Maximize multi-threaded performance across all CPU cores (Intel Core Ultra 7 255H - 16 Cores)
cpu_cores = os.cpu_count() or 16
torch.set_num_threads(cpu_cores)
os.environ["OMP_NUM_THREADS"] = str(cpu_cores)
os.environ["MKL_NUM_THREADS"] = str(cpu_cores)

# Try importing DirectML for Intel Arc GPU / Windows ML acceleration
try:
    import torch_directml
    DML_AVAILABLE = torch_directml.is_available()
except ImportError:
    torch_directml = None
    DML_AVAILABLE = False

from transformers import (
    AutoTokenizer, 
    AutoModelForSequenceClassification, 
    TrainingArguments, 
    Trainer,
    DataCollatorWithPadding,
    TrainerCallback,
    get_linear_schedule_with_warmup
)
from data.loader import load_lmd_dataset

class ProgressTracker:
    """Unified telemetry and progress tracker for both Hugging Face Trainer and DirectML native loops."""
    def __init__(self, output_dir, model_name, max_steps):
        self.output_dir = output_dir
        self.model_name = model_name
        self.max_steps = max_steps
        self.start_time = time.time()
        self.history = []
        self.progress_file = os.path.join(output_dir, "training_progress.json")
        self.external_progress_file = "external/training_progress.json"
        
        initial_progress = {
            "model_name": self.model_name,
            "status": "training",
            "current_step": 0,
            "max_steps": max_steps,
            "epoch": 0.0,
            "loss": 0.0,
            "learning_rate": 0.0,
            "elapsed_time": 0.0,
            "eta_seconds": 0.0,
            "history": []
        }
        self.save_progress(initial_progress)
        
    def update(self, step, epoch, loss, lr):
        elapsed_time = time.time() - self.start_time
        eta_seconds = 0.0
        if step > 0:
            steps_per_sec = step / elapsed_time
            remaining_steps = max(0, self.max_steps - step)
            eta_seconds = remaining_steps / max(1e-5, steps_per_sec)
            
        step_record = {
            "step": step,
            "loss": round(float(loss), 4),
            "learning_rate": float(lr),
            "epoch": round(float(epoch), 2)
        }
        if step > 0:
            self.history.append(step_record)
            
        progress = {
            "model_name": self.model_name,
            "status": "training",
            "current_step": step,
            "max_steps": self.max_steps,
            "epoch": round(float(epoch), 2),
            "loss": round(float(loss), 4),
            "learning_rate": float(lr),
            "elapsed_time": round(elapsed_time, 2),
            "eta_seconds": round(eta_seconds, 2),
            "history": self.history
        }
        self.save_progress(progress)
        
    def complete(self, step, epoch, final_loss=0.0):
        elapsed_time = time.time() - self.start_time
        progress = {
            "model_name": self.model_name,
            "status": "completed",
            "current_step": step,
            "max_steps": self.max_steps,
            "epoch": round(float(epoch), 2),
            "loss": round(float(final_loss), 4),
            "learning_rate": 0.0,
            "elapsed_time": round(elapsed_time, 2),
            "eta_seconds": 0.0,
            "history": self.history
        }
        self.save_progress(progress)
        
    def save_progress(self, progress):
        try:
            os.makedirs(os.path.dirname(self.progress_file), exist_ok=True)
            with open(self.progress_file, "w") as f:
                json.dump(progress, f, indent=4)
            ext_dir = os.path.dirname(self.external_progress_file)
            if os.path.exists(ext_dir):
                with open(self.external_progress_file, "w") as f:
                    json.dump(progress, f, indent=4)
        except Exception:
            pass

class ProgressCallback(TrainerCallback):
    def __init__(self, tracker):
        self.tracker = tracker

    def on_log(self, args, state, control, logs=None, **kwargs):
        if state.is_world_process_zero:
            logs = logs or {}
            self.tracker.update(
                step=state.global_step,
                epoch=state.epoch or 0.0,
                loss=logs.get("loss", 0.0),
                lr=logs.get("learning_rate", 0.0)
            )

    def on_train_end(self, args, state, control, **kwargs):
        if state.is_world_process_zero:
            loss = self.tracker.history[-1]["loss"] if self.tracker.history else 0.0
            self.tracker.complete(step=state.global_step, epoch=state.epoch or 3.0, final_loss=loss)

def parse_args():
    parser = argparse.ArgumentParser(description="Train SLM for Lateral Movement Classification with Hardware Acceleration")
    parser.add_argument("--csv_path", type=str, default="data/lmd_2023_dataset.csv", help="Path to the LMD-2023 CSV file")
    parser.add_argument("--model_name", type=str, default="auto", help="Base model: 'auto', 'distilbert-base-uncased', 'roberta-base', or 'microsoft/deberta-v3-small'")
    parser.add_argument("--output_dir", type=str, default="models/deberta-lateral-movement", help="Where to save the trained model")
    parser.add_argument("--device", type=str, default="auto", choices=["auto", "dml", "cuda", "cpu"], help="Hardware device: auto, dml (Intel Arc GPU via DirectML), cuda, cpu")
    parser.add_argument("--epochs", type=int, default=3, help="Number of training epochs")
    parser.add_argument("--batch_size", type=int, default=16, help="Batch size for training")
    parser.add_argument("--learning_rate", type=float, default=2e-5, help="Learning rate")
    parser.add_argument("--balance_classes", action="store_true", default=True, help="Balance dataset classes via downsampling")
    parser.add_argument("--window_size", type=int, default=3, help="Sliding window size (number of consecutive events per sequence, default: 3)")
    parser.add_argument("--max_length", type=int, default=128, help="Maximum token length for tokenizer (default: 128)")
    parser.add_argument("--target_minutes", type=float, default=30.0, help="Target total execution time in minutes on local hardware (default: 30.0)")
    return parser.parse_args()

def compute_metrics(eval_pred):
    """Computes precision, recall, F1, and accuracy for evaluation."""
    logits, labels = eval_pred
    predictions = np.argmax(logits, axis=-1)
    
    accuracy = accuracy_score(labels, predictions)
    precision_macro, recall_macro, f1_macro, _ = precision_recall_fscore_support(
        labels, predictions, average='macro', zero_division=0
    )
    precision_weighted, recall_weighted, f1_weighted, _ = precision_recall_fscore_support(
        labels, predictions, average='weighted', zero_division=0
    )
    precision_per_class, recall_per_class, f1_per_class, _ = precision_recall_fscore_support(
        labels, predictions, average=None, labels=[0, 1, 2], zero_division=0
    )
    
    metrics = {
        'eval_accuracy': accuracy,
        'eval_f1_macro': f1_macro,
        'eval_precision_macro': precision_macro,
        'eval_recall_macro': recall_macro,
        'eval_f1_weighted': f1_weighted,
        'eval_precision_weighted': precision_weighted,
        'eval_recall_weighted': recall_weighted,
        'eval_class_0_f1': f1_per_class[0],
        'eval_class_1_f1': f1_per_class[1],
        'eval_class_2_f1': f1_per_class[2]
    }
    return metrics

def profile_model_speed(model, tokenizer, device_obj, batch_size, max_length=128):
    """Profiles the training and evaluation speed (seconds per batch) on the active device using full-length sequences."""
    print("[*] Running hardware performance profiling with full-length sequences...")
    dummy_texts = [
        "[Event T-2] Event ID: 3 | Network: 192.168.1.50 -> 192.168.1.10:445\n[Event T-1] Event ID: 17 | Pipe Name: \\psexec\n[Target Event T_0] Event ID: 1 | Image: PSEXESVC.exe | CommandLine: psexec.exe \\\\CORP-SRV04 cmd.exe",
        "[Event T-2] Event ID: 1 | Image: cmd.exe | CommandLine: whoami\n[Event T-1] Event ID: 10 | SourceImage: mimikatz.exe | TargetImage: lsass.exe\n[Target Event T_0] Event ID: 10 | GrantedAccess: 0x1010 | CallTrace: C:\\Windows\\SYSTEM32\\ntdll.dll"
    ]
    inputs = tokenizer(dummy_texts, padding="max_length", truncation=True, max_length=max_length, return_tensors="pt")
    inputs = {k: v.repeat((batch_size + 1) // 2, 1)[:batch_size].to(device_obj) for k, v in inputs.items()}
    inputs["labels"] = torch.zeros(batch_size, dtype=torch.long).to(device_obj)
    
    model.train()
    try:
        outputs = model(**inputs)
        loss = outputs.loss
        loss.backward()
        model.zero_grad()
    except Exception as e:
        print(f"[!] Profiling warm-up step failed: {e}. Defaulting to safe fallback speeds.")
        return 0.8, 0.2
        
    start_time = time.time()
    steps = 4
    for _ in range(steps):
        outputs = model(**inputs)
        loss = outputs.loss
        loss.backward()
        model.zero_grad()
    t_train = (time.time() - start_time) / steps
    
    model.eval()
    start_time = time.time()
    with torch.no_grad():
        for _ in range(steps):
            _ = model(**inputs)
    t_val = (time.time() - start_time) / steps
    
    return t_train, t_val

def calibrate_dataset_size(model, tokenizer, train_dataset, val_dataset, device_obj, device_name_str, batch_size, epochs, max_length=128, target_minutes=15.0):
    """Dynamically calibrates dataset downsampling to target configured execution time."""
    t_train, t_val = profile_model_speed(model, tokenizer, device_obj, batch_size, max_length=max_length)
    
    full_train_samples = len(train_dataset)
    full_val_samples = len(val_dataset)
    full_train_batches = full_train_samples / batch_size
    full_val_batches = full_val_samples / batch_size
    estimated_full_duration = epochs * (full_train_batches * t_train + full_val_batches * t_val)
    
    target_seconds = float(os.environ.get("CALIBRATION_TARGET_SECONDS", target_minutes * 60.0))
    is_cuda = "cuda" in device_name_str.lower()
    
    use_full_dataset = False
    if is_cuda and "CALIBRATION_TARGET_SECONDS" not in os.environ:
        if estimated_full_duration <= 7200.0:
            use_full_dataset = True
            target_seconds = estimated_full_duration
            
    if use_full_dataset:
        n_train_samples = full_train_samples
        n_val_samples = full_val_samples
    else:
        denom = epochs * (t_train + 0.2 * t_val)
        if denom <= 0:
            denom = 1.0
        n_train_batches = target_seconds / denom
        n_train_samples = int(n_train_batches * batch_size)
        n_train_samples = max(300, min(n_train_samples, full_train_samples))
        n_train_samples = (n_train_samples // 3) * 3
        
        n_val_samples = int(n_train_samples * 0.2)
        n_val_samples = max(60, min(n_val_samples, full_val_samples))
        n_val_samples = (n_val_samples // 3) * 3
        
    est_train_batches = n_train_samples / batch_size
    est_val_batches = n_val_samples / batch_size
    est_total_seconds = epochs * (est_train_batches * t_train + est_val_batches * t_val)
    est_minutes = est_total_seconds / 60.0
    
    print("+" + "=" * 68 + "+")
    print(f"|                  DYNAMIC HARDWARE CALIBRATION DASHBOARD            |")
    print("+" + "=" * 68 + "+")
    print(f"|  Device detected:        {device_name_str:<41} |")
    print(f"|  Measured Step Speed:    Train={t_train*1000:.1f}ms/batch, Eval={t_val*1000:.1f}ms/batch |")
    print(f"|  Target Duration:        {target_seconds/60.0:.1f} minutes ({int(target_seconds)} seconds)             |")
    print(f"|  Calibrated Dataset:     Train Size={n_train_samples:<6} (balanced)               |")
    print(f"|                          Val Size={n_val_samples:<6} (balanced)                 |")
    print(f"|  Estimated Run Time:     {est_minutes:.1f} minutes ({int(est_total_seconds)} seconds)            |")
    print("+" + "=" * 68 + "+")
    
    train_df = train_dataset.to_pandas()
    val_df = val_dataset.to_pandas()
    
    train_sampled = []
    val_sampled = []
    train_per_class = n_train_samples // 3
    val_per_class = n_val_samples // 3
    
    for label in [0, 1, 2]:
        sub_train = train_df[train_df['normalized_label'] == label]
        sub_val = val_df[val_df['normalized_label'] == label]
        train_sampled.append(sub_train.sample(n=min(len(sub_train), train_per_class), random_state=42))
        val_sampled.append(sub_val.sample(n=min(len(sub_val), val_per_class), random_state=42))
        
    import pandas as pd
    from datasets import Dataset
    train_df_new = pd.concat(train_sampled).sample(frac=1, random_state=42).reset_index(drop=True)
    val_df_new = pd.concat(val_sampled).sample(frac=1, random_state=42).reset_index(drop=True)
    
    return Dataset.from_pandas(train_df_new), Dataset.from_pandas(val_df_new)

def train_directml(model, tokenizer, train_dataset, val_dataset, device_obj, args, tracker):
    """DirectML-accelerated high-performance native PyTorch training loop on Intel Arc GPU."""
    print("\n[*] Initializing DirectML Intel Arc GPU Training Pipeline...")
    
    data_collator = DataCollatorWithPadding(tokenizer=tokenizer)
    train_loader = DataLoader(
        train_dataset, 
        batch_size=args.batch_size, 
        shuffle=True, 
        collate_fn=data_collator
    )
    val_loader = DataLoader(
        val_dataset, 
        batch_size=args.batch_size, 
        shuffle=False, 
        collate_fn=data_collator
    )
    
    total_steps = len(train_loader) * args.epochs
    tracker.max_steps = total_steps
    
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.learning_rate, weight_decay=0.01)
    lr_scheduler = get_linear_schedule_with_warmup(
        optimizer, 
        num_warmup_steps=int(0.05 * total_steps), 
        num_training_steps=total_steps
    )
    
    global_step = 0
    best_f1 = -1.0
    best_metrics = {}
    
    print("\n" + "=" * 30 + " STARTING DIRECTML GPU TRAINING " + "=" * 30)
    for epoch in range(args.epochs):
        model.train()
        epoch_loss = 0.0
        
        for step, batch in enumerate(train_loader):
            batch = {k: v.to(device_obj) for k, v in batch.items()}
            optimizer.zero_grad()
            
            outputs = model(**batch)
            loss = outputs.loss
            loss.backward()
            
            optimizer.step()
            lr_scheduler.step()
            
            global_step += 1
            epoch_loss += loss.item()
            
            if global_step % 20 == 0 or global_step == total_steps:
                curr_lr = lr_scheduler.get_last_lr()[0] if lr_scheduler.get_last_lr() else args.learning_rate
                tracker.update(
                    step=global_step, 
                    epoch=epoch + (step + 1) / len(train_loader), 
                    loss=loss.item(), 
                    lr=curr_lr
                )
                print(f"Epoch {epoch+1}/{args.epochs} | Step {global_step}/{total_steps} | Loss: {loss.item():.4f} | LR: {curr_lr:.2e}")
                
        # Validation at end of each epoch
        model.eval()
        all_preds = []
        all_labels = []
        with torch.no_grad():
            for val_batch in val_loader:
                labels = val_batch["labels"].cpu().numpy()
                val_batch = {k: v.to(device_obj) for k, v in val_batch.items()}
                logits = model(**val_batch).logits.cpu().numpy()
                all_preds.append(logits)
                all_labels.append(labels)
                
        val_logits = np.concatenate(all_preds, axis=0)
        val_labels = np.concatenate(all_labels, axis=0)
        eval_metrics = compute_metrics((val_logits, val_labels))
        
        print(f"\n[+] Validation Epoch {epoch+1}: F1-Macro={eval_metrics['eval_f1_macro']:.4f}, Accuracy={eval_metrics['eval_accuracy']:.4f}")
        
        if eval_metrics['eval_f1_macro'] > best_f1:
            best_f1 = eval_metrics['eval_f1_macro']
            best_metrics = eval_metrics
            os.makedirs(args.output_dir, exist_ok=True)
            model.to("cpu")
            model.save_pretrained(args.output_dir)
            model.to(device_obj)
            tokenizer.save_pretrained(args.output_dir)
            
    print("=" * 30 + " TRAINING COMPLETE " + "=" * 30 + "\n")
    tracker.complete(step=global_step, epoch=args.epochs, final_loss=epoch_loss / max(1, len(train_loader)))
    return best_metrics

def main():
    args = parse_args()
    
    print("=" * 70)
    print("      [+] HARDWARE-ACCELERATED SLM LATERAL MOVEMENT TRAINING [+]      ")
    print("=" * 70)
    
    if not os.path.exists(args.csv_path):
        print(f"[!] Dataset not found at: {args.csv_path}")
        sys.exit(1)
        
    # Resolve Device
    device_mode = args.device.lower()
    if device_mode == "auto":
        if torch.cuda.is_available():
            device_mode = "cuda"
        elif DML_AVAILABLE and torch_directml.device_count() > 0:
            device_mode = "dml"
        else:
            device_mode = "cpu"
            
    if device_mode == "cuda":
        device_obj = torch.device("cuda")
        device_name_str = f"NVIDIA CUDA ({torch.cuda.get_device_name(0)})"
    elif device_mode == "dml":
        if not DML_AVAILABLE:
            print("[!] DirectML not installed. Falling back to 16-Core CPU.")
            device_mode = "cpu"
            device_obj = torch.device("cpu")
            device_name_str = f"Intel Core Ultra CPU ({cpu_cores} Cores)"
        else:
            device_obj = torch_directml.device()
            dml_name = torch_directml.device_name(torch_directml.default_device())
            device_name_str = f"DirectML GPU ({dml_name.strip()})"
    else:
        device_obj = torch.device("cpu")
        device_name_str = f"Intel Core Ultra CPU ({cpu_cores} Cores)"
        
    print(f"[*] Active Hardware Acceleration: {device_name_str}")
    
    # Resolve Model Architecture
    if args.model_name == "auto":
        if device_mode == "dml":
            model_name = "distilbert-base-uncased"
        else:
            model_name = "microsoft/deberta-v3-small"
    else:
        model_name = args.model_name
        
    print(f"[*] Base SLM Architecture: {model_name}")
    
    # Initialize Progress Telemetry
    tracker = ProgressTracker(args.output_dir, f"SLM Classifier ({model_name})", max_steps=100)
    
    # Load dataset with temporal sliding window
    try:
        raw_train_dataset, raw_val_dataset = load_lmd_dataset(
            args.csv_path, 
            window_size=args.window_size,
            balance_classes=args.balance_classes
        )
    except Exception as e:
        print(f"[!] Error loading dataset: {e}")
        sys.exit(1)
        
    print(f"\n[*] Initializing Tokenizer: {model_name}...")
    tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=True)
    
    print(f"[*] Loading Pre-trained Model: {model_name}...")
    model = AutoModelForSequenceClassification.from_pretrained(
        model_name, 
        num_labels=3
    )
    if device_mode == "cpu":
        model = model.float()
    model = model.to(device_obj)
    
    # Calibrate dataset size
    train_dataset, val_dataset = calibrate_dataset_size(
        model, 
        tokenizer, 
        raw_train_dataset, 
        raw_val_dataset, 
        device_obj, 
        device_name_str,
        args.batch_size, 
        args.epochs,
        max_length=args.max_length,
        target_minutes=args.target_minutes
    )
    
    def tokenize_function(examples):
        return tokenizer(
            examples['formatted_text'], 
            truncation=True, 
            max_length=args.max_length
        )
        
    print("[*] Tokenizing datasets...")
    tokenized_train = train_dataset.map(tokenize_function, batched=True)
    tokenized_val = val_dataset.map(tokenize_function, batched=True)
    
    tokenized_train = tokenized_train.rename_column("normalized_label", "label")
    tokenized_val = tokenized_val.rename_column("normalized_label", "label")
    tokenized_train = tokenized_train.remove_columns(["formatted_text"])
    tokenized_val = tokenized_val.remove_columns(["formatted_text"])
    
    if device_mode == "dml":
        # Run DirectML GPU training loop on Intel Arc GPU
        metrics = train_directml(
            model, 
            tokenizer, 
            tokenized_train, 
            tokenized_val, 
            device_obj, 
            args, 
            tracker
        )
    else:
        # Run Hugging Face Trainer for CUDA / 16-Core CPU
        training_args = TrainingArguments(
            output_dir=os.path.join(args.output_dir, "checkpoints"),
            learning_rate=args.learning_rate,
            per_device_train_batch_size=args.batch_size,
            per_device_eval_batch_size=args.batch_size,
            num_train_epochs=args.epochs,
            weight_decay=0.01,
            eval_strategy="epoch",
            save_strategy="epoch",
            logging_steps=20,
            load_best_model_at_end=True,
            metric_for_best_model="eval_f1_macro",
            greater_is_better=True,
            dataloader_pin_memory=False,
            report_to="none"
        )
        data_collator = DataCollatorWithPadding(tokenizer=tokenizer)
        progress_callback = ProgressCallback(tracker)
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
        trainer.train()
        print("=" * 30 + " TRAINING COMPLETE " + "=" * 30 + "\n")
        
        print(f"[*] Saving fine-tuned classifier and tokenizer to: {args.output_dir}")
        os.makedirs(args.output_dir, exist_ok=True)
        trainer.save_model(args.output_dir)
        tokenizer.save_pretrained(args.output_dir)
        metrics = trainer.evaluate()
        
    print("\n" + "=" * 25 + " FINAL PERFORMANCE REPORT " + "=" * 25)
    print(f"Accuracy:                  {metrics.get('eval_accuracy', 0.0):.4f}")
    print(f"Macro F1-Score:            {metrics.get('eval_f1_macro', 0.0):.4f}")
    print(f"Macro Precision:           {metrics.get('eval_precision_macro', 0.0):.4f}")
    print(f"Macro Recall:              {metrics.get('eval_recall_macro', 0.0):.4f}")
    print("-" * 70)
    print(f"Normal (Class 0) F1-Score: {metrics.get('eval_class_0_f1', 0.0):.4f}")
    print(f"EoRS (Class 1) F1-Score:   {metrics.get('eval_class_1_f1', 0.0):.4f}")
    print(f"EoHT (Class 2) F1-Score:   {metrics.get('eval_class_2_f1', 0.0):.4f}")
    print("=" * 76)
    
    summary_path = os.path.join(args.output_dir, "training_summary.json")
    with open(summary_path, "w") as f:
        json.dump(metrics, f, indent=4)
    print(f"[+] Summary written to: {summary_path}")

if __name__ == "__main__":
    main()
