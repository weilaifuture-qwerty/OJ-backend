#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting OnlineJudge Backend...${NC}"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}Docker is not running. Please start Docker first.${NC}"
    exit 1
fi

# Check if PostgreSQL container is running
if ! docker ps | grep -q oj-postgres-dev; then
    echo -e "${YELLOW}Starting PostgreSQL container...${NC}"
    docker start oj-postgres-dev > /dev/null 2>&1
    if [ $? -ne 0 ]; then
        echo -e "${YELLOW}PostgreSQL container not found. Creating new container...${NC}"
        docker run -d -e POSTGRES_DB=onlinejudge -e POSTGRES_USER=onlinejudge -e POSTGRES_PASSWORD=onlinejudge -p 127.0.0.1:5435:5432 --name oj-postgres-dev postgres:10
    fi
    sleep 3
else
    echo -e "${GREEN}PostgreSQL container is already running${NC}"
fi

# Check if Redis container is running
if ! docker ps | grep -q oj-redis-dev; then
    echo -e "${YELLOW}Starting Redis container...${NC}"
    docker start oj-redis-dev > /dev/null 2>&1
    if [ $? -ne 0 ]; then
        echo -e "${YELLOW}Redis container not found. Creating new container...${NC}"
        docker run -d -p 127.0.0.1:6380:6379 --name oj-redis-dev redis:4.0-alpine
    fi
    sleep 2
else
    echo -e "${GREEN}Redis container is already running${NC}"
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Virtual environment not found. Creating...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Check if secret key exists
if [ ! -f "data/config/secret.key" ]; then
    echo -e "${YELLOW}Secret key not found. Creating...${NC}"
    mkdir -p data/config
    echo $(cat /dev/urandom | head -1 | md5sum | head -c 32) > data/config/secret.key
fi

# Install/upgrade dependencies if needed
echo -e "${YELLOW}Checking dependencies...${NC}"
pip install -q --upgrade pip
pip install -q -r requirements.txt 2>/dev/null || {
    echo -e "${YELLOW}Installing additional dependencies...${NC}"
    pip install -q setuptools
    pip install -q django-dramatiq==0.11.6 django-redis==5.4.0 Django==3.2.25 dramatiq==1.16.0 redis
    pip install -q raven django-dbconn-retry envelopes jsonfield
    pip install -q qrcode[pil] otpauth xlsxwriter python-dateutil pillow django-cas-ng
}

# Run migrations
echo -e "${YELLOW}Checking database migrations...${NC}"
python manage.py migrate --noinput

# Start the development server
echo -e "${GREEN}Starting Django development server...${NC}"
echo -e "${GREEN}Server will be available at: http://localhost:8000${NC}"
echo -e "${GREEN}API endpoints: http://localhost:8000/api/${NC}"
echo -e "${GREEN}Admin credentials - Username: root, Password: rootroot${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"
echo ""

# Run the server
python manage.py runserver