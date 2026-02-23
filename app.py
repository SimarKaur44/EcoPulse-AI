import os
import streamlit as st
import ee
import folium
from folium.plugins import Draw
from streamlit_folium import st_folium
import geocoder

# --- GEE → Folium Bridge ---
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

# -------------------------------
# App Config
# -------------------------------
st.set_page_config(
    layout="wide",
    page_title="EcoPulse | Heat Intelligence",
    page_icon="🌍"
)

# -------------------------------
# Minimal Styling (keep premium feel)
# -------------------------------
st.markdown("""
<style>
.stApp { background-color: #0A0F18; color: #E2E8F0; }
.header-main { font-size: 34px; font-weight: 800; }
.header-sub { color: #00FF88; letter-spacing: 1.5px; }
.section-title { color: #94A3B8; font-size: 14px; text-transform: uppercase; }
.metric { font-size: 46px; font-weight: 800; }
</style>
""", unsafe_allow_html=True)

# -------------------------------
# Session State
# -------------------------------
if "roi_geom" not in st.session_state:
    st.session_state.roi_geom = None

if "map_center" not in st.session_state:
    st.session_state.map_center = [28.4610, 77.4900]

# -------------------------------
# Header
# -------------------------------
st.markdown("<div class='header-main'>EcoPulse</div>", unsafe_allow_html=True)
st.markdown("<div class='header-sub'>Urban Heat Intelligence Platform</div>", unsafe_allow_html=True)

# -------------------------------
# Earth Engine Init
# -------------------------------
try:
    ee_path = os.path.expanduser('~/.config/earthengine')
    os.makedirs(ee_path, exist_ok=True)

    with open(os.path.join(ee_path, 'credentials'), 'w') as f:
        f.write(st.secrets["EARTHENGINE_TOKEN"])

    ee.Initialize(project='ecoplus-iilm')
except Exception as e:
    st.error(f"Earth Engine Error: {e}")
    st.stop()

# -------------------------------
# Layout
# -------------------------------
col_left, col_map = st.columns([1.4, 2.6], gap="large")

# ===============================
# LEFT PANEL — INSIGHTS
# ===============================
with col_left:

    search = st.text_input(
        "📍 Search Location",
        placeholder="IIT Delhi, Stanford, Hyde Park London"
    )

    if search:
        g = geocoder.arcgis(search)
        if g.ok:
            st.session_state.map_center = [g.lat, g.lng]
            st.session_state.roi_geom = None
            st.rerun()

    st.markdown("<hr>", unsafe_allow_html=True)

    if st.session_state.roi_geom:
        roi = ee.Geometry(st.session_state.roi_geom)

        try:
            l9 = (
                ee.ImageCollection("LANDSAT/LC09/C02/T1_L2")
                .filterBounds(roi)
                .filterDate("2025-04-01", "2025-07-31")
                .sort("CLOUD_COVER")
                .first()
            )

            s2 = (
                ee.ImageCollection("COPERNICUS/S2_SR")
                .filterBounds(roi)
                .filterDate("2025-04-01", "2025-07-31")
                .sort("CLOUDY_PIXEL_PERCENTAGE")
                .first()
            )

            thermal = (
                l9.select("ST_B10")
                .multiply(0.00341802)
                .add(149.0)
                .subtract(273.15)
            )

            avg_temp = thermal.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=roi,
                scale=30,
                maxPixels=1e9
            ).get("ST_B10").getInfo()

            ndvi = s2.normalizedDifference(['B8', 'B4']).reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=roi,
                scale=10
            ).get('nd').getInfo()

            st.markdown("<div class='section-title'>Average Surface Temperature</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='metric'>{round(avg_temp,1)} °C</div>", unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("<div class='section-title'>Green Cover (NDVI)</div>", unsafe_allow_html=True)
            st.write(round(ndvi, 2))

        except:
            st.error("Satellite data unavailable for this area.")

    else:
        st.info("Draw a boundary on the map to analyze heat.")

# ===============================
# RIGHT PANEL — MAP
# ===============================
with col_map:

    m = folium.Map(
        location=st.session_state.map_center,
        zoom_start=15,
        tiles="CartoDB positron"
    )

    Draw(export=True).add_to(m)

    if st.session_state.roi_geom:
        roi = ee.Geometry(st.session_state.roi_geom)

        thermal = (
            ee.ImageCollection("LANDSAT/LC09/C02/T1_L2")
            .filterBounds(roi)
            .filterDate("2025-04-01", "2025-07-31")
            .sort("CLOUD_COVER")
            .first()
            .select("ST_B10")
            .multiply(0.00341802)
            .add(149.0)
            .subtract(273.15)
            .clip(roi)
        )

        m.addLayer(
            thermal,
            {
                "min": 20,
                "max": 45,
                "palette": ["blue", "green", "yellow", "red"]
            },
            "Heat Map",
            opacity=0.6
        )

    map_data = st_folium(m, height=720, use_container_width=True)

    if map_data and map_data.get("last_active_drawing"):
        st.session_state.roi_geom = map_data["last_active_drawing"]["geometry"]
        st.rerun()
