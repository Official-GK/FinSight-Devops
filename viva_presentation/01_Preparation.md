# Step 1: Pre-Viva Preparation

Before the faculty panel even starts the evaluation, you must have your environment set up perfectly. This guarantees you won't be fumbling with commands while they are watching.

## 1. Open Your IDE (VS Code)
Have the following files open in separate tabs so you can click them instantly when asked:
- `kubernetes/risk-engine.yaml` (To show HPA and Replicas)
- `Jenkinsfile` (To show CI/CD and Rollback)
- `terraform/eks.tf` (To show IaC)
- `vault/setup.sh` (To show Security)

## 2. Prepare Your Terminals
Open **TWO** separate terminal windows or split panes.

### Terminal 1: The "Demo" Terminal (AWS EC2)
Make sure this terminal is completely clean (`clear`). 
You will use this terminal *live* in front of the panel to type `kubectl` commands directly on your AWS Kubernetes Cluster.

To connect to it, run:
```bash
ssh -i ~/Desktop/demo-key.pem ubuntu@16.170.218.31
```
*(Keep this connected and ready for the demo)*

### Terminal 2: Jenkins Logs (Optional)
If you want to show live logs, keep a terminal ready, but you will mostly use the Jenkins web UI.

## 3. Prepare the Browser
1. Open Google Chrome.
2. Go to Jenkins: `http://localhost:8080`. Have the FinSight-CI-CD pipeline open. *(Running locally on your Mac)*
3. Keep a second tab ready for the Dashboard: `http://16.170.218.31`. *(Running in the AWS Kubernetes Cluster)*
4. Put the browser in **Full Screen**. Make sure the dashboard looks clean.

---
**When the panel says "You may begin", open the `02_Introduction.md` file.**
