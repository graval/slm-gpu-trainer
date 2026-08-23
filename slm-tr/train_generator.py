import os
import sys
import argparse
import time
import json
import pathlib

# Ensure UTF-8 default decoding for Windows systems when loading jinja templates in trl
os.environ["PYTHONUTF8"] = "1"
_orig_read_text = pathlib.Path.read_text
def _utf8_read_text(self, encoding=None, errors=None):
    if encoding is None:
        encoding = "utf-8"
    return _orig_read_text(self, encoding=encoding, errors=errors)
pathlib.Path.read_text = _utf8_read_text

import torch
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    TrainingArguments,
    BitsAndBytesConfig,
    TrainerCallback
)
from peft import LoraConfig, get_peft_model, TaskType
from trl import SFTTrainer, SFTConfig
from data.loader import load_lmd_for_decoder

class ProgressCallback(TrainerCallback):
    def __init__(self, output_dir, model_name, extra_meta=None):
        self.output_dir = output_dir
        self.model_name = model_name
        self.extra_meta = extra_meta or {}
        self.start_time = time.time()
        self.history = []
        
        # Primary progress file inside model directory
        self.progress_file = os.path.join(output_dir, "training_progress.json")
        
        # Secondary progress file inside external folder (for shared access in Docker / Dashboard)
        self.external_progress_file = "external/training_progress.json"

        # Immediately overwrite the progress file to signal starting a new active run
        initial_progress = {
            "model_name": self.model_name,
            "status": "training",
            "current_step": 0,
            "max_steps": 100,
            "epoch": 0.0,
            "loss": 0.0,
            "learning_rate": 0.0,
            "elapsed_time": 0.0,
            "eta_seconds": 0.0,
            "history": []
        }
        initial_progress.update(self.extra_meta)
        self._save_progress(initial_progress)


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
            progress.update(self.extra_meta)
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
            progress.update(self.extra_meta)
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
    parser = argparse.ArgumentParser(description="LoRA Fine-Tune Decoder SLM for Explanatory Lateral Movement Detection")
    parser.add_argument("--csv_path", type=str, default="data/lmd_2023_dataset.csv", help="Path to the LMD-2023 CSV file")
    parser.add_argument("--model_name", type=str, default="Qwen/Qwen2.5-1.5B-Instruct", help="Base decoder model")
    parser.add_argument("--output_dir", type=str, default="models/qwen-lateral-movement", help="Where to save the LoRA weights")
    parser.add_argument("--variant", type=str, default=None, choices=["v1", "v2", "v1_single_entry", "v2_sliding_window"], help="Architectural variant approach")
    parser.add_argument("--epochs", type=int, default=3, help="Number of training epochs")
    parser.add_argument("--batch_size", type=int, default=2, help="Batch size for training")
    parser.add_argument("--gradient_accumulation_steps", type=int, default=4, help="Gradient accumulation steps")
    parser.add_argument("--learning_rate", type=float, default=2e-4, help="LoRA learning rate")
    parser.add_argument("--qlora", action="store_true", default=False, help="Use 4-bit QLoRA to save memory (requires bitsandbytes)")
    parser.add_argument("--int8", action="store_true", default=False, help="Use 8-bit quantization (Quanto for CPU / BitsAndBytes for GPU)")
    parser.add_argument("--window_size", type=int, default=3, help="Sliding window size (number of consecutive events per sequence, default: 3)")
    parser.add_argument("--max_length", type=int, default=512, help="Maximum token sequence length (default: 512)")
    args = parser.parse_args()

    # Determine architectural approach suffix
    if args.variant:
        suffix = "v1_single_entry" if "v1" in args.variant else "v2_sliding_window"
        if "v1" in args.variant:
            args.window_size = 1
    else:
        suffix = "v1_single_entry" if args.window_size == 1 else "v2_sliding_window"

    # Append approach suffix if not already present
    if not (args.output_dir.endswith("v1_single_entry") or args.output_dir.endswith("v2_sliding_window")):
        args.output_dir = f"{args.output_dir.rstrip('/')}-{suffix}"

    return args

def profile_generator_speed(model, tokenizer, device):
    """Profiles the Qwen LoRA training speed (seconds per sample) on the active device."""
    print("[*] Running a brief causal LLM hardware performance profile...")
    import time
    
    # Create a tiny dummy text
    dummy_text = "<|im_start|>user\nAnalyze this Windows security log for potential lateral movement activity:\nEvent ID: 1\nImage: cmd.exe\nCommand Line: cmd.exe /c echo Hello<|im_end|>\n<|im_start|>assistant\n{\n  \"lateral_movement\": false\n}<|im_end|>"
    
    inputs = tokenizer(dummy_text, truncation=True, max_length=128, return_tensors="pt")
    inputs = {k: v.to(device) for k, v in inputs.items()}
    inputs["labels"] = inputs["input_ids"].clone()
    
    # Measure a forward and backward pass
    model.train()
    try:
        # Warm-up step
        outputs = model(**inputs)
        loss = outputs.loss
        loss.backward()
        if hasattr(model, "zero_grad"):
            model.zero_grad()
    except Exception as e:
        print(f"[!] LLM Warm-up step failed: {e}. Defaulting to safe fallback speeds.")
        return 12.0  # Safe fallback of 12 seconds per sample on typical CPU
        
    start_time = time.time()
    steps = 2
    for _ in range(steps):
        outputs = model(**inputs)
        loss = outputs.loss
        loss.backward()
        if hasattr(model, "zero_grad"):
            model.zero_grad()
    t_step = (time.time() - start_time) / steps
    
    # Scale for typical sequence length of ~512
    t_sample = t_step * 3.0
    return t_sample

def calibrate_generator_dataset_size(model, tokenizer, train_dataset, val_dataset, device, epochs):
    """Dynamically calibrates the dataset downsampling rate to target ~1 hour total execution on CPU or GPU limits, but uses full dataset on GPU if it takes <= 2 hours."""
    t_sample = profile_generator_speed(model, tokenizer, device)
    
    # Check GPU availability
    is_gpu = "cuda" in device.lower()
    
    # Calculate training duration for the FULL dataset
    full_train_samples = len(train_dataset)
    full_val_samples = len(val_dataset)
    estimated_full_duration = epochs * full_train_samples * t_sample
    
    # Target duration: 1 hour (3600 seconds) by default, or from env var
    import os
    target_seconds = float(os.environ.get("CALIBRATION_TARGET_SECONDS", 3600.0))
    
    # GPU logic:
    # Use full dataset if GPU is available and full training takes <= 2 hours (7200 seconds)
    # Unless CALIBRATION_TARGET_SECONDS env var is explicitly set to something else (e.g. for fast tests)
    use_full_dataset = False
    if is_gpu and "CALIBRATION_TARGET_SECONDS" not in os.environ:
        if estimated_full_duration <= 7200.0: # 2 hours
            use_full_dataset = True
            target_seconds = estimated_full_duration
        else:
            # If it takes > 2 hours, limit to 1 hour
            target_seconds = 3600.0
            
    if use_full_dataset:
        n_train_samples = full_train_samples
        n_val_samples = full_val_samples
    else:
        # Calibrate based on target_seconds
        denom = epochs * t_sample
        if denom <= 0:
            denom = 1.0
        n_train_samples = int(target_seconds / denom)
        
        # Enforce safe limits:
        # Min samples: 30 to ensure some LoRA learning occurs
        # Max samples: cannot exceed full training dataset size
        n_train_samples = max(30, min(n_train_samples, full_train_samples))
        
        n_val_samples = max(10, min(int(n_train_samples * 0.1), full_val_samples))
        
    # Recalculate estimated total time
    est_total_seconds = epochs * n_train_samples * t_sample
    est_minutes = est_total_seconds / 60.0
    
    # Draw a premium calibration console dashboard
    print("+" + "=" * 68 + "+")
    print(f"|                  DYNAMIC HARDWARE CALIBRATION DASHBOARD            |")
    print("+" + "=" * 68 + "+")
    print(f"|  Device detected:        {device.upper():<41} |")
    print(f"|  Measured Step Speed:    {t_sample*1000:.1f}ms/sample (scaled)                  |")
    if use_full_dataset:
        print(f"|  Mode:                   FULL DATASET TRAINING (GPU <= 2 Hours)    |")
    else:
        print(f"|  Target Duration:        {target_seconds/60.0:.1f} minutes ({int(target_seconds)} seconds)             |")
    print(f"|  Calibrated Dataset:     Train Size={n_train_samples:<6}                         |")
    print(f"|                          Val Size={n_val_samples:<6}                           |")
    print(f"|  Estimated Run Time:     {est_minutes:.1f} minutes ({int(est_total_seconds)} seconds)            |")
    print("+" + "=" * 68 + "+")
    
    # Perform downsampling
    train_sampled = train_dataset.select(range(min(len(train_dataset), n_train_samples)))
    val_sampled = val_dataset.select(range(min(len(val_dataset), n_val_samples)))
    
    return train_sampled, val_sampled

def main():
    args = parse_args()
    
    from v1_single_entry.data_loader import resolve_dataset_path
    args.csv_path = resolve_dataset_path(args.csv_path)

    # Immediately initialize the progress telemetry to signal starting a new active run
    variant_tag = "v1_single_entry" if args.window_size == 1 else "v2_sliding_window"
    variant_label = "v1 - Single Entry (K=1, Stateless)" if args.window_size == 1 else f"v2 - Sliding Window (K={args.window_size}, Temporal Sequence)"

    try:
        initial_progress = {
            "model_name": f"Generative Reasoner ({args.model_name})",
            "variant": variant_tag,
            "variant_label": variant_label,
            "window_size": args.window_size,
            "max_length": args.max_length,
            "output_dir": args.output_dir,
            "status": "training",
            "current_step": 0,
            "max_steps": 100,
            "epoch": 0.0,
            "loss": 0.0,
            "learning_rate": 0.0,
            "elapsed_time": 0.0,
            "eta_seconds": 0.0,
            "history": []
        }
        os.makedirs(args.output_dir, exist_ok=True)
        with open(os.path.join(args.output_dir, "training_progress.json"), "w") as f:
            import json
            json.dump(initial_progress, f, indent=4)
        if os.path.exists("external"):
            with open("external/training_progress.json", "w") as f:
                json.dump(initial_progress, f, indent=4)
    except Exception:
        pass

    print("=" * 70)
    print("      [+] DECODER-ONLY GENERATIVE SLM LORA FINE-TUNING [+]      ")
    print("=" * 70)

    
    # Verify dataset
    if not os.path.exists(args.csv_path):
        print(f"[!] Dataset not found at: {args.csv_path}")
        print("[!] Please run 'python scripts/setup_dataset.py' first to initialize the dataset!")
        sys.exit(1)
        
    device = "cuda" if torch.cuda.is_available() else "cpu"
    use_bf16 = device == "cuda" and torch.cuda.is_bf16_supported()
    print(f"[*] Training Device: {device.upper()}")
    if device == "cuda":
        print(f"    Mixed precision: {'bf16' if use_bf16 else 'fp16'}")
    if device != "cuda":
        print("    [!] WARNING: Fine-tuning a 1.5B+ parameter model on CPU is extremely slow.")
        print("    [*] Recommendation: Run on a system with a CUDA GPU, or in Google Colab / Kaggle.")
        
    # Load raw dataset
    try:
        raw_train_dataset, raw_val_dataset = load_lmd_for_decoder(
            args.csv_path,
            window_size=args.window_size,
            balance_classes=True
        )
    except Exception as e:
        print(f"[!] Error loading dataset: {e}")
        sys.exit(1)
        
    print(f"\n[*] Initializing Tokenizer: {args.model_name}...")
    tokenizer = AutoTokenizer.from_pretrained(args.model_name, use_fast=True)
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"
    
    # Load model with quantization if INT8 or QLoRA is enabled
    quantization_config = None
    if args.int8:
        if device == "cpu":
            print("[*] Configuring 8-bit weights quantization (INT8) using optimum/quanto on CPU...")
            from transformers import QuantoConfig
            quantization_config = QuantoConfig(weights="int8")
        else:
            print("[*] Configuring 8-bit weights quantization (INT8) using bitsandbytes on GPU...")
            quantization_config = BitsAndBytesConfig(load_in_8bit=True)
    elif args.qlora and device == "cuda":
        print("[*] Configuring 4-bit quantization (QLoRA) using bitsandbytes...")
        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True
        )
        
    print(f"[*] Loading Base Causal Language Model: {args.model_name}...")
    torch_dtype = torch.float16 if device == "cuda" else torch.float32
    
    model = AutoModelForCausalLM.from_pretrained(
        args.model_name,
        quantization_config=quantization_config,
        device_map="auto" if device == "cuda" else None,
        torch_dtype=torch_dtype,
        trust_remote_code=False
    )
    
    # Dynamic Hardware Performance Profiling and Dataset Calibration
    train_dataset, val_dataset = calibrate_generator_dataset_size(
        model,
        tokenizer,
        raw_train_dataset,
        raw_val_dataset,
        device,
        args.epochs
    )
    
    # Configure LoRA
    print("[*] Configuring Low-Rank Adaptation (LoRA)...")
    # Targets for Qwen/Llama attention layers
    target_modules = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
    
    peft_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        inference_mode=False,
        r=16,          # Rank of LoRA adapters
        lora_alpha=32, # Alpha scaling parameter
        lora_dropout=0.05,
        target_modules=target_modules,
        bias="none"
    )
    
    # Define training arguments using SFTConfig (required for trl>=0.12.0)
    training_args = SFTConfig(
        output_dir=os.path.join(args.output_dir, "checkpoints"),
        learning_rate=args.learning_rate,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        gradient_accumulation_steps=args.gradient_accumulation_steps,
        num_train_epochs=args.epochs,
        weight_decay=0.01,
        eval_strategy="epoch",
        save_strategy="epoch",
        logging_steps=1 if device == "cpu" else 10,
        fp16=(device == "cuda" and not args.qlora and not use_bf16),
        bf16=(device == "cuda" and not args.qlora and use_bf16),
        report_to="none",
        dataset_text_field="text",
        max_length=args.max_length,
        packing=False
    )
    
    print("\n[*] Initializing Supervised Fine-Tuning Trainer (trl.SFTTrainer)...")
    variant_tag = "v1_single_entry" if args.window_size == 1 else "v2_sliding_window"
    variant_label = "v1 - Single Entry (K=1, Stateless)" if args.window_size == 1 else f"v2 - Sliding Window (K={args.window_size}, Temporal Sequence)"
    progress_callback = ProgressCallback(
        args.output_dir, 
        f"Generative Reasoner ({args.model_name})",
        extra_meta={
            "variant": variant_tag,
            "variant_label": variant_label,
            "window_size": args.window_size,
            "max_length": args.max_length,
            "output_dir": args.output_dir
        }
    )
    trainer = SFTTrainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        peft_config=peft_config,
        processing_class=tokenizer,
        callbacks=[progress_callback]
    )
    
    # Ensure layers are trainable if using QLoRA
    if args.qlora and device == "cuda":
        from peft import prepare_model_for_kbit_training
        model = prepare_model_for_kbit_training(model)
        
    print("\n" + "=" * 30 + " STARTING TRAINING " + "=" * 30)
    train_result = trainer.train()
    print("=" * 30 + " TRAINING COMPLETE " + "=" * 30 + "\n")
    
    # Save LoRA weights and tokenizer
    print(f"[*] Saving fine-tuned LoRA weights and tokenizer to: {args.output_dir}")
    os.makedirs(args.output_dir, exist_ok=True)
    trainer.model.save_pretrained(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)
    
    print(f"[+] SUCCESS: LoRA adapters successfully serialized to {args.output_dir}")
    print("    You can now run 'python detect.py' to test model reasoning!")
    print("=" * 70)

if __name__ == "__main__":
    main()
