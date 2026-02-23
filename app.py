import streamlit as st
import ee
import folium
from folium.plugins import Draw
from streamlit_folium import st_folium
import geocoder

# -------------------------------
# App Config
# -------------------------------
st.set_page_config(
    page_title="EcoPulse | Heat Intelligence",
    layout="wide"
)

st.title("🌍 EcoPulse")
st.caption("Visualizing Urban Heat Using Satellite Intelligence")

# -------------------------------
# Earth Engine Init
# -------------------------------
try:
    ee.Initialize()
except:
    ee.Authenticate()
    ee.Initialize()

# -------------------------------
# Session State
# -------------------------------
if "roi" not in st.session_state:
    st.session_state.roi = None

if "center" not in st.session_state:
    st.session_state.center = [28.61, 77.21]  # Delhi default

# -------------------------------
# Sidebar Controls
# -------------------------------
st.sidebar.header("🔍 Area Selection")

search = st.sidebar.text_input("Search Location")

if search:
    g = geocoder.arcgis(search)
    if g.ok:
        st.session_state.center = [g.lat, g.lng]

date_range = st.sidebar.selectbox(
    "Select Time Period",
    ["Apr–Jun 2025", "Apr–Jun 2024"]
)

dates = {
    "Apr–Jun 2025": ("2025-04-01", "2025-06-30"),
    "Apr–Jun 2024": ("2024-04-01", "2024-06-30")
}

start_date, end_date = dates[date_range]

# -------------------------------
# Map
# -------------------------------
m = folium.Map(
    location=st.session_state.center,
    zoom_start=14,
    tiles="CartoDB positron"
)

Draw(export=True).add_to(m)

# -------------------------------
# If ROI selected
# -------------------------------
if st.session_state.roi:
    roi = ee.Geometry(st.session_state.roi)

    image = (
        ee.ImageCollection("LANDSAT/LC09/C02/T1_L2")
        .filterBounds(roi)
        .filterDate(start_date, end_date)
        .sort("CLOUD_COVER")
        .first()
    )

    lst = (
        image.select("ST_B10")
        .multiply(0.00341802)
        .add(149.0)
        .subtract(273.15)
    )

    stats = lst.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=roi,
        scale=30,
        maxPixels=1e9
    )

    avg_temp = stats.get("ST_B10").getInfo()

    folium.TileLayer(
        tiles=lst.getMapId({
            "min": 20,
            "max": 45,
            "palette": ["blue", "green", "yellow", "red"]
        })["tile_fetcher"].url_format,
        name="Heat Map",
        attr="Google Earth Engine"
    ).add_to(m)

    st.metric(
        "Average Surface Temperature",
        f"{round(avg_temp, 1)} °C"
    )

# -------------------------------
# Render Map
# -------------------------------
map_data = st_folium(
    m,
    height=650,
    use_container_width=True
)

if map_data and map_data.get("last_active_drawing"):
    st.session_state.roi = map_data["last_active_drawing"]["geometry"]
    st.experimental_rerun()
