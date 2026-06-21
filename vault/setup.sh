#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════════════════════
# vault/setup.sh — HashiCorp Vault Initialization & Configuration Script
#
# This script bootstraps Vault for the Financial Risk Analytics Platform.
# Run this ONCE on a fresh Vault cluster. All subsequent operations use
# the Vault Agent injected into K8s pods automatically.
#
# Prerequisites:
#   - vault CLI installed
#   - kubectl configured against your EKS cluster
#   - VAULT_ADDR environment variable set
# ════════════════════════════════════════════════════════════════════════════════

set -euo pipefail

# ── Configuration ──────────────────────────────────────────────────────────────
VAULT_NAMESPACE="vault"
VAULT_ADDR="${VAULT_ADDR:-http://vault.vault.svc.cluster.local:8200}"
K8S_NAMESPACE="financial-risk"
EKS_CLUSTER_NAME="${EKS_CLUSTER_NAME:-financial-risk-eks}"
AWS_REGION="${AWS_REGION:-us-east-1}"

# ── Colors for output ─────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'

info()    { echo -e "${BLUE}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}[✓]${NC} $1"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $1"; }
error()   { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

echo ""
echo "════════════════════════════════════════════════════════"
echo "  HashiCorp Vault Setup — Financial Risk Platform"
echo "════════════════════════════════════════════════════════"
echo ""

# ── STEP 1: Deploy Vault to Kubernetes via Helm ───────────────────────────────
info "Step 1: Deploying Vault to Kubernetes..."

helm repo add hashicorp https://helm.releases.hashicorp.com
helm repo update

kubectl create namespace ${VAULT_NAMESPACE} --dry-run=client -o yaml | kubectl apply -f -

helm upgrade --install vault hashicorp/vault \
    --namespace ${VAULT_NAMESPACE} \
    --set server.ha.enabled=true \
    --set server.ha.replicas=3 \
    --set server.ha.raft.enabled=true \
    --set server.ha.raft.setNodeId=true \
    --set injector.enabled=true \
    --set injector.replicas=2 \
    --set ui.enabled=true \
    --set ui.serviceType=ClusterIP \
    --wait --timeout=300s

success "Vault deployed to Kubernetes"

# ── STEP 2: Initialize Vault ──────────────────────────────────────────────────
info "Step 2: Initializing Vault cluster..."
sleep 10

# Initialize with 5 key shares, threshold of 3 (Shamir's Secret Sharing)
VAULT_INIT_OUTPUT=$(kubectl exec -n ${VAULT_NAMESPACE} vault-0 -- \
    vault operator init \
        -key-shares=5 \
        -key-threshold=3 \
        -format=json 2>/dev/null)

# Extract keys and root token
UNSEAL_KEY_1=$(echo $VAULT_INIT_OUTPUT | jq -r '.unseal_keys_b64[0]')
UNSEAL_KEY_2=$(echo $VAULT_INIT_OUTPUT | jq -r '.unseal_keys_b64[1]')
UNSEAL_KEY_3=$(echo $VAULT_INIT_OUTPUT | jq -r '.unseal_keys_b64[2]')
ROOT_TOKEN=$(echo $VAULT_INIT_OUTPUT | jq -r '.root_token')

# ⚠️  CRITICAL: In production, distribute unseal keys to different team members
# and store in separate secure locations (HSM, separate key custodians, etc.)
# NEVER commit these to version control!
warn "═══════════════════════════════════════════════════════════"
warn "  SAVE THESE SECURELY — They will NOT be shown again!"
warn "  Unseal Key 1: ${UNSEAL_KEY_1}"
warn "  Unseal Key 2: ${UNSEAL_KEY_2}"
warn "  Unseal Key 3: ${UNSEAL_KEY_3}"
warn "  Root Token  : ${ROOT_TOKEN}"
warn "═══════════════════════════════════════════════════════════"

# Save to a local file (chmod 600) — delete after distributing keys
cat > vault-init-output.json <<EOF
{
  "unseal_keys": ["${UNSEAL_KEY_1}", "${UNSEAL_KEY_2}", "${UNSEAL_KEY_3}"],
  "root_token": "${ROOT_TOKEN}",
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "WARNING": "DELETE THIS FILE AFTER DISTRIBUTING KEYS TO CUSTODIANS"
}
EOF
chmod 600 vault-init-output.json

success "Vault initialized"

# ── STEP 3: Unseal All Vault Pods ─────────────────────────────────────────────
info "Step 3: Unsealing Vault pods..."

for pod in vault-0 vault-1 vault-2; do
    info "  Unsealing ${pod}..."
    kubectl exec -n ${VAULT_NAMESPACE} ${pod} -- vault operator unseal ${UNSEAL_KEY_1} > /dev/null
    kubectl exec -n ${VAULT_NAMESPACE} ${pod} -- vault operator unseal ${UNSEAL_KEY_2} > /dev/null
    kubectl exec -n ${VAULT_NAMESPACE} ${pod} -- vault operator unseal ${UNSEAL_KEY_3} > /dev/null
    success "  ${pod} unsealed"
done

# ── STEP 4: Join Raft Cluster ─────────────────────────────────────────────────
info "Step 4: Joining vault-1 and vault-2 to Raft cluster..."
for pod in vault-1 vault-2; do
    kubectl exec -n ${VAULT_NAMESPACE} ${pod} -- \
        vault operator raft join \
        http://vault-0.vault-internal:8200
done
success "Raft cluster formed"

# ── STEP 5: Authenticate as Root ──────────────────────────────────────────────
info "Step 5: Authenticating with root token..."
export VAULT_TOKEN="${ROOT_TOKEN}"
kubectl exec -n ${VAULT_NAMESPACE} vault-0 -- \
    vault login ${ROOT_TOKEN} > /dev/null
success "Authenticated"

# ── STEP 6: Enable KV v2 Secrets Engine ──────────────────────────────────────
info "Step 6: Enabling KV v2 secrets engine..."
kubectl exec -n ${VAULT_NAMESPACE} vault-0 -- \
    vault secrets enable -path=secret -version=2 kv 2>/dev/null || \
    warn "KV v2 already enabled at 'secret/'"
success "KV v2 secrets engine enabled at path: secret/"

# ── STEP 7: Store Application Secrets ────────────────────────────────────────
info "Step 7: Writing application secrets to Vault..."

# Analytics API secrets
kubectl exec -n ${VAULT_NAMESPACE} vault-0 -- vault kv put secret/analytics-api/credentials \
    api_key="frp-api-$(openssl rand -hex 16)" \
    jwt_secret="$(openssl rand -base64 48)" \
    allowed_origins="https://dashboard.financial-risk.internal"

# Risk Engine secrets
kubectl exec -n ${VAULT_NAMESPACE} vault-0 -- vault kv put secret/risk-engine/credentials \
    market_data_api_key="mkt-$(openssl rand -hex 16)" \
    volatility_api_secret="$(openssl rand -base64 32)"

# Shared database credentials (mock — replace with real DB in production)
kubectl exec -n ${VAULT_NAMESPACE} vault-0 -- vault kv put secret/shared/database \
    host="postgres.financial-risk.internal" \
    port="5432" \
    database="financial_risk_db" \
    username="frp_app" \
    password="$(openssl rand -base64 24)" \
    ssl_mode="require"

# Observability secrets
kubectl exec -n ${VAULT_NAMESPACE} vault-0 -- vault kv put secret/shared/observability \
    grafana_admin_password="$(openssl rand -base64 16)" \
    elasticsearch_password="$(openssl rand -base64 16)"

success "All secrets written to Vault"

# ── STEP 8: Enable Kubernetes Auth Backend ────────────────────────────────────
info "Step 8: Enabling Kubernetes authentication backend..."
kubectl exec -n ${VAULT_NAMESPACE} vault-0 -- \
    vault auth enable kubernetes 2>/dev/null || \
    warn "Kubernetes auth already enabled"

# Get the Kubernetes service account JWT and CA cert for Vault's auth config
K8S_HOST=$(kubectl config view --raw --minify --flatten \
    -o jsonpath='{.clusters[].cluster.server}')
K8S_CA=$(kubectl config view --raw --minify --flatten \
    -o jsonpath='{.clusters[].cluster.certificate-authority-data}' | base64 -d)

kubectl exec -n ${VAULT_NAMESPACE} vault-0 -- vault write auth/kubernetes/config \
    kubernetes_host="${K8S_HOST}" \
    kubernetes_ca_cert="${K8S_CA}" \
    issuer="https://kubernetes.default.svc.cluster.local"

success "Kubernetes auth backend configured"

# ── STEP 9: Write Vault Policies ──────────────────────────────────────────────
info "Step 9: Writing access policies..."

# Analytics API policy
kubectl exec -n ${VAULT_NAMESPACE} vault-0 -- vault policy write analytics-api-policy - <<'POLICY'
# Analytics API — can only read its own secrets and shared observability config
path "secret/data/analytics-api/*" {
  capabilities = ["read", "list"]
}
path "secret/data/shared/database" {
  capabilities = ["read"]
}
path "secret/metadata/analytics-api/*" {
  capabilities = ["list"]
}
POLICY

# Risk Engine policy
kubectl exec -n ${VAULT_NAMESPACE} vault-0 -- vault policy write risk-engine-policy - <<'POLICY'
path "secret/data/risk-engine/*" {
  capabilities = ["read", "list"]
}
path "secret/data/shared/database" {
  capabilities = ["read"]
}
path "secret/metadata/risk-engine/*" {
  capabilities = ["list"]
}
POLICY

success "Policies written"

# ── STEP 10: Bind K8s Service Accounts to Vault Roles ─────────────────────────
info "Step 10: Creating Kubernetes auth roles..."

# Analytics API role — binds analytics-api-sa to analytics-api-policy
kubectl exec -n ${VAULT_NAMESPACE} vault-0 -- vault write auth/kubernetes/role/analytics-api \
    bound_service_account_names=analytics-api-sa \
    bound_service_account_namespaces=${K8S_NAMESPACE} \
    policies=analytics-api-policy \
    ttl=1h \
    max_ttl=24h

# Risk Engine role
kubectl exec -n ${VAULT_NAMESPACE} vault-0 -- vault write auth/kubernetes/role/risk-engine \
    bound_service_account_names=risk-engine-sa \
    bound_service_account_namespaces=${K8S_NAMESPACE} \
    policies=risk-engine-policy \
    ttl=1h \
    max_ttl=24h

success "Kubernetes auth roles created"

# ── STEP 11: Revoke Root Token ────────────────────────────────────────────────
warn "Step 11: Revoking root token (best practice for production)..."
warn "  Create admin tokens first if you need ongoing admin access!"
# Uncomment the line below after creating operator tokens:
# kubectl exec -n ${VAULT_NAMESPACE} vault-0 -- vault token revoke ${ROOT_TOKEN}

echo ""
echo "════════════════════════════════════════════════════════"
echo "  ✅ Vault Setup Complete!"
echo ""
echo "  Vault UI: kubectl port-forward -n vault svc/vault-ui 8200:8200"
echo "  Verify:   vault kv get secret/analytics-api/credentials"
echo "════════════════════════════════════════════════════════"
echo ""
success "Done! Remember to securely distribute the unseal keys from vault-init-output.json"
