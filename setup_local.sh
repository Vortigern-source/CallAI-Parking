#!/bin/bash

# Ensure we're in the project root
cd "$(dirname "$0")"

echo "Current directory: $(pwd)"

# Remove existing static directory to ensure clean state
rm -rf web-ui/backend/static
echo "Removed existing static directory"

# Create static directory
mkdir -p web-ui/backend/static
echo "Created new static directory"

# Copy the build files
echo "Copying build files..."
cp -r web-ui/build/* web-ui/backend/static/

# Verify the files were copied correctly
echo -e "\nStatic files copied successfully. Directory structure:"
find web-ui/backend/static -type f | sort

# Verify specific files
echo -e "\nVerifying key files:"
for file in "index.html" "asset-manifest.json" "static/js/main.bd332e19.js"; do
    if [ -f "web-ui/backend/static/$file" ]; then
        echo "✓ $file exists"
    else
        echo "✗ $file missing"
    fi
done
