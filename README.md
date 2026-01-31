# Google Maps Scraper API

REST API berbasis Flask untuk scraping data Google Maps per kecamatan dengan integrasi Laravel.

## Fitur Anti-Blocking

✅ **User Agent Rotation** - Rotasi otomatis user agent untuk menghindari deteksi
✅ **Random Delays** - Delay acak untuk meniru perilaku manusia
✅ **Proxy Support** - Mendukung proxy untuk IP rotation
✅ **Anti-Detection** - Berbagai teknik untuk menghindari deteksi bot
✅ **Scroll Simulation** - Simulasi scroll manusia saat mengambil data

## Instalasi

### 1. Install Dependencies Python

```bash
cd /Applications/python/chatcepat

# Buat virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# atau
venv\Scripts\activate  # Windows

# Install dependencies
pip3 install -r requirements.txt
```

### 2. Install Chrome Browser

Script ini menggunakan Selenium dengan Chrome WebDriver. `webdriver-manager` akan otomatis mengunduh ChromeDriver yang sesuai.

**Linux (Ubuntu/Debian):**
```bash
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo dpkg -i google-chrome-stable_current_amd64.deb
sudo apt-get install -f
```

**macOS:**
```bash
brew install --cask google-chrome
```

### 3. Konfigurasi Environment

```bash
cp .env.example .env
nano .env  # Edit sesuai kebutuhan
```

**.env Configuration:**
```bash
PORT=5000
DEBUG=false
API_KEY=your-secret-api-key-change-this

# Proxy (optional)
USE_PROXY=false
# PROXY_SERVER=ip:port
```

## Menjalankan API

### Development Mode

```bash
# Activate virtual environment
source venv/bin/activate

# Run Flask development server
python3 api.py
```

API akan berjalan di `http://localhost:5000`

### Production Mode (Gunicorn)

```bash
gunicorn --workers 4 --bind 0.0.0.0:5000 --timeout 300 api:app
```

### Test API

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

## API Endpoints

### 1. Health Check
```
GET /health
```
Response:
```json
{
  "status": "ok",
  "message": "Google Maps Scraper API is running"
}
```

### 2. Scrape Google Maps
```
POST /api/scrape
Headers:
  X-API-Key: your-secret-api-key
  Content-Type: application/json

Body:
{
  "keyword": "restaurant",
  "location": "Jakarta",
  "kecamatan": "Menteng",
  "max_results": 20
}
```

Response Success:
```json
{
  "status": "success",
  "data": [...],
  "total": 20,
  "query": {...}
}
```

Response Error:
```json
{
  "status": "error",
  "message": "Error message"
}
```

## Integrasi dengan Laravel

### 1. Konfigurasi Laravel .env

Tambahkan ke file `.env` Laravel:
```bash
PYTHON_SCRAPER_API_URL=http://localhost:5000
PYTHON_SCRAPER_API_KEY=chatcepat-secret-key-2024
```

**Untuk VPS/Production:**
```bash
PYTHON_SCRAPER_API_URL=http://your-vps-ip:5000
# atau dengan domain
PYTHON_SCRAPER_API_URL=https://scraper-api.yourdomain.com
```

### 2. Akses UI Laravel

1. Buka browser: `http://your-laravel-app.test/admin/google-maps-scraper`
2. Login ke admin panel
3. Isi form scraping dan klik "Mulai Scraping"
4. Hasil akan otomatis tersimpan di database

### 3. Export Data

Klik tombol "Export CSV" untuk mengunduh data dalam format CSV.

## Deployment ke VPS

### Opsi 1: Systemd Service

1. Copy service file:
```bash
sudo cp systemd-service.example /etc/systemd/system/gmaps-scraper.service
sudo nano /etc/systemd/system/gmaps-scraper.service  # Edit path
```

2. Start service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable gmaps-scraper
sudo systemctl start gmaps-scraper
sudo systemctl status gmaps-scraper
```

3. View logs:
```bash
sudo journalctl -u gmaps-scraper -f
```

### Opsi 2: Supervisor

1. Install Supervisor:
```bash
sudo apt-get install supervisor
```

2. Copy config:
```bash
sudo cp supervisor.conf.example /etc/supervisor/conf.d/gmaps-scraper.conf
sudo nano /etc/supervisor/conf.d/gmaps-scraper.conf  # Edit path
```

3. Start:
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start gmaps-scraper
sudo supervisorctl status
```

### Opsi 3: Docker

1. Build image:
```bash
docker-compose build
```

2. Run container:
```bash
docker-compose up -d
```

3. Check logs:
```bash
docker-compose logs -f
```

### Opsi 4: Nginx Reverse Proxy (Recommended untuk Production)

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

## Tips Menghindari Blocking

### 1. Gunakan Proxy Rotation

Edit `.env`:
```bash
USE_PROXY=true
PROXY_SERVER=ip:port
```

**Rekomendasi Proxy Provider:**
- [Bright Data](https://brightdata.com) - Premium, stabil
- [Oxylabs](https://oxylabs.io) - Residential proxies
- [ScraperAPI](https://scraperapi.com) - Built-in proxy rotation

### 2. Kurangi Request Rate

- Gunakan `max_results` yang lebih kecil (10-20)
- Beri jeda antara scraping (jangan terlalu sering)
- Scrape di luar jam sibuk

### 3. Rotate IP Address

Jika di-block, restart router atau gunakan VPN untuk ganti IP.

### 4. Gunakan Official API (Alternatif)

Pertimbangkan menggunakan [Google Places API](https://developers.google.com/maps/documentation/places/web-service/overview) untuk kebutuhan komersial. Lebih stabil dan tidak akan di-block.

## Troubleshooting

### Error: Chrome driver not found
```bash
# Manual install ChromeDriver
wget https://chromedriver.storage.googleapis.com/LATEST_RELEASE
```

### Error: Permission denied
```bash
chmod +x api.py scraper.py
```

### API tidak bisa diakses dari Laravel
1. Check firewall: `sudo ufw allow 5000`
2. Check API running: `curl http://localhost:5000/health`
3. Check API key di Laravel .env

### Scraping terlalu lambat
- Normal, karena ada random delay untuk anti-blocking
- Kurangi `max_results`
- Gunakan server dengan koneksi lebih cepat

### Error: 401 Unauthorized
API key salah atau tidak cocok antara Python dan Laravel.

### Data tidak lengkap
Normal. Beberapa tempat tidak punya semua field (rating, phone, dll).

## Security Best Practices

1. **Ganti API Key** - Jangan gunakan default key
2. **Firewall** - Batasi akses port 5000 hanya dari Laravel server
3. **HTTPS** - Gunakan SSL/TLS untuk production
4. **Rate Limiting** - Implementasi rate limiting di Nginx
5. **Monitoring** - Setup monitoring untuk detect failures

## Monitoring

### Check Service Status
```bash
# Systemd
sudo systemctl status gmaps-scraper

# Supervisor
sudo supervisorctl status gmaps-scraper

# Docker
docker-compose ps
```

### View Logs
```bash
# Systemd
sudo journalctl -u gmaps-scraper -f

# Supervisor
sudo tail -f /var/log/supervisor/gmaps-scraper.out.log

# Docker
docker-compose logs -f
```

## Performance Tuning

### Gunicorn Workers

Rumus: `workers = (2 x CPU_cores) + 1`

Contoh untuk 4 CPU cores:
```bash
gunicorn --workers 9 --bind 0.0.0.0:5000 --timeout 300 api:app
```

### Chrome Options

Edit `scraper.py` untuk tuning memory:
```python
self.options.add_argument('--disable-dev-shm-usage')
self.options.add_argument('--disable-gpu')
```

## Catatan Penting

⚠️ **Legal & Ethics:**
- Gunakan secara bertanggung jawab
- Patuhi Terms of Service Google Maps
- Untuk penggunaan komersial, pertimbangkan API resmi
- Scraping berlebihan dapat menyebabkan IP di-block

⚠️ **Rate Limiting:**
- Google Maps membatasi request dari IP yang sama
- Gunakan proxy rotation untuk volume tinggi
- Implementasi cache untuk data yang sama

⚠️ **Resource Usage:**
- Chrome memakan banyak memory (1-2GB per instance)
- Batasi concurrent scraping
- Monitor CPU & memory usage

## Support

Untuk issue dan bug report, silakan buat issue di repository.

## License

Untuk penggunaan internal dan edukasi.
# chatcepat-python
