#!/bin/bash
# Manage systemd services for Flask app and Cloud SQL Proxy

set -e

ACTION="${1:-status}"

case "$ACTION" in
    start)
        echo "Starting services..."
        sudo systemctl start cloud-sql-proxy
        sleep 3
        sudo systemctl start mypoly-app
        echo "Services started"
        ;;
    stop)
        echo "Stopping services..."
        sudo systemctl stop mypoly-app
        sudo systemctl stop cloud-sql-proxy
        echo "Services stopped"
        ;;
    restart)
        echo "Restarting services..."
        sudo systemctl restart cloud-sql-proxy
        sleep 3
        sudo systemctl restart mypoly-app
        echo "Services restarted"
        ;;
    status)
        echo "=========================================="
        echo "Service Status"
        echo "=========================================="
        echo ""
        echo "Cloud SQL Proxy:"
        sudo systemctl status cloud-sql-proxy --no-pager -l
        echo ""
        echo "Flask App:"
        sudo systemctl status mypoly-app --no-pager -l
        ;;
    logs)
        SERVICE="${2:-mypoly-app}"
        echo "Showing logs for $SERVICE (Ctrl+C to exit)..."
        sudo journalctl -u "$SERVICE" -f
        ;;
    enable)
        echo "Enabling services to start on boot..."
        sudo systemctl enable cloud-sql-proxy
        sudo systemctl enable mypoly-app
        echo "Services enabled"
        ;;
    disable)
        echo "Disabling services from starting on boot..."
        sudo systemctl disable mypoly-app
        sudo systemctl disable cloud-sql-proxy
        echo "Services disabled"
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs [service]|enable|disable}"
        echo ""
        echo "Commands:"
        echo "  start    - Start both services"
        echo "  stop     - Stop both services"
        echo "  restart  - Restart both services"
        echo "  status   - Show status of both services"
        echo "  logs     - Show logs (default: mypoly-app, use 'cloud-sql-proxy' for proxy)"
        echo "  enable   - Enable services to start on boot"
        echo "  disable  - Disable services from starting on boot"
        exit 1
        ;;
esac

