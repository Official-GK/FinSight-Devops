# 1. Problem Statement
A multinational financial services company provides risk assessment and analytics services to banks, investment firms, and insurance providers worldwide. The platform processes billions of financial transactions, market feeds, and economic indicators to generate real-time risk assessments. During periods of market volatility, transaction volumes increase significantly, placing immense pressure on infrastructure and analytics systems.

The current environment consists of multiple legacy applications deployed across different infrastructure environments, resulting in operational inefficiencies, delayed releases, and limited observability. Several incidents involving delayed risk calculations and infrastructure outages have exposed weaknesses in monitoring, scalability, and disaster recovery. 

The objective of this project is to design and implement **FinSight**, a secure, cloud-native financial risk analytics platform capable of handling extreme market volatility while maintaining zero downtime.

**Challenges Addressed**
* Handling sudden surges in transaction volume during market volatility
* Eliminating delayed deployments and manual infrastructure provisioning
* Secure management of database credentials and API secrets
* Lack of centralized monitoring and tracing for failed transactions
* Automating disaster recovery and system self-healing
* Seamless deployment rollbacks in case of application failures

# 2. Project Overview
**FinSight** is a DevOps-enabled financial risk analytics solution designed to facilitate real-time risk calculation and infrastructure automation. 

The platform provides:
* Real-time financial transaction risk calculation
* Interactive executive dashboards and analytics
* Live DevOps monitoring and system logs
* Automated scaling during simulated market volatility
* Secure secret injection for database connectivity
* Centralized logging and infrastructure observability
* Automated CI/CD pipelines with intelligent deployment rollbacks

The project follows modern DevOps practices including containerization, CI/CD automation, Infrastructure as Code (IaC), centralized monitoring, and secrets management.

# 3. System Architecture
**Technology Stack**

**Frontend**
* React.js
* Vite
* Tailwind CSS

**Backend**
* Python 
* FastAPI (Analytics API & Risk Engine)
* Uvicorn

**Database**
* PostgreSQL (Asyncpg / Databases)

**Security**
* HashiCorp Vault (Shamir's Secret Sharing)
* Kubernetes Auth Backend

**DevOps Tools**
* Docker & Docker Compose
* Jenkins (Declarative Pipeline)
* Bash Automation (Clean-slate deployment scripts)
* Terraform (Infrastructure as Code for AWS)
* Kubernetes (K3s, Deployments, HPA, Services, NodePorts)
* Prometheus
* Grafana
* ELK Stack (Elasticsearch, Logstash, Kibana, Filebeat)

**Architecture Flow**
Frontend (React)
↓
Ingress / Load Balancer
↓
Analytics API (FastAPI)  ↔  HashiCorp Vault (Secrets)
↓
Risk Engine (FastAPI)
↓
PostgreSQL Database
↓
Monitoring (Prometheus + Grafana)
↓
Centralized Logging (ELK Stack)

# 4. Technical Implementation

## 4.1 Docker & Containerization
The complete platform is containerized using Docker. Each microservice runs in an isolated container to ensure portability and consistency across environments. Multi-stage distroless builds were utilized to keep image sizes small and secure.

**Services included:**
* Frontend Container (Nginx)
* Analytics API Container (Python)
* Risk Engine Container (Python)
* PostgreSQL Container
* Vault Container
* Prometheus & Grafana Containers
* ELK Stack Containers (Elasticsearch, Logstash, Kibana, Filebeat)

*[Insert Screenshot: Built Docker Images / `docker images`]*

## 4.2 CI/CD Pipeline using Jenkins
A declarative Jenkins pipeline automates the software delivery process, strictly ensuring that failing code never reaches production.

**Pipeline Stages:**
1. Source Code Checkout
2. Test & Lint (Static Code Analysis)
3. Docker Image Build (Frontend & Backend)
4. Push to Container Registry / Import to K3s
5. Deploy to AWS Kubernetes Cluster (`kubectl apply`)
6. Verify Deployment (Health checks & pod status)
7. Automated Rollback (Triggers `kubectl rollout undo` and restores previous state on failure)

**Benefits:**
* Automated testing
* Reduced deployment errors with auto-rollbacks
* Continuous Integration and Delivery
* Zero-downtime rolling updates

*[Insert Screenshot: Jenkins Pipeline Dashboard]*

## 4.3 Database Management using PostgreSQL
PostgreSQL serves as the primary relational database for storing financial transaction data and historical risk analytics.

**Data persisted:**
* Transaction IDs
* Transaction Amounts and Currencies
* Transaction Types (PAYMENT, TRANSFER, TRADE)
* Computed Risk Scores and Risk Levels
* Timestamps

The database schema supports secure storage and high-throughput asynchronous insertions from the Analytics API.

*[Insert Screenshot: Database GUI / Query output]*

## 4.4 Security using HashiCorp Vault
Sensitive information such as PostgreSQL database credentials are removed completely from the source code and Kubernetes manifest files. They are stored securely in HashiCorp Vault.

**Advantages:**
* Eliminates hardcoded credentials
* Kubernetes pods authenticate directly with Vault via native K8s Service Accounts
* Vault Sidecar automatically injects secrets directly into the container (`/vault/secrets/database`) at runtime

*[Insert Screenshot: Vault UI / Secret Engine]*

## 4.5 Infrastructure & Kubernetes Orchestration
The underlying cloud infrastructure is provisioned dynamically using HashiCorp Terraform, preventing manual configuration drift.

**Resources Provisioned:**
* Highly Available AWS Cloud Infrastructure
* Amazon EC2 Instance (m7i-flex.large / t3.large optimized for Risk calculations)
* Security Groups and Network rules via Terraform
* K3s (Lightweight Kubernetes) cluster installed on EC2
* Automated bash scripts for namespace wiping, Docker image builds, and manifest application

*[Insert Screenshot: Kubernetes Pods running / `kubectl get pods -n finsight`]*

## 4.6 Auto-Scaling & Disaster Recovery
The platform uses Kubernetes Horizontal Pod Autoscalers (HPA) and a dedicated "Market Volatility Simulator" to test system resilience.

**Examples:**
* When transaction volume spikes (Demo Mode), CPU pressure increases.
* The K8s Metrics Server detects the spike.
* The HPA automatically scales the Risk Engine pods from 5 up to 20 to handle the load.
* If a pod crashes, Kubernetes ReplicaSets instantly self-heal and spin up a replacement.

*[Insert Screenshot: kubectl get hpa scaling up pods]*

## 4.7 Monitoring and Observability
Prometheus collects application and infrastructure metrics from the backend via exposed `/metrics` endpoints.

**Metrics monitored:**
* CPU & Memory Usage per Pod
* API Request Rate (RPS)
* HTTP Response Time (Latency)
* Risk Analysis Throughput
* Active Pod Count

Grafana visualizes these metrics using automated JSON-provisioned interactive dashboards (Infrastructure, Application, and Financial Analytics).

*[Insert Screenshot: Grafana Dashboard]*

## 4.8 Centralized Logging (ELK Stack)
To satisfy the strict observability requirements, the ELK Stack was implemented.
1. **Filebeat** scrapes container logs.
2. **Logstash** parses and tags the logs by microservice.
3. **Elasticsearch** indexes the logs.
4. **Kibana** provides a searchable dashboard to trace individual financial transactions across the cluster.

*[Insert Screenshot: Kibana Logs View]*

# 5. Website Demonstration

**Executive Dashboard**
**Features:**
* Live overview of system health
* Total transactions and real-time risk scores
* Market Volatility Index tracker
*[Insert Screenshot: Main Dashboard]*

**Risk Calculator**
**Features:**
* Submit manual transactions for analysis
* View immediate risk classification (LOW, MEDIUM, HIGH, CRITICAL)
*[Insert Screenshot: Risk Calculator Page]*

**Transactions & Analytics**
**Features:**
* View full transaction history
* Analyze risk distribution and trends over time
*[Insert Screenshot: Analytics Charts]*

**DevOps & Infrastructure Control Center**
**Features:**
* Trigger the "Market Volatility Simulator" (Demo Mode)
* Watch live Kubernetes cluster architecture animations
* View live streaming system logs natively in the browser
* Monitor CI/CD Pipeline status
*[Insert Screenshot: DevOps Section]*

# 6. Results and Achievements
The project successfully demonstrates:
* High-throughput financial risk calculation
* Containerized microservice deployment
* Resilient CI/CD automation with automatic rollbacks
* Infrastructure as Code using Terraform
* Seamless Kubernetes deployment using K3s on AWS EC2
* Dynamic Kubernetes Auto-scaling (HPA)
* Enterprise-grade Security (HashiCorp Vault secret injection)
* Comprehensive Monitoring (Prometheus + Grafana)
* Centralized Tracing (ELK Stack)

The platform provides a highly scalable, fault-tolerant foundation that perfectly addresses all operational inefficiencies highlighted in the initial case study.

# 7. Conclusion
The **FinSight Real-Time Financial Risk Analytics Platform** successfully integrates modern DevOps practices with high-performance financial computing. Through Docker, Jenkins, Terraform, Kubernetes, Vault, Prometheus, Grafana, PostgreSQL, and the ELK Stack, the platform demonstrates secure, scalable, and automated transaction processing.

The project showcases how DevOps methodologies can eliminate delayed releases, improve deployment efficiency, drastically enhance security, and guarantee uptime during extreme market volatility. It serves as a flawless practical implementation of a cloud-native architecture.

# 8. Future Scope and Enhancements
The platform can be enhanced with:
* Integration with real banking legacy systems via message queues (Kafka)
* Machine Learning models for more advanced predictive risk analytics
* Multi-region Kubernetes deployment for global disaster recovery
* Service Mesh (Istio) for advanced traffic routing and mTLS
* Advanced compliance support (PCI-DSS / SOC2)

# 9. Project Links & Endpoints

**Code Repository:**
* **Github:** https://github.com/Official-GK/FinSight-Devops.git

**Live Cloud Endpoints (AWS K3s):**
* **Frontend Dashboard:** http://16.170.218.31:30080
* **Analytics API (Swagger UI):** http://16.170.218.31:30800/docs
* **HashiCorp Vault (Secrets):** http://16.170.218.31:30200
* **Grafana (Dashboards):** http://16.170.218.31:30300
* **Prometheus (Metrics):** http://16.170.218.31:30909
* **Kibana (Centralized Logs):** http://16.170.218.31:30561

**Local CI/CD:**
* **Jenkins Pipeline:** http://localhost:8080
