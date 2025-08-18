#!/bin/bash

# OpenHands Pre-commit Hook
# This script runs before each commit

echo "Running pre-commit checks..."

# Terraform format check
if [ -f "main.tf" ]; then
    echo "Formatting Terraform files..."
    terraform fmt
fi

# Check for sensitive data
echo "Checking for sensitive data..."
if grep -r "AKIA\|aws_access_key\|aws_secret" --exclude-dir=.git --exclude="*.md" .; then
    echo "ERROR: Potential AWS credentials found in files!"
    exit 1
fi

# Validate Terraform configuration
if [ -f "main.tf" ]; then
    echo "Validating Terraform configuration..."
    terraform validate
fi

echo "Pre-commit checks passed!"