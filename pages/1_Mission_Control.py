import os
import streamlit as st
import ee
import folium
from folium.plugins import Draw, Geocoder
from streamlit_folium import st_folium
import geocoder

# --- 🌟 THE "HERO" FIX 🌟 ---
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

st.set_page_config(layout="wide", page_title="Mission Control", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    .stApp { background-color: #0A0F18; color: #E2E8F0; font-family: 'Inter', sans-serif; }
    .header-main { color: #F8FAFC; font-size: 28px; font-weight: 800; margin-bottom: 0px; letter-spacing: -0.5px;}
    .header-sub { color: #00FF88; font-size: 14px; font-weight: 600; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 15px; }
    .section-title { color: #94A3B8; font-size: 13px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 10px;}
    .metric-value { font-size: 42px; font-weight: 800; color: #F8FAFC; line-height: 1.1; }
    .metric-value-small { font-size: 24px; font-weight: 700; color: #F8FAFC; line-height: 1.1; }
    .metric-label { font-size: 14px; color: #94A3B8; font-weight: 500; }
    .shock-box { background: rgba(239, 68, 68, 0.1); border-left: 4px solid #EF4444; padding: 10px; border-radius: 4px; margin-top: 10px; margin-bottom: 10px;}
    .shock-text { color: #FCA5A5; font-size: 14px; font-weight: 600; }
    header {visibility: hidden;} footer {visibility: hidden;}
    
    /* Navigation Button */
    .nav-btn div.stButton > button:first-child { background-color: #3B82F6; color: white; border: none; font-weight: bold; width: 100%;}
    .nav-btn div.stButton > button:first-child:hover { background-color: #2563EB; }
</style>
""", unsafe_allow_html=True)

# --- GLOBAL SESSION STATES ---
if 'roi_geom' not in st.session_state: st.session_state.roi_geom = None
if 'map_center' not in st.session_state: st.session_state.map_center = [28.4610, 77.4900]
if 'map_zoom' not in st.session_state: st.session_state.map_zoom = 15
if 'mitigation_level' not in st.session_state: st.session_state.mitigation_level = 0
if 'clicked_coords' not in st.session_state: st.session_state.clicked_coords = None 
if 'report_data' not in st.session_state: st.session_state.report_data = {} # 📊 Saves data for the final page

# Engine Init
try:
    ee_path = os.path.expanduser('~/.config/earthengine')
    os.makedirs(ee_path, exist_ok=True)
    with open(os.path.join(ee_path, 'credentials'), 'w') as f:
        f.write(st.secrets["EARTHENGINE_TOKEN"])
    ee.Initialize(project='ecoplus-iilm')
    if not hasattr(ee.data, '_credentials'): ee.data._credentials = True
except Exception as e:
    st.error(f"Earth Engine Failed: {e}")
    st.stop()

# Header Area
c1, c2 = st.columns([4, 1])
with c1:
    st.markdown("<div class='header-main'>EcoPulse | Mission Control</div>", unsafe_allow_html=True)
    st.markdown("<div class='header-sub'>Live Orbital Radar & Mitigation Simulator</div>", unsafe_allow_html=True)
with c2:
    st.markdown("<div class='nav-btn'>", unsafe_allow_html=True)
    if st.button("📊 Generate Executive Report"):
        st.switch_page("pages/2_Executive_Brief.py")
    st.markdown("</div>", unsafe_allow_html=True)

# Layout Setup
col_insight, col_map = st.columns([1.2, 2.8], gap="large")

with col_insight:
    st.markdown("<div class='section-title'>Control Panel</div>", unsafe_allow_html=True)
    if st.button("🗑️ Clear Canvas", use_container_width=True):
        st.session_state.roi_geom = None
        st.session_state.mitigation_level = 0
        st.session_state.clicked_coords = None
        st.session_state.report_data = {}
        st.rerun()

    st.markdown("<hr style='margin: 15px 0px;'>", unsafe_allow_html=True)

    if st.session_state.roi_geom:
        roi = ee.Geometry(st.session_state.roi_geom)
        start_date, end_date = ['2025-04-01', '2025-07-31'] # Fixed to Peak Summer for Hackathon speed
        
        try:
            l9_collection = ee.ImageCollection("LANDSAT/LC09/C02/T1_L2").filterBounds(roi).filterDate(start_date, end_date).map(mask_l9_clouds)
            l9_img = l9_collection.median()
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
            
            # 🚀 AI MITIGATION SIMULATOR
            st.markdown("<div class='section-title' style='color: #3B82F6;'>🧪 AI Mitigation Simulator</div>", unsafe_allow_html=True)
            mitigation = st.slider("Investment Slider", 0, 100, st.session_state.mitigation_level, format="%d%%", label_visibility="collapsed", key="mitigation_slider")
            st.session_state.mitigation_level = mitigation 

            simulated_drop = (mitigation / 100.0) * 4.5 
            display_t = round(t_val_base - simulated_drop, 1)
            display_var = round(max(0.5, variance_base - (simulated_drop * 1.1)), 1)
            display_color = "#34D399" if mitigation > 30 else "#F8FAFC"
            base_loss = 4.2 if t_val_base > 35 else 2.8 if t_val_base > 28 else 1.1
            sim_loss = round(base_loss - ((mitigation/100) * base_loss * 0.7), 2)
            
            # 📊 SAVE TO SESSION STATE FOR PAGE 3
            st.session_state.report_data = {
                "t_avg": display_t, "variance": display_var, "loss": sim_loss, "ndvi": n_val, 
                "t_max": t_max_val_base, "mitigation": mitigation
            }

            st.markdown("<hr style='margin: 15px 0px;'>", unsafe_allow_html=True)
            
            # DISPLAY METRICS
            st.markdown(f"<div><span class='metric-value' style='color: {display_color};'>{display_t}°C</span></div><div class='metric-label'>Avg Surface Temp</div>", unsafe_allow_html=True)
            st.markdown(f"<div style='margin-top: 10px;'><span class='metric-value-small'>₹ {sim_loss} Lakhs</span></div><div class='metric-label'>Est. Cooling Taxes</div>", unsafe_allow_html=True)
            
            if display_var > 4:
                st.markdown(f"<div class='shock-box'><span class='shock-text'>⚠️ THERMAL VARIANCE: {display_var}°C</span></div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='shock-box' style='background: rgba(16, 185, 129, 0.1); border-left-color: #10B981;'><span class='shock-text' style='color: #34D399;'>✅ THERMAL VARIANCE: {display_var}°C</span></div>", unsafe_allow_html=True)
            
            # 🎯 PINPOINT TELEMETRY
            st.markdown("<hr style='margin: 15px 0px;'>", unsafe_allow_html=True)
            st.markdown("<div class='section-title' style='color: #F87171;'>📍 Pinpoint Inspection</div>", unsafe_allow_html=True)
            
            if st.session_state.clicked_coords:
                p_lat, p_lng = st.session_state.clicked_coords
                click_point = ee.Geometry.Point([p_lng, p_lat])
                val_dict = thermal_raw.clip(roi).reduceRegion(reducer=ee.Reducer.mean(), geometry=click_point, scale=3).getInfo()
                point_temp_raw = val_dict.get('ST_B10')
                
                if point_temp_raw is not None:
                    point_norm = max(0, min(1, (point_temp_raw - t_min_val_base) / (t_max_val_base - t_min_val_base))) if t_max_val_base > t_min_val_base else 0
                    point_cooling = point_norm * simulated_drop
                    final_point_temp = round(point_temp_raw - point_cooling, 1)
                    st.markdown(f"<div class='shock-box' style='background: rgba(248, 113, 113, 0.1); border-left-color: #F87171;'><span class='shock-text' style='color: #FCA5A5;'>🎯 TARGET LOCKED: {final_point_temp}°C</span><br><span style='color:#CBD5E1; font-size: 11px;'>{round(p_lat, 4)}, {round(p_lng, 4)}</span></div>", unsafe_allow_html=True)
                else:
                    st.markdown("<div style='color: #94A3B8; font-size: 12px;'>Target out of bounds.</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div style='color: #94A3B8; font-size: 12px;'>Click any building to extract temp.</div>", unsafe_allow_html=True)

        except Exception as error:
            st.error("Telemetry sync failed. Area too large.")
    else:
        st.markdown("<div style='color: #64748B; font-size: 16px; margin-top: 30px;'>Use the map search bar ↗️ and draw a boundary to begin scan.</div>", unsafe_allow_html=True)

with col_map:
    m = folium.Map(location=st.session_state.map_center, zoom_start=st.session_state.map_zoom)
    Geocoder(position='topright').add_to(m)
    Draw(export=True).add_to(m) 
    
    folium.TileLayer(
        tiles="https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}",
        attr="Google", name="Google Hybrid", overlay=False, control=True
    ).add_to(m)

    if st.session_state.roi_geom:
        roi = ee.Geometry(st.session_state.roi_geom)
        l9_collection = ee.ImageCollection("LANDSAT/LC09/C02/T1_L2").filterDate(start_date, end_date).filterBounds(roi).map(mask_l9_clouds)
        thermal_raw = l9_collection.median().select('ST_B10').multiply(0.00341802).add(149.0).subtract(273.15)
        thermal_hd = thermal_raw.resample('bicubic').reproject(crs=thermal_raw.projection(), scale=15)

        stats_fixed = thermal_hd.reduceRegion(reducer=ee.Reducer.minMax(), geometry=roi, scale=30, maxPixels=1e9).getInfo()
        fixed_min = stats_fixed.get('ST_B10_min', 20)
        fixed_max = stats_fixed.get('ST_B10_max', 40)
        if fixed_max == fixed_min: fixed_max += 1

        current_mitigation = st.session_state.mitigation_level
        max_sim_drop = (current_mitigation / 100.0) * 4.5 
        
        thermal_norm = thermal_hd.subtract(fixed_min).divide(fixed_max - fixed_min).clamp(0, 1)
        cooling_layer = thermal_norm.multiply(max_sim_drop)
        thermal_final = thermal_hd.subtract(cooling_layer).clip(roi)

        vis_params = {'min': fixed_min, 'max': fixed_max, 'palette': ['#00008B', '#00FFFF', '#00FF00', '#FFFF00', '#FF7F00', '#FF0000', '#800000']}
        m.addLayer(thermal_final, vis_params, f'Simulation: {current_mitigation}%', opacity=0.55)
        m.addLayer(ee.Image().byte().paint(ee.FeatureCollection([ee.Feature(roi)]), 1, 3), {'palette': ['00FF88']}, 'Target Boundary')
        
        if st.session_state.clicked_coords:
            folium.Marker(st.session_state.clicked_coords, icon=folium.Icon(color="red", icon="crosshairs", prefix='fa')).add_to(m)

    map_data = st_folium(m, height=700, use_container_width=True, key=f"map_update_{st.session_state.mitigation_level}")

    if map_data and map_data.get('last_active_drawing'):
        new_geom = map_data['last_active_drawing']['geometry']
        if st.session_state.roi_geom != new_geom:
            st.session_state.roi_geom = new_geom
            st.session_state.mitigation_level = 0
            st.session_state.clicked_coords = None 
            st.rerun()

    if map_data and map_data.get('last_clicked'):
        new_coords = [map_data['last_clicked']['lat'], map_data['last_clicked']['lng']]
        if st.session_state.clicked_coords != new_coords:
            st.session_state.clicked_coords = new_coords
            st.rerun()




