#!/usr/bin/env bash
# Bring the whole stack up from nothing (or after a `terraform destroy`).
# Handles the ECR bootstrap (App Runner can't start without an image) automatically.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT/terraform"

echo "==> Pass 1: ensure ECR repository exists"
terraform apply -auto-approve -target=aws_ecr_repository.this

ECR_URI="$(terraform output -raw ecr_repository_url)"
REGION="$(terraform output -raw aws_region)"
REGISTRY="${ECR_URI%/*}"

echo "==> Logging in to ECR ($REGISTRY)"
aws ecr get-login-password --region "$REGION" \
  | docker login --username AWS --password-stdin "$REGISTRY"

echo "==> Building and pushing image (linux/amd64)"
docker build --platform linux/amd64 --provenance=false --sbom=false \
  -t "${ECR_URI}:latest" "$ROOT"
docker push "${ECR_URI}:latest"

echo "==> Pass 2: apply the full stack"
terraform apply -auto-approve

echo
echo "==> Done. App URL:"
terraform output -raw apprunner_service_url
echo
