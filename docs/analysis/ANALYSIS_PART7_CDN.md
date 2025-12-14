# Part 7: CDN Server & Deployment

## 🌐 CDN SERVER (cdn_server.py - Flask)

### Configuration:
```python
HOST = "0.0.0.0"  # Listen on all interfaces
PORT = 4000
CDN_BASE_URL = "https://giftschart.the01studio.xyz/api"
```

### Endpoints:

#### 1. Gift Cards
```python
@app.route('/api/cards/<gift_name>')
def serve_gift_card(gift_name):
    # Normalize filename
    # Check if file exists
    # Serve from new_gift_cards/
```

#### 2. Sticker Cards
```python
@app.route('/api/stickers/<collection>/<sticker>')
def serve_sticker_card(collection, sticker):
    # Normalize collection and sticker names
    # Check if file exists
    # Serve from Sticker_Price_Cards/
```

#### 3. Sticker Images
```python
@app.route('/api/sticker_images/<collection>/<image_number>')
def serve_sticker_image(collection, image_number):
    # Serve from sticker_collections/
```

#### 4. Health Check
```python
@app.route('/api/health')
def health_check():
    return jsonify({"status": "ok"})
```

### CORS Configuration:
```python
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    return response
```

## 🐳 DOCKER DEPLOYMENT

### Dockerfile:
```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc libc-dev libffi-dev libcairo2-dev \
    libpango1.0-dev libgdk-pixbuf-2.0-dev \
    librsvg2-dev libfreetype6-dev libjpeg-dev \
    zlib1g-dev libpng-dev fonts-dejavu-core

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create directories
RUN mkdir -p sqlite_data new_gift_cards \
    Sticker_Price_Cards downloaded_images

# Copy custom font
COPY ["Typekiln - EloquiaDisplay-ExtraBold.otf", \
      "/usr/share/fonts/truetype/"]
RUN fc-cache -fv

CMD ["python3", "telegram_bot.py"]
```

### docker-compose.yml:
```yaml
version: "3.8"

services:
  bot:
    build: .
    container_name: giftschart_bot
    restart: unless-stopped
    command: python3 telegram_bot.py
    volumes:
      - ./sqlite_data:/app/sqlite_data
      - ./new_gift_cards:/app/new_gift_cards
      - ./Sticker_Price_Cards:/app/Sticker_Price_Cards
    environment:
      - TZ=UTC
    networks:
      - giftschart_network

  cdn:
    build: .
    container_name: giftschart_cdn
    restart: unless-stopped
    command: python3 cdn_server.py
    ports:
      - "4000:4000"
    volumes:
      - ./new_gift_cards:/app/new_gift_cards
      - ./Sticker_Price_Cards:/app/Sticker_Price_Cards
    networks:
      - giftschart_network

  scheduler:
    build: .
    container_name: giftschart_scheduler
    restart: unless-stopped
    command: python3 pregenerate_gift_cards.py
    volumes:
      - ./new_gift_cards:/app/new_gift_cards
    networks:
      - giftschart_network

  sticker:
    build: .
    container_name: giftschart_sticker
    restart: unless-stopped
    command: python3 scheduled_sticker_update.py
    volumes:
      - ./Sticker_Price_Cards:/app/Sticker_Price_Cards
    networks:
      - giftschart_network
```
