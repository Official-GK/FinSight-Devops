# FinSight Jenkins Setup Guide
## Complete Step-by-Step for DevOps Viva

---

## STEP 1 — Start Jenkins Server

Open a **new Terminal** in your project folder and run:
```bash
cd /Users/gauravkulkarni/Desktop/Devops_financialRisk
docker-compose -f docker-compose.jenkins.yml up -d
```

Wait **60 seconds** for Jenkins to fully boot, then run:
```bash
docker logs finsight-jenkins 2>&1 | grep -A 3 "Please use"
```

This will print your **initial admin password** — copy it!

If that doesn't show it, run:
```bash
docker exec finsight-jenkins cat /var/jenkins_home/secrets/initialAdminPassword
```

Save it to a file:
```bash
docker exec finsight-jenkins cat /var/jenkins_home/secrets/initialAdminPassword > jenkins_admin_password.txt
cat jenkins_admin_password.txt
```

---

## STEP 2 — Initial Jenkins Setup (Browser)

1. Open **http://localhost:8080** in your browser
2. Paste the password from Step 1 → Click **Continue**
3. On the plugin screen → Click **"Install suggested plugins"**
4. Wait ~3 minutes for plugins to install (they turn green one by one)
5. Create your admin account:
   - Username: `admin`
   - Password: `admin123`
   - Full name: `FinSight Admin`
   - Email: your email
6. Leave the Jenkins URL as `http://localhost:8080` → Click **Save and Finish**
7. Click **Start using Jenkins**

---

## STEP 3 — Install Additional Required Plugins

Go to: **Manage Jenkins → Plugins → Available Plugins**

Search for and install each of these (check the checkbox, then click Install):

| Plugin | Purpose |
|--------|---------|
| **Blue Ocean** | Beautiful pipeline visualization |
| **Pipeline Stage View** | Classic stage visualization |
| **Docker Pipeline** | Docker build commands in pipeline |
| **Timestamper** | Timestamps in console output |

After installing → check **"Restart Jenkins when installation is complete"**

---

## STEP 4 — Create the FinSight Pipeline Job

1. From the Jenkins home page → Click **"New Item"**
2. Enter name: `FinSight-CI-CD`
3. Select **"Pipeline"** → Click **OK**

In the configuration page:
- **Description**: `FinSight Real-Time Financial Risk Analytics Platform CI/CD Pipeline`
- Under **Build Triggers**: (leave empty for now)
- Under **Pipeline** section:
  - Definition: **Pipeline script**
  - Click into the script box and paste the entire contents of the `Jenkinsfile` from your project

> **Tip**: You can copy the Jenkinsfile content with:
> ```bash
> cat /Users/gauravkulkarni/Desktop/Devops_financialRisk/Jenkinsfile | pbcopy
> ```

Click **Save**.

---

## STEP 5 — Run the Pipeline

1. On the `FinSight-CI-CD` job page → Click **"Build Now"**
2. You will see a new build appear in the left panel under "Build History"
3. Click on **#1** → Click **"Console Output"** to watch live logs
4. Or click **"Open Blue Ocean"** for the beautiful visual stage view

The pipeline will run through all 8 stages:
```
✅ Checkout → ✅ Build Frontend → ✅ Build Backend
→ ✅ Run Tests → ✅ Docker Build → ✅ Docker Image Verification
→ ✅ Kubernetes Deployment → ✅ Deployment Verification
```

---

## STEP 6 — Take Your Screenshots

### Screenshot 1: Classic Pipeline View
- After a successful build, go to the job page
- You will see the **Stage View** with green boxes for all 8 stages
- Take screenshot

### Screenshot 2: Blue Ocean View
- Click **"Open Blue Ocean"** from the left menu
- You see the beautiful animated pipeline visualization
- Take screenshot

### Screenshot 3: Console Output
- Go to Build #1 → Console Output
- Scroll to the bottom showing the success banner:
```
╔══════════════════════════════════════════╗
║    ✅ BUILD SUCCEEDED                    ║
║    FinSight CI/CD Pipeline Complete      ║
╚══════════════════════════════════════════╝
```
- Take screenshot

### Screenshot 4: Build History
- Go back to the job homepage
- Run the pipeline 2-3 more times (to show a build history)
- Take screenshot of the build history showing multiple green builds

---

## STEP 7 — Demonstrate Rollback (for Viva)

To show the rollback stage to your panel:

1. Temporarily break the pipeline by adding this to Stage 8:
   ```groovy
   error("Simulating deployment failure for rollback demo")
   ```
2. Run the pipeline — it will fail and trigger the rollback `post { failure { ... } }` block
3. The console will show: `Rolling back to last known good Docker Compose state...`
4. Take screenshot of the rollback logs
5. Remove the error line and run again to show recovery

---

## STEP 8 — Verification Checklist

After completing setup, verify each item:

- [ ] **Jenkins accessible**: `curl http://localhost:8080` returns HTML
- [ ] **Admin login works**: Login with admin/admin123
- [ ] **Plugins installed**: Blue Ocean visible in left menu
- [ ] **Pipeline created**: `FinSight-CI-CD` job visible on dashboard
- [ ] **Build runs**: Build #1 completes with all green stages
- [ ] **Docker images built**: `docker images | grep finsight` shows 3 images
- [ ] **Services healthy**: `docker-compose ps` shows all containers `Up (healthy)`
- [ ] **Tests passed**: Stage 4 "Run Tests" shows pytest output
- [ ] **Rollback works**: Failed build triggers rollback in post section

---

## Useful Commands

```bash
# Check Jenkins is running
docker ps | grep jenkins

# View Jenkins logs
docker logs finsight-jenkins -f

# Get admin password again
docker exec finsight-jenkins cat /var/jenkins_home/secrets/initialAdminPassword

# Stop Jenkins
docker-compose -f docker-compose.jenkins.yml down

# Restart Jenkins
docker-compose -f docker-compose.jenkins.yml restart jenkins

# View all running containers
docker ps
```

---

## Troubleshooting

**Jenkins not loading at localhost:8080?**
```bash
docker logs finsight-jenkins | tail -20
# Wait another 30 seconds and retry
```

**Docker build fails inside Jenkins?**
```bash
# Verify Docker socket is mounted
docker exec finsight-jenkins docker info | head -5
```

**Tests failing in Stage 4?**
The tests require `python3` in the Jenkins container. If not present:
```bash
docker exec -u root finsight-jenkins apt-get install -y python3 python3-pip python3-venv
```
