# """
# HONEST STYLIST — AGENTIC EDITION
# LangGraph-orchestrated, RLHF-ready
# """

# import streamlit as st
# import tempfile
# import os
# import traceback
# from PIL import Image

# # Catalog
# from garment_catalog import (
#     get_garment,
#     get_full_catalog_display
# )

# # Agent
# from stylist_agent import stylist_agent

# # --------------------------------------------------
# # Page Config
# # --------------------------------------------------

# st.set_page_config(
#     page_title="Honest Stylist",
#     page_icon="👔",
#     layout="wide"
# )

# # --------------------------------------------------
# # Styles
# # --------------------------------------------------

# st.markdown("""
# <style>
# .verdict-works {
#     background-color: #d4edda;
#     border-left: 5px solid #28a745;
#     padding: 15px;
#     border-radius: 4px;
# }
# .verdict-risky {
#     background-color: #fff3cd;
#     border-left: 5px solid #ffc107;
#     padding: 15px;
#     border-radius: 4px;
# }
# .verdict-dont-buy {
#     background-color: #f8d7da;
#     border-left: 5px solid #dc3545;
#     padding: 15px;
#     border-radius: 4px;
# }
# </style>
# """, unsafe_allow_html=True)

# # --------------------------------------------------
# # Header
# # --------------------------------------------------

# st.title("👔 Honest Stylist")
# st.subheader("Agentic AI that tells you the truth — and learns from you")

# # --------------------------------------------------
# # Sidebar
# # --------------------------------------------------

# with st.sidebar:
#     st.header("1️⃣ Upload Photo")

#     uploaded_photo = st.file_uploader(
#         "Upload your photo (full body preferred)",
#         type=["jpg", "jpeg", "png"]
#     )

#     if uploaded_photo:
#         tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
#         tmp.write(uploaded_photo.getbuffer())
#         image_path = tmp.name
#         st.success("Photo uploaded")
#     else:
#         image_path = None

#     st.header("2️⃣ Pick Garment")

#     garment_options = get_full_catalog_display()

#     selected_tuple = st.selectbox(
#         "Choose a garment",
#         options=garment_options,
#         format_func=lambda x: x[1]
#     )

#     selected_sku = selected_tuple[0]
#     garment = get_garment(selected_sku)

#     analyze_clicked = st.button(
#         "🔥 Be Honest",
#         type="primary",
#         use_container_width=True
#     )

# # --------------------------------------------------
# # Main Execution
# # --------------------------------------------------

# if analyze_clicked:

#     if not image_path:
#         st.error("Please upload a photo.")
#         st.stop()

#     try:
#         with st.spinner("The stylist is thinking..."):

#             # -----------------------------
#             # Run LangGraph Agent
#             # -----------------------------
#             agent_result = stylist_agent.invoke({
#                 "image_path": image_path,
#                 "garment": garment,
#                 "user_feedback": None  # filled later
#             })

#         # -----------------------------
#         # Extract agent outputs safely
#         # -----------------------------
#         profile = agent_result.get("user_profile", {})
#         rule = agent_result.get("rule_result", {})
#         explanation = agent_result.get("explanation")
#         recommendations = agent_result.get("recommendations")
#         score = agent_result.get("verdict_score", 0)

#         # -----------------------------
#         # Verdict UI
#         # -----------------------------
#         st.markdown("---")
#         st.markdown("## 📊 Verdict")

#         if score >= 60:
#             v_class = "verdict-works"
#             verdict_label = "✅ Works for you"
#         elif score >= 40:
#             v_class = "verdict-risky"
#             verdict_label = "⚠️ Risky choice"
#         else:
#             v_class = "verdict-dont-buy"
#             verdict_label = "❌ Not recommended"

#         st.markdown(
#             f'<div class="{v_class}"><h3>{verdict_label}</h3></div>',
#             unsafe_allow_html=True
#         )

#         # -----------------------------
#         # Photo + Profile
#         # -----------------------------
#         col1, col2 = st.columns(2)

#         with col1:
#             st.subheader("You")
#             st.image(Image.open(image_path), use_column_width=True)

#             shape = profile.get("body_shape", "Not confidently detected")

#             st.caption(
#                 f"""
# Shape signal: {shape}  
# Season: {profile.get('season', 'Unknown')}  
# Contrast: {profile.get('contrast', 'Unknown')}  
# Confidence: {round(profile.get('confidence', 0), 2)}
# """
#             )

#         with col2:
#             st.subheader(garment["name"])
#             st.write(f"Color: {garment['color_name']}")
#             st.write(f"Silhouette: {garment['silhouette']}")
#             st.write(f"For seasons: {', '.join(garment['color_season'])}")

#         # -----------------------------
#         # Explanation
#         # -----------------------------
#         st.markdown("---")
#         st.markdown("## 💬 Why")

#         if explanation:
#             st.write(explanation.get("why_verdict"))
#         else:
#             for r in rule.get("reasons", []):
#                 if r["penalty"] < 0:
#                     st.success(r["text"])
#                 else:
#                     st.error(r["text"])

#         # -----------------------------
#         # Recommendations (Agent-driven)
#         # -----------------------------
#         if recommendations:
#             st.markdown("---")
#             st.markdown("## 🎯 Try This Instead")

#             for rec in recommendations[:3]:
#                 st.info(f"**{rec['name']}** — {rec['reason']}")

#         # -----------------------------
#         # RLHF Feedback
#         # -----------------------------
#         st.markdown("---")
#         st.markdown("## 🧠 Help the stylist learn")

#         feedback = st.radio(
#             "Was this advice accurate?",
#             ["agree", "disagree", "bought_anyway"],
#             horizontal=True
#         )

#         if st.button("Submit feedback"):
#             stylist_agent.invoke({
#                 "image_path": image_path,
#                 "garment": garment,
#                 "user_feedback": feedback
#             })
#             st.success("Thanks — the stylist will get better over time.")

#         # -----------------------------
#         # Debug
#         # -----------------------------
#         with st.expander("📈 Debug (Agent State)"):
#             st.write(agent_result)

#     except Exception:
#         st.error("Something went wrong.")
#         st.code(traceback.format_exc())

#     finally:
#         if image_path and os.path.exists(image_path):
#             os.remove(image_path)

# # --------------------------------------------------
# # Landing
# # --------------------------------------------------

# else:
#     st.info(
#         "Upload a photo and pick a garment to get honest advice — "
#         "powered by an agentic AI stylist that learns from feedback."
#     )


# app.py
import streamlit as st
import tempfile
import os
import json

from garment_catalog import get_full_catalog_display, get_garment
from vision_analyzer import VisionAnalyzer
from rule_engine import StylingAnalyzer
from stylist_agent import stylist_agent
from feedback_logger import log_feedback

st.set_page_config(
    page_title="Honest Stylist",
    page_icon="👔",
    layout="wide"
)

st.title("👔 Honest Stylist")
st.caption("Body balance, not body shame.")

# ---------------- Sidebar ----------------
with st.sidebar:
    st.header("1. Upload Photo")
    uploaded_file = st.file_uploader(
        "Full body preferred",
        type=["jpg", "jpeg", "png"]
    )

    st.header("2. Pick Garment")
    garment_options = get_full_catalog_display()
    selected = st.selectbox(
        "Choose garment",
        garment_options,
        format_func=lambda x: x[1]
    )

    run = st.button("🔥 Be Honest", use_container_width=True)

# ---------------- Main ----------------
if run:
    if not uploaded_file:
        st.error("Please upload a photo.")
        st.stop()

    if not selected:
        st.error("Please select a garment.")
        st.stop()

    sku = selected[0]
    garment = get_garment(sku)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
        tmp.write(uploaded_file.getbuffer())
        image_path = tmp.name

    with st.spinner("Analyzing your balance…"):
        agent_state = stylist_agent.invoke({
            "image_path": image_path,
            "garment": garment
        })

    os.remove(image_path)

    user_profile = agent_state["user_profile"]
    rule_result = agent_state["rule_result"]

    # ---------------- Verdict ----------------
    st.markdown(f"## {rule_result['verdict_short']}")
    st.metric("Compatibility Score", rule_result["score"])

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("You")
        st.image(uploaded_file, width=350)

        st.caption(
            f"""
**Season:** {user_profile.get("season")}  
**Contrast:** {user_profile.get("contrast")}  
"""
        )

    with col2:
        st.subheader(garment["name"])
        st.write(f"**Color:** {garment['color_name']}")
        st.write(f"**Silhouette:** {garment['silhouette']}")
        st.write(f"**Best seasons:** {', '.join(garment['color_season'])}")

    # ---------------- WHY (NO DEBUG) ----------------
    st.markdown("## 💬 Why")

    if rule_result["reasons"]:
        for r in rule_result["reasons"]:
            if r["type"] == "bonus":
                st.success(r["text"])
            else:
                st.error(r["text"])
    else:
        st.success(
            "This garment aligns well with your natural proportions and coloring."
        )

    # ---------------- Feedback (RLHF hook) ----------------
    st.markdown("## 🧠 Help the stylist learn")

    feedback = st.radio(
        "Was this advice accurate?",
        ["agree", "disagree", "bought_anyway"],
        horizontal=True
    )

    user_reason = st.text_input(
        "Want to tell us why? (optional)"
    )

    if st.button("Submit feedback"):
        log_feedback(
            agent_state=agent_state,
            feedback=feedback,
            user_reason=user_reason
        )
        st.success("Thank you! This helps improve future recommendations.")

else:
    st.info("Upload a photo and pick a garment to begin.")

# **Body balance confidence:** {user_profile["body_balance"]["confidence"]}
