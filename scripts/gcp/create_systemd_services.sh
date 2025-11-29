#!/bin/bash
# Create systemd services for Flask app and Cloud SQL Proxy
# This allows the app to run continuously even when PC is turned off

set -e

echo "=========================================="
echo "Creating systemd services"
echo "=========================================="

# Get current user
CURRENT_USER=$(whoami)
HOME_DIR=$(eval echo ~$CURRENT_USER)
APP_DIR="$HOME_DIR/MyPoly-LawData"

# Check if app directory exists
if [ ! -d "$APP_DIR" ]; then
    echo "Error: $APP_DIR does not exist"
    exit 1
fi

# Get Cloud SQL connection name from environment or prompt
CONNECTION_NAME="${CLOUD_SQL_CONNECTION_NAME:-}"
if [ -z "$CONNECTION_NAME" ]; then
    echo ""
    echo "Enter Cloud SQL connection name:"
    echo "Example: fiery-bedrock-479615-u2:asia-northeast3:mypoly-postgres"
    read -p "Connection name: " CONNECTION_NAME
fi

if [ -z "$CONNECTION_NAME" ]; then
    echo "Error: Cloud SQL connection name is required"
    exit 1
fi

echo ""
echo "Creating Cloud SQL Proxy service..."

# Create Cloud SQL Proxy systemd service
sudo tee /etc/systemd/system/cloud-sql-proxy.service > /dev/null <<EOF
[Unit]
Description=Cloud SQL Proxy
After=network.target

[Service]
Type=simple
User=$CURRENT_USER
ExecStart=/usr/local/bin/cloud_sql_proxy -instances=$CONNECTION_NAME=tcp:5432
Restart=always
RestartSec=5
StandardOutput=append:/var/log/cloud-sql-proxy.log
StandardError=append:/var/log/cloud-sql-proxy.log

[Install]
WantedBy=multi-user.target
EOF

echo "Creating Flask app service..."

# Load environment variables from .env file
ENV_FILE="$APP_DIR/.env"
ENV_VARS=""
if [ -f "$ENV_FILE" ]; then
    # Convert .env to systemd Environment format
    while IFS='=' read -r key value || [ -n "$key" ]; do
        # Skip comments and empty lines
        [[ "$key" =~ ^#.*$ ]] && continue
        [[ -z "$key" ]] && continue
        
        # Remove quotes from value if present
        value=$(echo "$value" | sed 's/^"//;s/"$//')
        
        # Add to ENV_VARS
        ENV_VARS="${ENV_VARS}Environment=\"${key}=${value}\"\n"
    done < "$ENV_FILE"
else
    echo "Warning: .env file not found at $ENV_FILE"
    echo "Creating service without environment variables"
fi

# Create Flask app systemd service
sudo tee /etc/systemd/system/mypoly-app.service > /dev/null <<EOF
[Unit]
Description=MyPoly LawData Flask App
After=network.target cloud-sql-proxy.service
Requires=cloud-sql-proxy.service

[Service]
Type=simple
User=$CURRENT_USER
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin"
$(echo -e "$ENV_VARS")
ExecStart=$APP_DIR/venv/bin/python $APP_DIR/app.py
Restart=always
RestartSec=10
StandardOutput=append:/var/log/mypoly-app.log
StandardError=append:/var/log/mypoly-app.log

[Install]
WantedBy=multi-user.target
EOF

echo ""
echo "Reloading systemd daemon..."
sudo systemctl daemon-reload

echo ""
echo "Enabling services to start on boot..."
sudo systemctl enable cloud-sql-proxy.service
sudo systemctl enable mypoly-app.service

echo ""
echo "=========================================="
echo "Services created successfully!"
echo "=========================================="
echo ""
echo "To start services now:"
echo "  sudo systemctl start cloud-sql-proxy"
echo "  sudo systemctl start mypoly-app"
echo ""
echo "To check status:"
echo "  sudo systemctl status cloud-sql-proxy"
echo "  sudo systemctl status mypoly-app"
echo ""
echo "To view logs:"
echo "  sudo journalctl -u cloud-sql-proxy -f"
echo "  sudo journalctl -u mypoly-app -f"
echo ""
echo "To stop services:"
echo "  sudo systemctl stop mypoly-app"
echo "  sudo systemctl stop cloud-sql-proxy"
echo ""

