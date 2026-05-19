# ── Pursh ECS task execution role ────────────────────────────────────────────
data "aws_iam_policy_document" "pursh_ecs_trust" {
  provider = aws.pursh

  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "pursh_ecs_execution" {
  provider           = aws.pursh
  name               = "${var.project_name}-ecs-execution-${var.environment}"
  assume_role_policy = data.aws_iam_policy_document.pursh_ecs_trust.json
  description        = "Pursh ECS task execution role: pull images, write logs."
}

resource "aws_iam_role_policy_attachment" "pursh_ecs_execution_managed" {
  provider   = aws.pursh
  role       = aws_iam_role.pursh_ecs_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# ── Pursh ECS task role ───────────────────────────────────────────────────────
# Used by the Pursh FastAPI container at runtime.
# Phase 6: add S3 + KMS permissions for file upload (lab results, prescriptions)
resource "aws_iam_role" "pursh_ecs_task" {
  provider           = aws.pursh
  name               = "${var.project_name}-ecs-task-${var.environment}"
  assume_role_policy = data.aws_iam_policy_document.pursh_ecs_trust.json
  description        = "Pursh ECS task role: least-privilege access. Synthetic data only."
}

# Phase 0: no permissions. Added per-phase.
# Phase 1: Secrets Manager read (Supabase connection string)
# Phase 6: S3 put/get on lab-results bucket with KMS decrypt
