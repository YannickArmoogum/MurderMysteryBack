resource "aws_apprunner_service" "this" {
  service_name = var.name

  source_configuration {
    # Private ECR pull
    authentication_configuration {
      access_role_arn = aws_iam_role.apprunner_ecr.arn
    }

    # CI triggers deployments explicitly via `aws apprunner start-deployment`.
    auto_deployments_enabled = false

    image_repository {
      image_identifier      = "${aws_ecr_repository.this.repository_url}:${var.image_tag}"
      image_repository_type = "ECR"

      image_configuration {
        port = "8000"

        runtime_environment_variables = {
          FRONTEND_URL = var.frontend_url
          PORT         = "8000"
          HF_TOKEN     = var.hf_token
        }

        runtime_environment_secrets = {
          ANTHROPIC_API_KEY = aws_secretsmanager_secret.anthropic.arn
          DATABASE_URL      = aws_secretsmanager_secret.database_url.arn
        }
      }
    }
  }

  instance_configuration {
    cpu               = var.apprunner_cpu
    memory            = var.apprunner_memory
    instance_role_arn = aws_iam_role.apprunner_instance.arn
  }

  # All egress goes through the VPC connector so the app can reach private RDS.
  network_configuration {
    egress_configuration {
      egress_type       = "VPC"
      vpc_connector_arn = aws_apprunner_vpc_connector.this.arn
    }
  }

  health_check_configuration {
    protocol            = "HTTP"
    path                = "/api/health"
    interval            = 10
    timeout             = 5
    healthy_threshold   = 1
    unhealthy_threshold = 5
  }

  lifecycle {
    # CI updates the image; don't let Terraform revert it on the next apply.
    ignore_changes = [source_configuration[0].image_repository[0].image_identifier]
  }
}
