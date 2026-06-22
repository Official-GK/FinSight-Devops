# 📂 FinSight Project – Codebase Navigation Guide

If the panel asks you to "Show me the code for [Feature]", use this cheat sheet to instantly know exactly which file to open in your IDE.

---

## 🎯 Quick Reference Cheat Sheet

### 1. "Show me your CI/CD Pipeline code."
**Open File:** `Jenkinsfile` (Root Directory)
> **What to point out:** Point out the different `stages` (Build Frontend, Build Backend, Run Tests, Docker Build). Show them the final stage where it simulates deploying the application or running rollbacks.

### 2. "Show me your Infrastructure as Code (IaC)."
**Open File:** `terraform/main.tf`
> **What to point out:** Show them the AWS provider block, the VPC creation, and the EC2 Instance/EKS resource blocks.

### 3. "Show me your Kubernetes deployment manifests."
**Open File:** Any file in the `kubernetes/` folder.
* Open `kubernetes/risk-engine.yaml` to show a standard Deployment with resource limits.
* Open `kubernetes/postgres.yaml` to show a `StatefulSet` and a `PersistentVolumeClaim` (which proves you know how to save database data permanently).
* Open `kubernetes/config.yaml` to show the `finsight-config` ConfigMap and `finsight-secrets`.

### 4. "Show me how you containerized your Python APIs."
**Open File:** `analytics-api/Dockerfile` or `risk-engine/Dockerfile`
> **What to point out:** Show them the `FROM python:3.12-slim` line. Explain that you used a "slim" image to reduce the container size for security and speed. Show the `COPY` and `RUN pip install` commands.

### 5. "Show me where the actual Risk Calculation math happens."
**Open File:** `risk-engine/app/main.py`
> **What to point out:** This is the FastAPI application for the Risk Engine. Scroll to the `analyze_risk` endpoint where the mathematical risk score logic and classification (LOW, MEDIUM, HIGH, CRITICAL) are defined.

### 6. "Show me how the Frontend communicates with the Backend API."
**Open File:** `frontend/src/services/api.ts`
> **What to point out:** This file uses Axios to make `GET` and `POST` requests to the Analytics API. 
> Also open `frontend/src/context/SimulationContext.tsx` to show how the "Market Volatility" simulation logic is handled.

### 7. "Show me how your API connects to PostgreSQL."
**Open File:** `analytics-api/app/database.py` and `analytics-api/app/in_memory_db.py`
> **What to point out:** Explain that the application is designed to write transaction data synchronously. Show the code where it inserts records using the credentials it fetched from Kubernetes Secrets/Vault.

---

## 📁 General Directory Structure Overview

If they ask you to walk them through your whole project, here is the high-level layout:

```text
FinSight-Devops/
│
├── Jenkinsfile                 # The master CI/CD pipeline automation script.
├── docker-compose.yml          # Used for running the whole stack locally for testing.
├── deploy_to_aws.sh            # The bash script used to wipe and redeploy the cluster.
│
├── kubernetes/                 # All Kubernetes Manifests
│   ├── frontend.yaml           # React web deployment
│   ├── analytics-api.yaml      # Python API deployment
│   ├── risk-engine.yaml        # Python engine + HPA (Autoscaler)
│   ├── postgres.yaml           # Database StatefulSet
│   ├── vault.yaml              # HashiCorp Vault security deployment
│   ├── prometheus.yaml         # Metrics scraping
│   ├── grafana.yaml            # Dashboard visualization
│   ├── elasticsearch.yaml      # ELK Stack (Database for logs)
│   ├── kibana.yaml             # ELK Stack (UI for logs)
│   └── filebeat.yaml           # Daemonset that scrapes container logs
│
├── frontend/                   # React.js Web Application
│   ├── Dockerfile              # Instructions to build the Nginx container
│   ├── package.json            # Node.js dependencies
│   └── src/                    # The actual React UI code (components, pages)
│
├── analytics-api/              # FastAPI Gateway
│   ├── Dockerfile              # Instructions to build the Python container
│   ├── requirements.txt        # Python dependencies
│   └── app/
│       ├── main.py             # Entry point, sets up Prometheus metrics
│       └── routers/            # HTTP endpoint definitions
│
├── risk-engine/                # Heavy Computation Service
│   ├── Dockerfile
│   └── app/
│       └── main.py             # Contains the risk scoring algorithm
│
└── terraform/                  # Infrastructure as Code
    ├── main.tf                 # AWS Resources (EC2, VPC, Security Groups)
    └── variables.tf            # Configurable AWS variables
```
