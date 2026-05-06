# ---- Nexus-Graph AI Service ----
FROM python:3.12-slim

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc curl && \
    rm -rf /var/lib/apt/lists/*

COPY ai-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ai-service .
COPY shared/proto ./shared/proto
RUN mkdir -p src/generated && \
    python -m grpc_tools.protoc \
      -I./shared/proto \
      --python_out=./src/generated \
      --grpc_python_out=./src/generated \
      ./shared/proto/nexus.proto && \
    touch src/generated/__init__.py && \
    sed -i 's/^import nexus_pb2/from src.generated import nexus_pb2/' src/generated/nexus_pb2_grpc.py

EXPOSE 8001

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8001"]
