import yfinance as yf
import requests
import pandas as pd
from datetime import datetime, timedelta

class FundamentalFilter:
    """
    Fundamental Filter Layer for XAUUSD
    Analyzes DXY trend and Fed Rate stance
    Acts as MULTIPLIER — boosts or penalizes technical score
    """

    DXY_BOOST    =  10.0  # DXY bearish  = gold bullish boost
    DXY_PENALTY  = -15.0  # DXY bullish  = gold bearish penalty
    FED_BOOST    =  10.0  # Dovish Fed   = gold bullish boost
    FED_PENALTY  = -15.0  # Hawkish Fed  = gold bearish penalty

    # Supreme economic events that affect Gold (48h radar)
    SUPREME_KEYWORDS = [
        'FOMC', 'Federal Reserve', 'Fed Rate', 'Interest Rate Decision',
        'CPI', 'Consumer Price Index', 'PCE',
        'Non-Farm Payroll', 'NFP', 'Nonfarm',
        'Powell', 'Fed Chair',
        'Geopolitical', 'War', 'Conflict',
    ]

    def get_dxy_analysis(self) -> dict:
        """
        Fetch DXY (US Dollar Index) and determine trend
        Bearish DXY = Bullish Gold (negative correlation)
        """
        try:
            dxy = yf.download('DX-Y.NYB', period='60d', interval='1d',
                              progress=False, auto_adjust=True)
            if dxy.empty:
                return self._dxy_fallback()

            close = dxy['Close'].squeeze()
            ma20  = close.rolling(20).mean()
            last  = close.iloc[-1]
            ma    = ma20.iloc[-1]

            # Slope of MA over last 5 days
            slope = (ma20.iloc[-1] - ma20.iloc[-5]) / 5

            prev_week = close.iloc[-6]
            change_pct = ((last - prev_week) / prev_week) * 100

            if slope < -0.05 and last < ma:
                trend    = "BEARISH"
                adj      = self.DXY_BOOST
                color    = "green"
                label    = "DXY Weakening — Bullish for Gold"
            elif slope > 0.05 and last > ma:
                trend    = "BULLISH"
                adj      = self.DXY_PENALTY
                color    = "red"
                label    = "DXY Strengthening — Bearish for Gold"
            else:
                trend    = "NEUTRAL"
                adj      = 0.0
                color    = "gray"
                label    = "DXY Neutral — No significant impact"

            return {
                'trend': trend, 'adjustment': adj,
                'last_value': round(float(last), 3),
                'ma20': round(float(ma), 3),
                'change_pct': round(float(change_pct), 2),
                'label': label, 'color': color,
                'available': True,
            }
        except Exception as e:
            return self._dxy_fallback(str(e))

    def _dxy_fallback(self, err="") -> dict:
        return {
            'trend': 'UNAVAILABLE', 'adjustment': 0.0,
            'last_value': None, 'ma20': None,
            'change_pct': None,
            'label': f'DXY data unavailable ({err})',
            'color': 'gray', 'available': False,
        }

    def get_fed_analysis(self) -> dict:
        """
        Fetch current Fed Funds Rate from FRED API (free, no key needed for basic)
        Determine hawkish vs dovish stance from recent rate direction
        """
        try:
            # Use yfinance proxy: 13-week T-Bill as Fed rate proxy (free, no API key)
            tbill = yf.download('^IRX', period='90d', interval='1d',
                                progress=False, auto_adjust=True)
            if tbill.empty:
                return self._fed_fallback()

            rate  = tbill['Close'].squeeze()
            last  = float(rate.iloc[-1])
            prev  = float(rate.iloc[-20])  # ~1 month ago

            change = last - prev

            if change > 0.10:
                stance   = "HAWKISH"
                adj      = self.FED_PENALTY
                color    = "red"
                label    = f"Fed Hawkish — Rates Rising ({last:.2f}%) → Bearish Gold"
            elif change < -0.10:
                stance   = "DOVISH"
                adj      = self.FED_BOOST
                color    = "green"
                label    = f"Fed Dovish — Rates Falling ({last:.2f}%) → Bullish Gold"
            else:
                stance   = "NEUTRAL"
                adj      = 0.0
                color    = "gray"
                label    = f"Fed Neutral — Rates Stable ({last:.2f}%)"

            return {
                'stance': stance, 'adjustment': adj,
                'current_rate': round(last, 2),
                'rate_change': round(change, 2),
                'label': label, 'color': color,
                'available': True,
            }
        except Exception as e:
            return self._fed_fallback(str(e))

    def _fed_fallback(self, err="") -> dict:
        return {
            'stance': 'UNAVAILABLE', 'adjustment': 0.0,
            'current_rate': None, 'rate_change': None,
            'label': f'Fed rate data unavailable ({err})',
            'color': 'gray', 'available': False,
        }

    def get_event_radar(self) -> dict:
        """
        Simple event radar — checks next 48h for supreme events
        Uses a static calendar approach (expandable later)
        Returns warning if high-impact event is near
        """
        # Static high-impact dates (update manually or via scraper later)
        # For now returns a safe default with instruction
        return {
            'events_found': [],
            'alert': False,
            'alert_message': '',
            'window_hours': 48,
            'note': 'Manual update: check forexfactory.com for FOMC/NFP/CPI dates',
        }

    def apply_fundamental_adjustment(self, technical_score: float) -> dict:
        """
        Apply DXY and Fed adjustments to technical probability score
        Returns adjusted score and full breakdown
        """
