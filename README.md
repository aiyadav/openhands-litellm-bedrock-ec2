# Deploy OpenHands with LiteLLM and AWS Bedrock on EC2

Deploy OpenHands AI coding assistant on AWS EC2 with Bedrock integration.

## Prerequisites

- Terraform installed (verify with `terraform --version`)
- AWS Bedrock model access approved (go to AWS Bedrock Console → Model Access (left pane scroll down) → Request access for required models)
- **For SSO Method**: AWS Username and Password ready
- **For Manual Method**: AWS Access Key, Secret Key, and Session Token ready

## Quick Start

1. **Setup credentials** (Choose one method):

      **Method 1: SSO Login** (Recommended)
      
      Update **sso_config.ini** with your **sso_start_url** and **regions** if required:
      ```bash
      ./sso_login.sh    # Linux/Mac
      .\sso_login.bat   # Windows PowerShell
      sso_login.bat     # Windows CMD
      ```
      Follow browser prompts: "Confirm and continue" → "Allow" → Close when "Request approved" appears.  
      Switch back to terminal - it will auto-configure AWS profiles for Terraform.
      
      ⚠️ **Important!**: Follow the instructions at the end to test your SSO login.

      **Method 2: Manual Environment Variables**
      ```bash
      # Directly paste these commands in your bash shell:
      export AWS_ACCESS_KEY_ID="your_access_key"
      export AWS_SECRET_ACCESS_KEY="your_secret_key"
      export AWS_SESSION_TOKEN="your_session_token"
      ```

2. **Configure**:
   ```bash
   # Edit terraform.tfvars and set:
   litellm_api_key = "sk-<your-choice-key>"
   ```

4. **Deploy**:
   ```bash
   terraform init
   terraform apply
   ```

5. **Access**: `http://<EC2_PUBLIC_IP>:8150`

6. **Set LLM**:
   - On first launch, a popup will appear - click "see advanced settings" (small text on top right of popup)
   - Or click gear icon at bottom left
   - Ensure that you are on LLM tab
   - Make sure "Advanced" toggle is enabled, you will see below options:
   - Enter **Custom Model** as: `litellm_proxy/ClaudeSonnet4` (keep `litellm_proxy/` and replace only ClaudeSonnet4 with any model_name from litellm-config.yml)
   - Enter **Base URL** as: `http://litellm`
   - Enter **API Key** as: Your `litellm_api_key` from terraform.tfvars (e.g., "sk-xxx")
   - Click **Save Changes** button on bottom right
   - A "Settings saved" message will appear confirming successful configuration
   - Complete the "Your Privacy Preferences" popup by selecting your data sharing preference

7. **Launching OpenHands Workspace with LiteLLM**:
   - Click **Plus** on top left to start a new session
   - Choose "Launch from scratch" or connect to repository (recommended: "Launch from scratch" for testing)
   - After clicking "Launch from scratch", a new window opens showing startup sequence (takes 1-1.5 mins):
     - "Connecting" → "Starting runtime..." → "Initializing agent..." → "Agent is awaiting user input..."
   - Once you see "Agent is awaiting user input...", you can start using OpenHands

## Model Configuration

**Adding/Removing Models**: You have two options:

**Option 1 - Terraform Redeploy** (Recommended):
- Update `litellm-config.yml` locally
- Run `terraform apply` - it will quickly recreate EC2 with updated models

**Option 2 - Manual EC2 Edit**:
- SSH into the instance → `sudo su - root` → Go to `/home/openhands-user/`
- Edit `litellm-config.yml` directly on EC2

⚠️ **Important**: If using Option 2, always update your local Terraform files too, or next deployment will overwrite your changes!

## 🔧 Troubleshooting

### Model Not Working? Check Cross-Region Settings!

Some Bedrock models need special configuration. Here's how to fix it:

**🔍 Step 1: Check Your Model Type**
- Open AWS Bedrock Console → **Model Access** (left sidebar)
- Find your model and look for **"Cross-region inference"** text

**⚙️ Step 2: Configure Based on What You See**

✅ **Sees "Cross-region inference"?** → Add `us.` prefix:
```yaml
model: us.anthropic.claude-sonnet-4-20250514-v1:0
```

❌ **No "Cross-region inference"?** → No `us.` prefix needed:
```yaml
model: anthropic.claude-3-haiku-20240307-v1:0
```

**💡 Pro Tips:**
- `model_name` = What you type in OpenHands UI
- `model` = Actual Bedrock identifier in config
- `bedrock/` prefix is optional - your EC2 auto-routes to Bedrock anyway!

## Cleanup

```bash
# Ensure your AWS credentials are not expired or use latest credentials before running terraform destroy:
terraform destroy
```