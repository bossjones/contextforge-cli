#!/bin/bash

# Set Taplo version
TAPLO_VERSION=0.9.3

# Determine the architecture
if [ "$(uname -m)" = "aarch64" ]; then
    DESIRED_ARCH=aarch64
elif [ "$(uname -m)" = "x86_64" ]; then
    DESIRED_ARCH=x86_64
else
    echo "Unsupported architecture: $(uname -m)"
    exit 1
fi

# Download Taplo
curl -Lo taplo-v${TAPLO_VERSION}.linux.${DESIRED_ARCH}.gz https://github.com/tamasfe/taplo/releases/download/${TAPLO_VERSION}/taplo-linux-${DESIRED_ARCH}.gz

# Decompress the file
gunzip -c taplo-v${TAPLO_VERSION}.linux.${DESIRED_ARCH}.gz > taplo

# Remove the compressed file
rm taplo-v${TAPLO_VERSION}.linux.${DESIRED_ARCH}.gz

# Make the binary executable
chmod +x taplo

echo "Taplo v${TAPLO_VERSION} for ${DESIRED_ARCH} has been installed successfully."
