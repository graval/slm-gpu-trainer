"""
EdgeShield: Edge Deployment & INT8 ONNX Runtime Engine
Implements zero-trust on-premise export, INT8 post-training quantization,
and multi-backend ONNX Runtime inference dispatch (CPU, DirectML, CUDA) with sub-second latency profiling.
"""

import os
import time
import shutil
from typing import Dict, List, Any, Optional, Tuple, Union
import numpy as np
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

try:
    import onnx
    import onnxruntime as ort
    from onnxruntime.quantization import quantize_dynamic, QuantType
    ONNX_AVAILABLE = True
except ImportError:
    onnx = None
    ort = None
    quantize_dynamic = None
    QuantType = None
    ONNX_AVAILABLE = False


class EdgeDeploymentEngine:
    """
    Manages ONNX model export, INT8 post-training quantization (PTQ),
    and edge-optimized inference execution using ONNX Runtime.
    """
    def __init__(self, export_dir: str = "models/onnx_edgeshield"):
        self.export_dir = export_dir
        os.makedirs(export_dir, exist_ok=True)
        self.available_providers = ort.get_available_providers() if ort else ["CPUExecutionProvider"]

    def export_to_onnx(
        self,
        pytorch_model: torch.nn.Module,
        tokenizer: Any,
        model_name: str = "edgeshield_lsa",
        seq_len: int = 512
    ) -> str:
        """
        Exports a PyTorch Transformer sequence classifier to standard ONNX FP32 format.
        """
        output_path = os.path.join(self.export_dir, f"{model_name}.onnx")
        pytorch_model.eval()
        
        dummy_input = tokenizer(
            "EventID: 4624 LogonType: 10 User: admin Computer: DC01",
            max_length=seq_len,
            padding="max_length",
            truncation=True,
            return_tensors="pt"
        )
        input_ids = dummy_input["input_ids"]
        attention_mask = dummy_input["attention_mask"]

        # Dynamic axes for variable batch size
        dynamic_axes = {
            "input_ids": {0: "batch_size", 1: "sequence_length"},
            "attention_mask": {0: "batch_size", 1: "sequence_length"},
            "logits": {0: "batch_size"}
        }

        class OnnxWrapper(torch.nn.Module):
            def __init__(self, base_model):
                super().__init__()
                self.base_model = base_model
            def forward(self, input_ids, attention_mask):
                out = self.base_model(input_ids=input_ids, attention_mask=attention_mask)
                return out.logits

        wrapper = OnnxWrapper(pytorch_model).cpu()

        torch.onnx.export(
            wrapper,
            (input_ids.cpu(), attention_mask.cpu()),
            output_path,
            input_names=["input_ids", "attention_mask"],
            output_names=["logits"],
            dynamic_axes=dynamic_axes,
            opset_version=14,
            do_constant_folding=True
        )
        return output_path

    def quantize_int8(self, onnx_model_path: str) -> str:
        """
        Applies INT8 Dynamic Post-Training Quantization (PTQ) to the ONNX graph.
        Reduces checkpoint size by ~75% while keeping latency < 200 ms per window.
        """
        if not ONNX_AVAILABLE or quantize_dynamic is None:
            raise RuntimeError("ONNX Runtime quantization tools not available.")

        quantized_path = onnx_model_path.replace(".onnx", "_int8.onnx")
        quantize_dynamic(
            model_input=onnx_model_path,
            model_output=quantized_path,
            weight_type=QuantType.QInt8,
            per_channel=True,
            reduce_range=False
        )
        return quantized_path

    def create_inference_session(self, onnx_path: str, prefer_gpu: bool = False) -> Any:
        """
        Instantiates an optimized ONNX Runtime InferenceSession.
        Dispatches compute across DirectML (Intel Arc/NPU/AMD/NVIDIA on Windows), CUDA, or CPU.
        """
        if not ONNX_AVAILABLE or ort is None:
            raise RuntimeError("ONNX Runtime is not installed in the active environment.")

        providers = []
        if prefer_gpu:
            if "DmlExecutionProvider" in self.available_providers:
                providers.append("DmlExecutionProvider")
            if "CUDAExecutionProvider" in self.available_providers:
                providers.append("CUDAExecutionProvider")
        providers.append("CPUExecutionProvider")

        sess_options = ort.SessionOptions()
        sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        sess_options.intra_op_num_threads = os.cpu_count() or 8
        
        session = ort.InferenceSession(onnx_path, sess_options, providers=providers)
        return session

    def benchmark_latency(
        self,
        session: Any,
        tokenizer: Any,
        num_runs: int = 50,
        seq_len: int = 512
    ) -> Dict[str, Any]:
        """
        Runs rigorous edge latency benchmarking over 512-token windows.
        """
        dummy_text = "[T_0] [EID:4624] [HOST:DC01] [USER:Administrator] [LOGON_TYPE:10] [CMD:psexec.exe \\\\192.168.1.50 cmd.exe]"
        inputs = tokenizer(
            dummy_text,
            max_length=seq_len,
            padding="max_length",
            truncation=True,
            return_tensors="np"
        )
        
        ort_inputs = {
            "input_ids": inputs["input_ids"].astype(np.int64),
            "attention_mask": inputs["attention_mask"].astype(np.int64)
        }

        # Warmup
        for _ in range(5):
            _ = session.run(None, ort_inputs)

        latencies = []
        for _ in range(num_runs):
            t0 = time.perf_counter()
            _ = session.run(None, ort_inputs)
            t1 = time.perf_counter()
            latencies.append((t1 - t0) * 1000.0)

        latencies = np.array(latencies)
        return {
            "avg_latency_ms": round(float(np.mean(latencies)), 2),
            "median_latency_ms": round(float(np.median(latencies)), 2),
            "p95_latency_ms": round(float(np.percentile(latencies, 95)), 2),
            "min_latency_ms": round(float(np.min(latencies)), 2),
            "max_latency_ms": round(float(np.max(latencies)), 2),
            "runs": num_runs,
            "meets_paper_target": bool(np.mean(latencies) < 200.0) # < 200 ms target from paper
        }
