# 🎓 Gaurav's Master Presentation Steps for the Panel

**Before you start:** 
* Have your Mac Terminal open.
* Have 5 browser tabs open, ready to go.

---

## 🟢 STEP 1: The Introduction (1-2 mins)
**Action:** Just talk to the panel.
**What to say:** 
> "Good morning panel. My project is **FinSight**, a Real-Time Financial Risk Analytics Platform. During periods of high market volatility, traditional banking systems crash because they can't handle the transaction load. 
> 
> To solve this, I migrated the legacy applications to a cloud-native microservices architecture on AWS. I implemented automated Jenkins CI/CD, Kubernetes auto-scaling, HashiCorp Vault for security, and Prometheus/Grafana for monitoring."

---

## 🟢 STEP 2: Show the CI/CD Pipeline (Jenkins)
**Action:** Open your Mac Terminal.
**Command to run:**
```bash
bash RUN_JENKINS.sh
```
**Action:** Open your browser to `http://localhost:8080`. Click on the FinSight project and click **"Build Now"**.
**What to say:** 
> "To solve the issue of delayed deployments, I built an automated Declarative Jenkins pipeline. When code is updated, Jenkins automatically checks out the code, builds isolated Docker images, runs Python tests, and verifies the deployment. As you can see, the pipeline is executing perfectly through every stage."

*(If they ask how it deploys to AWS if it's running locally, tell them: "In production, Jenkins holds the AWS SSH keys and uses kubectl to apply the manifests directly to the cloud.")*

---

## 🟢 STEP 3: Show the Live Application (Frontend)
**Action:** Open your browser to **`http://16.170.218.31:30080`**
**What to say:** 
> "Here is the live dashboard hosted on AWS. It is constantly polling our Analytics API to evaluate transactions in real time. The architecture consists of a React frontend, a FastAPI Analytics gateway, and a Python Risk Engine."
**Action:** Click on the **"Infrastructure"** tab on the left.
> "This control center gives us a live view of our Kubernetes Cluster Architecture, showing traffic flowing from the Load Balancer to the API and into PostgreSQL."

---

## 🟢 STEP 4: Prove it is running on AWS Kubernetes
**Action:** Open a NEW tab in your Mac Terminal.
**Command to run:**
```bash
ssh -i ~/Desktop/demo-key.pem ubuntu@16.170.218.31
```
**Command to run:**
```bash
sudo k3s kubectl get pods -n finsight
```
**What to say:**
> "As you can see on the AWS server, all 11 of my microservices are currently running inside Kubernetes."

---

## 🟢 STEP 5: Demonstrate Kubernetes Scaling & Self-Healing
**Action:** Stay in your AWS Terminal.

**1. Show Auto-Scaling:**
**Command to run:**
```bash
sudo k3s kubectl scale deployment risk-engine-deployment --replicas=5 -n finsight
```
**Command to run immediately after:**
```bash
sudo k3s kubectl get pods -l app=risk-engine -n finsight
```
**What to say:** 
> "If market volatility spikes, Kubernetes instantly scales up our Risk Engine pods. As you can see, it is immediately provisioning new servers to handle the traffic."

**2. Show Self-Healing:**
**Command to run:**
```bash
sudo k3s kubectl delete pod -l app=frontend -n finsight
```
**Command to run immediately after:**
```bash
sudo k3s kubectl get pods -l app=frontend -n finsight -w
```
**What to say:**
> "If a server crashes, Kubernetes detects it instantly and spins up a replacement in milliseconds, guaranteeing zero downtime." (Hit `Ctrl+C` to stop watching the pods).

---

## 🟢 STEP 6: Show Security (HashiCorp Vault)
**Action:** Open browser to **`http://16.170.218.31:30200`**
**Login Token:** `vault-token-123`
**Action:** Click `secret/` → `finsight/` → `database`. Click the little "Eye" icon to reveal the password.
**What to say:**
> "Security is critical in finance. Instead of hardcoding database passwords in GitHub, I deployed HashiCorp Vault. The database credentials are fully encrypted, and the microservices fetch them securely at runtime."

---

## 🟢 STEP 7: Show Monitoring (Grafana)
**Action:** Open browser to **`http://16.170.218.31:30300`**
**Login:** `admin` / `finsight123`
**What to say:**
> "To give executives visibility, I deployed Prometheus and Grafana. Here we have a live, centralized view of the platform's health, showing API Requests per second, latency, and Risk Level distributions in real-time."

---

## 🟢 STEP 8: Show Centralized Logging (Kibana)
**Action:** Open browser to **`http://16.170.218.31:30561`**
**Action:** Click the Hamburger Menu (top left) → **Discover**.
**What to say:**
> "Finally, for debugging, I deployed the ELK Stack. Filebeat collects logs from every container across the AWS cluster and ships them to Elasticsearch. If a transaction fails, we simply search Kibana, and it instantly aggregates all logs. This completely solves the 'limited observability' issue mentioned in the case study."

---

**End of Presentation. Say "Thank you, I am happy to answer any questions!"**
