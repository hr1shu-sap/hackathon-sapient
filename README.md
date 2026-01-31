# Honest Stylist - MVP

A brutally honest fashion advisor powered by vision AI + styling rules + LLM explanations.

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up API Key

Get your Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey)

```bash
# Copy .env.example to .env
cp .env.example .env

# Edit .env and paste your key
# GOOGLE_API_KEY=abc123...
```

### 3. Run the App

```bash
streamlit run app.py
```

Open http://localhost:8501 in your browser.

## How It Works

### User Flow

1. Upload a photo (face + shoulders visible)
2. Select a garment from the catalog
3. Click "Be Honest"
4. Get verdict + explanation + pivot suggestion

### Architecture

```
Photo Upload
    ↓
Vision Analysis (MediaPipe)
    ├─ Face detection → Skin tone extraction
    ├─ Pose detection → (optional pose features)
    └─ Contrast calculation
    ↓
Rule Engine
    ├─ Color season matching
    ├─ Silhouette rules
    ├─ Visual weight rules
    └─ Generate penalties/bonuses
    ↓
Gemini LLM (optional)
    ├─ Explain verdict
    ├─ Suggest pivot
    └─ Generate honest reasons
    ↓
User-Friendly Output
    ├─ Verdict (Works/Risky/Don't Buy)
    ├─ Why (rules applied)
    └─ Pivot (what to try instead)
```

## Components

### `garment_catalog.py`
- Hardcoded catalog of 20+ garments
- Each with: color, season, silhouette, shoulder emphasis, weight

### `vision_analyzer.py`
- MediaPipe face detection → skin tone extraction
- LAB color space analysis for undertone detection
- Maps to 4 color seasons (Deep Winter, Cool Winter, Light Spring, Soft Autumn)

### `rule_engine.py`
- Penalty-based scoring system (0-100)
- Rules for color matching and silhouette balance
- Generates rule reasons for transparency

### `gemini_explainer.py`
- Calls Gemini 1.5 Flash to explain verdicts
- Never decides verdict (rules only)
- Generates pivot suggestions
- Tone: honest, direct, no BS

### `app.py`
- Streamlit UI
- Orchestrates the full pipeline
- Displays results with visual feedback

## Features

✅ **Vision Analysis**
- Skin tone detection via k-means clustering
- Undertone determination (warm, cool, neutral)
- Contrast level calculation

✅ **Rule Engine**
- Color season matching (-40 if wrong season)
- Body shape + silhouette balance (-30 for inverted triangle + high shoulder emphasis)
- Visual weight considerations
- Undertone + brightness harmony

✅ **LLM Integration** (Optional)
- Gemini generates honest explanations
- Suggests specific pivot garments
- Never breaks—falls back to rule-based explanations

✅ **User Interface**
- Simple sidebar for uploads/selection
- Visual verdict indicators (green/yellow/red)
- Score breakdown for transparency
- Mobile-friendly

## Rules Applied

### Color Season (Rule 1)
If user's season ≠ garment season → **-40 points**

### Silhouette + Shoulder Emphasis (Rule 2)
- High shoulder emphasis on broad-shouldered silhouettes → **-30 points**
- Low shoulder emphasis on bottom-heavy silhouettes → **-25 points** (reduces balance)

### Visual Weight (Rule 3)
Heavy pieces on balanced silhouettes → **-15 points**

### Undertone + Brightness (Rule 4)
- Cool undertone + Very bright → **-10 points**
- Warm undertone + Very bright → **-5 points** (minor)

### Neckline + Contrast (Rule 5)
Low contrast face + Turtleneck → **-10 points** (overpowering)

### Silhouette Bonus (Rule 6)
Fitted top on bottom-heavy silhouettes → **+10 points** (balancing)

## Scoring

- **≥ 60**: Works ✅
- **40-59**: Risky ⚠️
- **< 40**: Don't Buy ❌

## Garment Catalog

20+ items including:
- Crisp White T-Shirt (Cool Winter, Light Spring)
- Camel Oversized Sweater (Soft Autumn, Light Spring)
- Black Turtleneck (Deep Winter, Cool Winter)
- Coral Crop Top (Light Spring, Soft Autumn)
- Navy Striped Shirt (Cool Winter, Deep Winter)
- And more...

## Fallbacks & Safety

✅ If face not detected → Use neutral defaults
✅ If pose not detected → Use pose fallback defaults
✅ If Gemini API fails → Show rule-based explanation
✅ If no rules match → Show generic positive feedback

## Known Limitations

- Photo must show face + shoulders clearly
- Silhouette estimation is approximate
- Color season mapping is simplified (4 categories)
- Garment catalog is hardcoded (no training/updates)
- VTON (virtual try-on) not included in MVP

## Next Steps (Post-MVP)

1. Add more garments to catalog (100+)
2. Implement VTON for visual preview
3. Add user feedback loop (thumbs up/down on verdicts)
4. Build admin panel for catalog management
5. Add before/after photos for pivot suggestions
6. Implement user profiles for future comparisons

## Testing

Try these combinations:

**Should work:** Cool Winter + Navy Striped Shirt
**Should be risky:** High shoulder emphasis + Coral Crop Top
**Should fail:** Oversized with low shoulders

## Support

For issues:
1. Check photo shows face + shoulders
2. Verify API key is set in .env
3. Check console logs for error details
4. Try different photo angles/lighting

---

**Built for a 48-hour hackathon. Simple > Perfect.** 🚀
