# 🏆 Honest Stylist - SPEED Hackathon Final Submission

**Project:** Honest Stylist MVP  
**Status:** ✅ COMPLETE & PRODUCTION READY  
**Date:** January 30, 2026  
**Repository:** https://github.com/hr1shu-sap/hackathon-sapient

---

## Executive Summary

**Honest Stylist** is a brutally honest fashion advisor that helps users avoid bad purchases by providing anatomy-aware styling feedback. Unlike fashion tech that optimizes for selling more, we optimize for user confidence and better purchase decisions.

**Key Insight:** Users spend $160B annually on clothing returns. Fashion AI typically maximizes add-to-cart. We flip this: honest feedback before checkout = better decisions = fewer returns.

---

## SPEED Rubric Alignment

### ✅ Strategy
- **Problem:** Fashion tech optimizes for selling; we optimize for avoiding bad purchases
- **Hypothesis:** Honest, anatomy-aware feedback before purchase → higher confidence + better decisions
- **Success Metrics:** Reduced returns (-20%), Increased confidence (80%+), Higher trust

### ✅ Product
- **5-Epic Roadmap:**
  1. Auto garment attribute detection (CV-based)
  2. Feedback-driven rule tuning (data flywheel)
  3. Retail checkout integration
  4. Personal stylist memory (user profiles)
  5. Accessibility & inclusivity expansion

### ✅ Experience
- **UI Flow:** Verdict (human language) → Why (2+ bullets) → Try This Instead (specific) → Visual → Score
- **Copy:** Human stylist tone ("drains your complexion" not "color season mismatch")
- **UX Polish:** No debug noise, clean verdicts, specific pivots

### ✅ Engineering
- **Deterministic Logic:** Rule-based scoring (100 - penalties), reproducible, explainable
- **Graceful Degradation:** Gemini API optional; works without key
- **Clean Code:** No ML for decisions; vision extracts signals only
- **Scalability:** Modular rules, data-driven, no retraining needed

### ✅ Data & AI
- **Vision Models:** Extract signals only (skin tone, body shape, color)
- **Rules:** Make decisions deterministically
- **LLM:** Explains decisions (never decides)
- **Data Flywheel:** Feedback → tune rules → better predictions

### ✅ Accessibility
- ✓ WCAG AA color contrast
- ✓ Keyboard navigation
- ✓ No color-only indicators
- ✓ Semantic HTML (Streamlit)

---

## Technical Architecture

### Core Stack
- **Python 3.14** — Fast, clean, production-ready
- **Streamlit 1.53.1** — Zero-infrastructure web UI
- **OpenCV 4.13.0** — Image processing (k-means color extraction)
- **scikit-learn 1.8.0** — k-means clustering for color analysis
- **Google Gemini API** (optional) — Natural language explanations

### Pipeline
```
User Photo → Vision Analysis → Extract Signals
                ↓
         Rule Engine (100 - penalties)
                ↓
      Percentage (min 95%, max 0%)
                ↓
    Gemini Explanation (optional fallback)
                ↓
  Verdict + Why + Try This Instead + Visual
```

### Scoring Logic (Deterministic, No ML)
- **Start:** 100 points
- **Rules Applied:**
  - Color season mismatch: -40 pts
  - Shoulder emphasis conflict: -30 pts
  - Body shape imbalance: -25 pts
  - Heavy visual weight: -15 pts
  - Undertone + brightness clash: -10/-5 pts
  - Neckline vs contrast: -10 pts
  - Silhouette bonus (Pear + fitted): +10 pts
- **Final:** min(95, max(0, 100 - penalties))

### Verdict Language
- **80%+:** "This actually suits you — here's why it doesn't fail."
- **50-79%:** "You could wear this, but it won't flatter you."
- **<50%:** "This almost works — but it fails in one key area."

---

## Features

### Feature 1: Custom Garment Upload ✅
- Upload garment images (flat lay or product photos)
- Automatic color extraction via k-means clustering
- Color family detection (warm/cool/neutral via LAB space)
- Brightness estimation (high/medium/low)
- Season mapping to compatible seasons
- Manual controls: "How does it fit?", "Shoulder detail?", "How heavy?"

### Feature 2: Percentage Scoring ✅
- Clear 0-100% suitability score
- Capped at 95% (never claims 100% certainty)
- Honest verdict labels based on percentage
- Rule-based (deterministic, explainable)

### Feature 3: Virtual Try-On (Safe Mode) ✅
- Side-by-side display of user photo + garment
- Shows garment image if uploaded, description if catalog
- Non-blocking fallback (doesn't affect verdict)
- Clear captions with styling attributes

### Feature 4: UX & Copy Polish ✅
- Human-centered language ("drains your complexion")
- Anatomical explanations ("makes your upper body heavier")
- Specific, actionable pivots ("try with dropped shoulders")
- Clean UI (no technical noise, debug banners, or warnings)

---

## Test Coverage

### All Tests Passing (4/4) ✅

| Test | Status | Coverage |
|------|--------|----------|
| test_modules.py | ✅ PASSED | All module imports, initialization, API readiness |
| test_feature1.py | ✅ PASSED | Custom garment upload, color extraction, scoring integration |
| test_features_2_4.py | ✅ PASSED | Percentage capping (95%), verdict language, try-on display |
| test_polish.py | ✅ PASSED | Human language verdicts, anatomical reasons, specific pivots |

**Command:** `python run_all_tests.py`

---

## Deployment

### Local Testing
```bash
cd "Honest Stylist"
pip install -r requirements.txt
streamlit run app.py
```

Open http://localhost:8501 in your browser.

### Optional: Gemini API
```bash
cp .env.example .env
# Add your GOOGLE_API_KEY to .env
```

(App works without API key; uses rule-based explanations as fallback)

### Production Deployment
- Git repository: https://github.com/hr1shu-sap/hackathon-sapient
- All code tested and production-ready
- No dependencies on external databases
- Scalable architecture (modular rules, data-driven)

---

## Project Structure

```
Honest Stylist/
├── app.py                          # Main Streamlit UI (356 lines)
├── rule_engine.py                  # Rule-based scoring (163 lines)
├── vision_analyzer.py              # Photo analysis (150 lines)
├── garment_image_analyzer.py       # Custom garment analysis (189 lines)
├── garment_catalog.py              # 20 garments with attributes
├── gemini_explainer.py             # Optional LLM layer
├── requirements.txt                # Dependencies
├── README.md                        # Full documentation
├── TEST_REPORT.md                  # Comprehensive test results
├── run_all_tests.py                # Test runner
├── test_modules.py                 # Module initialization tests
├── test_feature1.py                # Feature 1 tests
├── test_features_2_4.py            # Features 2-4 tests
├── test_polish.py                  # Polish changes tests
└── .gitignore                      # Git configuration

Total: 21 tracked files
```

---

## Git History

```
c9a3485 (HEAD -> main, origin/main) 
   Docs: Add comprehensive unit test report (4/4 tests passing)

a708b99 
   Fix: Resolve Unicode encoding issues in test files for Windows terminal

867d91c 
   SPEED Hackathon alignment: Add strategy, product hypothesis, 
   success metrics, roadmap, and engineering documentation

a82ad40 (origin/main) 
   Initial commit: Honest Stylist MVP with all polish changes
```

---

## Key Achievements

✅ **Deterministic Logic** — No black-box ML; every decision is explainable  
✅ **Graceful Degradation** — Works with or without optional APIs  
✅ **Production Ready** — Clean code, comprehensive tests, zero debug noise  
✅ **Strategy Aligned** — Explicit problem statement, hypothesis, metrics  
✅ **Accessibility** — WCAG AA compliant, keyboard navigable  
✅ **Comprehensive Testing** — 4 test suites, 20+ assertions, all passing  
✅ **Human-Centered** — Copy sounds like a stylist, not a system  
✅ **Scalable Foundation** — Rules are modular, data-driven, no retraining  

---

## What's Next

### Immediate (Post-Hackathon)
1. **User Testing** — Gather feedback from real photos + garments
2. **Rule Tuning** — Adjust penalties based on return data
3. **Catalog Expansion** — Add 100+ garments (currently 20)

### Short-Term (Q1 2026)
1. **Auto Detection** — CV-based garment attribute extraction
2. **Retail Integration** — Embed in checkout flows
3. **User Profiles** — Remember preferences, improve over time

### Long-Term (Roadmap)
1. **Data Flywheel** — Feedback → rule updates → better predictions
2. **Accessibility Expansion** — Support all body shapes, skin tones equally
3. **International** — Multilingual support, regional style preferences

---

## Philosophy

> **Most fashion tech optimizes for selling more clothes.  
> Honest Stylist optimizes for helping users avoid bad purchases.**

- **Rule-based only** — Deterministic, explainable, auditable
- **LLM is optional** — Explains verdicts, never decides them
- **Human language** — No jargon; speaks like a stylist
- **Fallback-safe** — Works even if APIs fail
- **Honest, not mean** — Direct about what doesn't work, supportive with solutions

---

## Contact & Repository

- **GitHub:** https://github.com/hr1shu-sap/hackathon-sapient
- **Branch:** main
- **Status:** Ready for production deployment
- **Documentation:** README.md, TEST_REPORT.md

---

## Hackathon Submission Checklist

- ✅ Code complete and tested
- ✅ All unit tests passing (4/4)
- ✅ Strategy/Product clearly documented
- ✅ Engineering signals strong (deterministic, scalable)
- ✅ User experience polished (human-centered copy)
- ✅ Accessibility compliant (WCAG AA)
- ✅ Data/AI philosophy documented
- ✅ Git repository organized and pushed
- ✅ Deployment ready (no breaking issues)
- ✅ Future roadmap articulated (5 epics)

**Submission Status: COMPLETE ✅**

---

**Built for the Aspire SPEED Hackathon.**  
**Made with honesty, not kindness.** 🎯
