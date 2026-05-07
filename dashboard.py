import streamlit as st
from streamlit_autorefresh import st_autorefresh
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
import requests
import pytz
from datetime import datetime

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
#  SESSION STATE
# ─────────────────────────────────────────────
for k, v in [("auto_refresh", True), ("risk_capital", 1000.0),
             ("risk_pct", 1.0), ("show_chart", False)]:
    if k not in st.session_state:
        st.session_state[k] = v

# ─────────────────────────────────────────────
#  AUTO-REFRESH — st_autorefresh (15 detik, benar-benar berfungsi)
# ─────────────────────────────────────────────
if st.session_state.auto_refresh:
    st_autorefresh(interval=15000, limit=None, key="ar15")

# Handle pause toggle dari FAB
qp = st.query_params
if "toggle_auto" in qp:
    st.session_state.auto_refresh = not st.session_state.auto_refresh
    st.query_params.clear()
    st.rerun()
if "show_chart" in qp:
    st.session_state.show_chart = not st.session_state.show_chart
    st.query_params.clear()
    st.rerun()

# ─────────────────────────────────────────────
#  CSS — full dark theme, white text, animasi
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;700&display=swap');

:root {
    --gold:#F5A623; --gold2:#FFD580; --glow:rgba(245,166,35,0.4);
    --buy:#00E676; --buy-bg:rgba(0,230,118,0.08); --buy-border:rgba(0,230,118,0.25);
    --sell:#FF1744; --sell-bg:rgba(255,23,68,0.08); --sell-border:rgba(255,23,68,0.25);
    --wait:#F5A623; --wait-bg:rgba(245,166,35,0.08); --wait-border:rgba(245,166,35,0.25);
    --bg:#07090E; --bg2:#0C0F17; --card:#111520; --card2:#161C28;
    --border:rgba(255,255,255,0.08);
    --txt:#FFFFFF; --txt2:#B0BAD0; --txt3:#5A6480;
    --r:12px;
}

/* === FULL APP DARK === */
html, body,
[data-testid="stApp"],
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
.main, .block-container,
section[data-testid="stSidebar"],
[data-testid="stVerticalBlock"],
[data-testid="stVerticalBlockBorderWrapper"],
[data-testid="stHorizontalBlock"] {
    background: var(--bg) !important;
    color: var(--txt) !important;
    font-family: 'Space Grotesk', sans-serif !important;
}

/* === SIDEBAR === */
[data-testid="stSidebar"] { background: #090C14 !important; border-right: 1px solid var(--border) !important; }
[data-testid="stSidebar"] * { color: var(--txt) !important; }

/* === HEADER === */
[data-testid="stHeader"] { background: rgba(7,9,14,0.98) !important; border-bottom: 1px solid var(--border) !important; backdrop-filter: blur(16px) !important; }
[data-testid="stToolbar"] { background: transparent !important; }
[data-testid="collapsedControl"] svg { fill: var(--gold) !important; }

/* === SEMUA TEKS PUTIH === */
p, span, div, label, h1, h2, h3, h4, h5,
[data-testid="stMarkdownContainer"] * {
    color: var(--txt) !important;
}

/* === INPUT & WIDGET === */
[data-testid="stNumberInput"] input,
[data-testid="stTextInput"] input,
div[data-baseweb="input"] input {
    background: var(--card2) !important;
    border-color: var(--border) !important;
    color: var(--txt) !important;
    border-radius: 8px !important;
    font-family: 'JetBrains Mono', monospace !important;
}
div[data-baseweb="select"] > div {
    background: var(--card2) !important;
    border-color: var(--border) !important;
    color: var(--txt) !important;
}

/* === SLIDER === */
[data-testid="stSlider"] [role="slider"] { background: var(--gold) !important; }
[data-testid="stSlider"] [data-testid="stSliderTrack"] > div { background: var(--gold) !important; }
[data-testid="stSlider"] label, [data-testid="stSlider"] p { color: var(--txt2) !important; }

/* === EXPANDER === */
[data-testid="stExpander"] { background: var(--card) !important; border: 1px solid var(--border) !important; border-radius: var(--r) !important; }
[data-testid="stExpander"] summary, [data-testid="stExpander"] summary p { color: var(--txt) !important; }
[data-testid="stExpander"] summary svg { fill: var(--txt2) !important; }

/* === BUTTONS === */
[data-testid="baseButton-secondary"] {
    background: var(--card2) !important; color: var(--txt) !important;
    border: 1px solid var(--border) !important; border-radius: 8px !important;
    font-family: 'Space Grotesk', sans-serif !important; font-weight: 600 !important;
    transition: all 0.2s !important;
}
[data-testid="baseButton-secondary"]:hover { border-color: var(--gold) !important; color: var(--gold) !important; }
[data-testid="baseButton-primary"] {
    background: linear-gradient(135deg, var(--gold), #E8941A) !important;
    color: #07090E !important; border: none !important; border-radius: 8px !important;
    font-family: 'Space Grotesk', sans-serif !important; font-weight: 700 !important;
}

/* === METRICS === */
[data-testid="stMetric"] { background: var(--card) !important; border: 1px solid var(--border) !important; border-radius: var(--r) !important; padding: 14px 16px !important; }
[data-testid="stMetricLabel"] { color: var(--txt3) !important; font-size: 10px !important; text-transform: uppercase !important; letter-spacing: 0.08em !important; }
[data-testid="stMetricLabel"] p { color: var(--txt3) !important; }
[data-testid="stMetricValue"] { color: var(--txt) !important; font-family: 'JetBrains Mono', monospace !important; }
[data-testid="stMetricValue"] div { color: var(--txt) !important; }

/* === INFO/WARNING === */
[data-testid="stAlert"] { background: var(--card) !important; border-color: var(--border) !important; color: var(--txt) !important; }
[data-testid="stAlert"] p { color: var(--txt) !important; }

hr { border-color: var(--border) !important; margin: 8px 0 !important; }
::-webkit-scrollbar { width: 3px; height: 3px; }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 2px; }

/* === CUSTOM COMPONENTS === */
.jvd-header {
    background: linear-gradient(135deg, var(--card), var(--card2));
    border: 1px solid var(--border);
    border-radius: var(--r); padding: 16px 22px; margin-bottom: 10px;
    position: relative; overflow: hidden;
}
.jvd-header::before {
    content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px;
    background: linear-gradient(90deg, transparent, var(--gold), transparent);
    animation: shimmer 3s infinite;
}
@keyframes shimmer {
    0% { background-position: -200% center; }
    100% { background-position: 200% center; }
}
.jvd-logo { font-size: 18px; font-weight: 700; color: var(--txt); }
.jvd-logo span { color: var(--gold); }
.price-display {
    font-family: 'JetBrains Mono', monospace;
    font-size: 34px; font-weight: 700; color: var(--gold);
    text-shadow: 0 0 24px var(--glow); letter-spacing: -0.02em; line-height: 1;
    animation: pricePulse 0.3s ease;
}
@keyframes pricePulse { 0% { opacity: 0.5; transform: scale(0.98); } 100% { opacity: 1; transform: scale(1); } }
.live-badge {
    display: inline-flex; align-items: center; gap: 5px;
    background: rgba(0,230,118,0.1); border: 1px solid rgba(0,230,118,0.3);
    border-radius: 20px; padding: 3px 10px; font-size: 10px; font-weight: 700; color: #00E676;
}
.live-dot { width: 6px; height: 6px; border-radius: 50%; background: #00E676; animation: blink 1.2s infinite; }
@keyframes blink { 0%,100%{opacity:1;} 50%{opacity:0.3;} }
.ts-label { font-size: 10px; color: var(--txt3); font-family: 'JetBrains Mono', monospace; margin-top: 3px; }

/* FAB pill */
.fab-wrap { position: fixed; top: 78px; left: 8px; z-index: 99999; display: flex; flex-direction: column; gap: 4px; }
.fab-pill { display: flex; align-items: center; background: rgba(7,9,14,0.97); border: 1px solid rgba(245,166,35,0.45); border-radius: 30px; backdrop-filter: blur(18px); box-shadow: 0 4px 20px rgba(0,0,0,0.6); overflow: hidden; }
.fab-r { display: flex; align-items: center; gap: 6px; background: linear-gradient(135deg,#F5A623,#E8941A); color: #07090E !important; border: none; border-radius: 30px 0 0 30px; padding: 9px 14px 9px 12px; font-family: 'Space Grotesk',sans-serif; font-size: 12px; font-weight: 700; cursor: pointer; white-space: nowrap; }
.fab-r:active { opacity: 0.8; }
.fab-div { width: 1px; height: 26px; background: rgba(245,166,35,0.2); }
.fab-p { display: flex; align-items: center; gap: 5px; background: transparent; color: #7A8398 !important; border: none; border-radius: 0 30px 30px 0; padding: 9px 12px 9px 10px; font-family: 'Space Grotesk',sans-serif; font-size: 11px; font-weight: 600; cursor: pointer; white-space: nowrap; }
.fab-p:hover { color: var(--gold) !important; }
.fab-chip { background: rgba(7,9,14,0.9); border: 1px solid rgba(255,255,255,0.06); border-radius: 16px; padding: 3px 9px; font-family: 'JetBrains Mono',monospace; font-size: 10px; color: var(--txt3); margin-left: 5px; }
@media(max-width:768px) { .fab-wrap{top:72px;left:5px;} .fab-r{font-size:11px;padding:8px 11px 8px 9px;} .fab-p{font-size:10px;padding:8px 10px;} }

/* Status bar */
.sbar { display:flex;align-items:center;gap:10px;flex-wrap:wrap;padding:6px 12px;background:var(--card);border:1px solid var(--border);border-radius:10px;margin-bottom:12px;font-size:10px;color:var(--txt3); }
.sbar b { color: var(--txt2); }
.sbar .son { color: #00E676; font-weight: 700; }
.sbar .soff { color: #FF1744; font-weight: 700; }

/* Section header */
.sh { font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.12em;color:var(--txt3);padding:5px 0 9px 0;border-bottom:1px solid var(--border);margin-bottom:12px;display:flex;align-items:center;gap:6px; }
.sh::before { content:'';width:3px;height:12px;background:var(--gold);border-radius:2px; }

/* Signal cards */
.sig-box { border-radius:var(--r); padding:16px; }
.sig-buy { background:var(--buy-bg); border:1px solid var(--buy-border); }
.sig-sell { background:var(--sell-bg); border:1px solid var(--sell-border); }
.sig-wait { background:var(--wait-bg); border:1px solid var(--wait-border); }
.sig-label { font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;color:var(--txt3);margin-bottom:4px; }
.sv-buy { font-size:42px;font-weight:700;color:var(--buy);line-height:1;text-shadow:0 0 24px rgba(0,230,118,0.4); animation:sigIn 0.4s ease; }
.sv-sell { font-size:42px;font-weight:700;color:var(--sell);line-height:1;text-shadow:0 0 24px rgba(255,23,68,0.4); animation:sigIn 0.4s ease; }
.sv-wait { font-size:42px;font-weight:700;color:var(--wait);line-height:1;text-shadow:0 0 24px rgba(245,166,35,0.4); animation:sigIn 0.4s ease; }
@keyframes sigIn { from{opacity:0;transform:translateY(4px);} to{opacity:1;transform:none;} }
.cbar-bg { height:5px;background:rgba(255,255,255,0.07);border-radius:3px;overflow:hidden;margin-top:9px; }

/* Snapshot cards */
.snap-grid { display:grid;grid-template-columns:repeat(2,1fr);gap:8px; }
.snap-item { background:var(--card2);border:1px solid var(--border);border-radius:10px;padding:12px 13px; }
.snap-lbl { font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;color:var(--txt3)!important;margin-bottom:3px; }
.snap-val { font-family:'JetBrains Mono',monospace;font-size:17px;font-weight:700;color:var(--txt)!important; }
.snap-sub { font-size:10px;color:var(--txt3)!important;margin-top:2px; }

/* Chart section */
.chart-toggle-btn { width:100%;padding:12px;background:var(--card);border:1px solid var(--border);border-radius:10px;color:var(--txt)!important;font-family:'Space Grotesk',sans-serif;font-size:13px;font-weight:700;cursor:pointer;text-align:center;transition:all 0.2s; }
.chart-toggle-btn:hover { border-color:var(--gold);color:var(--gold)!important; }
.chart-active { border-color:var(--gold)!important;color:var(--gold)!important;background:rgba(245,166,35,0.06)!important; }
.cnav { background:var(--card2);color:var(--txt2)!important;border:1px solid var(--border);border-radius:6px;padding:5px 10px;font-family:'Space Grotesk',sans-serif;font-size:10px;font-weight:600;cursor:pointer;transition:all 0.15s; }
.cnav:hover { background:var(--gold);color:#07090E!important;border-color:var(--gold); }
.cnav-t { background:rgba(245,166,35,0.1)!important;color:var(--gold)!important;border-color:rgba(245,166,35,0.3)!important; }
input[type=range].csl { width:100%;height:6px;appearance:none;-webkit-appearance:none;background:rgba(255,255,255,0.07);border-radius:3px;outline:none;cursor:pointer; }
input[type=range].csl::-webkit-slider-thumb { appearance:none;-webkit-appearance:none;width:18px;height:18px;border-radius:50%;background:#F5A623;border:2px solid #07090E;box-shadow:0 0 6px rgba(245,166,35,0.5);cursor:grab; }

/* Risk cards */
.rcard { background:var(--card);border:1px solid var(--border);border-radius:var(--r);padding:16px;margin-top:10px; }
.rrow { display:flex;justify-content:space-between;align-items:center;padding:8px 0;border-bottom:1px solid var(--border); }
.rrow:last-child { border-bottom:none; }
.rkey { font-size:12px;color:var(--txt2)!important; }
.rval { font-family:'JetBrains Mono',monospace;font-size:13px;font-weight:700;color:var(--txt)!important; }
.rval-b { color:var(--buy)!important; }
.rval-s { color:var(--sell)!important; }
.rval-w { color:#FFA500!important; }
.slexp { background:rgba(245,166,35,0.05);border:1px solid rgba(245,166,35,0.15);border-radius:10px;padding:13px;font-size:12px;color:var(--txt2)!important;line-height:1.7; }
.slexp strong { color:var(--gold)!important; }

/* Pills */
.mpill { display:inline-flex;align-items:center;gap:4px;border-radius:16px;padding:4px 9px;font-size:10px;font-weight:600; }
.pb { background:var(--buy-bg);border:1px solid var(--buy-border);color:var(--buy)!important; }
.ps { background:var(--sell-bg);border:1px solid var(--sell-border);color:var(--sell)!important; }
.pn { background:var(--wait-bg);border:1px solid var(--wait-border);color:var(--wait)!important; }

.cpbar { background:var(--card);border:1px solid var(--border);border-radius:10px;padding:12px 14px; }
.copyright-bar { text-align:center;font-size:10px;color:var(--txt3);padding:16px 0 6px 0;border-top:1px solid var(--border);margin-top:24px; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  FETCH LIVE PRICE
# ─────────────────────────────────────────────
def fetch_price():
    try:
        r = requests.get("https://api.gold-api.com/price/XAU", timeout=6)
        if r.status_code == 200:
            d = r.json()
            p = float(d.get("price", 0))
            if p > 1000:
                return p, float(d.get("ch", 0)), float(d.get("chp", 0))
    except Exception:
        pass
    try:
        t = yf.Ticker("GC=F")
        h = t.history(period="2d", interval="1m")
        if not h.empty:
            p = float(h["Close"].iloc[-1])
            p0 = float(h["Close"].iloc[0])
            if p > 1000:
                ch = p - p0
                return p, ch, (ch / p0 * 100 if p0 > 0 else 0)
    except Exception:
        pass
    return None, 0.0, 0.0

# ─────────────────────────────────────────────
#  LOAD HISTORICAL + COMPUTE ENGINE (cached 5 min)
# ─────────────────────────────────────────────
@st.cache_data(ttl=300, show_spinner=False)
def load_data():
    out = {}
    try:
        t = yf.Ticker("GC=F")
        h = t.history(period="2y", interval="1d")
        h = h[h["Close"] > 1000].copy()
        out["hist"] = h if not h.empty else pd.DataFrame()
    except Exception:
        out["hist"] = pd.DataFrame()

    hist = out.get("hist", pd.DataFrame())
    if hist.empty:
        out["sig"] = "WAIT"; out["conf"] = 50.0; out["atr"] = 0.0
        out["rsi"] = 50.0; out["regime"] = "NEUTRAL"; out["volatility"] = "NORMAL"
        out["weekly_open"] = 0.0; out["monthly_open"] = 0.0
        out["pdh"] = 0.0; out["pdl"] = 0.0
        return out

    c = hist["Close"]; h_ = hist["High"]; l_ = hist["Low"]

    # ATR 14
    tr = pd.concat([(h_-l_), (h_-c.shift(1)).abs(), (l_-c.shift(1)).abs()], axis=1).max(axis=1)
    atr = float(tr.rolling(14).mean().iloc[-1])

    # RSI 14
    delta = c.diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rsi = float(100 - (100 / (1 + gain / loss.replace(0, 0.0001))).iloc[-1])

    # EMAs
    ema8 = c.ewm(span=8).mean()
    ema20 = c.ewm(span=20).mean()
    ema50 = c.ewm(span=50).mean()

    # MACD
    macd = c.ewm(span=12).mean() - c.ewm(span=26).mean()
    macd_sig = macd.ewm(span=9).mean()
    macd_bull = float(macd.iloc[-1]) > float(macd_sig.iloc[-1])

    # Bollinger
    ma20 = c.rolling(20).mean()
    std20 = c.rolling(20).std()
    bb_upper = ma20 + 2 * std20
    bb_lower = ma20 - 2 * std20
    bb_pct = float((c.iloc[-1] - bb_lower.iloc[-1]) / (bb_upper.iloc[-1] - bb_lower.iloc[-1])) if (bb_upper.iloc[-1] - bb_lower.iloc[-1]) > 0 else 0.5

    # Score engine
    score = 0
    reasons = []

    if rsi > 60:
        score += 2; reasons.append("RSI bull")
    elif rsi > 50:
        score += 1; reasons.append("RSI mild bull")
    elif rsi < 40:
        score -= 2; reasons.append("RSI bear")
    elif rsi < 50:
        score -= 1; reasons.append("RSI mild bear")

    if float(ema8.iloc[-1]) > float(ema20.iloc[-1]) > float(ema50.iloc[-1]):
        score += 2; reasons.append("EMA bull stack")
    elif float(ema8.iloc[-1]) < float(ema20.iloc[-1]) < float(ema50.iloc[-1]):
        score -= 2; reasons.append("EMA bear stack")
    elif float(ema20.iloc[-1]) > float(ema50.iloc[-1]):
        score += 1; reasons.append("EMA20>50")
    else:
        score -= 1; reasons.append("EMA20<50")

    mom5 = float(c.iloc[-1] - c.iloc[-5]) if len(c) >= 5 else 0
    mom20 = float(c.iloc[-1] - c.iloc[-20]) if len(c) >= 20 else 0
    if mom5 > 0: score += 1; reasons.append("5D up")
    else: score -= 1; reasons.append("5D dn")
    if mom20 > 0: score += 1; reasons.append("20D up")
    else: score -= 1; reasons.append("20D dn")

    if macd_bull: score += 1; reasons.append("MACD bull")
    else: score -= 1; reasons.append("MACD bear")

    if bb_pct > 0.7: score += 1; reasons.append("BB high")
    elif bb_pct < 0.3: score -= 1; reasons.append("BB low")

    # Signal
    if score >= 3:
        sig = "BUY"
        conf = min(92.0, 60.0 + float(score) * 4.0)
    elif score <= -3:
        sig = "SELL"
        conf = min(92.0, 60.0 + float(abs(score)) * 4.0)
    elif score >= 1:
        sig = "BUY"
        conf = 50.0 + float(score) * 4.0
    elif score <= -1:
        sig = "SELL"
        conf = 50.0 + float(abs(score)) * 4.0
    else:
        sig = "WAIT"
        conf = 48.0

    # ATR regime
    atr_avg = float(tr.rolling(20).mean().mean())
    vol = "HIGH" if atr > atr_avg * 1.4 else ("LOW" if atr < atr_avg * 0.7 else "NORMAL")
    regime = "TRENDING" if abs(score) >= 3 else ("RANGING" if abs(score) <= 1 else "NEUTRAL")

    out["sig"] = sig
    out["conf"] = round(conf, 1)
    out["atr"] = round(atr, 2)
    out["rsi"] = round(rsi, 2)
    out["regime"] = regime
    out["volatility"] = vol
    out["weekly_open"] = round(float(c.iloc[-5]), 2) if len(c) >= 5 else round(float(c.iloc[0]), 2)
    out["monthly_open"] = round(float(c.iloc[-20]), 2) if len(c) >= 20 else round(float(c.iloc[0]), 2)
    out["pdh"] = round(float(h_.iloc[-2]), 2) if len(h_) >= 2 else 0.0
    out["pdl"] = round(float(l_.iloc[-2]), 2) if len(l_) >= 2 else 0.0
    out["ema20"] = ema20
    out["bb_upper"] = bb_upper
    out["bb_lower"] = bb_lower
    out["score"] = score
    out["reasons"] = reasons
    return out

# ─────────────────────────────────────────────
#  FETCH DATA
# ─────────────────────────────────────────────
live_price, price_change, price_change_pct = fetch_price()
data = load_data()
hist = data.get("hist", pd.DataFrame())

current_price = live_price if (live_price and live_price > 1000) else (
    float(hist["Close"].iloc[-1]) if not hist.empty else 4700.0)
price_change = price_change or 0.0
price_change_pct = price_change_pct or 0.0

signal = data["sig"]
confidence = data["conf"]
atr = data["atr"]
rsi = data["rsi"]
regime = data["regime"]
volatility = data["volatility"]
weekly_open = data["weekly_open"]
monthly_open = data["monthly_open"]
pdh = data["pdh"]
pdl = data["pdl"]
score = data.get("score", 0)
reasons = data.get("reasons", [])

# Risk calculations
SL_M = 1.5; TP_M = 2.5
sl_d = atr * SL_M if atr > 0 else 30.0
tp_d = atr * TP_M if atr > 0 else 50.0
sl_p = (current_price - sl_d) if signal != "SELL" else (current_price + sl_d)
tp_p = (current_price + tp_d) if signal != "SELL" else (current_price - tp_d)
rr = tp_d / sl_d if sl_d > 0 else 0.0

# ─────────────────────────────────────────────
#  HEADER
# ─────────────────────────────────────────────
wib = pytz.timezone("Asia/Jakarta")
ts = datetime.now(wib).strftime("%d %b %Y  %H:%M:%S WIB")
cs = "+" if price_change >= 0 else ""
cc = "#00E676" if price_change >= 0 else "#FF1744"

st.markdown(
    '<div class="jvd-header">'
    '<div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px;">'
    '<div>'
    '<div class="jvd-logo">XAU/USD <span>DSS</span>&nbsp;·&nbsp;JVD Studio</div>'
    '<div class="ts-label">⏱ ' + ts + '</div>'
    '</div>'
    '<div style="text-align:right">'
    '<div class="price-display">$' + "{:,.2f}".format(current_price) + '</div>'
    '<div style="display:flex;align-items:center;gap:8px;justify-content:flex-end;margin-top:4px;">'
    '<span style="font-family:JetBrains Mono,monospace;font-size:12px;color:' + cc + ';">'
    + cs + "{:+.2f}".format(price_change) + " (" + cs + "{:.2f}".format(price_change_pct) + "%)"
    '</span>'
    '<span class="live-badge"><span class="live-dot"></span>LIVE</span>'
    '</div>'
    '</div>'
    '</div>'
    '</div>',
    unsafe_allow_html=True
)

# ─────────────────────────────────────────────
#  FAB — top-left sticky
# ─────────────────────────────────────────────
ai = "⏸" if st.session_state.auto_refresh else "▶"
at = "Pause" if st.session_state.auto_refresh else "Resume"
ac = "#00E676" if st.session_state.auto_refresh else "#FF1744"
ct = "auto 15s" if st.session_state.auto_refresh else "paused"

st.markdown(
    '<div class="fab-wrap">'
    '<div class="fab-pill">'
    '<button class="fab-r" onclick="window.location.reload();">🔄 Refresh</button>'
    '<div class="fab-div"></div>'
    '<a href="?toggle_auto=1" style="text-decoration:none;">'
    '<div class="fab-p"><span style="color:' + ac + ';">' + ai + '</span> ' + at + '</div>'
    '</a>'
    '</div>'
    '<div class="fab-chip" id="fc">' + ct + '</div>'
    '</div>'
    '<script>(function(){'
    'if(!' + ('true' if st.session_state.auto_refresh else 'false') + ')return;'
    'var s=15,e=document.getElementById("fc");'
    'setInterval(function(){s--;if(s<=0)s=15;if(e)e.innerText=s+"s";},1000);'
    '})();</script>',
    unsafe_allow_html=True
)

# Status bar
a_s = "AUTO ON" if st.session_state.auto_refresh else "PAUSED"
a_c_cls = "son" if st.session_state.auto_refresh else "soff"
src = "gold-api.com" if live_price else "yfinance"
st.markdown(
    '<div class="sbar">'
    '<span>📊 <b>' + str(len(hist)) + ' rows</b></span>·'
    '<span>📡 <b>' + src + '</b></span>·'
    '<span>⏱ <b style="color:var(--gold)">15s</b></span>·'
    '<span>🧠 <b style="color:var(--gold)">5min</b></span>·'
    '<span class="' + a_c_cls + '">' + a_s + '</span>'
    '</div>',
    unsafe_allow_html=True
)

# ─────────────────────────────────────────────
#  ROW 1: SIGNAL GAUGE + SNAPSHOT
# ─────────────────────────────────────────────
col_g, col_s = st.columns([2, 3], gap="large")

with col_g:
    st.markdown('<div class="sh">Signal Engine</div>', unsafe_allow_html=True)

    if signal == "BUY":
        gc = "#00E676"; sc = "sig-buy"; vc = "sv-buy"
        bcc = "linear-gradient(90deg,#00E676,#00FFB3)"
        gsteps = [dict(range=[0,30],color="rgba(255,23,68,0.1)"),
                  dict(range=[30,60],color="rgba(245,166,35,0.06)"),
                  dict(range=[60,100],color="rgba(0,230,118,0.15)")]
    elif signal == "SELL":
        gc = "#FF1744"; sc = "sig-sell"; vc = "sv-sell"
        bcc = "linear-gradient(90deg,#FF1744,#FF6B6B)"
        gsteps = [dict(range=[0,30],color="rgba(0,230,118,0.1)"),
                  dict(range=[30,60],color="rgba(245,166,35,0.06)"),
                  dict(range=[60,100],color="rgba(255,23,68,0.15)")]
    else:
        gc = "#F5A623"; sc = "sig-wait"; vc = "sv-wait"
        bcc = "linear-gradient(90deg,#F5A623,#FFD580)"
        gsteps = [dict(range=[0,30],color="rgba(255,23,68,0.08)"),
                  dict(range=[30,70],color="rgba(245,166,35,0.1)"),
                  dict(range=[70,100],color="rgba(0,230,118,0.08)")]

    fig_g = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=confidence,
        delta=dict(reference=50, increasing=dict(color="#00E676"), decreasing=dict(color="#FF1744"),
                   font=dict(size=12)),
        number=dict(suffix="%", font=dict(size=30, color=gc, family="JetBrains Mono")),
        title=dict(text=signal + "<br><span style='font-size:11px;color:#5A6480;'>Confidence Score</span>",
                   font=dict(size=18, color=gc, family="Space Grotesk")),
        gauge=dict(
            axis=dict(range=[0,100], tickcolor="#3A4255",
                      tickfont=dict(size=9,color="#5A6480",family="JetBrains Mono"),
                      tickwidth=1, nticks=6),
            bar=dict(color=gc, thickness=0.22),
            bgcolor="rgba(0,0,0,0)", borderwidth=0,
            steps=gsteps,
            threshold=dict(line=dict(color=gc,width=3), thickness=0.85, value=confidence),
        ),
    ))
    fig_g.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=36,b=4,l=16,r=16), height=230,
        font=dict(family="Space Grotesk"),
    )
    st.plotly_chart(fig_g, use_container_width=True, config={"displayModeBar": False})

    st.markdown(
        '<div class="sig-box ' + sc + '">'
        '<div class="sig-label">Decision Signal</div>'
        '<div class="' + vc + '">' + signal + '</div>'
        '<div style="display:flex;justify-content:space-between;margin-top:8px;">'
        '<span style="font-size:11px;color:var(--txt3);">Confidence</span>'
        '<span style="font-family:JetBrains Mono,monospace;font-size:11px;color:var(--txt);">'
        + "{:.1f}".format(confidence) + '%</span>'
        '</div>'
        '<div class="cbar-bg"><div style="width:' + str(min(100, confidence)) + '%;height:100%;background:' + bcc + ';border-radius:3px;transition:width 0.5s ease;"></div></div>'
        '<div style="margin-top:8px;font-size:10px;color:var(--txt3);">'
        'Score: <b style="color:var(--txt);">' + ("+" if score >= 0 else "") + str(score) + '/8</b> &nbsp;·&nbsp; '
        + " · ".join(reasons[:3]) +
        '</div>'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    dxy_status = "—"
    try:
        from fundamental import get_fundamental_data
        fd = get_fundamental_data()
        dxy_status = fd.get("dxy_status", "—")
        fed_rate = float(fd.get("fed_rate", 0.0))
        macro_adj = fd.get("macro_adj", 0)
    except Exception:
        fed_rate = 0.0; macro_adj = 0

    fpc = "ps" if fed_rate > 4 else ("pb" if fed_rate < 3 else "pn")
    mpc = "pb" if macro_adj > 0 else ("ps" if macro_adj < 0 else "pn")
    st.markdown(
        '<div style="display:flex;flex-wrap:wrap;gap:5px;">'
        '<span class="mpill pn">DXY: ' + str(dxy_status) + '</span>'
        '<span class="mpill ' + fpc + '">Fed: ' + "{:.1f}".format(fed_rate) + '%</span>'
        '<span class="mpill ' + mpc + '">Adj: ' + ("+" if macro_adj >= 0 else "") + str(macro_adj) + '</span>'
        '</div>',
        unsafe_allow_html=True
    )

with col_s:
    st.markdown('<div class="sh">Market Snapshot</div>', unsafe_allow_html=True)
    rsi_lbl = "⚠ Overbought" if rsi > 70 else ("⚠ Oversold" if rsi < 30 else "Neutral")
    vs_w = current_price - weekly_open if weekly_open > 0 else 0
    vs_m = current_price - monthly_open if monthly_open > 0 else 0

    snap_items = [
        ("Gold Live", "$" + "{:,.2f}".format(current_price),
         ("+" if price_change >= 0 else "") + "{:.2f}".format(price_change) + " today"),
        ("ATR (14)", "${:.2f}".format(atr) if atr > 0 else "—", "Volatility daily"),
        ("RSI (14)", "{:.1f}".format(rsi), rsi_lbl),
        ("Regime", regime, "Market structure"),
        ("Volatility", volatility, "Risk environment"),
        ("Weekly Open", "$" + "{:,.2f}".format(weekly_open) if weekly_open > 0 else "—",
         ("+" if vs_w >= 0 else "") + "{:.2f}".format(vs_w)),
        ("Monthly Open", "$" + "{:,.2f}".format(monthly_open) if monthly_open > 0 else "—",
         ("+" if vs_m >= 0 else "") + "{:.2f}".format(vs_m)),
        ("Prev Day High", "$" + "{:,.2f}".format(pdh) if pdh > 0 else "—",
         "Dist: $" + "{:.2f}".format(abs(pdh - current_price)) if pdh > 0 else ""),
        ("Prev Day Low", "$" + "{:,.2f}".format(pdl) if pdl > 0 else "—",
         "Dist: $" + "{:.2f}".format(abs(current_price - pdl)) if pdl > 0 else ""),
    ]
    sh = '<div class="snap-grid">'
    for lb, vl, sb in snap_items:
        sh += (
            '<div class="snap-item">'
            '<div class="snap-lbl">' + lb + '</div>'
            '<div class="snap-val">' + vl + '</div>'
            '<div class="snap-sub">' + sb + '</div>'
            '</div>'
        )
    sh += '</div>'
    st.markdown(sh, unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  ROW 2: CHART
# ─────────────────────────────────────────────
st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
st.markdown('<div class="sh">Price Chart — XAUUSD (GC=F)</div>', unsafe_allow_html=True)

if not hist.empty:
    # Compute indicators
    ma20 = hist["Close"].rolling(20).mean()
    std20 = hist["Close"].rolling(20).std()
    bb_u = ma20 + 2 * std20
    bb_l = ma20 - 2 * std20
    ema20_s = hist["Close"].ewm(span=20).mean()

    # Build chart function
    def make_chart(h, cur, pdh_v, pdl_v, height=440):
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                            row_heights=[0.82, 0.18], vertical_spacing=0.015)

        # Candle — thin, clean
        fig.add_trace(go.Candlestick(
            x=h.index, open=h["Open"], high=h["High"], low=h["Low"], close=h["Close"],
            name="XAUUSD",
            increasing=dict(fillcolor="#00C97B", line=dict(color="#00C97B", width=1)),
            decreasing=dict(fillcolor="#FF3B5C", line=dict(color="#FF3B5C", width=1)),
            whiskerwidth=0.5,
        ), row=1, col=1)

        # EMA20
        fig.add_trace(go.Scatter(
            x=h.index, y=ema20_s, mode="lines", name="EMA20",
            line=dict(color="rgba(245,166,35,0.6)", width=1),
        ), row=1, col=1)

        # BB bands — very subtle
        fig.add_trace(go.Scatter(
            x=h.index, y=bb_u, mode="lines",
            line=dict(color="rgba(255,255,255,0.1)", width=0.6, dash="dot"),
            name="BB+", showlegend=False,
        ), row=1, col=1)
        fig.add_trace(go.Scatter(
            x=h.index, y=bb_l, mode="lines",
            line=dict(color="rgba(255,255,255,0.1)", width=0.6, dash="dot"),
            fill="tonexty", fillcolor="rgba(255,255,255,0.015)",
            name="BB-", showlegend=False,
        ), row=1, col=1)

        # Key levels
        if pdh_v > 0:
            fig.add_hline(y=pdh_v, line_dash="dash", line_color="rgba(0,230,118,0.5)",
                          line_width=0.8,
                          annotation_text="PDH", annotation_position="right",
                          annotation_font=dict(color="rgba(0,230,118,0.7)", size=9,
                                               family="JetBrains Mono"),
                          row=1, col=1)
        if pdl_v > 0:
            fig.add_hline(y=pdl_v, line_dash="dash", line_color="rgba(255,59,92,0.5)",
                          line_width=0.8,
                          annotation_text="PDL", annotation_position="right",
                          annotation_font=dict(color="rgba(255,59,92,0.7)", size=9,
                                               family="JetBrains Mono"),
                          row=1, col=1)
        # Live price
        fig.add_hline(y=cur, line_dash="solid",
                      line_color="rgba(245,166,35,0.9)", line_width=1.2,
                      annotation_text="$" + "{:,.2f}".format(cur),
                      annotation_position="right",
                      annotation_font=dict(color="#F5A623", size=10,
                                           family="JetBrains Mono"),
                      row=1, col=1)

        # Volume
        vc = ["rgba(0,201,123,0.4)" if float(cl) >= float(op) else "rgba(255,59,92,0.4)"
              for cl, op in zip(h["Close"], h["Open"])]
        fig.add_trace(go.Bar(
            x=h.index, y=h["Volume"], name="Vol",
            marker=dict(color=vc, line=dict(width=0)), showlegend=False,
        ), row=2, col=1)

        ax = dict(gridcolor="rgba(255,255,255,0.03)", linecolor="rgba(255,255,255,0.05)",
                  zerolinecolor="rgba(255,255,255,0.03)")

        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="#07090E",
            height=height,
            margin=dict(t=8, b=4, l=4, r=80),
            xaxis_rangeslider_visible=False,
            legend=dict(orientation="h", yanchor="bottom", y=1.002, xanchor="left", x=0,
                        bgcolor="rgba(0,0,0,0)",
                        font=dict(color="#5A6480", size=9, family="Space Grotesk")),
            font=dict(family="Space Grotesk", color="#5A6480"),
            xaxis=dict(**ax, tickfont=dict(color="#5A6480", size=8, family="JetBrains Mono"),
                       showgrid=True),
            yaxis=dict(**ax, tickfont=dict(color="#5A6480", size=8, family="JetBrains Mono"),
                       tickprefix="$", showgrid=True, side="right",
                       fixedrange=False, autorange=True),
            xaxis2=dict(**ax, tickfont=dict(color="#5A6480", size=7), showticklabels=False),
            yaxis2=dict(**ax, tickfont=dict(color="#5A6480", size=7), side="right",
                        fixedrange=True),
            dragmode="pan",
            hovermode="x unified",
            hoverlabel=dict(bgcolor="#12161F", bordercolor="#F5A623",
                            font=dict(color="#FFFFFF", size=10, family="JetBrains Mono")),
            modebar=dict(bgcolor="rgba(0,0,0,0)", color="#5A6480",
                         activecolor="#F5A623"),
        )

        fig.update_xaxes(
            rangeselector=dict(
                buttons=[
                    dict(count=5, label="5D", step="day", stepmode="backward"),
                    dict(count=1, label="1M", step="month", stepmode="backward"),
                    dict(count=3, label="3M", step="month", stepmode="backward"),
                    dict(count=6, label="6M", step="month", stepmode="backward"),
                    dict(step="all", label="MAX"),
                ],
                bgcolor="#111520", activecolor="#F5A623",
                bordercolor="rgba(255,255,255,0.07)", borderwidth=1,
                font=dict(color="#B0BAD0", size=10, family="Space Grotesk"),
                x=0, y=1.0,
            ),
            row=1, col=1,
        )
        return fig

    # Normal chart — selalu tampil
    fig_n = make_chart(hist, current_price, pdh, pdl, height=420)
    st.plotly_chart(fig_n, use_container_width=True, config={
        "displayModeBar": True,
        "modeBarButtonsToRemove": ["toImage", "sendDataToCloud", "select2d", "lasso2d", "autoScale2d"],
        "displaylogo": False,
        "scrollZoom": True,
        "responsive": True,
        "modeBarButtonsToAdd": [],
    })

    # Nav bar bawah chart
    tc = len(hist)
    st.markdown(
        '<div class="cpbar" style="margin-top:-2px;">'
        '<div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:6px;margin-bottom:9px;">'
        '<span style="font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;color:var(--txt3);">🕹 Timeline</span>'
        '<div style="display:flex;gap:4px;flex-wrap:wrap;">'
        '<button class="cnav" onclick="cZ(5)">5D</button>'
        '<button class="cnav" onclick="cZ(20)">1M</button>'
        '<button class="cnav" onclick="cZ(60)">3M</button>'
        '<button class="cnav" onclick="cZ(120)">6M</button>'
        '<button class="cnav" onclick="cZ(0)">MAX</button>'
        '<button class="cnav cnav-t" onclick="cH()">🏠 Home</button>'
        '</div>'
        '</div>'
        '<div style="display:flex;align-items:center;gap:8px;">'
        '<span style="font-size:9px;color:var(--txt3);">◀</span>'
        '<input type="range" class="csl" id="csl" min="0" max="100" value="100" step="1" oninput="cS(this.value)">'
        '<span style="font-size:9px;color:var(--txt3);">▶</span>'
        '</div>'
        '<div style="display:flex;align-items:center;justify-content:space-between;margin-top:8px;flex-wrap:wrap;gap:4px;">'
        '<div style="display:flex;gap:4px;">'
        '<button class="cnav" onclick="cZI()">🔍＋</button>'
        '<button class="cnav" onclick="cZO()">🔍－</button>'
        '</div>'
        '<span id="cpos" style="font-family:JetBrains Mono,monospace;font-size:9px;color:var(--txt3);">← geser · scroll/pinch zoom · drag pan →</span>'
        '</div>'
        '</div>'
        '<script>(function(){'
        'var T=' + str(tc) + ',V=60,P=100;'
        'function gd(){var d=document.querySelectorAll(".js-plotly-plot");return d.length?d[0]:null;}'
        'function ar(){'
        '  var d=gd();if(!d)return;'
        '  var ms=Math.max(0,T-V),si=Math.round(P/100*ms),ei=si+V;'
        '  if(ei>T){ei=T;si=Math.max(0,ei-V);}'
        '  try{'
        '    var x=d.data[0].x;if(!x||!x.length)return;'
        '    var x0=x[si]||x[0],x1=x[Math.min(ei,x.length-1)];'
        '    Plotly.relayout(d,{"xaxis.range":[x0,x1]});'
        '    var lb=document.getElementById("cpos");'
        '    if(lb)lb.innerText="C"+(si+1)+"-"+ei+"/"+T;'
        '    var sl=document.getElementById("csl");'
        '    if(sl)sl.style.background="linear-gradient(to right,#F5A623 "+P+"%,rgba(255,255,255,0.07) "+P+"%)";'
        '  }catch(e){}'
        '}'
        'window.cS=function(v){P=parseFloat(v);ar();};'
        'window.cZ=function(n){if(n===0){V=T;P=0;}else{V=Math.min(n,T);P=100;}ar();};'
        'window.cZI=function(){V=Math.max(5,Math.round(V*0.6));ar();};'
        'window.cZO=function(){V=Math.min(T,Math.round(V*1.6));ar();};'
        'window.cH=function(){'
        '  V=60;P=100;'
        '  var sl=document.getElementById("csl");if(sl)sl.value=100;'
        '  var d=gd();if(!d)return;'
        '  try{Plotly.relayout(d,{"xaxis.autorange":true,"yaxis.autorange":true});}catch(e){}'
        '  ar();'
        '};'
        'function ini(){var d=gd();if(!d||!d.data||!d.data[0]){setTimeout(ini,400);return;}ar();}'
        'setTimeout(ini,800);'
        '})();</script>',
        unsafe_allow_html=True
    )
    st.markdown(
        '<div style="text-align:center;padding:4px 0;font-size:10px;color:var(--txt3);">'
        '💡 Scroll/pinch = zoom in-out &nbsp;·&nbsp; Drag chart = geser &nbsp;·&nbsp; 🏠 Home = reset tampilan'
        '</div>',
        unsafe_allow_html=True
    )

else:
    st.warning("⚠️ Data chart tidak tersedia.")

# ─────────────────────────────────────────────
#  ROW 3: RISK MANAGER
# ─────────────────────────────────────────────
st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
st.markdown('<div class="sh">Risk Manager & Stop Loss</div>', unsafe_allow_html=True)
r1, r2 = st.columns([3, 2], gap="large")

with r1:
    st.markdown(
        '<div class="slexp">'
        '<strong>Stop Loss (SL)</strong> = batas harga kerugian max sebelum masuk posisi. '
        'Jika harga menyentuh SL, posisi otomatis ditutup.<br><br>'
        '<strong>Formula:</strong> SL = ' + "{:.1f}x".format(SL_M) + ' ATR ($' + "{:.2f}".format(atr) + ') = '
        '<b>$' + "{:.2f}".format(sl_d) + ' dari entry</b><br>'
        '<strong>TP</strong> = ' + "{:.1f}x".format(TP_M) + ' ATR = '
        '<b>$' + "{:.2f}".format(tp_d) + ' target profit</b><br><br>'
        '<strong>Hit-and-Run tip:</strong> Entry hanya saat signal BUY/SELL + confidence >60% + R/R ≥ 1:2'
        '</div>',
        unsafe_allow_html=True
    )
    arr = "↑ LONG" if signal == "BUY" else ("↓ SHORT" if signal == "SELL" else "— WAIT")
    st.markdown(
        '<div class="rcard">'
        '<div style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;color:var(--gold);margin-bottom:12px;">🎯 Risk/Reward — ' + signal + '</div>'
        '<div class="rrow"><span class="rkey">Entry Price</span><span class="rval">$' + "{:,.2f}".format(current_price) + ' ' + arr + '</span></div>'
        '<div class="rrow"><span class="rkey">Stop Loss</span><span class="rval rval-s">$' + "{:,.2f}".format(sl_p) + ' (-$' + "{:.2f}".format(sl_d) + ')</span></div>'
        '<div class="rrow"><span class="rkey">Take Profit</span><span class="rval rval-b">$' + "{:,.2f}".format(tp_p) + ' (+$' + "{:.2f}".format(tp_d) + ')</span></div>'
        '<div class="rrow"><span class="rkey">Risk/Reward</span><span class="rval ' + ("rval-b" if rr >= 2 else "rval-w") + '">1 : ' + "{:.2f}".format(rr) + '</span></div>'
        '<div class="rrow"><span class="rkey">ATR basis</span><span class="rval">$' + "{:.2f}".format(atr) + '/hari</span></div>'
        '</div>',
        unsafe_allow_html=True
    )

with r2:
    st.markdown('<div style="background:var(--card);border:1px solid var(--border);border-radius:var(--r);padding:16px;">', unsafe_allow_html=True)
    st.markdown('<div style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;color:var(--txt3);margin-bottom:12px;">💰 Lot Calculator</div>', unsafe_allow_html=True)
    cap = st.number_input("Modal Akun (USD)", min_value=100.0, max_value=1000000.0,
                          value=st.session_state.risk_capital, step=100.0, format="%.2f", key="cap")
    st.session_state.risk_capital = cap
    rpv = st.slider("Risk per Trade (%)", 0.5, 5.0, st.session_state.risk_pct, 0.1, format="%.1f%%", key="rpv")
    st.session_state.risk_pct = rpv
    r_usd = cap * rpv / 100
    mx = max(0.01, round(r_usd / (sl_d * 100), 2)) if sl_d > 0 else 0.01
    st.markdown(
        '<div class="rrow"><span class="rkey">Risk Amount</span><span class="rval">$' + "{:.2f}".format(r_usd) + '</span></div>'
        '<div class="rrow"><span class="rkey">SL Distance</span><span class="rval">$' + "{:.2f}".format(sl_d) + '</span></div>'
        '<div class="rrow"><span class="rkey">Max Lot Aman</span><span class="rval rval-b">' + "{:.2f}".format(mx) + ' lot</span></div>'
        '<div class="rrow"><span class="rkey">Maks Rugi</span><span class="rval rval-s">-$' + "{:.2f}".format(mx * sl_d * 100) + '</span></div>'
        '<div class="rrow" style="border:none;"><span class="rkey">Potensi Profit</span><span class="rval rval-b">+$' + "{:.2f}".format(mx * tp_d * 100) + '</span></div>',
        unsafe_allow_html=True
    )
    st.markdown('</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  USER MANUAL
# ─────────────────────────────────────────────
st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
with st.expander("📖 User Manual — Cara Membaca Dashboard"):
    st.markdown("""
<div style="color:#B0BAD0;line-height:1.8;font-size:13px;">

### 🏅 XAUUSD DSS — Panduan Pengguna JVD Studio

---
#### 🔄 Auto-Refresh & Tombol Refresh
- Harga diambil dari **gold-api.com** (gratis, realtime)
- **Otomatis update setiap 15 detik** — tidak perlu klik apapun
- Tombol **🔄 Refresh** kiri atas = paksa update sekarang
- Tombol **⏸ Pause / ▶ Resume** = kontrol auto-refresh
- Chip "14s...13s..." = countdown sebelum update berikutnya

#### 📊 Signal Engine (Speedometer)
Signal dihitung dari **6 indikator**: RSI, EMA stack (8/20/50), MACD, momentum 5D+20D, Bollinger Band
| Signal | Score | Arti |
|--------|-------|------|
| **BUY** | ≥+3 | Mayoritas indikator bullish |
| **SELL** | ≤-3 | Mayoritas indikator bearish |
| **WAIT** | -2 to +2 | Sinyal terbagi/tidak jelas |

Score ditampilkan di bawah bar confidence misal **+4/8** = 4 dari 8 sinyal bullish.

#### 🎯 Stop Loss & Take Profit
- **SL = 1.5× ATR** — jarak aman dari entry
- **TP = 2.5× ATR** — target profit
- **R/R ideal ≥ 1:2** (hijau), perlu perhatian jika < 1:2 (oranye)

#### 📈 Chart
- **Scroll/pinch** = zoom in-out langsung di chart
- **Drag chart** = geser kiri-kanan
- **Slider bawah** = navigasi timeline
- **5D/1M/3M/6M/MAX** = preset zoom
- **🏠 Home** = reset ke tampilan default 60 candle terakhir

#### 💰 Lot Calculator
- Masukkan modal dan % risiko per trade
- Sistem hitung lot maksimum agar rugi tidak melebihi batas
- Rekomendasi: **0.5–1% untuk pemula**

</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  COPYRIGHT
# ─────────────────────────────────────────────
st.markdown(
    '<div class="copyright-bar">'
    '⚠️ <b>DISCLAIMER:</b> DSS ini bukan rekomendasi investasi. '
    'Keputusan trading sepenuhnya tanggung jawab pengguna.'
    '<br>© 2026 <b style="color:var(--gold);">JVD Studio</b> · XAUUSD Hybrid DSS · All Rights Reserved'
    '</div>',
    unsafe_allow_html=True
)
