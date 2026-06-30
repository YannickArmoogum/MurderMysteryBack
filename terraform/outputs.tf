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
  description = "Public HTTPS URL of the frontend (custom domain if set, else CloudFront)."
  value       = local.enable_custom_domain ? "https://${var.domain_name}" : "https://${aws_cloudfront_distribution.frontend.domain_name}"
}

output "acm_certificate_validation_records" {
  description = "DNS records to add at your provider when using EXTERNAL DNS (empty when Route 53 automates it)."
  value = local.enable_custom_domain && !local.enable_route53 ? [
    for dvo in aws_acm_certificate.frontend[0].domain_validation_options : {
      name  = dvo.resource_record_name
      type  = dvo.resource_record_type
      value = dvo.resource_record_value
    }
  ] : []
}

output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID (used for cache invalidation on deploy)."
  value       = aws_cloudfront_distribution.frontend.id
}
