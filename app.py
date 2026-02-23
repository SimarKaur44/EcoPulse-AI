import streamlit as st

# 1. Page Config
st.set_page_config(layout="wide", page_title="EcoPulse | Enterprise", page_icon="🌍", initial_sidebar_state="collapsed")

# 2. Premium Landing Page CSS
st.markdown("""
<style>
    .stApp { background-color: #0A0F18; color: #E2E8F0; font-family: 'Inter', sans-serif; }
    .hero-title { font-size: 85px; font-weight: 900; color: #F8FAFC; letter-spacing: -2.5px; margin-bottom: 0px; text-align: center;}
    .hero-subtitle { font-size: 22px; color: #00FF88; font-weight: 600; text-transform: uppercase; letter-spacing: 4px; margin-top: -10px; text-align: center;}
    .hero-body { font-size: 18px; color: #94A3B8; max-width: 800px; margin: 30px auto; text-align: center; line-height: 1.6;}
    
    .feature-card { background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.05); padding: 30px; border-radius: 12px; text-align: center; transition: transform 0.3s;}
    .feature-card:hover { transform: translateY(-5px); border-color: rgba(0, 255, 136, 0.3); }
    .feature-icon { font-size: 40px; margin-bottom: 15px; }
    .feature-title { color: #F8FAFC; font-size: 20px; font-weight: 700; margin-bottom: 10px; }
    .feature-text { color: #64748B; font-size: 15px; line-height: 1.5; }
    
    /* Giant Launch Button */
    div.stButton > button:first-child { background-color: #00FF88; color: #0A0F18; border: none; font-size: 22px; font-weight: 800; padding: 20px 40px; border-radius: 8px; transition: all 0.3s;}
    div.stButton > button:first-child:hover { background-color: #34D399; color: #0A0F18; box-shadow: 0px 0px 25px rgba(0, 255, 136, 0.4); transform: scale(1.02);}
    header {visibility: hidden;} footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# 3. Hero Section
st.markdown("<br><br><br>", unsafe_allow_html=True)
st.markdown("<div class='hero-title'>EcoPulse</div>", unsafe_allow_html=True)
st.markdown("<div class='hero-subtitle'>Global Climate Intelligence</div>", unsafe_allow_html=True)
st.markdown("<div class='hero-body'>Urban Heat Islands are a silent infrastructure crisis. Concrete acts as a thermal battery, spiking campus HVAC cooling costs by 5% for every 1°C increase. EcoPulse leverages orbital telemetry to audit, predict, and mitigate thermal stress.</div>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# 4. CTA Button (Switches to the Mission Control Page)
col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])
with col_btn2:
    if st.button("🚀 INITIALIZE ORBITAL RADAR", use_container_width=True):
        st.switch_page("1_Mission_Control.py")

st.markdown("<br><br><br><br>", unsafe_allow_html=True)

# 5. Value Proposition Cards
c1, c2, c3 = st.columns(3, gap="large")

with c1:
    st.markdown("""
    <div class='feature-card'>
        <div class='feature-icon'>🛰️</div>
        <div class='feature-title'>Landsat 9 Telemetry</div>
        <div class='feature-text'>Bypasses physical IoT sensors. We pull building-level thermal radiation data directly from Google Earth Engine.</div>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown("""
    <div class='feature-card'>
        <div class='feature-icon'>🎯</div>
        <div class='feature-title'>Pinpoint Inspection</div>
        <div class='feature-text'>Click any building or campus sector to extract raw, uncompressed surface temperature metrics instantly.</div>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown("""
    <div class='feature-card'>
        <div class='feature-icon'>🧪</div>
        <div class='feature-title'>AI Mitigation Engine</div>
        <div class='feature-text'>Simulate the financial and physical ROI of applying high-albedo cool roofs or planting green canopies.</div>
    </div>
    """, unsafe_allow_html=True)


