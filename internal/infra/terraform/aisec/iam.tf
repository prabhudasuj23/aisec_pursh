# ── GitHub Actions OIDC provider ─────────────────────────────────────────────
# Allows GitHub Actions to assume AWS roles without long-lived access keys.
# Why: long-lived AWS keys in GitHub secrets are a supply-chain risk.
# Ephemeral OIDC credentials expire after the workflow run and cannot be reused.
resource "aws_iam_openid_connect_provider" "github_actions" {
  url = "https://token.actions.githubusercontent.com"

  client_id_list = ["sts.amazonaws.com"]

  # Thumbprint for token.actions.githubusercontent.com (as of 2024)
  # Update if GitHub rotates their TLS certificate.
  thumbprint_list = ["6938fd4d98bab03faadb97b34396831e3780aea1"]
}

# ── GitHub Actions role ───────────────────────────────────────────────────────
data "aws_iam_policy_document" "github_actions_trust" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.github_actions.arn]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }

    condition {
      test     = "StringLike"
      variable = "token.actions.githubusercontent.com:sub"
      # Restrict to this specific repo's main branch and PRs
      values = [
        "repo:${var.github_org}/${var.github_repo}:ref:refs/heads/main",
        "repo:${var.github_org}/${var.github_repo}:pull_request",
      ]
    }
  }
}

resource "aws_iam_role" "github_actions_oidc" {
  name               = "${var.project_name}-github-actions-oidc-${var.environment}"
  assume_role_policy = data.aws_iam_policy_document.github_actions_trust.json
  description        = "Role assumed by GitHub Actions via OIDC. No long-lived keys."
}

# Phase 0: minimal permissions — only ECR read for image pulls.
# Expand in Phase 5 (container scanning) and Phase 8 (CloudSec).
data "aws_iam_policy_document" "github_actions_minimal" {
  statement {
    effect = "Allow"
    actions = [
      "ecr:GetAuthorizationToken",
      "ecr:BatchGetImage",
      "ecr:GetDownloadUrlForLayer",
    ]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "github_actions_minimal" {
  name   = "minimal-ecr-read"
  role   = aws_iam_role.github_actions_oidc.id
  policy = data.aws_iam_policy_document.github_actions_minimal.json
}

# ── AISec ECS task execution role ────────────────────────────────────────────
# Used by ECS to pull images and write logs. Separate from the task role.
data "aws_iam_policy_document" "ecs_execution_trust" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "aisec_ecs_execution" {
  name               = "${var.project_name}-ecs-execution-${var.environment}"
  assume_role_policy = data.aws_iam_policy_document.ecs_execution_trust.json
  description        = "ECS task execution role: pull images, write logs."
}

resource "aws_iam_role_policy_attachment" "aisec_ecs_execution_managed" {
  role       = aws_iam_role.aisec_ecs_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# ── AISec ECS task role ───────────────────────────────────────────────────────
# Used by the running AISec container to access AWS services (Secrets Manager,
# S3, SQS, etc.). Follows least privilege — expand per feature phase.
resource "aws_iam_role" "aisec_ecs_task" {
  name               = "${var.project_name}-ecs-task-${var.environment}"
  assume_role_policy = data.aws_iam_policy_document.ecs_execution_trust.json
  description        = "AISec ECS task role: least-privilege access to AWS services."
}

# Phase 0: no permissions yet. Added per-phase as services are introduced.
# Phase 1: add Secrets Manager read for DB connection string
# Phase 5: add ECR push for scanner image builds
# Phase 8: add Security Hub write for CloudSec findings
