#!/usr/bin/env bash
# Bootstrap the Employee Management API on a fresh Ubuntu EC2 instance.
# Run from the repo root after cloning:
#   bash deploy/bootstrap.sh
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
echo ">>> App directory: $APP_DIR"

echo ">>> Installing system packages (python venv, nginx, git)..."
sudo apt-get update -y
sudo apt-get install -y python3-venv python3-pip nginx git

echo ">>> Creating Python virtual environment and installing dependencies..."
cd "$APP_DIR"
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt

echo ">>> Installing systemd service..."
sudo cp deploy/employee-api.service /etc/systemd/system/employee-api.service
sudo systemctl daemon-reload
sudo systemctl enable employee-api

echo ">>> Configuring nginx reverse proxy..."
sudo cp deploy/nginx-employee-api.conf /etc/nginx/sites-available/employee-api
sudo ln -sf /etc/nginx/sites-available/employee-api /etc/nginx/sites-enabled/employee-api
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t

echo ""
echo ">>> Bootstrap complete. Remaining steps:"
echo "    1. Create the env file:  sudo nano /etc/employee-api.env"
echo "       (use deploy/.env.production.example as the template)"
echo "    2. Start the API:        sudo systemctl start employee-api"
echo "    3. Reload nginx:         sudo systemctl restart nginx"
echo "    4. Check it's healthy:   curl http://localhost/health"
