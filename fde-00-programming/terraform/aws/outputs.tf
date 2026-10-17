output "ecr_repository_url" {
  description = "Push the image here: docker tag fde-00-programming:local <url>:<tag> && docker push <url>:<tag>"
  value       = aws_ecr_repository.app.repository_url
}

output "cluster_name" {
  value = aws_ecs_cluster.this.name
}

output "database_endpoint" {
  description = "Private RDS endpoint (reachable only from the ECS tasks)"
  value       = aws_db_instance.db.address
}

output "run_ingest_now" {
  description = "Start the ingest task once, without waiting for the schedule"
  value       = "aws ecs run-task --cluster ${aws_ecs_cluster.this.name} --launch-type FARGATE --task-definition ${aws_ecs_task_definition.ingest.family} --network-configuration 'awsvpcConfiguration={subnets=[${join(",", data.aws_subnets.default.ids)}],securityGroups=[${aws_security_group.app.id}],assignPublicIp=ENABLED}'"
}

output "find_public_ip" {
  description = "Command that prints the API task's public IP for the smoke test"
  value       = "aws ecs list-tasks --cluster ${aws_ecs_cluster.this.name} --service-name ${aws_ecs_service.app.name} --query 'taskArns[0]' --output text | xargs -I{} aws ecs describe-tasks --cluster ${aws_ecs_cluster.this.name} --tasks {} --query \"tasks[0].attachments[0].details[?name=='networkInterfaceId'].value\" --output text | xargs -I{} aws ec2 describe-network-interfaces --network-interface-ids {} --query 'NetworkInterfaces[0].Association.PublicIp' --output text"
}
