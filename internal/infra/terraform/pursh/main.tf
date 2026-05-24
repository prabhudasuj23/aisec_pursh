provider "aws" {
  region = var.aws_region
  alias  = "pursh"

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
      Repository  = "github.com/${var.github_org}/${var.github_repo}"
      # Pursh contains only synthetic data — no real PHI
      DataClass   = "synthetic"
    }
  }
}

# Phase 0: local backend. Migrate to S3 + DynamoDB before staging deploy.
