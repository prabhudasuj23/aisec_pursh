variable "aws_region" {
  description = "AWS region for AISec resources."
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Deployment environment: local, staging, or production."
  type        = string
  default     = "staging"

  validation {
    condition     = contains(["local", "staging", "production"], var.environment)
    error_message = "environment must be one of: local, staging, production."
  }
}

variable "project_name" {
  description = "Project name prefix applied to all resource names and tags."
  type        = string
  default     = "aisec"
}

variable "github_org" {
  description = "GitHub org or username that owns this repository. Used in OIDC trust policy."
  type        = string
  default     = "kvrp-csc-lgp"
}

variable "github_repo" {
  description = "GitHub repository name. Used in OIDC trust policy."
  type        = string
  default     = "ci_cd_seclab"
}
