#!/bin/bash
# Fix Git divergent branches and setup systemd services

set -e

echo "=========================================="
echo "Fixing Git and Setting Up Services"
echo "=========================================="

cd ~/MyPoly-LawData

# Fix divergent branches by resetting to origin
echo "[1/4] Fixing Git branches..."
git fetch origin
git reset --hard origin/main

# Pull latest changes
echo "[2/4] Pulling latest changes..."
git pull origin main

# Make scripts executable
echo "[3/4] Making scripts executable..."
chmod +x scripts/gcp/*.sh

# Check if scripts exist
if [ ! -f "scripts/gcp/create_systemd_services.sh" ]; then
    echo "Error: create_systemd_services.sh not found"
    exit 1
fi

if [ ! -f "scripts/gcp/manage_services.sh" ]; then
    echo "Error: manage_services.sh not found"
    exit 1
fi

# Get Cloud SQL connection name
CONNECTION_NAME="${CLOUD_SQL_CONNECTION_NAME:-}"
if [ -z "$CONNECTION_NAME" ]; then
    echo ""
    echo "[4/4] Enter Cloud SQL connection name:"
    echo "Example: fiery-bedrock-479615-u2:asia-northeast3:mypoly-postgres"
    read -p "Connection name: " CONNECTION_NAME
    export CLOUD_SQL_CONNECTION_NAME="$CONNECTION_NAME"
fi

if [ -z "$CONNECTION_NAME" ]; then
    echo "Error: Cloud SQL connection name is required"
    exit 1
fi

echo ""
echo "Creating systemd services..."
./scripts/gcp/create_systemd_services.sh

echo ""
echo "Starting services..."
./scripts/gcp/manage_services.sh start

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Check status:"
echo "  ./scripts/gcp/manage_services.sh status"
echo ""

