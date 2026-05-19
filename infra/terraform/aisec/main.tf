provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
      Repository  = "github.com/${var.github_org}/${var.github_repo}"
    }
  }
}

# ── Terraform state backend ───────────────────────────────────────────────────
# Phase 0: local backend so `terraform plan` works without an S3 bucket.
# Migration path: replace with S3 + DynamoDB backend before production deploy.
#
#   terraform {
#     backend "s3" {
#       bucket         = "aisec-terraform-state-${var.environment}"
#       key            = "aisec/terraform.tfstate"
#       region         = "us-east-1"
#       encrypt        = true
#       dynamodb_table = "aisec-terraform-locks"
#     }
#   }
#
# See /docs/architecture/terraform-state-migration.md (Phase 1)
