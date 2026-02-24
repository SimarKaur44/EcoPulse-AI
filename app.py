import os
import streamlit as st
import ee
import folium
from folium.plugins import Draw, Geocoder
from streamlit_folium import st_folium
import geocoder
import google.generativeai as genai # 🌟 LIVE AI API

# --- 🌟 CORE ENGINE FIX 🌟 ---
def add_ee_layer(self, ee_image_object, vis_params, name, opacity=1):
    map_id_dict = ee.Image(ee_image_object).getMapId(vis_params)
    folium.raster_layers.TileLayer(
        tiles=map_id_dict['tile_fetcher'].url_format,
        attr='Google Earth Engine',
        name=name, overlay=True, control=True, opacity=opacity
    ).add_to(self)
folium.Map.addLayer = add_ee_layer

def mask_l9_clouds(image):
    qa = image.select('QA_PIXEL')
    cloud_shadow_bit_mask = (1 << 4)
    clouds_bit_mask = (1 << 3)
    mask = qa.bitwiseAnd(cloud_shadow_bit_mask).eq(0).And(qa.bitwiseAnd(clouds_bit_mask).eq(0))
    return image.updateMask(mask)
# ---------------------------------------------------------

st.set_page_config(layout="wide", page_title="EcoPulse | AI Summit 2026", page_icon="🌍", initial_sidebar_state="collapsed")

# --- UI/UX ENTERPRISE STYLES ---
st.markdown("""
<style>
    .stApp { background-color: #0A0F18; color: #E2E8F0; font-family: 'Inter', sans-serif; }
    
    .hero-bg {
        background: radial-gradient(ellipse at 50% -20%, rgba(16, 185, 129, 0.15), transparent 60%),
                    radial-gradient(ellipse at 100% 50%, rgba(59, 130, 246, 0.1), transparent 50%),
                    linear-gradient(to bottom, #0A0F18, #05080f);
        border: 1px solid rgba(255,255,255,0.05);
        border-radius: 24px;
        padding: 80px 40px;
        box-shadow: 0 20px 50px rgba(0,0,0,0.5);
        text-align: center;
        position: relative;
        overflow: hidden;
    }
    
    .header-main { color: #F8FAFC; font-size: 30px; font-weight: 800; margin-bottom: 0px; letter-spacing: -0.5px;}
    .header-sub { color: #34D399; font-size: 14px; font-weight: 600; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 25px; }
    .section-title { color: #94A3B8; font-size: 13px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 10px;}
    
    .metric-value { font-size: 42px; font-weight: 700; color: #F8FAFC; line-height: 1.1; }
    .metric-value-small { font-size: 24px; font-weight: 600; color: #F8FAFC; line-height: 1.1; }
    .metric-label { font-size: 13px; color: #94A3B8; font-weight: 500; }
    
    header {visibility: hidden;} footer {visibility: hidden;}
    
    .nav-btn div.stButton > button:first-child { background-color: #10B981; color: #0A0F18; border: none; font-size: 16px; font-weight: 700; padding: 12px 24px; border-radius: 6px; transition: all 0.2s;}
    .nav-btn div.stButton > button:first-child:hover { background-color: #059669; }
    .sec-btn div.stButton > button:first-child { background-color: transparent; color: #94A3B8; border: 1px solid #475569; font-weight: 600;}
</style>
""", unsafe_allow_html=True)

# --- GLOBAL SESSION STATES ---
if 'app_page' not in st.session_state: st.session_state.app_page = "Home"
if 'roi_geom' not in st.session_state: st.session_state.roi_geom = None
if 'map_center' not in st.session_state: st.session_state.map_center = [28.4610, 77.4900]
if 'map_zoom' not in st.session_state: st.session_state.map_zoom = 15
if 'last_search' not in st.session_state: st.session_state.last_search = ""
if 'location_name' not in st.session_state: st.session_state.location_name = "Selected Sector"
if 'user_bill' not in st.session_state: st.session_state.user_bill = 15.0 
if 'report_data' not in st.session_state: st.session_state.report_data = {}
if 'chat_history' not in st.session_state: st.session_state.chat_history = []

dates = {
    "Jan - Mar 2025 (Spring/Baseline)": ['2025-01-01', '2025-03-31'],
    "Apr - Jul 2025 (Peak Summer)": ['2025-04-01', '2025-07-31'],
    "Jan - Mar 2024 (Historical Spring)": ['2024-01-01', '2024-03-31'],
    "Apr - Jul 2024 (Historical Summer)": ['2024-04-01', '2024-07-31'],
}

# ==========================================
# 🏠 PAGE 1: THE HOMEPAGE
# ==========================================
if st.session_state.app_page == "Home":
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    st.markdown("<div class='hero-bg'>", unsafe_allow_html=True)
    st.markdown("<div style='background: rgba(16, 185, 129, 0.1); color: #34D399; padding: 6px 16px; border-radius: 50px; font-size: 13px; font-weight: bold; display: inline-block; margin-bottom: 20px; border: 1px solid rgba(16, 185, 129, 0.3);'>AI Impact Telemetry Live</div>", unsafe_allow_html=True)
    st.markdown("<h1 style='font-size: 80px; color: #F8FAFC; font-weight: 900; letter-spacing: -2px; margin-bottom: 0px;'>EcoPulse</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='color: #94A3B8; font-size: 24px; font-weight: 400; margin-top: 5px;'>Revolutionize Your Climate Strategy with <span style='color: #10B981; font-weight:bold;'>Orbital AI</span></h3>", unsafe_allow_html=True)
    st.markdown("<p style='color: #64748B; font-size: 18px; max-width: 700px; margin: 20px auto; line-height: 1.6;'>Concrete buildings act like thermal batteries, trapping heat and forcing AC units to burn extreme amounts of electricity. Pinpoint heat leaks globally and prescribe automated mitigation strategies.</p>", unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1.5, 1, 1.5])
    with col2:
        st.markdown("<div class='nav-btn'>", unsafe_allow_html=True)
        if st.button("🚀 Launch Dashboard", use_container_width=True):
            st.session_state.app_page = "Dashboard"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns(3, gap="large")
    with c1:
        st.markdown("<div style='background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.05); padding: 30px; border-radius: 12px; text-align:center;'><h1 style='font-size: 40px; margin:0;'>🛰️</h1><h3 style='color: white; font-size:18px;'>Orbital Scanning</h3><p style='color: #64748B; font-size:14px;'>Extracts precise Land Surface Temperature (LST) directly from space without needing ground sensors.</p></div>", unsafe_allow_html=True)
    with c2:
        st.markdown("<div style='background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.05); padding: 30px; border-radius: 12px; text-align:center;'><h1 style='font-size: 40px; margin:0;'>💸</h1><h3 style='color: white; font-size:18px;'>Financial Impact</h3><p style='color: #64748B; font-size:14px;'>Input your electricity bill to calculate exactly how much money is being burnt on extra AC power.</p></div>", unsafe_allow_html=True)
    with c3:
        st.markdown("<div style='background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.05); padding: 30px; border-radius: 12px; text-align:center;'><h1 style='font-size: 40px; margin:0;'>🌱</h1><h3 style='color: white; font-size:18px;'>LEED Compliance</h3><p style='color: #64748B; font-size:14px;'>Actionable insights to help your facility qualify for green-building certification and tax credits.</p></div>", unsafe_allow_html=True)

# ==========================================
# 🌍 PAGE 2: THE DASHBOARD (CLEAN INPUTS)
# ==========================================
elif st.session_state.app_page == "Dashboard":
    try:
        ee_path = os.path.expanduser('~/.config/earthengine')
        os.makedirs(ee_path, exist_ok=True)
        with open(os.path.join(ee_path, 'credentials'), 'w') as f:
            f.write(st.secrets["EARTHENGINE_TOKEN"])
        ee.Initialize(project='ecoplus-iilm')
        if not hasattr(ee.data, '_credentials'): ee.data._credentials = True
    except Exception as e:
        st.error(f"System Offline: {e}")
        st.stop()

    c1, c2, c3 = st.columns([1, 4, 1.5])
    with c1:
        st.markdown("<div class='sec-btn'>", unsafe_allow_html=True)
        if st.button("⬅ Home", use_container_width=True):
            st.session_state.app_page = "Home"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    with c2:
        st.markdown("<div class='header-main' style='font-size: 24px; margin-top: -2px;'>Live Orbital Radar</div>", unsafe_allow_html=True)
    with c3:
        st.markdown("<div class='nav-btn' style='margin-top: -10px;'>", unsafe_allow_html=True)
        if st.button("Generate AI Report ➡️", use_container_width=True):
            st.session_state.app_page = "Report"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<hr style='margin: 10px 0px 20px 0px; border-color: #334155;'>", unsafe_allow_html=True)

    col_insight, col_map = st.columns([1.5, 2.5], gap="large")

    with col_insight:
        # 1. Search Bar & Clear Button
        c_search, c_clear = st.columns([3, 1])
        with c_search:
            search_query = st.text_input("TARGET COORDINATES", placeholder="Search sector...", label_visibility="collapsed")
        with c_clear:
            if st.button("🗑️ Clear", use_container_width=True):
                st.session_state.roi_geom = None
                st.session_state.report_data = {}
                st.rerun()

        if search_query and search_query != st.session_state.last_search:
            with st.spinner("Locking coordinates..."):
                g = geocoder.arcgis(search_query)
                if g.ok:
                    st.session_state.map_center = [g.lat, g.lng]
                    st.session_state.map_zoom = 16
                    st.session_state.roi_geom = None
                    st.session_state.last_search = search_query
                    st.session_state.location_name = search_query 
                    st.rerun()

        # 2. Timeframe Filter
        st.markdown("<div class='section-title' style='margin-top:15px;'>Orbital Timeframe Filter</div>", unsafe_allow_html=True)
        timeframe = st.selectbox("Timeframe", list(dates.keys()), label_visibility="collapsed")
        start_date, end_date = dates[timeframe]
        
        # 3. Electricity Bill Input
        st.markdown("<div class='section-title' style='margin-top:15px; color: #FCD34D;'>Approx Annual Electricity Bill (₹ Lakhs)</div>", unsafe_allow_html=True)
        user_bill = st.number_input("Bill", min_value=1.0, value=st.session_state.user_bill, step=1.0, label_visibility="collapsed")
        st.session_state.user_bill = user_bill

        if st.session_state.roi_geom:
            roi = ee.Geometry(st.session_state.roi_geom)
            
            try:
                l9_img = ee.ImageCollection("LANDSAT/LC09/C02/T1_L2").filterDate(start_date, end_date).filterBounds(roi).sort('CLOUD_COVER').first()
                s2_img = ee.ImageCollection('COPERNICUS/S2_SR').filterBounds(roi).filterDate(start_date, end_date).sort('CLOUDY_PIXEL_PERCENTAGE').first()
                
                ndvi = s2_img.normalizedDifference(['B8', 'B4']).reduceRegion(reducer=ee.Reducer.mean(), geometry=roi, scale=10).get('nd').getInfo()
                thermal_raw = l9_img.select('ST_B10').multiply(0.00341802).add(149.0).subtract(273.15)
                thermal_hd = thermal_raw.resample('bicubic').reproject(crs=thermal_raw.projection(), scale=3)
                
                temp_mean_base = thermal_hd.reduceRegion(reducer=ee.Reducer.mean(), geometry=roi, scale=30, maxPixels=1e9).get('ST_B10').getInfo()
                stats_fixed = thermal_hd.reduceRegion(reducer=ee.Reducer.percentile([5, 95]), geometry=roi, scale=30, maxPixels=1e9).getInfo()
                
                t_min_base = stats_fixed.get('ST_B10_p5', 20)
                t_max_base = stats_fixed.get('ST_B10_p95', 40)

                n_val = round(ndvi, 2) if ndvi else 0
                t_val_base = round(temp_mean_base, 1) if temp_mean_base else 0
                t_min_val_base = round(t_min_base, 1) if t_min_base else 0
                t_max_val_base = round(t_max_base, 1) if t_max_base else 0
                variance_base = round(t_max_val_base - t_min_val_base, 1)
                
                waste_multiplier = 0.04
                base_loss_lakhs = round(user_bill * max(0, (t_val_base - 28) * waste_multiplier), 2)

                st.session_state.report_data = {
                    "t_avg_base": t_val_base, 
                    "variance": variance_base, 
                    "t_min": t_min_val_base,
                    "t_max": t_max_val_base, 
                    "loss_base": base_loss_lakhs,
                    "ndvi": n_val
                }

                st.markdown("<hr style='margin-top: 5px; margin-bottom: 20px; border-color: #334155;'>", unsafe_allow_html=True)
                st.markdown("<div class='section-title'>Zone Temperature Profile</div>", unsafe_allow_html=True)
                
                cm1, cm2, cm3, cm4 = st.columns(4)
                cm1.markdown(f"<div class='metric-label'>Min Temp</div><div class='metric-value-small' style='color:#60A5FA;'>{t_min_val_base}°C</div>", unsafe_allow_html=True)
                cm2.markdown(f"<div class='metric-label'>Max Temp</div><div class='metric-value-small' style='color:#FCA5A5;'>{t_max_val_base}°C</div>", unsafe_allow_html=True)
                cm3.markdown(f"<div class='metric-label'>Avg Temp</div><div class='metric-value-small'>{t_val_base}°C</div>", unsafe_allow_html=True)
                cm4.markdown(f"<div class='metric-label'>Difference</div><div class='metric-value-small' style='color:#FCD34D;'>{variance_base}°C</div>", unsafe_allow_html=True)
                
                st.markdown(f"<div style='margin-top: 20px;'><span class='metric-value-small' style='color:#EF4444;'>₹ {base_loss_lakhs} Lakhs</span></div><div class='metric-label'>Estimated Loss due to Thermal Heat Trap</div>", unsafe_allow_html=True)

                st.info("💡 **Ready for Analysis:** Click 'Generate AI Report' on the top right to get recommendations and chat with the AI.")

            except Exception as error:
                st.error("Engine processing error. Sector may be too large or cloud cover detected.")
        else:
            st.markdown("<div style='color: #475569; font-size: 14px; margin-top: 50px;'>Use the polygon tool (⬟) on the map to outline a building or campus.</div>", unsafe_allow_html=True)

    with col_map:
        m = folium.Map(location=st.session_state.map_center, zoom_start=st.session_state.map_zoom)
        Geocoder(position='topright').add_to(m)
        Draw(export=True).add_to(m) 
        folium.TileLayer(tiles="https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}", attr="Google", name="Google Hybrid", overlay=False).add_to(m)

        if st.session_state.roi_geom:
            roi = ee.Geometry(st.session_state.roi_geom)
            l9_img = ee.ImageCollection("LANDSAT/LC09/C02/T1_L2").filterDate(start_date, end_date).filterBounds(roi).sort('CLOUD_COVER').first()
            thermal_raw = l9_img.select('ST_B10').multiply(0.00341802).add(149.0).subtract(273.15)
            thermal_hd = thermal_raw.resample('bicubic').reproject(crs=thermal_raw.projection(), scale=3)

            stats_fixed = thermal_hd.reduceRegion(reducer=ee.Reducer.percentile([5, 95]), geometry=roi, scale=30, maxPixels=1e9).getInfo()
            fixed_min = stats_fixed.get('ST_B10_p5', 20)
            fixed_max = stats_fixed.get('ST_B10_p95', 40)
            if fixed_max == fixed_min: fixed_max += 1

            vis_params = {
                'min': fixed_min, 
                'max': fixed_max, 
                'palette': ['#00008B', '#00FFFF', '#00FF00', '#FFFF00', '#FF7F00', '#FF0000', '#800000']
            }
            
            m.addLayer(thermal_hd.clip(roi), vis_params, 'Thermal Signature', opacity=0.55)
            empty_boundary = ee.Image().byte().paint(featureCollection=ee.FeatureCollection([ee.Feature(roi)]), color=1, width=3)
            m.addLayer(empty_boundary, {'palette': ['00FF88']}, 'Target Boundary')

        map_data = st_folium(m, height=750, use_container_width=True, key=f"map_update_dash")

        if map_data and map_data.get('last_active_drawing'):
            new_geom = map_data['last_active_drawing']['geometry']
            if st.session_state.roi_geom != new_geom:
                st.session_state.roi_geom = new_geom
                st.rerun()

# ==========================================
# 📊 PAGE 3: THE ESG, LEED & AI REPORT
# ==========================================
elif st.session_state.app_page == "Report":
    c1, c2 = st.columns([1, 5])
    with c1:
        st.markdown("<div class='sec-btn'>", unsafe_allow_html=True)
        if st.button("⬅ Back to Radar"):
            st.session_state.app_page = "Dashboard"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div class='header-main' style='font-size: 24px; margin-top: -2px;'>AI Intelligence Brief</div>", unsafe_allow_html=True)

    if not st.session_state.report_data:
        st.warning("No geospatial data in memory. Run Dashboard analysis.")
        st.stop()

    data = st.session_state.report_data
    loc = st.session_state.location_name.lower()

    if any(x in loc for x in ['school', 'college', 'university', 'iilm', 'institute', 'academy']):
        context_type = "Educational Campus"
        emoji = "🎓"
        recs = ["Deploy high-albedo elastomeric coatings on dormitories.", "Increase structural shading over pedestrian corridors between academic blocks."]
    elif any(x in loc for x in ['hospital', 'medical', 'clinic', 'health']):
        context_type = "Healthcare Facility"
        emoji = "🏥"
        recs = ["CRITICAL: Shield HVAC intake units from direct solar thermal reflection.", "Implement green roofing on flat wards to stabilize internal thermodynamics for patient comfort."]
    elif any(x in loc for x in ['metro', 'station', 'transit', 'railway', 'airport']):
        context_type = "Transit Hub / Station"
        emoji = "🚇"
        recs = ["Apply cool-roof paint to massive metal transit shelters.", "Increase canopy coverage in passenger pickup/drop-off asphalt zones."]
    elif any(x in loc for x in ['industry', 'industrial', 'factory', 'plant']):
        context_type = "Industrial Zone"
        emoji = "🏭"
        recs = ["Evaluate machinery exhaust heat compounding with solar radiation.", "Mandate highly reflective coatings on expansive warehouse flat roofs."]
    elif any(x in loc for x in ['ocean', 'sea', 'lake', 'river', 'water']):
        context_type = "Water Body"
        emoji = "🌊"
        recs = ["Monitor evaporation rates due to surrounding urban thermal bleed.", "Maintain riparian vegetation buffer zones to prevent thermal shock to the ecosystem."]
    else:
        context_type = "Urban / Commercial Sector"
        emoji = "🏙️"
        recs = ["Specify cool-roof materials for all subsequent flat-roof maintenance.", "Deploy localized canopy interventions over massive asphalt parking heat sinks."]

    st.markdown(f"<h3 style='color: #94A3B8; font-weight: 500; font-size: 16px;'>AI recognized location: <span style='color: #3B82F6; font-weight:bold;'>{emoji} {context_type}</span></h3>", unsafe_allow_html=True)
    st.markdown("<hr style='margin: 10px 0px 20px 0px; border-color: #334155;'>", unsafe_allow_html=True)

    cm1, cm2, cm3 = st.columns(3)
    cm1.markdown(f"<div style='background: rgba(255,255,255,0.02); padding: 20px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.05);'><div class='section-title'>Peak Thermal Threat</div><div class='metric-value-small' style='color:#FCA5A5;'>{data['t_max']}°C</div></div>", unsafe_allow_html=True)
    cm2.markdown(f"<div style='background: rgba(255,255,255,0.02); padding: 20px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.05);'><div class='section-title'>Vegetation Health (NDVI)</div><div class='metric-value-small' style='color:#6EE7B7;'>{data['ndvi']}</div></div>", unsafe_allow_html=True)
    cm3.markdown(f"<div style='background: rgba(255,255,255,0.02); padding: 20px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.05);'><div class='section-title'>Bill Wasted on Extra AC</div><div class='metric-value-small' style='color:#EF4444;'>₹ {data['loss_base']} Lakhs</div></div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col_ai, col_leed = st.columns([2, 1.5], gap="large")
    
    with col_ai:
        st.markdown(f"<div class='section-title' style='color: #3B82F6;'>🤖 Highly Personalized Baseline Action Plan</div>", unsafe_allow_html=True)
        st.markdown(f"""
        <div style='background: rgba(59, 130, 246, 0.05); padding: 20px; border-radius: 8px; border: 1px solid rgba(59, 130, 246, 0.2);'>
        <p style='color: #E2E8F0; font-size: 15px; margin-bottom: 10px;'>Because this is identified as a <b>{context_type}</b>, the system recommends:</p>
        <ul style='color: #CBD5E1; font-size: 15px; line-height: 1.8;'>
            <li>{recs[0]}</li>
            <li>{recs[1]}</li>
        </ul>
        <p style='color: #34D399; font-weight:bold; margin-top:10px;'>Talk to the AI below to simulate specific financial savings for your interventions!</p>
        </div>
        """, unsafe_allow_html=True)

    with col_leed:
        st.markdown("<div style='background: rgba(16, 185, 129, 0.05); border-left: 3px solid #10B981; padding: 20px; border-radius: 4px;'>", unsafe_allow_html=True)
        st.markdown("<h3 style='color: #10B981; font-size: 16px; margin-top:0px;'>🌱 LEED Certification Target</h3>", unsafe_allow_html=True)
        st.markdown("<p style='color: #A7F3D0; font-size: 14px;'><strong>Sustainable Sites (SS): Heat Island Reduction</strong></p>", unsafe_allow_html=True)
        st.markdown("<p style='color: #D1D5DB; font-size: 13px;'>By executing the AI Action Plan and ensuring at least <strong>50% high-reflectance coverage</strong> (cool roofs or canopies), this facility qualifies for <strong>+2 LEED Points</strong>.</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # --- 🌟 LIVE GEMINI AI CHATBOT 🌟 ---
    st.markdown("<hr style='margin: 30px 0px 20px 0px; border-color: #334155;'>", unsafe_allow_html=True)
    st.markdown("<div class='header-main' style='font-size: 20px;'>💬 Live Engineering Consultant (Gemini AI)</div>", unsafe_allow_html=True)
    st.markdown(f"<p style='color: #94A3B8; font-size: 14px;'>Ask specific questions about mitigating heat at {st.session_state.location_name}.</p>", unsafe_allow_html=True)
    
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
    if prompt := st.chat_input(f"e.g. 'What specific trees should we plant here to drop temps by 2 degrees?'"):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        with st.spinner("EcoPulse AI is analyzing orbital telemetry and architectural parameters..."):
            try:
                # ☢️ NUCLEAR BYPASS: Hardcoding the exact key provided to bypass Streamlit Secrets completely.
                genai.configure(api_key="AIzaSyDh0N_Xi-4G92p4gw757GB6JYFXf7Z7dIA")
                model = genai.GenerativeModel('gemini-pro')
                
                system_prompt = f"You are EcoPulse AI, an expert in urban heat mitigation, LEED certification, and sustainable architecture. The user is evaluating {st.session_state.location_name} (Type: {context_type}). The current average surface temperature is {data['t_avg_base']}°C with a thermal variance of {data['variance']}°C. The estimated financial cooling loss is ₹{data['loss_base']} Lakhs. Answer the following query concisely, professionally, and provide actionable engineering/botanical advice: {prompt}"
                
                response = model.generate_content(system_prompt)
                ai_response = response.text
                
            except Exception as e:
                # This will print the exact reason if it fails again
                ai_response = f"⚠️ **System Error:** {str(e)}"
                
        st.session_state.chat_history.append({"role": "assistant", "content": ai_response})
        with st.chat_message("assistant"):
            st.markdown(ai_response)

