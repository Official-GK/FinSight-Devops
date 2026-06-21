# Step 7: Observability & Security (ELK & Vault)

**Goal:** Satisfy the requirement: *"Monitoring, logging, and secret management must be implemented using Prometheus, Grafana, ELK Stack, and Vault."*

## What you are doing on screen:
1. Switch back to your **Browser (Frontend)**.
2. Click on the **Logs** tab in the sidebar to show the live terminal logs.
3. Switch back to your **IDE (VS Code)**.
4. Open `observability/elk/logstash.conf`.
5. Open `vault/setup.sh`.

## What you should say exactly:
> "Finally, the case study cited a lack of observability and secure secret management. 
> 
> For **Logging**, I implemented the **ELK Stack**. *(Point to logstash.conf)* All Docker container logs are scraped by Filebeat and sent to Logstash, where I tag them by microservice and forward them to Elasticsearch. This allows us to trace any single financial transaction across the entire cluster.
> 
> *(Switch to vault/setup.sh)*
> For **Secret Management**, I completely removed hardcoded credentials. I used **HashiCorp Vault** initialized with Shamir's Secret Sharing. Database credentials and API keys are stored securely in Vault and dynamically injected into the Kubernetes pods at runtime using Vault's Kubernetes Auth backend.
> 
> For **Monitoring**, Prometheus scrapes the metrics endpoints of our FastAPI apps, and Grafana visualizes the exact CPU and memory pressure the faculty requested."

---
**Next Step -> Open `08_Conclusion.md`**
