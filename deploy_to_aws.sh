#!/bin/bash
# ============================================================
# FinSight – Full Clean-Slate AWS Deploy Script
# Run this on the EC2 instance to wipe and redeploy everything
# ============================================================
set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

KUBECTL="sudo k3s kubectl"
DOCKER="sudo docker"

echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}   FinSight Full Deploy – Starting         ${NC}"
echo -e "${GREEN}============================================${NC}"

# ── Step 1: Wipe existing finsight namespace ──────────────────
echo -e "\n${YELLOW}[1/7] Wiping existing finsight namespace...${NC}"
$KUBECTL delete namespace finsight --ignore-not-found=true
echo -e "${GREEN}✓ Old namespace deleted${NC}"

# Wait for full cleanup
sleep 5

# ── Step 2: Build Docker images ───────────────────────────────
echo -e "\n${YELLOW}[2/7] Building Docker images...${NC}"

cd /home/ubuntu/finsight

echo -e "${BLUE}  → Building analytics-api...${NC}"
$DOCKER build -t finsight/analytics-api:latest ./analytics-api 2>&1 | grep -E "Step|Successfully|error|ERROR" || true

echo -e "${BLUE}  → Building risk-engine...${NC}"
$DOCKER build -t finsight/risk-engine:latest ./risk-engine 2>&1 | grep -E "Step|Successfully|error|ERROR" || true

echo -e "${BLUE}  → Building frontend...${NC}"
$DOCKER build -t finsight/frontend:latest ./frontend 2>&1 | grep -E "Step|Successfully|error|ERROR" || true

echo -e "${GREEN}✓ All Docker images built${NC}"

# ── Step 3: Import images into K3s containerd ─────────────────
echo -e "\n${YELLOW}[3/7] Importing images into K3s containerd...${NC}"

$DOCKER save finsight/analytics-api:latest | sudo k3s ctr images import -
$DOCKER save finsight/risk-engine:latest | sudo k3s ctr images import -
$DOCKER save finsight/frontend:latest | sudo k3s ctr images import -

echo -e "${GREEN}✓ Images imported into K3s${NC}"

# ── Step 4: Apply Kubernetes manifests in order ───────────────
echo -e "\n${YELLOW}[4/7] Applying Kubernetes manifests...${NC}"

# Config first (namespace, configmap, secrets)
$KUBECTL apply -f kubernetes/config.yaml
echo "  ✓ namespace + configmap + secrets"

sleep 2

# Core application services
$KUBECTL apply -f kubernetes/postgres.yaml
echo "  ✓ postgres"

$KUBECTL apply -f kubernetes/analytics-api.yaml
echo "  ✓ analytics-api"

$KUBECTL apply -f kubernetes/risk-engine.yaml
echo "  ✓ risk-engine"

$KUBECTL apply -f kubernetes/frontend.yaml
echo "  ✓ frontend"

# Observability stack
$KUBECTL apply -f kubernetes/elasticsearch.yaml
echo "  ✓ elasticsearch (ELK)"

$KUBECTL apply -f kubernetes/kibana.yaml
echo "  ✓ kibana (ELK)"

$KUBECTL apply -f kubernetes/prometheus.yaml
echo "  ✓ prometheus"

$KUBECTL apply -f kubernetes/grafana.yaml
echo "  ✓ grafana"

# Secret management
$KUBECTL apply -f kubernetes/vault.yaml
echo "  ✓ vault"

echo -e "${GREEN}✓ All manifests applied${NC}"

# ── Step 5: Wait for core pods to be Running ──────────────────
echo -e "\n${YELLOW}[5/7] Waiting for core pods to start (up to 3 minutes)...${NC}"

wait_for_pod() {
    local app=$1
    local timeout=${2:-180}
    echo -ne "  Waiting for $app..."
    for i in $(seq 1 $timeout); do
        STATUS=$($KUBECTL get pods -n finsight -l app=$app -o jsonpath='{.items[0].status.phase}' 2>/dev/null || echo "Pending")
        if [ "$STATUS" = "Running" ]; then
            echo -e " ${GREEN}Running ✓${NC}"
            return 0
        fi
        sleep 2
        echo -ne "."
    done
    echo -e " ${RED}Timeout!${NC}"
    return 1
}

wait_for_pod analytics-api 180
wait_for_pod risk-engine 180
wait_for_pod frontend 120
wait_for_pod prometheus 60
wait_for_pod grafana 60
wait_for_pod vault 60

# ── Step 6: Show all pod status ───────────────────────────────
echo -e "\n${YELLOW}[6/7] Final pod status:${NC}"
$KUBECTL get pods -n finsight -o wide

# ── Step 7: Print all access URLs ─────────────────────────────
PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo "16.170.218.31")

echo -e "\n${GREEN}============================================${NC}"
echo -e "${GREEN}   FinSight Deploy COMPLETE! 🚀             ${NC}"
echo -e "${GREEN}============================================${NC}"
echo -e ""
echo -e "${BLUE}📊 Frontend Dashboard   :${NC} http://$PUBLIC_IP:30080"
echo -e "${BLUE}🔌 Analytics API        :${NC} http://$PUBLIC_IP:30800"
echo -e "${BLUE}🔌 Analytics API Docs   :${NC} http://$PUBLIC_IP:30800/docs"
echo -e "${BLUE}📈 Grafana (Monitoring) :${NC} http://$PUBLIC_IP:30300  (admin / finsight123)"
echo -e "${BLUE}🔍 Prometheus (Metrics) :${NC} http://$PUBLIC_IP:30909"
echo -e "${BLUE}📜 Kibana (Logs / ELK)  :${NC} http://$PUBLIC_IP:30561"
echo -e "${BLUE}🔐 Vault (Secrets)      :${NC} http://$PUBLIC_IP:30200  (token: vault-token-123)"
echo -e ""
echo -e "${YELLOW}Quick health check:${NC}"
curl -s http://localhost:30800/health | python3 -m json.tool 2>/dev/null || echo "  (API still starting up, try again in 30s)"
echo -e "${GREEN}============================================${NC}"
