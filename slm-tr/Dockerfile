# GPU default: PyTorch 2.11 + CUDA 12.8 (RTX 50-series / sm_120 Blackwell support).
# CPU build: pass BASE_IMAGE=pytorch/pytorch:2.11.0-cpu and REQUIREMENTS_FILE=requirements-docker.txt
ARG BASE_IMAGE=pytorch/pytorch:2.11.0-cuda12.8-cudnn9-runtime

FROM ${BASE_IMAGE}

ARG REQUIREMENTS_FILE=requirements-docker-gpu.txt

ENV PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    PIP_BREAK_SYSTEM_PACKAGES=1 \
    NVIDIA_VISIBLE_DEVICES=all \
    NVIDIA_DRIVER_CAPABILITIES=compute,utility

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Verify base PyTorch before layering ML deps (fail fast on wrong CUDA arch)
RUN python -c "\
import torch; \
ver = tuple(int(x) for x in torch.__version__.split('.')[:2]); \
print('PyTorch', torch.__version__, 'CUDA', torch.version.cuda); \
assert ver >= (2, 7), f'PyTorch 2.7+ required for RTX 5090, got {torch.__version__}'; \
"

COPY requirements-docker.txt requirements-docker-gpu.txt ./
RUN pip install --upgrade pip && \
    pip install -r "${REQUIREMENTS_FILE}"

COPY data/loader.py ./data/loader.py
COPY scripts/ ./scripts/
COPY train_classifier.py train_generator.py detect.py app.py eval.py ./

COPY docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh

ENTRYPOINT ["/app/docker-entrypoint.sh"]
