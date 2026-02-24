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

st.set_page_config(layout="wide", page_title="EcoPulse | Global Climate Intelligence", page_icon="🌍", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    .stApp { background-color: #0A0F18; color: #E2E8F0; font-family: 'Inter', sans-serif; }
    .header-main { color: #F8FAFC; font-size: 34px; font-weight: 900; margin-bottom: 0px; letter-spacing: -0.5px;}
    .header-sub { color: #00FF88; font-size: 16px; font-weight: 600; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 25px; }
    .section-title { color: #94A3B8; font-size: 14px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 10px;}
    .metric-value { font-size: 48px; font-weight: 800; color: #F8FAFC; line-height: 1.1; }
    .metric-value-small { font-size: 28px; font-weight: 700; color: #F8FAFC; line-height: 1.1; }
    .metric-label { font-size: 14px; color: #94A3B8; font-weight: 500; }
    .shock-box { background: rgba(239, 68, 68, 0.1); border-left: 4px solid #EF4444; padding: 12px; border-radius: 4px; margin-top: 15px; margin-bottom: 15px;}
    .shock-text { color: #FCA5A5; font-size: 15px; font-weight: 600; }
    .card { background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.05); padding: 25px; border-radius: 8px; margin-bottom: 20px;}
    .leed-box { background: linear-gradient(145deg, rgba(16, 185, 129, 0.1) 0%, rgba(59, 130, 246, 0.1) 100%); border-left: 4px solid #10B981; padding: 20px; border-radius: 4px;}
    header {visibility: hidden;} footer {visibility: hidden;}
    
    /* Navigation Buttons */
    .nav-btn div.stButton > button:first-child { background-color: #00FF88; color: #0A0F18; border: none; font-size: 18px; font-weight: 800; padding: 15px 30px; border-radius: 8px; transition: all 0.3s;}
    .nav-btn div.stButton > button:first-child:hover { background-color: #34D399; box-shadow: 0px 0px 20px rgba(0, 255, 136, 0.4);}
    .sec-btn div.stButton > button:first-child { background-color: transparent; color: #60A5FA; border: 1px solid #60A5FA; font-weight: 600;}
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
if 'facility_area' not in st.session_state: st.session_state.facility_area = 50000 # Default 50k sq ft
if 'report_data' not in st.session_state: st.session_state.report_data = {}

# ==========================================
# 🏠 PAGE 1: THE HOMEPAGE
# ==========================================
if st.session_state.app_page == "Home":
    st.markdown("<br><br><br><br>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center; font-size: 90px; color: #F8FAFC; font-weight: 900; letter-spacing: -2px; margin-bottom: 0px;'>EcoPulse</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: #00FF88; font-size: 24px; font-weight: 600; letter-spacing: 4px; text-transform: uppercase; margin-top: -10px;'>Global Climate Intelligence</h3>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #94A3B8; font-size: 18px; max-width: 800px; margin: 30px auto; line-height: 1.6;'>Urban Heat Islands are a silent infrastructure crisis. Concrete acts as a thermal battery, spiking HVAC cooling costs and blocking LEED certification. EcoPulse leverages orbital telemetry to audit, predict, and mitigate thermal stress.</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown("<div class='nav-btn'>", unsafe_allow_html=True)
        if st.button("🚀 INITIALIZE ORBITAL RADAR", use_container_width=True):
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
        st.error(f"Earth Engine Connection Failed: {e}")
        st.stop()

    c1, c2, c3 = st.columns([1, 4, 1.5])
    with c1:
        st.markdown("<div class='sec-btn'>", unsafe_allow_html=True)
        if st.button("⬅ Home", use_container_width=True):
            st.session_state.app_page = "Home"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    with c2:
        st.markdown("<div class='header-main' style='font-size: 28px; margin-top: -5px;'>EcoPulse | Mission Control</div>", unsafe_allow_html=True)
    with c3:
        st.markdown("<div class='nav-btn' style='margin-top: -10px;'>", unsafe_allow_html=True)
        if st.button("📊 Generate ESG Report", use_container_width=True):
            st.session_state.app_page = "Report"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<hr style='margin: 10px 0px 20px 0px;'>", unsafe_allow_html=True)

    col_insight, col_map = st.columns([1.5, 2.5], gap="large")

    with col_insight:
        search_query = st.text_input("📍 INTELLIGENCE TARGETING", placeholder="Search 'IILM', 'Knowledge Park 2'...", label_visibility="collapsed")
        if search_query and search_query != st.session_state.last_search:
            with st.spinner(f"Locking coordinates for {search_query}..."):
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
                # Map rendering logic untouched
                l9_img = ee.ImageCollection("LANDSAT/LC09/C02/T1_L2").filterBounds(roi).filterDate(start_date, end_date).map(mask_l9_clouds).sort('CLOUD_COVER').first()
                s2_img = ee.ImageCollection('COPERNICUS/S2_SR').filterBounds(roi).filterDate(start_date, end_date).sort('CLOUDY_PIXEL_PERCENTAGE').first()
                
                ndvi = s2_img.normalizedDifference(['B8', 'B4']).reduceRegion(reducer=ee.Reducer.mean(), geometry=roi, scale=10).get('nd').getInfo()
                thermal_raw = l9_img.select('ST_B10').multiply(0.00341802).add(149.0).subtract(273.15)
                
                temp_mean_base = thermal_raw.reduceRegion(reducer=ee.Reducer.mean(), geometry=roi, scale=30).get('ST_B10').getInfo()
                stats_base = thermal_raw.reduceRegion(reducer=ee.Reducer.minMax(), geometry=roi, scale=30, maxPixels=1e9).getInfo()
                t_min_base = stats_base.get('ST_B10_min')
                t_max_base = stats_base.get('ST_B10_max')

                n_val = round(ndvi, 2) if ndvi else 0
                t_val_base = round(temp_mean_base, 1) if temp_mean_base else 0
                t_min_val_base = round(t_min_base, 1) if t_min_base else 0
                t_max_val_base = round(t_max_base, 1) if t_max_base else 0
                variance_base = round(t_max_val_base - t_min_val_base, 1)
                
               # -------------------------------
# 🔥 HEAT SINK BASED FINANCIAL MODEL (Corrected & Defendable)
# -------------------------------

st.markdown("<div class='section-title'>🏢 Facility Parameters</div>", unsafe_allow_html=True)
area_input = st.number_input(
    "Conditioned Built-up Area (Sq. Ft.)",
    min_value=1000,
    max_value=5000000,
    value=st.session_state.facility_area,
    step=5000
)
st.session_state.facility_area = area_input

st.markdown("<div class='section-title' style='margin-top:15px;'>🧪 Mitigation Simulation</div>", unsafe_allow_html=True)
mitigation = st.slider(
    "Mitigation Level",
    0, 100,
    st.session_state.mitigation_level,
    format="%d%%",
    label_visibility="collapsed",
    key="mitigation_slider"
)
st.session_state.mitigation_level = mitigation

# -------------------------------
# 🌡️ THERMAL EXCESS CALCULATION
# -------------------------------

comfort_baseline = 28.0  # thermal comfort threshold

# Excess temperature only where above baseline
thermal_excess = thermal_raw.subtract(comfort_baseline).max(0)

# Mask only overheated pixels
heat_mask = thermal_excess.gt(0)
thermal_excess_masked = thermal_excess.updateMask(heat_mask)

# Pixel area image (band name = 'area')
pixel_area = ee.Image.pixelArea()

# Total overheated area (m²)
heat_area_stats = pixel_area.updateMask(heat_mask).reduceRegion(
    reducer=ee.Reducer.sum(),
    geometry=roi,
    scale=30,
    maxPixels=1e9
).getInfo()

heat_area_m2 = heat_area_stats.get('area', 0)

# Mean excess temperature over overheated pixels
mean_excess_stats = thermal_excess_masked.reduceRegion(
    reducer=ee.Reducer.mean(),
    geometry=roi,
    scale=30,
    maxPixels=1e9
).getInfo()

mean_excess_temp = mean_excess_stats.get('ST_B10', 0)

# -------------------------------
# 💸 ENERGY IMPACT MODEL
# -------------------------------

# Assumption: HVAC load increases ~6% per 1°C above comfort
energy_increase_factor = 0.06

# Base annual cooling cost assumption
base_cooling_cost = 60  # ₹ per sqft per year

# Percent increase based on real mean excess
cooling_penalty_pct = mean_excess_temp * energy_increase_factor

# Convert heat-affected area from m² → sqft
heat_area_sqft = heat_area_m2 * 10.7639

# Cooling loss applies only to overheated portion
effective_area = min(heat_area_sqft, area_input)

base_loss_lakhs = round(
    (effective_area * base_cooling_cost * cooling_penalty_pct) / 100000,
    2
)

# -------------------------------
# ❄️ APPLY MITIGATION EFFECT
# -------------------------------

simulated_drop = (mitigation / 100.0) * 4.5

adjusted_excess = max(0, mean_excess_temp - simulated_drop)

sim_penalty_pct = adjusted_excess * energy_increase_factor

sim_loss_lakhs = round(
    (effective_area * base_cooling_cost * sim_penalty_pct) / 100000,
    2
)

# -------------------------------
# 📊 DISPLAY
# -------------------------------

display_t = round(temp_mean_base - simulated_drop, 1)

st.session_state.report_data = {
    "t_avg_base": round(temp_mean_base, 1),
    "t_avg_sim": display_t,
    "loss_base": base_loss_lakhs,
    "loss_sim": sim_loss_lakhs,
    "ndvi": n_val,
    "t_max": t_max_val_base,
    "mitigation": mitigation,
    "area": area_input
}

st.markdown("<hr style='margin-top: 10px; margin-bottom: 20px;'>", unsafe_allow_html=True)

st.markdown("<div class='section-title'>Thermal Summary</div>", unsafe_allow_html=True)
st.markdown(f"<div class='metric-value'>{display_t}°C</div><div class='metric-label'>Mean Surface Temperature</div>", unsafe_allow_html=True)

st.write("")
st.markdown(
    f"<div class='metric-value-small'>₹ {sim_loss_lakhs} Lakhs</div>"
    "<div class='metric-label'>Estimated Annual Cooling Burden (Heat Sink Only)</div>",
    unsafe_allow_html=True
)
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
        if st.button("⬅ Back to Map"):
            st.session_state.app_page = "Dashboard"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    with c2:
        st.markdown("<div class='header-main' style='font-size: 28px; margin-top: -5px;'>ESG & LEED Intelligence Brief</div>", unsafe_allow_html=True)

    if not st.session_state.report_data:
        st.warning("⚠️ No data found. Please run an analysis in the Dashboard first.")
        st.stop()

    data = st.session_state.report_data
    loc = st.session_state.location_name.lower()

    if "college" in loc or "university" in loc or "institute" in loc or "iilm" in loc:
        context_type = "Educational Campus"
        recs = ["Implement shaded student walkways between academic blocks.", "Apply high-albedo coatings to dormitories to reduce overnight thermal stress for students."]
    elif "hospital" in loc or "medical" in loc:
        context_type = "Healthcare Facility"
        recs = ["Critical: Reduce thermal load on HVAC systems protecting sensitive ICU wards.", "Deploy green roofing to improve patient recovery environments."]
    else:
        context_type = "Commercial / Urban Sector"
        recs = ["Apply Polyurea Elastomeric coatings to expansive flat commercial roofs.", "Deploy drought-resistant *Azadirachta indica* (Neem) in large parking lots."]

    st.markdown(f"<h3 style='color: #94A3B8;'>Target Analysis: <span style='color: #F8FAFC;'>{st.session_state.location_name}</span> ({context_type})</h3>", unsafe_allow_html=True)
    
    st.markdown("<hr style='margin: 15px 0px 30px 0px;'>", unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    c1.markdown(f"<div class='card'><div class='section-title'>Peak Thermal Threat</div><div class='metric-value' style='color:#FCA5A5;'>{data['t_max']}°C</div></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='card'><div class='section-title'>Vegetation Health (NDVI)</div><div class='metric-value' style='color:#6EE7B7;'>{data['ndvi']}</div></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='card'><div class='section-title'>UHI Cooling Penalty</div><div class='metric-value'>₹ {data['loss_base']} L</div><div class='metric-label' style='margin-top:5px;'>Based on {data['area']:,} sq.ft</div></div>", unsafe_allow_html=True)

    col_graph, col_leed = st.columns([2, 1.5], gap="large")
    
    with col_graph:
        st.markdown("<div class='card-title' style='color: #60A5FA; font-weight: bold; margin-bottom: 15px;'>📉 Mitigation Impact Graph</div>", unsafe_allow_html=True)
        chart_data = pd.DataFrame([
            {"Metric": "Baseline Temp (°C)", "Value": data['t_avg_base']},
            {"Metric": "Simulated Temp (°C)", "Value": data['t_avg_sim']},
            {"Metric": "Baseline Tax (Lakhs)", "Value": data['loss_base']},
            {"Metric": "Simulated Tax (Lakhs)", "Value": data['loss_sim']},
        ])
        st.bar_chart(chart_data.set_index("Metric"), height=300)

    with col_leed:
        st.markdown("<div class='leed-box'>", unsafe_allow_html=True)
        st.markdown("<h3 style='color: #10B981; margin-top:0px;'>🌱 LEED v4 Certification Check</h3>", unsafe_allow_html=True)
        st.markdown("<p style='color: #D1D5DB; font-size: 14px;'>Based on your simulated <b>{}% mitigation investment</b>, this facility qualifies for:</p>".format(data['mitigation']), unsafe_allow_html=True)
        st.markdown("<h4 style='color: #F8FAFC;'>Sustainable Sites (SS) Credit: Heat Island Reduction</h4>", unsafe_allow_html=True)
        
        if data['mitigation'] >= 50:
            st.markdown("<h2 style='color: #34D399; margin: 10px 0px;'>+2 Points Eligible ✅</h2>", unsafe_allow_html=True)
            st.markdown("<p style='color: #A7F3D0; font-size: 13px;'>Simulation meets the 50%+ threshold for high-reflectance roofing and non-roof vegetation cover requirements under LEED v4 standard.</p>", unsafe_allow_html=True)
        else:
            st.markdown("<h2 style='color: #FCD34D; margin: 10px 0px;'>+0 Points (Requires >50%) ⚠️</h2>", unsafe_allow_html=True)
            st.markdown("<p style='color: #FDE68A; font-size: 13px;'>Increase mitigation slider above 50% on the Dashboard to simulate qualification for LEED compliance credits.</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown(f"<div class='section-title' style='color: #3B82F6;'>🧠 Contextual AI Strategy for {context_type}</div>", unsafe_allow_html=True)
    st.markdown(f"<ul style='color: #CBD5E1; font-size: 16px; line-height: 1.8;'><li>{recs[0]}</li><li>{recs[1]}</li><li><b>Financial ROI:</b> Implementing this strategy will recover approximately <b>₹ {round(data['loss_base'] - data['loss_sim'], 2)} Lakhs</b> annually in wasted HVAC expenditure.</li></ul>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

