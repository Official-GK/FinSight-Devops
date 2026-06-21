# Case Study 53: FinSight Panel Presentation Script

This guide is a step-by-step script for your evaluation viva. Follow this exactly to showcase the complete DevOps lifecycle, satisfy the case study requirements, and maximize your marks.

---

## Preparation (Before the Panel Arrives)
1. **Start the Frontend:** 
   Open Terminal 1 and run:
   ```bash
   cd /Users/gauravkulkarni/Desktop/Devops_financialRisk/frontend
   npm run dev
   ```
2. **Start the Backend Services:**
   Open Terminal 2 and run:
   ```bash
   cd /Users/gauravkulkarni/Desktop/Devops_financialRisk
   ./start_backend.sh
   ```
3. **Open the Dashboard:** Navigate to `http://localhost:5173` in your browser. Keep it full screen.

---

## ⏱️ Minute 0-2: Introduction & Business Application
**What to say:**
> "Welcome to the FinSight Analytics Platform demo. This platform was built to satisfy Case Study 53, solving the issue of legacy application bottlenecks during high market volatility. 
> 
> The application uses a microservices architecture. The React frontend communicates with a FastAPI Analytics gateway, which delegates heavy computations to an async Risk Engine."

**What to do:**
1. Show the main **Dashboard** view.
2. Click on the **Risk Calculator** in the sidebar.
3. Enter an amount (e.g., `5000`), select `TRADE`, and click **Calculate Risk Score**.
4. Point out the instant latency and score generation to prove the backend is alive and well-integrated.

---

## ⏱️ Minute 2-4: Scenario 1 - Market Volatility Simulation & Auto-scaling
**What to say:**
> "The case study specifically requires us to handle massive spikes in transaction volumes during market volatility. Let me simulate a market event right now."

**What to do:**
1. Click the **Demo Mode** button in the top right corner of the dashboard.
2. Navigate to the **Transactions** tab to show the graph spiking.
3. Navigate to the **Infrastructure** tab.
4. **Explain:** "Under normal circumstances, the Risk Engine runs on 3 pods. However, because our Kubernetes Horizontal Pod Autoscaler (HPA) detects CPU spikes over 75%, it will automatically scale up to 10 pods to prevent bottlenecks."

*If the panel asks for proof of the HPA command, open a terminal and type:*
```bash
kubectl get hpa -n finsight
```

---

## ⏱️ Minute 4-6: Scenario 2 - Infrastructure Outage & Self-Healing
**What to say:**
> "Another requirement was handling infrastructure outages. Kubernetes ensures our application is highly available. I will now simulate a critical failure by manually killing one of the Risk Engine pods."

**What to do:**
1. Open your terminal in front of the panel and run:
   ```bash
   # Show running pods
   kubectl get pods -n finsight -l app=risk-engine
   
   # Delete one pod to simulate a crash
   kubectl delete pod <copy-paste-one-pod-name-from-above> -n finsight
   ```
2. Switch immediately back to the browser.
3. **Explain:** "Notice that the frontend did not crash, and we received no 502 Bad Gateway errors. The Kubernetes ReplicaSet immediately detected the dead pod via Liveness Probes and spun up a replacement instantly while the Service LoadBalancer rerouted active traffic to healthy pods."

---

## ⏱️ Minute 6-8: Scenario 3 - CI/CD & Automated Testing
**What to say:**
> "To solve the issue of delayed releases and untested code, we implemented a fully automated Jenkins CI/CD pipeline that runs tests inside isolated Docker environments."

**What to do:**
1. Open the Jenkins dashboard at `http://localhost:8080` and show the fully green `FinSight-CI-CD` pipeline.
2. Click on the latest build (#12) and open the **Console Output**.
3. **Explain:** "Our pipeline automatically checks out the code, and then spins up ephemeral Docker containers (like `python:3.12-slim`) to run PyTest on our API and Risk Engine. This ensures no environment pollution."
4. Scroll down the console output to show the **Docker Build** and **Smoke Testing** stages.
5. **The Rollback:** Highlight the end of the Console Output or the `Jenkinsfile` post-actions. 
6. **Explain:** "If a bad deployment occurs or a test fails, the pipeline immediately initiates a rollback, using `docker-compose down` and `docker-compose up -d --no-build` to restore the last known good configuration automatically."

---

## ⏱️ Minute 8-10: Scenario 4 - Observability & Security (Vault/ELK)
**What to say:**
> "Finally, to address the lack of observability and secure secret management, we implemented an enterprise monitoring stack."

**What to do:**
1. Navigate to the **Logs** tab on the frontend.
2. **Explain:** "All container logs are scraped by Filebeat and forwarded to our ELK stack (Logstash/Elasticsearch). This allows us to trace any transaction ID across the entire microservice ecosystem."
3. Open the `vault/setup.sh` script in your IDE.
4. **Explain:** "For security, we completely removed hardcoded secrets. We use HashiCorp Vault with Shamir's Secret Sharing. Database credentials and API keys are dynamically injected into the Kubernetes pods at runtime."

---

## ⏱️ Conclusion
**What to say:**
> "By utilizing Terraform for Infrastructure as Code, Docker for containerization, Kubernetes for orchestration, Jenkins for CI/CD, and the ELK/Prometheus stack for observability, FinSight successfully resolves all operational inefficiencies highlighted in Case Study 53. Thank you."
