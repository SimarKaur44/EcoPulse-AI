import os
import streamlit as st
import ee
import folium
from folium.plugins import Draw
from streamlit_folium import st_folium
import geocoder

# ---------------- EARTH ENGINE → FOLIUM BRIDGE ----------------
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
# -------------------------------------------------------------

# ---------------- APP CONFIG ----------------
st.set_page_config(
    layout="wide",
    page_title="EcoPulse | Global Climate Intelligence",
    page_icon="🌍",
    initial_sidebar_state="collapsed"
)

# ---------------- PREMIUM UI ----------------
st.markdown("""
<style>
.block-container { padding: 1.5rem 3rem; max-width: 100%; }
.stApp { background-color: #0A0F18; color: #E2E8F0; font-family: Inter, sans-serif; }
.header-main { font-size: 34px; font-weight: 800; color: #F8FAFC; }
.header-sub { color: #00FF88; font-size: 16px; font-weight: 600; margin-bottom: 25px; }
.section-title { color: #94A3B8; font-size: 14px; font-weight: 700; text-transform: uppercase; }
.metric-value { font-size: 56px; font-weight: 800; }
.metric-small { font-size: 28px; font-weight: 700; }
.metric-label { font-size: 15px; color: #94A3B8; }
.badge-high { background: rgba(239,68,68,.2); color:#FCA5A5; padding:6px 12px; border-radius:12px; }
.badge-warn { background: rgba(245,158,11,.2); color:#FCD34D; padding:6px 12px; border-radius:12px; }
.badge-good { background: rgba(16,185,129,.2); color:#6EE7B7; padding:6px 12px; border-radius:12px; }
header, footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ---------------- SESSION STATE ----------------
if 'roi_geom' not in st.session_state:
    st.session_state.roi_geom = None
if 'map_center' not in st.session_state:
    st.session_state.map_center = [28.4610, 77.4900]
if 'map_zoom' not in st.session_state:
    st.session_state.map_zoom = 15
if 'last_search' not in st.session_state:
    st.session_state.last_search = ""

# ---------------- DATE PRESETS ----------------
dates = {
    "Jan – Mar 2025 (Spring)": ['2025-01-01', '2025-03-31'],
    "Apr – Jul 2025 (Peak Summer)": ['2025-04-01', '2025-07-31'],
    "Jan – Mar 2024 (Historical)": ['2024-01-01', '2024-03-31'],
    "Apr – Jul 2024 (Historical Summer)": ['2024-04-01', '2024-07-31'],
}

# ---------------- HEADER ----------------
st.markdown("<div class='header-main'>EcoPulse | Global Climate Intelligence</div>", unsafe_allow_html=True)
st.markdown("<div class='header-sub'>Hackathon Live Build</div>", unsafe_allow_html=True)

# ---------------- EARTH ENGINE INIT ----------------
try:
    ee_path = os.path.expanduser('~/.config/earthengine')
    os.makedirs(ee_path, exist_ok=True)
    with open(os.path.join(ee_path, 'credentials'), 'w') as f:
        f.write(st.secrets["EARTHENGINE_TOKEN"])
    ee.Initialize(project='ecoplus-iilm')
except Exception as e:
    st.error(f"Earth Engine Init Failed: {e}")
    st.stop()

# ---------------- LAYOUT ----------------
col_left, col_map = st.columns([1.5, 2.5], gap="large")

# ================= LEFT PANEL =================
with col_left:
    query = st.text_input("Location", placeholder="Search any city / campus")
    if query and query != st.session_state.last_search:
        g = geocoder.arcgis(query)
        if g.ok:
            st.session_state.map_center = [g.lat, g.lng]
            st.session_state.map_zoom = 16
            st.session_state.last_search = query
            st.session_state.roi_geom = None
            st.rerun()

    timeframe = st.selectbox("Timeframe", list(dates.keys()))
    start_date, end_date = dates[timeframe]

    if st.session_state.roi_geom:
        roi = ee.Geometry(st.session_state.roi_geom)

        try:
            l9 = ee.ImageCollection("LANDSAT/LC09/C02/T1_L2") \
                .filterBounds(roi).filterDate(start_date, end_date) \
                .sort('CLOUD_COVER').first()

            s2 = ee.ImageCollection("COPERNICUS/S2_SR") \
                .filterBounds(roi).filterDate(start_date, end_date) \
                .sort('CLOUDY_PIXEL_PERCENTAGE').first()

            ndvi = s2.normalizedDifference(['B8', 'B4']) \
                .reduceRegion(ee.Reducer.mean(), roi, 10).get('nd').getInfo()

            thermal = l9.select('ST_B10') \
                .multiply(0.00341802).add(149).subtract(273.15)

            stats = thermal.reduceRegion(
                reducer=ee.Reducer.percentile([5, 95]),
                geometry=roi,
                scale=30,
                maxPixels=1e9
            ).getInfo()

            t_min = round(stats['ST_B10_p5'], 1)
            t_max = round(stats['ST_B10_p95'], 1)
            t_avg = round((t_min + t_max) / 2, 1)

            st.markdown("<div class='section-title'>Thermal Overview</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='metric-value'>{t_avg}°C</div>", unsafe_allow_html=True)
            st.markdown("<div class='metric-label'>Average Surface Temperature</div>", unsafe_allow_html=True)

            c1, c2 = st.columns(2)
            c1.markdown(f"<div class='metric-small'>{t_min}°C</div><div class='metric-label'>Coolest Zone</div>", unsafe_allow_html=True)
            c2.markdown(f"<div class='metric-small'>{t_max}°C</div><div class='metric-label'>Hottest Zone</div>", unsafe_allow_html=True)

            st.markdown("<div class='section-title'>Risk Indicators</div>", unsafe_allow_html=True)

            heat_badge = "badge-high" if t_max > 40 else "badge-warn" if t_max > 32 else "badge-good"
            green_badge = "badge-high" if ndvi < 0.15 else "badge-warn" if ndvi < 0.35 else "badge-good"

            st.markdown(f"<span class='{heat_badge}'>HEAT RISK</span>", unsafe_allow_html=True)
            st.markdown(f"<span class='{green_badge}'>GREEN COVER</span>", unsafe_allow_html=True)

        except:
            st.error("Satellite data unavailable for this area/timeframe.")
    else:
        st.info("Draw a region on the map to begin analysis.")

# ================= MAP PANEL =================
with col_map:
    m = folium.Map(
        location=st.session_state.map_center,
        zoom_start=st.session_state.map_zoom
    )

    Draw(export=True).add_to(m)

    folium.TileLayer(
        tiles="https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}",
        attr="Google",
        name="Google Hybrid",
        control=True
    ).add_to(m)

    if st.session_state.roi_geom:
        roi = ee.Geometry(st.session_state.roi_geom)

        thermal = ee.ImageCollection("LANDSAT/LC09/C02/T1_L2") \
            .filterBounds(roi).filterDate(start_date, end_date) \
            .sort('CLOUD_COVER').first() \
            .select('ST_B10') \
            .multiply(0.00341802).add(149).subtract(273.15) \
            .clip(roi)

        vis = {
            'min': 20,
            'max': 45,
            'palette': ['#00008B','#00FFFF','#00FF00','#FFFF00','#FF7F00','#FF0000','#800000']
        }

        m.addLayer(thermal, vis, "Land Surface Temperature", opacity=0.6)

        boundary = ee.Image().byte().paint(roi, 1, 3)
        m.addLayer(boundary, {'palette': ['00FF88']}, "ROI Boundary")

    map_data = st_folium(m, height=750, use_container_width=True)

    if map_data and map_data.get("last_active_drawing"):
        geom = map_data["last_active_drawing"]["geometry"]
        if geom != st.session_state.roi_geom:
            st.session_state.roi_geom = geom
            st.rerun()
