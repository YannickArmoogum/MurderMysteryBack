# Role GitHub Actions assumes (via the existing OIDC provider) to deploy the
# frontend: upload to S3 and invalidate CloudFront. Scoped to the frontend
# repo's main branch. local.github_oidc_arn is defined in iam_github.tf.

resource "aws_iam_role" "gh_deploy_frontend" {
  count = var.frontend_github_repo != "" ? 1 : 0
  name  = "${var.name}-gh-deploy-frontend"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Federated = local.github_oidc_arn }
      Action    = "sts:AssumeRoleWithWebIdentity"
      Condition = {
        StringEquals = { "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com" }
        StringLike   = { "token.actions.githubusercontent.com:sub" = "repo:${var.frontend_github_repo}:ref:refs/heads/main" }
      }
    }]
  })
}

resource "aws_iam_role_policy" "gh_deploy_frontend" {
  count = var.frontend_github_repo != "" ? 1 : 0
  name  = "deploy-frontend"
  role  = aws_iam_role.gh_deploy_frontend[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["s3:ListBucket"]
        Resource = aws_s3_bucket.frontend.arn
      },
      {
        Effect   = "Allow"
        Action   = ["s3:PutObject", "s3:DeleteObject", "s3:GetObject"]
        Resource = "${aws_s3_bucket.frontend.arn}/*"
      },
      {
        Effect   = "Allow"
        Action   = ["cloudfront:CreateInvalidation", "cloudfront:GetInvalidation"]
        Resource = aws_cloudfront_distribution.frontend.arn
      },
    ]
  })
}

output "frontend_github_deploy_role_arn" {
  description = "Value for the AWS_DEPLOY_ROLE_ARN variable in the FRONTEND GitHub repo."
  value       = var.frontend_github_repo != "" ? aws_iam_role.gh_deploy_frontend[0].arn : null
}
