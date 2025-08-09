#!/bin/bash

# SSL Setup Script for www.fufu.academy
# This script sets up Let's Encrypt SSL certificates

set -e

DOMAIN="www.fufu.academy"
ALT_DOMAIN="fufu.academy"
EMAIL="admin@fufu.academy"  # Change this to your email

echo "========================================="
echo "Setting up SSL for $DOMAIN"
echo "========================================="

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Install Certbot if not installed
if ! command -v certbot &> /dev/null; then
    echo "Installing Certbot..."
    apt-get update
    apt-get install -y certbot
    print_success "Certbot installed"
else
    print_success "Certbot is already installed"
fi

# Stop nginx temporarily to get certificates
echo "Stopping nginx container..."
docker-compose stop nginx

# Get SSL certificates
echo "Obtaining SSL certificates..."
certbot certonly --standalone \
    -d $DOMAIN \
    -d $ALT_DOMAIN \
    --non-interactive \
    --agree-tos \
    --email $EMAIL \
    --expand

if [ $? -eq 0 ]; then
    print_success "SSL certificates obtained successfully"
else
    print_error "Failed to obtain SSL certificates"
    exit 1
fi

# Create SSL directory if it doesn't exist
mkdir -p ssl

# Copy certificates to project directory
echo "Copying certificates..."
cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem ssl/cert.pem
cp /etc/letsencrypt/live/$DOMAIN/privkey.pem ssl/key.pem
chmod 644 ssl/cert.pem
chmod 600 ssl/key.pem
print_success "Certificates copied to ssl directory"

# Update nginx configuration to enable HTTPS
echo "Updating nginx configuration..."
sed -i 's|# return 301|return 301|' nginx/sites-enabled/oj.conf
sed -i 's|# server {|server {|' nginx/sites-enabled/oj.conf
sed -i 's|#     listen 443|    listen 443|' nginx/sites-enabled/oj.conf
sed -i 's|#     server_name|    server_name|' nginx/sites-enabled/oj.conf
sed -i 's|#     ssl_|    ssl_|' nginx/sites-enabled/oj.conf
sed -i 's|#     add_header|    add_header|' nginx/sites-enabled/oj.conf
sed -i 's|#     location|    location|' nginx/sites-enabled/oj.conf
sed -i 's|#         |        |g' nginx/sites-enabled/oj.conf
sed -i 's|#     }|    }|' nginx/sites-enabled/oj.conf
sed -i 's|# }|}|' nginx/sites-enabled/oj.conf

print_success "Nginx configuration updated for HTTPS"

# Start nginx with SSL
echo "Starting nginx with SSL..."
docker-compose up -d nginx
print_success "Nginx started with SSL"

# Set up auto-renewal
echo "Setting up auto-renewal..."
(crontab -l 2>/dev/null; echo "0 3 * * * certbot renew --quiet --post-hook 'cd /root/OJ/OJ-backend && cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem ssl/cert.pem && cp /etc/letsencrypt/live/$DOMAIN/privkey.pem ssl/key.pem && docker-compose restart nginx'") | crontab -
print_success "Auto-renewal configured"

echo ""
echo "========================================="
echo "SSL Setup Complete!"
echo "========================================="
echo ""
echo "Your site is now accessible at:"
echo "  https://www.fufu.academy"
echo "  https://fufu.academy"
echo ""
echo "HTTP traffic will be automatically redirected to HTTPS"
echo "Certificates will auto-renew every 60 days"