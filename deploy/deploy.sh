#!/bin/bash
# ==========================================================
# ONE-CLICK DEPLOYMENT SCRIPT FOR AMAZON LINUX (2023 / 2)
# Target: Amazon EC2 (ec2-user) in eu-north-1
# ==========================================================

set -e

echo "=== [1/6] Installing packages with dnf/yum ==="
if command -v dnf &> /dev/null; then
    sudo dnf update -y
    sudo dnf install -y python3.11 python3.11-pip python3.11-devel nginx gcc || sudo dnf install -y python3 python3-pip python3-devel nginx gcc
else
    sudo yum update -y
    sudo yum install -y python3.11 python3.11-pip python3.11-devel nginx gcc || sudo yum install -y python3 python3-pip python3-devel nginx gcc
fi

PROJECT_DIR="/home/ec2-user/AssignmentManagementSystem"
cd "$PROJECT_DIR"

# Ensure .env exists
if [ ! -f .env ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
    sed -i 's/ALLOWED_HOSTS=.*/ALLOWED_HOSTS=*/' .env
fi

echo "=== [2/6] Setting up Python virtual environment ==="
rm -rf venv
if command -v python3.11 &> /dev/null; then
    python3.11 -m venv venv
else
    python3 -m venv venv
fi
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "=== [3/6] Running database migrations ==="
python manage.py migrate

echo "=== [4/6] Collecting static files ==="
python manage.py collectstatic --noinput

echo "=== [5/6] Configuring Gunicorn systemd service ==="
sudo cp deploy/gunicorn.service /etc/systemd/system/gunicorn.service
sudo systemctl daemon-reload
sudo systemctl restart gunicorn
sudo systemctl enable gunicorn

echo "=== [6/6] Configuring Nginx reverse proxy ==="
sudo mkdir -p /etc/nginx/conf.d/
sudo cp deploy/nginx_assignment.conf /etc/nginx/conf.d/assignment.conf

# Give nginx access to static files and socket in home directory
sudo chmod 755 /home/ec2-user
sudo usermod -a -G ec2-user nginx || true
sudo systemctl restart nginx
sudo systemctl enable nginx

echo "=========================================================="
echo "DEPLOYMENT COMPLETE!"
echo "Your Assignment Management System is now live on port 80."
echo "=========================================================="
