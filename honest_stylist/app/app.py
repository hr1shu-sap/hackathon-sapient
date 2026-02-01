"""
HONEST STYLIST
Unified: Agentic AI (RLHF), Batch, and Classic Honest Stylist
"""

import streamlit as st
import os
import tempfile
import uuid
import warnings
import logging
from pathlib import Path
from PIL import Image

# --- AGENTIC AI & RLHF imports ---
try:
    from garment_catalog import (
        get_garment,
        get_full_catalog,
        get_full_catalog_display,
        list_garments_display,
    )
except ImportError:
    from garment_catalog import (
        get_garment,
        list_garments_display,
    )
from vision_analyzer import VisionAnalyzer
from rule_engine import StylingAnalyzer
from gemini_explainer import GeminiExplainer

# Optional/conditional imports for agentic mode
try:
    from ai_recommender import AIRecommender
    from feedback_logger import FeedbackLogger
except ImportError:
    AIRecommender = None
    FeedbackLogger = None

# Classic agent-based
try:
    from agents import PhotoAnalysisAgent, GarmentSelectionAgent, VerdictAgent, PivotAgent
    from garment_image_analyzer import GarmentImageAnalyzer
except ImportError:
    PhotoAnalysisAgent = None
    GarmentSelectionAgent = None
    VerdictAgent = None
    PivotAgent = None
    GarmentImageAnalyzer = None

warnings.filterwarnings('ignore')
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("honest_stylist.app")

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
    .stMetric { background-color: #f0f2f6; padding: 10px; border-radius: 10px; }
    </style>
""", unsafe_allow_html=True)

# --- MODE SELECTION ---
mode = st.radio(
    "Choose Mode:",
    [
        "Agentic AI (RLHF, Recommendations, Feedback)",
        "Batch Analysis (Multi-photo, Classic Verdicts)",
        "Classic Honest Stylist (Single, Catalog/Upload)"
    ],
    horizontal=False
)
st.divider()

# --- AGENTIC AI (RLHF, Recommendations, Feedback) ---
if mode == "Agentic AI (RLHF, Recommendations, Feedback)":
    st.title("👔 Honest Stylist")
    st.subheader("A brutally honest AI stylist that learns from you")

    # --- SESSION STATE ---
    DEFAULTS = {
        "analysis_done": False,
        "agent_state": None,
        "recommendations": None,
        "feedback_submitted": False,
    }
    for k, v in DEFAULTS.items():
        if k not in st.session_state:
            st.session_state[k] = v

    # --- SIDEBAR ---
    with st.sidebar:
        st.header("1️⃣ Upload Photo")
        uploaded_file = st.file_uploader(
            "Upload a full-body or upper-body photo",
            type=["jpg", "jpeg", "png"]
        )

        st.header("2️⃣ Choose Garment")
        garment_options = get_full_catalog_display()
        selected_display = st.selectbox(
            "Pick a garment",
            options=garment_options,
            format_func=lambda x: x[1]
        )
        selected_sku = selected_display[0] if selected_display else None

        run_analysis = st.button("🔥 Analyze Outfit", type="primary")

    # --- ANALYSIS ---
    if run_analysis:
        if not uploaded_file or not selected_sku:
            st.error("Please upload a photo and select a garment.")
            st.stop()

        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            tmp.write(uploaded_file.getbuffer())
            image_path = tmp.name

        vision = VisionAnalyzer()
        analyzer = StylingAnalyzer()
        feedback_logger = FeedbackLogger() if FeedbackLogger else None

        api_key = os.getenv("GOOGLE_API_KEY")
        gemini = GeminiExplainer(api_key) if api_key else None
        recommender = AIRecommender(gemini_client=gemini) if AIRecommender else None

        garment = get_garment(selected_sku)

        with st.spinner("Analyzing your style..."):
            user_profile = vision.analyze_photo(image_path)
            rule_result = analyzer.analyze(user_profile, garment)
            explanation_prompt, explanation = (
                gemini.explain(user_profile, garment, rule_result)
                if gemini else ("", "Rule-based analysis applied.")
            )
            recommendations = recommender.recommend(
                user_profile=user_profile,
                current_garment=garment,
                rule_result=rule_result,
                top_k=3
            ) if recommender else []

        st.session_state.agent_state = {
            "user_profile": user_profile,
            "garment": garment,
            "rule_result": rule_result,
            "explanation": explanation,
            "explanation_prompt": explanation_prompt,
        }
        st.session_state.recommendations = recommendations
        st.session_state.analysis_done = True
        st.session_state.feedback_submitted = False

    # --- RESULTS ---
    if st.session_state.analysis_done:
        state = st.session_state.agent_state
        user = state["user_profile"]
        garment = state["garment"]
        rule_result = state["rule_result"]

        st.markdown("---")
        st.header("📊 Verdict")

        score = rule_result["score"]
        verdict = rule_result["verdict"]
        verdict_short = rule_result.get("verdict_short", verdict)

        if score >= 75:
            box = "🟢"
        elif score >= 55:
            box = "🟡"
        else:
            box = "🔴"

        st.markdown(f"### {box} {verdict_short}")
        st.write(f"**Score:** {score}/100")

        col1, col2 = st.columns([1, 2])
        with col1:
            st.image(uploaded_file, use_container_width=True)
        with col2:
            st.markdown("#### 🧬 Style DNA")
            st.write(f"**Season:** {user['season']}")
            st.write(f"**Contrast:** {user['contrast']}")
            body_balance = user.get("body_balance", {})
            st.write(
                f"**Body balance confidence:** {round(body_balance.get('confidence', 0.0), 2)}"
            )

        st.markdown("---")
        st.header("💬 Why this works / doesn’t")
        st.write(state["explanation"])
        if rule_result["reasons"]:
            st.markdown("**Key signals noticed:**")
            for r in rule_result["reasons"]:
                text = r.get("text", "")
                negative_markers = ["too", "over", "clash", "adds bulk", "hides", "overwhelm", "outside"]
                is_negative = any(m in text.lower() for m in negative_markers)
                prefix = "❌" if is_negative else "✅"
                st.write(f"{prefix} {text}")

        st.markdown("---")
        st.header("🎯 Try these instead")
        recs = st.session_state.recommendations
        if recs:
            for rec in recs:
                st.markdown(f"**{rec['name']}**")
                st.caption(f"Color: {rec['color']} · Silhouette: {rec['silhouette']}")
                st.write(f"Why: {rec['reason']}")
                st.markdown("---")
        else:
            st.info("No alternatives found yet.")

        st.markdown("---")
        st.header("🗳️ Help the stylist learn")
        feedback_logger = FeedbackLogger() if FeedbackLogger else None
        with st.form("feedback_form"):
            agree = st.radio(
                "Do you agree with this advice?",
                ["Agree", "Disagree"]
            )
            reason = st.text_input(
                "What felt right or wrong? (optional)"
            )
            override = st.selectbox(
                "What would you choose instead?",
                options=[""] + [g["name"] for g in get_full_catalog()]
            )
            submitted = st.form_submit_button("Submit feedback")
            if submitted and feedback_logger:
                feedback_logger.log_event(
                    user_id="demo_user",
                    prompt=state["explanation_prompt"],
                    response=state["explanation"],
                    user_feedback={
                        "agree": agree == "Agree",
                        "reason": reason,
                        "override": override
                    },
                    context=state
                )
                st.session_state.feedback_submitted = True

        if st.session_state.feedback_submitted:
            st.success("✅ Feedback saved — this will improve future advice.")

    if not st.session_state.analysis_done:
        st.info(
            "👈 Upload a photo, pick a garment, and click **Analyze Outfit** to begin.\n\n"
            "This stylist learns from your feedback and gets better over time."
        )

# --- BATCH ANALYSIS ---
elif mode == "Batch Analysis (Multi-photo, Classic Verdicts)":
    st.title("👔 Honest Stylist")
    st.subheader("Refined Body Analysis & Batch Testing")
    st.info("👈 Upload your photos in the sidebar and pick a garment to start the batch analysis.")

    with st.sidebar:
        st.header("1. Upload Photos")
        uploaded_photos = st.file_uploader(
            "Upload photos (Full body for shape analysis)",
            type=["jpg", "jpeg", "png"],
            accept_multiple_files=True
        )
        st.header("2. Pick Garment")
        garment_options = list_garments_display()
        selected_garment_display = st.selectbox(
            "Compare against:",
            options=garment_options,
            format_func=lambda x: x[1]
        )
        selected_sku = selected_garment_display[0] if selected_garment_display else None
        analyze_clicked = st.button("🔥 Run Analysis", use_container_width=True, type="primary")

    if analyze_clicked:
        if not uploaded_photos:
            st.error("Please upload at least one photo.")
            st.stop()
        garment = get_garment(selected_sku)
        vision = VisionAnalyzer()
        analyzer = StylingAnalyzer()
        api_key = os.getenv("GOOGLE_API_KEY")
        st.markdown(f"## 📊 Analysis for: {garment['name']}")
        rows = len(uploaded_photos)
        for idx, uploaded_file in enumerate(uploaded_photos):
            st.divider()
            col_img, col_info = st.columns([1, 2])
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                tmp.write(uploaded_file.getbuffer())
                tmp_path = tmp.name
            try:
                with st.spinner(f"Analyzing {uploaded_file.name}..."):
                    user_profile = vision.analyze_photo(tmp_path)
                    user_profile["skin_season"] = user_profile.get("season", "Unknown")
                    rule_result = analyzer.analyze(user_profile, garment)
                    explanation = None
                    if api_key:
                        explainer = GeminiExplainer(api_key)
                        explanation = explainer.explain_verdict(
                            verdict=rule_result["verdict"],
                            user_profile=user_profile,
                            garment=garment,
                            rule_reasons=rule_result["reasons"],
                            score=rule_result["score"]
                        )
                with col_img:
                    st.image(uploaded_file, use_column_width=True)
                    st.metric("Compatibility Score", f"{rule_result['score']}/100")
                with col_info:
                    v_class = "verdict-works" if rule_result["score"] >= 60 else "verdict-risky" if rule_result["score"] >= 40 else "verdict-dont-buy"
                    st.markdown(f'<div class="{v_class}"><h3></h3></div>', unsafe_allow_html=True)
                    c1, c2, c3 = st.columns(3)
                    c1.markdown(f"**Shape:** {user_profile.get('body_shape', 'N/A')}")
                    c2.markdown(f"**Season:** {user_profile.get('season', 'N/A')}")
                    c3.markdown(f"**Contrast:** {user_profile.get('contrast', 'N/A')}")
                    if explanation:
                        st.markdown("#### 💬 The Stylist's Verdict")
                        st.write(explanation["why_verdict"])
                        st.markdown("#### 🎯 Try This Instead")
                        st.info(f"**Pivot:** {explanation['pivot_suggestion']}\n\n{explanation['pivot_reason']}")
                    else:
                        st.markdown("#### Reasons")
                        for r in rule_result["reasons"]:
                            st.write(f"- {r['text']}")
            except Exception as e:
                st.error(f"Error processing {uploaded_file.name}")
                with st.expander("Traceback"):
                    import traceback
                    st.code(traceback.format_exc())
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
    else:
        st.markdown("### How the Geometry Works")
        st.write(
            "Our refined analyzer uses **Shoulder-to-Hip** and **Waist-to-Hip** ratios to categorize your frame into 5 professional body shapes."
        )
        st.markdown("""
        **Batch Analysis Instructions:**
        1. Upload multiple photos (full body recommended).
        2. Select a garment from the catalog.
        3. Click 'Run Analysis' to get honest feedback for each photo.
        """)

# --- CLASSIC HONEST STYLIST ---
elif mode == "Classic Honest Stylist (Single, Catalog/Upload)":
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
        garment_agent = GarmentSelectionAgent(catalog_path) if GarmentSelectionAgent else None
        if garment_source == "From catalog" and garment_agent:
            garment_options = garment_agent.get_options()
            selected_garment_display = st.selectbox(
                "Pick a garment:",
                options=garment_options,
                format_func=lambda x: x[1]
            )
            if selected_garment_display:
                selected_sku = selected_garment_display[0]
                garment = garment_agent.get_garment(selected_sku)
        elif garment_source == "From catalog":
            garment_options = list_garments_display()
            selected_garment_display = st.selectbox(
                "Pick a garment:",
                options=garment_options,
                format_func=lambda x: x[1]
            )
            if selected_garment_display:
                selected_sku = selected_garment_display[0]
                garment = get_garment(selected_sku)
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
                    st.image(uploaded_garment, width=150, caption = "Uploaded garment image", output_format="PNG")

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
                    # Try agent-based pipeline first
                    try:
                        photo_agent = PhotoAnalysisAgent() if PhotoAnalysisAgent else None
                        user_profile = photo_agent.analyze(temp_path) if photo_agent else None
                        if user_profile is None:
                            raise Exception("Photo agent not available")
                        user_profile["body_shape"] = manual_body_shape
                    except Exception as e:
                        logger.error(f"Photo analysis failed: {e}")
                        # Fallback to classic vision analyzer
                        vision = VisionAnalyzer()
                        user_profile = vision.analyze_photo(temp_path)
                        user_profile["body_shape"] = manual_body_shape

                    st.write("User profile (debug):", user_profile)

                    if garment_source == "From catalog":
                        pass  # garment already set
                    else:
                        try:
                            garment_analyzer = GarmentImageAnalyzer() if GarmentImageAnalyzer else None
                            if garment_analyzer:
                                garment_analysis = garment_analyzer.analyze_garment_image(garment_image_path)
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
                            else:
                                raise Exception("Garment image analyzer not available")
                        except Exception as e:
                            logger.error(f"Garment analysis failed: {e}")
                            st.error("❌ Failed to analyze garment image. Please try another image.")
                            st.stop()

                    try:
                        verdict_agent = VerdictAgent() if VerdictAgent else None
                        if verdict_agent:
                            rule_result = verdict_agent.score(user_profile, garment)
                        else:
                            raise Exception("Verdict agent not available")
                    except Exception as e:
                        logger.error(f"Verdict scoring failed: {e}")
                        # Fallback to classic rule engine
                        analyzer = StylingAnalyzer()
                        rule_result = analyzer.analyze(user_profile, garment)

                    percentage = min(95, max(0, rule_result['score']))

                    try:
                        pivot_agent = PivotAgent() if PivotAgent else None
                        if pivot_agent:
                            explanation = pivot_agent.suggest(
                                verdict=rule_result["verdict"],
                                user_profile=user_profile,
                                garment=garment,
                                reasons=rule_result["reasons"],
                                score=percentage
                            )
                        else:
                            raise Exception("Pivot agent not available")
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
                    if explanation and "pivot_suggestion" in explanation:
                        st.info(f"💡 **{explanation['pivot_suggestion']}**\n\n{explanation['pivot_reason']}")
                    else:
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
                        st.caption(f"**Your Style:**\n{user_profile.get('skin_season', user_profile.get('season', ''))} | {user_profile['body_shape']}")
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