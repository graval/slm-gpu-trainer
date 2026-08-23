"""
v2 - Sliding Window Generative Reasoner LoRA / QLoRA Training Pipeline
Fine-tunes decoder SLMs (Phi-3-mini, Qwen2.5-1.5B) on multi-event temporal sequences (K=3..5)
to generate structured JSON reports detailing lateral movement progression across events.
"""

import os
import sys
import argparse
import time
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import torch
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    TrainingArguments
)
from peft import LoraConfig, get_peft_model, TaskType
from trl import SFTTrainer, SFTConfig
from v2_sliding_window.data_loader import load_v2_for_decoder

def parse_args():
    parser = argparse.ArgumentParser(description="Train v2 (Sliding Window) Generative SLM Reasoner")
    parser.add_argument("--csv_path", type=str, default="data/lmd_2023_dataset.csv", help="Dataset CSV path")
    parser.add_argument("--base_model", type=str, default="microsoft/Phi-3-mini-4k-instruct", help="Base model")
    parser.add_argument("--output_dir", type=str, default="models/phi3-lateral-movement-v2_sliding_window", help="Save directory")
    parser.add_argument("--window_size", type=int, default=3, help="Sliding window size")
    parser.add_argument("--epochs", type=int, default=3, help="Epochs")
    parser.add_argument("--batch_size", type=int, default=2, help="Batch size")
    parser.add_argument("--lr", type=float, default=2e-4, help="Learning rate")
    parser.add_argument("--max_seq_length", type=int, default=1024, help="Max sequence length for multi-event prompts")
    return parser.parse_args()

def main():
    args = parse_args()
    print("=" * 70)
    print(f"   [v2 - SLIDING WINDOW] GENERATIVE REASONER LORA TRAINING (K={args.window_size})   ")
    print("=" * 70)
    
    os.makedirs(args.output_dir, exist_ok=True)
    train_dataset, val_dataset = load_v2_for_decoder(
        args.csv_path, 
        window_size=args.window_size, 
        balance_classes=True
    )
    
    tokenizer = AutoTokenizer.from_pretrained(args.base_model, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
        
    model = AutoModelForCausalLM.from_pretrained(
        args.base_model,
        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
        device_map="auto" if torch.cuda.is_available() else None,
        trust_remote_code=True
    )
    
    peft_config = LoraConfig(
        r=16,
        lora_alpha=32,
        target_modules=["o_proj", "qkv_proj", "gate_up_proj", "down_proj"] if "Phi-3" in args.base_model else ["q_proj", "k_proj", "v_proj", "o_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type=TaskType.CAUSAL_LM
    )
    
    training_args = SFTConfig(
        output_dir=args.output_dir,
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        gradient_accumulation_steps=4,
        learning_rate=args.lr,
        logging_steps=10,
        save_strategy="epoch",
        max_seq_length=args.max_seq_length,
        dataset_text_field="text",
        report_to="none"
    )
    
    trainer = SFTTrainer(
        model=model,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        peft_config=peft_config,
        tokenizer=tokenizer,
        args=training_args
    )
    
    print("[*] Starting v2 LoRA instruction tuning on temporal event windows...")
    trainer.train()
    trainer.model.save_pretrained(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)
    print(f"[+] v2 Generative reasoner saved to: {args.output_dir}")

if __name__ == "__main__":
    main()
