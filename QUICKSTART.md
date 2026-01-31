# Quick Start Guide

Panduan cepat untuk menjalankan Google Maps Scraper API.

## Local Development (Mac/Linux)

### 1. Install Dependencies

```bash
cd /Applications/python/chatcepat

# Buat virtual environment
python3 -m venv venv
source venv/bin/activate

# Install packages
pip3 install -r requirements.txt
```

### 2. Setup Environment

```bash
cp .env.example .env
# Edit .env jika perlu, atau gunakan default
```

### 3. Run API Server

```bash
python3 api.py
```

Output:
```
Starting Google Maps Scraper API on port 5000
Debug mode: false
 * Running on http://0.0.0.0:5000
```

### 4. Test API

Buka terminal baru:

```bash
# Health check
curl http://localhost:5000/health

# Test scraping
curl -X POST http://localhost:5000/api/scrape \
  -H "Content-Type: application/json" \
  -H "X-API-Key: chatcepat-secret-key-2024" \
  -d '{
    "keyword": "restaurant",
    "location": "Jakarta",
    "kecamatan": "Menteng",
    "max_results": 5
  }'
```

### 5. Setup Laravel

```bash
cd /Applications/laravel/chatcepat

# Tambahkan ke .env
echo "PYTHON_SCRAPER_API_URL=http://localhost:5000" >> .env
echo "PYTHON_SCRAPER_API_KEY=chatcepat-secret-key-2024" >> .env

# Run Laravel
php artisan serve
npm run dev
```

### 6. Akses UI

Buka browser: `http://localhost:8000/admin/google-maps-scraper`

---

## Production VPS (Ubuntu/Debian)

### 1. Install System Requirements

```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install Python
sudo apt-get install -y python3 python3-pip python3-venv

# Install Chrome
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo dpkg -i google-chrome-stable_current_amd64.deb
sudo apt-get install -f -y

# Install Supervisor
sudo apt-get install -y supervisor
```

### 2. Deploy Application

```bash
# Clone atau upload files ke VPS
sudo mkdir -p /var/www/chatcepat-scraper
cd /var/www/chatcepat-scraper

# Upload semua file dari /Applications/python/chatcepat

# Create virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Setup Supervisor

```bash
# Copy config
sudo cp supervisor.conf.example /etc/supervisor/conf.d/gmaps-scraper.conf

# Edit config (sesuaikan path)
sudo nano /etc/supervisor/conf.d/gmaps-scraper.conf

# Update & start
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start gmaps-scraper
sudo supervisorctl status
```

### 4. Setup Firewall

```bash
# Allow port 5000 (atau batasi hanya dari Laravel server)
sudo ufw allow 5000

# Atau hanya dari IP Laravel
sudo ufw allow from YOUR_LARAVEL_SERVER_IP to any port 5000
```

### 5. Configure Laravel

Edit Laravel `.env`:
```bash
PYTHON_SCRAPER_API_URL=http://YOUR_VPS_IP:5000
PYTHON_SCRAPER_API_KEY=chatcepat-secret-key-2024
```

### 6. Test Connection

Dari Laravel server:
```bash
curl http://YOUR_VPS_IP:5000/health
```

---

## Production with Nginx + SSL (Recommended)

### 1. Install Nginx

```bash
sudo apt-get install -y nginx certbot python3-certbot-nginx
```

### 2. Create Nginx Config

```bash
sudo nano /etc/nginx/sites-available/scraper-api
```

Paste:
```nginx
server {
    listen 80;
    server_name scraper-api.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
}
```

### 3. Enable Site

```bash
sudo ln -s /etc/nginx/sites-available/scraper-api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 4. Setup SSL (Let's Encrypt)

```bash
sudo certbot --nginx -d scraper-api.yourdomain.com
```

### 5. Update Laravel .env

```bash
PYTHON_SCRAPER_API_URL=https://scraper-api.yourdomain.com
PYTHON_SCRAPER_API_KEY=chatcepat-secret-key-2024
```

---

## Docker Deployment

### 1. Build & Run

```bash
cd /var/www/chatcepat-scraper

# Build image
docker-compose build

# Run container
docker-compose up -d

# Check status
docker-compose ps
docker-compose logs -f
```

### 2. Configure Laravel

```bash
PYTHON_SCRAPER_API_URL=http://YOUR_VPS_IP:5000
PYTHON_SCRAPER_API_KEY=chatcepat-secret-key-2024
```

---

## Troubleshooting

### API tidak bisa diakses

1. Check service running:
```bash
sudo supervisorctl status gmaps-scraper
# atau
docker-compose ps
```

2. Check port:
```bash
netstat -tlnp | grep 5000
```

3. Check firewall:
```bash
sudo ufw status
```

### Chrome error

```bash
# Install Chrome dependencies
sudo apt-get install -y libnss3 libgconf-2-4 libxss1 libappindicator1 libindicator7
```

### Permission errors

```bash
sudo chown -R www-data:www-data /var/www/chatcepat-scraper
```

### Memory issues

Tambahkan swap:
```bash
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

---

## Monitoring

### Check Logs

```bash
# Supervisor
sudo tail -f /var/log/supervisor/gmaps-scraper.out.log

# Docker
docker-compose logs -f

# Systemd
sudo journalctl -u gmaps-scraper -f
```

### Test Scraping

```bash
curl -X POST http://localhost:5000/api/scrape \
  -H "Content-Type: application/json" \
  -H "X-API-Key: chatcepat-secret-key-2024" \
  -d '{
    "keyword": "cafe",
    "location": "Jakarta",
    "kecamatan": "Senopati",
    "max_results": 3
  }'
```

---

## Tips

1. **Ganti API Key** di production untuk security
2. **Monitor resource** - Chrome memakan banyak memory
3. **Setup monitoring** dengan tools seperti Uptime Kuma
4. **Backup database** Laravel secara berkala
5. **Gunakan proxy** jika scraping volume tinggi

---

## Need Help?

- Check dokumentasi lengkap di [README.md](README.md)
- Review logs untuk error messages
- Test API endpoint secara manual dengan curl
