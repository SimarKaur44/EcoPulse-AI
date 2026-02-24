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

st.markdown("""
<style>
    .stApp { background-color: #0A0F18; color: #E2E8F0; font-family: 'Inter', sans-serif; }
    .header-main { color: #F8FAFC; font-size: 30px; font-weight: 800; margin-bottom: 0px; letter-spacing: -0.5px;}
    .header-sub { color: #34D399; font-size: 14px; font-weight: 600; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 25px; }
    .section-title { color: #94A3B8; font-size: 13px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 10px;}
    .metric-value { font-size: 42px; font-weight: 700; color: #F8FAFC; line-height: 1.1; }
    .metric-value-small { font-size: 24px; font-weight: 600; color: #F8FAFC; line-height: 1.1; }
    .metric-label { font-size: 13px; color: #94A3B8; font-weight: 500; }
    .status-box { background: rgba(255, 255, 255, 0.03); border-left: 3px solid #3B82F6; padding: 12px; border-radius: 4px; margin-top: 15px; margin-bottom: 15px;}
    .status-text { color: #E2E8F0; font-size: 14px; font-weight: 500; }
    .card { background: rgba(255, 255, 255, 0.02); border: 1px solid rgba(255, 255, 255, 0.05); padding: 25px; border-radius: 6px; margin-bottom: 20px;}
    .leed-box { background: rgba(16, 185, 129, 0.05); border-left: 3px solid #10B981; padding: 20px; border-radius: 4px;}
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
        search_query = st.text_input("TARGET COORDINATES", placeholder="Search sector...", label_visibility="collapsed")
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
                
                # 🛠️ PIXEL-BASED THERMAL EXCESS LOGIC (Engineered Model) 🛠️
                # Creates a new image containing ONLY the degrees above 28 for pixels > 28°C
                excess_img = thermal_raw.subtract(28.0).multiply(thermal_raw.gt(28.0))
                
                # Fetch spatial means
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
                
                st.markdown("<div class='section-title'>Facility Footprint</div>", unsafe_allow_html=True)
                area_input = st.number_input("Total Area (Sq. Ft.)", min_value=1000, max_value=5000000, value=st.session_state.facility_area, step=5000, label_visibility="collapsed")
                st.session_state.facility_area = area_input

                st.markdown("<div class='section-title' style='margin-top: 20px;'>Mitigation Simulator</div>", unsafe_allow_html=True)
                mitigation = st.slider("Investment Slider", 0, 100, st.session_state.mitigation_level, format="%d%%", label_visibility="collapsed", key="mitigation_slider")
                st.session_state.mitigation_level = mitigation 

                # Simulation Math
                simulated_drop = (mitigation / 100.0) * 4.5 
                display_t = round(t_val_base - simulated_drop, 1)
                
                # Fast linear approx of new spatial excess
                e_val_sim = max(0, e_val_base - simulated_drop)
                
                # 🛠️ FINANCIAL CALCULATION (Area-weighted excess cost) 🛠️
                # Cost = Area * BaseRate(60) * (ExcessMean * 0.06)
                base_loss_lakhs = round((area_input * 60 * (e_val_base * 0.06)) / 100000, 2)
                sim_loss_lakhs = round((area_input * 60 * (e_val_sim * 0.06)) / 100000, 2)
                
                st.session_state.report_data = {
                    "t_avg_base": t_val_base, "t_avg_sim": display_t,
                    "variance": variance_base, "loss_base": base_loss_lakhs, "loss_sim": sim_loss_lakhs,
                    "ndvi": n_val, "t_max": t_max_val_base, "mitigation": mitigation, "area": area_input,
                    "excess_deg": round(e_val_base, 2)
                }
                
                st.markdown("<hr style='margin-top: 15px; margin-bottom: 20px; border-color: #334155;'>", unsafe_allow_html=True)
                st.markdown("<div class='section-title'>Spatial Telemetry Metrics</div>", unsafe_allow_html=True)
                
                st.markdown(f"<div><span class='metric-value'>{display_t}°C</span></div><div class='metric-label'>Mean Surface Temperature (LST)</div>", unsafe_allow_html=True)
                
                st.markdown(f"<div class='status-box' style='border-left-color: {'#EF4444' if variance_base > 5 else '#10B981'};'><span class='status-text'>Thermal Variance: {variance_base}°C across sector.</span></div>", unsafe_allow_html=True)
                
                st.write("")
                st.markdown(f"<div><span class='metric-value-small'>₹ {sim_loss_lakhs} L</span></div><div class='metric-label'>Calculated Spatial Excess Cost (Annual)</div>", unsafe_allow_html=True)

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

            current_mitigation = st.session_state.mitigation_level
            thermal_norm = thermal_hd.subtract(fixed_min).divide(fixed_max - fixed_min).clamp(0, 1)
            cooling_layer = thermal_norm.multiply((current_mitigation / 100.0) * 4.5)
            thermal_final = thermal_hd.subtract(cooling_layer).clip(roi)

            vis_params = {'min': fixed_min, 'max': fixed_max, 'palette': ['#00008B', '#00FFFF', '#00FF00', '#FFFF00', '#FF7F00', '#FF0000', '#800000']}
            m.addLayer(thermal_final, vis_params, f'Simulation: {current_mitigation}%', opacity=0.55)
            m.addLayer(ee.Image().byte().paint(ee.FeatureCollection([ee.Feature(roi)]), 1, 3), {'palette': ['00FF88']}, 'Target Boundary')

        map_data = st_folium(m, height=750, use_container_width=True, key=f"map_update_{st.session_state.mitigation_level}")

        if map_data and map_data.get('last_active_drawing'):
            new_geom = map_data['last_active_drawing']['geometry']
            if st.session_state.roi_geom != new_geom:
                st.session_state.roi_geom = new_geom
                st.session_state.mitigation_level = 0
                st.rerun()

# ==========================================
# 📊 PAGE 3: THE ESG & LEED REPORT
# ==========================================
elif st.session_state.app_page == "Report":
    c1, c2 = st.columns([1, 5])
    with c1:
        st.markdown("<div class='sec-btn'>", unsafe_allow_html=True)
        if st.button("⬅ Back"):
            st.session_state.app_page = "Dashboard"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    with c2:
        st.markdown("<div class='header-main' style='font-size: 24px; margin-top: -2px;'>Action Report & Compliance</div>", unsafe_allow_html=True)

    if not st.session_state.report_data:
        st.warning("No geospatial data in memory. Run Dashboard analysis.")
        st.stop()

    data = st.session_state.report_data
    loc = st.session_state.location_name.lower()

    if "college" in loc or "university" in loc or "institute" in loc or "iilm" in loc:
        context_type = "Educational Campus"
        recs = ["Deploy high-albedo elastomeric coatings on dormitories.", "Increase structural shading over pedestrian transit corridors."]
    elif "hospital" in loc or "medical" in loc:
        context_type = "Healthcare Facility"
        recs = ["Shield HVAC intake units from direct solar thermal reflection.", "Implement green roofing on flat wards to stabilize internal thermodynamics."]
    else:
        context_type = "Commercial Sector"
        recs = ["Specify cool-roof materials for all subsequent flat-roof maintenance.", "Deploy localized canopy interventions (*Azadirachta indica*) over asphalt heat sinks."]

    st.markdown(f"<h3 style='color: #94A3B8; font-weight: 500; font-size: 16px;'>Sector: <span style='color: #F8FAFC;'>{st.session_state.location_name}</span></h3>", unsafe_allow_html=True)
    
    st.markdown("<hr style='margin: 15px 0px 30px 0px; border-color: #334155;'>", unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    c1.markdown(f"<div class='card'><div class='section-title'>Peak Thermal Value</div><div class='metric-value' style='color:#FCA5A5;'>{data['t_max']}°C</div></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='card'><div class='section-title'>Area-Weighted Excess</div><div class='metric-value' style='color:#FCD34D;'>+{data['excess_deg']}°C</div><div class='metric-label'>Mean spatial deviance >28°C baseline</div></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='card'><div class='section-title'>Calculated HVAC Penalty</div><div class='metric-value'>₹ {data['loss_base']} L</div><div class='metric-label'>Per {data['area']:,} sq.ft</div></div>", unsafe_allow_html=True)

    col_graph, col_leed = st.columns([2, 1.5], gap="large")
    
    with col_graph:
        st.markdown("<div class='section-title' style='color: #60A5FA; margin-bottom: 15px;'>Mitigation Impact Analysis</div>", unsafe_allow_html=True)
        chart_data = pd.DataFrame([
            {"Metric": "Baseline LST (°C)", "Value": data['t_avg_base']},
            {"Metric": "Simulated LST (°C)", "Value": data['t_avg_sim']},
            {"Metric": "Base Excess Tax (Lakhs)", "Value": data['loss_base']},
            {"Metric": "Sim Excess Tax (Lakhs)", "Value": data['loss_sim']},
        ])
        st.bar_chart(chart_data.set_index("Metric"), height=250)

    with col_leed:
        st.markdown("<div class='leed-box'>", unsafe_allow_html=True)
        st.markdown("<h3 style='color: #10B981; font-size: 16px; margin-top:0px;'>LEED v4 Standard Compliance</h3>", unsafe_allow_html=True)
        st.markdown("<p style='color: #94A3B8; font-size: 13px;'>Evaluating proposed <b>{}% intervention</b>.</p>".format(data['mitigation']), unsafe_allow_html=True)
        st.markdown("<h4 style='color: #F8FAFC; font-size: 14px;'>Sustainable Sites (SS): Heat Island Reduction</h4>", unsafe_allow_html=True)
        
        if data['mitigation'] >= 50:
            st.markdown("<h2 style='color: #34D399; font-size: 20px; margin: 10px 0px;'>Eligible (+2 Points)</h2>", unsafe_allow_html=True)
            st.markdown("<p style='color: #A7F3D0; font-size: 12px;'>Simulation satisfies the 50%+ threshold for high-reflectance material coverage.</p>", unsafe_allow_html=True)
        else:
            st.markdown("<h2 style='color: #FCD34D; font-size: 20px; margin: 10px 0px;'>Ineligible (Requires >50%)</h2>", unsafe_allow_html=True)
            st.markdown("<p style='color: #FDE68A; font-size: 12px;'>Increase mitigation slider to >50% to model standard compliance.</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='card' style='margin-top: 15px;'>", unsafe_allow_html=True)
    st.markdown(f"<div class='section-title' style='color: #3B82F6;'>System Recommendations [{context_type}]</div>", unsafe_allow_html=True)
    st.markdown(f"<ul style='color: #E2E8F0; font-size: 14px; line-height: 1.8;'><li>{recs[0]}</li><li>{recs[1]}</li><li><b>Financial Output:</b> Modeled spatial mitigation intercepts approximately <b>₹ {round(data['loss_base'] - data['loss_sim'], 2)} Lakhs</b> in excess thermodynamic load annually.</li></ul>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
