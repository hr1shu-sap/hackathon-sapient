# app.py
"""
HONEST STYLIST
Agentic AI fashion advisor with RLHF feedback loop
"""

import streamlit as st
import os
import tempfile
from PIL import Image

from garment_catalog import (
    get_garment,
    get_full_catalog,
    get_full_catalog_display
)
from vision_analyzer import VisionAnalyzer
from rule_engine import StylingAnalyzer
from gemini_explainer import GeminiExplainer
from ai_recommender import AIRecommender
from feedback_logger import FeedbackLogger

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------

st.set_page_config(
    page_title="Honest Stylist",
    page_icon="👔",
    layout="wide"
)

st.title("👔 Honest Stylist")
st.subheader("A brutally honest AI stylist that learns from you")

# --------------------------------------------------
# SESSION STATE INITIALIZATION
# --------------------------------------------------

DEFAULTS = {
    "analysis_done": False,
    "agent_state": None,
    "recommendations": None,
    "feedback_submitted": False,
}

for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# --------------------------------------------------
# SIDEBAR — INPUTS
# --------------------------------------------------

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

# --------------------------------------------------
# ANALYSIS (RUN ONCE)
# --------------------------------------------------

if run_analysis:
    if not uploaded_file or not selected_sku:
        st.error("Please upload a photo and select a garment.")
        st.stop()

    # Save image temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
        tmp.write(uploaded_file.getbuffer())
        image_path = tmp.name

    # Instantiate engines
    vision = VisionAnalyzer()
    analyzer = StylingAnalyzer()
    feedback_logger = FeedbackLogger()
    
    api_key = os.getenv("GOOGLE_API_KEY")
    gemini = GeminiExplainer(api_key) if api_key else None
    recommender = AIRecommender(gemini_client=gemini)

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
        )

    # Persist state
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

# --------------------------------------------------
# RESULTS VIEW (NO RE-RUNS)
# --------------------------------------------------

if st.session_state.analysis_done:
    state = st.session_state.agent_state
    user = state["user_profile"]
    garment = state["garment"]
    rule_result = state["rule_result"]

    st.markdown("---")
    st.header("📊 Verdict")

    score = rule_result["score"]
    verdict = rule_result["verdict"]
    verdict_short = rule_result["verdict_short"]

    if score >= 75:
        box = "🟢"
    elif score >= 55:
        box = "🟡"
    else:
        box = "🔴"

    st.markdown(f"### {box} {verdict_short}")
    st.write(f"**Score:** {score}/100")

    # --------------------------------------------------
    # IMAGE + PROFILE
    # --------------------------------------------------

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


    # --------------------------------------------------
    # WHY SECTION (LLM-DRIVEN)
    # --------------------------------------------------

    st.markdown("---")
    st.header("💬 Why this works / doesn’t")

    st.write(state["explanation"])

    if rule_result["reasons"]:
        st.markdown("**Key signals noticed:**")
        for r in rule_result["reasons"]:
            text = r.get("text", "")
            # Heuristic: negative phrasing → ❌, otherwise ✅
            negative_markers = ["too", "over", "clash", "adds bulk", "hides", "overwhelm", "outside"]
            is_negative = any(m in text.lower() for m in negative_markers)

            prefix = "❌" if is_negative else "✅"

            st.write(f"{prefix} {text}")

    # --------------------------------------------------
    # RECOMMENDATIONS (ALWAYS SHOWN)
    # --------------------------------------------------

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

    # --------------------------------------------------
    # FEEDBACK (RLHF) — FORM-BASED
    # --------------------------------------------------

    st.markdown("---")
    st.header("🗳️ Help the stylist learn")

    feedback_logger = FeedbackLogger()

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

        if submitted:
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

# --------------------------------------------------
# LANDING VIEW
# --------------------------------------------------

if not st.session_state.analysis_done:
    st.info(
        "👈 Upload a photo, pick a garment, and click **Analyze Outfit** to begin.\n\n"
        "This stylist learns from your feedback and gets better over time."
    )
