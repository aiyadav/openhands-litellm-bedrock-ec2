#!/bin/bash
cd "$(dirname "$0")"

# Detect shell environment
if [[ -n "$MSYSTEM" ]] || [[ "$MSYSTEM_PREFIX" == *"MINGW"* ]]; then
    SHELL_TYPE="gitbash"
elif [[ -n "$ZSH_VERSION" ]]; then
    SHELL_TYPE="zsh"
elif [[ -n "$FISH_VERSION" ]]; then
    SHELL_TYPE="fish"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    SHELL_TYPE="linuxbash"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    SHELL_TYPE="macbash"
elif [[ "$OSTYPE" == "freebsd"* ]]; then
    SHELL_TYPE="freebsdbash"
elif [[ "$OSTYPE" == "solaris"* ]]; then
    SHELL_TYPE="solarisbash"
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
    SHELL_TYPE="wslbash"
else
    SHELL_TYPE="bash"
fi

python sso_aws_helper.py --shell="$SHELL_TYPE" "$@"