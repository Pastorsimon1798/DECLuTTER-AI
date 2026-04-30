# MutualCircle Deployment Guide 🚀

Complete guide for deploying MutualCircle to production.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Database Setup](#database-setup)
4. [Backend Deployment](#backend-deployment)
5. [Frontend Deployment](#frontend-deployment)
6. [Celery & Redis Setup](#celery--redis-setup)
7. [Production Checklist](#production-checklist)
8. [Monitoring & Maintenance](#monitoring--maintenance)

---

## Prerequisites

### Required Software

- **Python:** 3.11 or higher
- **Node.js:** 18.x or higher
- **PostgreSQL:** 16.x with PostGIS extension
- **Redis:** 7.x (for Celery task queue)
- **Nginx:** Latest stable (for reverse proxy)
- **Certbot:** For SSL certificates (Let's Encrypt)

### Optional

- **Docker:** 24.x (for containerized deployment)
- **Git:** For version control
- **Supervisor:** For process management

---

## Environment Setup

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/mutualcircle.git
cd mutualcircle
```

### 2. Backend Environment

Create `.env` file in `backend/` directory:

```bash
cp backend/.env.example backend/.env
```

Edit `backend/.env` with your values:

```env
# Database
DATABASE_URL=postgresql://username:password@localhost:5432/mutualcircle_prod
TEST_DATABASE_URL=postgresql://username:password@localhost:5432/mutualcircle_test

# Security
SECRET_KEY=your-very-long-secret-key-change-this-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS
CORS_ORIGINS=https://mutualcircle.org,https://www.mutualcircle.org

# Celery & Redis
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Email (for notifications)
SMTP_SERVER=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USERNAME=apikey
SMTP_PASSWORD=your-sendgrid-api-key
FROM_EMAIL=noreply@mutualcircle.org
FROM_NAME=MutualCircle

# SMS (Twilio - for shift reminders and SOS)
TWILIO_ACCOUNT_SID=your-account-sid
TWILIO_AUTH_TOKEN=your-auth-token
TWILIO_PHONE_NUMBER=+1234567890

# 211 API (for resource listings)
TWO_ONE_ONE_API_KEY=your-211-api-key

# Environment
ENVIRONMENT=production
API_V1_PREFIX=/api/v1

# Sentry (Error Tracking - Optional)
SENTRY_DSN=https://your-sentry-dsn
```

### 3. Frontend Environment

Create `.env.production` file in `frontend/` directory:

```bash
cp frontend/.env.example frontend/.env.production
```

Edit `frontend/.env.production`:

```env
VITE_API_URL=https://api.mutualcircle.org
VITE_ENVIRONMENT=production
VITE_SENTRY_DSN=https://your-sentry-dsn
VITE_GOOGLE_MAPS_API_KEY=your-google-maps-key
```

---

## Database Setup

### 1. Install PostgreSQL with PostGIS

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install postgresql-16 postgresql-16-postgis-3

# macOS (Homebrew)
brew install postgresql@16 postgis

# Start PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### 2. Create Database

```bash
sudo -u postgres psql

CREATE DATABASE mutualcircle_prod;
CREATE USER mutualcircle WITH PASSWORD 'your-secure-password';
GRANT ALL PRIVILEGES ON DATABASE mutualcircle_prod TO mutualcircle;

# Enable PostGIS extension
\c mutualcircle_prod
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

\q
```

### 3. Run Migrations

```bash
cd backend

# Install dependencies
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run migrations
alembic upgrade head
```

---

## Backend Deployment

### Option 1: Uvicorn with Supervisor (Recommended)

#### 1. Install Backend Dependencies

```bash
cd backend
pip install -r requirements.txt
```

#### 2. Create Supervisor Config

Create `/etc/supervisor/conf.d/mutualcircle-api.conf`:

```ini
[program:mutualcircle-api]
directory=/home/deploy/mutualcircle/backend
command=/home/deploy/mutualcircle/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
user=deploy
autostart=true
autorestart=true
stderr_logfile=/var/log/mutualcircle/api.err.log
stdout_logfile=/var/log/mutualcircle/api.out.log
environment=PYTHONPATH="/home/deploy/mutualcircle/backend"
```

#### 3. Start Service

```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start mutualcircle-api
```

### Option 2: Docker

Create `docker-compose.yml` in project root:

```yaml
version: '3.8'

services:
  db:
    image: postgis/postgis:16-3.4
    environment:
      POSTGRES_DB: mutualcircle_prod
      POSTGRES_USER: mutualcircle
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  backend:
    build: ./backend
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
    volumes:
      - ./backend:/app
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://mutualcircle:${DB_PASSWORD}@db:5432/mutualcircle_prod
      CELERY_BROKER_URL: redis://redis:6379/0
    depends_on:
      - db
      - redis

  celery_worker:
    build: ./backend
    command: celery -A app.celery_app worker --loglevel=info
    volumes:
      - ./backend:/app
    environment:
      DATABASE_URL: postgresql://mutualcircle:${DB_PASSWORD}@db:5432/mutualcircle_prod
      CELERY_BROKER_URL: redis://redis:6379/0
    depends_on:
      - db
      - redis

  celery_beat:
    build: ./backend
    command: celery -A app.celery_app beat --loglevel=info
    volumes:
      - ./backend:/app
    environment:
      DATABASE_URL: postgresql://mutualcircle:${DB_PASSWORD}@db:5432/mutualcircle_prod
      CELERY_BROKER_URL: redis://redis:6379/0
    depends_on:
      - db
      - redis

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      VITE_API_URL: https://api.mutualcircle.org
    depends_on:
      - backend

volumes:
  postgres_data:
```

Run:

```bash
docker-compose up -d
```

---

## Frontend Deployment

### 1. Build Frontend

```bash
cd frontend
npm install
npm run build
```

This creates optimized production build in `dist/` directory.

### 2. Deploy to Nginx

#### Install Nginx

```bash
sudo apt install nginx
```

#### Configure Nginx

Create `/etc/nginx/sites-available/mutualcircle`:

```nginx
# API Server (backend)
server {
    listen 80;
    server_name api.mutualcircle.org;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Frontend (React app)
server {
    listen 80;
    server_name mutualcircle.org www.mutualcircle.org;

    root /var/www/mutualcircle/frontend/dist;
    index index.html;

    # Compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml;

    # Frontend routes
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Static assets with caching
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

Enable site:

```bash
sudo ln -s /etc/nginx/sites-available/mutualcircle /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 3. Setup SSL with Let's Encrypt

```bash
sudo apt install certbot python3-certbot-nginx

# Generate certificates
sudo certbot --nginx -d mutualcircle.org -d www.mutualcircle.org -d api.mutualcircle.org

# Auto-renewal
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer
```

### Option: Deploy to Vercel (Frontend Only)

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
cd frontend
vercel --prod
```

Configure environment variables in Vercel dashboard.

---

## Celery & Redis Setup

### 1. Install Redis

```bash
sudo apt install redis-server
sudo systemctl start redis
sudo systemctl enable redis
```

### 2. Configure Celery Workers

Create `/etc/supervisor/conf.d/mutualcircle-celery-worker.conf`:

```ini
[program:mutualcircle-celery-worker]
directory=/home/deploy/mutualcircle/backend
command=/home/deploy/mutualcircle/backend/venv/bin/celery -A app.celery_app worker --loglevel=info
user=deploy
autostart=true
autorestart=true
stderr_logfile=/var/log/mutualcircle/celery-worker.err.log
stdout_logfile=/var/log/mutualcircle/celery-worker.out.log
```

### 3. Configure Celery Beat (Scheduler)

Create `/etc/supervisor/conf.d/mutualcircle-celery-beat.conf`:

```ini
[program:mutualcircle-celery-beat]
directory=/home/deploy/mutualcircle/backend
command=/home/deploy/mutualcircle/backend/venv/bin/celery -A app.celery_app beat --loglevel=info
user=deploy
autostart=true
autorestart=true
stderr_logfile=/var/log/mutualcircle/celery-beat.err.log
stdout_logfile=/var/log/mutualcircle/celery-beat.out.log
```

### 4. Start Celery

```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start mutualcircle-celery-worker
sudo supervisorctl start mutualcircle-celery-beat
```

---

## Production Checklist

### Security

- [ ] Change `SECRET_KEY` to strong random value
- [ ] Enable HTTPS (SSL certificates installed)
- [ ] Configure CORS to only allow your domains
- [ ] Set secure database passwords
- [ ] Enable firewall (allow only ports 80, 443, 22)
- [ ] Disable debug mode (`DEBUG=False`)
- [ ] Set up rate limiting
- [ ] Configure CSP headers
- [ ] Enable SQL injection prevention
- [ ] Set up backup encryption

### Database

- [ ] Run all migrations (`alembic upgrade head`)
- [ ] Create database indexes
- [ ] Set up automated backups (daily)
- [ ] Configure connection pooling
- [ ] Enable query logging (temporary)
- [ ] Test database restore procedure

### Services

- [ ] Backend API running and accessible
- [ ] Frontend build deployed
- [ ] Nginx configured and running
- [ ] SSL certificates valid
- [ ] Celery workers running
- [ ] Celery beat running
- [ ] Redis running

### Email & Notifications

- [ ] SMTP credentials configured
- [ ] Test email sending
- [ ] Twilio credentials configured (optional)
- [ ] Test SMS sending (optional)
- [ ] Set up email templates
- [ ] Configure notification preferences

### Monitoring

- [ ] Set up error tracking (Sentry)
- [ ] Configure logging
- [ ] Set up uptime monitoring
- [ ] Configure performance monitoring
- [ ] Set up alerts for errors
- [ ] Create admin dashboard

### Backups

- [ ] Database backups configured (automated)
- [ ] Test restore procedure
- [ ] Off-site backup storage
- [ ] Backup rotation policy (keep 30 days)
- [ ] Document backup locations

### Documentation

- [ ] Update README with production URLs
- [ ] Create admin documentation
- [ ] Document deployment process
- [ ] Create runbook for common issues
- [ ] Document rollback procedure

---

## Monitoring & Maintenance

### Logs

**View logs:**

```bash
# API logs
sudo tail -f /var/log/mutualcircle/api.out.log

# Celery worker logs
sudo tail -f /var/log/mutualcircle/celery-worker.out.log

# Nginx access logs
sudo tail -f /var/log/nginx/access.log

# Nginx error logs
sudo tail -f /var/log/nginx/error.log
```

### Database Backups

Create backup script `/usr/local/bin/backup-mutualcircle-db.sh`:

```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/mutualcircle"
DB_NAME="mutualcircle_prod"
DB_USER="mutualcircle"

mkdir -p $BACKUP_DIR

# Create backup
pg_dump -U $DB_USER -d $DB_NAME | gzip > $BACKUP_DIR/backup_$DATE.sql.gz

# Delete backups older than 30 days
find $BACKUP_DIR -type f -name "backup_*.sql.gz" -mtime +30 -delete

echo "Backup completed: backup_$DATE.sql.gz"
```

Make executable and add to cron:

```bash
chmod +x /usr/local/bin/backup-mutualcircle-db.sh
crontab -e

# Add line (runs daily at 2 AM):
0 2 * * * /usr/local/bin/backup-mutualcircle-db.sh
```

### Restore from Backup

```bash
# Stop services
sudo supervisorctl stop all

# Restore database
gunzip -c /backups/mutualcircle/backup_20241112_020000.sql.gz | psql -U mutualcircle -d mutualcircle_prod

# Start services
sudo supervisorctl start all
```

### Health Checks

Create health check endpoint monitoring:

```bash
# Add to crontab (check every 5 minutes)
*/5 * * * * curl -f https://api.mutualcircle.org/health || echo "API is down" | mail -s "MutualCircle Alert" admin@mutualcircle.org
```

### Update Deployment

```bash
# Pull latest code
cd /home/deploy/mutualcircle
git pull origin main

# Update backend
cd backend
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head

# Update frontend
cd ../frontend
npm install
npm run build
sudo cp -r dist/* /var/www/mutualcircle/frontend/dist/

# Restart services
sudo supervisorctl restart mutualcircle-api
sudo supervisorctl restart mutualcircle-celery-worker
sudo supervisorctl restart mutualcircle-celery-beat
sudo systemctl reload nginx
```

---

## Troubleshooting

### API Not Responding

```bash
# Check if process is running
sudo supervisorctl status mutualcircle-api

# Check logs
sudo tail -f /var/log/mutualcircle/api.err.log

# Restart service
sudo supervisorctl restart mutualcircle-api
```

### Database Connection Errors

```bash
# Test connection
psql -U mutualcircle -d mutualcircle_prod

# Check PostgreSQL status
sudo systemctl status postgresql

# Restart PostgreSQL
sudo systemctl restart postgresql
```

### Celery Tasks Not Running

```bash
# Check Redis
redis-cli ping

# Check workers
sudo supervisorctl status mutualcircle-celery-worker

# Check beat
sudo supervisorctl status mutualcircle-celery-beat

# Restart Celery
sudo supervisorctl restart mutualcircle-celery-worker
sudo supervisorctl restart mutualcircle-celery-beat
```

### Frontend Not Loading

```bash
# Check Nginx
sudo nginx -t
sudo systemctl status nginx

# Check build exists
ls -la /var/www/mutualcircle/frontend/dist

# Check Nginx logs
sudo tail -f /var/log/nginx/error.log
```

---

## Performance Optimization

### Database

- Add indexes on frequently queried columns
- Use connection pooling
- Configure autovacuum
- Monitor slow queries

### Backend

- Use gunicorn/uvicorn with multiple workers
- Enable caching (Redis)
- Optimize database queries
- Use async where possible

### Frontend

- Enable gzip compression
- Set far-future cache headers for assets
- Use CDN for static files
- Implement code splitting

### Monitoring Metrics

- Response times (< 200ms target)
- Error rates (< 0.1% target)
- Database query times
- Memory usage
- CPU usage
- Disk space

---

## Security Updates

### Regular Maintenance

```bash
# Update system packages
sudo apt update && sudo apt upgrade

# Update Python packages
cd backend
pip list --outdated
pip install -U package-name

# Update Node packages
cd frontend
npm outdated
npm update
```

### Security Scanning

```bash
# Check Python vulnerabilities
pip-audit

# Check Node vulnerabilities
npm audit
npm audit fix
```

---

## Rollback Procedure

If deployment fails:

1. **Revert code:**
   ```bash
   git revert HEAD
   git push
   ```

2. **Restore database:**
   ```bash
   # Use latest backup
   gunzip -c /backups/mutualcircle/backup_latest.sql.gz | psql -U mutualcircle -d mutualcircle_prod
   ```

3. **Restart services:**
   ```bash
   sudo supervisorctl restart all
   ```

---

## Support

- **Documentation:** https://docs.mutualcircle.org
- **Issues:** https://github.com/yourusername/mutualcircle/issues
- **Email:** devops@mutualcircle.org

---

**Last Updated:** November 2024
**Version:** 1.0
