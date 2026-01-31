"""
HONEST STYLIST
A brutally honest fashion advisor
Vision → Rules → Explanation → AI Recommendations
"""

import streamlit as st
import os
import tempfile
from PIL import Image
import traceback

# -----------------------------
# Local imports
# -----------------------------
from garment_catalog import (
    #list_garments_display,
    get_garment,
    list_garment_skus,
    get_full_catalog,
    get_full_catalog_display   # <-- make sure this returns raw list of dicts
)
from vision_analyzer import VisionAnalyzer
from rule_engine import StylingAnalyzer
from gemini_explainer import GeminiExplainer
from ai_recommender import AIRecommender


# -----------------------------
# Page config
# -----------------------------
st.set_page_config(
    page_title="Honest Stylist",
    page_icon="👔",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# -----------------------------
# Styles
# -----------------------------
st.markdown(
    """
<style>
.verdict-works {
    background-color: #d4edda;
    border-left: 5px solid #28a745;
    padding: 15px;
    border-radius: 6px;
}
.verdict-risky {
    background-color: #fff3cd;
    border-left: 5px solid #ffc107;
    padding: 15px;
    border-radius: 6px;
}
.verdict-dont-buy {
    background-color: #f8d7da;
    border-left: 5px solid #dc3545;
    padding: 15px;
    border-radius: 6px;
}
</style>
""",
    unsafe_allow_html=True,
)

# -----------------------------
# Header
# -----------------------------
st.title("👔 Honest Stylist")
st.subheader("Not a hype machine. A stylist who tells the truth.")

# -----------------------------
# Sidebar
# -----------------------------
with st.sidebar:
    st.header("Setup")

    uploaded_photo = st.file_uploader(
        "Upload a full-body photo",
        type=["jpg", "jpeg", "png"],
    )

    # Use the updated catalog API
    garment_options = get_full_catalog_display()
    selected_garment_display = st.selectbox(
        "Pick a garment to evaluate",
        options=garment_options,
        # support both (sku,name) tuples and dict entries for future-proofing
        format_func=lambda x: x[1] if isinstance(x, (list, tuple)) else x.get("name", str(x)),
    )

    analyze_clicked = st.button(
        "🔥 Be Honest",
        use_container_width=True,
        type="primary",
    )

# -----------------------------
# Main logic
# -----------------------------
if analyze_clicked:

    if uploaded_photo is None:
        st.error("Please upload a photo.")
        st.stop()

    if not selected_garment_display:
        st.error("Please select a garment.")
        st.stop()

    selected_sku = selected_garment_display[0]
    garment = get_garment(selected_sku)

    # Save uploaded image temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
        tmp.write(uploaded_photo.getbuffer())
        image_path = tmp.name

    try:
        with st.spinner("Analyzing your style honestly…"):

            # -----------------------------
            # 1. Vision
            # -----------------------------
            vision = VisionAnalyzer()
            user_profile = vision.analyze_photo(image_path)

            # Backward compatibility (if anything expects this)
            user_profile["skin_season"] = user_profile.get("season")

            # -----------------------------
            # 2. Rules
            # -----------------------------
            analyzer = StylingAnalyzer()
            rule_result = analyzer.analyze(user_profile, garment)

            # Defensive check: ensure the rule engine returned expected fields
            if not isinstance(rule_result, dict) or "verdict" not in rule_result:
                st.warning("Rule engine returned unexpected result; using fallback verdict.")
                rule_result = {
                    "score": 0,
                    "verdict": "Analysis failed",
                    "reasons": [{"text": "Rule engine error or invalid output", "penalty": 0}],
                }
            # -----------------------------
            # 3. Gemini explanation (optional)
            # -----------------------------
            api_key = os.getenv("GOOGLE_API_KEY")
            explainer = None
            explanation = None

            if api_key:
                explainer = GeminiExplainer(api_key)
                explanation = explainer.explain_verdict(
                    verdict=rule_result["verdict"],
                    user_profile=user_profile,
                    garment=garment,
                    rule_reasons=rule_result["reasons"],
                    score=rule_result["score"],
                )

            # -----------------------------
            # 4. AI Recommendations (NEW)
            # -----------------------------
            recommender = AIRecommender(gemini_client=explainer)
            catalog = get_full_catalog()

            recommendations = recommender.recommend(
                user_profile=user_profile,
                current_garment=garment,
                catalog=catalog,
                rule_result=rule_result,
                top_k=3,
            )

        # -----------------------------
        # DISPLAY
        # -----------------------------
        st.markdown("---")
        st.markdown("## 📊 Verdict")

        score = rule_result["score"]
        if score >= 75:
            v_class = "verdict-works"
        elif score >= 40:
            v_class = "verdict-risky"
        else:
            v_class = "verdict-dont-buy"

        st.markdown(
            f'<div class="{v_class}"><h3>{rule_result["verdict"]} — {score}/100</h3></div>',
            unsafe_allow_html=True,
        )

        # -----------------------------
        # Image + garment
        # -----------------------------
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("You")
            st.image(Image.open(image_path), use_column_width=True)

            bp = user_profile["body_profile"]
            st.caption(
                f"""
**Season:** {user_profile['season']}  
**Contrast:** {user_profile['contrast']}  
**Silhouette balance:** {bp['shape']}  
**Analysis confidence:** {round(user_profile['confidence'], 2)}
"""
            )

        with col2:
            st.subheader(garment["name"])
            st.write(f"**Color:** {garment['color_name']}")
            st.write(f"**Silhouette:** {garment['silhouette']}")
            st.write(f"**Best for:** {', '.join(garment['color_season'])}")

        # -----------------------------
        # WHY
        # -----------------------------
        st.markdown("---")
        st.markdown("## 💬 Why this verdict")

        if explanation:
            st.write(explanation["why_verdict"])
        else:
            for r in rule_result["reasons"]:
                if r["penalty"] < 0:
                    st.success(r["text"])
                else:
                    st.error(r["text"])

        # -----------------------------
        # AI Recommendations
        # -----------------------------
        if recommendations:
            st.markdown("---")
            st.markdown("## 🛍️ Better picks for you")

            for rec in recommendations:
                st.markdown(
                    f"""
**{rec['name']}**  
_Why_: {rec['reason']}
"""
                )

        else:
            st.markdown("---")
            st.markdown("## 🛍️ No better alternatives needed")
            st.write("This piece already works well for your profile.")

        # -----------------------------
        # Debug (optional)
        # -----------------------------
        with st.expander("🧪 Debug details"):
            st.write("User profile:", user_profile)
            st.write("Rule result:", rule_result)

    except Exception as e:
        st.error("Something went wrong during analysis.")
        st.expander("Traceback").code(traceback.format_exc())

    finally:
        if os.path.exists(image_path):
            os.remove(image_path)

# -----------------------------
# Landing
# -----------------------------
else:
    st.markdown(
        """
### How Honest Stylist works

1. Upload a real photo (no filters, no poses)
2. Pick a garment from our catalog
3. Get an honest verdict — and better alternatives if needed

We don’t flatter.  
We don’t upsell.  
We help you buy **what actually works**.
"""
    )