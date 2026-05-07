import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
import requests
import time
import pytz
from datetime import datetime, timedelta

try:
    from engine import run_engine
except Exception:
    run_engine = None

try:
    from fundamental import get_fundamental_data
except Exception:
    get_fundamental_data = None

# ─────────────────────────────────────────────
#  PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="XAUUSD DSS — JVD Studio",
    page_icon="🏅",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────
#  GLOBAL CSS — full dark/light theme fix
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;700&display=swap');

/* ── ROOT VARIABLES ── */
:root {
    --gold: #F5A623;
    --gold-light: #FFD580;
    --gold-glow: rgba(245,166,35,0.35);
    --buy: #00E396;
    --buy-bg: rgba(0,227,150,0.12);
    --sell: #FF4560;
    --sell-bg: rgba(255,69,96,0.12);
    --wait: #F5A623;
    --wait-bg: rgba(245,166,35,0.12);
    --bg-primary: #0A0C10;
    --bg-secondary: #111318;
    --bg-card: #161A22;
    --bg-card2: #1C2130;
    --border: rgba(255,255,255,0.07);
    --text-primary: #F0F2F5;
    --text-secondary: #8B93A5;
    --text-muted: #525B6B;
    --radius: 14px;
    --shadow: 0 4px 24px rgba(0,0,0,0.4);
}

/* ── FULL APP BACKGROUND ── */
html, body, [data-testid="stAppViewContainer"],
[data-testid="stApp"], .main, .block-container,
[data-testid="stVerticalBlock"] {
    background-color: var(--bg-primary) !important;
    color: var(--text-primary) !important;
    font-family: 'Space Grotesk', sans-serif !important;
}

/* ── SIDEBAR ── */
[data-testid="stSidebar"],
[data-testid="stSidebar"] > div,
[data-testid="stSidebarContent"] {
    background-color: #0D0F14 !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] * {
    color: var(--text-primary) !important;
    font-family: 'Space Grotesk', sans-serif !important;
}

/* ── HAMBURGER BUTTON ── */
[data-testid="collapsedControl"],
[data-testid="collapsedControl"] svg,
[data-testid="collapsedControl"] path {
    color: var(--gold) !important;
    fill: var(--gold) !important;
}
button[kind="header"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
}

/* ── HEADER TOOLBAR ── */
[data-testid="stHeader"],
header[data-testid="stHeader"] {
    background-color: rgba(10,12,16,0.95) !important;
    backdrop-filter: blur(12px) !important;
    border-bottom: 1px solid var(--border) !important;
}
[data-testid="stToolbar"] {
    background: transparent !important;
}

/* ── ALL STREAMLIT WIDGETS ── */
div[data-baseweb="select"] > div,
div[data-baseweb="input"] > div,
div[data-baseweb="textarea"] > div,
[data-testid="stNumberInput"] input,
[data-testid="stTextInput"] input {
    background-color: var(--bg-card2) !important;
    border-color: var(--border) !important;
    color: var(--text-primary) !important;
    border-radius: 8px !important;
}

/* ── SLIDER ── */
[data-testid="stSlider"] [role="slider"] {
    background-color: var(--gold) !important;
}
[data-testid="stSlider"] [data-testid="stSliderTrack"] > div:first-child {
    background: var(--gold) !important;
}

/* ── EXPANDER ── */
[data-testid="stExpander"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
}
[data-testid="stExpander"] summary {
    color: var(--text-primary) !important;
}

/* ── STREAMLIT BUTTONS ── */
[data-testid="baseButton-secondary"],
[data-testid="baseButton-primary"] {
    background: var(--bg-card2) !important;
    color: var(--text-primary) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 600 !important;
    transition: all 0.2s !important;
}
[data-testid="baseButton-primary"] {
    background: linear-gradient(135deg, var(--gold), #E8941A) !important;
    color: #0A0C10 !important;
    border-color: var(--gold) !important;
}

/* ── METRICS ── */
[data-testid="stMetric"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    padding: 16px 20px !important;
}
[data-testid="stMetricLabel"] {
    color: var(--text-secondary) !important;
    font-size: 11px !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
}
[data-testid="stMetricValue"] {
    color: var(--text-primary) !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 22px !important;
}
[data-testid="stMetricDelta"] {
    font-size: 12px !important;
}

/* ── DIVIDER ── */
hr {
    border-color: var(--border) !important;
    margin: 12px 0 !important;
}

/* ── SCROLLBAR ── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: var(--bg-primary); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }

/* ── CUSTOM COMPONENTS ── */
.jvd-header {
    background: linear-gradient(135deg, var(--bg-card) 0%, var(--bg-card2) 100%);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 20px 28px;
    margin-bottom: 20px;
    position: relative;
    overflow: hidden;
}
.jvd-header::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, transparent, var(--gold), transparent);
}
.jvd-header-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 12px;
}
.jvd-logo {
    font-size: 22px;
    font-weight: 700;
    letter-spacing: -0.02em;
    color: var(--text-primary);
}
.jvd-logo span { color: var(--gold); }
.live-price-big {
    font-family: 'JetBrains Mono', monospace;
    font-size: 38px;
    font-weight: 700;
    color: var(--gold);
    text-shadow: 0 0 30px var(--gold-glow), 0 0 60px rgba(245,166,35,0.15);
    letter-spacing: -0.02em;
    line-height: 1;
}
.live-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(0,227,150,0.12);
    border: 1px solid rgba(0,227,150,0.3);
    border-radius: 20px;
    padding: 4px 12px;
    font-size: 11px;
    font-weight: 600;
    color: #00E396;
    letter-spacing: 0.05em;
}
.live-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #00E396;
    animation: pulse 1.5s infinite;
}
@keyframes pulse {
    0%, 100% { opacity: 1; box-shadow: 0 0 0 0 rgba(0,227,150,0.5); }
    50% { opacity: 0.6; box-shadow: 0 0 0 5px rgba(0,227,150,0); }
}
.timestamp-label {
    font-size: 11px;
    color: var(--text-muted);
    font-family: 'JetBrains Mono', monospace;
    margin-top: 4px;
}
.card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 20px;
    height: 100%;
    position: relative;
    overflow: hidden;
}
.card-title {
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: var(--text-muted);
    margin-bottom: 12px;
}
.signal-buy {
    background: var(--buy-bg);
    border: 1px solid rgba(0,227,150,0.3);
    border-radius: var(--radius);
    padding: 20px;
}
.signal-sell {
    background: var(--sell-bg);
    border: 1px solid rgba(255,69,96,0.3);
    border-radius: var(--radius);
    padding: 20px;
}
.signal-wait {
    background: var(--wait-bg);
    border: 1px solid rgba(245,166,35,0.3);
    border-radius: var(--radius);
    padding: 20px;
}
.signal-label {
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: var(--text-secondary);
    margin-bottom: 6px;
}
.signal-value-buy { font-size: 42px; font-weight: 700; color: var(--buy); line-height: 1; text-shadow: 0 0 20px rgba(0,227,150,0.3); }
.signal-value-sell { font-size: 42px; font-weight: 700; color: var(--sell); line-height: 1; text-shadow: 0 0 20px rgba(255,69,96,0.3); }
.signal-value-wait { font-size: 42px; font-weight: 700; color: var(--wait); line-height: 1; text-shadow: 0 0 20px rgba(245,166,35,0.3); }
.confidence-bar-wrap { margin-top: 12px; }
.confidence-bar-bg { height: 6px; background: rgba(255,255,255,0.08); border-radius: 3px; overflow: hidden; }
.confidence-bar-fill-buy { height: 100%; background: linear-gradient(90deg, var(--buy), #00FFB3); border-radius: 3px; transition: width 0.8s ease; }
.confidence-bar-fill-sell { height: 100%; background: linear-gradient(90deg, var(--sell), #FF7A8A); border-radius: 3px; }
.confidence-bar-fill-wait { height: 100%; background: linear-gradient(90deg, var(--wait), var(--gold-light)); border-radius: 3px; }
.snap-row { display: flex; flex-wrap: wrap; gap: 10px; }
.snap-item {
    flex: 1 1 140px;
    background: var(--bg-card2);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 14px 16px;
}
.snap-label { font-size: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.08em; color: var(--text-muted); margin-bottom: 5px; }
.snap-value { font-family: 'JetBrains Mono', monospace; font-size: 17px; font-weight: 700; color: var(--text-primary); }
.snap-sub { font-size: 11px; color: var(--text-secondary); margin-top: 3px; }
.risk-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 24px;
    margin-top: 16px;
}
.risk-title {
    font-size: 13px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: var(--gold);
    margin-bottom: 18px;
    display: flex;
    align-items: center;
    gap: 8px;
}
.risk-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px 0;
    border-bottom: 1px solid var(--border);
}
.risk-row:last-child { border-bottom: none; }
.risk-key { font-size: 13px; color: var(--text-secondary); }
.risk-val { font-family: 'JetBrains Mono', monospace; font-size: 14px; font-weight: 700; color: var(--text-primary); }
.risk-val-buy { color: var(--buy); }
.risk-val-sell { color: var(--sell); }
.risk-val-warn { color: #FFA500; }
.sl-explainer {
    background: rgba(245,166,35,0.06);
    border: 1px solid rgba(245,166,35,0.2);
    border-radius: 10px;
    padding: 16px;
    margin-top: 16px;
    font-size: 13px;
    color: var(--text-secondary);
    line-height: 1.7;
}
.sl-explainer strong { color: var(--gold); }
.macro-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    border-radius: 20px;
    padding: 5px 12px;
    font-size: 12px;
    font-weight: 600;
}
.pill-bull { background: var(--buy-bg); border: 1px solid rgba(0,227,150,0.3); color: var(--buy); }
.pill-bear { background: var(--sell-bg); border: 1px solid rgba(255,69,96,0.3); color: var(--sell); }
.pill-neut { background: var(--wait-bg); border: 1px solid rgba(245,166,35,0.3); color: var(--wait); }
.section-header {
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: var(--text-muted);
    padding: 8px 0 12px 0;
    border-bottom: 1px solid var(--border);
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    gap: 8px;
}
.section-header::before {
    content: '';
    width: 3px;
    height: 14px;
    background: var(--gold);
    border-radius: 2px;
}
.copyright-bar {
    text-align: center;
    font-size: 11px;
    color: var(--text-muted);
    padding: 20px 0 8px 0;
    border-top: 1px solid var(--border);
    margin-top: 32px;
}

/* ── FLOATING ACTION BUTTON — selalu terlihat saat scroll ── */
.jvd-fab-wrapper {
    position: fixed;
    bottom: 24px;
    right: 24px;
    z-index: 99999;
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 10px;
}
.jvd-fab {
    display: flex;
    align-items: center;
    gap: 10px;
    background: linear-gradient(135deg, #F5A623, #E8941A);
    color: #0A0C10 !important;
    border: none;
    border-radius: 50px;
    padding: 14px 22px;
    font-family: 'Space Grotesk', sans-serif;
    font-size: 14px;
    font-weight: 700;
    cursor: pointer;
    box-shadow: 0 4px 20px rgba(245,166,35,0.5), 0 0 40px rgba(245,166,35,0.15);
    transition: all 0.2s ease;
    text-decoration: none;
    letter-spacing: 0.01em;
    white-space: nowrap;
}
.jvd-fab:hover {
    transform: translateY(-2px) scale(1.03);
    box-shadow: 0 8px 30px rgba(245,166,35,0.6), 0 0 60px rgba(245,166,35,0.2);
    background: linear-gradient(135deg, #FFB940, #F5A623);
}
.jvd-fab:active {
    transform: translateY(0) scale(0.98);
}
.jvd-fab-pause {
    display: flex;
    align-items: center;
    gap: 8px;
    background: rgba(10,12,16,0.92);
    color: #8B93A5 !important;
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 50px;
    padding: 8px 16px;
    font-family: 'Space Grotesk', sans-serif;
    font-size: 12px;
    font-weight: 600;
    cursor: pointer;
    backdrop-filter: blur(12px);
    box-shadow: 0 2px 12px rgba(0,0,0,0.4);
    transition: all 0.2s ease;
    white-space: nowrap;
}
.jvd-fab-pause:hover {
    border-color: rgba(245,166,35,0.4);
    color: #F5A623 !important;
}
.jvd-fab-status {
    background: rgba(10,12,16,0.88);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 50px;
    padding: 6px 14px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    color: #525B6B;
    backdrop-filter: blur(12px);
    text-align: right;
}
.fab-spin {
    animation: fabspin 1s linear infinite;
}
@keyframes fabspin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
}
/* Mobile adjustment */
@media (max-width: 768px) {
    .jvd-fab-wrapper { bottom: 16px; right: 12px; }
    .jvd-fab { padding: 12px 18px; font-size: 13px; }
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  SESSION STATE
# ─────────────────────────────────────────────
if "live_price" not in st.session_state:
    st.session_state.live_price = None
if "price_change" not in st.session_state:
    st.session_state.price_change = 0.0
if "price_change_pct" not in st.session_state:
    st.session_state.price_change_pct = 0.0
if "last_price_fetch" not in st.session_state:
    st.session_state.last_price_fetch = 0
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = time.time()
if "auto_refresh" not in st.session_state:
    st.session_state.auto_refresh = True
if "dss_result" not in st.session_state:
    st.session_state.dss_result = None
if "hist_data" not in st.session_state:
    st.session_state.hist_data = None
if "risk_capital" not in st.session_state:
    st.session_state.risk_capital = 1000.0
if "risk_pct" not in st.session_state:
    st.session_state.risk_pct = 1.0
if "lot_size" not in st.session_state:
    st.session_state.lot_size = 0.01

# ─────────────────────────────────────────────
#  LIVE PRICE FETCH (gold-api.com — FREE, no key)
# ─────────────────────────────────────────────
def fetch_live_price():
    try:
        r = requests.get("https://api.gold-api.com/price/XAU", timeout=5)
        if r.status_code == 200:
            d = r.json()
            price = float(d.get("price", 0))
            if price > 1000:
                ch = float(d.get("ch", 0))
                chp = float(d.get("chp", 0))
                return price, ch, chp
    except Exception:
        pass
    # Fallback: yfinance
    try:
        t = yf.Ticker("GC=F")
        h = t.history(period="2d", interval="1m")
        if not h.empty and h["Close"].iloc[-1] > 1000:
            price = float(h["Close"].iloc[-1])
            prev = float(h["Close"].iloc[0])
            ch = price - prev
            chp = (ch / prev) * 100 if prev > 0 else 0
            return price, ch, chp
    except Exception:
        pass
    return None, 0, 0

# ─────────────────────────────────────────────
#  DSS DATA FETCH (cached 5 min)
# ─────────────────────────────────────────────
@st.cache_data(ttl=300)
def load_dss_data():
    result = {}
    # Historical data
    try:
        ticker = yf.Ticker("GC=F")
        hist = ticker.history(period="2y", interval="1d")
        hist = hist[hist["Close"] > 1000].copy()
        if not hist.empty:
            result["hist"] = hist
        else:
            raise ValueError("No valid data")
    except Exception:
        try:
            ticker = yf.Ticker("GLD")
            hist = ticker.history(period="2y", interval="1d")
            hist["Close"] = hist["Close"] * 10
            result["hist"] = hist
        except Exception:
            result["hist"] = pd.DataFrame()

    # Engine
    if run_engine is not None and not result.get("hist", pd.DataFrame()).empty:
        try:
            eng = run_engine(result["hist"])
            result["engine"] = eng
        except Exception as e:
            result["engine"] = {"error": str(e)}
    else:
        result["engine"] = {}

    # Fundamental
    if get_fundamental_data is not None:
        try:
            result["fundamental"] = get_fundamental_data()
        except Exception:
            result["fundamental"] = {}
    else:
        result["fundamental"] = {}

    return result

# ─────────────────────────────────────────────
#  AUTO-REFRESH LOGIC (15 seconds for price only)
# ─────────────────────────────────────────────
now = time.time()
price_stale = (now - st.session_state.last_price_fetch) >= 15

if price_stale or st.session_state.live_price is None:
    p, ch, chp = fetch_live_price()
    if p is not None:
        st.session_state.live_price = p
        st.session_state.price_change = ch
        st.session_state.price_change_pct = chp
        st.session_state.last_price_fetch = now

# ─────────────────────────────────────────────
#  LOAD DSS DATA
# ─────────────────────────────────────────────
with st.spinner("Loading market data..."):
    data = load_dss_data()

hist = data.get("hist", pd.DataFrame())
engine = data.get("engine", {})
fundamental = data.get("fundamental", {})

# ─────────────────────────────────────────────
#  EXTRACT DSS VALUES
# ─────────────────────────────────────────────
current_price = st.session_state.live_price or (float(hist["Close"].iloc[-1]) if not hist.empty else 4700.0)
price_change = st.session_state.price_change
price_change_pct = st.session_state.price_change_pct

# Signal from engine
signal = engine.get("signal", "WAIT")
confidence = engine.get("confidence", 55.0)
atr = engine.get("atr", 0.0)
rsi = engine.get("rsi", 50.0)
regime = engine.get("regime", "NEUTRAL")
volatility = engine.get("volatility", "NORMAL")
weekly_open = engine.get("weekly_open", current_price)
monthly_open = engine.get("monthly_open", current_price)
pdh = engine.get("pdh", current_price + 20)
pdl = engine.get("pdl", current_price - 20)

# If engine is missing, compute basic indicators from hist
if not hist.empty and atr == 0.0:
    try:
        c = hist["Close"]
        h = hist["High"]
        l = hist["Low"]
        # ATR
        tr = pd.concat([
            h - l,
            (h - c.shift(1)).abs(),
            (l - c.shift(1)).abs()
        ], axis=1).max(axis=1)
        atr = float(tr.rolling(14).mean().iloc[-1])
        # RSI
        delta = c.diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss.replace(0, 0.0001)
        rsi = float(100 - (100 / (1 + rs.iloc[-1])))
        weekly_open = float(c.iloc[-5]) if len(c) >= 5 else float(c.iloc[0])
        monthly_open = float(c.iloc[-20]) if len(c) >= 20 else float(c.iloc[0])
        pdh = float(h.iloc[-2]) if len(h) >= 2 else current_price + 20
        pdl = float(l.iloc[-2]) if len(l) >= 2 else current_price - 20
    except Exception:
        pass

# Fundamental data
dxy_status = fundamental.get("dxy_status", "—")
dxy_trend = fundamental.get("dxy_trend", "NEUTRAL")
fed_rate = fundamental.get("fed_rate", 0.0)
fed_bias = fundamental.get("fed_bias", "NEUTRAL")
macro_adj = fundamental.get("macro_adj", 0)

# ─────────────────────────────────────────────
#  RISK CALCULATIONS
# ─────────────────────────────────────────────
SL_ATR_MULT = 1.5
TP_ATR_MULT = 2.5
sl_distance = atr * SL_ATR_MULT if atr > 0 else 30.0
tp_distance = atr * TP_ATR_MULT if atr > 0 else 50.0

if signal == "BUY":
    sl_price = current_price - sl_distance
    tp_price = current_price + tp_distance
elif signal == "SELL":
    sl_price = current_price + sl_distance
    tp_price = current_price - tp_distance
else:
    sl_price = current_price - sl_distance
    tp_price = current_price + tp_distance

rr_ratio = tp_distance / sl_distance if sl_distance > 0 else 0

# Pip value for XAUUSD: 1 pip = $0.1 per 0.01 lot (mini)
# For standard lot (1.0): 1 point = $1
pip_val_per_lot = 1.0  # $1 per point per standard lot
sl_pips = sl_distance  # in USD = in points for Gold
risk_usd = (st.session_state.risk_capital * st.session_state.risk_pct / 100)
max_lot = risk_usd / (sl_pips * 100 * pip_val_per_lot) if sl_pips > 0 else 0.01
max_lot = round(max_lot, 2)

# ─────────────────────────────────────────────
#  HEADER
# ─────────────────────────────────────────────
wib_tz = pytz.timezone("Asia/Jakarta")
now_wib = datetime.now(wib_tz)
timestamp_str = now_wib.strftime("%d %b %Y  %H:%M:%S WIB")

change_sign = "+" if price_change >= 0 else ""
change_color = "#00E396" if price_change >= 0 else "#FF4560"

st.markdown(
    '<div class="jvd-header">'
    '<div class="jvd-header-row">'
    '<div>'
    '<div class="jvd-logo">XAU/USD <span>DSS</span> &nbsp;·&nbsp; JVD Studio</div>'
    '<div class="timestamp-label">⏱ ' + timestamp_str + '</div>'
    '</div>'
    '<div style="text-align:right">'
    '<div class="live-price-big">$' + "{:,.2f}".format(current_price) + '</div>'
    '<div style="display:flex;align-items:center;gap:10px;justify-content:flex-end;margin-top:6px">'
    '<span style="font-family:JetBrains Mono,monospace;font-size:13px;color:' + change_color + '">'
    + change_sign + "{:+.2f}".format(price_change) + " (" + change_sign + "{:.2f}".format(price_change_pct) + "%)"
    '</span>'
    '<span class="live-badge"><span class="live-dot"></span>LIVE · AUTO</span>'
    '</div>'
    '</div>'
    '</div>'
    '</div>',
    unsafe_allow_html=True
)

# ─────────────────────────────────────────────
#  FLOATING ACTION BUTTON — mengikuti scroll, selalu terlihat
#  Pakai JS onclick karena st.button tidak bisa fixed position.
#  Klik FAB = hard reload (sama efeknya dengan Refresh Now).
# ─────────────────────────────────────────────
auto_icon = "⏸" if st.session_state.auto_refresh else "▶"
auto_text = "Pause Auto" if st.session_state.auto_refresh else "Resume Auto"
auto_color_fab = "#525B6B" if st.session_state.auto_refresh else "#00E396"

fab_html = (
    '<div class="jvd-fab-wrapper">'
    '<div class="jvd-fab-status" id="fab-status-bar">Live price · auto 15s</div>'
    '<form action="" method="get" style="margin:0">'
    '<button type="button" class="jvd-fab-pause" '
    'onclick="window.location.href=window.location.pathname + \'?toggle_auto=1\'">'
    '<span style="color:' + auto_color_fab + '">' + auto_icon + '</span>'
    ' ' + auto_text +
    '</button>'
    '</form>'
    '<button class="jvd-fab" onclick="'
    'this.querySelector(\'.fab-icon\').classList.add(\'fab-spin\');'
    'setTimeout(function(){window.location.reload(true);},100);">'
    '<span class="fab-icon" style="font-size:16px">🔄</span>'
    'Refresh Now'
    '</button>'
    '</div>'
    '<script>'
    'var fabSecs=15;'
    'var fabEl=document.getElementById("fab-status-bar");'
    'var fabIv=setInterval(function(){'
    '  fabSecs--;'
    '  if(fabEl) fabEl.innerText="Live price \u00b7 refresh in "+fabSecs+"s";'
    '  if(fabSecs<=0){clearInterval(fabIv);if(fabEl)fabEl.innerText="Refreshing...";}'
    '},1000);'
    '</script>'
)
st.markdown(fab_html, unsafe_allow_html=True)

# Handle toggle_auto via query params
qp = st.query_params
if "toggle_auto" in qp:
    st.session_state.auto_refresh = not st.session_state.auto_refresh
    st.query_params.clear()
    st.rerun()

# Info bar slim — status data
rows_label = str(len(hist)) + " rows" if not hist.empty else "No data"
next_refresh_secs = max(0, int(15 - (time.time() - st.session_state.last_price_fetch)))
auto_status = "AUTO ON" if st.session_state.auto_refresh else "AUTO PAUSED"
auto_status_color = "#00E396" if st.session_state.auto_refresh else "#FF4560"
st.markdown(
    '<div style="display:flex;align-items:center;gap:16px;flex-wrap:wrap;'
    'padding:8px 16px;background:var(--bg-card);border:1px solid var(--border);'
    'border-radius:10px;margin-bottom:16px;">'
    '<span style="font-size:11px;color:var(--text-muted);">📊 Data: '
    '<b style="color:var(--text-secondary)">' + rows_label + '</b></span>'
    '<span style="font-size:11px;color:var(--text-muted);">·</span>'
    '<span style="font-size:11px;color:var(--text-muted);">⏱ Price: '
    '<b style="color:var(--gold)">15s auto</b></span>'
    '<span style="font-size:11px;color:var(--text-muted);">·</span>'
    '<span style="font-size:11px;color:var(--text-muted);">🧠 DSS: '
    '<b style="color:var(--gold)">5min cache</b></span>'
    '<span style="font-size:11px;color:var(--text-muted);">·</span>'
    '<span style="font-size:11px;color:' + auto_status_color + ';font-weight:700;">'
    + auto_status + '</span>'
    '<span style="margin-left:auto;font-size:11px;color:var(--text-muted);">'
    '💡 Tombol <b style="color:var(--gold)">🔄 Refresh Now</b> selalu ada di kanan bawah'
    '</span>'
    '</div>',
    unsafe_allow_html=True
)

# ─────────────────────────────────────────────
#  ROW 1: SIGNAL GAUGE  +  MARKET SNAPSHOT
# ─────────────────────────────────────────────
col_gauge, col_snap = st.columns([2, 3], gap="large")

# ── ANIMATED GAUGE ──
with col_gauge:
    st.markdown('<div class="section-header">Signal Engine</div>', unsafe_allow_html=True)

    # Determine colors
    if signal == "BUY":
        sig_class = "signal-buy"
        val_class = "signal-value-buy"
        bar_class = "confidence-bar-fill-buy"
        gauge_color = "#00E396"
        gauge_glow = "rgba(0,227,150,0.4)"
    elif signal == "SELL":
        sig_class = "signal-sell"
        val_class = "signal-value-sell"
        bar_class = "confidence-bar-fill-sell"
        gauge_color = "#FF4560"
        gauge_glow = "rgba(255,69,96,0.4)"
    else:
        sig_class = "signal-wait"
        val_class = "signal-value-wait"
        bar_class = "confidence-bar-fill-wait"
        gauge_color = "#F5A623"
        gauge_glow = "rgba(245,166,35,0.4)"

    # Plotly animated speedometer gauge
    gauge_val = float(confidence) if signal == "BUY" else (100 - float(confidence)) if signal == "SELL" else 50.0
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=float(confidence),
        number={
            "suffix": "%",
            "font": {"size": 36, "color": gauge_color, "family": "JetBrains Mono"},
        },
        delta={
            "reference": 50,
            "increasing": {"color": "#00E396"},
            "decreasing": {"color": "#FF4560"},
            "font": {"size": 14},
        },
        title={
            "text": signal + "<br><span style='font-size:13px;color:#8B93A5'>Confidence</span>",
            "font": {"size": 22, "color": gauge_color, "family": "Space Grotesk"},
        },
        gauge={
            "axis": {
                "range": [0, 100],
                "tickcolor": "#525B6B",
                "tickfont": {"size": 10, "color": "#525B6B", "family": "JetBrains Mono"},
                "tickwidth": 1,
                "nticks": 6,
            },
            "bar": {
                "color": gauge_color,
                "thickness": 0.28,
            },
            "bgcolor": "rgba(0,0,0,0)",
            "borderwidth": 0,
            "steps": [
                {"range": [0, 30], "color": "rgba(255,69,96,0.15)"},
                {"range": [30, 50], "color": "rgba(245,166,35,0.1)"},
                {"range": [50, 70], "color": "rgba(245,166,35,0.1)"},
                {"range": [70, 100], "color": "rgba(0,227,150,0.15)"},
            ],
            "threshold": {
                "line": {"color": gauge_color, "width": 3},
                "thickness": 0.85,
                "value": float(confidence),
            },
        },
    ))
    fig_gauge.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin={"t": 40, "b": 10, "l": 20, "r": 20},
        height=260,
        font={"family": "Space Grotesk"},
    )
    fig_gauge.update_traces(
        gauge_bar_color=gauge_color,
    )
    st.plotly_chart(fig_gauge, use_container_width=True, config={"displayModeBar": False})

    # Signal card with confidence bar
    st.markdown(
        '<div class="' + sig_class + '">'
        '<div class="signal-label">Decision Signal</div>'
        '<div class="' + val_class + '">' + signal + '</div>'
        '<div class="confidence-bar-wrap">'
        '<div style="display:flex;justify-content:space-between;margin-bottom:5px;">'
        '<span style="font-size:11px;color:var(--text-secondary)">Confidence</span>'
        '<span style="font-family:JetBrains Mono,monospace;font-size:12px;color:var(--text-primary)">' + "{:.1f}".format(confidence) + '%</span>'
        '</div>'
        '<div class="confidence-bar-bg">'
        '<div class="' + bar_class + '" style="width:' + str(confidence) + '%"></div>'
        '</div>'
        '</div>'
        '</div>',
        unsafe_allow_html=True
    )

    # Macro pills
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    dxy_pill = "pill-bear" if "weak" in str(dxy_trend).lower() or "bull" in str(dxy_trend).lower() else "pill-neut"
    fed_pill = "pill-bear" if fed_rate > 4 else ("pill-bull" if fed_rate < 3 else "pill-neut")
    st.markdown(
        '<div style="display:flex;flex-wrap:wrap;gap:8px;">'
        '<span class="macro-pill ' + dxy_pill + '">DXY: ' + str(dxy_status) + '</span>'
        '<span class="macro-pill pill-neut">Fed: ' + "{:.1f}".format(fed_rate) + '%</span>'
        '<span class="macro-pill ' + ("pill-bull" if macro_adj > 0 else ("pill-bear" if macro_adj < 0 else "pill-neut")) + '">'
        'Macro Adj: ' + ("+" if macro_adj >= 0 else "") + str(macro_adj) + ' pts</span>'
        '</div>',
        unsafe_allow_html=True
    )

# ── MARKET SNAPSHOT ──
with col_snap:
    st.markdown('<div class="section-header">Market Snapshot</div>', unsafe_allow_html=True)

    # Price vs key levels
    vs_weekly = current_price - weekly_open
    vs_monthly = current_price - monthly_open
    dist_pdh = pdh - current_price
    dist_pdl = current_price - pdl

    rsi_color = "#FF4560" if rsi > 70 else ("#00E396" if rsi < 30 else "#F5A623")
    rsi_label = "Overbought" if rsi > 70 else ("Oversold" if rsi < 30 else "Neutral")
    vol_color = "#FF4560" if str(volatility).upper() in ["HIGH", "EXTREME"] else "#00E396"

    snap_items = [
        ("Gold Price", "$" + "{:,.2f}".format(current_price), ("+" if price_change >= 0 else "") + "{:.2f}".format(price_change) + " today"),
        ("ATR (14)", "${:.2f}".format(atr) if atr > 0 else "—", "Daily range estimate"),
        ("RSI (14)", "{:.1f}".format(rsi), rsi_label),
        ("Regime", str(regime), "Market structure"),
        ("Volatility", str(volatility), "Risk environment"),
        ("Weekly Open", "$" + "{:,.2f}".format(weekly_open), ("+" if vs_weekly >= 0 else "") + "{:.2f}".format(vs_weekly) + " vs now"),
        ("Monthly Open", "$" + "{:,.2f}".format(monthly_open), ("+" if vs_monthly >= 0 else "") + "{:.2f}".format(vs_monthly) + " vs now"),
        ("Prev Day High", "$" + "{:,.2f}".format(pdh), "Dist: ${:.2f}".format(dist_pdh)),
        ("Prev Day Low", "$" + "{:,.2f}".format(pdl), "Dist: ${:.2f}".format(dist_pdl)),
    ]

    snap_html = '<div class="snap-row">'
    for label, val, sub in snap_items:
        snap_html += (
            '<div class="snap-item">'
            '<div class="snap-label">' + label + '</div>'
            '<div class="snap-value">' + val + '</div>'
            '<div class="snap-sub">' + sub + '</div>'
            '</div>'
        )
    snap_html += '</div>'
    st.markdown(snap_html, unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  ROW 2: CHART
# ─────────────────────────────────────────────
st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
st.markdown('<div class="section-header">Price Chart — XAUUSD (GC=F)</div>', unsafe_allow_html=True)

if not hist.empty:
    # Build candlestick chart
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        row_heights=[0.75, 0.25],
        vertical_spacing=0.04,
    )

    # Candlestick
    fig.add_trace(go.Candlestick(
        x=hist.index,
        open=hist["Open"], high=hist["High"],
        low=hist["Low"], close=hist["Close"],
        name="XAUUSD",
        increasing_fillcolor="#00E396",
        increasing_line_color="#00E396",
        decreasing_fillcolor="#FF4560",
        decreasing_line_color="#FF4560",
    ), row=1, col=1)

    # StdDev bands (20-day MA ± 2 StdDev)
    ma20 = hist["Close"].rolling(20).mean()
    std20 = hist["Close"].rolling(20).std()
    upper = ma20 + 2 * std20
    lower = ma20 - 2 * std20

    fig.add_trace(go.Scatter(
        x=hist.index, y=upper,
        mode="lines", name="Upper Band",
        line=dict(color="rgba(245,166,35,0.4)", width=1, dash="dot"),
        showlegend=True,
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=hist.index, y=lower,
        mode="lines", name="Lower Band",
        line=dict(color="rgba(245,166,35,0.4)", width=1, dash="dot"),
        fill="tonexty",
        fillcolor="rgba(245,166,35,0.04)",
        showlegend=False,
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=hist.index, y=ma20,
        mode="lines", name="MA20",
        line=dict(color="rgba(245,166,35,0.7)", width=1.5),
    ), row=1, col=1)

    # Key levels — PDH / PDL
    fig.add_hline(
        y=pdh, line_dash="dash", line_color="rgba(0,227,150,0.5)",
        annotation_text="PDH", annotation_position="right",
        annotation_font_color="#00E396", row=1, col=1)
    fig.add_hline(
        y=pdl, line_dash="dash", line_color="rgba(255,69,96,0.5)",
        annotation_text="PDL", annotation_position="right",
        annotation_font_color="#FF4560", row=1, col=1)
    # Current price line
    fig.add_hline(
        y=current_price, line_dash="solid", line_color="rgba(245,166,35,0.8)",
        line_width=1.5,
        annotation_text="LIVE $" + "{:,.2f}".format(current_price),
        annotation_position="right",
        annotation_font_color="#F5A623", row=1, col=1)

    # Volume
    vol_colors = [
        "#00E39666" if c >= o else "#FF456066"
        for c, o in zip(hist["Close"], hist["Open"])
    ]
    fig.add_trace(go.Bar(
        x=hist.index, y=hist["Volume"],
        name="Volume",
        marker_color=vol_colors,
        showlegend=False,
    ), row=2, col=1)

    # Layout
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#0F1218",
        height=480,
        margin=dict(t=10, b=10, l=60, r=80),
        xaxis_rangeslider_visible=False,
        xaxis2_rangeslider_visible=True,
        xaxis2_rangeslider_thickness=0.03,
        legend=dict(
            orientation="h", yanchor="bottom", y=1.01, xanchor="left", x=0,
            bgcolor="rgba(0,0,0,0)", font=dict(color="#8B93A5", size=11),
        ),
        font=dict(family="Space Grotesk", color="#8B93A5"),
        xaxis=dict(
            gridcolor="rgba(255,255,255,0.04)",
            zerolinecolor="rgba(255,255,255,0.05)",
            linecolor="rgba(255,255,255,0.07)",
            tickfont=dict(color="#525B6B", size=10),
            showgrid=True,
        ),
        yaxis=dict(
            gridcolor="rgba(255,255,255,0.04)",
            zerolinecolor="rgba(255,255,255,0.05)",
            linecolor="rgba(255,255,255,0.07)",
            tickfont=dict(color="#525B6B", size=10, family="JetBrains Mono"),
            tickprefix="$",
            showgrid=True,
            side="right",
        ),
        xaxis2=dict(
            gridcolor="rgba(255,255,255,0.04)",
            tickfont=dict(color="#525B6B", size=10),
        ),
        yaxis2=dict(
            gridcolor="rgba(255,255,255,0.04)",
            tickfont=dict(color="#525B6B", size=9),
            side="right",
        ),
        dragmode="pan",
    )

    # Range buttons
    fig.update_xaxes(
        rangeselector=dict(
            buttons=[
                dict(count=1, label="1M", step="month", stepmode="backward"),
                dict(count=3, label="3M", step="month", stepmode="backward"),
                dict(count=6, label="6M", step="month", stepmode="backward"),
                dict(step="all", label="ALL"),
            ],
            bgcolor="#161A22",
            activecolor="#F5A623",
            bordercolor="rgba(255,255,255,0.07)",
            font=dict(color="#8B93A5", size=11, family="Space Grotesk"),
            x=0, y=1.0,
        ),
        row=1, col=1,
    )

    st.plotly_chart(fig, use_container_width=True, config={
        "displayModeBar": True,
        "modeBarButtonsToRemove": ["toImage", "sendDataToCloud"],
        "displaylogo": False,
        "scrollZoom": False,
    })

    # ── CUSTOM HORIZONTAL SCROLLBAR + ZOOM CONTROLS di bawah chart ──
    # Jumlah total candle
    total_candles = len(hist)

    st.markdown(
        '<div id="chart-nav-wrap" style="'
        'background:var(--bg-card);'
        'border:1px solid var(--border);'
        'border-radius:12px;'
        'padding:16px 20px;'
        'margin-top:-8px;'
        'margin-bottom:8px;'
        '">'

        # ── Baris 1: Label + Zoom preset buttons
        '<div style="display:flex;align-items:center;justify-content:space-between;'
        'flex-wrap:wrap;gap:8px;margin-bottom:14px;">'
        '<span style="font-size:11px;font-weight:700;text-transform:uppercase;'
        'letter-spacing:0.1em;color:var(--text-muted);">📊 Navigasi Chart</span>'
        '<div style="display:flex;gap:6px;flex-wrap:wrap;">'
        '<button class="cnav-btn" onclick="chartZoom(20)" title="Tampilkan 20 candle terakhir">20C</button>'
        '<button class="cnav-btn" onclick="chartZoom(60)" title="Tampilkan 60 candle terakhir">2M</button>'
        '<button class="cnav-btn" onclick="chartZoom(90)" title="Tampilkan 90 candle terakhir">3M</button>'
        '<button class="cnav-btn" onclick="chartZoom(180)" title="Tampilkan 180 candle terakhir">6M</button>'
        '<button class="cnav-btn" onclick="chartZoom(0)" title="Tampilkan semua data">ALL</button>'
        '<button class="cnav-btn cnav-today" onclick="chartGoToday()" title="Lompat ke hari ini">⊳ Today</button>'
        '</div>'
        '</div>'

        # ── Baris 2: Scrollbar geser kiri-kanan
        '<div style="display:flex;align-items:center;gap:10px;">'
        '<span style="font-size:10px;color:var(--text-muted);white-space:nowrap;">◀ Lama</span>'
        '<div style="flex:1;position:relative;">'
        '<input type="range" id="chart-hscroll" min="0" max="100" value="100" step="1"'
        ' oninput="chartScroll(this.value)"'
        ' style="'
        'width:100%;'
        'height:8px;'
        'appearance:none;-webkit-appearance:none;'
        'background:linear-gradient(to right,#F5A623 var(--val,100%),rgba(255,255,255,0.08) var(--val,100%));'
        'border-radius:4px;'
        'outline:none;'
        'cursor:pointer;'
        '">'
        '</div>'
        '<span style="font-size:10px;color:var(--text-muted);white-space:nowrap;">Baru ▶</span>'
        '</div>'

        # ── Baris 3: Zoom in/out + label posisi
        '<div style="display:flex;align-items:center;justify-content:space-between;'
        'margin-top:12px;flex-wrap:wrap;gap:8px;">'
        '<div style="display:flex;gap:6px;">'
        '<button class="cnav-btn" onclick="chartZoomIn()" title="Zoom In — tampilkan lebih sedikit candle">🔍+</button>'
        '<button class="cnav-btn" onclick="chartZoomOut()" title="Zoom Out — tampilkan lebih banyak candle">🔍−</button>'
        '</div>'
        '<span id="chart-pos-label" style="font-family:JetBrains Mono,monospace;'
        'font-size:11px;color:var(--text-secondary);">← Geser slider untuk navigasi →</span>'
        '</div>'

        '</div>'

        # ── CSS untuk tombol nav
        '<style>'
        '.cnav-btn{'
        'background:var(--bg-card2);'
        'color:var(--text-secondary);'
        'border:1px solid var(--border);'
        'border-radius:6px;'
        'padding:5px 12px;'
        'font-family:Space Grotesk,sans-serif;'
        'font-size:11px;'
        'font-weight:600;'
        'cursor:pointer;'
        'transition:all 0.15s;'
        'white-space:nowrap;'
        '}'
        '.cnav-btn:hover{'
        'background:var(--gold);'
        'color:#0A0C10;'
        'border-color:var(--gold);'
        '}'
        '.cnav-today{'
        'background:rgba(245,166,35,0.12);'
        'color:var(--gold);'
        'border-color:rgba(245,166,35,0.3);'
        '}'
        'input[type=range]::-webkit-slider-thumb{'
        'appearance:none;-webkit-appearance:none;'
        'width:20px;height:20px;'
        'border-radius:50%;'
        'background:#F5A623;'
        'border:2px solid #0A0C10;'
        'box-shadow:0 0 8px rgba(245,166,35,0.5);'
        'cursor:grab;'
        '}'
        'input[type=range]::-webkit-slider-thumb:active{cursor:grabbing;}'
        'input[type=range]::-moz-range-thumb{'
        'width:20px;height:20px;'
        'border-radius:50%;'
        'background:#F5A623;'
        'border:2px solid #0A0C10;'
        'cursor:grab;'
        '}'
        '</style>'

        # ── JavaScript: komunikasi dengan Plotly chart
        '<script>'
        '(function(){'

        # State
        'var totalCandles = ' + str(total_candles) + ';'
        'var visibleCandles = 60;'  # default tampilkan 60 candle
        'var scrollPos = 100;'      # 100 = paling kanan (terbaru)

        # Helper: dapatkan Plotly div
        'function getPlotDiv(){'
        '  var divs = document.querySelectorAll(".js-plotly-plot");'
        '  return divs.length ? divs[0] : null;'
        '}'

        # Hitung range index dari scrollPos dan visibleCandles
        'function applyRange(){'
        '  var d = getPlotDiv(); if(!d) return;'
        '  var maxStart = totalCandles - visibleCandles;'
        '  var startIdx = Math.round((scrollPos / 100) * maxStart);'
        '  var endIdx = startIdx + visibleCandles;'
        '  if(endIdx > totalCandles){ endIdx = totalCandles; startIdx = endIdx - visibleCandles; }'
        '  if(startIdx < 0) startIdx = 0;'
        # Plotly xaxis range pakai index untuk category, atau date string
        '  try{'
        '    var xdata = d.data[0].x;'
        '    if(!xdata || xdata.length === 0) return;'
        '    var x0 = xdata[startIdx] || xdata[0];'
        '    var x1 = xdata[Math.min(endIdx, xdata.length-1)];'
        '    Plotly.relayout(d, {"xaxis.range": [x0, x1], "xaxis2.range": [x0, x1]});'
        '    var lbl = document.getElementById("chart-pos-label");'
        '    if(lbl) lbl.innerText = "Candle " + (startIdx+1) + " – " + endIdx + " dari " + totalCandles;'
        '  } catch(e){}'
        '}'

        # Update slider gradient fill
        'function updateSliderFill(val){'
        '  var sl = document.getElementById("chart-hscroll");'
        '  if(sl) sl.style.setProperty("--val", val + "%");'
        '}'

        # Fungsi publik
        'window.chartScroll = function(val){'
        '  scrollPos = parseFloat(val);'
        '  updateSliderFill(scrollPos);'
        '  applyRange();'
        '};'

        'window.chartZoom = function(n){'
        '  if(n === 0){ visibleCandles = totalCandles; scrollPos = 0; }'
        '  else { visibleCandles = Math.min(n, totalCandles); }'
        '  var sl = document.getElementById("chart-hscroll");'
        '  if(sl){ sl.value = scrollPos; updateSliderFill(scrollPos); }'
        '  applyRange();'
        '};'

        'window.chartZoomIn = function(){'
        '  visibleCandles = Math.max(10, Math.round(visibleCandles * 0.6));'
        '  applyRange();'
        '};'

        'window.chartZoomOut = function(){'
        '  visibleCandles = Math.min(totalCandles, Math.round(visibleCandles * 1.6));'
        '  applyRange();'
        '};'

        'window.chartGoToday = function(){'
        '  scrollPos = 100;'
        '  var sl = document.getElementById("chart-hscroll");'
        '  if(sl){ sl.value = 100; updateSliderFill(100); }'
        '  applyRange();'
        '};'

        # Init setelah Plotly render
        'function initNav(){'
        '  var d = getPlotDiv();'
        '  if(!d || !d.data || !d.data[0]){'
        '    setTimeout(initNav, 300); return;'
        '  }'
        '  updateSliderFill(100);'
        '  chartZoom(60);'   # default 60 candle saat load
        '}'
        'setTimeout(initNav, 800);'

        '})();'
        '</script>',
        unsafe_allow_html=True
    )
else:
    st.warning("⚠️ Chart data unavailable. Check your connection and refresh.")

# ─────────────────────────────────────────────
#  ROW 3: RISK MANAGER  +  LOT CALCULATOR
# ─────────────────────────────────────────────
st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
st.markdown('<div class="section-header">Risk Manager & Stop Loss</div>', unsafe_allow_html=True)

col_rm, col_lc = st.columns([3, 2], gap="large")

with col_rm:
    # Stop Loss explainer
    st.markdown(
        '<div class="sl-explainer">'
        '<strong>Apa itu Stop Loss (SL)?</strong><br>'
        'Stop Loss adalah batas harga maksimum kerugian yang Anda siapkan <em>sebelum</em> masuk posisi. '
        'Jika harga mencapai level SL, posisi otomatis ditutup untuk mencegah kerugian lebih besar.<br><br>'
        '<strong>Cara baca di bawah:</strong> '
        'SL dihitung dari ATR (Average True Range) — yaitu rata-rata pergerakan harian emas. '
        'Karena ATR Gold saat ini <strong>~$' + ("{:.0f}".format(atr) if atr > 0 else "—") + '/hari</strong>, '
        'SL dipasang di <strong>' + "{:.1f}x".format(SL_ATR_MULT) + ' ATR = $' + "{:.2f}".format(sl_distance) + '</strong> dari harga entry. '
        'Ini cukup jauh agar tidak kena "noise" pasar, tapi tetap melindungi modal.<br><br>'
        '<strong>Tip untuk Daily/Hit-and-Run:</strong> '
        'Masuk hanya ketika Signal BUKAN WAIT, confidence >60%, dan pastikan SL Anda tidak lebih besar dari 1–2% modal.'
        '</div>',
        unsafe_allow_html=True
    )

    # Risk table
    if signal == "BUY":
        sl_col = "risk-val-sell"
        tp_col = "risk-val-buy"
        entry_arrow = "↑"
    elif signal == "SELL":
        sl_col = "risk-val-sell"
        tp_col = "risk-val-buy"
        entry_arrow = "↓"
    else:
        sl_col = ""
        tp_col = ""
        entry_arrow = "—"

    st.markdown(
        '<div class="risk-card">'
        '<div class="risk-title">🎯 Risk/Reward untuk Signal: ' + signal + '</div>'
        '<div class="risk-row"><span class="risk-key">Entry Price</span><span class="risk-val">$' + "{:,.2f}".format(current_price) + ' ' + entry_arrow + '</span></div>'
        '<div class="risk-row"><span class="risk-key">Stop Loss (SL)</span><span class="risk-val ' + sl_col + '">$' + "{:,.2f}".format(sl_price) + ' &nbsp;|&nbsp; ' + "{:.2f}".format(sl_distance) + ' pips</span></div>'
        '<div class="risk-row"><span class="risk-key">Take Profit (TP)</span><span class="risk-val ' + tp_col + '">$' + "{:,.2f}".format(tp_price) + ' &nbsp;|&nbsp; ' + "{:.2f}".format(tp_distance) + ' pips</span></div>'
        '<div class="risk-row"><span class="risk-key">Risk/Reward Ratio</span><span class="risk-val ' + ("risk-val-buy" if rr_ratio >= 2 else "risk-val-warn") + '">1 : ' + "{:.2f}".format(rr_ratio) + '</span></div>'
        '<div class="risk-row"><span class="risk-key">ATR (basis SL)</span><span class="risk-val">$' + "{:.2f}".format(atr) + '/hari</span></div>'
        '<div class="risk-row"><span class="risk-key">SL Multiplier</span><span class="risk-val">' + "{:.1f}x".format(SL_ATR_MULT) + ' ATR</span></div>'
        '</div>',
        unsafe_allow_html=True
    )

with col_lc:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">💰 Lot Calculator</div>', unsafe_allow_html=True)

    capital = st.number_input(
        "Modal Akun (USD)",
        min_value=100.0, max_value=1000000.0,
        value=st.session_state.risk_capital,
        step=100.0,
        format="%.2f",
        key="capital_input",
    )
    st.session_state.risk_capital = capital

    risk_pct = st.slider(
        "Risk per Trade (%)",
        min_value=0.5, max_value=5.0,
        value=st.session_state.risk_pct,
        step=0.1,
        format="%.1f%%",
        key="risk_pct_input",
    )
    st.session_state.risk_pct = risk_pct

    # Recalculate
    risk_usd_calc = capital * risk_pct / 100
    max_lot_calc = risk_usd_calc / (sl_distance * 100) if sl_distance > 0 else 0.01
    max_lot_calc = max(0.01, round(max_lot_calc, 2))
    lot_risk_usd = max_lot_calc * sl_distance * 100

    st.markdown(
        '<div style="margin-top:16px;">'
        '<div class="risk-row"><span class="risk-key">Risk Amount</span><span class="risk-val">$' + "{:.2f}".format(risk_usd_calc) + '</span></div>'
        '<div class="risk-row"><span class="risk-key">SL Distance</span><span class="risk-val">$' + "{:.2f}".format(sl_distance) + ' (' + "{:.0f}".format(sl_distance) + ' pips)</span></div>'
        '<div class="risk-row"><span class="risk-key">Max Safe Lot</span><span class="risk-val risk-val-buy">' + "{:.2f}".format(max_lot_calc) + ' lot</span></div>'
        '<div class="risk-row"><span class="risk-key">Risk jika SL kena</span><span class="risk-val risk-val-sell">-$' + "{:.2f}".format(lot_risk_usd) + '</span></div>'
        '<div class="risk-row"><span class="risk-key">Potential Profit (TP)</span><span class="risk-val risk-val-buy">+$' + "{:.2f}".format(max_lot_calc * tp_distance * 100) + '</span></div>'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div style="margin-top:16px;padding:12px;background:rgba(0,0,0,0.3);border-radius:8px;">'
        '<div style="font-size:11px;color:var(--text-muted);line-height:1.6;">'
        '⚠️ <b style="color:var(--gold)">Catatan:</b> Kalkulasi berdasarkan 1 pip Gold = $1/lot standard. '
        'Sesuaikan dengan leverage dan jenis akun broker Anda.'
        '</div>'
        '</div>',
        unsafe_allow_html=True
    )
    st.markdown("</div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  ROW 4: USER MANUAL
# ─────────────────────────────────────────────
st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

with st.expander("📖 User Manual — Cara Membaca Dashboard Ini"):
    st.markdown("""
<div style="color:var(--text-secondary);line-height:1.8;font-size:13px;">

### 🏅 XAUUSD DSS — Panduan Pengguna

**DSS (Decision Support System)** ini dirancang untuk membantu trader Gold membuat keputusan lebih terstruktur berdasarkan analisis teknikal multi-indikator dan data makro fundamental.

---

#### 📊 Signal Engine
| Signal | Arti | Tindakan |
|--------|------|----------|
| **BUY** | Indikator menunjukkan momentum naik | Pertimbangkan posisi Long |
| **SELL** | Indikator menunjukkan momentum turun | Pertimbangkan posisi Short |
| **WAIT** | Sinyal belum jelas / kondisi sideways | Tunggu, jangan masuk |

**Confidence %** = seberapa kuat sinyal. Di bawah 60% = sinyal lemah, sebaiknya WAIT.

---

#### 🎯 Stop Loss & Take Profit
- **SL** dihitung dari **1.5x ATR** — makin tinggi ATR (volatilitas), makin jauh SL
- **TP** dihitung dari **2.5x ATR** — target profit selalu lebih besar dari risiko
- **R/R Ratio** idealnya minimal 1:2 — artinya potensi profit 2x lipat dari risiko

---

#### 💰 Lot Calculator
- Masukkan modal dan persentase risiko
- Sistem menghitung lot maksimum agar jika SL kena, kerugian tidak melebihi batas risiko Anda
- Untuk pemula: gunakan **0.5–1% risk per trade**

---

#### 📈 Chart
- **Candle hijau** = harga naik | **Candle merah** = harga turun
- **Band kuning** = Bollinger Band (StdDev 2x dari MA20) — harga sering kembali ke tengah band
- **Garis hijau putus (PDH)** = Previous Day High — resistance potensial
- **Garis merah putus (PDL)** = Previous Day Low — support potensial
- **Garis kuning solid** = harga live saat ini

---

#### 🔄 Refresh
- Harga otomatis update **setiap 15 detik** dari gold-api.com
- DSS analysis update **setiap 5 menit** (cached)
- Klik **Refresh Now** untuk paksa update semua data

</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  DISCLAIMER + COPYRIGHT
# ─────────────────────────────────────────────
st.markdown(
    '<div class="copyright-bar">'
    '⚠️ <b>DISCLAIMER:</b> Dashboard ini adalah Decision Support System — bukan rekomendasi investasi. '
    'Seluruh keputusan trading adalah tanggung jawab pengguna sepenuhnya.'
    '<br><br>'
    '© 2026 <b style="color:var(--gold)">JVD Studio</b> · XAUUSD Hybrid DSS · All Rights Reserved'
    '</div>',
    unsafe_allow_html=True
)

# ─────────────────────────────────────────────
#  AUTO-RERUN — JavaScript (non-blocking, 15 detik)
#  FAB di kanan bawah sudah handle countdown visual.
#  Di sini hanya inject setTimeout reload.
# ─────────────────────────────────────────────
if st.session_state.auto_refresh:
    st.markdown(
        '<script>'
        'setTimeout(function() { window.location.reload(true); }, 15000);'
        '</script>',
        unsafe_allow_html=True
    )
