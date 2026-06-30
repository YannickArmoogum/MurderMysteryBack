# Optional custom domain + TLS for the CloudFront frontend.
#
# - Set `domain_name` to enable it (e.g. "play.example.com"). Empty = use the
#   default *.cloudfront.net domain and skip everything in this file.
# - If the domain's DNS is hosted in Route 53 in THIS account, also set
#   `route53_zone_name` (e.g. "example.com"). Validation + the alias record are
#   then fully automated and `terraform apply` completes in one step.
# - If DNS is external, leave `route53_zone_name` empty: Terraform creates the
#   ACM cert and outputs the records you must add at your DNS provider. Add
#   them, wait for issuance, then re-apply so CloudFront attaches the cert.

# CloudFront certificates MUST live in us-east-1, regardless of var.aws_region.
provider "aws" {
  alias  = "us_east_1"
  region = "us-east-1"
}

locals {
  enable_custom_domain = var.domain_name != ""
  enable_route53       = var.domain_name != "" && var.route53_zone_name != ""
}

resource "aws_acm_certificate" "frontend" {
  count    = local.enable_custom_domain ? 1 : 0
  provider = aws.us_east_1

  domain_name       = var.domain_name
  validation_method = "DNS"

  lifecycle {
    create_before_destroy = true
  }
}

# --- Route 53 automation (only when route53_zone_name is set) ---------------
data "aws_route53_zone" "this" {
  count = local.enable_route53 ? 1 : 0
  name  = var.route53_zone_name
}

resource "aws_route53_record" "cert_validation" {
  for_each = local.enable_route53 ? {
    for dvo in aws_acm_certificate.frontend[0].domain_validation_options :
    dvo.domain_name => {
      name   = dvo.resource_record_name
      type   = dvo.resource_record_type
      record = dvo.resource_record_value
    }
  } : {}

  zone_id         = data.aws_route53_zone.this[0].zone_id
  name            = each.value.name
  type            = each.value.type
  records         = [each.value.record]
  ttl             = 300
  allow_overwrite = true
}

# Blocks until the certificate is ISSUED. Only created for the Route 53 path
# (external DNS validation can't complete inside a single apply).
resource "aws_acm_certificate_validation" "frontend" {
  count    = local.enable_route53 ? 1 : 0
  provider = aws.us_east_1

  certificate_arn         = aws_acm_certificate.frontend[0].arn
  validation_record_fqdns = [for r in aws_route53_record.cert_validation : r.fqdn]
}

# DNS alias pointing the custom domain at CloudFront.
resource "aws_route53_record" "frontend_alias" {
  count   = local.enable_route53 ? 1 : 0
  zone_id = data.aws_route53_zone.this[0].zone_id
  name    = var.domain_name
  type    = "A"

  alias {
    name                   = aws_cloudfront_distribution.frontend.domain_name
    zone_id                = aws_cloudfront_distribution.frontend.hosted_zone_id
    evaluate_target_health = false
  }
}

locals {
  # Use the validated cert on the Route 53 path (guarantees it's ISSUED before
  # CloudFront references it); otherwise the raw cert ARN (external DNS).
  frontend_cert_arn = local.enable_custom_domain ? (
    local.enable_route53 ? aws_acm_certificate_validation.frontend[0].certificate_arn : aws_acm_certificate.frontend[0].arn
  ) : null
}
