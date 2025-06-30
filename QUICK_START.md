# Quick Start Guide

## 0. Prerequisites  
- **Docker Engine** ≥ 24.x **and** Docker Compose Plugin ≥ 2.24  
  `docker compose version` should succeed.  
- **AWS CLI v2** configured with an IAM identity that has **Amazon Bedrock**, **S3** and **STS** permissions.  
- **Git** ≥ 2.40 

---

## 1. Clone the repository
```bash
git clone https://github.com/enriquegomeztagle/stori-genai-rag.git
cd stori-genai-rag
```

---

## 2. Configure the environment
Copy the sample and fill in the blanks:

```bash
cp env.example .env
```

| Variable | Example value | Purpose |
|----------|---------------|---------|
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | `AKIA…` | Credentials for Bedrock & S3 |
| `AWS_REGION` | `us-west-2` | Region that supports the chosen Bedrock model |
| `BEDROCK_MODEL_ID` | `anthropic.claude-3-5-haiku-20241022-v1:0` | LLM used for generation |
| `EMBEDDING_MODEL` | `amazon.titan-embed-text-v1` | Embedding model for vector store |
| `S3_BUCKET_NAME` | `stori-genai-rag-demo` | Optional raw‑document archive (leave blank to disable) |
| `REDIS_URL` | `redis://redis:6379/0` | Chat‑memory store |
| `CHROMA_PERSIST_DIRECTORY` | `/chroma` | Volume path for vectors |

---

## 3. Launch the local stack

### One‑liner (recommended)
```bash
chmod +x start.sh      # one‑time
./start.sh             # builds & starts everything
```

### Manual
```bash
docker compose pull    # pre‑fetch public base images
docker compose up --build -d
```

**Services**

| Container | Port | Description |
|-----------|------|-------------|
| `frontend` | 3000 | React + Vite UI |
| `backend`  | 8000 | FastAPI REST API |
| `redis`    | 6379 | In‑memory cache & chat memory |
| `chroma`   | 8001 | Persistent vector database |

---

## 4. Smoke‑test the API
```bash
# Overall health
curl http://localhost:8000/api/v1/health/health

# Bedrock round‑trip
time curl -X POST http://localhost:8000/api/v1/conversation/chat \
     -H "Content-Type: application/json" \
     -d '{"message": "¿Quién fue Emiliano Zapata?"}'
```
A JSON answer should return within a few seconds.

---

## 5. Open the application
```bash
open http://localhost:3000          # Chat UI
open http://localhost:8000/docs     # Swagger / ReDoc
```

---

## 6. Upload a document
1. Go to **Upload**.  
2. Drop any PDF/DOCX/TXT or click **Upload Sample Mexican Revolution Document**.  
3. The backend splits the file into chunks, generates embeddings, stores them in ChromaDB and (optionally) pushes the raw file to S3.

---

## 7. Chat & iterate
Ask in **Spanish or English**. Follow‑up questions reuse short‑term memory stored in Redis.

Example prompts:
```text
"¿Qué planteaba el Plan de Ayala?"
"¿Quién fue Emiliano Zapata?"
```

---

## 8. Shutdown & cleanup
```bash
docker compose down            # stop containers
docker compose down -v         # additionally remove named volumes (erases vectors & redis)
```

---

## 9. Troubleshooting

| Symptom | Log snippet | Fix |
|---------|-------------|-----|
| Bedrock 4xx | `AmazonBedrockException: AccessDeniedException` | Verify IAM policy & region |
| Port busy | `Error: port 8000 already allocated` | `lsof -i :8000` & kill or change ports |
| Redis unreachable | `ConnectionError: Error 111 connecting to redis:6379` | Containers still starting; wait or `docker compose restart redis` |
| Chroma lock | `ValueError: Storage already locked` | Remove volume: `docker compose down -v` |

---
