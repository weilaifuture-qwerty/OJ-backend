#!/bin/bash

# Online Judge Deployment Script for Alibaba Cloud ECS
# This script deploys the OJ system using Docker Compose

set -e

echo "========================================="
echo "Online Judge Deployment Script"
echo "========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   print_error "This script must be run as root"
   exit 1
fi

# Update system packages
echo "Updating system packages..."
apt-get update && apt-get upgrade -y
print_success "System packages updated"

# Install Docker if not installed
if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    systemctl enable docker
    systemctl start docker
    print_success "Docker installed"
else
    print_success "Docker is already installed"
fi

# Install Docker Compose if not installed
if ! command -v docker-compose &> /dev/null; then
    echo "Installing Docker Compose..."
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    print_success "Docker Compose installed"
else
    print_success "Docker Compose is already installed"
fi

# Check if .env file exists
if [ ! -f .env ]; then
    print_error ".env file not found!"
    print_warning "Please copy .env.example to .env and configure it:"
    echo "  cp .env.example .env"
    echo "  nano .env"
    exit 1
fi

# Create necessary directories
echo "Creating necessary directories..."
mkdir -p ssl
mkdir -p OnlineJudge/logs
mkdir -p OnlineJudge/test_cases
mkdir -p OnlineJudge/media
print_success "Directories created"

# Pull latest code (optional, comment out if not using git)
# echo "Pulling latest code from repository..."
# git pull origin main
# print_success "Code updated"

# Build and start services
echo "Building Docker images..."
docker-compose build --no-cache
print_success "Docker images built"

echo "Starting services..."
docker-compose up -d
print_success "Services started"

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 10

# Check service status
echo "Checking service status..."
docker-compose ps

# Run database migrations
echo "Running database migrations..."
docker-compose exec -T backend python manage.py migrate
print_success "Database migrations completed"

# Collect static files
echo "Collecting static files..."
docker-compose exec -T backend python manage.py collectstatic --noinput
print_success "Static files collected"

# Create superuser (optional, uncomment if needed)
# echo "Creating superuser..."
# docker-compose exec -T backend python manage.py createsuperuser

# Display status
echo ""
echo "========================================="
echo "Deployment Complete!"
echo "========================================="
echo ""
echo "Services Status:"
docker-compose ps
echo ""
echo "Access the application at:"
echo "  http://your-server-ip"
echo ""
echo "Useful commands:"
echo "  View logs:        docker-compose logs -f [service-name]"
echo "  Stop services:    docker-compose down"
echo "  Restart services: docker-compose restart"
echo "  Enter backend:    docker-compose exec backend bash"
echo ""
print_warning "Remember to:"
echo "  1. Configure your domain name in nginx configuration"
echo "  2. Set up SSL certificates for HTTPS"
echo "  3. Configure firewall rules (ports 80, 443)"
echo "  4. Set up backup strategies for database and files"