import streamlit as st
import ee
import folium
from folium.plugins import Draw
from streamlit_folium import st_folium
import geocoder
from datetime import datetime
from dateutil.relativedelta import relativedelta
import os

# --- 🌟 THE "HERO" FIX: Bypassing geemap entirely 🌟 ---
def add_ee_layer(self, ee_image_object, vis_params, name, opacity=1):
    map_id_dict = ee.Image(ee_image_object).getMapId(vis_params)
    folium.raster_layers.TileLayer(
        tiles=map_id_dict['tile_fetcher'].url_format,
        attr='Google Earth Engine',
        name=name,
        overlay=True,
        control=True,
        opacity=opacity
    ).add_to(self)

folium.Map.addLayer = add_ee_layer
# ---------------------------------------------------------

# 1. High-Tech App Config
st.set_page_config(layout="wide", page_title="EcoPulse | AI Summit 2026", page_icon="🌍", initial_sidebar_state="collapsed")

# 2. Premium "Enterprise SaaS" CSS Injection
st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; padding-bottom: 0rem; padding-left: 3rem; padding-right: 3rem; max-width: 100%; }
    .stApp { background-color: #0A0F18; color: #E2E8F0; font-family: 'Inter', sans-serif; }
    hr { border-top: 1px solid rgba(255, 255, 255, 0.1); margin-top: 1.5rem; margin-bottom: 1.5rem; }
    .header-main { color: #F8FAFC; font-size: 34px; font-weight: 800; margin-bottom: 0px; letter-spacing: -0.5px;}
    .header-sub { color: #00FF88; font-size: 16px; font-weight: 600; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 25px; }
    .section-title { color: #94A3B8; font-size: 14px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 10px;}
    .metric-value { font-size: 56px; font-weight: 800; color: #F8FAFC; line-height: 1.1; transition: color 0.3s; }
    .metric-value-small { font-size: 28px; font-weight: 700; color: #F8FAFC; line-height: 1.1; }
    .metric-label { font-size: 16px; color: #94A3B8; font-weight: 500; }
    .shock-box { background: rgba(239, 68, 68, 0.1); border-left: 4px solid #EF4444; padding: 12px; border-radius: 4px; margin-top: 15px; margin-bottom: 15px;}
    .shock-text { color: #FCA5A5; font-size: 15px; font-weight: 600; }
    .badge-high { background-color: rgba(239, 68, 68, 0.15); color: #FCA5A5; padding: 6px 12px; border-radius: 12px; font-size: 13px; font-weight: 700; border: 1px solid rgba(239, 68, 68, 0.3); }
    .badge-warn { background-color: rgba(245, 158, 11, 0.15); color: #FCD34D; padding: 6px 12px; border-radius: 12px; font-size: 13px; font-weight: 700; border: 1px solid rgba(245, 158, 11, 0.3); }
    .badge-good { background-color: rgba(16, 185, 129, 0.15); color: #6EE7B7; padding: 6px 12px; border-radius: 12px; font-size: 13px; font-weight: 700; border: 1px solid rgba(16, 185, 129, 0.3); }
    .ai-box { background: linear-gradient(145deg, rgba(16, 185, 129, 0.05) 0%, rgba(59, 130, 246, 0.05) 100%); border-left: 4px solid #3B82F6; padding: 20px; border-radius: 0px 8px 8px 0px; margin-top: 20px; }
    .ai-title { color: #60A5FA; font-size: 15px; font-weight: 800; margin-bottom: 10px; display: flex; align-items: center; gap: 6px; }
    .ai-text { color: #CBD5E1; font-size: 15px; line-height: 1.6; margin-bottom: 6px; }
    
    /* Sleek Clear Button & Launch Button */
    div.stButton > button:first-child { background-color: transparent; color: #F87171; border: 1px solid rgba(239, 68, 68, 0.4); border-radius: 6px; font-weight: 600; transition: all 0.3s ease;}
    div.stButton > button:first-child:hover { background-color: rgba(239, 68, 68, 0.1); border: 1px solid #EF4444; }
    
    /* Special styling for the giant Launch button */
    .launch-btn div.stButton > button:first-child { background-color: #00FF88; color: #0A0F18; border: none; font-size: 20px; font-weight: 800; padding: 15px 30px; border-radius: 8px;}
    .launch-btn div.stButton > button:first-child:hover { background-color: #34D399; color: #0A0F18; box-shadow: 0px 0px 20px rgba(0, 255, 136, 0.4);}
    
    header {visibility: hidden;} footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- GLOBAL SESSION STATES ---
if 'roi_geom' not in st.session_state: st.session_state.roi_geom = None
if 'map_center' not in st.session_state: st.session_state.map_center = [28.4610, 77.4900]
if 'map_zoom' not in st.session_state: st.session_state.map_zoom = 15
if 'last_search' not in st.session_state: st.session_state.last_search = ""
if 'mitigation_level' not in st.session_state: st.session_state.mitigation_level = 0
if 'app_page' not in st.session_state: st.session_state.app_page = "Home"

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
    st.markdown("<h1 style='text-align: center; font-size: 90px; color: #F8FAFC; font-weight: 900; letter-spacing: -2px; margin-bottom: 0px;'>EcoPulse</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: #00FF88; font-size: 24px; font-weight: 600; letter-spacing: 4px; text-transform: uppercase; margin-top: -10px;'>Global Climate Intelligence</h3>", unsafe_allow_html=True)
    
    st.markdown("<p style='text-align: center; color: #94A3B8; font-size: 18px; max-width: 800px; margin: 0 auto; margin-top: 30px; line-height: 1.6;'>An advanced AI-driven platform designed to monitor, predict, and mitigate Urban Heat Islands. Leveraging Google Earth Engine and high-fidelity thermal telemetry, EcoPulse identifies critical heat sinks and simulates real-time financial ROI for structural cooling investments.</p>", unsafe_allow_html=True)
    
    st.markdown("<p style='text-align: center; color: #CBD5E1; font-size: 15px; margin-top: 20px;'><b>AI Summit 2026 Live Demo</b><br>Developed by B.Tech CSE, IILM University</p>", unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Center the launch button
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown("<div class='launch-btn'>", unsafe_allow_html=True)
        if st.button("🚀 Initialize Global Radar", use_container_width=True):
            st.session_state.app_page = "Dashboard"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    # 🌟 NEW: HERO IMAGE CENTERED ON THE FRONT PAGE
    col_img1, col_img2, col_img3 = st.columns([1, 4, 1])
    with col_img2:
        try:
            st.image("sample_thermal_map.png", caption="Sample Thermal Variance Scan: Supreme Court Area & Bharat Mandapam", use_container_width=True)
        except Exception:
            st.warning("Please upload 'sample_thermal_map.png' to your GitHub repository to display the Hero image.")
        
    st.markdown("<hr style='margin-top: 50px; opacity: 0.2;'>", unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns(3)
    c1.markdown("<h4 style='color: #60A5FA; text-align: center;'>🛰️ Orbital Telemetry</h4><p style='color: #64748B; text-align: center; font-size: 14px;'>Processes Landsat 9 thermal bands using custom bicubic algorithms to map building-level heat leakage.</p>", unsafe_allow_html=True)
    c2.markdown("<h4 style='color: #34D399; text-align: center;'>🧪 AI Mitigation</h4><p style='color: #64748B; text-align: center; font-size: 14px;'>Predictive modeling simulates the impact of high-albedo coatings and green canopies on ambient temperatures.</p>", unsafe_allow_html=True)
    c3.markdown("<h4 style='color: #F87171; text-align: center;'>📉 Financial Modeling</h4><p style='color: #64748B; text-align: center; font-size: 14px;'>Translates raw thermal variance into estimated annual HVAC energy losses and cooling taxes.</p>", unsafe_allow_html=True)


# ==========================================
# 🌍 PAGE 2: THE DASHBOARD
# ==========================================
elif st.session_state.app_page == "Dashboard":

    with st.spinner("Establishing secure orbital link..."):
        try:
            ee_path = os.path.expanduser('~/.config/earthengine')
            os.makedirs(ee_path, exist_ok=True)
            
            with open(os.path.join(ee_path, 'credentials'), 'w') as f:
                f.write(st.secrets["EARTHENGINE_TOKEN"])
                
            ee.Initialize(project='ecoplus-iilm')
            if not hasattr(ee.data, '_credentials'): ee.data._credentials = True

        except Exception as e:
            st.error(f"Earth Engine Connection Failed: {e}")
            st.stop()

    col_back, col_title = st.columns([0.5, 4])
    with col_back:
        if st.button("⬅ Home"):
            st.session_state.app_page = "Home"
            st.rerun()
    with col_title:
        st.markdown("<div class='header-main' style='font-size: 28px; margin-top: -5px;'>EcoPulse | Global Climate Intelligence</div>", unsafe_allow_html=True)
        st.markdown("<div class='header-sub' style='margin-bottom: 15px;'>AI Summit 2026 Live Demo</div>", unsafe_allow_html=True)

    col_insight, col_map = st.columns([1.5, 2.5], gap="large")

    with col_insight:
        search_query = st.text_input("📍 GLOBAL TARGETING SYSTEM", placeholder="Search 'Hyde Park London', 'Stanford'...", label_visibility="collapsed")
        if search_query and search_query != st.session_state.last_search:
            with st.spinner(f"Locking coordinates for {search_query}..."):
                g = geocoder.arcgis(search_query)
                if g.ok:
                    st.session_state.map_center = [g.lat, g.lng]
                    st.session_state.map_zoom = 16
                    st.session_state.roi_geom = None
                    st.session_state.last_search = search_query
                    st.session_state.mitigation_level = 0
                    st.rerun()
                    
        st.write("")
        st.markdown("<div class='section-title'>Orbital Timeframe Filter</div>", unsafe_allow_html=True)
        
        col_time, col_clear = st.columns([3, 1.5])
        with col_time:
            timeframe = st.selectbox("Timeframe", list(dates.keys()), label_visibility="collapsed")
            start_date, end_date = dates[timeframe]
        with col_clear:
            if st.button("🗑️ Clear Scan", use_container_width=True):
                st.session_state.roi_geom = None
                st.session_state.mitigation_level = 0
                st.rerun()

        st.markdown("<hr>", unsafe_allow_html=True)

        if st.session_state.roi_geom:
            roi = ee.Geometry(st.session_state.roi_geom)
            
            try:
                l9_img = ee.ImageCollection("LANDSAT/LC09/C02/T1_L2").filterBounds(roi).filterDate(start_date, end_date).sort('CLOUD_COVER').first()
                s2_img = ee.ImageCollection('COPERNICUS/S2_SR').filterBounds(roi).filterDate(start_date, end_date).sort('CLOUDY_PIXEL_PERCENTAGE').first()
                
                ndvi = s2_img.normalizedDifference(['B8', 'B4']).reduceRegion(reducer=ee.Reducer.mean(), geometry=roi, scale=10).get('nd').getInfo()
                thermal_raw = l9_img.select('ST_B10').multiply(0.00341802).add(149.0).subtract(273.15)
                
                temp_mean_base = thermal_raw.reduceRegion(reducer=ee.Reducer.mean(), geometry=roi, scale=30).get('ST_B10').getInfo()
                stats_base = thermal_raw.reduceRegion(reducer=ee.Reducer.percentile([5, 95]), geometry=roi, scale=30, maxPixels=1e9).getInfo()
                t_min_base = stats_base.get('ST_B10_p5')
                t_max_base = stats_base.get('ST_B10_p95')

                n_val = round(ndvi, 2) if ndvi else 0
                t_val_base = round(temp_mean_base, 1) if temp_mean_base else 0
                t_min_val_base = round(t_min_base, 1) if t_min_base else 0
                t_max_val_base = round(t_max_base, 1) if t_max_base else 0
                variance_base = round(t_max_val_base - t_min_val_base, 1)
                
                st.markdown("<div class='section-title' style='color: #3B82F6;'>🧪 AI Mitigation Simulator</div>", unsafe_allow_html=True)
                st.markdown("<p style='color: #94A3B8; font-size: 13px; margin-top: -5px;'>Drag slider to simulate converting roofs to High-Albedo materials and adding Green Canopy.</p>", unsafe_allow_html=True)
                
                mitigation = st.slider("Investment", 0, 100, st.session_state.mitigation_level, format="%d%%", label_visibility="collapsed", key="mitigation_slider")
                st.session_state.mitigation_level = mitigation 

                simulated_drop = (mitigation / 100.0) * 4.5 
                
                display_t = round(t_val_base - simulated_drop, 1)
                display_var = round(max(0.5, variance_base - (simulated_drop * 1.1)), 1)
                display_color = "#34D399" if mitigation > 30 else "#F8FAFC"
                
                base_loss = 4.2 if t_val_base > 35 else 2.8 if t_val_base > 28 else 1.1
                sim_loss = round(base_loss - ((mitigation/100) * base_loss * 0.7), 2)
                
                st.markdown("<hr style='margin-top: 5px; margin-bottom: 20px;'>", unsafe_allow_html=True)
                
                st.markdown("<div class='section-title'>Zone Temperature Profile</div>", unsafe_allow_html=True)
                st.markdown(f"<div><span class='metric-value' style='color: {display_color};'>{display_t}°C</span></div><div class='metric-label'>Average Surface Temperature (LST)</div>", unsafe_allow_html=True)
                
                c1, c2 = st.columns(2)
                c1.markdown(f"<div><span class='metric-value-small'>{t_min_val_base}°C</span></div><div class='metric-label' style='font-size:13px;'>Original Coolest Point</div>", unsafe_allow_html=True)
                c2.markdown(f"<div><span class='metric-value-small' style='color:#FCA5A5;'>{t_max_val_base}°C</span></div><div class='metric-label' style='font-size:13px;'>Original Hottest Building</div>", unsafe_allow_html=True)
                
                if display_var > 4:
                    st.markdown(f"<div class='shock-box'><span class='shock-text'>⚠️ THERMAL VARIANCE: {display_var}°C</span><br><span style='color:#CBD5E1; font-size: 13px;'>Massive heat difference persists.</span></div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div class='shock-box' style='background: rgba(16, 185, 129, 0.1); border-left-color: #10B981;'><span class='shock-text' style='color: #34D399;'>✅ THERMAL VARIANCE: {display_var}°C</span><br><span style='color:#CBD5E1; font-size: 13px;'>Temperatures stabilized across the sector.</span></div>", unsafe_allow_html=True)
                
                st.write("")
                st.markdown(f"<div><span class='metric-value-small'>₹ {sim_loss} Lakhs</span></div><div class='metric-label'>Est. Annual Energy Loss (Cooling Taxes)</div>", unsafe_allow_html=True)
                st.markdown("<hr>", unsafe_allow_html=True)

                st.markdown("<div class='section-title'>Risk Summary</div>", unsafe_allow_html=True)
                heat_badge = "badge-high'>HIGH RISK 🔴" if display_var > 8 else "badge-warn'>ELEVATED 🟠" if display_var > 4 else "badge-good'>STABLE 🟢"
                green_badge = "badge-high'>CRITICAL 🔴" if n_val < 0.15 else "badge-warn'>MODERATE 🟠" if n_val < 0.35 else "badge-good'>HEALTHY 🟢"
                
                col_b1, col_b2 = st.columns(2)
                col_b1.markdown(f"<span class='{heat_badge}</span>", unsafe_allow_html=True)
                col_b2.markdown(f"<span class='{green_badge}</span>", unsafe_allow_html=True)

            except Exception as error:
                st.error("Telemetry sync failed. Area might be too large or lack clear satellite data for those dates.")
        else:
            st.markdown("<div style='color: #64748B; font-size: 18px; margin-top: 50px;'>Awaiting sector selection...<br>Use the ⬟ tool on the map to outline a campus zone.</div>", unsafe_allow_html=True)

    with col_map:
        m = folium.Map(location=st.session_state.map_center, zoom_start=st.session_state.map_zoom)
        Draw(export=True).add_to(m) 
        
        folium.TileLayer(
            tiles="https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}",
            attr="Google", name="Google Hybrid", overlay=False, control=True
        ).add_to(m)

        if st.session_state.roi_geom:
            roi = ee.Geometry(st.session_state.roi_geom)
            
            l9_img = ee.ImageCollection("LANDSAT/LC09/C02/T1_L2").filterDate(start_date, end_date).filterBounds(roi).sort('CLOUD_COVER').first()
            thermal_raw = l9_img.select('ST_B10').multiply(0.00341802).add(149.0).subtract(273.15)
            
            thermal_hd = thermal_raw.resample('bicubic').reproject(crs=thermal_raw.projection(), scale=3)

            stats_fixed = thermal_hd.reduceRegion(reducer=ee.Reducer.percentile([5, 95]), geometry=roi, scale=30, maxPixels=1e9).getInfo()
            fixed_min = stats_fixed.get('ST_B10_p5', 20)
            fixed_max = stats_fixed.get('ST_B10_p95', 40)
            if fixed_max == fixed_min: fixed_max += 1

            current_mitigation = st.session_state.mitigation_level
            max_sim_drop = (current_mitigation / 100.0) * 4.5 
            
            thermal_norm = thermal_hd.subtract(fixed_min).divide(fixed_max - fixed_min).clamp(0, 1)
            cooling_layer = thermal_norm.multiply(max_sim_drop)
            thermal_simulated = thermal_hd.subtract(cooling_layer)
            thermal_final = thermal_simulated.clip(roi)

            vis_params = {
                'min': fixed_min, 
                'max': fixed_max, 
                'palette': ['#00008B', '#00FFFF', '#00FF00', '#FFFF00', '#FF7F00', '#FF0000', '#800000']
            }
            
            layer_name = f'Simulation: {current_mitigation}% Investment'
            m.addLayer(thermal_final, vis_params, layer_name, opacity=0.55)
            
            empty_boundary = ee.Image().byte().paint(featureCollection=ee.FeatureCollection([ee.Feature(roi)]), color=1, width=3)
            m.addLayer(empty_boundary, {'palette': ['00FF88']}, 'Target Boundary')

        map_data = st_folium(m, height=750, use_container_width=True, key=f"map_update_{st.session_state.mitigation_level}")

        if map_data and map_data.get('last_active_drawing'):
            new_geom = map_data['last_active_drawing']['geometry']
            if st.session_state.roi_geom != new_geom:
                st.session_state.roi_geom = new_geom
                st.session_state.mitigation_level = 0
                st.rerun()
