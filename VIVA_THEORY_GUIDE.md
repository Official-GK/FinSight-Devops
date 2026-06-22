# 🎓 FinSight Project – Viva Theory & Interview Guide

This document contains all the theoretical concepts, definitions, and likely questions the panel will ask you regarding the tools and architecture you used in your project.

---

## 1. General DevOps Concepts

**What is DevOps?**
DevOps is the combination of cultural philosophies, practices, and tools (Development + Operations) designed to increase an organization's ability to deliver applications at high velocity. It aims to shorten the systems development life cycle and provide continuous delivery with high software quality.

**What is CI/CD?**
* **CI (Continuous Integration):** The practice of automating the integration of code changes from multiple contributors into a single software project. (e.g., Jenkins pulling code, building Docker images, running tests).
* **CD (Continuous Delivery/Deployment):** The automated deployment of the verified code to a staging or production environment. (e.g., Jenkins running `kubectl apply` to deploy to AWS).

**Microservices vs Monolith:**
* **Monolith:** All components of the software are bundled into a single massive program. If one part fails, the whole application crashes. Hard to scale.
* **Microservices:** Breaking the application into small, independent services (e.g., Frontend, Analytics API, Risk Engine). They communicate via APIs. If the Analytics API crashes, the Database stays up. Much easier to scale individually.

---

## 2. Docker & Containerization

**What is Docker?**
Docker is a platform designed to help developers build, share, and run modern applications. It packages software into standardized units called **containers** that have everything the software needs to run including libraries, system tools, code, and runtime.

**Why use Docker instead of Virtual Machines (VMs)?**
VMs require a full, heavy guest operating system for every application. Docker containers share the host machine's OS kernel, making them incredibly lightweight, fast to boot, and resource-efficient.

**What is a Dockerfile?**
A text document that contains all the commands a user could call on the command line to assemble an image. (e.g., `FROM python:3.12`, `RUN pip install`, `CMD ["uvicorn"]`).

**What is the "Build Once, Run Anywhere" concept?**
A Docker container behaves exactly the same on your Mac laptop as it does on a massive AWS Linux server. It eliminates the "It works on my machine" problem.

---

## 3. Kubernetes (K8s) & K3s

**What is Kubernetes?**
Kubernetes is an open-source container orchestration engine for automating deployment, scaling, and management of containerized applications.

**What is K3s?**
K3s is a highly available, certified Kubernetes distribution designed for production workloads in unattended, resource-constrained, remote locations. It is a lightweight version of Kubernetes (perfect for running on a single AWS EC2 instance).

**Key Kubernetes Components:**
* **Pod:** The smallest deployable computing unit in Kubernetes. A pod encapsulates one or more Docker containers (e.g., your Risk Engine container runs inside a Pod).
* **Deployment:** Provides declarative updates for Pods. It tells Kubernetes how many copies (replicas) of a Pod should run, and handles self-healing (if a Pod crashes, the Deployment spins up a new one).
* **StatefulSet:** Similar to a Deployment, but used for stateful applications like Databases (PostgreSQL). It guarantees the ordering and uniqueness of these Pods, and ensures data isn't lost if the Pod restarts.
* **Service:** An abstraction that defines a logical set of Pods and a policy by which to access them (like an internal load balancer). E.g., `ClusterIP` for internal communication, `NodePort` to expose it to the internet.
* **Ingress:** Manages external access to the services in a cluster, typically HTTP/HTTPS.

---

## 4. Kubernetes Horizontal Pod Autoscaler (HPA)

**What is HPA?**
The Horizontal Pod Autoscaler automatically updates a workload resource (like a Deployment) with the aim of automatically scaling the workload to match demand.

**How does it work in your project?**
1. **Metrics Server:** You have a Metrics Server running in your cluster that constantly tracks CPU and Memory usage of all pods.
2. **Thresholds:** You configured the `risk-engine-hpa` to monitor the CPU. The target is set to 70%.
3. **Scaling Up:** If the Risk Engine experiences heavy transaction volume (market volatility) and its CPU hits 70%, the HPA tells the Deployment to spin up new Pods (up to a maximum of 6).
4. **Scaling Down:** When the market cools down and CPU drops, the HPA kills the extra pods to save AWS compute resources.

*Difference between Horizontal and Vertical Scaling:*
* **Horizontal:** Adding *more* machines/pods (Scaling OUT). (This is what HPA does).
* **Vertical:** Adding *more power* (CPU/RAM) to an existing machine (Scaling UP).

---

## 5. HashiCorp Vault (Security)

**What is HashiCorp Vault?**
Vault is a tool for securely accessing *secrets*. A secret is anything that you want to tightly control access to, such as API keys, passwords, or certificates.

**Why did you use it?**
To prevent hardcoding our PostgreSQL database passwords into our source code or Kubernetes manifest files. Hardcoded secrets are a massive security vulnerability.

**How does it work?**
Vault encrypts the password and stores it centrally. When the FastAPI application starts, it authenticates with Vault using a secure Kubernetes Service Account, retrieves the password directly into memory, and connects to the database.

---

## 6. Prometheus & Grafana (Monitoring)

**What is Prometheus?**
An open-source systems monitoring and alerting toolkit. It works on a **"Pull" model**. Instead of applications pushing data to Prometheus, Prometheus connects to the applications via HTTP (the `/metrics` endpoint) and scrapes/pulls the current data (like CPU usage, active transactions, latency).

**What is Grafana?**
Grafana is the visualization layer. It doesn't collect data itself; it queries the Prometheus database and turns those raw numbers into beautiful, interactive graphs and executive dashboards.

---

## 7. ELK Stack (Logging)

**What is ELK?**
ELK stands for **Elasticsearch, Logstash, and Kibana**. (Though in your project, you used **Filebeat** instead of Logstash, which is the modern standard for Kubernetes).

**Why do you need it?**
In a microservices architecture, you might have 15 different servers running at once. If a transaction fails, you cannot SSH into 15 different servers to look at text files. You need Centralized Logging.

**How does the flow work?**
1. **Filebeat (The Shipper):** Runs as a `DaemonSet` on the Kubernetes node. It automatically captures all terminal logs from every single running Docker container.
2. **Elasticsearch (The Database):** Filebeat sends the logs to Elasticsearch, which acts as a powerful search engine designed to index huge amounts of text data incredibly fast.
3. **Kibana (The UI):** The web interface where you can type in a Transaction ID and instantly see every log related to that transaction across the entire cluster.

---

## 8. Tricky Panel Questions & Answers

**Q: Why didn't you just deploy your code directly to the AWS EC2 instance without Docker or Kubernetes?**
> **A:** Deploying directly to the OS creates "configuration drift" and the "it works on my machine" problem. By using Docker, I guarantee environment consistency. By using Kubernetes, I get automatic self-healing, zero-downtime deployments, and horizontal auto-scaling which are required for high-availability financial systems.

**Q: What happens if your AWS EC2 instance crashes entirely? (Hardware failure)**
> **A:** Currently, the cluster is running on a single Node. If the Node dies, the application goes down. However, the architecture is completely portable. In a production scenario, I would use a multi-node EKS cluster. If one node dies, the Kubernetes Control Plane automatically moves the pods to a surviving node.

**Q: Your HPA scales the Risk Engine based on CPU. What if the bottleneck is memory instead?**
> **A:** HPA supports multiple metrics. While I configured it for CPU (since risk calculations are math-heavy), it can easily be configured to scale based on Memory usage, or even custom metrics like "Active HTTP Requests in the Queue" provided by Prometheus.

**Q: How does Jenkins authenticate to AWS to deploy the code?**
> **A:** Jenkins runs securely and uses its internal "Credentials Manager". It stores the Kubernetes `kubeconfig` file or AWS IAM roles. The pipeline executes `kubectl apply` using those secure credentials to communicate with the cluster's API server over HTTPS.
