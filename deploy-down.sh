#!/usr/bin/env bash
# Tear the whole stack down to stop ALL billing (NAT gateway, App Runner, RDS, etc.).
# Note: this deletes the RDS instance and its data.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT/terraform"

terraform destroy -auto-approve
echo "==> Stack destroyed. Billing for NAT/App Runner/RDS has stopped."
