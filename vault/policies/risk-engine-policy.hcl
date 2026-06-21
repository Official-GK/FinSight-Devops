# Risk Engine — Vault Access Policy
# ────────────────────────────────────────────────────────────────────────────
# Strictly isolated: Risk Engine can only read its own secrets.
# It has no access to Analytics API secrets whatsoever.

path "secret/data/risk-engine/*" {
  capabilities = ["read", "list"]
}

path "secret/data/shared/database" {
  capabilities = ["read"]
}

path "secret/metadata/risk-engine/*" {
  capabilities = ["list"]
}

# Explicit deny for everything else
path "*" {
  capabilities = ["deny"]
}
