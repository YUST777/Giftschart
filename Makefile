.PHONY: help install test lint format clean run docker-build docker-up docker-down backup

# Default target
help:
	@echo "GiftsChart Bot - Available Commands"
	@echo "===================================="
	@echo ""
	@echo "Development:"
	@echo "  make install       - Install dependencies"
	@echo "  make test          - Run tests"
	@echo "  make lint          - Run linters"
	@echo "  make format        - Format code"
	@echo "  make clean         - Clean cache and temp files"
	@echo ""
	@echo "Running:"
	@echo "  make run           - Run the bot"
	@echo "  make run-pm2       - Run with PM2"
	@echo "  make stop-pm2      - Stop PM2 processes"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build  - Build Docker image"
	@echo "  make docker-up     - Start Docker containers"
	@echo "  make docker-down   - Stop Docker containers"
	@echo "  make docker-logs   - View Docker logs"
	@echo ""
	@echo "Maintenance:"
	@echo "  make backup        - Run database backup"
	@echo "  make generate      - Generate all cards"
	@echo "  make check         - Check system status"
	@echo ""

# Install dependencies
install:
	@echo "Installing dependencies..."
	pip install --upgrade pip
	pip install -r requirements.txt
	@echo "✓ Dependencies installed"

# Run tests
test:
	@echo "Running tests..."
	pytest tests/ -v --cov=. --cov-report=html --cov-report=term
	@echo "✓ Tests completed"

# Run linters
lint:
	@echo "Running linters..."
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	flake8 . --count --exit-zero --max-complexity=10 --max-line-length=100 --statistics
	pylint **/*.py --exit-zero
	@echo "✓ Linting completed"

# Format code
format:
	@echo "Formatting code..."
	black --line-length 100 .
	isort --profile black --line-length 100 .
	@echo "✓ Code formatted"

# Clean cache and temp files
clean:
	@echo "Cleaning cache and temp files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.log" -delete
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf *.egg-info
	rm -rf build
	rm -rf dist
	@echo "✓ Cleaned"

# Run the bot
run:
	@echo "Starting GiftsChart Bot..."
	python core/telegram_bot.py

# Run with PM2
run-pm2:
	@echo "Starting with PM2..."
	pm2 start ecosystem.config.js
	pm2 logs

# Stop PM2
stop-pm2:
	@echo "Stopping PM2 processes..."
	pm2 stop all
	pm2 delete all

# Docker build
docker-build:
	@echo "Building Docker image..."
	docker-compose build
	@echo "✓ Docker image built"

# Docker up
docker-up:
	@echo "Starting Docker containers..."
	docker-compose up -d
	docker-compose logs -f

# Docker down
docker-down:
	@echo "Stopping Docker containers..."
	docker-compose down

# Docker logs
docker-logs:
	docker-compose logs -f

# Run backup
backup:
	@echo "Running database backup..."
	python schedulers/supabase_backup_sync.py
	@echo "✓ Backup completed"

# Generate all cards
generate:
	@echo "Generating all cards..."
	python generators/pregenerate_gift_cards.py
	python generators/generate_all_stickers.py
	@echo "✓ Cards generated"

# Check system status
check:
	@echo "Checking system status..."
	python check_system.py

# Setup pre-commit hooks
setup-hooks:
	@echo "Setting up pre-commit hooks..."
	pip install pre-commit
	pre-commit install
	@echo "✓ Pre-commit hooks installed"

# Run pre-commit on all files
pre-commit:
	@echo "Running pre-commit on all files..."
	pre-commit run --all-files

# Security scan
security:
	@echo "Running security scan..."
	pip install safety bandit pip-audit
	safety check
	bandit -r . -f txt
	pip-audit
	@echo "✓ Security scan completed"

# Update dependencies
update:
	@echo "Updating dependencies..."
	pip install --upgrade -r requirements.txt
	@echo "✓ Dependencies updated"

# Create virtual environment
venv:
	@echo "Creating virtual environment..."
	python3 -m venv venv
	@echo "✓ Virtual environment created"
	@echo "Activate with: source venv/bin/activate"

# Full setup (for new developers)
setup: venv install setup-hooks
	@echo ""
	@echo "✓ Setup completed!"
	@echo ""
	@echo "Next steps:"
	@echo "1. Activate virtual environment: source venv/bin/activate"
	@echo "2. Copy .env.example to .env and configure"
	@echo "3. Run the bot: make run"
	@echo ""
