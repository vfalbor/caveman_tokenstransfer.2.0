FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    LLMLINGUA_DEVICE=cpu

WORKDIR /app

# Install build deps for sentencepiece etc.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential git curl ca-certificates \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
# Pre-install torch CPU wheels to skip CUDA download (~2GB saved)
RUN pip install --index-url https://download.pytorch.org/whl/cpu torch==2.4.1 \
 && pip install -r requirements.txt

COPY app.py .

# Model is downloaded on first call. To pre-warm, uncomment:
# RUN python -c "from llmlingua import PromptCompressor; PromptCompressor(model_name='microsoft/llmlingua-2-xlm-roberta-large-meetingbank', use_llmlingua2=True, device_map='cpu')"

EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
  CMD curl -fs http://localhost:8080/health || exit 1

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
