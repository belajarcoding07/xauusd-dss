import yfinance as yf
import pandas as pd

class FundamentalFilter:
    DXY_BOOST   =  10.0
    DXY_PENALTY = -15.0
    FED_BOOST   =  10.0
    FED_PENALTY = -15.0

    def get_dxy_analysis(self):
        try:
            tk = yf.Ticker('DX-Y.NYB')
            df = tk.history(period='60d', interval='1d')
            if df is None or df.empty or len(df) < 10:
                return self._dxy_fallback()
            close = df['Close'].astype(float)
            ma20  = close.rolling(20).mean()
            last  = float(close.iloc[-1])
            ma    = float(ma20.iloc[-1])
            prev  = float(close.iloc[-6]) if len(close) >= 6 else last
            change_pct = ((last - prev) / prev) * 100
            slope = float((ma20.iloc[-1] - ma20.iloc[-5]) / 5) if len(ma20) >= 5 else 0
            if slope < -0.05 and last < ma:
                trend = "BEARISH"
                adj   = self.DXY_BOOST
                label = "DXY Weakening — Bullish for Gold"
            elif slope > 0.05 and last > ma:
                trend = "BULLISH"
                adj   = self.DXY_PENALTY
                label = "DXY Strengthening — Bearish for Gold"
            else:
                trend = "NEUTRAL"
                adj   = 0.0
                label = "DXY Neutral — No significant impact"
            return {
                'trend': trend, 'adjustment': adj,
                'last_value': round(last, 3),
                'ma20': round(ma, 3),
                'change_pct': round(change_pct, 2),
                'label': label, 'available': True,
            }
        except Exception as e:
            return self._dxy_fallback(str(e))

    def _dxy_fallback(self, err=""):
        return {
            'trend': 'NEUTRAL', 'adjustment': 0.0,
            'last_value': None, 'ma20': None,
            'change_pct': None,
            'label': 'DXY data unavailable',
            'available': False,
        }

    def get_fed_analysis(self):
        try:
            tk = yf.Ticker('^IRX')
            df = tk.history(period='90d', interval='1d')
            if df is None or df.empty or len(df) < 20:
                return self._fed_fallback()
            rate  = df['Close'].astype(float)
            last  = float(rate.iloc[-1])
            prev  = float(rate.iloc[-20])
            change = last - prev
            if change > 0.10:
                stance = "HAWKISH"
                adj    = self.FED_PENALTY
                label  = "Fed Hawkish — Rates Rising (" + str(round(last, 2)) + "%) — Bearish Gold"
            elif change < -0.10:
                stance = "DOVISH"
                adj    = self.FED_BOOST
                label  = "Fed Dovish — Rates Falling (" + str(round(last, 2)) + "%) — Bullish Gold"
            else:
                stance = "NEUTRAL"
                adj    = 0.0
                label  = "Fed Neutral — Rates Stable (" + str(round(last, 2)) + "%)"
            return {
                'stance': stance, 'adjustment': adj,
                'current_rate': round(last, 2),
                'rate_change': round(change, 2),
                'label': label, 'available': True,
            }
        except Exception as e:
            return self._fed_fallback(str(e))

    def _fed_fallback(self, err=""):
        return {
            'stance': 'NEUTRAL', 'adjustment': 0.0,
            'current_rate': None, 'rate_change': None,
            'label': 'Fed data unavailable',
            'available': False,
        }

    def apply_fundamental_adjustment(self, technical_score):
        dxy = self.get_dxy_analysis()
        fed = self.get_fed_analysis()
        total_adj = dxy['adjustment'] + fed['adjustment']
        total_adj = max(min(total_adj, 25.0), -25.0)
        adjusted  = round(min(max(technical_score + total_adj, 0), 100), 1)
        if total_adj > 5:
            stance = "BULLISH"
            label  = "Macro supports Gold"
        elif total_adj < -5:
            stance = "BEARISH"
            label  = "Macro pressures Gold"
        else:
            stance = "NEUTRAL"
            label  = "Macro neutral for Gold"
        return {
            'technical_score':  technical_score,
            'adjusted_score':   adjusted,
            'total_adjustment': round(total_adj, 1),
            'macro_stance':     stance,
            'macro_label':      label,
            'macro_color':      'green' if total_adj > 5 else 'red' if total_adj < -5 else 'gray',
            'dxy':   dxy,
            'fed':   fed,
            'event_radar': {'alert': False, 'events_found': []},
        }
