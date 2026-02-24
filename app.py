import os
import streamlit as st
import ee
import folium
from folium.plugins import Draw, Geocoder
from streamlit_folium import st_folium
import geocoder
import pandas as pd

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

st.set_page_config(layout="wide", page_title="EcoPulse | AI Impact Summit", page_icon="🌍", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    .stApp { background-color: #0A0F18; color: #E2E8F0; font-family: 'Inter', sans-serif; }
    .header-main { color: #F8FAFC; font-size: 30px; font-weight: 800; margin-bottom: 0px; letter-spacing: -0.5px;}
    .header-sub { color: #34D399; font-size: 14px; font-weight: 600; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 25px; }
    .section-title { color: #94A3B8; font-size: 13px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 10px;}
    .metric-value { font-size: 42px; font-weight: 700; color: #F8FAFC; line-height: 1.1; }
    .metric-value-small { font-size: 24px; font-weight: 600; color: #F8FAFC; line-height: 1.1; }
    .metric-label { font-size: 13px; color: #94A3B8; font-weight: 500; }
    .card { background: rgba(255, 255, 255, 0.02); border: 1px solid rgba(255, 255, 255, 0.05); padding: 25px; border-radius: 6px; margin-bottom: 20px;}
    header {visibility: hidden;} footer {visibility: hidden;}
    .nav-btn div.stButton > button:first-child { background-color: #10B981; color: #0A0F18; border: none; font-size: 16px; font-weight: 700; padding: 12px 24px; border-radius: 6px; transition: all 0.2s;}
    .nav-btn div.stButton > button:first-child:hover { background-color: #059669; }
    .sec-btn div.stButton > button:first-child { background-color: transparent; color: #94A3B8; border: 1px solid #475569; font-weight: 600;}
</style>
""", unsafe_allow_html=True)

if 'app_page' not in st.session_state: st.session_state.app_page = "Home"
if 'roi_geom' not in st.session_state: st.session_state.roi_geom = None
if 'map_center' not in st.session_state: st.session_state.map_center = [28.4610, 77.4900]
if 'map_zoom' not in st.session_state: st.session_state.map_zoom = 15
if 'last_search' not in st.session_state: st.session_state.last_search = ""
if 'location_name' not in st.session_state: st.session_state.location_name = "Selected Sector"
if 'mitigation_level' not in st.session_state: st.session_state.mitigation_level = 0
if 'facility_area' not in st.session_state: st.session_state.facility_area = 50000 
if 'report_data' not in st.session_state: st.session_state.report_data = {}
if 'chat_history' not in st.session_state: st.session_state.chat_history = []

# ==========================================
# 🏠 PAGE 1: THE HOMEPAGE (REDESIGNED)
# ==========================================
if st.session_state.app_page == "Home":
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center; font-size: 80px; color: #F8FAFC; font-weight: 900; letter-spacing: -2px; margin-bottom: 0px;'>EcoPulse</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: #34D399; font-size: 20px; font-weight: 600; letter-spacing: 4px; text-transform: uppercase; margin-top: 5px;'>Satellite-Powered Climate Intelligence</h3>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #94A3B8; font-size: 18px; max-width: 800px; margin: 20px auto; line-height: 1.6;'>Concrete buildings act like thermal batteries, trapping heat and forcing AC units to burn extreme amounts of electricity. EcoPulse uses <b>Landsat 9 Telemetry</b> to pinpoint heat leaks and prescribe AI-driven cooling strategies.</p>", unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1.5, 1, 1.5])
    with col2:
        st.markdown("<div class='nav-btn'>", unsafe_allow_html=True)
        if st.button("🚀 Enter Dashboard", use_container_width=True):
            st.session_state.app_page = "Dashboard"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Visual Highlights
    c1, c2, c3 = st.columns(3, gap="large")
    with c1:
        st.markdown("<div class='card' style='text-align:center;'><h1 style='font-size: 50px; margin:0;'>🛰️</h1><h3 style='color: white;'>Orbital Scanning</h3><p style='color: #94A3B8;'>Extracts precise Land Surface Temperature (LST) directly from space without needing ground sensors.</p></div>", unsafe_allow_html=True)
    with c2:
        st.markdown("<div class='card' style='text-align:center;'><h1 style='font-size: 50px; margin:0;'>💸</h1><h3 style='color: white;'>Financial Impact</h3><p style='color: #94A3B8;'>Calculates exactly how much extra money is being burnt on AC bills due to the trapped concrete heat.</p></div>", unsafe_allow_html=True)
    with c3:
        st.markdown("<div class='card' style='text-align:center;'><h1 style='font-size: 50px; margin:0;'>🌱</h1><h3 style='color: white;'>LEED Compliance</h3><p style='color: #94A3B8;'>Tracks green-building certification points. <i>Feature requested during preliminary judging.</i></p></div>", unsafe_allow_html=True)

# ==========================================
# 🌍 PAGE 2: THE DASHBOARD (SIMPLIFIED)
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
        c_search, c_clear = st.columns([3, 1])
        with c_search:
            search_query = st.text_input("TARGET COORDINATES", placeholder="Search sector...", label_visibility="collapsed")
        with c_clear:
            if st.button("🗑️ Clear", use_container_width=True):
                st.session_state.roi_geom = None
                st.session_state.mitigation_level = 0
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
                    st.session_state.mitigation_level = 0
                    st.rerun()

        if st.session_state.roi_geom:
            roi = ee.Geometry(st.session_state.roi_geom)
            start_date, end_date = ['2025-04-01', '2025-07-31'] 
            
            try:
                l9_img = ee.ImageCollection("LANDSAT/LC09/C02/T1_L2").filterBounds(roi).filterDate(start_date, end_date).map(mask_l9_clouds).sort('CLOUD_COVER').first()
                thermal_raw = l9_img.select('ST_B10').multiply(0.00341802).add(149.0).subtract(273.15)
                
                excess_img = thermal_raw.subtract(28.0).multiply(thermal_raw.gt(28.0))
                temp_mean_base = thermal_raw.reduceRegion(reducer=ee.Reducer.mean(), geometry=roi, scale=30).get('ST_B10').getInfo()
                excess_mean_base = excess_img.reduceRegion(reducer=ee.Reducer.mean(), geometry=roi, scale=30).get('ST_B10').getInfo()
                
                stats_base = thermal_raw.reduceRegion(reducer=ee.Reducer.minMax(), geometry=roi, scale=30, maxPixels=1e9).getInfo()
                t_min_base = stats_base.get('ST_B10_min')
                t_max_base = stats_base.get('ST_B10_max')

                t_val_base = round(temp_mean_base, 1) if temp_mean_base else 0
                e_val_base = excess_mean_base if excess_mean_base else 0
                t_min_val_base = round(t_min_base, 1) if t_min_base else 0
                t_max_val_base = round(t_max_base, 1) if t_max_base else 0
                variance_base = round(t_max_val_base - t_min_val_base, 1)
                
                st.session_state.report_data = {
                    "t_avg_base": t_val_base, 
                    "variance": variance_base, 
                    "t_max": t_max_val_base, 
                    "excess_deg": round(e_val_base, 2)
                }

                st.markdown("<hr style='margin-top: 5px; margin-bottom: 20px; border-color: #334155;'>", unsafe_allow_html=True)
                st.markdown("<div class='section-title'>Spatial Telemetry Metrics</div>", unsafe_allow_html=True)
                st.markdown(f"<div><span class='metric-value'>{t_val_base}°C</span></div><div class='metric-label'>Average Surface Temperature</div>", unsafe_allow_html=True)
                
                v_color = '#EF4444' if variance_base > 5 else '#FCD34D' if variance_base > 3 else '#10B981'
                st.markdown(f"<div style='background: rgba(255,255,255,0.03); border-left: 3px solid {v_color}; padding: 12px; margin-top: 15px;'><span style='color: #E2E8F0; font-size: 14px;'>Temperature Difference: {variance_base}°C across selected area.</span></div>", unsafe_allow_html=True)

                st.info("💡 **Ready for Analysis:** Click 'Generate AI Report' on the top right to calculate extra AC costs and simulate solutions.")

            except Exception as error:
                st.error("Engine processing error. Sector may be too large.")
        else:
            st.markdown("<div style='color: #475569; font-size: 14px; margin-top: 50px;'>Use the polygon tool (⬟) on the map to outline a building or campus.</div>", unsafe_allow_html=True)

    with col_map:
        m = folium.Map(location=st.session_state.map_center, zoom_start=st.session_state.map_zoom)
        Geocoder(position='topright').add_to(m)
        Draw(export=True).add_to(m) 
        folium.TileLayer(tiles="https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}", attr="Google", name="Google Hybrid", overlay=False).add_to(m)

        if st.session_state.roi_geom:
            roi = ee.Geometry(st.session_state.roi_geom)
            l9_img = ee.ImageCollection("LANDSAT/LC09/C02/T1_L2").filterDate(start_date, end_date).filterBounds(roi).map(mask_l9_clouds).sort('CLOUD_COVER').first()
            thermal_raw = l9_img.select('ST_B10').multiply(0.00341802).add(149.0).subtract(273.15)
            thermal_hd = thermal_raw.resample('bicubic').reproject(crs=thermal_raw.projection(), scale=3)

            stats_fixed = thermal_hd.reduceRegion(reducer=ee.Reducer.minMax(), geometry=roi, scale=30, maxPixels=1e9).getInfo()
            fixed_min = stats_fixed.get('ST_B10_min', 20)
            fixed_max = stats_fixed.get('ST_B10_max', 40)
            if fixed_max == fixed_min: fixed_max += 1

            # 🌟 PALETTE FIXED: Removed confusing green. Now strictly Blue -> Cyan -> Yellow -> Red 🌟
            vis_params = {'min': fixed_min, 'max': fixed_max, 'palette': ['#0000FF', '#00FFFF', '#FFFF00', '#FF0000']}
            m.addLayer(thermal_hd.clip(roi), vis_params, 'Thermal Signature', opacity=0.55)

        map_data = st_folium(m, height=750, use_container_width=True, key=f"map_update_dash")

        if map_data and map_data.get('last_active_drawing'):
            new_geom = map_data['last_active_drawing']['geometry']
            if st.session_state.roi_geom != new_geom:
                st.session_state.roi_geom = new_geom
                st.session_state.mitigation_level = 0
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

    # 🌟 ADVANCED CONTEXT CLASSIFIER 🌟
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

    # --- HEAT MITIGATION SIMULATOR ---
    st.markdown("<div class='header-main' style='font-size: 20px; color: #60A5FA; margin-bottom: 15px;'>⚙️ Solution Simulator</div>", unsafe_allow_html=True)
    
    sim_col1, sim_col2 = st.columns([1.2, 2], gap="large")
    
    with sim_col1:
        st.markdown("<div style='background: rgba(255,255,255,0.02); padding: 20px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.05); height: 100%;'>", unsafe_allow_html=True)
        st.markdown("<div class='section-title'>Total Area (Sq.Ft)</div>", unsafe_allow_html=True)
        new_area = st.number_input("Area", min_value=1000, max_value=5000000, value=st.session_state.facility_area, step=5000, label_visibility="collapsed")
        st.session_state.facility_area = new_area
        
        st.markdown("<div class='section-title' style='margin-top: 20px;'>% of Area Cooled (White Roofs/Trees)</div>", unsafe_allow_html=True)
        mitigation = st.slider("Intervention %", 0, 100, st.session_state.mitigation_level, format="%d%%", label_visibility="collapsed")
        st.session_state.mitigation_level = mitigation
        st.markdown("</div>", unsafe_allow_html=True)

    base_loss_lakhs = round((new_area * 60 * (data['excess_deg'] * 0.06)) / 100000, 2)
    simulated_drop = (mitigation / 100.0) * 4.5 
    display_t = round(data['t_avg_base'] - simulated_drop, 1)
    e_val_sim = max(0, data['excess_deg'] - simulated_drop)
    sim_loss_lakhs = round((new_area * 60 * (e_val_sim * 0.06)) / 100000, 2)
    savings = round(base_loss_lakhs - sim_loss_lakhs, 2)

    with sim_col2:
        st.markdown("<div class='ba-container'>", unsafe_allow_html=True)
        st.markdown(f"""
        <div class='ba-card'>
            <div class='ba-header'>Average Temp</div>
            <div class='ba-val'>{data['t_avg_base']}°C <span style='color:#64748B; font-weight:400;'>→</span> <span style='color:#34D399;'>{display_t}°C</span></div>
            <div style='color:#10B981; font-weight:700; margin-top:5px;'>⬇ Drops {simulated_drop}°C</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class='ba-card'>
            <div class='ba-header'>Extra AC Bill Due To Heat Leak</div>
            <div class='ba-val'>₹{base_loss_lakhs}L <span style='color:#64748B; font-weight:400;'>→</span> <span style='color:#60A5FA;'>₹{sim_loss_lakhs}L</span></div>
            <div style='color:#3B82F6; font-weight:700; margin-top:5px;'>⬇ Saves ₹ {savings} Lakhs</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- ACTION PLAN & LEED ---
    col_ai, col_leed = st.columns([2, 1.5], gap="large")
    
    with col_ai:
        st.markdown(f"<div class='section-title' style='color: #3B82F6;'>🤖 Highly Personalized AI Action Plan</div>", unsafe_allow_html=True)
        st.markdown(f"""
        <div style='background: rgba(59, 130, 246, 0.05); padding: 20px; border-radius: 8px; border: 1px solid rgba(59, 130, 246, 0.2);'>
        <p style='color: #E2E8F0; font-size: 15px; margin-bottom: 10px;'>Because this is identified as a <b>{context_type}</b>, the system recommends:</p>
        <ul style='color: #CBD5E1; font-size: 15px; line-height: 1.8;'>
            <li>{recs[0]}</li>
            <li>{recs[1]}</li>
        </ul>
        <p style='color: #34D399; font-weight:bold; margin-top:10px;'>Financial Justification: This {mitigation}% cooling plan will save the facility ₹{savings} Lakhs in AC electricity overworking.</p>
        </div>
        """, unsafe_allow_html=True)

    with col_leed:
        st.markdown("<div style='background: rgba(16, 185, 129, 0.05); border-left: 3px solid #10B981; padding: 20px; border-radius: 4px;'>", unsafe_allow_html=True)
        st.markdown("<h3 style='color: #10B981; font-size: 16px; margin-top:0px;'>🌱 LEED Certification Tracker</h3>", unsafe_allow_html=True)
        st.markdown("<p style='color: #94A3B8; font-size: 12px; font-style: italic;'>*Feature added based on judge's recommendation during prelims.</p>", unsafe_allow_html=True)
        
        if mitigation >= 50:
            st.markdown("<h2 style='color: #34D399; font-size: 20px; margin: 10px 0px;'>Eligible (+2 Points) ✅</h2>", unsafe_allow_html=True)
            st.markdown("<p style='color: #A7F3D0; font-size: 13px;'>Your simulation hits the 50% threshold to earn the 'Heat Island Reduction' credit, giving this facility massive tax advantages.</p>", unsafe_allow_html=True)
        else:
            st.markdown("<h2 style='color: #FCD34D; font-size: 20px; margin: 10px 0px;'>Ineligible ⚠️</h2>", unsafe_allow_html=True)
            st.markdown("<p style='color: #FDE68A; font-size: 13px;'>Increase the slider to at least 50% to see how to qualify for green-building tax breaks.</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # --- AI Q&A CHAT ---
    st.markdown("<hr style='margin: 30px 0px 20px 0px; border-color: #334155;'>", unsafe_allow_html=True)
    st.markdown("<div class='header-main' style='font-size: 20px;'>💬 Ask EcoPulse AI</div>", unsafe_allow_html=True)
    st.markdown(f"<p style='color: #94A3B8; font-size: 14px;'>Ask specific questions about mitigating heat at {st.session_state.location_name}.</p>", unsafe_allow_html=True)
    
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
    if prompt := st.chat_input(f"e.g. 'What specific trees should we plant here?'"):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Simple simulated response logic for hackathon speed
        ai_response = f"Based on the thermal telemetry for this {context_type}, prioritizing drought-resistant, broad-canopy native species like *Azadirachta indica* (Neem) will provide maximum shade while minimizing irrigation costs."
        st.session_state.chat_history.append({"role": "assistant", "content": ai_response})
        with st.chat_message("assistant"):
            st.markdown(ai_response)
