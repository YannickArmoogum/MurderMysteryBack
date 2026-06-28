data "aws_availability_zones" "available" {
  state = "available"
}

# A small dedicated VPC. App Runner routes ALL egress through the VPC connector,
# so we need a NAT gateway for the app to reach the internet (Anthropic API, etc.)
# while RDS stays in private subnets.
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  name = "${var.name}-vpc"
  cidr = "10.0.0.0/16"

  azs             = slice(data.aws_availability_zones.available.names, 0, 2)
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24"]

  enable_nat_gateway = true
  single_nat_gateway = true # one NAT to keep costs down (~$32/mo)

  enable_dns_hostnames = true
  enable_dns_support   = true
}

# Security group attached to the App Runner VPC connector.
resource "aws_security_group" "apprunner" {
  name        = "${var.name}-apprunner"
  description = "App Runner VPC connector egress"
  vpc_id      = module.vpc.vpc_id

  egress {
    description = "all outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# RDS only accepts Postgres traffic from the App Runner connector SG.
resource "aws_security_group" "rds" {
  name        = "${var.name}-rds"
  description = "Postgres access from App Runner only"
  vpc_id      = module.vpc.vpc_id

  ingress {
    description     = "Postgres from App Runner"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.apprunner.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_apprunner_vpc_connector" "this" {
  vpc_connector_name = "${var.name}-conn"
  subnets            = module.vpc.private_subnets
  security_groups    = [aws_security_group.apprunner.id]
}
