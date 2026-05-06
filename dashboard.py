import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from engine import XAUEngine
from fundamental import FundamentalFilter
from datetime import datetime
import pytz

# ── PAGE CONFIG ─────────────────────────────────────────────────────
st.set_page_config(
    page_title="XAUUSD Decision Engine",
    page_icon="🥇",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── DARK MODE CSS ────────────────────────────────────────────────────
st.markdown("""
<style>
  html, body, [data-testid="stAppViewContainer"] {
    background-color: #0d0d0d !important; color: #e8e8e8;
  }
  [data-testid="stSidebar"] { background-color: #111 !important; }
  .metric-box {
    background: #1a1a1a; border: 1px solid #2a2a2a;
    border-radius: 12px; padding: 16px 20px; margin-bottom: 10px;
  }
  .metric-label { font-size: 11px; color: #666; letter-spacing: .08em; margin-bottom: 4px; }
  .metric-value { font-size: 22px; font-weight: 600; color: #e8e8e8; }
  .metric-sub   { font-size: 12px; color: #888; margin-top: 3px; }
  .signal-buy   { color: #00d084; font-size: 32px; font-weight: 700; }
  .signal-sell  { color: #ff4d4d; font-size: 32px; font-weight: 700; }
  .signal-wait  { color: #f5a623; font-size: 32px; font-weight: 700; }
  .signal-no    { color: #888;    font-size: 32px; font-weight: 700; }
  .reason-box {
    background: #141414; border-left: 3px solid #2a2a2a;
    border-radius: 0 8px 8px 0; padding: 14px 18px;
    font-size: 13px; color: #aaa; line-height: 1.7; margin-top: 8px;
  }
  .disclaimer {
    background: #1a1208; border: 1px solid #3a2a00;
    border-radius: 8px; padding: 10px 16px;
    font-size: 11px; color: #a08040; margin-top: 16px; line-height: 1.6;
  }
  .event-alert {
    background: #1a1400; border: 1px solid #f5a623;
    border-radius: 8px; padding: 10px 16px;
    font-size: 12px; color: #f5a623; margin-bottom: 12px;
  }
  .stButton > button {
    background: #1a1a1a; border: 1px solid #333; color: #e8e8e8;
    border-radius: 8px; padding: 8px 24px; font-size: 13px;
  }
  .stButton > button:hover { border-color: #888; }
  div[data-testid="stMetric"] { background: #1a1a1a; border-radius: 10px; padding: 12px; }
</style>
""", unsafe_allow_html=True)

# ── HELPERS ──────────────────────────────────────────────────────────
@st.cache_data(ttl=3600)
def fetch_gold_data():
    df = yf.download('GC=F', period='2y', interval='1d',
                     progress=False, auto_adjust=True)
    df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
    df.dropna(inplace=True)
    return df

def signal_color(signal):
    return {'BUY': '#00d084', 'SELL': '#ff4d4d',
            'WAIT': '#f5a623', 'NO_TRADE': '#888', 'AVOID': '#888'}.get(signal, '#888')

def signal_class(signal):
    return {'BUY': 'signal-buy', 'SELL': 'signal-sell',
            'WAIT': 'signal-wait'}.get(signal, 'signal-no')

def make_gauge(prob, signal):
    color = signal_color(signal)
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=prob,
        number={'suffix': '%', 'font': {'size': 36, 'color': color}},
        gauge={
            'axis': {'range': [0, 100], 'tickcolor': '#444',
                     'tickfont': {'color': '#666', 'size': 10}},
            'bar': {'color': color, 'thickness': 0.25},
            'bgcolor': '#1a1a1a',
            'bordercolor': '#2a2a2a',
            'steps': [
                {'range': [0,  40], 'color': '#1a0a0a'},
                {'range': [40, 60], 'color': '#1a1a0a'},
                {'range': [60, 100],'color': '#0a1a0a'},
            ],
            'threshold': {
                'line': {'color': color, 'width': 3},
                'thickness': 0.8, 'value': prob,
            },
        },
        domain={'x': [0, 1], 'y': [0, 1]},
    ))
    fig.update_layout(
        paper_bgcolor='#0d0d0d', plot_bgcolor='#0d0d0d',
        margin=dict(t=20, b=10, l=20, r=20), height=260,
        font={'color': '#888'},
    )
    return fig

def make_price_chart(df, liq):
    close = df['Close']
    ma20  = close.rolling(20).mean()
    std   = close.rolling(20).std()
    u2    = ma20 + 2*std; l2 = ma20 - 2*std
    u3    = ma20 + 3*std; l3 = ma20 - 3*std

    fig = go.Figure()
    last90 = df.tail(90)

    # Candles
    fig.add_trace(go.Candlestick(
        x=last90.index,
        open=last90['Open'], high=last90['High'],
        low=last90['Low'],   close=last90['Close'],
        increasing_line_color='#00d084',
        decreasing_line_color='#ff4d4d',
        name='XAUUSD', showlegend=False,
    ))

    # StdDev bands
    for band, name, dash in [
        (u3.tail(90), '3σ Upper', 'dot'),
        (u2.tail(90), '2σ Upper', 'dash'),
        (ma20.tail(90),'MA20',    'solid'),
        (l2.tail(90), '2σ Lower', 'dash'),
        (l3.tail(90), '3σ Lower', 'dot'),
    ]:
        fig.add_trace(go.Scatter(
            x=last90.index, y=band, name=name,
            line=dict(color='#3a3a3a' if 'MA' not in name else '#556',
                      width=1, dash=dash),
            showlegend=True,
        ))

    # Liquidity levels
    levels = {
        'PDH': (liq['pdh'],         '#f5a623'),
        'PDL': (liq['pdl'],         '#f5a623'),
        'Weekly Open': (liq['weekly_open'],  '#5599ff'),
        'Monthly Open':(liq['monthly_open'], '#aa55ff'),
    }
    for name, (val, col) in levels.items():
        fig.add_hline(y=val, line_dash='dot', line_color=col,
                      line_width=1,
                      annotation_text=f" {name}: {val}",
                      annotation_font_color=col,
                      annotation_font_size=10)

    fig.update_layout(
        paper_bgcolor='#0d0d0d', plot_bgcolor='#0d0d0d',
        xaxis=dict(gridcolor='#1a1a1a', color='#555',
                   rangeslider_visible=False),
        yaxis=dict(gridcolor='#1a1a1a', color='#555'),
        margin=dict(t=10, b=10, l=10, r=10),
        height=400, legend=dict(
            bgcolor='#111', bordercolor='#2a2a2a',
            font=dict(color='#666', size=10), x=0, y=1,
        ),
    )
    return fig

# ── MAIN APP ─────────────────────────────────────────────────────────
def main():
    # Header
    col_h1, col_h2 = st.columns([3, 1])
    with col_h1:
        st.markdown("## 🥇 XAUUSD Decision Engine")
        st.markdown("<span style='color:#555;font-size:12px'>Hybrid Confluence · Daily Timeframe · Institutional Grade</span>",
                    unsafe_allow_html=True)
    with col_h2:
        wib = pytz.timezone('Asia/Jakarta')
        now = datetime.now(wib).strftime('%d %b %Y · %H:%M WIB')
        st.markdown(f"<div style='text-align:right;color:#555;font-size:12px;padding-top:16px'>{now}</div>",
                    unsafe_allow_html=True)

    st.markdown("<hr style='border-color:#1a1a1a;margin:4px 0 16px'>", unsafe_allow_html=True)

    # Load & Analyze
    with st.spinner("Fetching market data..."):
        df = fetch_gold_data()

    if df is None or len(df) < 30:
        st.error("Unable to fetch Gold data. Please refresh.")
        return

    engine = XAUEngine(df)
    result = engine.get_full_analysis()
    ff     = FundamentalFilter()
    macro  = ff.apply_fundamental_adjustment(result['probability'])

    prob   = macro['adjusted_score']
    signal = result['signal']
    r      = result['regime']
    v      = result['volatility']
    l      = result['liquidity']
    m      = result['momentum']

    # ── ROW 1: GAUGE + SIGNAL + REASON ──────────────────────────────
    col1, col2 = st.columns([1, 2])

    with col1:
        st.plotly_chart(make_gauge(prob, signal), use_container_width=True)
        sc = signal_class(signal)
        st.markdown(
            f"<div style='text-align:center'><span class='{sc}'>{signal}</span></div>",
            unsafe_allow_html=True)

    with col2:
        st.markdown("#### Logic Breakdown")
        # Pillar scores
        p1, p2, p3, p4 = st.columns(4)
        pillars = [
            ("Regime",     result['regime']['score'],     "25%"),
            ("Volatility", result['volatility']['score'], "30%"),
            ("Liquidity",  result['liquidity']['score'],  "25%"),
            ("Momentum",   result['momentum']['score'],   "20%"),
        ]
        for col, (name, score, wt) in zip([p1,p2,p3,p4], pillars):
            bar_color = '#00d084' if score>=70 else '#f5a623' if score>=50 else '#ff4d4d'
            col.markdown(
                f"<div class='metric-box'>"
                f"<div class='metric-label'>{name} · {wt}</div>"
                f"<div class='metric-value' style='color:{bar_color}'>{score}</div>"
                f"</div>",
                unsafe_allow_html=True)

        # Reason text
        st.markdown(
            f"<div class='reason-box'>{result['reason']}</div>",
            unsafe_allow_html=True)

        # Macro adjustment
        adj_color = '#00d084' if macro['total_adjustment']>0 else '#ff4d4d' if macro['total_adjustment']<0 else '#888'
        adj_sign  = '+' if macro['total_adjustment']>=0 else ''
        st.markdown(
            f"<div class='reason-box' style='margin-top:6px'>"
            f"<b style='color:{adj_color}'>Macro Filter: {macro['macro_label']}</b><br>"
            f"DXY → {macro['dxy']['label']}<br>"
            f"Fed → {macro['fed']['label']}<br>"
            f"Score adjustment: <b style='color:{adj_color}'>{adj_sign}{macro['total_adjustment']} pts</b> "
            f"· Technical: {macro['technical_score']}% → Final: <b>{prob}%</b>"
            f"</div>",
            unsafe_allow_html=True)

    # ── ROW 2: PRICE CHART ───────────────────────────────────────────
    st.markdown("#### Price Chart · 90 Days · StdDev Channels + Liquidity Zones")
    st.plotly_chart(make_price_chart(df, l), use_container_width=True)

    # ── ROW 3: MARKET DATA + LOT CALCULATOR ─────────────────────────
    col3, col4 = st.columns([1, 1])

    with col3:
        st.markdown("#### Market Snapshot")
        last_price = float(df['Close'].iloc[-1])
        prev_price = float(df['Close'].iloc[-2])
        chg        = last_price - prev_price
        chg_pct    = (chg / prev_price) * 100
        chg_color  = '#00d084' if chg >= 0 else '#ff4d4d'
        chg_sign   = '+' if chg >= 0 else ''

        snap = [
            ("Gold Price (XAU/USD)",
             f"${last_price:,.2f}",
             f"<span style='color:{chg_color}'>{chg_sign}{chg:.2f} ({chg_sign}{chg_pct:.2f}%)</span>"),
            ("ATR (14)",       f"{v['current_atr']}", f"Ratio vs hist avg: {v['atr_ratio']}x"),
            ("RSI (14)",       f"{m['rsi']}",         m['rsi_signal'].replace('_',' ').title()),
            ("Regime",         r['regime'].replace('_',' ').title(), ""),
            ("Volatility",     v['volatility_state'].replace('_',' ').title(), ""),
            ("Weekly Open",    f"${l['weekly_open']:,}", "Key level"),
            ("Monthly Open",   f"${l['monthly_open']:,}", "Key level"),
            ("PDH",            f"${l['pdh']:,}",  "Previous Day High"),
            ("PDL",            f"${l['pdl']:,}",  "Previous Day Low"),
        ]
        for label, value, sub in snap:
            st.markdown(
                f"<div class='metric-box'>"
                f"<div class='metric-label'>{label}</div>"
                f"<div class='metric-value'>{value}</div>"
                f"<div class='metric-sub'>{sub}</div>"
                f"</div>",
                unsafe_allow_html=True)

    with col4:
        st.markdown("#### Lot Size Calculator")
        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

        balance   = st.number_input("Account Balance (USD)",
                                    min_value=100.0, max_value=10_000_000.0,
                                    value=10_000.0, step=500.0)
        risk_pct  = st.slider("Risk per Trade (%)", 0.5, 5.0, 1.0, 0.5)
        sl_pts    = st.number_input("Stop Loss (USD pts) — Dynamic SL suggestion below",
                                    min_value=1.0, max_value=500.0,
                                    value=float(v['dynamic_sl']), step=0.5)
        leverage  = st.selectbox("Leverage", [1, 10, 50, 100, 200, 500], index=2)

        risk_usd  = balance * (risk_pct / 100)
        # 1 standard lot Gold = 100 oz; pip value ≈ $1 per 0.01 lot per $1 move
        lot_size  = round(risk_usd / (sl_pts * 100), 4)
        lot_size  = max(lot_size, 0.01)

        st.markdown(
            f"<div class='metric-box' style='margin-top:12px'>"
            f"<div class='metric-label'>Dynamic SL Suggestion (1.5x ATR)</div>"
            f"<div class='metric-value' style='color:#f5a623'>{v['dynamic_sl']} pts</div>"
            f"</div>",
            unsafe_allow_html=True)
        st.markdown(
            f"<div class='metric-box'>"
            f"<div class='metric-label'>Risk Amount</div>"
            f"<div class='metric-value'>${risk_usd:,.2f}</div>"
            f"<div class='metric-sub'>{risk_pct}% of ${balance:,.0f}</div>"
            f"</div>",
            unsafe_allow_html=True)
        sl_color = '#ff4d4d' if v['high_risk'] else '#00d084'
        st.markdown(
            f"<div class='metric-box'>"
            f"<div class='metric-label'>Recommended Lot Size</div>"
            f"<div class='metric-value' style='color:{sl_color}'>{lot_size} lots</div>"
            f"<div class='metric-sub'>{'⚠ HIGH RISK — consider 0 lot' if v['high_risk'] else f'Based on {sl_pts} pts SL · {leverage}x leverage'}</div>"
            f"</div>",
            unsafe_allow_html=True)

    # ── DISCLAIMER ───────────────────────────────────────────────────
    st.markdown(
        "<div class='disclaimer'>"
        "⚠ <b>DISCLAIMER:</b> This tool is a Decision Support System (DSS) for educational and "
        "analytical purposes only. It does NOT constitute financial advice or a guarantee of profit. "
        "All trading involves substantial risk of loss. Past confluence patterns do not guarantee "
        "future results. Always apply your own judgment and risk management. "
        "The developer assumes no liability for trading decisions made based on this tool."
        "</div>",
        unsafe_allow_html=True)

    # ── REFRESH BUTTON ───────────────────────────────────────────────
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()

if __name__ == '__main__':
    main()
