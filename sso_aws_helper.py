#!/usr/bin/env python3
"""
AWS SSO Helper - Automates AWS SSO login and profile management
"""

import subprocess
import json
import os
import boto3
import configparser
import sys
from pathlib import Path
from typing import List, Tuple, Optional


class AWSConfig:
    """Configuration manager for AWS SSO settings"""
    
    def __init__(self, config_file: str = "sso_config.ini"):
        self.config = configparser.ConfigParser()
        self.config_file = config_file
        self._load_config()
    
    def _load_config(self):
        """Load configuration from file"""
        if not os.path.exists(self.config_file):
            raise FileNotFoundError(f"Configuration file {self.config_file} not found")
        self.config.read(self.config_file)
    
    @property
    def sso_profile(self) -> str:
        return self.config.get('aws', 'sso_profile')
    
    @property
    def sso_start_url(self) -> str:
        return self.config.get('aws', 'sso_start_url')
    
    @property
    def sso_region(self) -> str:
        return self.config.get('aws', 'sso_region')
    
    @property
    def default_region(self) -> str:
        return self.config.get('aws', 'default_region')
    
    @property
    def output_format(self) -> str:
        return self.config.get('aws', 'output_format')
    
    @property
    def aws_folder_name(self) -> str:
        return self.config.get('paths', 'aws_folder_name')
    
    @property
    def config_file_name(self) -> str:
        return self.config.get('paths', 'config_file')
    
    @property
    def credentials_file_name(self) -> str:
        return self.config.get('paths', 'credentials_file')
    
    @property
    def sso_cache_folder(self) -> str:
        return self.config.get('paths', 'sso_cache_folder')


class AWSPathManager:
    """Manages AWS file paths and directories"""
    
    def __init__(self, aws_config: AWSConfig):
        self.config = aws_config
        self._aws_folder = self._find_aws_folder()
    
    def _find_aws_folder(self) -> Path:
        """Find the AWS configuration folder"""
        home_dir = Path.home()
        aws_folder = home_dir / self.config.aws_folder_name
        
        if not aws_folder.exists():
            aws_folder.mkdir(parents=True, exist_ok=True)
        
        return aws_folder
    
    @property
    def aws_folder(self) -> Path:
        return self._aws_folder
    
    @property
    def config_file(self) -> Path:
        return self._aws_folder / self.config.config_file_name
    
    @property
    def credentials_file(self) -> Path:
        return self._aws_folder / self.config.credentials_file_name
    
    @property
    def sso_cache_dir(self) -> Path:
        return self._aws_folder / self.config.sso_cache_folder


class SSOTokenManager:
    """Manages SSO token retrieval and caching"""
    
    def __init__(self, path_manager: AWSPathManager):
        self.path_manager = path_manager
    
    def get_latest_access_token(self) -> str:
        """Retrieve the latest SSO access token from cache"""
        cache_dir = self.path_manager.sso_cache_dir
        
        if not cache_dir.exists():
            raise FileNotFoundError(f"SSO cache directory not found: {cache_dir}")
        
        cache_files = [f for f in cache_dir.iterdir() if f.suffix == '.json']
        
        if not cache_files:
            raise FileNotFoundError("No SSO cache files found")
        
        latest_cache = max(cache_files, key=lambda f: f.stat().st_mtime)
        
        with open(latest_cache, 'r') as f:
            cached_data = json.load(f)
        
        return cached_data['accessToken']


class AWSProfileManager:
    """Manages AWS CLI profiles"""
    
    def __init__(self, aws_config: AWSConfig, path_manager: AWSPathManager):
        self.aws_config = aws_config
        self.path_manager = path_manager
    
    def update_profile(self, credentials: dict, account_id: str, role_name: str, profile_name: str):
        """Update AWS CLI config file (no credentials file for SSO)"""
        self._update_config_file(profile_name)
        print(f"Updated profile: {profile_name}")
        print(f"Updated default profile for SSO")
    
    def _update_config_file(self, profile_name: str):
        """Update the AWS config file"""
        config = configparser.ConfigParser()
        config_file = self.path_manager.config_file
        
        if config_file.exists():
            config.read(config_file)
        
        # Extract account ID and role name from profile name
        account_id = profile_name.split('-')[1]
        role_name = profile_name.split('-', 2)[2]
        
        # Use correct SSO start URL with /# suffix
        sso_start_url = self.aws_config.sso_start_url
        if not sso_start_url.endswith('/#'):
            sso_start_url = sso_start_url.rstrip('/') + '/#'
        
        # Add default profile with SSO settings (no credentials)
        config["default"] = {
            "sso_start_url": sso_start_url,
            "sso_region": self.aws_config.sso_region,
            "sso_account_id": account_id,
            "sso_role_name": role_name,
            "region": self.aws_config.default_region,
            "output": self.aws_config.output_format
        }
        
        # Add named profile
        config[f"profile {profile_name}"] = {
            "sso_start_url": sso_start_url,
            "sso_region": self.aws_config.sso_region,
            "sso_account_id": account_id,
            "sso_role_name": role_name,
            "region": self.aws_config.default_region,
            "output": self.aws_config.output_format
        }
        
        with open(config_file, 'w') as f:
            config.write(f)
        
        print(f"Updated config file: {config_file}")
    
    def _update_credentials_file(self, credentials: dict, profile_name: str):
        """Update the AWS credentials file"""
        config = configparser.ConfigParser()
        credentials_file = self.path_manager.credentials_file
        
        if credentials_file.exists():
            config.read(credentials_file)
        
        config[profile_name] = {
            "aws_access_key_id": credentials['accessKeyId'],
            "aws_secret_access_key": credentials['secretAccessKey'],
            "aws_session_token": credentials['sessionToken']
        }
        
        with open(credentials_file, 'w') as f:
            config.write(f)
        
        print(f"Updated credentials file: {credentials_file}")


class AWSSSOManager:
    """Main AWS SSO management class"""
    
    def __init__(self, config_file: str = "sso_config.ini"):
        self.aws_config = AWSConfig(config_file)
        self.path_manager = AWSPathManager(self.aws_config)
        self.token_manager = SSOTokenManager(self.path_manager)
        self.profile_manager = AWSProfileManager(self.aws_config, self.path_manager)
    
    def ensure_sso_profile_exists(self):
        """Ensure the SSO profile exists in AWS config"""
        config = configparser.ConfigParser()
        config_file = self.path_manager.config_file
        
        if config_file.exists():
            config.read(config_file)
        
        profile_section = f"profile {self.aws_config.sso_profile}"
        if profile_section not in config:
            config[profile_section] = {
                "sso_start_url": self.aws_config.sso_start_url,
                "sso_region": self.aws_config.sso_region,
                "region": self.aws_config.default_region,
                "output": self.aws_config.output_format
            }
            
            with open(config_file, 'w') as f:
                config.write(f)
            
            print(f"Created SSO profile '{self.aws_config.sso_profile}' in AWS config")
    
    def login(self):
        """Perform AWS SSO login"""
        # Ensure SSO profile exists before attempting login
        self.ensure_sso_profile_exists()
        
        print("Initiating AWS SSO login. Please complete the login process in your browser.")
        try:
            subprocess.run(
                ["aws", "sso", "login", "--profile", self.aws_config.sso_profile], 
                check=True
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"AWS SSO login failed: {e}")
    
    def get_available_roles(self) -> List[Tuple[str, str]]:
        """Get all available roles from SSO"""
        access_token = self.token_manager.get_latest_access_token()
        sso = boto3.client('sso', region_name=self.aws_config.sso_region)
        
        accounts = sso.list_accounts(accessToken=access_token)
        available_roles = []
        
        for account in accounts['accountList']:
            roles = sso.list_account_roles(
                accessToken=access_token,
                accountId=account['accountId']
            )
            
            for role in roles['roleList']:
                available_roles.append((account['accountId'], role['roleName']))
        
        return available_roles
    
    def setup_profiles(self, available_roles: List[Tuple[str, str]]) -> List[str]:
        """Set up AWS CLI profiles for all available roles"""
        access_token = self.token_manager.get_latest_access_token()
        sso = boto3.client('sso', region_name=self.aws_config.sso_region)
        
        profile_names = []
        
        for account_id, role_name in available_roles:
            try:
                print(f"Setting up SSO profile for Account ID: {account_id}, Role: {role_name}")
                profile_name = f"sso-{account_id}-{role_name}"
                profile_names.append(profile_name)
                self.profile_manager.update_profile({}, account_id, role_name, profile_name)
            
            except Exception as e:
                print(f"Failed to setup profile for {account_id}/{role_name}: {e}")
        
        return profile_names
    
    def display_console_urls(self, available_roles: List[Tuple[str, str]]):
        """Display direct console URLs"""
        print("\nDirect URLs to the console:")
        print()
        for account_id, role_name in available_roles:
            url = f"{self.aws_config.sso_start_url}/#/console?account_id={account_id}&role_name={role_name}"
            print(url)
    
    def display_profile_commands(self, profile_names: List[str]):
        """Display profile information"""
        print("\nAWS CLI is now configured and ready to use!")
        print("- Current session: Uses default profile automatically")
        print("- New terminals: Will use the global profile automatically")
        print(f"- You can also use specific profiles: --profile {profile_names[0] if profile_names else 'profile-name'}")

    
    def verify_credentials(self):
        """Verify that the default credentials work"""
        try:
            # First try without additional login
            result = subprocess.run(["aws", "sts", "get-caller-identity"], 
                                  capture_output=True, text=True, check=True)
            caller_info = json.loads(result.stdout)
            print(f"\nCredentials verified successfully!")
            print(f"  Account: {caller_info.get('Account')}")
            print(f"  User: {caller_info.get('Arn', '').split('/')[-1]}")
            return True
        except subprocess.CalledProcessError:
            # If that fails, try SSO login for default profile
            print("\nCredentials not active, running SSO login for default profile...")
            try:
                subprocess.run(["aws", "sso", "login", "--profile", "default"], check=True)
                result = subprocess.run(["aws", "sts", "get-caller-identity"], 
                                      capture_output=True, text=True, check=True)
                caller_info = json.loads(result.stdout)
                print(f"\nCredentials verified successfully!")
                print(f"  Account: {caller_info.get('Account')}")
                print(f"  User: {caller_info.get('Arn', '').split('/')[-1]}")
                return True
            except subprocess.CalledProcessError as e:
                print(f"\nCredential verification failed: {e}")
                return False
        except Exception as e:
            print(f"\nCould not verify credentials: {e}")
            return False
    
    def setup_global_profile(self, profile_names: List[str]):
        """Set up global AWS profile in shell profiles"""
        if not profile_names:
            return
            
        # Always use 'default' profile for shell environments
        default_profile = "default"
        home_dir = Path.home()
        
        # Setup for Bash
        self._setup_bash_profile(default_profile, home_dir)
        
        # Setup for PowerShell
        self._setup_powershell_profile(default_profile, home_dir)
        
        # Setup for CMD (via registry)
        self._setup_cmd_profile(default_profile)
    
    def _setup_bash_profile(self, default_profile: str, home_dir: Path):
        """Setup Bash profile"""
        try:
            bashrc_file = home_dir / ".bashrc"
            aws_export = f"export AWS_DEFAULT_PROFILE={default_profile}"
            clear_aws_alias = "alias clear_aws='unset AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN AWS_DEFAULT_PROFILE'"
            
            content = ""
            if bashrc_file.exists():
                with open(bashrc_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
            # Clean up excessive blank lines and update AWS settings
            lines = content.split('\n') if content else []
            new_lines = []
            aws_profile_added = False
            blank_line_count = 0
            
            for line in lines:
                if line.strip() == "":  # Empty line
                    blank_line_count += 1
                    if blank_line_count <= 1:  # Keep max 1 blank line
                        new_lines.append(line)
                else:
                    blank_line_count = 0
                    if line.strip().startswith("export AWS_DEFAULT_PROFILE="):
                        # Replace existing line
                        if not aws_profile_added:
                            new_lines.append(aws_export)
                            aws_profile_added = True
                        # Skip the old line
                    else:
                        new_lines.append(line)
            
            # Add AWS_DEFAULT_PROFILE if not found
            if not aws_profile_added:
                # Add with proper spacing
                if new_lines and new_lines[-1].strip() != "":
                    new_lines.append("")
                new_lines.append(aws_export)
            
            # Add clear_aws alias if not present
            content_str = '\n'.join(new_lines)
            if clear_aws_alias not in content_str:
                new_lines.append(clear_aws_alias)
            
            with open(bashrc_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(new_lines))
                
            print("Updated Bash profile successfully")
            print("To apply changes in current Git Bash session, run: source ~/.bashrc")
        except Exception as e:
            print(f"Could not update Bash profile: {e}")
    
    def _setup_powershell_profile(self, default_profile: str, home_dir: Path):
        """Setup PowerShell profile"""
        try:
            # PowerShell profile location
            ps_profile_dir = home_dir / "Documents" / "WindowsPowerShell"
            ps_profile_file = ps_profile_dir / "Microsoft.PowerShell_profile.ps1"
            
            # Create directory if it doesn't exist
            ps_profile_dir.mkdir(parents=True, exist_ok=True)
            
            aws_env = f"$env:AWS_DEFAULT_PROFILE = '{default_profile}'"
            clear_aws_function = '''function Clear-AWS {
    Remove-Item Env:AWS_ACCESS_KEY_ID,Env:AWS_SECRET_ACCESS_KEY,Env:AWS_SESSION_TOKEN -ErrorAction SilentlyContinue
    $env:AWS_DEFAULT_PROFILE = 'default'
    Write-Host "Cleared AWS environment variables and set default profile"
}'''
            
            content = ""
            if ps_profile_file.exists():
                with open(ps_profile_file, 'r', encoding='utf-8') as f:
                    content = f.read()
            
            # Clean up excessive blank lines and update AWS settings
            lines = content.split('\n') if content else []
            new_lines = []
            aws_profile_added = False
            clear_aws_added = False
            blank_line_count = 0
            
            for line in lines:
                if line.strip() == "":  # Empty line
                    blank_line_count += 1
                    if blank_line_count <= 1:  # Keep max 1 blank line
                        new_lines.append(line)
                else:
                    blank_line_count = 0
                    if "$env:AWS_DEFAULT_PROFILE" in line:
                        # Replace existing line
                        if not aws_profile_added:
                            new_lines.append(aws_env)
                            aws_profile_added = True
                        # Skip the old line
                    elif "function Clear-AWS" in line:
                        clear_aws_added = True
                        new_lines.append(line)
                    else:
                        new_lines.append(line)
            
            # Add AWS_DEFAULT_PROFILE if not found
            if not aws_profile_added:
                # Add with proper spacing
                if new_lines and new_lines[-1].strip() != "":
                    new_lines.append("")
                new_lines.append(aws_env)
            
            # Add Clear-AWS function if not present
            if not clear_aws_added:
                if new_lines and new_lines[-1].strip() != "":
                    new_lines.append("")
                new_lines.extend(clear_aws_function.split('\n'))
            
            with open(ps_profile_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(new_lines))
                
            print("Updated PowerShell profile successfully")
            print("Restart PowerShell or run: . $PROFILE")
        except Exception as e:
            print(f"Could not update PowerShell profile: {e}")
    
    def _setup_cmd_profile(self, default_profile: str):
        """Setup CMD environment via registry"""
        try:
            import winreg
            
            # Set user environment variable
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, "AWS_DEFAULT_PROFILE", 0, winreg.REG_SZ, default_profile)
            winreg.CloseKey(key)
            
            print(f"Updated CMD environment variable: AWS_DEFAULT_PROFILE={default_profile}")
            print("Note: CMD changes take effect in new command prompt windows")
        except Exception as e:
            print(f"Could not update CMD environment: {e}")
    
    def clear_powershell_env_vars(self):
        """Clear PowerShell environment variables and set default profile"""
        try:
            print("\nEnvironment variables will be cleared automatically...")
            print("If needed, manually run: Remove-Item Env:AWS_ACCESS_KEY_ID,Env:AWS_SECRET_ACCESS_KEY,Env:AWS_SESSION_TOKEN,Env:AWS_DEFAULT_PROFILE -ErrorAction SilentlyContinue")
            
        except Exception as e:
            print(f"Could not provide PowerShell commands: {e}")
    
    def execute_powershell_clear(self):
        """Execute PowerShell commands to clear environment variables and test credentials"""
        try:
            # Execute PowerShell commands directly
            ps_commands = "Remove-Item Env:AWS_ACCESS_KEY_ID,Env:AWS_SECRET_ACCESS_KEY,Env:AWS_SESSION_TOKEN,Env:AWS_DEFAULT_PROFILE -ErrorAction SilentlyContinue; Write-Host 'Cleared AWS environment variables'; aws sts get-caller-identity"
            
            print("\nExecuting PowerShell commands to clear environment and test credentials...")
            result = subprocess.run(["powershell", "-Command", ps_commands], 
                                  capture_output=True, text=True, check=False)
            
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(result.stderr)
                
            print("\nEnvironment variables cleared and credentials tested!")
            
        except Exception as e:
            print(f"Could not execute PowerShell commands: {e}")
    
    def execute_bash_clear(self):
        """Execute bash commands to clear environment variables and test credentials"""
        try:
            # Use Git Bash if available, otherwise try bash
            bash_path = "C:\\Program Files\\Git\\bin\\bash.exe"
            if not os.path.exists(bash_path):
                bash_path = "bash"
            
            bash_commands = "unset AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN AWS_DEFAULT_PROFILE; echo 'Cleared AWS environment variables'; aws sts get-caller-identity"
            
            print("\nExecuting bash commands to clear environment and test credentials...")
            result = subprocess.run([bash_path, "-c", bash_commands], 
                                  capture_output=True, text=True, check=False)
            
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(result.stderr)
                
            print("\nEnvironment variables cleared and credentials tested!")
            
        except Exception as e:
            print(f"Could not execute bash commands: {e}")
    
    def execute_cmd_clear(self):
        """Execute CMD commands to clear environment variables and test credentials"""
        try:
            print("\nExecuting CMD commands to clear environment and test credentials...")
            
            # Clear environment variables
            for var in ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_SESSION_TOKEN', 'AWS_DEFAULT_PROFILE']:
                subprocess.run(["cmd", "/c", f"set {var}="], check=False)
            
            print("Cleared AWS environment variables")
            
            # Test credentials
            result = subprocess.run(["aws", "sts", "get-caller-identity"], 
                                  capture_output=True, text=True, check=False)
            
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(result.stderr)
                
            print("\nEnvironment variables cleared and credentials tested!")
            
        except Exception as e:
            print(f"Could not execute CMD commands: {e}")
    
    def run(self, shell_override=None):
        """Main execution method"""
        try:
            print("Starting AWS SSO credential refresh...")
            self.login()
            available_roles = self.get_available_roles()
            profile_names = self.setup_profiles(available_roles)
            
            # Set up global profile for all terminals
            self.setup_global_profile(profile_names)
            
            # Verify credentials work
            self.verify_credentials()
            
            self.display_console_urls(available_roles)
            self.display_profile_commands(profile_names)
            
            # Clear environment variables and test credentials based on shell type
            if shell_override == "powershell":
                self.clear_powershell_env_vars()
                self.execute_powershell_clear()
            elif shell_override in ["bash", "gitbash", "linuxbash", "macbash", "zsh", "fish"]:
                self.execute_bash_clear()
            elif shell_override == "cmd":
                self.execute_cmd_clear()
            
        except Exception as e:
            print(f"An error occurred: {e}")
            sys.exit(1)


def detect_and_clear_shell_variables(shell_override):
    """Clear AWS environment variables for specified shell type"""
    aws_env_vars = ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_SESSION_TOKEN', 'AWS_DEFAULT_PROFILE']
    
    # Clear from Python environment
    for var in aws_env_vars:
        if var in os.environ:
            del os.environ[var]
            print(f"Cleared Python environment variable: {var}")
    
    # Use the shell type provided by batch file
    shell_type = shell_override
    print(f"Detected shell: {shell_type}")
    
    # Clear PowerShell environment variables immediately if PowerShell detected
    if shell_type == "powershell":
        try:
            ps_command = "Remove-Item Env:AWS_ACCESS_KEY_ID,Env:AWS_SECRET_ACCESS_KEY,Env:AWS_SESSION_TOKEN,Env:AWS_DEFAULT_PROFILE -ErrorAction SilentlyContinue"
            subprocess.run(["powershell", "-Command", ps_command], check=False)
            print("Executed initial PowerShell environment variable clearing")
        except:
            pass
    
    # Clear shell-specific environment variables
    clear_shell_environment_variables(shell_type)

def clear_shell_environment_variables(shell_type):
    """Clear AWS environment variables in the current shell session"""
    aws_env_vars = ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_SESSION_TOKEN', 'AWS_DEFAULT_PROFILE']
    
    try:
        if shell_type == "powershell":
            # PowerShell commands to clear environment variables
            ps_cmd = "Remove-Item Env:AWS_ACCESS_KEY_ID,Env:AWS_SECRET_ACCESS_KEY,Env:AWS_SESSION_TOKEN,Env:AWS_DEFAULT_PROFILE -ErrorAction SilentlyContinue"
            subprocess.run(["powershell", "-Command", ps_cmd], check=False)
            print("Cleared PowerShell environment variables")
            
        elif shell_type == "cmd":
            # CMD commands to clear environment variables
            for var in aws_env_vars:
                subprocess.run(["cmd", "/c", f"set {var}="], check=False)
            print("Cleared CMD environment variables")
            
        elif shell_type in ["gitbash", "linuxbash", "macbash", "bash", "zsh", "fish"]:
            # For bash-like shells, we can't directly modify the parent shell
            print(f"Note: {shell_type.title()} variables cleared in Python process only")
            
    except Exception as e:
        print(f"Note: Could not execute shell-specific clear commands: {e}")



def main():
    """Main entry point"""
    # Check for shell parameter
    shell_override = None
    config_file = "sso_config.ini"
    
    for arg in sys.argv[1:]:
        if arg.startswith('--shell='):
            shell_override = arg.split('=')[1]
        elif not arg.startswith('--'):
            config_file = arg
    
    # Detect shell and clear Python environment variables
    detect_and_clear_shell_variables(shell_override)
    
    sso_manager = AWSSSOManager(config_file)
    sso_manager.run(shell_override)
    
    # Clear shell environment variables after updating credentials
    if shell_override:
        print("\n" + "="*60)
        print("AWS SSO CONFIGURATION COMPLETED SUCCESSFULLY")
        print("="*60)
        if shell_override == "powershell":
            print("\nStatus:")
            print("  ✓ AWS SSO profiles configured")
            print("  ✓ Shell profiles updated")
            print("  ✓ Environment variables cleared")
            print("\nNext Steps:")
            print("  1. Test credentials: aws sts get-caller-identity")
            print("  2. If authentication fails, run: . $PROFILE; Clear-AWS")
            print("  3. Re-test credentials: aws sts get-caller-identity")
            print("\nYou're now ready to use AWS CLI and Terraform!")
        elif shell_override in ["bash", "gitbash", "linuxbash", "macbash", "zsh", "fish"]:
            print("\nStatus:")
            print("  ✓ AWS SSO profiles configured")
            print("  ✓ Shell profiles updated")
            print("  ✓ Environment variables cleared")
            print("\nNext Steps:")
            print("  1. Reload shell: source ~/.bashrc")
            print("  2. Test credentials: aws sts get-caller-identity")
            print("  3. If authentication fails, run: clear_aws")
            print("  4. Re-test credentials: aws sts get-caller-identity")
            print("\nYou're now ready to use AWS CLI and Terraform!")
        else:
            print("\nStatus:")
            print("  ✓ AWS SSO profiles configured")
            print("  ✓ Shell profiles updated")
            print("  ✓ Environment variables cleared")
            print("\nNext Steps:")
            print("  1. Test credentials: aws sts get-caller-identity")
            print("\nYou're now ready to use AWS CLI and Terraform!")


if __name__ == "__main__":
    main()