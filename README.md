# 👔 Honest Stylist

A brutally honest fashion advisor that analyzes your photo and tells you whether a garment actually suits you—no sugar-coating.

## How It Works

1. **Upload your photo** (face + upper body)
2. **Select or upload a garment** (from catalog or custom image)
3. **Get honest feedback** about suitability

The app analyzes:
- Your skin tone & undertone
- Your body shape & proportions
- Color harmony & contrast
- Silhouette balance

## Verdict Scale

- **✅ 80%+** — "This actually suits you — here's why it doesn't fail."
- **⚠️ 50-79%** — "You could wear this, but it won't flatter you."
- **❌ <50%** — "This almost works — but it fails in one key area."

## Tech Stack

- **Python 3.14**
- **Streamlit** — Web UI
- **OpenCV** — Image processing
- **scikit-learn** — Color analysis (k-means clustering)
- **Google Gemini API** (optional) — Human-friendly explanations

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up API Key (Optional)

Get your Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey)

```bash
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY
```

### 3. Run the App

```bash
streamlit run app.py
```

Open http://localhost:8501 in your browser.

## Features

### Feature 1: Custom Garment Upload
Upload your own garment images. The app automatically extracts color, brightness, and maps to compatible color seasons.

**Manual controls:**
- "How does it fit?" → Silhouette (fitted, oversized, straight)
- "Shoulder detail?" → Shoulder emphasis (low, medium, high)
- "How heavy does it feel?" → Visual weight (light, medium, heavy)

### Feature 2: Percentage Scoring
Clear suitability percentage (0-100%, capped at 95%) with honest verdict language.

### Feature 3: Virtual Try-On
Side-by-side comparison of your photo and the garment.

### Feature 4: Honest Copy & UX
- Human-centered language ("drains your complexion" not "color mismatch")
- Anatomical explanations ("makes your upper body look heavier")
- Specific actionable pivots ("try with dropped shoulders")
- Clean UI with no technical noise

## Core Algorithm

### Scoring (Rule-Based)

Starts at 100 points, applies penalties:

| Rule | Penalty | Trigger |
|------|---------|---------|
| Color season mismatch | -40 | Wrong season for skin tone |
| Shoulder emphasis conflict | -30 | Inverted Triangle + high shoulders |
| Body imbalance | -25 | Pear + low shoulder emphasis |
| Heavy visual weight | -15 | Rectangle + heavy fabric |
| Undertone + brightness | -10/-5 | Cool skin + very bright color |
| Neckline vs contrast | -10 | Low contrast + turtleneck |
| **Silhouette bonus** | **+10** | **Pear + fitted top** |

**Final Score = min(95, max(0, 100 - penalties))**

### Color Analysis

1. **Skin tone extraction** — K-means clustering on face
2. **Undertone detection** — LAB color space analysis
3. **Contrast calculation** — Brightness bucketing
4. **Season mapping** — Undertone + contrast → color season

### Garment Analysis

1. **Dominant color extraction** — K-means on non-background pixels
2. **Color family detection** — LAB-based warm/cool/neutral
3. **Brightness estimation** — LAB L value mapping
4. **Season compatibility** — Color + brightness → seasons

## Project Structure

```
Honest Stylist/
├── app.py                      # Main Streamlit UI
├── garment_catalog.py          # Garment database (20 items)
├── rule_engine.py              # Rule-based scoring
├── vision_analyzer.py          # User photo analysis
├── garment_image_analyzer.py   # Custom garment analysis
├── gemini_explainer.py         # Optional LLM layer
├── README.md                   # This file
├── .gitignore                  # Git ignore rules
└── test_*.py                   # Test suites
```

## Testing

```bash
python test_feature1.py        # Custom garment upload
python test_features_2_4.py    # Percentage & UI
python test_polish.py          # Verdict language
```

## Philosophy

- **Rule-based only** — No ML models for verdicts (deterministic, explainable)
- **LLM is optional** — Explains verdicts, never decides them
- **Human language** — No jargon, speaks like a stylist
- **Fallback-safe** — Works even if APIs fail
- **Honest, not mean** — Direct about what doesn't work, supportive with solutions

## Garment Catalog

20+ items with attributes: color, season, silhouette, shoulder emphasis, visual weight, etc.

## Future Enhancements

- [ ] Larger garment catalog (100+)
- [ ] User profiles and history
- [ ] Wardrobe compatibility analysis
- [ ] Advanced color space mapping
- [ ] ML-based body shape detection

---

**Made with honesty, not kindness.** 🚀
