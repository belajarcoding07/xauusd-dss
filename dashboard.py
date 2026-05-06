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
.metric-box {
    background: #1a1a1a; border: 1px solid #2a2a2a;
    border-radius: 12px; padding: 16px 20px; margin-bottom: 10px;
}
.metric-label { font-size: 11px; color: #666; letter-spacing: .08em; margin-bottom: 4px; }
.metric-value { font-size: 22px; font-weight: 600; color: #e8e8e8; }
.metric-sub   { font-size: 12px; color: #888; margin-top: 3px; }
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


def fetch_gold_data():
    tickers = ['GC=F', 'GC=F', 'GC=F']
    for i, ticker in enumerate(tickers):
        try:
            import time
            if i > 0:
                time.sleep(3)
            tk = yf.Ticker(ticker)
            df = tk.history(period='2y', interval='1d')
            if df is None or df.empty or len(df) < 30:
                continue
            df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
            df.dropna(inplace=True)
            if float(df['Close'].iloc[-1]) < 1000:
                continue
            return df, ticker
        except Exception:
            continue
    return None, None


def get_macro(prob):
    try:
        ff = FundamentalFilter()
        result = ff.apply_fundamental_adjustment(prob)
        if result is None:
            raise ValueError("None returned")
        if 'adjusted_score' not in result:
            raise ValueError("Missing key")
        return result
    except Exception:
        return {
            'adjusted_score':   prob,
            'technical_score':  prob,
            'total_adjustment': 0,
            'macro_label':      'Macro data unavailable',
            'macro_color':      'gray',
            'macro_stance':     'NEUTRAL',
            'dxy': {
                'label': 'DXY data unavailable',
                'available': False,
                'adjustment': 0,
            },
            'fed': {
                'label': 'Fed data unavailable',
                'available': False,
                'adjustment': 0,
            },
            'event_radar': {
                'alert': False,
                'events_found': [],
            },
        }


def signal_color(signal):
    colors = {
        'BUY':      '#00d084',
        'SELL':     '#ff4d4d',
        'WAIT':     '#f5a623',
        'NO_TRADE': '#888888',
        'AVOID':    '#888888',
    }
    return colors.get(signal, '#888888')


def make_gauge(prob, signal):
    color = signal_color(signal)
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=prob,
        number={'suffix': '%', 'font': {'size': 36, 'color': color}},
        gauge={
            'axis': {
                'range': [0, 100],
                'tickcolor': '#444',
                'tickfont': {'color': '#666', 'size': 10},
            },
            'bar': {'color': color, 'thickness': 0.25},
            'bgcolor': '#1a1a1a',
            'bordercolor': '#2a2a2a',
            'steps': [
                {'range': [0,   40], 'color': '#1a0a0a'},
                {'range': [40,  60], 'color': '#1a1a0a'},
                {'range': [60, 100], 'color': '#0a1a0a'},
            ],
            'threshold': {
                'line': {'color': color, 'width': 3},
                'thickness': 0.8,
                'value': prob,
            },
        },
        domain={'x': [0, 1], 'y': [0, 1]},
    ))
    fig.update_layout(
        paper_bgcolor='#0d0d0d',
        plot_bgcolor='#0d0d0d',
        margin=dict(t=20, b=10, l=20, r=20),
        height=260,
        font={'color': '#888'},
    )
    return fig


def make_price_chart(df, liq):
    close = df['Close'].astype(float)
    ma20  = close.rolling(20).mean()
    std   = close.rolling(20).std()
    u2    = ma20 + 2 * std
    l2    = ma20 - 2 * std
    u3    = ma20 + 3 * std
    l3    = ma20 - 3 * std
    last90 = df.tail(90)

    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=last90.index,
        open=last90['Open'].astype(float),
        high=last90['High'].astype(float),
        low=last90['Low'].astype(float),
        close=last90['Close'].astype(float),
        increasing_line_color='#00d084',
        decreasing_line_color='#ff4d4d',
        name='Price',
        showlegend=False,
    ))

    bands = [
        (u3.tail(90), '3sd Upper', 'dot'),
        (u2.tail(90), '2sd Upper', 'dash'),
        (ma20.tail(90), 'MA20',    'solid'),
        (l2.tail(90), '2sd Lower', 'dash'),
        (l3.tail(90), '3sd Lower', 'dot'),
    ]
    for band, name, dash in bands:
        fig.add_trace(go.Scatter(
            x=last90.index, y=band, name=name,
            line=dict(
                color='#3a3a3a' if 'MA' not in name else '#5566aa',
                width=1, dash=dash,
            ),
            showlegend=True,
        ))

    hlines = [
        ('PDH',    liq['pdh'],          '#f5a623'),
        ('PDL',    liq['pdl'],          '#f5a623'),
        ('W.Open', liq['weekly_open'],  '#5599ff'),
        ('M.Open', liq['monthly_open'], '#aa55ff'),
    ]
    for name, val, col in hlines:
        fig.add_hline(
            y=val, line_dash='dot', line_color=col, line_width=1,
            annotation_text=" " + name + " " + str(val),
            annotation_font_color=col,
            annotation_font_size=10,
        )

    fig.update_layout(
        paper_bgcolor='#0d0d0d',
        plot_bgcolor='#0d0d0d',
        xaxis=dict(
            gridcolor='#1a1a1a', color='#555',
            rangeslider_visible=False,
        ),
        yaxis=dict(gridcolor='#1a1a1a', color='#555'),
        margin=dict(t=10, b=10, l=10, r=10),
        height=400,
        legend=dict(
            bgcolor='#111', bordercolor='#2a2a2a',
            font=dict(color='#666', size=10),
            x=0, y=1,
        ),
    )
    return fig


def render_metric(label, value, sub=""):
    st.markdown(
        "<div class='metric-box'>"
        "<div class='metric-label'>" + label + "</div>"
        "<div class='metric-value'>" + str(value) + "</div>"
        "<div class='metric-sub'>" + str(sub) + "</div>"
        "</div>",
        unsafe_allow_html=True,
    )


def main():
    col_h1, col_h2 = st.columns([3, 1])
    with col_h1:
        st.markdown("## XAUUSD Decision Engine")
        st.markdown(
            "<span style='color:#555;font-size:12px'>"
            "Hybrid Confluence | Daily Timeframe | Institutional Grade"
            "</span>",
            unsafe_allow_html=True,
        )
    with col_h2:
        wib = pytz.timezone('Asia/Jakarta')
        now = datetime.now(wib).strftime('%d %b %Y | %H:%M WIB')
        st.markdown(
            "<div style='text-align:right;color:#555;"
            "font-size:12px;padding-top:16px'>" + now + "</div>",
            unsafe_allow_html=True,
        )

    st.markdown(
        "<hr style='border-color:#1a1a1a;margin:4px 0 16px'>",
        unsafe_allow_html=True,
    )

    df, source = fetch_gold_data()

    if df is None:
        st.error(
            "Unable to fetch Gold data. "
            "Market may be closed or data source unavailable. "
            "Please try again in a few minutes."
        )
        if st.button("Retry"):
            st.rerun()
        return

    st.caption("Data: " + str(source) + " | Rows: " + str(len(df)))

    try:
        engine = XAUEngine(df)
        result = engine.get_full_analysis()
    except Exception as e:
        st.error("Engine error: " + str(e))
        return

    macro  = get_macro(result['probability'])
    prob   = macro['adjusted_score']
    signal = result['signal']
    r      = result['regime']
    v      = result['volatility']
    l      = result['liquidity']
    m      = result['momentum']

    col1, col2 = st.columns([1, 2])

    with col1:
        st.plotly_chart(
        make_price_chart(df, l),
        use_container_width=True,
        config={
            'scrollZoom': True,
            'displayModeBar': True,
            'displaylogo': False,
        }
    )
        sc = signal_color(signal)
        st.markdown(
            "<div style='text-align:center;font-size:32px;"
            "font-weight:700;color:" + sc + "'>" + signal + "</div>",
            unsafe_allow_html=True,
        )

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
            bc = '#00d084' if score >= 70 else '#f5a623' if score >= 50 else '#ff4d4d'
            col.markdown(
                "<div class='metric-box'>"
                "<div class='metric-label'>" + name + " | " + wt + "</div>"
                "<div class='metric-value' style='color:" + bc + "'>"
                + str(score) + "</div></div>",
                unsafe_allow_html=True,
            )

        st.markdown(
            "<div class='reason-box'>" + result['reason'] + "</div>",
            unsafe_allow_html=True,
        )

        adj = macro['total_adjustment']
        ac  = '#00d084' if adj > 0 else '#ff4d4d' if adj < 0 else '#888'
        sg  = '+' if adj >= 0 else ''
        st.markdown(
            "<div class='reason-box' style='margin-top:6px'>"
            "<b style='color:" + ac + "'>Macro: " + str(macro['macro_label']) + "</b><br>"
            "DXY: " + str(macro['dxy']['label']) + "<br>"
            "Fed: " + str(macro['fed']['label']) + "<br>"
            "Adj: <b style='color:" + ac + "'>"
            + sg + str(adj) + " pts</b>"
            " | Final: <b>" + str(prob) + "%</b>"
            "</div>",
            unsafe_allow_html=True,
        )

    st.markdown("#### Price Chart | 90 Days")
    st.plotly_chart(make_price_chart(df, l), use_container_width=True)

    col3, col4 = st.columns(2)

    with col3:
        st.markdown("#### Market Snapshot")
        lp  = float(df['Close'].iloc[-1])
        pp  = float(df['Close'].iloc[-2])
        chg = lp - pp
        cp  = (chg / pp) * 100
        cc  = '#00d084' if chg >= 0 else '#ff4d4d'
        cs  = '+' if chg >= 0 else ''

        render_metric(
            "Gold Price",
            "$" + "{:,.2f}".format(lp),
            "<span style='color:" + cc + "'>"
            + cs + "{:.2f}".format(chg)
            + " (" + cs + "{:.2f}".format(cp) + "%)</span>",
        )
        render_metric("ATR 14", str(v['current_atr']),
                      "Ratio: " + str(v['atr_ratio']) + "x avg")
        render_metric("RSI 14", str(m['rsi']),
                      m['rsi_signal'].replace('_', ' ').title())
        render_metric("Regime",
                      r['regime'].replace('_', ' ').title(), "")
        render_metric("Volatility",
                      v['volatility_state'].replace('_', ' ').title(), "")
        render_metric("Weekly Open",
                      "$" + str(l['weekly_open']), "Key level")
        render_metric("Monthly Open",
                      "$" + str(l['monthly_open']), "Key level")
        render_metric("PDH", "$" + str(l['pdh']), "Prev Day High")
        render_metric("PDL", "$" + str(l['pdl']), "Prev Day Low")

    with col4:
        st.markdown("#### Lot Size Calculator")
        balance  = st.number_input(
            "Account Balance (USD)",
            min_value=100.0, max_value=10000000.0,
            value=10000.0, step=500.0,
        )
        risk_pct = st.slider("Risk per Trade (%)", 0.5, 5.0, 1.0, 0.5)
        sl_pts   = st.number_input(
            "Stop Loss (USD pts)",
            min_value=1.0, max_value=500.0,
            value=float(v['dynamic_sl']), step=0.5,
        )

        risk_usd = balance * (risk_pct / 100)
        lot_size = max(round(risk_usd / (sl_pts * 100), 4), 0.01)
        slc      = '#ff4d4d' if v['high_risk'] else '#00d084'

        render_metric(
            "Dynamic SL (1.5x ATR)",
            "<span style='color:#f5a623'>"
            + str(v['dynamic_sl']) + " pts</span>",
            "",
        )
        render_metric(
            "Risk Amount",
            "$" + "{:,.2f}".format(risk_usd),
            str(risk_pct) + "% of $" + "{:,.0f}".format(balance),
        )
        render_metric(
            "Recommended Lot",
            "<span style='color:" + slc + "'>"
            + str(lot_size) + " lots</span>",
            "HIGH RISK" if v['high_risk']
            else str(sl_pts) + " pts SL",
        )

    st.markdown(
        "<div class='disclaimer'>"
        "DISCLAIMER: This tool is a Decision Support System for analytical "
        "purposes only. NOT financial advice or guarantee of profit. "
        "All trading involves substantial risk of loss. "
        "Developer assumes no liability for trading decisions."
        "</div>",
        unsafe_allow_html=True,
    )

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    if st.button("Refresh Data"):
        st.rerun()


if __name__ == '__main__':
    main()
