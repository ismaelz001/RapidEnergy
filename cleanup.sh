#!/bin/bash
# cleanup.sh - Surgical cleanup script

echo "Starting cleanup..."

# 1. Delete generated folders/files
echo "Removing node_modules..."
rm -rf node_modules

echo "Removing local.db..."
rm -f local.db

echo "Removing Python caches..."
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

# 2. Stash secrets
echo "Stashing secrets..."
mkdir -p _secrets_stash
if [ -f .env ]; then
    echo "Moving .env to _secrets_stash/"
    mv .env _secrets_stash/
fi
if [ -f google_creds.json ]; then
    echo "Moving google_creds.json to _secrets_stash/"
    mv google_creds.json _secrets_stash/
fi

echo "Cleanup complete. Secrets moved to _secrets_stash/ (ensure this is ignored)."
