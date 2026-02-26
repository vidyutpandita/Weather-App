#!/usr/bin/env python3
"""
Weather dashboard — Streamlit UI.
Uses Open-Meteo API (free, no key required).
"""

import random
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


def get_weather_animation_html(code: int, is_day: bool) -> str:
    """Return a fixed-position animated weather overlay (pointer-events:none)."""
    rng = random.Random(code * 31 + (0 if is_day else 1000))

    if code in (95, 96, 99):
        anim = "thunder"
    elif code in (71, 73, 75, 77, 85, 86):
        anim = "snow"
    elif code in (51, 53, 55, 61, 63, 65, 80, 81, 82):
        anim = "rain"
    elif code in (45, 48):
        anim = "fog"
    elif code == 3:
        anim = "overcast"
    elif code in (1, 2):
        anim = "partly_cloudy"
    else:
        anim = "clear_day" if is_day else "clear_night"

    keyframes = """<style>
@keyframes wt-rain    { from{transform:translateY(-30px) translateX(0)}   to{transform:translateY(105vh) translateX(-15px)} }
@keyframes wt-snow    { 0%{transform:translateY(-20px) translateX(0);opacity:.9} 25%{transform:translateY(25vh) translateX(20px)} 75%{transform:translateY(75vh) translateX(-15px)} 100%{transform:translateY(105vh) translateX(5px);opacity:.3} }
@keyframes wt-star    { 0%,100%{opacity:.15;transform:scale(.8)} 50%{opacity:.9;transform:scale(1.2)} }
@keyframes wt-sun-glow{ 0%,100%{box-shadow:0 0 50px 25px rgba(255,200,50,.3),0 0 100px 50px rgba(255,140,0,.12)} 50%{box-shadow:0 0 70px 40px rgba(255,200,50,.45),0 0 140px 70px rgba(255,140,0,.2)} }
@keyframes wt-ray-cw  { from{transform:rotate(0deg)}   to{transform:rotate(360deg)} }
@keyframes wt-ray-ccw { from{transform:rotate(0deg)}   to{transform:rotate(-360deg)} }
@keyframes wt-cloud   { from{transform:translateX(-220px)} to{transform:translateX(110vw)} }
@keyframes wt-fog     { 0%{transform:translateX(-30%);opacity:0} 15%{opacity:1} 85%{opacity:1} 100%{transform:translateX(110%);opacity:0} }
@keyframes wt-flash   { 0%,100%{opacity:0} 5%{opacity:.55} 6%{opacity:0} 7%{opacity:.3} 8%{opacity:0} }
</style>"""

    wrap = '<div style="position:fixed;top:0;left:0;width:100vw;height:100vh;pointer-events:none;z-index:9999;overflow:hidden;">'
    parts = []

    if anim in ("rain", "thunder"):
        count = 55 if code in (65, 82) else 30
        for _ in range(count):
            left = rng.randint(0, 100)
            h    = rng.randint(12, 28)
            d    = round(rng.uniform(0, 3), 2)
            dur  = round(rng.uniform(0.55, 1.3), 2)
            op   = round(rng.uniform(0.35, 0.65), 2)
            parts.append(
                f'<div style="position:absolute;left:{left}%;top:0;width:1.5px;height:{h}px;'
                f'background:linear-gradient(transparent,rgba(100,181,246,{op}));'
                f'animation:wt-rain {dur}s {d}s linear infinite;border-radius:1px;"></div>'
            )
        if anim == "thunder":
            parts.append(
                '<div style="position:absolute;inset:0;background:rgba(180,210,255,.18);'
                'animation:wt-flash 7s .5s ease-in-out infinite;"></div>'
            )

    elif anim == "snow":
        for _ in range(38):
            left = rng.randint(0, 100)
            size = round(rng.uniform(0.7, 1.7), 1)
            d    = round(rng.uniform(0, 12), 2)
            dur  = round(rng.uniform(7, 16), 2)
            op   = round(rng.uniform(0.45, 0.8), 2)
            ch   = rng.choice(["❄", "❅", "❆", "·", "•"])
            parts.append(
                f'<div style="position:absolute;left:{left}%;top:-24px;font-size:{size}rem;'
                f'color:rgba(255,255,255,{op});'
                f'animation:wt-snow {dur}s {d}s linear infinite;'
                f'user-select:none;">{ch}</div>'
            )

    elif anim == "clear_day":
        parts += [
            '<div style="position:absolute;top:30px;right:50px;width:90px;height:90px;'
            'background:radial-gradient(circle,rgba(255,225,80,.95),rgba(255,160,0,.75));'
            'border-radius:50%;animation:wt-sun-glow 4s ease-in-out infinite;"></div>',
            '<div style="position:absolute;top:10px;right:30px;width:130px;height:130px;'
            'border:3px dashed rgba(255,210,60,.3);border-radius:50%;'
            'animation:wt-ray-cw 15s linear infinite;"></div>',
            '<div style="position:absolute;top:-10px;right:10px;width:170px;height:170px;'
            'border:2px dashed rgba(255,200,50,.12);border-radius:50%;'
            'animation:wt-ray-ccw 25s linear infinite;"></div>',
        ]

    elif anim == "clear_night":
        for _ in range(60):
            top  = rng.randint(2, 65)
            left = rng.randint(0, 100)
            size = round(rng.uniform(0.18, 0.45), 2)
            d    = round(rng.uniform(0, 6), 2)
            dur  = round(rng.uniform(2, 5), 2)
            parts.append(
                f'<div style="position:absolute;top:{top}%;left:{left}%;'
                f'width:{size}rem;height:{size}rem;background:white;border-radius:50%;'
                f'animation:wt-star {dur}s {d}s ease-in-out infinite;"></div>'
            )

    elif anim in ("partly_cloudy", "overcast"):
        count = 3 if anim == "partly_cloudy" else 6
        op    = 0.10 if anim == "partly_cloudy" else 0.18
        for _ in range(count):
            top = rng.randint(3, 40)
            w   = rng.randint(120, 220)
            d   = rng.randint(0, 20)
            dur = rng.randint(30, 60)
            parts.append(
                f'<div style="position:absolute;top:{top}%;left:-{w}px;'
                f'width:{w}px;height:{w // 2}px;'
                f'background:rgba(200,220,255,{op});border-radius:50%;filter:blur(12px);'
                f'animation:wt-cloud {dur}s {d}s linear infinite;"></div>'
            )

    elif anim == "fog":
        for _ in range(6):
            top = rng.randint(5, 85)
            h   = rng.randint(50, 120)
            d   = rng.randint(0, 25)
            dur = rng.randint(18, 35)
            op  = round(rng.uniform(0.05, 0.12), 2)
            parts.append(
                f'<div style="position:absolute;top:{top}%;left:0;width:100%;height:{h}px;'
                f'background:rgba(200,220,240,{op});filter:blur(18px);'
                f'animation:wt-fog {dur}s {d}s linear infinite;"></div>'
            )

    return keyframes + wrap + "".join(parts) + "</div>"


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

# ── Weather animation overlay ──────────────────────────────────────────────
st.markdown(get_weather_animation_html(code, bool(cur["is_day"])), unsafe_allow_html=True)


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