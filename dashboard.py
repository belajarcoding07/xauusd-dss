import streamlit as st
from streamlit_autorefresh import st_autorefresh
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
import requests
import time
import pytz
from datetime import datetime

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
#  SESSION STATE
# ─────────────────────────────────────────────
def ss(k, v):
    if k not in st.session_state:
        st.session_state[k] = v

ss("auto_refresh", True)
ss("risk_capital", 1000.0)
ss("risk_pct", 1.0)
ss("chart_fullscreen", False)

# ─────────────────────────────────────────────
#  AUTO-REFRESH — st_autorefresh (benar-benar berfungsi)
#  Ini yang membuat harga, gauge, dan semua data benar-benar update
#  otomatis setiap 15 detik tanpa perlu klik apapun.
# ─────────────────────────────────────────────
if st.session_state.auto_refresh:
    st_autorefresh(interval=15000, limit=None, key="live_autorefresh")

# Handle toggle_auto dari FAB pause button
qp = st.query_params
if "toggle_auto" in qp:
    st.session_state.auto_refresh = not st.session_state.auto_refresh
    st.query_params.clear()
    st.rerun()

# ─────────────────────────────────────────────
#  GLOBAL CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;700&display=swap');
:root {
    --gold:#F5A623;--gold-light:#FFD580;--gold-glow:rgba(245,166,35,0.35);
    --buy:#00C97B;--buy-bg:rgba(0,201,123,0.1);
    --sell:#FF3B5C;--sell-bg:rgba(255,59,92,0.1);
    --wait:#F5A623;--wait-bg:rgba(245,166,35,0.1);
    --bg-primary:#080A0F;--bg-secondary:#0D0F15;
    --bg-card:#12161F;--bg-card2:#181D28;
    --border:rgba(255,255,255,0.07);
    --text-primary:#EEF0F5;--text-secondary:#7A8398;
    --text-muted:#3E4659;--radius:14px;
}
html,body,[data-testid="stAppViewContainer"],[data-testid="stApp"],
.main,.block-container,[data-testid="stVerticalBlock"] {
    background-color:var(--bg-primary)!important;
    color:var(--text-primary)!important;
    font-family:'Space Grotesk',sans-serif!important;
}
[data-testid="stSidebar"],[data-testid="stSidebar"]>div,[data-testid="stSidebarContent"] {
    background-color:#0A0C12!important;
    border-right:1px solid var(--border)!important;
}
[data-testid="stSidebar"] * { color:var(--text-primary)!important; }
[data-testid="stHeader"],header[data-testid="stHeader"] {
    background-color:rgba(8,10,15,0.97)!important;
    backdrop-filter:blur(12px)!important;
    border-bottom:1px solid var(--border)!important;
}
[data-testid="stToolbar"]{background:transparent!important;}
div[data-baseweb="select"]>div,[data-testid="stNumberInput"] input {
    background-color:var(--bg-card2)!important;
    border-color:var(--border)!important;
    color:var(--text-primary)!important;border-radius:8px!important;
}
[data-testid="stSlider"] [role="slider"]{background-color:var(--gold)!important;}
[data-testid="stExpander"]{background:var(--bg-card)!important;border:1px solid var(--border)!important;border-radius:var(--radius)!important;}
[data-testid="stExpander"] summary{color:var(--text-primary)!important;}
[data-testid="baseButton-secondary"]{background:var(--bg-card2)!important;color:var(--text-primary)!important;border:1px solid var(--border)!important;border-radius:8px!important;font-family:'Space Grotesk',sans-serif!important;font-weight:600!important;}
[data-testid="baseButton-primary"]{background:linear-gradient(135deg,var(--gold),#E8941A)!important;color:#080A0F!important;border-color:var(--gold)!important;font-family:'Space Grotesk',sans-serif!important;font-weight:700!important;}
[data-testid="stMetric"]{background:var(--bg-card)!important;border:1px solid var(--border)!important;border-radius:var(--radius)!important;padding:14px 18px!important;}
[data-testid="stMetricLabel"]{color:var(--text-secondary)!important;font-size:10px!important;text-transform:uppercase!important;letter-spacing:0.08em!important;}
[data-testid="stMetricValue"]{color:var(--text-primary)!important;font-family:'JetBrains Mono',monospace!important;}
hr{border-color:var(--border)!important;}
::-webkit-scrollbar{width:4px;height:4px;}
::-webkit-scrollbar-track{background:var(--bg-primary);}
::-webkit-scrollbar-thumb{background:var(--border);border-radius:2px;}
.jvd-header{background:linear-gradient(135deg,var(--bg-card) 0%,var(--bg-card2) 100%);border:1px solid var(--border);border-radius:var(--radius);padding:18px 24px;margin-bottom:12px;position:relative;overflow:hidden;}
.jvd-header::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,transparent,var(--gold),transparent);}
.jvd-logo{font-size:20px;font-weight:700;letter-spacing:-0.02em;color:var(--text-primary);}
.jvd-logo span{color:var(--gold);}
.live-price-big{font-family:'JetBrains Mono',monospace;font-size:36px;font-weight:700;color:var(--gold);text-shadow:0 0 30px var(--gold-glow),0 0 60px rgba(245,166,35,0.12);letter-spacing:-0.02em;line-height:1;}
.live-badge{display:inline-flex;align-items:center;gap:6px;background:rgba(0,201,123,0.1);border:1px solid rgba(0,201,123,0.3);border-radius:20px;padding:4px 12px;font-size:10px;font-weight:700;color:#00C97B;letter-spacing:0.05em;}
.live-dot{width:6px;height:6px;border-radius:50%;background:#00C97B;animation:pulse 1.5s infinite;}
@keyframes pulse{0%,100%{opacity:1;box-shadow:0 0 0 0 rgba(0,201,123,0.5);}50%{opacity:0.6;box-shadow:0 0 0 5px rgba(0,201,123,0);}}
.timestamp-label{font-size:11px;color:var(--text-muted);font-family:'JetBrains Mono',monospace;margin-top:4px;}
.jvd-fab-wrap{position:fixed;top:80px;left:10px;z-index:99999;display:flex;flex-direction:column;align-items:flex-start;gap:5px;}
.jvd-fab-pill{display:flex;align-items:center;background:rgba(8,10,15,0.97);border:1px solid rgba(245,166,35,0.4);border-radius:40px;backdrop-filter:blur(16px);box-shadow:0 4px 20px rgba(0,0,0,0.5);overflow:hidden;}
.jvd-fab-r{display:flex;align-items:center;gap:7px;background:linear-gradient(135deg,#F5A623,#E8941A);color:#080A0F!important;border:none;border-radius:40px 0 0 40px;padding:10px 15px 10px 13px;font-family:'Space Grotesk',sans-serif;font-size:12px;font-weight:700;cursor:pointer;transition:all 0.2s;white-space:nowrap;}
.jvd-fab-r:hover{background:linear-gradient(135deg,#FFB940,#F5A623);}
.jvd-fab-r:active{opacity:0.85;}
.jvd-fab-sep{width:1px;height:28px;background:rgba(245,166,35,0.2);}
.jvd-fab-p{display:flex;align-items:center;gap:5px;background:transparent;color:#7A8398!important;border:none;border-radius:0 40px 40px 0;padding:10px 13px 10px 11px;font-family:'Space Grotesk',sans-serif;font-size:11px;font-weight:600;cursor:pointer;transition:all 0.2s;white-space:nowrap;}
.jvd-fab-p:hover{color:#F5A623!important;background:rgba(245,166,35,0.07);}
.jvd-chip{background:rgba(8,10,15,0.88);border:1px solid rgba(255,255,255,0.05);border-radius:20px;padding:3px 10px;font-family:'JetBrains Mono',monospace;font-size:10px;color:#3E4659;backdrop-filter:blur(10px);margin-left:6px;}
.fab-spin{animation:fabspin 0.7s linear infinite;}
@keyframes fabspin{from{transform:rotate(0deg);}to{transform:rotate(360deg);}}
@media(max-width:768px){.jvd-fab-wrap{top:74px;left:6px;}.jvd-fab-r{font-size:11px;padding:9px 12px 9px 10px;}.jvd-fab-p{font-size:10px;padding:9px 10px;}}
.card{background:var(--bg-card);border:1px solid var(--border);border-radius:var(--radius);padding:18px;}
.card-title{font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;color:var(--text-muted);margin-bottom:12px;}
.sh{font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.12em;color:var(--text-muted);padding:6px 0 10px 0;border-bottom:1px solid var(--border);margin-bottom:14px;display:flex;align-items:center;gap:7px;}
.sh::before{content:'';width:3px;height:13px;background:var(--gold);border-radius:2px;}
.sig-buy{background:var(--buy-bg);border:1px solid rgba(0,201,123,0.25);border-radius:var(--radius);padding:16px;}
.sig-sell{background:var(--sell-bg);border:1px solid rgba(255,59,92,0.25);border-radius:var(--radius);padding:16px;}
.sig-wait{background:var(--wait-bg);border:1px solid rgba(245,166,35,0.25);border-radius:var(--radius);padding:16px;}
.sv-buy{font-size:40px;font-weight:700;color:var(--buy);line-height:1;text-shadow:0 0 20px rgba(0,201,123,0.3);}
.sv-sell{font-size:40px;font-weight:700;color:var(--sell);line-height:1;text-shadow:0 0 20px rgba(255,59,92,0.3);}
.sv-wait{font-size:40px;font-weight:700;color:var(--wait);line-height:1;text-shadow:0 0 20px rgba(245,166,35,0.3);}
.cb{height:5px;background:rgba(255,255,255,0.07);border-radius:3px;overflow:hidden;margin-top:10px;}
.snap-row{display:flex;flex-wrap:wrap;gap:8px;}
.snap-item{flex:1 1 130px;background:var(--bg-card2);border:1px solid var(--border);border-radius:10px;padding:12px 14px;}
.snap-label{font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;color:var(--text-muted);margin-bottom:4px;}
.snap-value{font-family:'JetBrains Mono',monospace;font-size:16px;font-weight:700;color:var(--text-primary);}
.snap-sub{font-size:10px;color:var(--text-secondary);margin-top:2px;}
.rcard{background:var(--bg-card);border:1px solid var(--border);border-radius:var(--radius);padding:18px;margin-top:12px;}
.rtitle{font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;color:var(--gold);margin-bottom:14px;}
.rrow{display:flex;justify-content:space-between;align-items:center;padding:8px 0;border-bottom:1px solid var(--border);}
.rrow:last-child{border-bottom:none;}
.rkey{font-size:12px;color:var(--text-secondary);}
.rval{font-family:'JetBrains Mono',monospace;font-size:13px;font-weight:700;color:var(--text-primary);}
.rval-b{color:var(--buy);} .rval-s{color:var(--sell);} .rval-w{color:#FFA500;}
.slexp{background:rgba(245,166,35,0.05);border:1px solid rgba(245,166,35,0.15);border-radius:10px;padding:14px;font-size:12px;color:var(--text-secondary);line-height:1.7;}
.slexp strong{color:var(--gold);}
.mpill{display:inline-flex;align-items:center;gap:5px;border-radius:20px;padding:4px 10px;font-size:11px;font-weight:600;}
.pill-b{background:var(--buy-bg);border:1px solid rgba(0,201,123,0.25);color:var(--buy);}
.pill-s{background:var(--sell-bg);border:1px solid rgba(255,59,92,0.25);color:var(--sell);}
.pill-n{background:var(--wait-bg);border:1px solid rgba(245,166,35,0.25);color:var(--wait);}
.cpbar{background:var(--bg-card);border:1px solid var(--border);border-radius:10px;padding:12px 14px;margin-top:-2px;}
.cnav{background:var(--bg-card2);color:var(--text-secondary);border:1px solid var(--border);border-radius:6px;padding:5px 10px;font-family:'Space Grotesk',sans-serif;font-size:10px;font-weight:600;cursor:pointer;transition:all 0.15s;white-space:nowrap;}
.cnav:hover{background:var(--gold);color:#080A0F;border-color:var(--gold);}
.cnav-t{background:rgba(245,166,35,0.1);color:var(--gold);border-color:rgba(245,166,35,0.3);}
input[type=range].csl{width:100%;height:6px;appearance:none;-webkit-appearance:none;background:rgba(255,255,255,0.07);border-radius:3px;outline:none;cursor:pointer;}
input[type=range].csl::-webkit-slider-thumb{appearance:none;-webkit-appearance:none;width:18px;height:18px;border-radius:50%;background:#F5A623;border:2px solid #080A0F;box-shadow:0 0 6px rgba(245,166,35,0.5);cursor:grab;}
input[type=range].csl::-moz-range-thumb{width:18px;height:18px;border-radius:50%;background:#F5A623;border:2px solid #080A0F;cursor:grab;}
.cpbar-footer{text-align:center;padding:4px 0;font-size:10px;color:var(--text-muted);}
.copyright-bar{text-align:center;font-size:10px;color:var(--text-muted);padding:18px 0 6px 0;border-top:1px solid var(--border);margin-top:28px;}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  LIVE PRICE FETCH
# ─────────────────────────────────────────────
def fetch_live_price():
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
#  DSS DATA — cached 5 min
# ─────────────────────────────────────────────
@st.cache_data(ttl=300, show_spinner=False)
def load_dss():
    out = {}
    try:
        t = yf.Ticker("GC=F")
        h = t.history(period="2y", interval="1d")
        h = h[h["Close"] > 1000].copy()
        out["hist"] = h if not h.empty else pd.DataFrame()
    except Exception:
        out["hist"] = pd.DataFrame()
    if run_engine is not None and not out.get("hist", pd.DataFrame()).empty:
        try:
            out["engine"] = run_engine(out["hist"])
        except Exception:
            out["engine"] = {}
    else:
        out["engine"] = {}
    if get_fundamental_data is not None:
        try:
            out["fundamental"] = get_fundamental_data()
        except Exception:
            out["fundamental"] = {}
    else:
        out["fundamental"] = {}
    return out

# ─────────────────────────────────────────────
#  FETCH ALL DATA
# ─────────────────────────────────────────────
live_price, price_change, price_change_pct = fetch_live_price()
data = load_dss()
hist = data.get("hist", pd.DataFrame())
engine = data.get("engine", {})
fundamental = data.get("fundamental", {})

current_price = live_price if (live_price and live_price > 1000) else (
    float(hist["Close"].iloc[-1]) if not hist.empty else 4700.0)
price_change = price_change or 0.0
price_change_pct = price_change_pct or 0.0

signal = engine.get("signal", "WAIT")
confidence = float(engine.get("confidence", 55.0))
atr = float(engine.get("atr", 0.0))
rsi = float(engine.get("rsi", 50.0))
regime = engine.get("regime", "NEUTRAL")
volatility = engine.get("volatility", "NORMAL")
weekly_open = float(engine.get("weekly_open", current_price))
monthly_open = float(engine.get("monthly_open", current_price))
pdh = float(engine.get("pdh", current_price + 20))
pdl = float(engine.get("pdl", current_price - 20))

if not hist.empty and atr == 0.0:
    try:
        c = hist["Close"]; hh = hist["High"]; ll = hist["Low"]
        tr = pd.concat([(hh-ll), (hh-c.shift(1)).abs(), (ll-c.shift(1)).abs()], axis=1).max(axis=1)
        atr = float(tr.rolling(14).mean().iloc[-1])
        d2 = c.diff()
        g = d2.where(d2 > 0, 0).rolling(14).mean()
        ls = (-d2.where(d2 < 0, 0)).rolling(14).mean()
        rsi = float(100 - (100 / (1 + g / ls.replace(0, 0.0001))).iloc[-1])
        weekly_open = float(c.iloc[-5]) if len(c) >= 5 else float(c.iloc[0])
        monthly_open = float(c.iloc[-20]) if len(c) >= 20 else float(c.iloc[0])
        pdh = float(hist["High"].iloc[-2]) if len(hist) >= 2 else current_price + 20
        pdl = float(hist["Low"].iloc[-2]) if len(hist) >= 2 else current_price - 20
    except Exception:
        pass

dxy_status = fundamental.get("dxy_status", "—")
dxy_trend = fundamental.get("dxy_trend", "NEUTRAL")
fed_rate = float(fundamental.get("fed_rate", 0.0))
macro_adj = fundamental.get("macro_adj", 0)

SL_MULT = 1.5; TP_MULT = 2.5
sl_dist = atr * SL_MULT if atr > 0 else 30.0
tp_dist = atr * TP_MULT if atr > 0 else 50.0
sl_price = (current_price - sl_dist) if signal != "SELL" else (current_price + sl_dist)
tp_price = (current_price + tp_dist) if signal != "SELL" else (current_price - tp_dist)
rr = tp_dist / sl_dist if sl_dist > 0 else 0.0

# ─────────────────────────────────────────────
#  HEADER
# ─────────────────────────────────────────────
wib = pytz.timezone("Asia/Jakarta")
ts = datetime.now(wib).strftime("%d %b %Y  %H:%M:%S WIB")
cs = "+" if price_change >= 0 else ""
cc = "#00C97B" if price_change >= 0 else "#FF3B5C"

st.markdown(
    '<div class="jvd-header">'
    '<div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px;">'
    '<div>'
    '<div class="jvd-logo">XAU/USD <span>DSS</span> &nbsp;·&nbsp; JVD Studio</div>'
    '<div class="timestamp-label">⏱ ' + ts + '</div>'
    '</div>'
    '<div style="text-align:right">'
    '<div class="live-price-big">$' + "{:,.2f}".format(current_price) + '</div>'
    '<div style="display:flex;align-items:center;gap:8px;justify-content:flex-end;margin-top:5px;">'
    '<span style="font-family:JetBrains Mono,monospace;font-size:12px;color:' + cc + '">'
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
#  FAB — top-left, always visible
# ─────────────────────────────────────────────
a_icon = "⏸" if st.session_state.auto_refresh else "▶"
a_text = "Pause" if st.session_state.auto_refresh else "Resume"
a_col = "#00C97B" if st.session_state.auto_refresh else "#FF3B5C"
chip_txt = "auto 15s" if st.session_state.auto_refresh else "paused"

st.markdown(
    '<div class="jvd-fab-wrap">'
    '<div class="jvd-fab-pill">'
    '<button class="jvd-fab-r" onclick="window.location.reload();">'
    '<span class="fab-icon">🔄</span>Refresh'
    '</button>'
    '<div class="jvd-fab-sep"></div>'
    '<a href="?toggle_auto=1" style="text-decoration:none;">'
    '<div class="jvd-fab-p">'
    '<span style="color:' + a_col + ';font-size:12px;">' + a_icon + '</span>'
    + a_text +
    '</div>'
    '</a>'
    '</div>'
    '<div class="jvd-chip" id="jvd-chip">' + chip_txt + '</div>'
    '</div>'
    '<script>(function(){'
    'var on=' + ('true' if st.session_state.auto_refresh else 'false') + ';'
    'if(!on)return;'
    'var s=15,el=document.getElementById("jvd-chip");'
    'setInterval(function(){s--;if(s<=0)s=15;if(el)el.innerText=s+"s";},1000);'
    '})();</script>',
    unsafe_allow_html=True
)

# Status bar
rows_info = str(len(hist)) + " rows" if not hist.empty else "No data"
a_status = "AUTO ON" if st.session_state.auto_refresh else "PAUSED"
a_scolor = "#00C97B" if st.session_state.auto_refresh else "#FF3B5C"
src_lbl = "gold-api.com" if live_price else "yfinance"

st.markdown(
    '<div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;'
    'padding:7px 14px;background:var(--bg-card);border:1px solid var(--border);'
    'border-radius:10px;margin-bottom:14px;font-size:10px;color:var(--text-muted);">'
    '<span>📊 <b style="color:var(--text-secondary)">' + rows_info + '</b></span>·'
    '<span>📡 <b style="color:var(--text-secondary)">' + src_lbl + '</b></span>·'
    '<span>⏱ <b style="color:var(--gold)">15s auto</b></span>·'
    '<span>🧠 <b style="color:var(--gold)">5min DSS</b></span>·'
    '<span style="color:' + a_scolor + ';font-weight:700;">' + a_status + '</span>'
    '</div>',
    unsafe_allow_html=True
)

# ─────────────────────────────────────────────
#  ROW 1: SIGNAL GAUGE + MARKET SNAPSHOT
# ─────────────────────────────────────────────
cg, cs2 = st.columns([2, 3], gap="large")

with cg:
    st.markdown('<div class="sh">Signal Engine</div>', unsafe_allow_html=True)
    if signal == "BUY":
        gc="#00C97B"; sc="sig-buy"; vc="sv-buy"; bcc="linear-gradient(90deg,#00C97B,#00FFAB)"
        steps=[dict(range=[0,30],color="rgba(255,59,92,0.08)"),dict(range=[30,60],color="rgba(245,166,35,0.06)"),dict(range=[60,100],color="rgba(0,201,123,0.12)")]
    elif signal == "SELL":
        gc="#FF3B5C"; sc="sig-sell"; vc="sv-sell"; bcc="linear-gradient(90deg,#FF3B5C,#FF8FA3)"
        steps=[dict(range=[0,30],color="rgba(0,201,123,0.08)"),dict(range=[30,60],color="rgba(245,166,35,0.06)"),dict(range=[60,100],color="rgba(255,59,92,0.12)")]
    else:
        gc="#F5A623"; sc="sig-wait"; vc="sv-wait"; bcc="linear-gradient(90deg,#F5A623,#FFD580)"
        steps=[dict(range=[0,30],color="rgba(255,59,92,0.06)"),dict(range=[30,70],color="rgba(245,166,35,0.1)"),dict(range=[70,100],color="rgba(0,201,123,0.06)")]

    fg = go.Figure(go.Indicator(
        mode="gauge+number",
        value=confidence,
        number=dict(suffix="%", font=dict(size=32, color=gc, family="JetBrains Mono")),
        title=dict(text=signal+"<br><span style='font-size:11px;color:#3E4659'>Confidence</span>",
                   font=dict(size=19, color=gc, family="Space Grotesk")),
        gauge=dict(
            axis=dict(range=[0,100],tickcolor="#3E4659",tickfont=dict(size=9,color="#3E4659",family="JetBrains Mono"),tickwidth=1,nticks=6),
            bar=dict(color=gc, thickness=0.25),
            bgcolor="rgba(0,0,0,0)", borderwidth=0,
            steps=steps,
            threshold=dict(line=dict(color=gc,width=2.5),thickness=0.8,value=confidence),
        ),
    ))
    fg.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
                     margin=dict(t=34,b=4,l=16,r=16),height=230,font=dict(family="Space Grotesk"))
    st.plotly_chart(fg, use_container_width=True, config={"displayModeBar": False})

    st.markdown(
        '<div class="' + sc + '">'
        '<div style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;color:var(--text-secondary);margin-bottom:5px;">Decision</div>'
        '<div class="' + vc + '">' + signal + '</div>'
        '<div style="display:flex;justify-content:space-between;margin-top:9px;">'
        '<span style="font-size:11px;color:var(--text-secondary)">Confidence</span>'
        '<span style="font-family:JetBrains Mono,monospace;font-size:11px;color:var(--text-primary)">' + "{:.1f}".format(confidence) + '%</span>'
        '</div>'
        '<div class="cb"><div style="width:' + str(min(100, confidence)) + '%;height:100%;background:' + bcc + ';border-radius:3px;"></div></div>'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    dpc = "pill-s" if "weak" in str(dxy_trend).lower() else "pill-n"
    fpc = "pill-s" if fed_rate > 4 else ("pill-b" if fed_rate < 3 else "pill-n")
    mpc = "pill-b" if macro_adj > 0 else ("pill-s" if macro_adj < 0 else "pill-n")
    st.markdown(
        '<div style="display:flex;flex-wrap:wrap;gap:5px;">'
        '<span class="mpill ' + dpc + '">DXY: ' + str(dxy_status) + '</span>'
        '<span class="mpill ' + fpc + '">Fed: ' + "{:.1f}".format(fed_rate) + '%</span>'
        '<span class="mpill ' + mpc + '">Adj: ' + ("+" if macro_adj >= 0 else "") + str(macro_adj) + '</span>'
        '</div>',
        unsafe_allow_html=True
    )

with cs2:
    st.markdown('<div class="sh">Market Snapshot</div>', unsafe_allow_html=True)
    rsi_lbl = "Overbought" if rsi > 70 else ("Oversold" if rsi < 30 else "Neutral")
    vs_w = current_price - weekly_open
    vs_m = current_price - monthly_open
    snap_items = [
        ("Gold Live", "$" + "{:,.2f}".format(current_price), ("+" if price_change >= 0 else "") + "{:.2f}".format(price_change)),
        ("ATR (14)", "${:.2f}".format(atr) if atr > 0 else "—", "Daily volatility"),
        ("RSI (14)", "{:.1f}".format(rsi), rsi_lbl),
        ("Regime", str(regime), "Market structure"),
        ("Volatility", str(volatility), "Risk level"),
        ("Weekly Open", "$" + "{:,.2f}".format(weekly_open), ("+" if vs_w >= 0 else "") + "{:.2f}".format(vs_w)),
        ("Monthly Open", "$" + "{:,.2f}".format(monthly_open), ("+" if vs_m >= 0 else "") + "{:.2f}".format(vs_m)),
        ("Prev Day High", "$" + "{:,.2f}".format(pdh), "-$" + "{:.2f}".format(pdh - current_price)),
        ("Prev Day Low", "$" + "{:,.2f}".format(pdl), "+$" + "{:.2f}".format(current_price - pdl)),
    ]
    sh = '<div class="snap-row">'
    for lb, vl, sb in snap_items:
        sh += '<div class="snap-item"><div class="snap-label">' + lb + '</div><div class="snap-value">' + vl + '</div><div class="snap-sub">' + sb + '</div></div>'
    sh += '</div>'
    st.markdown(sh, unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  ROW 2: CHART
# ─────────────────────────────────────────────
st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
cc1, cc2 = st.columns([5, 1])
with cc1:
    st.markdown('<div class="sh">Price Chart — XAUUSD (GC=F)</div>', unsafe_allow_html=True)
with cc2:
    fs_lbl = "⛶ Fullscreen" if not st.session_state.chart_fullscreen else "✕ Tutup"
    if st.button(fs_lbl, key="btn_fs", use_container_width=True):
        st.session_state.chart_fullscreen = not st.session_state.chart_fullscreen
        st.rerun()

def build_chart(hist, cur, pdh, pdl, fh=False):
    ht = 820 if fh else 400
    ma = hist["Close"].rolling(20).mean()
    sd = hist["Close"].rolling(20).std()
    ub = ma + 2 * sd
    lb = ma - 2 * sd
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.83, 0.17], vertical_spacing=0.02)
    fig.add_trace(go.Candlestick(x=hist.index, open=hist["Open"], high=hist["High"],
        low=hist["Low"], close=hist["Close"], name="XAUUSD",
        increasing_fillcolor="#00C97B", increasing_line_color="#00C97B",
        decreasing_fillcolor="#FF3B5C", decreasing_line_color="#FF3B5C",
        line=dict(width=1), whiskerwidth=0.4), row=1, col=1)
    fig.add_trace(go.Scatter(x=hist.index, y=ma, mode="lines", name="MA20",
        line=dict(color="rgba(245,166,35,0.5)", width=1)), row=1, col=1)
    fig.add_trace(go.Scatter(x=hist.index, y=ub, mode="lines",
        line=dict(color="rgba(245,166,35,0.15)", width=0.7, dash="dot"), showlegend=False), row=1, col=1)
    fig.add_trace(go.Scatter(x=hist.index, y=lb, mode="lines",
        line=dict(color="rgba(245,166,35,0.15)", width=0.7, dash="dot"),
        fill="tonexty", fillcolor="rgba(245,166,35,0.02)", showlegend=False), row=1, col=1)
    fig.add_hline(y=pdh, line_dash="dash", line_color="rgba(0,201,123,0.4)", line_width=0.8,
        annotation_text="PDH", annotation_position="right",
        annotation_font=dict(color="rgba(0,201,123,0.65)", size=10), row=1, col=1)
    fig.add_hline(y=pdl, line_dash="dash", line_color="rgba(255,59,92,0.4)", line_width=0.8,
        annotation_text="PDL", annotation_position="right",
        annotation_font=dict(color="rgba(255,59,92,0.65)", size=10), row=1, col=1)
    fig.add_hline(y=cur, line_dash="solid", line_color="rgba(245,166,35,0.85)", line_width=1.0,
        annotation_text="LIVE $" + "{:,.2f}".format(cur),
        annotation_position="right",
        annotation_font=dict(color="#F5A623", size=10, family="JetBrains Mono"), row=1, col=1)
    vc = ["rgba(0,201,123,0.3)" if float(c) >= float(o) else "rgba(255,59,92,0.3)"
          for c, o in zip(hist["Close"], hist["Open"])]
    fig.add_trace(go.Bar(x=hist.index, y=hist["Volume"], name="Vol",
        marker=dict(color=vc, line=dict(width=0)), showlegend=False), row=2, col=1)
    ax = dict(gridcolor="rgba(255,255,255,0.025)", linecolor="rgba(255,255,255,0.04)",
              zerolinecolor="rgba(255,255,255,0.025)")
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#080C12",
        height=ht, margin=dict(t=6, b=4, l=6, r=76),
        xaxis_rangeslider_visible=False,
        legend=dict(orientation="h", yanchor="bottom", y=1.002, xanchor="left", x=0,
                    bgcolor="rgba(0,0,0,0)", font=dict(color="#3E4659", size=9, family="Space Grotesk")),
        font=dict(family="Space Grotesk", color="#3E4659"),
        xaxis=dict(**ax, tickfont=dict(color="#3E4659", size=8, family="JetBrains Mono"), showgrid=True),
        yaxis=dict(**ax, tickfont=dict(color="#3E4659", size=8, family="JetBrains Mono"),
                   tickprefix="$", showgrid=True, side="right", fixedrange=False),
        xaxis2=dict(**ax, tickfont=dict(color="#3E4659", size=7), showticklabels=False),
        yaxis2=dict(**ax, tickfont=dict(color="#3E4659", size=7), side="right", fixedrange=True),
        dragmode="pan",
        hovermode="x unified",
        hoverlabel=dict(bgcolor="#12161F", bordercolor="#F5A623",
                        font=dict(color="#EEF0F5", size=10, family="JetBrains Mono")),
    )
    fig.update_xaxes(rangeselector=dict(
        buttons=[
            dict(count=5, label="5D", step="day", stepmode="backward"),
            dict(count=1, label="1M", step="month", stepmode="backward"),
            dict(count=3, label="3M", step="month", stepmode="backward"),
            dict(count=6, label="6M", step="month", stepmode="backward"),
            dict(step="all", label="MAX"),
        ],
        bgcolor="#12161F", activecolor="#F5A623",
        bordercolor="rgba(255,255,255,0.05)", borderwidth=1,
        font=dict(color="#7A8398", size=9, family="Space Grotesk"),
        x=0, y=1.0,
    ), row=1, col=1)
    return fig

if not hist.empty:
    if st.session_state.chart_fullscreen:
        st.markdown(
            '<div style="position:fixed;top:0;left:0;right:0;bottom:0;z-index:88888;'
            'background:#080C12;padding:10px 6px 6px 6px;overflow:hidden;">'
            '<div style="display:flex;justify-content:space-between;align-items:center;padding:0 8px 8px 8px;">'
            '<span style="font-family:Space Grotesk,sans-serif;font-size:13px;font-weight:700;color:#F5A623;">'
            'XAU/USD · $' + "{:,.2f}".format(current_price) + '</span>'
            '<span style="font-size:10px;color:#3E4659;">Pinch/scroll zoom · geser pan · 5D 1M 3M 6M MAX</span>'
            '</div></div>',
            unsafe_allow_html=True
        )
        fig_fs = build_chart(hist, current_price, pdh, pdl, fh=True)
        st.plotly_chart(fig_fs, use_container_width=True, config={
            "displayModeBar": True,
            "modeBarButtonsToRemove": ["toImage", "sendDataToCloud", "select2d", "lasso2d"],
            "displaylogo": False, "scrollZoom": True, "responsive": True,
        })
        st.info("💡 Pinch zoom · geser kiri-kanan · gunakan 5D/1M/3M/6M/MAX di chart · klik **✕ Tutup** untuk kembali")
    else:
        fn = build_chart(hist, current_price, pdh, pdl, fh=False)
        st.plotly_chart(fn, use_container_width=True, config={
            "displayModeBar": False, "scrollZoom": False, "responsive": True,
        })
        tc = len(hist)
        st.markdown(
            '<div class="cpbar">'
            '<div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:6px;margin-bottom:10px;">'
            '<span style="font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;color:var(--text-muted);">🕹 Navigasi Timeline</span>'
            '<div style="display:flex;gap:4px;flex-wrap:wrap;">'
            '<button class="cnav" onclick="cZ(5)">5D</button>'
            '<button class="cnav" onclick="cZ(20)">1M</button>'
            '<button class="cnav" onclick="cZ(60)">3M</button>'
            '<button class="cnav" onclick="cZ(120)">6M</button>'
            '<button class="cnav" onclick="cZ(0)">MAX</button>'
            '<button class="cnav cnav-t" onclick="cToday()">⊳ Today</button>'
            '</div></div>'
            '<div style="display:flex;align-items:center;gap:8px;">'
            '<span style="font-size:9px;color:var(--text-muted);">◀ Lama</span>'
            '<input type="range" class="csl" id="csl" min="0" max="100" value="100" step="1" oninput="cS(this.value)">'
            '<span style="font-size:9px;color:var(--text-muted);">Baru ▶</span>'
            '</div>'
            '<div style="display:flex;align-items:center;justify-content:space-between;margin-top:8px;flex-wrap:wrap;gap:4px;">'
            '<div style="display:flex;gap:4px;">'
            '<button class="cnav" onclick="cZI()">🔍＋</button>'
            '<button class="cnav" onclick="cZO()">🔍－</button>'
            '</div>'
            '<span id="cpos" style="font-family:JetBrains Mono,monospace;font-size:9px;color:var(--text-muted);">← geser →</span>'
            '</div></div>'
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
            '    Plotly.relayout(d,{"xaxis.range":[x0,x1],"xaxis2.range":[x0,x1]});'
            '    var lb=document.getElementById("cpos");'
            '    if(lb)lb.innerText="C"+(si+1)+"-"+ei+"/"+T;'
            '    var sl=document.getElementById("csl");'
            '    if(sl)sl.style.background="linear-gradient(to right,#F5A623 "+P+"%,rgba(255,255,255,0.07) "+P+"%)";'
            '  }catch(e){}'
            '}'
            'window.cS=function(v){P=parseFloat(v);ar();};'
            'window.cZ=function(n){if(n===0){V=T;P=0;}else V=Math.min(n,T);ar();};'
            'window.cZI=function(){V=Math.max(5,Math.round(V*0.6));ar();};'
            'window.cZO=function(){V=Math.min(T,Math.round(V*1.6));ar();};'
            'window.cToday=function(){P=100;var sl=document.getElementById("csl");if(sl)sl.value=100;ar();};'
            'function ini(){var d=gd();if(!d||!d.data||!d.data[0]){setTimeout(ini,400);return;}ar();}'
            'setTimeout(ini,900);'
            '})();</script>',
            unsafe_allow_html=True
        )
        st.markdown(
            '<div class="cpbar-footer">💡 Klik <b style="color:var(--gold)">⛶ Fullscreen</b> untuk grafik layar penuh — lebih mudah di HP</div>',
            unsafe_allow_html=True
        )
else:
    st.warning("⚠️ Data chart tidak tersedia.")

# ─────────────────────────────────────────────
#  ROW 3: RISK MANAGER + LOT CALCULATOR
# ─────────────────────────────────────────────
st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
st.markdown('<div class="sh">Risk Manager & Stop Loss</div>', unsafe_allow_html=True)
rm1, rm2 = st.columns([3, 2], gap="large")

with rm1:
    st.markdown(
        '<div class="slexp">'
        '<strong>Apa itu Stop Loss (SL)?</strong><br>'
        'Batas harga kerugian maksimum yang Anda siapkan sebelum masuk posisi. '
        'Jika harga menyentuh SL, posisi otomatis ditutup.<br><br>'
        '<strong>Cara hitung:</strong> SL = ' + "{:.1f}x".format(SL_MULT) + ' ATR = $' + "{:.2f}".format(sl_dist) + ' dari entry. '
        'ATR saat ini $' + ("{:.2f}".format(atr) if atr > 0 else "—") + '/hari.<br><br>'
        '<strong>Tip:</strong> Masuk hanya saat signal bukan WAIT + confidence >60% + risiko max 1-2% modal.'
        '</div>',
        unsafe_allow_html=True
    )
    arr = "↑ LONG" if signal == "BUY" else ("↓ SHORT" if signal == "SELL" else "— WAIT")
    slc = "rval-s"; tpc = "rval-b"
    st.markdown(
        '<div class="rcard">'
        '<div class="rtitle">🎯 Risk/Reward — ' + signal + '</div>'
        '<div class="rrow"><span class="rkey">Entry Price</span><span class="rval">$' + "{:,.2f}".format(current_price) + ' ' + arr + '</span></div>'
        '<div class="rrow"><span class="rkey">Stop Loss</span><span class="rval ' + slc + '">$' + "{:,.2f}".format(sl_price) + '&nbsp;(-$' + "{:.2f}".format(sl_dist) + ')</span></div>'
        '<div class="rrow"><span class="rkey">Take Profit</span><span class="rval ' + tpc + '">$' + "{:,.2f}".format(tp_price) + '&nbsp;(+$' + "{:.2f}".format(tp_dist) + ')</span></div>'
        '<div class="rrow"><span class="rkey">Risk/Reward</span><span class="rval ' + ("rval-b" if rr >= 2 else "rval-w") + '">1 : ' + "{:.2f}".format(rr) + '</span></div>'
        '<div class="rrow"><span class="rkey">ATR basis</span><span class="rval">$' + "{:.2f}".format(atr) + '/hari</span></div>'
        '</div>',
        unsafe_allow_html=True
    )

with rm2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">💰 Lot Calculator</div>', unsafe_allow_html=True)
    cap = st.number_input("Modal Akun (USD)", min_value=100.0, max_value=1000000.0,
                          value=st.session_state.risk_capital, step=100.0, format="%.2f", key="cap_in")
    st.session_state.risk_capital = cap
    rpv = st.slider("Risk per Trade (%)", min_value=0.5, max_value=5.0,
                    value=st.session_state.risk_pct, step=0.1, format="%.1f%%", key="rp_in")
    st.session_state.risk_pct = rpv
    r_usd = cap * rpv / 100
    mx = max(0.01, round(r_usd / (sl_dist * 100), 2)) if sl_dist > 0 else 0.01
    st.markdown(
        '<div style="margin-top:12px;">'
        '<div class="rrow"><span class="rkey">Risk Amount</span><span class="rval">$' + "{:.2f}".format(r_usd) + '</span></div>'
        '<div class="rrow"><span class="rkey">SL Distance</span><span class="rval">$' + "{:.2f}".format(sl_dist) + '</span></div>'
        '<div class="rrow"><span class="rkey">Max Safe Lot</span><span class="rval rval-b">' + "{:.2f}".format(mx) + ' lot</span></div>'
        '<div class="rrow"><span class="rkey">Max Rugi (SL kena)</span><span class="rval rval-s">-$' + "{:.2f}".format(mx * sl_dist * 100) + '</span></div>'
        '<div class="rrow"><span class="rkey">Potensi Profit (TP)</span><span class="rval rval-b">+$' + "{:.2f}".format(mx * tp_dist * 100) + '</span></div>'
        '</div>'
        '<div style="margin-top:10px;padding:9px;background:rgba(0,0,0,0.25);border-radius:8px;font-size:11px;color:var(--text-muted);line-height:1.5;">'
        '⚠️ <b style="color:var(--gold)">Catatan:</b> 1 pip Gold = $1/lot standard. Sesuaikan leverage broker.'
        '</div>',
        unsafe_allow_html=True
    )
    st.markdown("</div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  USER MANUAL
# ─────────────────────────────────────────────
st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
with st.expander("📖 User Manual — Cara Membaca Dashboard Ini"):
    st.markdown("""
<div style="color:#7A8398;line-height:1.8;font-size:13px;">

### 🏅 XAUUSD DSS — Panduan Pengguna

**DSS (Decision Support System)** membantu trader Gold membuat keputusan terstruktur berdasarkan analisis teknikal dan data makro.

---

#### 🔄 Live Price & Auto-Refresh
- Harga diambil dari **gold-api.com** (gratis, realtime, no API key)
- **Auto-refresh setiap 15 detik** otomatis — harga, gauge, semua data berubah sendiri
- Tombol **🔄 Refresh** (kiri atas) = paksa refresh sekarang
- Tombol **⏸ Pause** = matikan auto-refresh sementara; klik **▶ Resume** untuk aktifkan kembali
- Countdown "14s... 13s..." di chip bawah FAB = sisa waktu sebelum update berikutnya

#### 📊 Signal Engine (Speedometer)
| Signal | Arti | Tindakan |
|--------|------|----------|
| **BUY** | Momentum naik | Pertimbangkan Long |
| **SELL** | Momentum turun | Pertimbangkan Short |
| **WAIT** | Sinyal belum jelas | Tunggu konfirmasi |

**Confidence %** = kekuatan sinyal. Di bawah 60% = sinyal lemah, sebaiknya WAIT.

#### 🎯 Stop Loss & Take Profit
- **SL = 1.5× ATR** dari entry — cukup jauh agar tidak kena noise pasar
- **TP = 2.5× ATR** — target profit selalu lebih besar dari risiko
- **R/R ≥ 1:2** = ideal untuk hit-and-run

#### 💰 Lot Calculator
- Masukkan modal dan % risiko per trade
- Sistem hitung otomatis lot maksimum aman
- Rekomendasi pemula: **0.5–1% risk per trade**

#### 📈 Chart — Normal View
- Slider bawah = geser timeline kiri (lama) – kanan (baru)
- **5D/1M/3M/6M/MAX** = preset zoom periode
- **🔍+ / 🔍−** = zoom in/out

#### 📈 Chart — Fullscreen
- Klik **⛶ Fullscreen** = grafik mengisi seluruh layar HP
- Pinch zoom, geser pan bebas tanpa bentrok scroll halaman
- Klik **✕ Tutup** untuk kembali

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
