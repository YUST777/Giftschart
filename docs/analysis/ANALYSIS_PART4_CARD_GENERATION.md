# Part 4: Card Generation System

## 🎨 GIFT CARD GENERATOR (gift_card_generator.py - 1,946 lines)

### Generation Process:

1. **Fetch Gift Data**
   ```python
   # Portal API (primary)
   results = await portal_search(
       gift_name=gift_name,
       authData=auth_token,
       sort="price_asc",
       limit=5
   )
   ```

2. **Load Template & Metadata**
   ```python
   template_path = f"card_templates/{Gift_Name}_template.png"
   metadata_path = f"card_metadata/{Gift_Name}_metadata.json"
   ```

3. **Generate Background**
   ```python
   def apply_color_to_background(background_img, color):
       # Creates radial gradient
       # Darker edges → Base color → Accent → Lighter center
       # 40 steps for smooth transition
   ```

4. **Overlay Elements**
   - Gift image (webp format)
   - Price in TON
   - Price in USD
   - Supply count
   - TON logo
   - Star logo

5. **Save Output**
   ```python
   output_path = f"new_gift_cards/{Gift_Name}_card.webp"
   ```

### Color System:

```python
def get_dominant_color(image_path):
    # Extract dominant color from gift image
    # Remove transparent pixels
    # Enhance saturation by 50%
    # Return RGB tuple
```

### Gradient Algorithm:
```python
# Multi-point gradient
if factor < 0.25:  # Outer 25%
    darker_color → base_color
elif factor < 0.5:  # Next 25%
    base_color → accent_color
else:  # Inner 50%
    accent_color → lighter_color
```

### Font System:
```python
MAIN_FONT_PATH = "assets/fonts/Typekiln - EloquiaDisplay-ExtraBold.otf"
```

## 📅 PREGENERATION SCHEDULER

### Schedule:
```python
schedule.every(35).minutes.do(main)
```

### Process:
1. Read all_gift_names.txt (77+ gifts)
2. For each gift:
   - Fetch latest Portal API data
   - Generate card with current prices
   - Save to new_gift_cards/
3. Update last_generation_time.txt
4. Log results

### Timestamp Check:
```python
if elapsed_minutes > 32:
    # Trigger regeneration
    subprocess.Popen([sys.executable, "pregenerate_gift_cards.py"])
```
