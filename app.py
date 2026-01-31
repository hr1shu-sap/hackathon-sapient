"""
HONEST STYLIST
A brutally honest fashion advisor

USER FLOW:
1. Upload photo (face + shoulders)
2. Select garment
3. Click "Be Honest"
4. Get verdict + explanation + pivot
"""

# """
# HONEST STYLIST
# A brutally honest fashion advisor
# """

# import streamlit as st
# import os
# from pathlib import Path
# from PIL import Image
# import tempfile

# # Local imports
# from garment_catalog import list_garments_display, get_garment
# from vision_analyzer import VisionAnalyzer
# from rule_engine import StylingAnalyzer
# from gemini_explainer import GeminiExplainer

# # Page config
# st.set_page_config(
#     page_title="Honest Stylist",
#     page_icon="👔",
#     layout="wide",
#     initial_sidebar_state="collapsed"
# )

# # CSS
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

# # Title
# st.title("👔 Honest Stylist")
# st.subheader("Get brutally honest styling advice in seconds")

# # Sidebar
# with st.sidebar:
#     st.header("Setup")

#     uploaded_photo = st.file_uploader(
#         "Upload your photo (upper body + face)",
#         type=["jpg", "jpeg", "png"]
#     )

#     if uploaded_photo:
#         temp_dir = tempfile.gettempdir()
#         temp_path = os.path.join(temp_dir, uploaded_photo.name)
#         with open(temp_path, "wb") as f:
#             f.write(uploaded_photo.getbuffer())
#         st.success("Photo uploaded")
#     else:
#         temp_path = None

#     garment_options = list_garments_display()
#     selected_garment_display = st.selectbox(
#         "Pick a garment:",
#         options=garment_options,
#         format_func=lambda x: x[1]
#     )

#     selected_sku = selected_garment_display[0] if selected_garment_display else None

#     analyze_clicked = st.button(
#         "🔥 Be Honest",
#         use_container_width=True,
#         type="primary"
#     )

# # ---------------------------------------------------
# # ANALYSIS
# # ---------------------------------------------------

# if analyze_clicked:

#     if temp_path is None:
#         st.error("Upload a photo first.")
#         st.stop()

#     if selected_sku is None:
#         st.error("Select a garment.")
#         st.stop()

#     try:
#         with st.spinner("Analyzing..."):

#             # -------------------------------
#             # Step 1 Vision
#             # -------------------------------
#             st.info("Step 1: Reading your style DNA...")

#             vision = VisionAnalyzer()
#             user_profile = vision.analyze_photo(temp_path)

#             # 🔥 Compatibility bridge
#             user_profile["skin_season"] = user_profile["season"]

#             st.success(
#                 f"✓ Detected: {user_profile['season']} "
#                 f"(confidence {user_profile['confidence']})"
#             )

#             # -------------------------------
#             # Step 2 Garment
#             # -------------------------------
#             garment = get_garment(selected_sku)

#             st.info(f"Step 2: Checking {garment['name']}...")

#             # -------------------------------
#             # Step 3 Rule Engine
#             # -------------------------------
#             analyzer = StylingAnalyzer()
#             rule_result = analyzer.analyze(user_profile, garment)

#             st.success(f"✓ Score: {rule_result['score']}/100")

#             # -------------------------------
#             # Step 4 Gemini (optional)
#             # -------------------------------
#             api_key = os.getenv("GOOGLE_API_KEY")

#             if api_key:
#                 explainer = GeminiExplainer(api_key)
#                 explanation = explainer.explain_verdict(
#                     verdict=rule_result["verdict"],
#                     user_profile=user_profile,
#                     garment=garment,
#                     rule_reasons=rule_result["reasons"],
#                     score=rule_result["score"]
#                 )
#             else:
#                 explanation = None

#         # ---------------------------------------------------
#         # DISPLAY
#         # ---------------------------------------------------

#         st.markdown("---")
#         st.markdown("## 📊 VERDICT")

#         if rule_result["score"] >= 60:
#             verdict_class = "verdict-works"
#             icon = "✅"
#         elif rule_result["score"] >= 40:
#             verdict_class = "verdict-risky"
#             icon = "⚠️"
#         else:
#             verdict_class = "verdict-dont-buy"
#             icon = "❌"

#         st.markdown(
#             f'<div class="{verdict_class}"><h3>{icon} {rule_result["verdict"]}</h3></div>',
#             unsafe_allow_html=True
#         )

#         # Photo + Garment
#         col1, col2 = st.columns(2)

#         with col1:
#             st.subheader("You")

#             image = Image.open(temp_path)
#             st.image(image, use_column_width=True)

#             st.caption(
#                 f"""
# Season: {user_profile['season']}
# Temperature: {user_profile['temperature']}
# Contrast: {user_profile['contrast']}
# Confidence: {user_profile['confidence']}
# """
#             )

#         with col2:
#             st.subheader(garment["name"])
#             st.write(f"Color: {garment['color_name']}")
#             st.write(f"Silhouette: {garment['silhouette']}")
#             st.write(f"For: {', '.join(garment['color_season'])}")

#         # WHY
#         st.markdown("---")
#         st.markdown("## 💬 WHY")

#         if explanation:
#             st.write(explanation["why_verdict"])
#         else:
#             for reason in rule_result["reasons"]:
#                 if reason["penalty"] < 0:
#                     st.success(reason["text"])
#                 else:
#                     st.error(reason["text"])

#         # Pivot
#         st.markdown("---")
#         st.markdown("## 🎯 TRY THIS INSTEAD")

#         if explanation:
#             st.write(f"**{explanation['pivot_suggestion']}**")
#             st.write(explanation["pivot_reason"])
#         else:
#             st.write("Try a better color or silhouette.")

#         # Debug
#         with st.expander("📈 Debug"):
#             st.write(user_profile)
#             st.write(rule_result)

#     except Exception as e:
#         st.error(f"Error: {e}")
#         import traceback
#         st.code(traceback.format_exc())

# # ---------------------------------------------------
# # LANDING
# # ---------------------------------------------------

# else:

#     col1, col2 = st.columns(2)

#     with col1:
#         st.markdown("""
# ### How it works

# 1. Upload your photo  
# 2. Pick a garment  
# 3. Get honest advice  

# We analyze:
# - Skin tone  
# - Contrast  
# - Color harmony  
# """)

#     with col2:
#         st.markdown("""
# ### What you get

# ✅ Direct verdict  
# 💭 Honest reasons  
# 🎯 Pivot suggestion  

# No fluff. Just truth.
# """)

"""
HONEST STYLIST - Refined Edition
A brutally honest fashion advisor with Batch Analysis
"""

import streamlit as st
import os
from PIL import Image
import tempfile
import traceback

# Local imports
from garment_catalog import list_garments_display, get_garment
from vision_analyzer import VisionAnalyzer
from rule_engine import StylingAnalyzer
from gemini_explainer import GeminiExplainer

# Page config
st.set_page_config(
    page_title="Honest Stylist",
    page_icon="👔",
    layout="wide"
)

# Custom Styles
st.markdown("""
<style>
    .verdict-works { background-color: #d4edda; border-left: 5px solid #28a745; padding: 15px; border-radius: 4px; }
    .verdict-risky { background-color: #fff3cd; border-left: 5px solid #ffc107; padding: 15px; border-radius: 4px; }
    .verdict-dont-buy { background-color: #f8d7da; border-left: 5px solid #dc3545; padding: 15px; border-radius: 4px; }
    .stMetric { background-color: #f0f2f6; padding: 10px; border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

st.title("👔 Honest Stylist")
st.subheader("Refined Body Analysis & Batch Testing")

# Sidebar Configuration
with st.sidebar:
    st.header("1. Upload Photos")
    # Updated to accept multiple files for batch testing
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

# --- Analysis Logic ---
if analyze_clicked:
    if not uploaded_photos:
        st.error("Please upload at least one photo.")
        st.stop()
    
    garment = get_garment(selected_sku)
    vision = VisionAnalyzer()
    analyzer = StylingAnalyzer()
    api_key = os.getenv("GOOGLE_API_KEY")

    st.markdown(f"## 📊 Analysis for: {garment['name']}")
    
    # Grid layout for Batch Results
    rows = len(uploaded_photos)
    for idx, uploaded_file in enumerate(uploaded_photos):
        st.divider()
        col_img, col_info = st.columns([1, 2])

        # Save uploaded file to temporary path
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            tmp.write(uploaded_file.getbuffer())
            tmp_path = tmp.name

        try:
            with st.spinner(f"Analyzing {uploaded_file.name}..."):
                # 1. Vision Analysis
                user_profile = vision.analyze_photo(tmp_path)
                user_profile["skin_season"] = user_profile.get("season", "Unknown")

                # 2. Rule Engine
                rule_result = analyzer.analyze(user_profile, garment)

                # 3. Gemini Explanation
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

            # --- Display Results ---
            with col_img:
                st.image(uploaded_file, use_container_width=True)
                st.metric("Compatibility Score", f"{rule_result['score']}/100")

            with col_info:
                # Verdict Header
                v_class = "verdict-works" if rule_result["score"] >= 60 else "verdict-risky" if rule_result["score"] >= 40 else "verdict-dont-buy"
                st.markdown(f'<div class="{v_class}"><h3></h3></div>', unsafe_allow_html=True)
                
                # Biometric Summary
                c1, c2, c3 = st.columns(3)
                c1.markdown(f"**Shape:** {user_profile['body_shape']}")
                c2.markdown(f"**Season:** {user_profile['season']}")
                c3.markdown(f"**Contrast:** {user_profile['contrast']}")

                # Explanation text
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
            st.expander("Traceback").code(traceback.format_exc())
        
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

else:
    # Landing Page
    st.info("👈 Upload your photos in the sidebar and pick a garment to start the batch analysis.")
    
    # Show instructional visual
    st.markdown("### How the Geometry Works")
    st.write("Our refined analyzer uses **Shoulder-to-Hip** and **Waist-to-Hip** ratios to categorize your frame into 5 professional body shapes.")