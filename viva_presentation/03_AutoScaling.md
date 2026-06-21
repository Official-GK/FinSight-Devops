# Step 3: Simulating Market Volatility & Auto-Scaling

**Goal:** Satisfy the requirement: *"During periods of market volatility, transaction volumes increase significantly... process ten times the current workload."* Prove that Kubernetes autoscales.

## What you are doing on screen:
1. Go to the **Dashboard** tab on the frontend.
2. Click the green **Demo Mode** button in the top right. (The graphs will start moving rapidly).
3. Switch your screen to your **IDE (VS Code)**.
4. Open the `kubernetes/risk-engine.yaml` file and highlight lines `49-62` (The HorizontalPodAutoscaler section).

## What you should say exactly:
> "The case study specifically notes that during market volatility, immense pressure is placed on the infrastructure. I am currently simulating a massive spike in transaction volume using Demo Mode.
>
> To handle this 10x workload without crashing, I containerized the applications using **Docker** and orchestrated them via **Kubernetes**. 
>
> Here in my `risk-engine.yaml` file (point to the code), you can see I have implemented a **Horizontal Pod Autoscaler (HPA)**. Under normal load, we run 5 replicas. However, I have configured the HPA to monitor CPU metrics. If average utilization exceeds 75% due to the market volatility I just triggered, Kubernetes will automatically scale the engine up to 20 pods to absorb the load seamlessly."

## The "Prove It" Live Command (Optional but highly recommended)
Switch to your empty **Terminal 3** and run:
```bash
kubectl get hpa -n finsight
```
> "If we run this command in the cluster, you can see the HPA actively tracking the CPU targets."

---
**Next Step -> Open `04_SelfHealing.md`**
