# =============================================================================
# GiftsChart Telegram Bot - Dockerfile
# Multi-service container for bot, CDN, and schedulers
# =============================================================================

FROM python:3.14-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Set working directory
WORKDIR /app

# Install system dependencies for PIL, matplotlib, cairosvg
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libc-dev \
    libffi-dev \
    libcairo2-dev \
    libpango1.0-dev \
    libgdk-pixbuf-2.0-dev \
    librsvg2-dev \
    libfreetype6-dev \
    libjpeg-dev \
    zlib1g-dev \
    libpng-dev \
    fonts-dejavu-core \
    fontconfig \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean


# Copy requirements first for layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories if they don't exist
RUN mkdir -p sqlite_data new_gift_cards Sticker_Price_Cards downloaded_images

# Copy custom font (JSON array form for filename with spaces)
COPY ["Typekiln - EloquiaDisplay-ExtraBold.otf", "/usr/share/fonts/truetype/"]
RUN fc-cache -fv || true

# Default command (overridden by docker-compose)
CMD ["python3", "telegram_bot.py"]
