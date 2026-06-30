variable "aws_region" {
  description = "AWS region to deploy into."
  type        = string
  default     = "eu-west-1"
}

variable "name" {
  description = "Base name used to prefix all resources."
  type        = string
  default     = "murder-mystery"
}

variable "github_repo" {
  description = "GitHub repository in 'owner/name' form, used to scope the OIDC trust policy."
  type        = string
  # e.g. "yannickarmoo/MurderMystery"
}

variable "create_oidc_provider" {
  description = "Create the GitHub Actions OIDC provider. Set false if one already exists in the account."
  type        = bool
  default     = true
}

variable "anthropic_api_key" {
  description = "Anthropic API key, stored in Secrets Manager."
  type        = string
  sensitive   = true
}

variable "hf_token" {
  description = "Optional Hugging Face token."
  type        = string
  default     = ""
  sensitive   = true
}

variable "frontend_url" {
  description = "Allowed CORS origin / frontend URL."
  type        = string
  default     = "http://localhost:4200"
}

variable "domain_name" {
  description = "Custom domain for the frontend (e.g. 'play.example.com'). Empty = use the default CloudFront domain."
  type        = string
  default     = ""
}

variable "route53_zone_name" {
  description = "Route 53 hosted zone name (e.g. 'example.com') if the domain's DNS is in this account. Empty = external DNS (manual validation)."
  type        = string
  default     = ""
}

variable "frontend_github_repo" {
  description = "Frontend GitHub repo in 'owner/name' form for the CI deploy role. Empty = no frontend CI role."
  type        = string
  default     = ""
}

variable "image_tag" {
  description = "ECR image tag App Runner deploys. The CI pipeline pushes 'latest'."
  type        = string
  default     = "latest"
}

variable "db_engine_version" {
  description = "PostgreSQL major version."
  type        = string
  default     = "16"
}

variable "db_instance_class" {
  description = "RDS instance class."
  type        = string
  default     = "db.t4g.micro"
}

variable "apprunner_cpu" {
  description = "App Runner vCPU units (1024 = 1 vCPU)."
  type        = string
  default     = "1024"
}

variable "apprunner_memory" {
  description = "App Runner memory in MB."
  type        = string
  default     = "2048"
}
