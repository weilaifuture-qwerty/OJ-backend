#!/bin/bash

# Update and Deploy Script for OJ System
# This script safely updates both repositories and deploys

set -e

echo "========================================="
echo "OnlineJudge Update and Deploy"
echo "========================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Update Backend
echo ""
echo "Updating Backend..."
cd /root/OJ/OJ-backend

# Check for local changes
if [[ -n $(git status -s) ]]; then
    print_warning "Local changes detected in backend"
    echo "Stashing local changes..."
    git stash
    BACKEND_STASHED=true
fi

git pull origin main
print_success "Backend updated"

if [[ $BACKEND_STASHED == true ]]; then
    print_warning "You had local changes that were stashed. Review with: git stash list"
fi

# Update Frontend
echo ""
echo "Updating Frontend..."
cd /root/OJ/OJ-frontend

# Check for local changes
if [[ -n $(git status -s) ]]; then
    print_warning "Local changes detected in frontend"
    echo "Stashing local changes..."
    git stash
    FRONTEND_STASHED=true
fi

git pull origin main
print_success "Frontend updated"

if [[ $FRONTEND_STASHED == true ]]; then
    print_warning "You had local changes that were stashed. Review with: git stash list"
fi

# Return to backend directory for deployment
cd /root/OJ/OJ-backend

# Build and deploy
echo ""
echo "Building and deploying..."
echo ""

# Stop existing containers
docker-compose down

# Build images
echo "Building Docker images..."
docker-compose build --no-cache

# Start services
echo "Starting services..."
docker-compose up -d

# Wait for services to be ready
echo "Waiting for services to initialize..."
sleep 10

# Run migrations
echo "Running database migrations..."
docker-compose exec -T backend python manage.py migrate

# Collect static files
echo "Collecting static files..."
docker-compose exec -T backend python manage.py collectstatic --noinput

# Show status
echo ""
echo "========================================="
echo "Deployment Status"
echo "========================================="
docker-compose ps

echo ""
print_success "Update and deployment complete!"
echo ""
echo "Your application should be accessible at:"
echo "  http://www.fufu.academy"
echo ""
echo "To set up SSL, run: ./setup-ssl.sh"
echo ""

if [[ $BACKEND_STASHED == true ]] || [[ $FRONTEND_STASHED == true ]]; then
    echo "========================================="
    print_warning "Note: You had local changes that were stashed"
    echo "To view stashed changes:"
    if [[ $BACKEND_STASHED == true ]]; then
        echo "  Backend: cd /root/OJ/OJ-backend && git stash list"
    fi
    if [[ $FRONTEND_STASHED == true ]]; then
        echo "  Frontend: cd /root/OJ/OJ-frontend && git stash list"
    fi
    echo "To restore stashed changes: git stash pop"
fi