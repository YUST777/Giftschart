# Project Structure

## Overview
Clean, organized structure for the GiftsChart Telegram bot project.

## Directory Layout

```
GiftsChart-ALL/
│
├── 📄 README.md                 # Main project documentation
├── 📄 .env                      # Environment variables (not in git)
├── 📄 .gitignore                # Git ignore rules
├── 📄 requirements.txt          # Python dependencies
├── 📄 Dockerfile                # Docker configuration
├── 📄 docker-compose.yml        # Docker Compose setup
├── 📄 ecosystem.config.js       # PM2 configuration
├── 📄 quick_start.sh            # Quick start script
│
├── 📁 docs/                     # 📚 All Documentation
│   ├── README.md                # Documentation index
│   ├── CLEANUP_SUMMARY.md       # Cleanup details
│   ├── PROJECT_STRUCTURE.md     # This file
│   ├── analysis/                # Technical analysis (15 files)
│   ├── backup/                  # Backup documentation (4 files)
│   ├── code_quality/            # Code quality reports (3 files)
│   ├── setup/                   # Setup guides (5 files)
│   └── status/                  # Status & changes (8 files)
│
├── 📁 logs/                     # 📊 Log Files
│   ├── bot.log                  # Main bot logs
│   ├── card_generation.log      # Card generation logs
│   ├── sticker_generation.log   # Sticker generation logs
│   └── [other logs]
│
├── 📁 core/                     # 🎯 Core Bot Functionality
│   ├── telegram_bot.py          # Main bot logic
│   ├── callback_handler.py      # Button callbacks
│   ├── bot_config.py            # Bot configuration
│   ├── premium_system.py        # Premium features
│   ├── rate_limiter.py          # Rate limiting
│   └── supabase_client.py       # Database client
│
├── 📁 services/                 # 🔌 External Services
│   ├── portal_api.py            # Portal API integration
│   ├── mrkt_api.py              # MRKT API integration
│   ├── stickers_tools_api.py    # Stickers.tools API
│   ├── sticker_integration.py   # Sticker functionality
│   ├── premarket_gifts.py       # Premarket gifts
│   ├── plus_premarket_gifts.py  # Plus premarket
│   └── cdn_server.py            # CDN server
│
├── 📁 generators/               # 🎨 Card Generators
│   ├── gift_card_generator.py   # Gift price cards
│   ├── sticker_price_card_generator.py  # Sticker cards
│   ├── goodies_price_card_generator.py  # Goodies cards
│   ├── plus_premarket_card_generator.py # Plus cards
│   ├── generate_all_stickers.py # Batch sticker generation
│   └── pregenerate_gift_cards.py # Batch gift generation
│
├── 📁 schedulers/               # ⏰ Background Tasks
│   ├── supabase_backup_sync.py  # Database backup
│   └── run_supabase_backup.py   # Backup runner
│
├── 📁 utils/                    # 🛠️ Utility Functions
│   ├── ton_price_utils.py       # TON price fetching
│   └── [other utilities]
│
├── 📁 config/                   # ⚙️ Configuration
│   └── paths.py                 # Centralized paths
│
├── 📁 data/                     # 💾 Data Files
│   ├── sticker_price_results.json  # Sticker prices
│   └── logs/                    # Data-related logs
│
├── 📁 assets/                   # 🖼️ Static Assets
│   ├── fonts/                   # Font files
│   ├── TON2.webp                # TON logo
│   ├── star.webp                # Star icon
│   ├── supply.svg               # Supply icon
│   └── [other assets]
│
├── 📁 card_templates/           # 🎴 Gift Templates
│   ├── Astral_Shard_template.webp
│   ├── Diamond_Ring_template.webp
│   └── [93 gift templates]
│
├── 📁 card_metadata/            # 📋 Gift Metadata
│   ├── Astral_Shard_metadata.json
│   ├── Diamond_Ring_metadata.json
│   └── [93 metadata files]
│
├── 📁 sticker_collections/      # 🎭 Sticker Images
│   ├── dogs_og/                 # Dogs OG collection
│   ├── not_pixel/               # Not Pixel collection
│   ├── pudgy_penguins/          # Pudgy Penguins
│   └── [other collections]
│
├── 📁 new_gift_cards/           # 🆕 Generated Gift Cards
│   └── [102 generated cards]
│
├── 📁 Sticker_Price_Cards/      # 🆕 Generated Sticker Cards
│   └── [218 generated cards]
│
├── 📁 sqlite_data/              # 🗄️ SQLite Database
│   └── bot_data.db              # Main database
│
└── 📁 api/                      # 🔬 API Testing
    ├── mrkt/                    # MRKT API tests
    ├── quant/                   # Quant API tests
    └── quantom0.2/              # Quantom API tests
```

## Key Directories

### 📚 docs/
All project documentation organized by category:
- **analysis/** - Technical deep dives and architecture
- **setup/** - Getting started and deployment guides
- **backup/** - Database backup documentation
- **status/** - Current status and change logs
- **code_quality/** - Code review and quality reports

### 🎯 core/
Core bot functionality:
- Bot initialization and command handlers
- Callback query handling
- Premium system management
- Rate limiting and spam protection
- Database operations

### 🔌 services/
External API integrations:
- Portal API (gift marketplace)
- MRKT API (sticker marketplace)
- Stickers.tools API (sticker data)
- CDN server for image hosting

### 🎨 generators/
Price card generation:
- Gift price cards with live data
- Sticker price cards
- Batch generation scripts
- Template-based rendering

### ⏰ schedulers/
Background tasks:
- Database backup to Supabase
- Scheduled maintenance tasks

## File Naming Conventions

### Python Files
- `snake_case.py` - All Python files
- `*_api.py` - API integration modules
- `*_generator.py` - Card generation modules
- `*_handler.py` - Event handler modules

### Documentation
- `UPPERCASE_TITLE.md` - Major documentation
- `lowercase_title.md` - Supporting documentation

### Assets
- `lowercase_name.webp` - Image files (WebP preferred)
- `lowercase_name.svg` - Vector graphics
- `lowercase_name.png` - Fallback images

### Templates & Metadata
- `Gift_Name_template.webp` - Gift templates
- `Gift_Name_metadata.json` - Gift metadata
- `collection_sticker_price_card.webp` - Generated cards

## Important Files

### Configuration
- `.env` - Environment variables (API keys, tokens)
- `core/bot_config.py` - Bot configuration
- `config/paths.py` - Centralized file paths

### Entry Points
- `core/telegram_bot.py` - Main bot entry point
- `quick_start.sh` - Quick start script
- `ecosystem.config.js` - PM2 process manager

### Documentation
- `README.md` - Main project README
- `docs/setup/START_HERE.md` - Getting started guide
- `docs/status/FINAL_STATUS.md` - Current status

## Generated Files (Not in Git)

These directories contain generated content:
- `new_gift_cards/` - Generated gift price cards
- `Sticker_Price_Cards/` - Generated sticker cards
- `logs/` - Log files
- `sqlite_data/` - Database files
- `__pycache__/` - Python cache

## Navigation Tips

### For New Developers
1. Start with `docs/setup/START_HERE.md`
2. Review `docs/analysis/ANALYSIS_INDEX.md`
3. Check `docs/status/FINAL_STATUS.md`

### For Deployment
1. See `docs/setup/PRODUCTION_SETUP.md`
2. Configure `.env` file
3. Run `quick_start.sh`

### For Troubleshooting
1. Check `logs/bot.log`
2. Review `docs/code_quality/`
3. See `docs/analysis/` for technical details

## Maintenance

### Keep It Clean
- Use `logs/` for all log files
- Put docs in `docs/` with proper category
- Remove temporary files after use
- Update `.gitignore` for new file types

### Regular Tasks
```bash
# Clean Python cache
find . -type d -name "__pycache__" -exec rm -rf {} +

# Move logs
mv *.log logs/ 2>/dev/null

# Check for ghost files
find . -name "*_old.py" -o -name "*_backup.py"
```

## Statistics

- **Total Python Files**: ~50
- **Documentation Files**: 39
- **Gift Templates**: 93
- **Sticker Collections**: 218
- **Generated Cards**: 320+ (102 gifts + 218 stickers)
- **Lines of Code**: ~15,000+

## Version Control

### Tracked Files
- Source code (`.py`)
- Configuration templates
- Documentation (`.md`)
- Assets (images, fonts)
- Templates and metadata

### Ignored Files
- Generated cards
- Log files
- Database files
- Python cache
- Environment variables
- Auth tokens

See `.gitignore` for complete list.
