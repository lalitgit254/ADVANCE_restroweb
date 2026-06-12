# RestaurantPro Deployment Guide

## Prerequisites

- Ubuntu 22.04+ server
- Docker & Docker Compose (recommended) OR Python 3.11+, MySQL 8+, Redis, Nginx
- Domain name with SSL certificate (Let's Encrypt)

## Quick Start with Docker

```bash
# Clone and configure
cp .env.example .env
# Edit .env with production secrets

# Start all services
docker-compose up -d --build

# Seed sample data
docker-compose exec web python seed_data.py
```

Access the app at `http://localhost` (via Nginx) or `http://localhost:5000` (direct).

## Manual Deployment (Ubuntu)

### 1. Install Dependencies

```bash
sudo apt update
sudo apt install -y python3.11 python3.11-venv mysql-server redis-server nginx
```

### 2. Database Setup

```bash
sudo mysql -u root -p < database/schema.sql
```

### 3. Application Setup

```bash
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your configuration

flask db init
flask db migrate -m "Initial migration"
flask db upgrade
python seed_data.py
```

### 4. Gunicorn + Eventlet (Production)

```bash
gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:5000 wsgi:app
```

### 5. Systemd Service

Create `/etc/systemd/system/restaurantpro.service`:

```ini
[Unit]
Description=RestaurantPro Web Application
After=network.target mysql.service redis.service

[Service]
User=www-data
WorkingDirectory=/var/www/restaurantpro
Environment="PATH=/var/www/restaurantpro/venv/bin"
ExecStart=/var/www/restaurantpro/venv/bin/gunicorn --worker-class eventlet -w 1 --bind 127.0.0.1:5000 wsgi:app
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable restaurantpro
sudo systemctl start restaurantpro
```

### 6. Nginx Configuration

Copy `nginx/nginx.conf` to `/etc/nginx/sites-available/restaurantpro` and enable:

```bash
sudo ln -s /etc/nginx/sites-available/restaurantpro /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

### 7. SSL with Certbot

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | Flask secret key (generate with `python -c "import secrets; print(secrets.token_hex(32))"`) |
| `DATABASE_URL` | MySQL connection string |
| `REDIS_URL` | Redis connection for SocketIO |
| `RAZORPAY_KEY_ID` | Razorpay payment gateway key |
| `CLOUDINARY_*` | Cloudinary image storage credentials |
| `MAIL_*` | SMTP email configuration |
| `GOOGLE_CLIENT_ID` | Google OAuth credentials |

## API Documentation

Swagger UI is available at `/api/v1/docs` when the application is running.

## Default Login Credentials (after seeding)

| Role | Email | Password |
|------|-------|----------|
| Super Admin | superadmin@restaurantpro.com | Admin@123 |
| Admin | admin@restaurantpro.com | Admin@123 |
| Customer | customer@restaurantpro.com | Customer@123 |
| Chef | chef@restaurantpro.com | Staff@123 |

**Change all passwords immediately in production.**

## Health Checks

- Application: `curl http://localhost:5000/`
- API: `curl http://localhost:5000/api/v1/restaurants`
- Database: `docker-compose exec db mysqladmin ping`

## Backup

```bash
# Database backup
mysqldump -u restaurant_user -p restaurant_db > backup_$(date +%Y%m%d).sql

# Uploads backup
tar -czf uploads_backup.tar.gz uploads/
```
