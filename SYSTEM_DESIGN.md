# System Design
## Local
### Architecture Overview
The solution adopts a clean two‑tier pattern. A **React + Vite** single‑page application (served on port 3000) handles all user interaction—chatting, document upload and metric visualisation.  Requests flow over HTTPS/REST to a **FastAPI** backend (port 8000) that exposes versioned endpoints under `/api/v1`, keeping the client stateless and the transport simple.

Inside the backend, the Retrieval‑Augmented‑Generation pipeline fans out to four specialised services: **Redis** stores conversation turns and cached summaries; **ChromaDB** holds vector embeddings for low‑latency semantic search; **AWS Bedrock** (Claude 3.5 Haiku) provides generation, intent classification and safety checks; and **Amazon S3** (optional) keeps raw documents for durable backup.  Orchestration happens in `RAGService`, which retrieves relevant chunks from Chroma, injects recent dialogue from Redis, calls Bedrock, and returns a concise answer to the client.

Below is the equivalent Mermaid diagram.

```mermaid
graph TD
    user["User<br>External Actor"]

    subgraph "Web Application<br>React / Vite"
        app_root["React App Entry<br>React / TSX"]
        ui_components["UI Components<br>React / TSX"]
        api_client["API Client<br>TypeScript"]
        app_root -->|renders| ui_components
        ui_components -->|sends requests via| api_client
    end

    subgraph "Backend API<br>Python / FastAPI"
        api_entry["API Server Entry<br>Python / FastAPI"]
        api_endpoints["API Endpoints<br>Python / FastAPI"]
        rag_service["RAG Service<br>Python"]
        doc_mgmt["Document Mgmt<br>Python"]
        bedrock_adapter["Bedrock Service Adapter<br>Python / Boto3"]
        conv_memory["Conversation Memory<br>Python / Redis"]
        api_entry -->|initializes| api_endpoints
        api_endpoints -->|routes to| rag_service
        api_endpoints -->|manages| doc_mgmt
        rag_service -->|loads to| doc_mgmt
        rag_service -->|uses| bedrock_adapter
        rag_service -->|retrieves from| conv_memory
    end

    subgraph "External Systems"
        ai_apis["AI APIs<br>AWS Bedrock"]
        vector_db["Vector Databases<br>ChromaDB"]
        data_store["Data Stores<br>Redis"]
        cloud_storage["Cloud Storage<br>AWS S3"]
    end

    user -->|interacts with| ui_components
    api_client -->|calls| api_endpoints
    conv_memory -->|stores/retrieves| vector_db
    doc_mgmt -->|loads documents to| cloud_storage
    bedrock_adapter -->|invokes| ai_apis
    conv_memory -->|stores/retrieves| data_store

```

### Design Trade‑offs and Assumptions

| Decision | Rationale | Implication |
|----------|-----------|-------------|
| **Local persistent ChromaDB** | Easiest to run in Docker Compose without managed services. | Not highly available; single‑node persistence only. |
| **In‑memory metrics (Python lists)** | Fast to prototype; zero external state. | Metrics reset on container restart; not horizontally scalable. |
| **Fixed chunk size = 1000 chars / overlap = 200** | Balances recall vs. indexing speed for mixed‑format docs. | May under‑segment very long paragraphs; tuning needed for other corpora. |
| **Last‑6 message context window** | Lightweight memory that avoids prompt bloat. | Older context drops off; nuance may be lost in long chats. |


## Cloud
### Architecture Overview
The cloud architecture is designed to be scalable, secure, and resilient, deploying all components on AWS and leveraging managed services for storage, compute, and networking.

Frontend and backend run in containers orchestrated by ECS Fargate, exposed via Application Load Balancer (ALB). Redis and ChromaDB persist on ElastiCache and EFS, respectively. Documents are stored in S3 and credentials/configuration in Secrets Manager. The LLM model is consumed via AWS Bedrock.

```mermaid
graph TD
  %% Clusters and subgraphs
  subgraph Internet [Internet]
    A[Users]
  end

  subgraph VPC [AWS VPC]
    direction TB

    subgraph Public [Public Subnets]
      direction LR
      ALB_FE[ALB Frontend<br/>port 3000]
      ALB_BE[ALB Backend<br/>port 8000]
    end

    subgraph ECSCluster [ECS Cluster]
      direction TB

      subgraph Frontend [Frontend Task]
        FE[ECS Frontend Service<br/>Fargate: 256 CPU, 512 MB RAM]
      end

      subgraph Backend [Backend Task]
        BE[ECS Backend Service<br/>Fargate: 512 CPU, 1 GB RAM]
      end
    end

    subgraph Data [Data Layer]
      direction LR
      Redis[ElastiCache Redis<br/>t3.micro, Redis 7.0]
      EFS[EFS File System<br/>ChromaDB Persistence]
    end

    subgraph Services [AWS Services]
      direction LR
      subgraph ECR_Containers [ECR – Container Images]
        FE_Image[Frontend Image]
        BE_Image[Backend Image]
      end
      SM[Secrets Manager<br/>stori/rag/backend]
      S3[S3 – Document Storage]
      Bedrock[AWS Bedrock<br/>Claude 3.5 Haiku]
    end
  end

  %% Connections
  A -->|HTTPS| ALB_FE
  A -->|HTTPS| ALB_BE
  ALB_FE -->|HTTP| FE
  ALB_BE -->|HTTP| BE
  FE -->|VITE_API_URL| ALB_BE
  BE -->|Redis 6379| Redis
  BE -->|NFS 2049| EFS
  BE -->|IAM Auth| SM
  BE -->|S3 API| S3
  BE -->|Bedrock API| Bedrock
```

### Cloud system description
- **Frontend**: React + Vite, deployed on ECS Fargate, exposed via ALB (port 3000).
- **Backend**: FastAPI, deployed on ECS Fargate, exposed via ALB (port 8000), integrates LangChain and orchestrates the RAG logic.
- **Vector DB**: Persistent ChromaDB on EFS, accessible from the backend.
- **Cache/Memory**: Managed Redis (ElastiCache), for conversational context and caching.
- **Storage**: S3 for documents, EFS for vector persistence.
- **Security**: Secrets Manager for credentials/configuration, IAM roles with least privilege.
- **LLM**: AWS Bedrock (Claude 3.5 Haiku) for generation, classification, and safety checks.
- **Network**: VPC with public and private subnets, restrictive security groups.
- **Orchestration**: ECS Fargate for scalability and serverless deployment.

### Cloud trade-offs and considerations
| Decision | Rationale | Implication |
|----------|-----------|-------------|
| **ECS Fargate** | Serverless deployment, no server management | Pay-per-use cost, possible cold starts |
| **ALB for frontend/backend** | Centralized TLS security and load balancing | Additional configuration, ALB cost |
| **ElastiCache Redis** | Managed cache and memory, high availability | Cost and instance limits |
| **ChromaDB on EFS** | Persistence without data loss between deployments | Network latency, not optimal for very high loads |
| **S3 for documents** | Durable and scalable storage | Access latency, storage and access costs |
| **Secrets Manager** | Secure secrets and configuration management | Cost per secret, IAM integration |
| **Bedrock API** | Managed LLM, no infrastructure management | Pay-per-use cost, AWS dependency |
| **VPC and SGs** | Network isolation and control | Configuration complexity |

# Future Improvements (If Given More Time)

- [ ] **Streaming responses**: Implement streaming responses for better user experience.
- [ ] **Authentication**: Add login and logout functionality.
- [ ] **Vector Database Migration**: Replace EFS ChromaDB with OpenSearch or pgvector for better scalability and performance.
- [ ] **Granular IAM Permissions**: Implement least-privilege access with custom IAM policies instead of broad permissions.
- [ ] **Multi-Region Deployment**: Active-active setup with Route 53 failover for high availability.
- [ ] **Auto-scaling**: Implement ECS auto-scaling based on CPU/memory usage and custom metrics.
- [ ] **Document Processing Pipeline**: Implement async document processing with progress tracking.
- [ ] **Monitoring & Alerting**: CloudWatch custom alarms, and SNS notifications for critical issues.
- [ ] **Backup & Recovery**: Automated backups for EFS, S3 versioning, and disaster recovery procedures.
- [ ] **Security Enhancements**: WAF, VPC endpoints, encryption at rest/transit, and security scanning.
- [ ] **Grafana dashboards fed by Prometheus exporter.**
- [ ] **Fully Automated CI/CD pipeline.**
