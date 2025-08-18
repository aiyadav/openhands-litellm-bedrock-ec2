#!/bin/bash
echo "Installing Docker on Amazon Linux 2..."

# Update system
sudo yum update -y

# Create openhands-user
sudo useradd -m -s /bin/bash openhands-user
sudo usermod -aG wheel openhands-user

# Wait for EBS volume to be attached
echo "Waiting for EBS volume to be attached..."
while [ ! -e /dev/xvdf ]; do sleep 5; done

# Check if EBS volume has a filesystem, if not format it
if ! blkid /dev/xvdf; then
    echo "Formatting EBS volume..."
    sudo mkfs.ext4 /dev/xvdf
fi

# Create mount point and mount EBS volume
sudo mkdir -p /mnt/openhands-data
sudo mount /dev/xvdf /mnt/openhands-data

# Add to fstab for persistent mounting
echo '/dev/xvdf /mnt/openhands-data ext4 defaults,nofail 0 2' | sudo tee -a /etc/fstab

# Create OpenHands data directories on EBS
sudo mkdir -p /mnt/openhands-data/openhands
sudo mkdir -p /mnt/openhands-data/vscode-workspace
sudo chown openhands-user:openhands-user /mnt/openhands-data/openhands
sudo chown openhands-user:openhands-user /mnt/openhands-data/vscode-workspace

# Create symlink from home directory to EBS mount
sudo ln -sf /mnt/openhands-data/openhands /home/openhands-user/.openhands

# Install Docker
sudo yum install -y docker

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose



# Start and enable Docker
sudo systemctl start docker
sudo systemctl enable docker

# Add openhands-user to docker group
sudo usermod -aG docker openhands-user

# Create docker-compose.yml from template
cat > /home/openhands-user/docker-compose.yml << 'EOF'
${docker_compose_content}
EOF

# Create litellm-config.yml from template
cat > /home/openhands-user/litellm-config.yml << 'EOF'
${litellm_config_content}
EOF

# Create .openhands directory structure
mkdir -p /home/openhands-user/.openhands/microagents

# Create setup.sh
cat > /home/openhands-user/.openhands/setup.sh << 'EOF'
${openhands_setup_content}
EOF

# Create pre-commit.sh
cat > /home/openhands-user/.openhands/pre-commit.sh << 'EOF'
${openhands_precommit_content}
EOF

# Create all .md files from microagents folder
%{ for md_file in openhands_microagents_files ~}
cat > /home/openhands-user/.openhands/microagents/${md_file.name} << 'EOF'
${md_file.content}
EOF
%{ endfor ~}

# Make scripts executable
chmod +x /home/openhands-user/.openhands/setup.sh
chmod +x /home/openhands-user/.openhands/pre-commit.sh

# Set proper ownership
chown -R openhands-user:openhands-user /home/openhands-user/.openhands
chown openhands-user:openhands-user /home/openhands-user/docker-compose.yml
chown openhands-user:openhands-user /home/openhands-user/litellm-config.yml

# SSM Agent is pre-installed on Amazon Linux 2
sudo systemctl enable amazon-ssm-agent
sudo systemctl start amazon-ssm-agent

echo "Activating OpenHands and LiteLLM Docker"
sudo su - 
cd /home/openhands-user/
docker-compose up -d

echo "Docker installation and OpenHands setup complete!"
