import streamlit as st

st.set_page_config(layout="wide", page_title="Executive Brief", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    .stApp { background-color: #0A0F18; color: #E2E8F0; font-family: 'Inter', sans-serif; }
    .header-main { color: #F8FAFC; font-size: 34px; font-weight: 800; margin-bottom: 0px; letter-spacing: -0.5px;}
    .header-sub { color: #94A3B8; font-size: 16px; font-weight: 500; margin-bottom: 30px; }
    .card { background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.05); padding: 25px; border-radius: 8px; margin-bottom: 20px;}
    .card-title { color: #00FF88; font-size: 18px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 15px;}
    .big-number { font-size: 48px; font-weight: 800; color: #F8FAFC; line-height: 1; margin-bottom: 5px;}
    .number-label { color: #94A3B8; font-size: 14px; font-weight: 600;}
    header {visibility: hidden;} footer {visibility: hidden;}
    
    .back-btn div.stButton > button:first-child { background-color: transparent; color: #94A3B8; border: 1px solid #94A3B8; }
    .back-btn div.stButton > button:first-child:hover { background-color: rgba(255,255,255,0.1); color: white;}
</style>
""", unsafe_allow_html=True)

st.markdown("<div class='back-btn'>", unsafe_allow_html=True)
if st.button("⬅ Return to Mission Control"):
    st.switch_page("pages/1_🌍_Mission_Control.py")
st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div class='header-main'>ESG Compliance & Action Report</div>", unsafe_allow_html=True)
st.markdown("<div class='header-sub'>Automated AI synthesis based on orbital thermal telemetry.</div>", unsafe_allow_html=True)

# 🚦 Check if data exists
if 'report_data' not in st.session_state or not st.session_state.report_data:
    st.warning("⚠️ No sector data found. Please return to Mission Control, outline a sector on the map, and run the simulator to generate a report.")
    st.stop()

data = st.session_state.report_data

# 1. Top Metrics Row
c1, c2, c3 = st.columns(3)
with c1:
    st.markdown(f"<div class='card'><div class='card-title'>Current Heat Threat</div><div class='big-number' style='color:#FCA5A5;'>{data['t_max']}°C</div><div class='number-label'>Peak Building Surface Temperature</div></div>", unsafe_allow_html=True)
with c2:
    st.markdown(f"<div class='card'><div class='card-title'>Vegetation Index (NDVI)</div><div class='big-number' style='color:#6EE7B7;'>{data['ndvi']}</div><div class='number-label'>Scale 0.0 to 1.0 (Higher is healthier)</div></div>", unsafe_allow_html=True)
with c3:
    st.markdown(f"<div class='card'><div class='card-title'>Financial Bleed</div><div class='big-number'>₹ {data['loss']} L</div><div class='number-label'>Estimated Annual HVAC Loss</div></div>", unsafe_allow_html=True)

# 2. AI Intelligence Summary
st.markdown("<div class='card'>", unsafe_allow_html=True)
st.markdown("<div class='card-title'>🧠 Prescriptive AI Intelligence</div>", unsafe_allow_html=True)

if data['variance'] > 6:
    st.markdown(f"<p style='color:#E2E8F0; font-size: 16px; line-height:1.6;'><b>CRITICAL:</b> Severe thermal pooling detected. The sector exhibits an extreme variance of {data['variance']}°C between impervious concrete and surrounding areas. This structural heat absorption is actively driving up ambient temperatures and increasing facility cooling taxes.</p>", unsafe_allow_html=True)
else:
    st.markdown(f"<p style='color:#E2E8F0; font-size: 16px; line-height:1.6;'><b>MODERATE:</b> Sector shows moderate thermal stress with a variance of {data['variance']}°C. Preventative mitigation is recommended to halt micro-climate warming.</p>", unsafe_allow_html=True)

if data['mitigation'] > 0:
    st.markdown(f"<p style='color:#34D399; font-size: 16px; line-height:1.6; border-left: 3px solid #34D399; padding-left: 15px;'><b>SIMULATION RESULTS:</b> Implementing your proposed {data['mitigation']}% mitigation investment is projected to successfully drop the average zone temperature to {data['t_avg']}°C, stabilizing the thermal gradient.</p>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# 3. Action Plan
st.markdown("### Strategic Mitigation Roadmap")
ca, cb = st.columns(2)
with ca:
    st.info("**🏗️ Architectural Strategy:** Apply high-albedo (white) Polyurea Elastomeric coatings to all flat commercial roofs detected in the hot-zones. This can increase solar reflectivity by up to 85%.")
with cb:
    st.success("**🌳 Botanical Strategy:** Due to the local climate profile, immediately deploy high-canopy, drought-resistant native species such as *Azadirachta indica* (Neem) in the highlighted red zones to cast structural shadows.")

st.download_button("📥 Download Official ESG PDF Report (Simulated)", "EcoPulse ESG Report Data...", file_name="EcoPulse_ESG_Report.txt")