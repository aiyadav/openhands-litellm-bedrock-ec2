output "instance_id" {
  description = "EC2 instance ID"
  value       = aws_instance.openhands.id
}

output "EC2_public_ip" {
  description = "EC2 public IP"
  value       = aws_instance.openhands.public_ip
}

output "ssh_command" {
  description = "SSH command to connect"
  value       = "ssh -i openhands-key.pem ec2-user@${aws_instance.openhands.public_ip}"
}

output "local_ip" {
  description = "Your local machine IP (allowed in security group)"
  value       = chomp(data.http.myip.response_body)
}

output "litellm_url" {
  description = "LiteLLM API URL"
  value       = "http://${aws_instance.openhands.public_ip}:8250"
}

output "openhands_url" {
  description = "OpenHands web interface URL"
  value       = "http://${aws_instance.openhands.public_ip}:8150"
}

output "user_data_logs_command" {
  description = "Command to view live user data execution logs"
  value       = "ssh -i openhands-key.pem -o StrictHostKeyChecking=no ec2-user@${aws_instance.openhands.public_ip} -t 'sudo tail -f /var/log/cloud-init-output.log'"
}
