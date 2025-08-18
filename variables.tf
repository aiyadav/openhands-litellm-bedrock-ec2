variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "m5.2xlarge"
}

variable "litellm_api_key" {
  description = "LiteLLM API key"
  type        = string
  default     = "sk-12345"
}

variable "ebs_volume_size" {
  description = "Size of EBS volume for OpenHands data in GB"
  type        = number
  default     = 20
}

variable "openhands_image" {
  description = "OpenHands Docker image"
  type        = string
  default     = "docker.all-hands.dev/all-hands-ai/openhands:0.53"
}

variable "openhands_runtime_image" {
  description = "OpenHands runtime Docker image"
  type        = string
  default     = "docker.all-hands.dev/all-hands-ai/runtime:0.53-nikolaik"
}

variable "litellm_image" {
  description = "LiteLLM Docker image"
  type        = string
  default     = "ghcr.io/berriai/litellm:main-latest"
}

