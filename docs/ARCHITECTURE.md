# FinSight Architecture

## Overview
FinSight is a highly available, cloud-native analytics platform designed to process billions of financial transactions with low-latency. It employs a microservices architecture running on Kubernetes (EKS).

## Components
1. **Frontend (React/Vite)**
   - Serves the executive dashboard.
   - Communicates with Analytics API via Ingress.
2. **Analytics API (FastAPI)**
   - Acts as the main entry point for data ingestion.
   - Handles API routing, initial validation, and metrics collection.
3. **Risk Engine (FastAPI / Compute Heavy)**
   - The core computational engine.
   - Calculates risk scores factoring in market volatility and transaction type.
4. **Database (PostgreSQL StatefulSet)**
   - Persists transactional data and risk scores.
5. **Observability Stack**
   - **Prometheus + Grafana:** Scrapes metrics (`/metrics`) from microservices for real-time dashboarding.
   - **ELK Stack:** Aggregates logs from all containers via Filebeat.
6. **Secret Management (Vault)**
   - Injects DB credentials and API keys dynamically to pods.

## Infrastructure
- **Terraform** provisions the underlying VPC, subnets, NAT gateways, and the EKS cluster.
- **Kubernetes** manages container orchestration, load balancing (Services), and auto-scaling (HPA).
