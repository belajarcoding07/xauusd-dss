import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine import XAUEngine
from fundamental import FundamentalFilter
from datetime import datetime
import pytz

st.set_page_config(
    page_title="XAUUSD Decision Engine",
    page_icon="gold",
    layout="wide",
    initial_sidebar_state="collapsed",
)

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
.stButton > button {
    background: #1a1a1a; border: 1px solid #333; color: #e8e8e8;
    border-radius: 8px; padding: 8px 24px; font-size: 13px;
}
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=3600)
def fetch_gold_data():
    tickers = ['GC=F', 'XAUUSD=X', 'GLD']
    for ticker in tickers:
        try:
            df = yf.download(ticker, period='2y', interval='1d',
                             progress=False, auto_adjust=True)
            if df is None or df.empty:
                continue
            df.columns = [c[0] if isinstance(c, tuple) else c
                          for c in df.columns]
            df.dropna(inplace=True)
            if len(df) >= 30:
                return df
        except Exception:
            continue
    return None

def signal_color(signal):
    return {
        'BUY': '#00d084', 'SELL': '#ff4d4d',
        'WAIT': '#f5a623', 'NO_TRADE': '#888', 'AVOID': '#888'
    }.get(signal, '#888')

def signal_class(signal):
    return {
        'BUY': 'signal-buy', 'SELL': 'signal-sell',
        'WAIT': 'signal-wait'
    }.get(signal, 'signal-no')

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
                {'range': [60, 100], 'color': '#0a1a0a'},
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
    u2 = ma20 + 2*std
    l2 = ma20 - 2*std
    u3 = ma20 + 3*std
    l3 = ma20 - 3*std
    last90 = df.tail(90)

    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=last90.index,
        open=last90['Open'], high=last90['High'],
        low=last90['Low'],   close=last90['Close'],
        increasing_line_color='#00d084',
        decreasing_line_color='#ff4d4d',
        name='XAUUSD', showlegend=False,
    ))
    for band, name, dash in [
        (u3.tail(90), '3sd Upper', 'dot'),
        (u2.tail(90), '2sd Upper', 'dash'),
        (ma20.tail(90), 'MA20', 'solid'),
        (l2.tail(90), '2sd Lower', 'dash'),
        (l3.tail(90), '3sd Lower', 'dot'),
    ]:
        fig.add_trace(go.Scatter(
            x=last90.index, y=band, name=name,
            line=dict(
                color='#3a3a3a' if 'MA' not in name else '#556',
                width=1, dash=dash),
            showlegend=True,
        ))
    levels = {
        'PDH': (liq['pdh'], '#f5a623'),
        'PDL': (liq['pdl'], '#f5a623'),
        'Weekly Open': (liq['weekly_open'], '#5599ff'),
        'Monthly Open': (liq['monthly_open'], '#aa55ff'),
    }
    for name, (val, col) in levels.items():
        fig.add_hline(
            y=val, line_dash='dot', line_color=col, line_width=1,
            annotation_text=" " + name + ": " + str(val),
            annotation_font_color=col,
            annotation_font_size=10,
        )
    fig.update_layout(
        paper_bgcolor='#0d0d0d', plot_bgcolor='#0d0d0d',
        xaxis=dict(gridcolor='#1a1a1a', color='#555', rangeslider_visible=False),
        yaxis=dict(gridcolor='#1a1a1a', color='#555'),
        margin=dict(t=10, b=10, l=10, r=10),
        height=400,
        legend=dict(bgcolor='#111', bordercolor='#2a2a2a',
                    font=dict(color='#666', size=10), x=0, y=1),
    )
    return fig

def main():
    col_h1, col_h2 = st.columns([3, 1])
    with col_h1:
        st.markdown("## XAUUSD Decision Engine")
        st.markdown(
            "<span style='color:#555;font-size:12px'>"
            "Hybrid Confluence | Daily Timeframe | Institutional Grade"
            "</span>",
            unsafe_allow_html=True)
    with col_h2:
        wib = pytz.timezone('Asia/Jakarta')
        now = datetime.now(wib).strftime('%d %b %Y | %H:%M WIB')
        st.markdown(
            "<div style='text-align:right;color:#555;font-size:12px;padding-top:16px'>"
            + now + "</div>",
            unsafe_allow_html=True)

    st.markdown(
        "<hr style='border-color:#1a1a1a;margin:4px 0 16px'>",
        unsafe_allow_html=True)

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

    col1, col2 = st.columns([1, 2])
    with col1:
        st.plotly_chart(make_gauge(prob, signal), use_container_width=True)
        sc = signal_class(signal)
        st.markdown(
            "<div style='text-align:center'>"
            "<span class='" + sc + "'>" + signal + "</span>"
            "</div>",
            unsafe_allow_html=True)

    with col2:
        st.markdown("#### Logic Breakdown")
        p1, p2, p3, p4 = st.columns(4)
        pillars = [
            ("Regime",     result['regime']['score'],     "25%"),
            ("Volatility", result['volatility']['score'], "30%"),
            ("Liquidity",  result['liquidity']['score'],  "25%"),
            ("Momentum",   result['momentum']['score'],   "20%"),
        ]
        for col, (name, score, wt) in zip([p1, p2, p3, p4], pillars):
            bar_color = '#00d084' if score >= 70 else '#f5a623' if score >= 50 else '#ff4d4d'
            col.markdown(
                "<div class='metric-box'>"
                "<div class='metric-label'>" + name + " | " + wt + "</div>"
                "<div class='metric-value' style='color:" + bar_color + "'>"
                + str(score) + "</div>"
                "</div>",
                unsafe_allow_html=True)

        st.markdown(
            "<div class='reason-box'>" + result['reason'] + "</div>",
            unsafe_allow_html=True)

        adj_color = '#00d084' if macro['total_adjustment'] > 0 else \
                    '#ff4d4d' if macro['total_adjustment'] < 0 else '#888'
        adj_sign  = '+' if macro['total_adjustment'] >= 0 else ''
        st.markdown(
            "<div class='reason-box' style='margin-top:6px'>"
            "<b style='color:" + adj_color + "'>Macro: " + macro['macro_label'] + "</b><br>"
            "DXY: " + macro['dxy']['label'] + "<br>"
            "Fed: " + macro['fed']['label'] + "<br>"
            "Adjustment: <b style='color:" + adj_color + "'>"
            + adj_sign + str(macro['total_adjustment']) + " pts</b>"
            " | Technical: " + str(macro['technical_score']) +
            "% | Final: <b>" + str(prob) + "%</b>"
            "</div>",
            unsafe_allow_html=True)

    st.markdown("#### Price Chart | 90 Days | StdDev Channels + Liquidity Zones")
    st.plotly_chart(make_price_chart(df, l), use_container_width=True)

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
            ("Gold Price XAU/USD",
             "$" + "{:,.2f}".format(last_price),
             "<span style='color:" + chg_color + "'>"
             + chg_sign + "{:.2f}".format(chg) +
             " (" + chg_sign + "{:.2f}".format(chg_pct) + "%)</span>"),
            ("ATR 14",       str(v['current_atr']),
             "Ratio vs hist avg: " + str(v['atr_ratio']) + "x"),
            ("RSI 14",       str(m['rsi']),
             m['rsi_signal'].replace('_', ' ').title()),
            ("Regime",
             r['regime'].replace('_', ' ').title(), ""),
            ("Volatility",
             v['volatility_state'].replace('_', ' ').title(), ""),
            ("Weekly Open",  "$" + "{:,}".format(l['weekly_open']),  "Key level"),
            ("Monthly Open", "$" + "{:,}".format(l['monthly_open']), "Key level"),
            ("PDH",          "$" + "{:,}".format(l['pdh']),  "Previous Day High"),
            ("PDL",          "$" + "{:,}".format(l['pdl']),  "Previous Day Low"),
        ]
        for label, value, sub in snap:
            st.markdown(
                "<div class='metric-box'>"
                "<div class='metric-label'>" + label + "</div>"
                "<div class='metric-value'>" + value + "</div>"
                "<div class='metric-sub'>" + sub + "</div>"
                "</div>",
                unsafe_allow_html=True)

    with col4:
        st.markdown("#### Lot Size Calculator")
        balance  = st.number_input(
            "Account Balance (USD)",
            min_value=100.0, max_value=10000000.0,
            value=10000.0, step=500.0)
        risk_pct = st.slider("Risk per Trade (%)", 0.5, 5.0, 1.0, 0.5)
        sl_pts   = st.number_input(
            "Stop Loss (USD pts)",
            min_value=1.0, max_value=500.0,
            value=float(v['dynamic_sl']), step=0.5)

        risk_usd = balance * (risk_pct / 100)
        lot_size = round(risk_usd / (sl_pts * 100), 4)
        lot_size = max(lot_size, 0.01)

        sl_color = '#ff4d4d' if v['high_risk'] else '#00d084'
        st.markdown(
            "<div class='metric-box' style='margin-top:12px'>"
            "<div class='metric-label'>Dynamic SL (1.5x ATR)</div>"
            "<div class='metric-value' style='color:#f5a623'>"
            + str(v['dynamic_sl']) + " pts</div>"
            "</div>",
            unsafe_allow_html=True)
        st.markdown(
            "<div class='metric-box'>"
            "<div class='metric-label'>Risk Amount</div>"
            "<div class='metric-value'>$" + "{:,.2f}".format(risk_usd) + "</div>"
            "<div class='metric-sub'>" + str(risk_pct) +
            "% of $" + "{:,.0f}".format(balance) + "</div>"
            "</div>",
            unsafe_allow_html=True)
        st.markdown(
            "<div class='metric-box'>"
            "<div class='metric-label'>Recommended Lot Size</div>"
            "<div class='metric-value' style='color:" + sl_color + "'>"
            + str(lot_size) + " lots</div>"
            "<div class='metric-sub'>"
            + ("HIGH RISK - consider 0 lot" if v['high_risk']
               else "Based on " + str(sl_pts) + " pts SL")
            + "</div>"
            "</div>",
            unsafe_allow_html=True)

    st.markdown(
        "<div class='disclaimer'>"
        "DISCLAIMER: This tool is a Decision Support System (DSS) for analytical purposes only. "
        "It does NOT constitute financial advice or guarantee of profit. "
        "All trading involves substantial risk of loss. "
        "The developer assumes no liability for trading decisions made based on this tool."
        "</div>",
        unsafe_allow_html=True)

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    if st.button("Refresh Data"):
        st.cache_data.clear()
        st.rerun()

if __name__ == '__main__':
    main()
