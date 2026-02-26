#!/usr/bin/env python3
"""
Weather dashboard — Streamlit UI.
Uses Open-Meteo API (free, no key required).
"""

import streamlit as st
import requests
from datetime import datetime
from streamlit_searchbox import st_searchbox

# --- API endpoints ---
WEATHER_API  = "https://api.open-meteo.com/v1/forecast"
GEO_API      = "https://geocoding-api.open-meteo.com/v1/search"

# --- Default city ---
DEFAULT_LOCATION = {
    "name": "Bothell",
    "admin1": "Washington",
    "country": "United States",
    "latitude": 47.7623,
    "longitude": -122.2054,
    "timezone": "America/Los_Angeles",
}

WMO_CODES = {
    0:  ("Clear sky",            "☀️"),
    1:  ("Mainly clear",         "🌤️"),
    2:  ("Partly cloudy",        "⛅"),
    3:  ("Overcast",             "☁️"),
    45: ("Foggy",                "🌫️"),
    48: ("Rime fog",             "🌫️"),
    51: ("Light drizzle",        "🌦️"),
    53: ("Moderate drizzle",     "🌦️"),
    55: ("Dense drizzle",        "🌧️"),
    61: ("Slight rain",          "🌧️"),
    63: ("Moderate rain",        "🌧️"),
    65: ("Heavy rain",           "🌧️"),
    71: ("Slight snowfall",      "❄️"),
    73: ("Moderate snowfall",    "❄️"),
    75: ("Heavy snowfall",       "❄️"),
    77: ("Snow grains",          "🌨️"),
    80: ("Slight showers",       "🌦️"),
    81: ("Moderate showers",     "🌦️"),
    82: ("Violent showers",      "⛈️"),
    85: ("Slight snow showers",  "🌨️"),
    86: ("Heavy snow showers",   "🌨️"),
    95: ("Thunderstorm",         "⛈️"),
    96: ("Thunderstorm + hail",  "⛈️"),
    99: ("Thunderstorm + hail",  "⛈️"),
}

WIND_DIRS = ["N","NNE","NE","ENE","E","ESE","SE","SSE",
             "S","SSW","SW","WSW","W","WNW","NW","NNW"]


def wind_dir_label(degrees):
    return WIND_DIRS[round(degrees / 22.5) % 16]


def location_label(loc):
    parts = [loc["name"]]
    if loc.get("admin1"):
        parts.append(loc["admin1"])
    parts.append(loc["country"])
    return ", ".join(parts)


@st.cache_data(ttl=3600)
def geocode(query: str):
    """Return list of matching locations for a city name query."""
    r = requests.get(GEO_API, params={"name": query, "count": 5, "language": "en"}, timeout=10)
    r.raise_for_status()
    return r.json().get("results", [])


def search_cities(query: str):
    """Called on every keystroke — returns (label, loc_dict) pairs for the dropdown."""
    if not query or len(query.strip()) < 2:
        return []
    try:
        results = geocode(query.strip())
        return [(location_label(loc), loc) for loc in results]
    except Exception:
        return []


@st.cache_data(ttl=600)
def fetch_weather(lat: float, lon: float, timezone: str, temp_unit: str = "fahrenheit"):
    params = {
        "latitude": lat,
        "longitude": lon,
        "timezone": timezone,
        "temperature_unit": temp_unit,
        "wind_speed_unit": "mph",
        "precipitation_unit": "inch",
        "current": [
            "temperature_2m", "apparent_temperature", "relative_humidity_2m",
            "weather_code", "wind_speed_10m", "wind_direction_10m",
            "wind_gusts_10m", "precipitation", "cloud_cover", "is_day",
        ],
        "daily": [
            "weather_code", "temperature_2m_max", "temperature_2m_min",
            "precipitation_sum", "precipitation_probability_max",
        ],
        "forecast_days": 5,
    }
    r = requests.get(WEATHER_API, params=params, timeout=10)
    r.raise_for_status()
    return r.json()


# ── Page setup ────────────────────────────────────────────────────────────
st.set_page_config(page_title="Weather", page_icon="🌤️", layout="centered")

st.markdown("""
<style>
  .stApp { background-color: #1a2535; }
  #MainMenu, footer, header { visibility: hidden; }

  /* Searchbox */
  div[data-testid="stCustomComponentV1"] iframe {
    border-radius: 10px;
  }

  /* Temperature */
  .temp-display {
    font-size: 5rem; font-weight: 700; color: #ffffff; line-height: 1;
  }
  .cond-icon { font-size: 3.5rem; line-height: 1; }

  /* Stat cards */
  .stat-card {
    background: #223047; border-radius: 12px;
    padding: 14px 10px; text-align: center;
  }
  .stat-icon  { font-size: 1.6rem; }
  .stat-value { font-size: 1.3rem; font-weight: 700; color: #ffffff; margin: 2px 0; }
  .stat-label { font-size: 0.75rem; color: #8ba7c7; }

  /* Forecast cards */
  .fc-card {
    background: #223047; border-radius: 12px;
    padding: 12px 8px; text-align: center;
  }
  .fc-day  { font-size: 0.8rem; font-weight: 700; color: #8ba7c7; }
  .fc-icon { font-size: 1.8rem; line-height: 1.4; }
  .fc-hi   { font-size: 1rem; font-weight: 700; color: #ffffff; }
  .fc-lo   { font-size: 0.9rem; color: #8ba7c7; }
  .fc-rain { font-size: 0.75rem; color: #64b5f6; margin-top: 2px; }

  .subtext { color: #8ba7c7; font-size: 0.9rem; }
  .feels   { color: #8ba7c7; font-size: 1rem; margin-top: -4px; }
  hr { border-color: #223047 !important; margin: 1rem 0; }

  div[data-testid="stButton"] > button {
    background: #223047; color: #5bc8f5;
    border: 1px solid #5bc8f5; border-radius: 8px; padding: 6px 20px;
  }
  div[data-testid="stButton"] > button:hover {
    background: #5bc8f5; color: #1a2535;
  }
</style>
""", unsafe_allow_html=True)


# ── Session state defaults ────────────────────────────────────────────────
if "location" not in st.session_state:
    st.session_state.location = DEFAULT_LOCATION
if "temp_unit" not in st.session_state:
    st.session_state.temp_unit = "fahrenheit"


# ── Live search bar ───────────────────────────────────────────────────────
selected = st_searchbox(
    search_cities,
    key="city_search",
    placeholder="🔍  Search any city in the world…",
    clear_on_submit=False,
    debounce=300,
)

if selected:
    st.session_state.location = selected
    st.cache_data.clear()


# ── Fetch weather for selected location ───────────────────────────────────
loc = st.session_state.location
try:
    data = fetch_weather(loc["latitude"], loc["longitude"], loc["timezone"], st.session_state.temp_unit)
except Exception as e:
    st.error(f"Could not fetch weather: {e}")
    st.stop()

cur   = data["current"]
daily = data["daily"]

code           = cur["weather_code"]
condition, icon = WMO_CODES.get(code, ("Unknown", "❓"))
wind_dir       = wind_dir_label(cur["wind_direction_10m"])
dt             = datetime.fromisoformat(cur["time"])
day_night      = "☀ Day" if cur["is_day"] else "☾ Night"
time_str       = dt.strftime("%A, %B %-d  •  %-I:%M %p")


# ── Header ────────────────────────────────────────────────────────────────
unit_symbol = "F" if st.session_state.temp_unit == "fahrenheit" else "C"

col_title, col_unit, col_refresh = st.columns([4, 1, 1])
with col_title:
    st.markdown(f"## 📍 {location_label(loc)}")
    st.markdown(f'<p class="subtext">{time_str} &nbsp;·&nbsp; {day_night}</p>',
                unsafe_allow_html=True)
with col_unit:
    st.markdown("<br>", unsafe_allow_html=True)
    chosen = st.radio("Unit", ["°F", "°C"], index=0 if st.session_state.temp_unit == "fahrenheit" else 1,
                      horizontal=True, label_visibility="collapsed")
    new_unit = "fahrenheit" if chosen == "°F" else "celsius"
    if new_unit != st.session_state.temp_unit:
        st.session_state.temp_unit = new_unit
        st.cache_data.clear()
        st.rerun()
with col_refresh:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("⟳ Refresh"):
        st.cache_data.clear()
        st.rerun()

st.markdown("---")


# ── Current conditions ────────────────────────────────────────────────────
col_left, col_right = st.columns([1, 1])
with col_left:
    st.markdown(f'<div class="cond-icon">{icon}</div>', unsafe_allow_html=True)
    st.markdown(f"**{condition}**")
    st.markdown(f'<p class="feels">Feels like {cur["apparent_temperature"]:.0f}°{unit_symbol}</p>',
                unsafe_allow_html=True)
with col_right:
    st.markdown(
        f'<div class="temp-display">{cur["temperature_2m"]:.0f}°'
        f'<span style="font-size:2rem;color:#8ba7c7">{unit_symbol}</span></div>',
        unsafe_allow_html=True,
    )

st.markdown("---")


# ── Stats row ─────────────────────────────────────────────────────────────
stats = [
    ("💧", f'{cur["relative_humidity_2m"]}%',              "Humidity"),
    ("💨", f'{cur["wind_speed_10m"]:.0f} mph {wind_dir}',  "Wind"),
    ("🌬️", f'{cur["wind_gusts_10m"]:.0f} mph',             "Gusts"),
    ("☁️",  f'{cur["cloud_cover"]}%',                       "Cloud Cover"),
]
cols = st.columns(4)
for col, (icon_s, value, label) in zip(cols, stats):
    with col:
        st.markdown(
            f'<div class="stat-card">'
            f'<div class="stat-icon">{icon_s}</div>'
            f'<div class="stat-value">{value}</div>'
            f'<div class="stat-label">{label}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

if cur["precipitation"] > 0:
    st.markdown(
        f'<p class="subtext" style="margin-top:10px">🌧 Current precipitation: {cur["precipitation"]:.2f} in</p>',
        unsafe_allow_html=True,
    )

st.markdown("---")


# ── 5-Day Forecast ────────────────────────────────────────────────────────
st.markdown("**5-Day Forecast**")
fc_cols = st.columns(5)
for i, col in enumerate(fc_cols):
    date    = datetime.fromisoformat(daily["time"][i])
    fc_code = daily["weather_code"][i]
    _, fc_icon = WMO_CODES.get(fc_code, ("?", "❓"))
    hi   = daily["temperature_2m_max"][i]
    lo   = daily["temperature_2m_min"][i]
    prob = daily["precipitation_probability_max"][i] or 0

    day_label = "Today" if i == 0 else date.strftime("%a")
    rain_html = f'<div class="fc-rain">💧 {prob}%</div>' if prob > 10 else ""

    with col:
        st.markdown(
            f'<div class="fc-card">'
            f'<div class="fc-day">{day_label}</div>'
            f'<div class="fc-icon">{fc_icon}</div>'
            f'<div class="fc-hi">{hi:.0f}°{unit_symbol}</div>'
            f'<div class="fc-lo">{lo:.0f}°{unit_symbol}</div>'
            f'{rain_html}'
            f'</div>',
            unsafe_allow_html=True,
        )

st.markdown("<br>", unsafe_allow_html=True)
updated = datetime.now().strftime("%-I:%M %p")
st.markdown(
    f'<p class="subtext" style="text-align:center">'
    f'Last updated {updated} · Data from Open-Meteo</p>',
    unsafe_allow_html=True,
)