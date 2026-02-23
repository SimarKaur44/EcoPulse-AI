import streamlit as st
import ee
import folium
from folium.plugins import Draw
from streamlit_folium import st_folium
import geocoder
import os

# --- 🌟 CORE ENGINE: Bypassing geemap entirely 🌟 ---
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

# 1. UI Setup
st.set_page_config(layout="wide", page_title="EcoPulse | Core Engine", page_icon="🌍", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    .stApp { background-color: #0A0F18; color: #E2E8F0; font-family: 'Inter', sans-serif; }
    .title { font-size: 36px; font-weight: 900; color: #F8FAFC; margin-bottom: 0px;}
    .subtitle { font-size: 16px; color: #00FF88; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 20px;}
</style>
""", unsafe_allow_html=True)

st.markdown("<div class='title'>EcoPulse | Core Telemetry</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Live Orbital Scan: ACTIVE</div>", unsafe_allow_html=True)

# 2. Secure Cloud Bridge Initialization
with st.spinner("Connecting to Google Earth Engine..."):
    try:
        ee_path = os.path.expanduser('~/.config/earthengine')
        os.makedirs(ee_path, exist_ok=True)
        with open(os.path.join(ee_path, 'credentials'), 'w') as f:
            f.write(st.secrets["EARTHENGINE_TOKEN"])
        ee.Initialize(project='ecoplus-iilm')
        if not hasattr(ee.data, '_credentials'): ee.data._credentials = True
    except Exception as e:
        st.error(f"Engine Offline. Check Streamlit Secrets. Error: {e}")
        st.stop()

# 3. Session States for Map
if 'map_center' not in st.session_state: st.session_state.map_center = [28.4610, 77.4900] # Defaults to Greater Noida
if 'map_zoom' not in st.session_state: st.session_state.map_zoom = 15
if 'roi_geom' not in st.session_state: st.session_state.roi_geom = None

# 4. Search Bar
search_query = st.text_input("📍 TARGETING SYSTEM", placeholder="Search 'Knowledge Park 2', 'IILM University'...", label_visibility="collapsed")
if search_query:
    with st.spinner(f"Locking coordinates for {search_query}..."):
        g = geocoder.arcgis(search_query)
        if g.ok:
            st.session_state.map_center = [g.lat, g.lng]
            st.session_state.map_zoom = 16
            st.session_state.roi_geom = None

st.write("") # Spacer

# 5. Render Map
# 🌟 THE CRITICAL FIX: lyrs=s forces pure satellite view with NO text labels 🌟
m = folium.Map(location=st.session_state.map_center, zoom_start=st.session_state.map_zoom)
folium.TileLayer(
    tiles="https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
    attr="Google", name="Google Satellite (No Labels)", overlay=False, control=True
).add_to(m)

Draw(export=True).add_to(m)

# 6. Apply Thermal Layer if area is drawn
if st.session_state.roi_geom:
    roi = ee.Geometry(st.session_state.roi_geom)
    
    # Grab recent summer data for high contrast
    l9_img = ee.ImageCollection("LANDSAT/LC09/C02/T1_L2").filterBounds(roi).filterDate('2025-04-01', '2025-07-31').sort('CLOUD_COVER').first()
    
    if l9_img:
        thermal_raw = l9_img.select('ST_B10').multiply(0.00341802).add(149.0).subtract(273.15)
        thermal_hd = thermal_raw.resample('bicubic').reproject(crs=thermal_raw.projection(), scale=3)
        
        stats = thermal_hd.reduceRegion(reducer=ee.Reducer.percentile([5, 95]), geometry=roi, scale=30, maxPixels=1e9).getInfo()
        t_min = stats.get('ST_B10_p5', 20)
        t_max = stats.get('ST_B10_p95', 40)
        if t_max == t_min: t_max += 1

        vis_params = {
            'min': t_min, 
            'max': t_max, 
            'palette': ['#00008B', '#00FFFF', '#00FF00', '#FFFF00', '#FF7F00', '#FF0000', '#800000']
        }
        
        m.addLayer(thermal_hd.clip(roi), vis_params, 'Thermal Variance Scan', opacity=0.6)
        
        # Calculate max diff for the UI
        variance = round(t_max - t_min, 1)
        st.markdown(f"<div style='background: rgba(239, 68, 68, 0.1); border-left: 4px solid #EF4444; padding: 10px; color: #FCA5A5; font-weight: bold;'>⚠️ Detected Thermal Variance in Zone: {variance}°C</div><br>", unsafe_allow_html=True)
    else:
        st.warning("No clear satellite imagery found for this specific area during the selected dates.")

# Render Folium
map_data = st_folium(m, height=600, use_container_width=True)

if map_data and map_data.get('last_active_drawing'):
    new_geom = map_data['last_active_drawing']['geometry']
    if st.session_state.roi_geom != new_geom:
        st.session_state.roi_geom = new_geom
        st.rerun()
