# Step 4: Infrastructure Outages & Self-Healing

**Goal:** Satisfy the requirement: *"Several incidents involving infrastructure outages have exposed weaknesses... architect a resilient analytics platform."* Prove that if a server dies, the app survives.

## What you are doing on screen:
1. Open your empty **Terminal 3**.
2. Run this exact command to list your pods:
   ```bash
   kubectl get pods -n finsight -l app=risk-engine
   ```
3. Copy the name of *one* of the pods (e.g., `risk-engine-deployment-5c4b8d-xyz12`).
4. Tell the panel what you are about to do, then run:
   ```bash
   kubectl delete pod <paste-pod-name-here> -n finsight
   ```
5. Immediately switch back to the **Browser (Frontend)**.

## What you should say exactly:
> "The legacy system suffered from infrastructure outages. To prove resilience, I am going to manually destroy one of our core backend compute pods right now.
> 
> *(Execute the delete command, switch to browser)*
> 
> As you can see, the frontend dashboard did not crash. There are no 502 Bad Gateway errors. 
> 
> Because I implemented **Readiness and Liveness probes** in the Kubernetes deployments, the Kubernetes control plane immediately detected the dead pod. The Kubernetes Service instantly stopped routing traffic to the dead pod, and the ReplicaSet automatically spun up a brand new pod to replace it. 
> 
> This guarantees zero-downtime high availability."

---
**Next Step -> Open `05_CICD_Rollback.md`**
