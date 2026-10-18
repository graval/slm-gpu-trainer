# Clean Code Guiding Principles for EdgeShield SLM Framework

> **Purpose**: Streamline future development. All AI agents and human developers **must follow** these principles when modifying this codebase.

---

## 1. Architecture & Structure

### 1.1 Dual-Decoupled SLM Architecture (ADR-001)
- **Classifier SLM** (encoder-only, ~44M params): Evaluates 100% of telemetry at ~1.1ms/log
- **Reasoner SLM** (generative, 1.5B-3.8B params): Triggered ONLY on suspicious events (<0.1% traffic)
- **Never** merge these into a monolithic model. Keep inference paths strictly separated.

### 1.2 Package Delineation (ADR-003)
```
v1_single_entry/   # K=1 isolated single-event analysis (stateless)
v2_sliding_window/ # K=3..5 rolling temporal windows (stateful ring buffers)
reasoning/         # Central heuristic rules, MITRE KB, prompt builders (ADR-002)
edgeshield/        # Dual-stream pipeline: LSA + BPD + Correlation + Edge Deploy
scripts/           # Training, evaluation, benchmarking CLIs
data/              # Dataset loaders, CSV files
```
- **Do not** create cross-imports between `v1_single_entry` and `v2_sliding_window`
- **Do** import from `reasoning/` and `edgeshield/` as shared utilities

### 1.3 Central Reasoning Engine (ADR-002)
- All subtype detection, MITRE mapping, prompt formatting lives in `reasoning/`
- **Single source of truth** for: `MITRE_TECHNIQUES`, `SUBTYPES`, `create_decoder_sample()`
- Any MITRE update → update `reasoning/mitre_kb.py` only

---

## 2. Code Quality Standards

### 2.1 Type Hints & Documentation
```python
# REQUIRED: Type hints on all public functions
def load_v1_dataset(
    csv_path: Union[str, List[str]], 
    balance_classes: bool = True, 
    test_size: float = 0.2, 
    random_state: int = 42
) -> Tuple[Dataset, Dataset]:
    """Loads dataset CSV(s), normalizes labels, formats each line as single event."""
```

### 2.2 Module-Level Docstrings
Every `.py` file **must** start with:
```python
"""
Module Purpose: One-line summary.
Key Responsibilities:
  - Responsibility 1
  - Responsibility 2
"""
```

### 2.3 Naming Conventions
| Element | Convention | Example |
|---------|------------|---------|
| Classes | PascalCase | `LogSemanticAnalyzer`, `AttackCorrelationEngine` |
| Functions/Methods | snake_case | `load_v1_dataset`, `identify_subtype` |
| Constants | UPPER_SNAKE_CASE | `CALIBRATION_TARGET_SECONDS`, `TECHNIQUE_TO_ID` |
| Private | _leading_underscore | `_build_prompt`, `_normalize_label` |
| CLI args | kebab-case | `--model-name`, `--output-dir` |

---

## 3. Data & Path Handling

### 3.1 Dataset Path Resolution (ADR-003, AGENTS.md Rule 3)
```python
# ALWAYS use resolve_dataset_path() from the appropriate loader
from v1_single_entry.data_loader import resolve_dataset_path
# or
from v2_sliding_window.data_loader import resolve_dataset_path

path = resolve_dataset_path(csv_path)  # Handles data/, external/, scratch/, Docker paths
```

### 3.2 Model Output Suffixing (ADR-006)
```python
# Training scripts MUST append approach suffix
output_dir = f"models/deberta-lateral-movement-{APPROACH_TAG}"  # e.g., -v1_single_entry, -v2_sliding_window
```

### 3.3 Tokenizer Vocab Synchronization (ADR-004)
```python
# ALWAYS load tokenizer from model directory FIRST
tokenizer = AutoTokenizer.from_pretrained(model_path, use_fast=True)
# Fallback ONLY if local tokenizer missing
tokenizer = AutoTokenizer.from_pretrained(base_model_name, use_fast=True)
```

---

## 4. Training & Hardware Patterns

### 4.1 Dynamic Hardware Calibration (ADR-005)
All training scripts **must** include:
```python
# Maximize CPU threads
cpu_cores = os.cpu_count() or 16
torch.set_num_threads(cpu_cores)
os.environ["OMP_NUM_THREADS"] = str(cpu_cores)
os.environ["MKL_NUM_THREADS"] = str(cpu_cores)

# Device detection with DirectML fallback
device = detect_best_device()  # CUDA → DirectML → CPU
```

### 4.2 Progress Persistence
```python
# Write live progress JSON for UI monitoring
prog_data = {
    "status": "training",  # or "completed"
    "current_epoch": epoch,
    "total_epochs": epochs,
    "current_step": step,
    "total_steps": total_steps,
    "loss": round(loss.item(), 4),
    "timestamp": time.time(),
}
write_progress(prog_data)  # To both root and output_dir
```

### 4.3 Model Checkpoint Saving
```python
os.makedirs(output_dir, exist_ok=True)
model.cpu().save_pretrained(output_dir)
tokenizer.save_pretrained(output_dir)
torch.save(custom_head.state_dict(), os.path.join(output_dir, "scoring_head.pt"))
```

---

## 5. CLI & Terminal Safety

### 5.1 ASCII-Only Output (ADR-007)
```python
# FORBIDDEN on Windows
print("🟢 Training complete")  
print("🔴 Error occurred")

# REQUIRED - ASCII safe
print("[+] Training complete")
print("[!] Error occurred")
print("[COMPARISON] v1 vs v2 results")
```

### 5.2 Argument Parsing
```python
def parse_args():
    parser = argparse.ArgumentParser(description="Descriptive name")
    parser.add_argument("--model_name", type=str, default="distilbert-base-uncased")
    parser.add_argument("--output_dir", type=str, default="models/edgeshield_bpd")
    # Use type hints in help
    return parser.parse_args()
```

---

## 6. ML/DL Specific Patterns

### 6.1 Data Loading Pipeline
```python
# Standard pattern for all loaders
def load_dataset(csv_path, balance_classes=True, test_size=0.2):
    # 1. Resolve path
    # 2. Find label column dynamically
    # 3. Normalize labels to 0/1/2
    # 4. Format text (single event or window)
    # 5. Balance classes if requested
    # 6. Train/val split with stratification
    # 7. Return HF Dataset objects
```

### 6.2 Tokenization & Collation
```python
# Dynamic padding (not fixed max_length)
def collate_fn(batch):
    input_ids = [torch.tensor(item["input_ids"]) for item in batch]
    pad_id = tokenizer.pad_token_id or 0
    padded = torch.nn.utils.rnn.pad_sequence(input_ids, batch_first=True, padding_value=pad_id)
    return {"input_ids": padded, "attention_mask": mask, "labels": labels}
```

### 6.3 Loss & Optimization
```python
# Combined loss pattern (classification + auxiliary)
ce_loss_fn = nn.CrossEntropyLoss()
bce_loss_fn = nn.BCELoss()

total_loss = ce_loss + aux_weight * aux_loss
total_loss.backward()
torch.nn.utils.clip_grad_norm_(params, max_norm=1.0)
optimizer.step()
scheduler.step()
```

---

## 7. EdgeShield Pipeline Patterns

### 7.1 Dual-Stream Initialization
```python
class EdgeShieldPipeline:
    def __init__(self, lsa_model_path=None, bpd_model_path=None, ...):
        # Lazy defaults with fallbacks
        self.lsa = LogSemanticAnalyzer(model_name_or_path=lsa_model_path, device=device)
        self.bpd = BehavioralPatternDetector(model_name_or_path=bpd_model_path, device=device)
        self.correlator = AttackCorrelationEngine(correlation_window_sec=300.0)
        self.edge_engine = EdgeDeploymentEngine()
        self.knowledge_graph = AttackKnowledgeGraph()  # Central MITRE KB
```

### 7.2 Telemetry Processing
```python
def process_telemetry_event(self, auth_log=None, behavior_log=None, ...):
    # Stream A (LSA): Windows auth logs
    # Stream B (BPD): Ransomware behavioral traces  
    # Fuse → Correlate → Return unified result
```

---

## 8. Testing & Evaluation

### 8.1 Evaluation Scripts
```python
# Always load model + tokenizer together
model = AutoModelForSequenceClassification.from_pretrained(model_path).to(device)
tokenizer = AutoTokenizer.from_pretrained(model_path, use_fast=True)  # From model dir!

# Use unified eval.py with --variant flag
python eval.py --variant v1 --csv_path data/optc_test_benchmark.csv
python eval.py --variant v2 --csv_path data/optc_test_benchmark.csv
```

### 8.2 Comparison Benchmarking
```python
# Use scripts/compare_v1_v2.py for side-by-side
python scripts/compare_v1_v2.py --csv_path optc_test_benchmark.csv --num_samples 50
```

---

## 9. Error Handling & Logging

### 9.1 Graceful Degradation
```python
try:
    tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=True)
except Exception:
    tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased", use_fast=True)
```

### 9.2 Explicit Failures for Data Issues
```python
if not label_col:
    raise ValueError(f"[!] Could not identify label column in {resolved_path}")

if not os.path.exists(resolved_path):
    raise FileNotFoundError(f"Dataset not found: {csv_path} (searched: {resolved_path})")
```

---

## 10. Dependency Management

### 10.1 Imports Organization
```python
# 1. Standard library
import os, sys, json, time, argparse
from typing import Dict, List, Tuple, Optional, Union

# 2. Third-party
import pandas as pd
import numpy as np
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# 3. Local (absolute from project root)
from reasoning.engine import ReasoningEngine
from edgeshield.taxonomy import AttackKnowledgeGraph
from v1_single_entry.data_loader import resolve_dataset_path
```

### 10.2 sys.path for Scripts
```python
# In scripts/ only - add project root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
```

---

## 11. Git & Version Control

### 11.1 Commit Messages
```
feat: add BPD attention scoring head
fix: resolve tokenizer vocab mismatch in eval.py
refactor: extract shared data loader to reasoning/
docs: update ADR-004 with DirectML details
```

### 11.2 Protected Branches
- `main` - production ready, protected
- Feature branches: `feat/<description>`, `fix/<description>`

---

## 12. AI Agent Compliance Checklist

Before submitting any code change, **verify**:

- [ ] Type hints on all public functions
- [ ] Module docstring present
- [ ] Uses `resolve_dataset_path()` for data loading
- [ ] Model outputs suffixed with approach tag
- [ ] Tokenizer loaded from model directory first
- [ ] ASCII-only terminal output (`[+]`, `[!]`, `[COMPARISON]`)
- [ ] Dynamic hardware detection (CUDA → DirectML → CPU)
- [ ] Progress JSON written during training
- [ ] No cross-imports between v1/v2 packages
- [ ] Imports organized: stdlib → third-party → local
- [ ] Error messages prefixed with `[!]` or `[ERROR]`
- [ ] Docstrings follow Google/NumPy style
- [ ] No hardcoded paths (use `resolve_dataset_path`, `os.path.join`)
- [ ] Constants in UPPER_SNAKE_CASE at module level

---

## 13. Quick Reference: Key Files to Know

| File | Purpose |
|------|---------|
| `reasoning/engine.py` | Central LMD subtype detection & MITRE mapping |
| `reasoning/mitre_kb.py` | MITRE ATT&CK technique catalog |
| `reasoning/prompt_builder.py` | ChatML prompt formatting for decoder |
| `v1_single_entry/data_loader.py` | Single-event dataset loading |
| `v2_sliding_window/data_loader.py` | Sliding-window dataset loading |
| `edgeshield/pipeline.py` | Dual-stream orchestration |
| `edgeshield/taxonomy.py` | Attack knowledge graph |
| `scripts/train_classifier.py` | Encoder training (v1/v2) |
| `scripts/train_generator.py` | Decoder training (v1/v2) |
| `scripts/train_edgeshield_bpd.py` | BPD stream training |
| `scripts/train_edgeshield_lsa.py` | LSA stream training |
| `eval.py` | Unified evaluation CLI |
| `detect.py` | Threat hunter CLI |
| `scripts/compare_v1_v2.py` | Side-by-side benchmarking |

---

## 14. Evolution Policy

1. **New ADRs** → Add to `specs/04_ARCHITECTURAL_DECISIONS.md`
2. **Breaking changes** → Update this document + version bump
3. **Deprecation** → Mark with `# DEPRECATED` + removal timeline
4. **Agent updates** → Re-read this file + `CLAUDE.md` + `AGENTS.md` on every session start

---

*Generated from codebase analysis via graphify. Enforced by all AI agents operating on this repository.*