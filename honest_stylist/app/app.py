"""
HONEST STYLIST
A brutally honest fashion advisor

STRATEGY:
- Most fashion tech optimizes for selling more clothes
- Honest Stylist optimizes for helping users avoid bad purchases
- Reduce returns through honest, anatomy-aware feedback before checkout

HYPOTHESIS:
- If users receive honest, anatomy-aware styling feedback before purchase,
  they will trust the platform more and make better decisions

FLOW:
1. Upload photo (face + shoulders)
2. Select or upload garment
3. Click "Be Honest"
4. Get verdict + explanation + actionable pivot
"""

import streamlit as st
import os
from pathlib import Path
from PIL import Image
import tempfile
import uuid
import warnings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("honest_stylist.app")

warnings.filterwarnings('ignore')

from agents import PhotoAnalysisAgent, GarmentSelectionAgent, VerdictAgent, PivotAgent
from garment_image_analyzer import GarmentImageAnalyzer

st.set_page_config(
    page_title="Honest Stylist",
    page_icon="👔",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
    .verdict-works {
        background-color: #d4edda;
        border-left: 5px solid #28a745;
        padding: 15px;
        border-radius: 4px;
        color: #155724;
    }
    .verdict-risky {
        background-color: #fff3cd;
        border-left: 5px solid #ffc107;
        padding: 15px;
        border-radius: 4px;
        color: #856404;
    }
    .verdict-dont-buy {
        background-color: #f8d7da;
        border-left: 5px solid #dc3545;
        padding: 15px;
        border-radius: 4px;
        color: #721c24;
    }
    </style>
""", unsafe_allow_html=True)

st.title("👔 Honest Stylist")
st.subheader("Get brutally honest styling advice in seconds")
st.markdown("""
**Most fashion tech optimizes for selling more clothes.**  
**We optimize for helping you avoid bad purchases.**

Get anatomy-aware feedback on whether a piece actually suits you—before checkout.
""")
st.divider()

with st.sidebar:
    st.header("Setup")

    uploaded_photo = st.file_uploader(
        "1️⃣ Upload your photo (upper body or face)",
        type=["jpg", "jpeg", "png"],
        key="photo_upload",
        accept_multiple_files=False,
        help="Only .jpg, .jpeg, .png files up to 5MB are accepted."
    )
    temp_path = None
    if uploaded_photo is not None:
        if uploaded_photo.size > 5 * 1024 * 1024:
            st.error("❌ File too large. Please upload an image under 5MB.")
            uploaded_photo = None
        else:
            temp_dir = tempfile.gettempdir()
            unique_photo_name = f"{uuid.uuid4()}_{uploaded_photo.name}"
            temp_path = os.path.join(temp_dir, unique_photo_name)
            with open(temp_path, "wb") as f:
                f.write(uploaded_photo.getbuffer())

    manual_body_shape = st.selectbox(
        "Select your body shape (for more honest results):",
        ["Inverted Triangle", "Pear", "Rectangle", "Hourglass", "Apple"],
        index=2
    )

    # CHANGE: Removed manual skin season selector (for demo/testing) as per request

    st.divider()

    garment_source = st.radio(
        "2️⃣ How to evaluate a garment:",
        ["From catalog", "Upload your own"],
        horizontal=False
    )

    selected_sku = None
    garment = None
    garment_image_path = None

    catalog_path = os.path.join(os.path.dirname(__file__), "garment_catalog.json")
    garment_agent = GarmentSelectionAgent(catalog_path)

    if garment_source == "From catalog":
        garment_options = garment_agent.get_options()
        selected_garment_display = st.selectbox(
            "Pick a garment:",
            options=garment_options,
            format_func=lambda x: x[1]
        )
        if selected_garment_display:
            selected_sku = selected_garment_display[0]
            garment = garment_agent.get_garment(selected_sku)
    else:
        uploaded_garment = st.file_uploader(
            "Upload garment image (flat lay or product photo)",
            type=["jpg", "jpeg", "png"],
            key="garment_upload",
            accept_multiple_files=False,
            help="Only .jpg, .jpeg, .png files up to 5MB are accepted."
        )
        if uploaded_garment is not None:
            if uploaded_garment.size > 5 * 1024 * 1024:
                st.error("❌ File too large. Please upload an image under 5MB.")
                uploaded_garment = None
            else:
                temp_dir = tempfile.gettempdir()
                unique_garment_name = f"{uuid.uuid4()}_{uploaded_garment.name}"
                garment_image_path = os.path.join(temp_dir, unique_garment_name)
                with open(garment_image_path, "wb") as f:
                    f.write(uploaded_garment.getbuffer())
                st.image(uploaded_garment, width=150, caption="Uploaded garment image", output_format="PNG")

    st.divider()
    analyze_clicked = st.button(
        "🔥 Be Honest",
        use_container_width=True,
        type="primary"
    )

if analyze_clicked:
    if temp_path is None:
        st.error("❌ Please upload a photo first")
    elif garment_source == "From catalog" and selected_sku is None:
        st.error("❌ Please select a garment from the catalog")
    elif garment_source == "Upload your own" and garment_image_path is None:
        st.error("❌ Please upload a garment image")
    else:
        with st.spinner("Analyzing your style..."):
            try:
                photo_agent = PhotoAnalysisAgent()
                try:
                    user_profile = photo_agent.analyze(temp_path)
                except Exception as e:
                    logger.error(f"Photo analysis failed: {e}")
                    st.error("❌ Failed to analyze photo. Please try another image.")
                    st.stop()
                user_profile["body_shape"] = manual_body_shape
                st.write("User profile (debug):", user_profile)


                if garment_source == "From catalog":
                    pass
                else:
                    garment_analyzer = GarmentImageAnalyzer()
                    try:
                        garment_analysis = garment_analyzer.analyze_garment_image(garment_image_path)
                    except Exception as e:
                        logger.error(f"Garment analysis failed: {e}")
                        st.error("❌ Failed to analyze garment image. Please try another image.")
                        st.stop()
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        silhouette = st.selectbox("How does it fit?", ["fitted", "oversized", "straight"])
                    with col2:
                        shoulder_emphasis = st.selectbox("Shoulder detail?", ["low", "medium", "high"])
                    with col3:
                        visual_weight = st.selectbox("How heavy does it feel?", ["light", "medium", "heavy"])
                    possible_seasons = garment_analyzer.map_color_to_season(
                        garment_analysis["color_family"], garment_analysis["brightness"])
                    garment = {
                        "name": f"Your {garment_analysis['color_hex']} garment",
                        "color_name": garment_analysis["color_hex"],
                        "color_season": possible_seasons,
                        "silhouette": silhouette,
                        "shoulder_emphasis": shoulder_emphasis,
                        "visual_weight": visual_weight,
                        "neckline": "unknown",
                        "brightness": garment_analysis["brightness"]
                    }
                    st.write("Garment analysis (debug):", garment_analysis)

                verdict_agent = VerdictAgent()
                try:
                    rule_result = verdict_agent.score(user_profile, garment)
                except Exception as e:
                    logger.error(f"Verdict scoring failed: {e}")
                    st.error("❌ Failed to score verdict. Please try again.")
                    st.stop()
                percentage = min(95, max(0, rule_result['score']))

                # CHANGE: Always attempt GenAI (Gemini) for explanation if API key is set
                pivot_agent = PivotAgent()
                try:
                    explanation = pivot_agent.suggest(
                        verdict=rule_result["verdict"],
                        user_profile=user_profile,
                        garment=garment,
                        reasons=rule_result["reasons"],
                        score=percentage
                    )
                except Exception as e:
                    logger.error(f"Pivot suggestion failed: {e}")
                    explanation = None


                st.markdown("---")
                if percentage >= 80:
                    verdict_class = "verdict-works"
                    verdict_text = "This actually suits you — here's why it doesn't fail."
                    icon = "✅"
                elif percentage >= 50:
                    verdict_class = "verdict-risky"
                    verdict_text = "You could wear this, but it won't flatter you."
                    icon = "⚠️"
                else:
                    verdict_class = "verdict-dont-buy"
                    verdict_text = "This almost works — but it fails in one key area."
                    icon = "❌"
                st.markdown(
                    f"""<div class="{verdict_class}" role="status" aria-live="polite"><h2>{icon} {verdict_text}</h2><h1 style='color: inherit; margin-top: 10px;'>{percentage}%</h1></div>""",
                    unsafe_allow_html=True
                )

                st.markdown("---")
                st.markdown("### Why? (Penalties applied)")
                if rule_result["reasons"]:
                    for reason in rule_result["reasons"]:
                        if reason["penalty"] < 0:
                            st.success(f"✓ {reason['text']}")
                        else:
                            st.warning(f"✗ {reason['text']} (–{reason['penalty']} pts)")
                else:
                    st.success("✓ No conflicts — this works well with your profile.")

                st.markdown("---")
                st.markdown("### Try This Instead")
                # CHANGE: Show GenAI (Gemini) output if available, else fallback
                if explanation and "pivot_suggestion" in explanation:
                    st.info(f"💡 **{explanation['pivot_suggestion']}**\n\n{explanation['pivot_reason']}")
                else:
                    from rule_engine import StylingAnalyzer
                    analyzer = StylingAnalyzer()
                    pivot = analyzer.generate_pivot_suggestion(user_profile, garment)
                    st.info(f"💡 {pivot}")


                st.markdown("---")
                st.markdown("### Visual Comparison")
                col1, col2 = st.columns(2)
                with col1:
                    try:
                        st.image(Image.open(temp_path), width=350, caption="Your uploaded photo", output_format="PNG")
                    except Exception as e:
                        logger.warning(f"Failed to display user photo: {e}")
                        st.warning("Could not display your photo.")
                    st.caption(f"**Your Style:**\n{user_profile['skin_season']} | {user_profile['body_shape']}")
                with col2:
                    if garment_source == "Upload your own" and garment_image_path:
                        try:
                            st.image(garment_image_path, width=350, caption="Garment image", output_format="PNG")
                        except Exception as e:
                            logger.warning(f"Failed to display garment image: {e}")
                            st.warning("Could not display garment image.")
                    else:
                        st.write(f"**{garment['name']}**")
                        st.write(f"Color: {garment['color_name']}")
                        st.write(f"Silhouette: {garment['silhouette'].title()}")
                        st.write(f"For: {', '.join(garment['color_season'])}")
                    st.caption(f"**Garment:**\n{garment.get('silhouette', 'N/A')} | {garment.get('shoulder_emphasis', 'N/A')} shoulders")

                with st.expander("📊 How I judged this"):
                    st.write(f"**Base Score:** 100/100")
                    st.write(f"**Final Score:** {rule_result['score']}/100 ({percentage}%)")
                    if rule_result["reasons"]:
                        st.write("**Penalties Applied:**")
                        for reason in rule_result["reasons"]:
                            st.write(f"• {reason['text']}")
                            st.write(f"  *(–{reason['penalty']} points)*")
            except Exception as e:
                import traceback
                logger.critical(f"Unhandled error: {e}")
                st.error(f"❌ Error analyzing your photo or garment. Details: {e}")
                st.code(traceback.format_exc())

else:
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        ### How it works:
        
        1. **Upload** your photo (face + shoulders visible)
        2. **Pick** a garment from our catalog
        3. **Get honest feedback** about whether it suits you
        
        We analyze:
        - Your skin tone & undertone
        - Your body shape
        - Color harmony
        - Silhouette balance
        
        Then we tell you the TRUTH—not what you want to hear.
        """)
    with col2:
        st.markdown("""
        ### What you get:
        
        ✅ **Direct verdict**: Works, Risky, or Don't Buy
        
        💭 **Honest reasons**: Why it works or doesn't
        
        🎯 **Pivot suggestion**: What to try instead
        
        No BS. No upselling. Just truth.
        """)