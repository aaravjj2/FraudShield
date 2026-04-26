FROM python:3.12-slim

WORKDIR /app

# Install deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY api/ api/
COPY ml/inference/ ml/inference/
COPY ml/__init__.py ml/__init__.py
COPY ml/inference/__init__.py ml/inference/__init__.py

# Copy model (built separately via ml/training/train.py)
COPY ml/model.pkl ml/model.pkl

# Create data dir
RUN mkdir -p data

EXPOSE 8000
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
