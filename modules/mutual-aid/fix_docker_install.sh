#!/bin/bash

# Script to fix Docker installation issues

echo "Fixing Docker installation issues..."

# Remove the conflicting binary
if [ -f "/usr/local/bin/hub-tool" ]; then
    echo "Removing conflicting binary: /usr/local/bin/hub-tool"
    sudo rm -f /usr/local/bin/hub-tool
fi

# Try to install Docker again
echo "Installing Docker Desktop..."
brew install --cask docker

if [ -d "/Applications/Docker.app" ]; then
    echo "✅ Docker Desktop installed successfully!"
    echo "Starting Docker Desktop..."
    open -a Docker
    echo "Please wait for Docker Desktop to start, then run the launch script again."
else
    echo "❌ Installation failed. Please install Docker Desktop manually:"
    echo "https://www.docker.com/products/docker-desktop/"
fi

