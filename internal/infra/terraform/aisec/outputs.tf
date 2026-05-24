output "github_actions_role_arn" {
  description = "ARN of the GitHub Actions OIDC role. Use in workflow `role-to-assume`."
  value       = aws_iam_role.github_actions_oidc.arn
}

output "aisec_ecs_task_role_arn" {
  description = "ARN of the AISec ECS task role."
  value       = aws_iam_role.aisec_ecs_task.arn
}

output "aisec_ecs_execution_role_arn" {
  description = "ARN of the AISec ECS task execution role."
  value       = aws_iam_role.aisec_ecs_execution.arn
}
