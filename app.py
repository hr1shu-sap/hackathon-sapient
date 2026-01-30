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
import warnings

# Suppress warnings
warnings.filterwarnings('ignore')

# Local imports
from garment_catalog import list_garments_display, get_garment
from vision_analyzer import VisionAnalyzer
from rule_engine import StylingAnalyzer
from gemini_explainer import GeminiExplainer
from garment_image_analyzer import GarmentImageAnalyzer

# Page config
st.set_page_config(
    page_title="Honest Stylist",
    page_icon="👔",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for styling
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

# Title
st.title("👔 Honest Stylist")
st.subheader("Get brutally honest styling advice in seconds")
st.markdown("""
**Most fashion tech optimizes for selling more clothes.**  
**We optimize for helping you avoid bad purchases.**

Get anatomy-aware feedback on whether a piece actually suits you—before checkout.
""")
st.divider()

# Sidebar for uploads/selections
with st.sidebar:
    st.header("Setup")
    
    # Photo upload
    uploaded_photo = st.file_uploader(
        "1️⃣ Upload your photo (upper body + face)",
        type=["jpg", "jpeg", "png"],
        key="photo_upload"
    )
    
    if uploaded_photo is not None:
        # Save temporarily (use system temp dir)
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, uploaded_photo.name)
        with open(temp_path, "wb") as f:
            f.write(uploaded_photo.getbuffer())
    else:
        temp_path = None
    
    st.divider()
    
    # Choose garment source
    garment_source = st.radio(
        "2️⃣ How to evaluate a garment:",
        ["From catalog", "Upload your own"],
        horizontal=False
    )
    
    selected_sku = None
    garment = None
    garment_image_path = None
    
    if garment_source == "From catalog":
        # Garment selection from catalog
        garment_options = list_garments_display()
        selected_garment_display = st.selectbox(
            "Pick a garment:",
            options=garment_options,
            format_func=lambda x: x[1]  # Display name
        )
        
        if selected_garment_display:
            selected_sku = selected_garment_display[0]
            garment = get_garment(selected_sku)
    else:
        # Upload custom garment image
        uploaded_garment = st.file_uploader(
            "Upload garment image (flat lay or product photo)",
            type=["jpg", "jpeg", "png"],
            key="garment_upload"
        )
        
        if uploaded_garment is not None:
            temp_dir = tempfile.gettempdir()
            garment_image_path = os.path.join(temp_dir, f"garment_{uploaded_garment.name}")
            with open(garment_image_path, "wb") as f:
                f.write(uploaded_garment.getbuffer())
            
            # Show the uploaded image
            st.image(uploaded_garment, width=150)
    
    st.divider()
    
    # Analyze button
    analyze_clicked = st.button(
        "🔥 Be Honest",
        use_container_width=True,
        type="primary"
    )

# Main content area
if analyze_clicked:
    if temp_path is None:
        st.error("❌ Please upload a photo first")
    elif garment_source == "From catalog" and selected_sku is None:
        st.error("❌ Please select a garment from the catalog")
    elif garment_source == "Upload your own" and garment_image_path is None:
        st.error("❌ Please upload a garment image")
    else:
        # Show loading state
        with st.spinner("Analyzing your style..."):
            try:
                # Step 1: Vision analysis
                vision = VisionAnalyzer()
                user_profile = vision.analyze_photo(temp_path)
                
                # Step 2: Get or create garment attributes
                if garment_source == "From catalog":
                    garment = get_garment(selected_sku)
                else:
                    # Analyze custom garment image
                    garment_analyzer = GarmentImageAnalyzer()
                    garment_analysis = garment_analyzer.analyze_garment_image(garment_image_path)
                    
                    # Ask user for silhouette
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        silhouette = st.selectbox(
                            "How does it fit?",
                            ["fitted", "oversized", "straight"]
                        )
                    with col2:
                        shoulder_emphasis = st.selectbox(
                            "Shoulder detail?",
                            ["low", "medium", "high"]
                        )
                    with col3:
                        visual_weight = st.selectbox(
                            "How heavy does it feel?",
                            ["light", "medium", "heavy"]
                        )
                    
                    # Build garment object from analyzed image
                    possible_seasons = garment_analyzer.map_color_to_season(
                        garment_analysis["color_family"],
                        garment_analysis["brightness"]
                    )
                    
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
                
                # Step 3: Rule engine
                with st.spinner("Analyzing compatibility..."):
                    analyzer = StylingAnalyzer()
                    rule_result = analyzer.analyze(user_profile, garment)
                    
                    # Convert to percentage (max 95%)
                    percentage = min(95, max(0, rule_result['score']))
                
                # Step 4: Gemini explanation (if API key available)
                explanation = None
                api_key = os.getenv("GOOGLE_API_KEY")
                if api_key:
                    with st.spinner("Generating explanation..."):
                        try:
                            explainer = GeminiExplainer(api_key)
                            explanation = explainer.explain_verdict(
                                verdict=rule_result["verdict"],
                                user_profile=user_profile,
                                garment=garment,
                                rule_reasons=rule_result["reasons"],
                                score=percentage
                            )
                        except:
                            explanation = None
                
                # Display results
                st.markdown("---")
                
                # Determine verdict based on percentage
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
                
                # Display verdict prominently
                st.markdown(
                    f"""<div class="{verdict_class}"><h2>{icon} {verdict_text}</h2><h1 style="color: inherit; margin-top: 10px;">{percentage}%</h1></div>""",
                    unsafe_allow_html=True
                )
                
                # Why it works/doesn't
                st.markdown("---")
                st.markdown("### Why?")
                
                if explanation:
                    st.write(explanation["why_verdict"])
                else:
                    # Rule-based explanation
                    if rule_result["reasons"]:
                        for reason in rule_result["reasons"]:
                            if reason["penalty"] < 0:
                                st.success(f"✓ {reason['text']}")
                            else:
                                st.warning(f"✗ {reason['text']}")
                    else:
                        st.success("✓ No conflicts — this works well with your profile.")
                
                # Pivot suggestion
                st.markdown("---")
                st.markdown("### Try This Instead")
                
                if explanation:
                    st.info(f"💡 **{explanation['pivot_suggestion']}**\n\n{explanation['pivot_reason']}")
                else:
                    # Generate rule-based pivot
                    analyzer = StylingAnalyzer()
                    pivot = analyzer.generate_pivot_suggestion(user_profile, garment)
                    st.info(f"💡 {pivot}")
                
                # Display photo + garment side by side
                st.markdown("---")
                st.markdown("### Visual Comparison")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.image(Image.open(temp_path), width=350)
                    st.caption(f"**Your Style:**\n{user_profile['skin_season']} | {user_profile['body_shape']}")
                
                with col2:
                    if garment_source == "Upload your own" and garment_image_path:
                        st.image(garment_image_path, width=350)
                    else:
                        st.write(f"**{garment['name']}**")
                        st.write(f"Color: {garment['color_name']}")
                        st.write(f"Silhouette: {garment['silhouette'].title()}")
                        st.write(f"For: {', '.join(garment['color_season'])}")
                    st.caption(f"**Garment:**\n{garment['silhouette']} | {garment['shoulder_emphasis']} shoulders")
                
                # Score breakdown (hidden by default)
                with st.expander("📊 How I judged this"):
                    st.write(f"**Base Score:** 100/100")
                    st.write(f"**Final Score:** {rule_result['score']}/100 ({percentage}%)")
                    if rule_result["reasons"]:
                        st.write("**Penalties Applied:**")
                        for reason in rule_result["reasons"]:
                            st.write(f"• {reason['text']}")
                            st.write(f"  *(–{reason['penalty']} points)*")
                
            except Exception as e:
                st.error(f"❌ We couldn't analyze your photo. Make sure it shows your face and shoulders clearly, then try again.")

else:
    # Landing page
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
