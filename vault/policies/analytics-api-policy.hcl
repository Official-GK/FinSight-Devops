# Analytics API — Vault Access Policy
# ────────────────────────────────────────────────────────────────────────────
# Principle of Least Privilege: This service can ONLY read its own secrets
# and the shared database credentials. It cannot write, update, or delete.

# Own credentials (API keys, JWT secrets)
path "secret/data/analytics-api/*" {
  capabilities = ["read", "list"]
}

# Read-only access to shared DB credentials
path "secret/data/shared/database" {
  capabilities = ["read"]
}

# Allow listing secret paths (for health check / agent validation)
path "secret/metadata/analytics-api/*" {
  capabilities = ["list"]
}

# Deny all other paths explicitly
path "*" {
  capabilities = ["deny"]
}
