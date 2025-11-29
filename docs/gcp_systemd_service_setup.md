# GCP VM Systemd Service Setup Guide

This guide explains how to set up systemd services so that the Flask app and Cloud SQL Proxy run continuously on the VM, even when your PC is turned off.

## Overview

By creating systemd services, the Flask app and Cloud SQL Proxy will:
- Start automatically when the VM boots
- Restart automatically if they crash
- Continue running even when you disconnect from SSH
- Run in the background without requiring a terminal session

## Prerequisites

- VM is set up and running
- Flask app directory exists at `~/MyPoly-LawData`
- `.env` file is configured
- Cloud SQL Proxy is installed at `/usr/local/bin/cloud_sql_proxy`

## Setup Steps

### 1. Create Systemd Services

SSH into your VM and run:

```bash
cd ~/MyPoly-LawData
chmod +x scripts/gcp/create_systemd_services.sh
./scripts/gcp/create_systemd_services.sh
```

You will be prompted to enter your Cloud SQL connection name (e.g., `fiery-bedrock-479615-u2:asia-northeast3:mypoly-postgres`).

Alternatively, set it as an environment variable:

```bash
export CLOUD_SQL_CONNECTION_NAME="fiery-bedrock-479615-u2:asia-northeast3:mypoly-postgres"
./scripts/gcp/create_systemd_services.sh
```

### 2. Start the Services

```bash
chmod +x scripts/gcp/manage_services.sh
./scripts/gcp/manage_services.sh start
```

### 3. Verify Services are Running

```bash
./scripts/gcp/manage_services.sh status
```

You should see both services as "active (running)".

### 4. Enable Auto-Start on Boot

The services are automatically enabled to start on boot when created. To verify:

```bash
./scripts/gcp/manage_services.sh enable
```

## Managing Services

Use the `manage_services.sh` script to control the services:

```bash
# Start services
./scripts/gcp/manage_services.sh start

# Stop services
./scripts/gcp/manage_services.sh stop

# Restart services
./scripts/gcp/manage_services.sh restart

# Check status
./scripts/gcp/manage_services.sh status

# View logs (Flask app)
./scripts/gcp/manage_services.sh logs mypoly-app

# View logs (Cloud SQL Proxy)
./scripts/gcp/manage_services.sh logs cloud-sql-proxy

# Disable auto-start on boot
./scripts/gcp/manage_services.sh disable
```

## Alternative: Manual systemctl Commands

You can also use `systemctl` directly:

```bash
# Start services
sudo systemctl start cloud-sql-proxy
sudo systemctl start mypoly-app

# Stop services
sudo systemctl stop mypoly-app
sudo systemctl stop cloud-sql-proxy

# Restart services
sudo systemctl restart cloud-sql-proxy
sudo systemctl restart mypoly-app

# Check status
sudo systemctl status cloud-sql-proxy
sudo systemctl status mypoly-app

# View logs
sudo journalctl -u mypoly-app -f
sudo journalctl -u cloud-sql-proxy -f

# Enable/disable auto-start
sudo systemctl enable cloud-sql-proxy
sudo systemctl enable mypoly-app
sudo systemctl disable mypoly-app
sudo systemctl disable cloud-sql-proxy
```

## Troubleshooting

### Service fails to start

1. Check service status:
   ```bash
   sudo systemctl status mypoly-app
   ```

2. View detailed logs:
   ```bash
   sudo journalctl -u mypoly-app -n 50
   ```

3. Common issues:
   - `.env` file missing or incorrect
   - Cloud SQL Proxy not running
   - Database connection issues
   - Port 5000 already in use

### Cloud SQL Proxy connection issues

1. Check Cloud SQL Proxy logs:
   ```bash
   sudo journalctl -u cloud-sql-proxy -f
   ```

2. Verify connection name is correct
3. Check GCP IAM permissions
4. Ensure Cloud SQL Admin API is enabled

### App not accessible

1. Check if app is running:
   ```bash
   sudo systemctl status mypoly-app
   ```

2. Check firewall rules:
   ```bash
   # On GCP Console, verify firewall rule allows TCP:5000
   ```

3. Verify app is listening on port 5000:
   ```bash
   sudo netstat -tlnp | grep 5000
   ```

## Service Files Location

The systemd service files are created at:
- `/etc/systemd/system/cloud-sql-proxy.service`
- `/etc/systemd/system/mypoly-app.service`

Log files:
- `/var/log/cloud-sql-proxy.log`
- `/var/log/mypoly-app.log`

## Notes

- Services will automatically restart if they crash (RestartSec=10 for app, RestartSec=5 for proxy)
- The Flask app depends on Cloud SQL Proxy, so it will wait for the proxy to start
- Environment variables from `.env` are automatically loaded into the service
- You can disconnect from SSH and the services will continue running

