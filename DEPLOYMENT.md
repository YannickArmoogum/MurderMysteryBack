# Deployment

Deploys the FastAPI backend to **AWS App Runner**, backed by **RDS Postgres**, with
**GitHub Actions** building/pushing images and triggering deployments. The Angular
frontend is served as a static site from **S3 via CloudFront**, which also proxies
`/api/*` to App Runner so the whole app lives on **one HTTPS origin (no CORS)**. All
CI authenticates to AWS via **OIDC** (no long-lived keys).

```
                       ┌─────────────── CloudFront (one HTTPS origin) ───────────────┐
browser ──▶ CloudFront │  /*      ──▶ S3 (Angular static site)                        │
                       │  /api/*  ──▶ App Runner ──▶ RDS Postgres                     │
                       └─────────────────────────────────────────────────────────────┘
```

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

## 4. Frontend (Angular → S3 + CloudFront)

The same Terraform stack provisions the frontend bucket, CloudFront distribution
(with the `/api/*` → App Runner proxy), and an OIDC deploy role for the frontend repo
(created when `frontend_github_repo` is set in `terraform.tfvars`).

The frontend lives in a **separate repo** (`YannickArmoogum/MurderMysteryFront`) and
already ships its own `.github/workflows/deploy.yml`. Wire it up once:

1. Get the outputs from this stack:
   ```bash
   cd terraform
   terraform output -raw frontend_bucket
   terraform output -raw cloudfront_distribution_id
   terraform output -raw frontend_github_deploy_role_arn
   terraform output -raw aws_region
   ```
2. In the **frontend repo** → Settings → Secrets and variables → Actions → **Variables**:

   | Variable | Value |
   |---|---|
   | `AWS_REGION` | `aws_region` |
   | `FRONTEND_BUCKET` | `frontend_bucket` |
   | `CLOUDFRONT_DISTRIBUTION_ID` | `cloudfront_distribution_id` |
   | `AWS_DEPLOY_ROLE_ARN` | `frontend_github_deploy_role_arn` |

3. Push the frontend repo's `main`. The workflow builds the Angular app (production
   config → `apiBaseUrl: ''`, same-origin), syncs `dist/murder-mystery-ai/browser` to
   S3, and invalidates CloudFront.

Your live site is the CloudFront URL (or custom domain):
```bash
terraform output -raw frontend_url
```

> The app calls `/api/*` on its own origin, so **no CORS config is needed** for the
> browser. `FRONTEND_URL` on the backend only matters if something calls it
> cross-origin directly.

### Optional: custom domain
Set in `terraform.tfvars`, then `terraform apply`:
- `domain_name = "play.example.com"` — enables ACM (in us-east-1) + CloudFront alias.
- `route53_zone_name = "example.com"` — set **only if** the domain's DNS is in Route 53
  in this account; validation + alias record are then fully automated.
- External DNS? Leave `route53_zone_name` empty, apply, add the records from
  `terraform output acm_certificate_validation_records`, wait for issuance, re-apply.

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
