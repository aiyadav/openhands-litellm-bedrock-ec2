@echo off
cd /d "%~dp0"

:: Clear AWS environment variables first
set AWS_ACCESS_KEY_ID=
set AWS_SECRET_ACCESS_KEY=
set AWS_SESSION_TOKEN=
set AWS_DEFAULT_PROFILE=default

:: Check if launched from PowerShell by examining CMDCMDLINE for /c parameter
echo %CMDCMDLINE% | findstr /c:"/c" >nul
if %errorlevel%==0 (
    powershell -Command "& { python sso_aws_helper.py --shell=powershell %*; Remove-Item Env:AWS_ACCESS_KEY_ID,Env:AWS_SECRET_ACCESS_KEY,Env:AWS_SESSION_TOKEN,Env:AWS_DEFAULT_PROFILE -ErrorAction SilentlyContinue; $env:AWS_DEFAULT_PROFILE = 'default' }"
) else (
    python sso_aws_helper.py --shell=cmd %*
)