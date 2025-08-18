# Repository Overview

## Project: OpenHands with LiteLLM and AWS Bedrock on EC2

This repository contains Terraform infrastructure code to deploy OpenHands AI coding assistant on AWS EC2 with Bedrock integration.

### Key Components

- **main.tf**: Core Terraform configuration for EC2 instance and security groups
- **variables.tf**: Input variables for customization
- **outputs.tf**: Output values including EC2 public IP
- **terraform.tfvars**: Configuration values (API keys, instance settings)
- **docker-compose.yml**: Container orchestration for OpenHands and LiteLLM
- **litellm-config.yml**: LiteLLM proxy configuration for AWS Bedrock models
- **ec2-docker-install.sh**: EC2 initialization script

### Architecture

```
User → EC2 Instance → Docker Containers:
                     ├── OpenHands (Port 8150)
                     └── LiteLLM Proxy → AWS Bedrock
```

### Quick Commands

```bash
# Deploy
terraform init && terraform apply

# Update models
# Edit litellm-config.yml, then:
terraform apply

# Cleanup
terraform destroy
```

### Model Configuration

Models are configured in `litellm-config.yml`. Use `us.` prefix for cross-region inference models.

### Access

- OpenHands UI: `http://<EC2_PUBLIC_IP>:8150`
- Configure with Base URL: `http://litellm`
- Custom Model: `litellm_proxy/<model_name>`