# Step 1: Pre-Viva Preparation

Before the faculty panel even starts the evaluation, you must have your environment set up perfectly. This guarantees you won't be fumbling with commands while they are watching.

## 1. Open Your IDE (VS Code)
Have the following files open in separate tabs so you can click them instantly when asked:
- `kubernetes/risk-engine.yaml` (To show HPA and Replicas)
- `Jenkinsfile` (To show CI/CD and Rollback)
- `terraform/eks.tf` (To show IaC)
- `vault/setup.sh` (To show Security)

## 2. Prepare Your Terminals
Open **THREE** separate terminal windows or split panes.

### Terminal 1: Run the Backend
```bash
cd /Users/gauravkulkarni/Desktop/Devops_financialRisk
./start_backend.sh
```
*(Leave this running in the background. It starts both FastAPI services.)*

### Terminal 2: Run the Frontend
```bash
cd /Users/gauravkulkarni/Desktop/Devops_financialRisk/frontend
npm run dev
```
*(Leave this running in the background.)*

### Terminal 3: The "Demo" Terminal
Make sure this terminal is completely clean (`clear`). 
You will use this terminal *live* in front of the panel to type `kubectl` commands to prove your infrastructure works.

## 3. Prepare the Browser
1. Open Google Chrome.
2. Go to `http://localhost:5173`.
3. Put the browser in **Full Screen**. Make sure the dashboard looks clean.

---
**When the panel says "You may begin", open the `02_Introduction.md` file.**
