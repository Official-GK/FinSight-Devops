# Step 5: Jenkins CI/CD & Rollbacks

**Goal:** Satisfy the requirement: *"delayed releases... deployments failures... CI/CD pipelines automated through Jenkins."* Prove you have a robust pipeline.

## What you are doing on screen:
1. Switch to your **IDE (VS Code)**.
2. Open the `Jenkinsfile` located in the root directory.
3. Scroll down to the `Deploy to Kubernetes` stage.
4. Scroll further down to the `post { failure }` block.

## What you should say exactly:
> "To eliminate the operational inefficiencies and delayed releases mentioned in the case study, I automated the entire continuous delivery process using a declarative **Jenkins pipeline**.
> 
> *(Point to the file)*
> Here in my Jenkinsfile, you can see parallel stages for testing the frontend and backend. It then builds the Docker images and dynamically injects the new image tags into our Kubernetes manifests via `sed` before deploying.
> 
> However, the prompt specifically mentioned dealing with **Deployment Failures**. To solve this, I added a 'Verify Deployment' stage using `kubectl rollout status`. 
> 
> *(Point to the post { failure } block)*
> If any bugs slip through, or if Kubernetes readiness probes fail, the pipeline catches the timeout and immediately executes a `kubectl rollout undo` command. This automatic rollback ensures bad code never takes down the production platform."

---
**Next Step -> Open `06_InfraAsCode.md`**
