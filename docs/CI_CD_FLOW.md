# CI/CD Flow

## Pipeline Overview
The pipeline is managed via a declarative `Jenkinsfile` executing on a Jenkins master/agent setup.

## Stages
1. **Checkout:** Pulls latest code from Git.
2. **Test & Lint (Parallel):**
   - Frontend tests (npm).
   - Analytics API tests (pytest).
   - Risk Engine tests (pytest).
3. **Build Docker Images:** Builds images using local Dockerfiles and tags them with the Jenkins build number (`BUILD_NUMBER`).
4. **Push Docker Images:** Pushes tagged images to the secure registry.
5. **Deploy to Kubernetes:**
   - Dynamically updates the image tags in the `kubernetes/*.yaml` manifests using `sed`.
   - Executes `kubectl apply -f` to deploy to the EKS cluster.
6. **Verify Deployment:**
   - Executes `kubectl rollout status` to wait for readiness probes to pass.
7. **Rollback (Post-Failure Action):**
   - If any stage fails (tests, build, or rollout verification), the pipeline explicitly triggers `kubectl rollout undo` to revert the cluster to the previous stable state.
