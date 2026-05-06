import pandas as pd
import numpy as np
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange

class XAUEngine:
    PILLAR_WEIGHTS = {
        'regime':     0.25,
        'volatility': 0.30,
        'liquidity':  0.25,
        'momentum':   0.20,
    }
    ATR_HISTORICAL_AVG   = 8.0
    HIGH_RISK_MULTIPLIER = 2.0

    def __init__(self, df):
        self.df = df.copy()
        # Normalize column names
        self.df.columns = [str(c).strip().capitalize() 
                          if str(c).strip().lower() != 'volume' 
                          else 'Volume' for c in self.df.columns]
        # Ensure index is datetime
        if not isinstance(self.df.index, pd.DatetimeIndex):
            self.df.index = pd.to_datetime(self.df.index)
        self.df = self.df.sort_index()
        self._validate()

    def _validate(self):
        for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
            if col not in self.df.columns:
                raise ValueError("Missing column: " + col)
        if len(self.df) < 30:
            raise ValueError("Not enough data rows: " + str(len(self.df)))

    def calc_regime(self):
        close = self.df['Close'].astype(float)
        ma    = close.rolling(20).mean()
        std   = close.rolling(20).std()

        last_close = float(close.iloc[-1])
        last_ma    = float(ma.iloc[-1])
        last_std   = float(std.iloc[-1])

        upper2 = last_ma + 2 * last_std
        lower2 = last_ma - 2 * last_std
        upper3 = last_ma + 3 * last_std
        lower3 = last_ma - 3 * last_std

        ma_slope   = float((ma.iloc[-1] - ma.iloc[-5]) / 5)
        trend_up   = bool(ma_slope > 0)
        trend_down = bool(ma_slope < 0)

        above_2std  = last_close > upper2
        below_2std  = last_close < lower2
        above_3std  = last_close > upper3
        below_3std  = last_close < lower3
        inside_1std = abs(last_close - last_ma) < last_std

        if above_3std or below_3std:
            regime, score = "EXTREME", 10
        elif above_2std and trend_up:
            regime, score = "STRONG_TREND_UP", 80
        elif below_2std and trend_down:
            regime, score = "STRONG_TREND_DOWN", 80
        elif above_2std:
            regime, score = "OVERBOUGHT_REVERSAL", 40
        elif below_2std:
            regime, score = "OVERSOLD_REVERSAL", 60
        elif inside_1std:
            regime, score = "MEAN_REVERTING", 50
        else:
            regime, score = "TRENDING", 65

        return {
            'score': score, 'regime': regime,
            'trend_up': trend_up, 'trend_down': trend_down,
            'last_close': round(last_close, 2),
            'ma20':       round(last_ma, 2),
            'upper2std':  round(upper2, 2),
            'lower2std':  round(lower2, 2),
            'upper3std':  round(upper3, 2),
            'lower3std':  round(lower3, 2),
        }

    def calc_volatility(self):
        high  = self.df['High'].astype(float)
        low   = self.df['Low'].astype(float)
        close = self.df['Close'].astype(float)

        atr_s = AverageTrueRange(
            high=high, low=low, close=close, window=14
        ).average_true_range()

        current_atr = float(atr_s.iloc[-1])
        atr_20avg   = float(atr_s.rolling(20).mean().iloc[-1])
        ratio       = current_atr / self.ATR_HISTORICAL_AVG
        high_risk   = bool(ratio >= self.HIGH_RISK_MULTIPLIER)
        dynamic_sl  = round(current_atr * 1.5, 2)

        if high_risk:
            score, state = 0,  "HIGH_RISK"
        elif ratio < 0.5:
            score, state = 60, "LOW_VOL"
        elif ratio < 1.0:
            score, state = 80, "NORMAL"
        elif ratio < 1.5:
            score, state = 60, "ELEVATED"
        else:
            score, state = 30, "HIGH"

        return {
            'score': score, 'high_risk': high_risk,
            'current_atr': round(current_atr, 2),
            'atr_20avg':   round(atr_20avg, 2),
            'atr_ratio':   round(ratio, 2),
            'dynamic_sl':  dynamic_sl,
            'volatility_state': state,
        }

    def calc_liquidity(self):
        close = self.df['Close'].astype(float)
        high  = self.df['High'].astype(float)
        low   = self.df['Low'].astype(float)
        opens = self.df['Open'].astype(float)

        last_close = float(close.iloc[-1])
        pdh        = float(high.iloc[-2])
        pdl        = float(low.iloc[-2])

        try:
            df_w = self.df.resample('W-MON').first()
            weekly_open = float(df_w['Open'].astype(float).iloc[-1])
        except Exception:
            weekly_open = float(opens.iloc[-5])

        try:
            df_m = self.df.resample('MS').first()
            monthly_open = float(df_m['Open'].astype(float).iloc[-1])
        except Exception:
            monthly_open = float(opens.iloc[-20])

        atr = float(AverageTrueRange(
            high=high, low=low, close=close, window=14
        ).average_true_range().iloc[-1])

        t1 = atr * 0.3
        t2 = atr * 0.6
        t3 = atr * 0.9

        at_pdh     = bool(abs(last_close - pdh)          < t1)
        at_pdl     = bool(abs(last_close - pdl)          < t1)
        at_weekly  = bool(abs(last_close - weekly_open)  < t2)
        at_monthly = bool(abs(last_close - monthly_open) < t3)
        magnets    = sum([at_pdh, at_pdl, at_weekly, at_monthly])

        above_weekly  = bool(last_close > weekly_open)
        above_monthly = bool(last_close > monthly_open)

        if magnets >= 2:
            score, status = 85, "STRONG_ZONE"
        elif magnets == 1:
            score, status = 65, "AT_ZONE"
        elif above_weekly and above_monthly:
            score, status = 60, "ABOVE_KEY_LEVELS"
        elif not above_weekly and not above_monthly:
            score, status = 55, "BELOW_KEY_LEVELS"
        else:
            score, status = 45, "BETWEEN_LEVELS"

        return {
            'score': score,
            'pdh': round(pdh, 2), 'pdl': round(pdl, 2),
            'weekly_open':  round(weekly_open, 2),
            'monthly_open': round(monthly_open, 2),
            'at_pdh': at_pdh, 'at_pdl': at_pdl,
            'at_weekly': at_weekly, 'at_monthly': at_monthly,
            'magnets_hit': magnets, 'zone_status': status,
            'above_weekly': above_weekly, 'above_monthly': above_monthly,
        }

    def calc_momentum(self, regime_data):
        close  = self.df['Close'].astype(float)
        volume = self.df['Volume'].astype(float)

        rsi = float(RSIIndicator(close=close, window=14).rsi().iloc[-1])

        vol_avg    = float(volume.rolling(20).mean().iloc[-1])
        vol_current = float(volume.iloc[-1])
        vol_ratio  = (vol_current / vol_avg) if vol_avg > 0 else 1.0
        vol_confirm = bool(vol_ratio > 1.1)

        trend_up   = bool(regime_data.get('trend_up', False))
        trend_down = bool(regime_data.get('trend_down', False))

        if trend_up:
            if 40 <= rsi <= 70:   rsi_score, sig = 75, "BULLISH_CONTINUATION"
            elif rsi < 40:        rsi_score, sig = 85, "PULLBACK_BUY"
            elif rsi > 80:        rsi_score, sig = 30, "OVERBOUGHT"
            else:                 rsi_score, sig = 50, "NEUTRAL"
        elif trend_down:
            if 30 <= rsi <= 60:   rsi_score, sig = 75, "BEARISH_CONTINUATION"
            elif rsi > 60:        rsi_score, sig = 85, "PULLBACK_SELL"
            elif rsi < 20:        rsi_score, sig = 30, "OVERSOLD"
            else:                 rsi_score, sig = 50, "NEUTRAL"
        else:
            if rsi < 35:          rsi_score, sig = 70, "OVERSOLD_BOUNCE"
            elif rsi > 65:        rsi_score, sig = 70, "OVERBOUGHT_FADE"
            else:                 rsi_score, sig = 45, "NEUTRAL_RANGE"

        final_score = min(rsi_score + (10 if vol_confirm else 0), 100)

        return {
            'score': final_score, 'rsi': round(rsi, 1),
            'rsi_signal': sig,
            'vol_ratio': round(vol_ratio, 2),
            'vol_confirm': vol_confirm,
        }

    def get_full_analysis(self):
        try:
            regime     = self.calc_regime()
            volatility = self.calc_volatility()
            liquidity  = self.calc_liquidity()
            momentum   = self.calc_momentum(regime)
        except Exception as e:
            raise ValueError("Engine calculation error: " + str(e))

        if volatility['high_risk']:
            return {
                'probability': 0, 'signal': 'NO_TRADE',
                'signal_label': 'NO TRADE',
                'reason': 'Volatility exceeds 2x historical average. High risk.',
                'regime': regime, 'volatility': volatility,
                'liquidity': liquidity, 'momentum': momentum,
            }

        W = self.PILLAR_WEIGHTS
        prob = round(min(max(
            regime['score']     * W['regime'] +
            volatility['score'] * W['volatility'] +
            liquidity['score']  * W['liquidity'] +
            momentum['score']   * W['momentum'],
        0), 100), 1)

        trend_up   = regime.get('trend_up', False)
        trend_down = regime.get('trend_down', False)

        if prob >= 70 and trend_up:
            signal, label = 'BUY',   'BUY'
        elif prob >= 70 and trend_down:
            signal, label = 'SELL',  'SELL'
        elif prob >= 70:
            signal, label = 'WAIT',  'WAIT'
        elif prob < 40:
            signal, label = 'AVOID', 'AVOID'
        else:
            signal, label = 'WAIT',  'WAIT'

        return {
            'probability': prob,
            'signal': signal,
            'signal_label': label,
            'reason': self._build_reason(regime, volatility, liquidity, momentum, prob),
            'regime': regime,
            'volatility': volatility,
            'liquidity': liquidity,
            'momentum': momentum,
        }

    def _build_reason(self, r, v, l, m, prob):
        parts = [
            "Regime: " + r['regime'].replace('_', ' ').title(),
            "Volatility: " + v['volatility_state'].replace('_', ' ').title() +
            " (ATR " + str(v['current_atr']) + ")",
        ]
        if l['magnets_hit'] > 0:
            parts.append("At " + str(l['magnets_hit']) + " liquidity zone(s)")
        parts.append(
            "Momentum: " + m['rsi_signal'].replace('_', ' ').title() +
            " (RSI " + str(m['rsi']) + ")"
        )
        if m['vol_confirm']:
            parts.append("Volume confirmed")
        parts.append("Score: " + str(prob) + "%")
        return " | ".join(parts)
