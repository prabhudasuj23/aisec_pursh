output "pursh_ecs_task_role_arn" {
  description = "ARN of the Pursh ECS task role."
  value       = aws_iam_role.pursh_ecs_task.arn
}

output "pursh_ecs_execution_role_arn" {
  description = "ARN of the Pursh ECS task execution role."
  value       = aws_iam_role.pursh_ecs_execution.arn
}
