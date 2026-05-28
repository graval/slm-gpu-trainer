import os
import sys
import argparse
import torch
import time
import json
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
    parser = argparse.ArgumentParser(description="LoRA Fine-Tune Decoder SLM for Explanatory Lateral Movement Detection")
    parser.add_argument("--csv_path", type=str, default="data/lmd_2023_dataset.csv", help="Path to the LMD-2023 CSV file")
    parser.add_argument("--model_name", type=str, default="Qwen/Qwen2.5-1.5B-Instruct", help="Base decoder model")
    parser.add_argument("--output_dir", type=str, default="models/qwen-lateral-movement", help="Where to save the LoRA weights")
    parser.add_argument("--epochs", type=int, default=3, help="Number of training epochs")
    parser.add_argument("--batch_size", type=int, default=2, help="Batch size for training")
    parser.add_argument("--gradient_accumulation_steps", type=int, default=4, help="Gradient accumulation steps")
    parser.add_argument("--learning_rate", type=float, default=2e-4, help="LoRA learning rate")
    parser.add_argument("--qlora", action="store_true", default=False, help="Use 4-bit QLoRA to save memory (requires bitsandbytes)")
    parser.add_argument("--int8", action="store_true", default=False, help="Use 8-bit quantization (Quanto for CPU / BitsAndBytes for GPU)")
    return parser.parse_args()

def main():
    args = parse_args()
    
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
        
    # Load dataset
    try:
        train_dataset, val_dataset = load_lmd_for_decoder(
            args.csv_path,
            balance_classes=True
        )
    except Exception as e:
        print(f"[!] Error loading dataset: {e}")
        sys.exit(1)
        
    # Downsample for quick CPU training demonstration
    if device == "cpu":
        print("\n[*] OPTIMIZING FOR CPU: Downsampling dataset to a tiny subset for ultra-fast training...")
        train_dataset = train_dataset.select(range(min(len(train_dataset), 3)))
        val_dataset = val_dataset.select(range(min(len(val_dataset), 1)))
        print(f"[+] CPU Balanced Dataset: Train size={len(train_dataset)}, Val size={len(val_dataset)}")

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
        logging_steps=10,
        fp16=(device == "cuda" and not args.qlora and not use_bf16),
        bf16=(device == "cuda" and not args.qlora and use_bf16),
        report_to="none",
        dataset_text_field="text",
        max_length=512,
        packing=False
    )
    
    print("\n[*] Initializing Supervised Fine-Tuning Trainer (trl.SFTTrainer)...")
    progress_callback = ProgressCallback(args.output_dir, f"Qwen LoRA Generator ({args.model_name})")
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
