# Deployment

Deploys the FastAPI backend to **AWS App Runner**, backed by **RDS Postgres**, with
**GitHub Actions** building/pushing images and triggering deployments. CI authenticates
to AWS via **OIDC** (no long-lived keys).

```
GitHub push (main) ──▶ GitHub Actions (OIDC) ──▶ build image ──▶ ECR
                                                                  │
                                                  start-deployment │
                                                                  ▼
                                                            App Runner
                                                                  │ VPC connector
                                                                  ▼
                                                            RDS Postgres
```

On every deploy the container entrypoint runs `alembic upgrade head`, then `uvicorn`.

---

## Prerequisites
- AWS account + AWS CLI configured with admin (for the one-time `terraform apply`).
- [Terraform](https://developer.hashicorp.com/terraform/install) >= 1.5.
- Docker (to push the first image).
- A GitHub repo for this project.

---

## 1. Provision AWS infrastructure (Terraform)

The `terraform/` stack creates: a VPC (with NAT gateway), ECR repo, RDS Postgres,
Secrets Manager entries, the GitHub OIDC provider + CI deploy role, App Runner IAM
roles, a VPC connector, and the App Runner service.

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
# edit terraform.tfvars: github_repo, anthropic_api_key, frontend_url, region
terraform init
```

### Bootstrap ordering (important)
App Runner refuses to create until an image exists in ECR. So apply in two passes:

```bash
# Pass 1 — create ECR (and the rest of the network/db) without App Runner yet.
terraform apply -target=aws_ecr_repository.this

# Build & push the first image to the new repo.
ECR_URL=$(terraform output -raw ecr_repository_url)
REGION=$(terraform output -raw aws_region)
aws ecr get-login-password --region "$REGION" \
  | docker login --username AWS --password-stdin "${ECR_URL%/*}"
docker build -t "$ECR_URL:latest" ..
docker push "$ECR_URL:latest"

# Pass 2 — create everything, including App Runner.
terraform apply
```

> On Apple Silicon, build for the App Runner platform: add `--platform linux/amd64`
> to the `docker build` command.

### Grab the outputs
```bash
terraform output
```
You'll need these four for GitHub:
- `aws_region`
- `ecr_repository_name`
- `github_deploy_role_arn`
- `apprunner_service_arn`

---

## 2. Configure GitHub Actions

In **GitHub → repo → Settings → Secrets and variables → Actions → Variables**
add these as **Variables** (not Secrets — none are sensitive):

| Variable | Value (from `terraform output`) |
|---|---|
| `AWS_REGION` | `aws_region` |
| `ECR_REPOSITORY` | `ecr_repository_name` |
| `AWS_DEPLOY_ROLE_ARN` | `github_deploy_role_arn` |
| `APP_RUNNER_SERVICE_ARN` | `apprunner_service_arn` |

The workflow lives at `.github/workflows/deploy.yml` and runs on push to `main`
(or manual "Run workflow"). It builds the image, pushes `:latest` and `:<sha>` to
ECR, calls `apprunner start-deployment`, and waits for `RUNNING`.

---

## 3. Deploy
```bash
git push origin main
```
Watch **Actions**. When green, get the public URL:
```bash
cd terraform && terraform output -raw apprunner_service_url
```
Health check: `GET <url>/api/health`.

---

## Configuration reference

The app reads these environment variables (set by Terraform on App Runner):

| Var | Source | Notes |
|---|---|---|
| `DATABASE_URL` | Secrets Manager | `postgresql+psycopg2://…` pointing at RDS |
| `ANTHROPIC_API_KEY` | Secrets Manager | required |
| `FRONTEND_URL` | plain env | CORS origin — set to your real frontend |
| `HF_TOKEN` | plain env | optional |
| `PORT` | plain env | `8000` |

To rotate a secret: update it in Secrets Manager (or re-run `terraform apply`),
then trigger a new deployment so App Runner picks up the new value.

---

## Local development
Use Docker Compose (bundled Postgres, not RDS):
```bash
cp .env.example .env   # fill ANTHROPIC_API_KEY
docker compose up --build
# API at http://localhost:8000
```

---

## Cost notes
Rough monthly baseline (eu-west-1, light use): App Runner ~$5–25, RDS
db.t4g.micro ~$13, **NAT gateway ~$32** (largest fixed cost — required so the
VPC-routed app can reach the Anthropic API). To cut the NAT cost you'd swap the
VPC connector for a publicly-accessible RDS, but that's less secure.

## Gotchas
- **NAT gateway is mandatory** here: App Runner's VPC egress means *all* outbound
  (including Anthropic calls) flows through the VPC, which needs NAT for internet.
- **Migrations run on container start.** Fine at 1 instance; if you scale App Runner
  to multiple instances, move `alembic upgrade head` to a one-off task to avoid races.
- **OIDC provider already exists?** Set `create_oidc_provider = false` in tfvars.
- Terraform `ignore_changes` keeps it from reverting the image tag CI deploys.
