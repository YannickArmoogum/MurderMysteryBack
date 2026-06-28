output "ecr_repository_url" {
  description = "Push images here."
  value       = aws_ecr_repository.this.repository_url
}

output "ecr_repository_name" {
  description = "Value for the ECR_REPOSITORY GitHub Actions variable."
  value       = aws_ecr_repository.this.name
}

output "github_deploy_role_arn" {
  description = "Value for the AWS_DEPLOY_ROLE_ARN GitHub Actions variable."
  value       = aws_iam_role.gh_deploy.arn
}

output "apprunner_service_arn" {
  description = "Value for the APP_RUNNER_SERVICE_ARN GitHub Actions variable."
  value       = aws_apprunner_service.this.arn
}

output "apprunner_service_url" {
  description = "Public HTTPS URL of the deployed app."
  value       = "https://${aws_apprunner_service.this.service_url}"
}

output "rds_endpoint" {
  description = "RDS Postgres endpoint."
  value       = aws_db_instance.this.address
}

output "aws_region" {
  description = "Value for the AWS_REGION GitHub Actions variable."
  value       = var.aws_region
}

output "frontend_bucket" {
  description = "S3 bucket the built Angular app is uploaded to."
  value       = aws_s3_bucket.frontend.bucket
}

output "frontend_url" {
  description = "Public HTTPS URL of the frontend (CloudFront)."
  value       = "https://${aws_cloudfront_distribution.frontend.domain_name}"
}

output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID (used for cache invalidation on deploy)."
  value       = aws_cloudfront_distribution.frontend.id
}
