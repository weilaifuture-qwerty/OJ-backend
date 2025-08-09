# Online Judge Deployment Guide for Alibaba Cloud

This guide will help you deploy the Online Judge system on an Alibaba Cloud ECS instance.

## Prerequisites

- Alibaba Cloud ECS instance (recommended: 4 vCPU, 8GB RAM minimum)
- Ubuntu 20.04 or 22.04 LTS
- Domain name (optional but recommended)
- SSH access to your server

## Step 1: Prepare Your Alibaba Cloud ECS Instance

### 1.1 Create ECS Instance
1. Log in to Alibaba Cloud Console
2. Create an ECS instance with:
   - Ubuntu 20.04/22.04 LTS
   - At least 4 vCPU and 8GB RAM
   - 100GB SSD storage
   - Public IP address

### 1.2 Configure Security Group
Add the following inbound rules:
- Port 22 (SSH)
- Port 80 (HTTP)
- Port 443 (HTTPS)

### 1.3 Connect to Your Server
```bash
ssh root@your-server-ip
```

## Step 2: Upload Project Files

### Option A: Using Git (Recommended)
```bash
# Install git
apt-get update && apt-get install -y git

# Create project directory
mkdir -p /root/OJ
cd /root/OJ

# Clone both repositories
git clone https://github.com/weilaifuture-qwerty/OJ-backend.git
git clone https://github.com/weilaifuture-qwerty/OJ-frontend.git

# Navigate to backend directory
cd OJ-backend
```

### Option B: Using SCP
From your local machine:
```bash
# Compress the projects
tar -czf oj-deploy.tar.gz OJ-backend/ OJ-frontend/

# Upload to server
scp oj-deploy.tar.gz root@your-server-ip:/root/

# On the server, extract files
ssh root@your-server-ip
cd /root
tar -xzf oj-deploy.tar.gz
mv OJ-backend OJ-frontend /root/OJ/
cd /root/OJ/OJ-backend
```

## Step 3: Configure Environment Variables

```bash
# Copy environment template
cp .env.example .env

# Edit environment variables
nano .env
```

Required configurations:
- `DB_PASSWORD`: Set a strong database password
- `REDIS_PASSWORD`: Set a strong Redis password
- `SECRET_KEY`: Generate a random secret key (use `openssl rand -hex 32`)
- `ALLOWED_HOSTS`: Set your domain name or server IP
- `JUDGE_SERVER_TOKEN`: Generate a secure token for judge server

## Step 4: Run Deployment Script

```bash
# Make script executable
chmod +x deploy.sh

# Run deployment
./deploy.sh
```

## Step 5: Configure Domain Name (Optional)

### 5.1 Point Domain to Server
In your domain registrar's DNS settings:
- Add an A record pointing to your server's IP address

### 5.2 Update Nginx Configuration
```bash
# Edit nginx configuration
nano nginx/sites-enabled/oj.conf

# Replace 'your-domain.com' with your actual domain
# Restart nginx
docker-compose restart nginx
```

## Step 6: Set Up SSL Certificate (Recommended)

### Using Let's Encrypt
```bash
# Install Certbot
apt-get install -y certbot

# Stop nginx temporarily
docker-compose stop nginx

# Get certificate
certbot certonly --standalone -d your-domain.com -d www.your-domain.com

# Copy certificates to project
cp /etc/letsencrypt/live/your-domain.com/fullchain.pem ssl/cert.pem
cp /etc/letsencrypt/live/your-domain.com/privkey.pem ssl/key.pem

# Update nginx configuration (uncomment HTTPS section)
nano nginx/sites-enabled/oj.conf

# Start nginx
docker-compose up -d nginx
```

## Step 7: Create Admin User

```bash
# Create superuser
docker-compose exec backend python manage.py createsuperuser

# Follow the prompts to create admin account
```

## Step 8: Initial Configuration

1. Access admin panel at `http://your-domain.com/admin`
2. Log in with your superuser credentials
3. Configure:
   - Website settings
   - Judge server settings
   - Email settings (if needed)

## Maintenance Commands

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f judge_server
```

### Restart Services
```bash
# All services
docker-compose restart

# Specific service
docker-compose restart backend
```

### Stop Services
```bash
docker-compose down
```

### Backup Database
```bash
# Create backup
docker-compose exec postgres pg_dump -U ojuser onlinejudge > backup_$(date +%Y%m%d).sql

# Restore backup
docker-compose exec -T postgres psql -U ojuser onlinejudge < backup_20240101.sql
```

### Update Code
```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose build
docker-compose up -d

# Run migrations if needed
docker-compose exec backend python manage.py migrate
```

## Monitoring

### Check Service Status
```bash
docker-compose ps
```

### Monitor Resource Usage
```bash
docker stats
```

### Check Disk Usage
```bash
df -h
docker system df
```

## Troubleshooting

### Services Not Starting
```bash
# Check logs
docker-compose logs [service-name]

# Check Docker status
systemctl status docker
```

### Database Connection Issues
```bash
# Test database connection
docker-compose exec backend python manage.py dbshell
```

### Judge Server Issues
```bash
# Check judge server logs
docker-compose logs judge_server

# Verify token configuration
docker-compose exec backend python manage.py shell
>>> from conf.models import JudgeServer
>>> JudgeServer.objects.all()
```

### Performance Issues
- Increase server resources (CPU/RAM)
- Enable swap if needed:
```bash
fallocate -l 4G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
echo '/swapfile none swap sw 0 0' >> /etc/fstab
```

## Security Recommendations

1. **Regular Updates**
   ```bash
   apt-get update && apt-get upgrade -y
   docker-compose pull
   ```

2. **Firewall Configuration**
   ```bash
   ufw allow 22/tcp
   ufw allow 80/tcp
   ufw allow 443/tcp
   ufw enable
   ```

3. **Backup Strategy**
   - Set up automated daily database backups
   - Use Alibaba Cloud OSS for backup storage
   - Test restore procedures regularly

4. **Monitoring**
   - Set up Alibaba Cloud monitoring alerts
   - Monitor disk space, CPU, and memory usage
   - Set up log rotation

## Support

If you encounter issues:
1. Check the logs: `docker-compose logs -f`
2. Review this guide's troubleshooting section
3. Check system resources: `htop`, `df -h`
4. Ensure all environment variables are properly configured

## Next Steps

After successful deployment:
1. Test all functionalities (user registration, problem submission, judging)
2. Configure email settings for notifications
3. Set up monitoring and alerts
4. Create regular backup schedule
5. Document any custom configurations