import os
import streamlit as st
import ee
import folium
from folium.plugins import Draw, Geocoder
from streamlit_folium import st_folium
import geocoder
import pandas as pd

# --- 🌟 CORE ENGINE FIX (UNTOUCHED) 🌟 ---
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

st.set_page_config(layout="wide", page_title="EcoPulse | Spatial Climate Intelligence", page_icon="🌍", initial_sidebar_state="collapsed")

# --- UI/UX ENTERPRISE STYLES ---
st.markdown("""
<style>
    .stApp { background-color: #0A0F18; color: #E2E8F0; font-family: 'Inter', sans-serif; }
    
    /* Typography */
    .header-main { color: #F8FAFC; font-size: 30px; font-weight: 800; margin-bottom: 0px; letter-spacing: -0.5px;}
    .header-sub { color: #34D399; font-size: 14px; font-weight: 600; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 25px; }
    .section-title { color: #94A3B8; font-size: 13px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 10px;}
    
    /* Dashboard Metrics */
    .metric-value { font-size: 42px; font-weight: 700; color: #F8FAFC; line-height: 1.1; }
    .metric-value-small { font-size: 24px; font-weight: 600; color: #F8FAFC; line-height: 1.1; }
    .metric-label { font-size: 13px; color: #94A3B8; font-weight: 500; }
    
    /* Report Page Hero Cards */
    .hero-card { background: rgba(30, 41, 59, 0.4); border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 12px; padding: 24px; height: 100%; display: flex; flex-direction: column; justify-content: center; transition: transform 0.2s;}
    .hero-card:hover { transform: translateY(-3px); border-color: rgba(255, 255, 255, 0.1); }
    .hero-title { font-size: 14px; color: #94A3B8; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px;}
    .hero-data { font-size: 48px; font-weight: 900; color: #F8FAFC; line-height: 1;}
    .hero-subdata { font-size: 14px; color: #64748B; margin-top: 8px; font-weight: 500;}
    
    /* Badges */
    .risk-badge-high { background-color: rgba(239, 68, 68, 0.15); color: #FCA5A5; border: 1px solid rgba(239, 68, 68, 0.3); padding: 8px 16px; border-radius: 50px; font-weight: 800; font-size: 16px; display: inline-block;}
    .risk-badge-mod { background-color: rgba(245, 158, 11, 0.15); color: #FCD34D; border: 1px solid rgba(245, 158, 11, 0.3); padding: 8px 16px; border-radius: 50px; font-weight: 800; font-size: 16px; display: inline-block;}
    .risk-badge-low { background-color: rgba(16, 185, 129, 0.15); color: #6EE7B7; border: 1px solid rgba(16, 185, 129, 0.3); padding: 8px 16px; border-radius: 50px; font-weight: 800; font-size: 16px; display: inline-block;}
    
    /* Before/After Cards */
    .ba-container { display: flex; gap: 15px; margin-top: 15px;}
    .ba-card { flex: 1; background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(255,255,255,0.05); padding: 20px; border-radius: 8px; text-align: center;}
    .ba-header { font-size: 12px; color: #94A3B8; text-transform: uppercase; font-weight: 700; letter-spacing: 1px; margin-bottom: 10px;}
    .ba-val { font-size: 32px; font-weight: 800; color: #F8FAFC;}
    
    /* Dynamic Highlight */
    .savings-highlight { color: #34D399; font-weight: 800; font-size: 20px;}
    
    header {visibility: hidden;} footer {visibility: hidden;}
    
    /* Navigation Buttons */
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
if 'mitigation_level' not in st.session_state: st.session_state.mitigation_level = 0
if 'facility_area' not in st.session_state: st.session_state.facility_area = 50000 
if 'report_data' not in st.session_state: st.session_state.report_data = {}

# ==========================================
# 🏠 PAGE 1: THE HOMEPAGE
# ==========================================
if st.session_state.app_page == "Home":
    st.markdown("<br><br><br><br>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center; font-size: 72px; color: #F8FAFC; font-weight: 800; letter-spacing: -1.5px; margin-bottom: 0px;'>EcoPulse</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: #34D399; font-size: 18px; font-weight: 600; letter-spacing: 3px; text-transform: uppercase; margin-top: 5px;'>Spatial Climate Intelligence</h3>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #94A3B8; font-size: 16px; max-width: 700px; margin: 30px auto; line-height: 1.6;'>A planetary-scale telemetry engine for evaluating Urban Heat Island severity. We provide enterprise-grade financial analytics by calculating spatial thermal excess natively from orbital data.</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1.5, 1, 1.5])
    with col2:
        st.markdown("<div class='nav-btn'>", unsafe_allow_html=True)
        if st.button("Initialize System", use_container_width=True):
            st.session_state.app_page = "Dashboard"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# 🌍 PAGE 2: THE DASHBOARD
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
        st.markdown("<div class='header-main' style='font-size: 24px; margin-top: -2px;'>System Dashboard</div>", unsafe_allow_html=True)
    with c3:
        st.markdown("<div class='nav-btn' style='margin-top: -10px;'>", unsafe_allow_html=True)
        if st.button("Generate Report", use_container_width=True):
            st.session_state.app_page = "Report"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<hr style='margin: 10px 0px 20px 0px; border-color: #334155;'>", unsafe_allow_html=True)

    col_insight, col_map = st.columns([1.5, 2.5], gap="large")

    with col_insight:
        # 🌟 ADDED: Prominent Clear Scan Button 🌟
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
                    
        st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

        if st.session_state.roi_geom:
            roi = ee.Geometry(st.session_state.roi_geom)
            start_date, end_date = ['2025-04-01', '2025-07-31'] 
            
            try:
                l9_img = ee.ImageCollection("LANDSAT/LC09/C02/T1_L2").filterBounds(roi).filterDate(start_date, end_date).map(mask_l9_clouds).sort('CLOUD_COVER').first()
                s2_img = ee.ImageCollection('COPERNICUS/S2_SR').filterBounds(roi).filterDate(start_date, end_date).sort('CLOUDY_PIXEL_PERCENTAGE').first()
                
                ndvi = s2_img.normalizedDifference(['B8', 'B4']).reduceRegion(reducer=ee.Reducer.mean(), geometry=roi, scale=10).get('nd').getInfo()
                thermal_raw = l9_img.select('ST_B10').multiply(0.00341802).add(149.0).subtract(273.15)
                
                # Math Logic Unchanged
                excess_img = thermal_raw.subtract(28.0).multiply(thermal_raw.gt(28.0))
                temp_mean_base = thermal_raw.reduceRegion(reducer=ee.Reducer.mean(), geometry=roi, scale=30).get('ST_B10').getInfo()
                excess_mean_base = excess_img.reduceRegion(reducer=ee.Reducer.mean(), geometry=roi, scale=30).get('ST_B10').getInfo()
                
                stats_base = thermal_raw.reduceRegion(reducer=ee.Reducer.minMax(), geometry=roi, scale=30, maxPixels=1e9).getInfo()
                t_min_base = stats_base.get('ST_B10_min')
                t_max_base = stats_base.get('ST_B10_max')

                n_val = round(ndvi, 2) if ndvi else 0
                t_val_base = round(temp_mean_base, 1) if temp_mean_base else 0
                e_val_base = excess_mean_base if excess_mean_base else 0
                t_min_val_base = round(t_min_base, 1) if t_min_base else 0
                t_max_val_base = round(t_max_base, 1) if t_max_base else 0
                variance_base = round(t_max_val_base - t_min_val_base, 1)
                
                # Save base data to session state for the Report page
                st.session_state.report_data = {
                    "t_avg_base": t_val_base, 
                    "variance": variance_base, 
                    "ndvi": n_val, 
                    "t_max": t_max_val_base, 
                    "excess_deg": round(e_val_base, 2)
                }

                st.markdown("<hr style='margin-top: 5px; margin-bottom: 20px; border-color: #334155;'>", unsafe_allow_html=True)
                st.markdown("<div class='section-title'>Spatial Telemetry Metrics</div>", unsafe_allow_html=True)
                st.markdown(f"<div><span class='metric-value'>{t_val_base}°C</span></div><div class='metric-label'>Mean Surface Temperature (LST)</div>", unsafe_allow_html=True)
                
                v_color = '#EF4444' if variance_base > 5 else '#FCD34D' if variance_base > 3 else '#10B981'
                st.markdown(f"<div style='background: rgba(255,255,255,0.03); border-left: 3px solid {v_color}; padding: 12px; margin-top: 15px;'><span style='color: #E2E8F0; font-size: 14px;'>Thermal Variance: {variance_base}°C across sector.</span></div>", unsafe_allow_html=True)

                st.markdown("<br><div class='metric-label'>Head to the Report Page to run the Financial Simulator & Action Plan ↗️</div>", unsafe_allow_html=True)

            except Exception as error:
                st.error("Engine processing error. Sector may be too large.")
        else:
            st.markdown("<div style='color: #475569; font-size: 14px; margin-top: 50px;'>Awaiting sector boundaries...<br>Use the polygon tool on the map.</div>", unsafe_allow_html=True)

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

            thermal_norm = thermal_hd.subtract(fixed_min).divide(fixed_max - fixed_min).clamp(0, 1)
            vis_params = {'min': fixed_min, 'max': fixed_max, 'palette': ['#00008B', '#00FFFF', '#00FF00', '#FFFF00', '#FF7F00', '#FF0000', '#800000']}
            m.addLayer(thermal_hd.clip(roi), vis_params, 'Thermal Signature', opacity=0.55)
            m.addLayer(ee.Image().byte().paint(ee.FeatureCollection([ee.Feature(roi)]), 1, 3), {'palette': ['00FF88']}, 'Target Boundary')

        map_data = st_folium(m, height=750, use_container_width=True, key=f"map_update_dash")

        if map_data and map_data.get('last_active_drawing'):
            new_geom = map_data['last_active_drawing']['geometry']
            if st.session_state.roi_geom != new_geom:
                st.session_state.roi_geom = new_geom
                st.session_state.mitigation_level = 0
                st.rerun()

# ==========================================
# 📊 PAGE 3: THE ESG & LEED REPORT (REDESIGNED)
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
        st.markdown(f"<div class='header-main' style='font-size: 24px; margin-top: -2px;'>Executive Intelligence Brief: {st.session_state.location_name}</div>", unsafe_allow_html=True)

    if not st.session_state.report_data:
        st.warning("No geospatial data in memory. Run Dashboard analysis.")
        st.stop()

    data = st.session_state.report_data
    
    # --- HERO SECTION ---
    # Determine Risk Level
    if data['variance'] > 5:
        risk_html = "<div class='risk-badge-high'>🔴 HIGH RISK</div>"
        risk_sub = "Severe thermal pooling detected."
    elif data['variance'] > 3:
        risk_html = "<div class='risk-badge-mod'>🟠 MODERATE</div>"
        risk_sub = "Elevated heat signatures present."
    else:
        risk_html = "<div class='risk-badge-low'>🟢 STABLE</div>"
        risk_sub = "Thermal gradient within bounds."

    # Base Financial Math (Before Simulation)
    area_input = st.session_state.facility_area
    base_loss_lakhs = round((area_input * 60 * (data['excess_deg'] * 0.06)) / 100000, 2)

    st.markdown("<hr style='margin: 10px 0px 20px 0px; border-color: #334155;'>", unsafe_allow_html=True)
    
    h1, h2, h3 = st.columns(3, gap="medium")
    with h1:
        st.markdown(f"<div class='hero-card'><div class='hero-title'>Heat Risk Status</div><div style='margin-top:5px;'>{risk_html}</div><div class='hero-subdata'>{risk_sub}</div></div>", unsafe_allow_html=True)
    with h2:
        st.markdown(f"<div class='hero-card'><div class='hero-title'>Peak Thermal Threat</div><div class='hero-data'>{data['t_max']}°C</div><div class='hero-subdata'>Max surface temperature recorded</div></div>", unsafe_allow_html=True)
    with h3:
        st.markdown(f"<div class='hero-card'><div class='hero-title'>Base Annual Cooling Burden</div><div class='hero-data' style='color:#FCD34D;'>₹ {base_loss_lakhs} L</div><div class='hero-subdata'>Calculated via spatial excess mapping</div></div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- HEAT MITIGATION SIMULATOR ---
    st.markdown("<div class='header-main' style='font-size: 20px; color: #60A5FA; margin-bottom: 15px;'>⚙️ Heat Mitigation Simulator</div>", unsafe_allow_html=True)
    
    sim_col1, sim_col2 = st.columns([1.2, 2], gap="large")
    
    with sim_col1:
        st.markdown("<div style='background: rgba(255,255,255,0.02); padding: 20px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.05); height: 100%;'>", unsafe_allow_html=True)
        st.markdown("<div class='section-title'>Facility Footprint (Sq.Ft)</div>", unsafe_allow_html=True)
        new_area = st.number_input("Area", min_value=1000, max_value=5000000, value=st.session_state.facility_area, step=5000, label_visibility="collapsed")
        st.session_state.facility_area = new_area
        
        st.markdown("<div class='section-title' style='margin-top: 20px;'>Capital Investment Level</div>", unsafe_allow_html=True)
        mitigation = st.slider("Intervention %", 0, 100, st.session_state.mitigation_level, format="%d%%", label_visibility="collapsed")
        st.session_state.mitigation_level = mitigation
        st.markdown("</div>", unsafe_allow_html=True)

    # Dynamic Math execution
    base_loss_lakhs = round((new_area * 60 * (data['excess_deg'] * 0.06)) / 100000, 2)
    simulated_drop = (mitigation / 100.0) * 4.5 
    display_t = round(data['t_avg_base'] - simulated_drop, 1)
    e_val_sim = max(0, data['excess_deg'] - simulated_drop)
    sim_loss_lakhs = round((new_area * 60 * (e_val_sim * 0.06)) / 100000, 2)
    
    savings = round(base_loss_lakhs - sim_loss_lakhs, 2)
    pct_reduction = round((savings / base_loss_lakhs) * 100) if base_loss_lakhs > 0 else 0

    with sim_col2:
        # Before / After UI
        st.markdown("<div class='ba-container'>", unsafe_allow_html=True)
        
        # Temp comparison
        st.markdown(f"""
        <div class='ba-card'>
            <div class='ba-header'>Average Temp</div>
            <div class='ba-val'>{data['t_avg_base']}°C <span style='color:#64748B; font-weight:400;'>→</span> <span style='color:#34D399;'>{display_t}°C</span></div>
            <div style='color:#10B981; font-weight:700; margin-top:5px;'>⬇ {simulated_drop}°C Reduction</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Financial comparison
        st.markdown(f"""
        <div class='ba-card'>
            <div class='ba-header'>Cooling Penalty</div>
            <div class='ba-val'>₹{base_loss_lakhs}L <span style='color:#64748B; font-weight:400;'>→</span> <span style='color:#60A5FA;'>₹{sim_loss_lakhs}L</span></div>
            <div style='color:#3B82F6; font-weight:700; margin-top:5px;'>⬇ ₹ {savings} Lakhs Saved (-{pct_reduction}%)</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- METHODOLOGY EXPANDER ---
    with st.expander("📚 Engineering Methodology & Financial Math", expanded=False):
        st.markdown("""
        **1. Heat Sink Pixel Extraction:** We do not average the entire bounding box. The engine dynamically masks and extracts only the pixels radiating above a **28°C human comfort baseline**.
        
        **2. Spatial Excess Mapping:** We calculate the exact mathematical deviation $(T_{pixel} - 28)$ for overheated areas, generating an **Area-Weighted Excess** variable.
        
        **3. Thermodynamic Conversion:** Using established HVAC engineering principles, a 1°C ambient increase demands an approximate **6% increase in cooling energy**.
        
        **4. Financial Output:** $Cost = Total Area \\times Base Rate (₹60) \\times (ExcessMean \\times 0.06)$. This strictly isolates the financial penalty of the *Urban Heat Island effect*, ignoring standard baseline utility costs.
        """)

    # --- DYNAMIC ACTION RECOMMENDATIONS ---
    st.markdown("<div class='header-main' style='font-size: 20px; margin-top: 20px; margin-bottom: 15px;'>📋 Strategic Action Plan</div>", unsafe_allow_html=True)
    
    if mitigation == 0:
        st.info("💡 **Awaiting Input:** Increase the Investment Slider above to generate a prescriptive mitigation strategy.")
    elif mitigation < 40:
        st.markdown("""
        <div style='background: rgba(255,255,255,0.02); padding: 20px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.05);'>
        <p style='color: #F8FAFC; font-weight: 600; margin-bottom: 10px;'>Phase 1: Foundational Interventions (Low CAPEX)</p>
        <ul style='color: #CBD5E1; font-size: 15px; line-height: 1.8;'>
            <li>🏢 <b>Reflective Paint:</b> Apply standard white acrylic coatings to existing flat rooftops to immediately boost albedo.</li>
            <li>🌳 <b>Targeted Shading:</b> Plant rapid-growth native canopy trees specifically over dark asphalt parking lots.</li>
            <li>⚙️ <b>HVAC Scheduling:</b> Pre-cool buildings during the night to minimize grid reliance during peak afternoon thermal spikes.</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)
    elif mitigation < 80:
        st.markdown("""
        <div style='background: rgba(255,255,255,0.02); padding: 20px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.05);'>
        <p style='color: #60A5FA; font-weight: 600; margin-bottom: 10px;'>Phase 2: Advanced Infrastructure (Moderate CAPEX)</p>
        <ul style='color: #CBD5E1; font-size: 15px; line-height: 1.8;'>
            <li>🏢 <b>Polyurea Elastomeric Coatings:</b> Deploy industrial-grade cool roof membranes capable of reflecting 85% of solar radiation.</li>
            <li>🌿 <b>Green Roof Integration:</b> Convert structurally viable rooftops into shallow-soil green spaces to completely neutralize roof heat absorption.</li>
            <li>🚶 <b>Pedestrian Corridors:</b> Construct high-albedo shaded walkways between primary buildings to lower localized ground temperature.</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style='background: rgba(16, 185, 129, 0.05); padding: 20px; border-radius: 8px; border: 1px solid rgba(16, 185, 129, 0.2);'>
        <p style='color: #34D399; font-weight: 600; margin-bottom: 10px;'>Phase 3: Deep Urban Cooling (High CAPEX / ESG Compliance)</p>
        <ul style='color: #A7F3D0; font-size: 15px; line-height: 1.8;'>
            <li>🏙️ <b>Full Material Retrofit:</b> Rip and replace dark asphalt with permeable, high-albedo concrete across the entire campus footprint.</li>
            <li>🌳 <b>Urban Micro-Forests:</b> Deploy dense Miyawaki forest patches to create permanent, self-sustaining cool-air sinks.</li>
            <li>🏆 <b>LEED v4 Certification:</b> This level of intervention fully qualifies the facility for Sustainable Sites (SS) Heat Island Reduction credits.</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)
