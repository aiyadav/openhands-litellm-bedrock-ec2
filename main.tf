terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.1"
    }
    http = {
      source  = "hashicorp/http"
      version = "~> 3.1"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]
  filter {
    name   = "name"
    values = ["al2023-ami-*-x86_64"]
  }
}

resource "aws_vpc" "openhands" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true
  
  tags = {
    Name = "openhands-vpc"
  }
}

resource "aws_subnet" "openhands" {
  vpc_id                  = aws_vpc.openhands.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = data.aws_availability_zones.available.names[0]
  map_public_ip_on_launch = true
  
  tags = {
    Name = "openhands-subnet"
  }
}

resource "aws_internet_gateway" "openhands" {
  vpc_id = aws_vpc.openhands.id
  
  tags = {
    Name = "openhands-igw"
  }
}

resource "aws_route_table" "openhands" {
  vpc_id = aws_vpc.openhands.id
  
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.openhands.id
  }
  
  tags = {
    Name = "openhands-rt"
  }
}

resource "aws_route_table_association" "openhands" {
  subnet_id      = aws_subnet.openhands.id
  route_table_id = aws_route_table.openhands.id
}

data "aws_availability_zones" "available" {
  state = "available"
}

data "http" "myip" {
  url = "http://ipv4.icanhazip.com"
}

resource "random_id" "suffix" {
  byte_length = 4
}

# Enable EC2 Serial Console access
resource "aws_ec2_serial_console_access" "example" {
  enabled = true
}

# VPC Endpoints for SSM
resource "aws_vpc_endpoint" "ssm" {
  vpc_id              = aws_vpc.openhands.id
  service_name        = "com.amazonaws.${var.aws_region}.ssm"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = [aws_subnet.openhands.id]
  security_group_ids  = [aws_security_group.vpc_endpoint.id]
  
  tags = {
    Name = "openhands-ssm-endpoint"
  }
}

resource "aws_vpc_endpoint" "ssmmessages" {
  vpc_id              = aws_vpc.openhands.id
  service_name        = "com.amazonaws.${var.aws_region}.ssmmessages"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = [aws_subnet.openhands.id]
  security_group_ids  = [aws_security_group.vpc_endpoint.id]
  
  tags = {
    Name = "openhands-ssmmessages-endpoint"
  }
}

resource "aws_vpc_endpoint" "ec2messages" {
  vpc_id              = aws_vpc.openhands.id
  service_name        = "com.amazonaws.${var.aws_region}.ec2messages"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = [aws_subnet.openhands.id]
  security_group_ids  = [aws_security_group.vpc_endpoint.id]
  
  tags = {
    Name = "openhands-ec2messages-endpoint"
  }
}

resource "aws_security_group" "vpc_endpoint" {
  name_prefix = "openhands-vpc-endpoint-"
  vpc_id      = aws_vpc.openhands.id
  
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = [aws_vpc.openhands.cidr_block]
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  tags = {
    Name = "openhands-vpc-endpoint-sg"
  }
}

resource "aws_security_group" "openhands" {
  name        = "openhands-sg-${random_id.suffix.hex}"
  description = "Managed by Terraform"
  vpc_id      = aws_vpc.openhands.id
  
  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["${chomp(data.http.myip.response_body)}/32"]
  }
  
  ingress {
    description = "OpenHands Web Interface"
    from_port   = 8150
    to_port     = 8150
    protocol    = "tcp"
    cidr_blocks = ["${chomp(data.http.myip.response_body)}/32"]
  }
  
  ingress {
    description = "LiteLLM API port 80"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["${chomp(data.http.myip.response_body)}/32"]
  }

  ingress {
    description = "LiteLLM API"
    from_port   = 8250
    to_port     = 8250
    protocol    = "tcp"
    cidr_blocks = ["${chomp(data.http.myip.response_body)}/32"]
  }

  ingress {
    description = "VS Code"
    from_port   = 30000
    to_port     = 60000
    protocol    = "tcp"
    cidr_blocks = ["${chomp(data.http.myip.response_body)}/32"]
  }
  
  ingress {
    description = "Browser"
    from_port   = 8080
    to_port     = 8080
    protocol    = "tcp"
    cidr_blocks = ["${chomp(data.http.myip.response_body)}/32"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  tags = {
    Name = "openhands-security-group"
  }
}



resource "aws_key_pair" "openhands" {
  key_name   = "openhands-key"
  public_key = tls_private_key.openhands.public_key_openssh
}

resource "tls_private_key" "openhands" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

resource "local_file" "private_key" {
  content  = tls_private_key.openhands.private_key_pem
  filename = "openhands-key.pem"
  file_permission = "0600"
}

resource "aws_iam_role" "ssm_role" {
  name = "openhands-ssm-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ssm_policy" {
  role       = aws_iam_role.ssm_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_role_policy_attachment" "bedrock_policy" {
  role       = aws_iam_role.ssm_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonBedrockFullAccess"
}

resource "aws_iam_role_policy" "bedrock_access" {
  name = "bedrock-access"
  role = aws_iam_role.ssm_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_instance_profile" "ssm_profile" {
  name = "openhands-ssm-profile"
  role = aws_iam_role.ssm_role.name
}

# EBS volume for persistent OpenHands data
resource "aws_ebs_volume" "openhands_data" {
  availability_zone = data.aws_availability_zones.available.names[0]
  size              = var.ebs_volume_size
  type              = "gp3"
  
  tags = {
    Name = "openhands-data-volume"
  }
}

resource "aws_volume_attachment" "openhands_data" {
  device_name = "/dev/xvdf"
  volume_id   = aws_ebs_volume.openhands_data.id
  instance_id = aws_instance.openhands.id
}

resource "aws_instance" "openhands" {
  ami           = data.aws_ami.amazon_linux.id
  instance_type = var.instance_type
  key_name      = aws_key_pair.openhands.key_name
  subnet_id     = aws_subnet.openhands.id
  iam_instance_profile = aws_iam_instance_profile.ssm_profile.name
  
  vpc_security_group_ids = [aws_security_group.openhands.id]
  
  user_data_replace_on_change = true

  user_data = templatefile("${path.module}/ec2-docker-install.sh", {
    docker_compose_content = templatefile("${path.module}/docker-compose.yml", {
      litellm_api_key = var.litellm_api_key
      openhands_image = var.openhands_image
      openhands_runtime_image = var.openhands_runtime_image
      litellm_image = var.litellm_image
    })
    litellm_config_content = file("${path.module}/litellm-config.yml")
    openhands_setup_content = file("${path.module}/.openhands/setup.sh")
    openhands_precommit_content = file("${path.module}/.openhands/pre-commit.sh")
    openhands_microagents_files = concat(
      [{
        name    = "repo.md"
        content = file("${path.module}/.openhands/microagents/repo.md")
      }],
      [
        for f in fileset("${path.module}/.openhands/microagents", "*.md") : {
          name    = f
          content = file("${path.module}/.openhands/microagents/${f}")
        } if f != "repo.md"
      ]
    )
  })
  
  root_block_device {
    volume_size = 30
  }
  
  tags = {
    Name = "openhands-server"
  }
  lifecycle {
    create_before_destroy = true
  }
}