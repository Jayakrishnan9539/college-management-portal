"""
analysis.py – StockVibe Data & Technical Analysis
Handles yfinance fetching, indicator computation, charting, and signals.
"""

import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Tuple
import warnings
warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────
#  Data Fetching (cached)
# ─────────────────────────────────────────────

@st.cache_data(ttl=30, show_spinner=False)
def fetch_quote(ticker: str) -> Optional[Dict]:
    """Fetch a single live quote for a ticker. Cached 30s."""
    try:
        t = yf.Ticker(ticker)
        info = t.fast_info
        hist = t.history(period="2d", interval="1d")
        if hist.empty:
            return None
        last_close = hist["Close"].iloc[-1]
        prev_close = hist["Close"].iloc[-2] if len(hist) > 1 else last_close
        change     = last_close - prev_close
        pct_change = (change / prev_close) * 100 if prev_close else 0
        return {
            "ticker":     ticker,
            "price":      round(last_close, 2),
            "prev_close": round(prev_close, 2),
            "change":     round(change, 2),
            "pct_change": round(pct_change, 2),
            "volume":     int(info.shares_outstanding or 0),
            "market_cap": getattr(info, "market_cap", None),
        }
    except Exception:
        return None


@st.cache_data(ttl=30, show_spinner=False)
def fetch_intraday(ticker: str, interval: str = "5m", days: int = 1) -> Optional[pd.DataFrame]:
    """Fetch intraday OHLCV data. Cached 30s."""
    try:
        period_map = {
            "1m": "1d", "2m": "1d", "5m": "1d",
            "15m": "5d", "30m": "5d",
            "1h": "1mo", "1d": "6mo",
        }
        period = period_map.get(interval, "1d")
        df = yf.download(ticker, period=period, interval=interval,
                         progress=False, auto_adjust=True)
        if df.empty:
            return None
        df = df.dropna()
        df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
        df.index = pd.to_datetime(df.index)
        return df
    except Exception:
        return None


@st.cache_data(ttl=300, show_spinner=False)
def fetch_fundamentals(ticker: str) -> Dict:
    """Fetch fundamental data. Cached 5 min."""
    try:
        t = yf.Ticker(ticker)
        info = t.info
        return {
            "Market Cap":    info.get("marketCap"),
            "P/E Ratio":     info.get("trailingPE"),
            "EPS":           info.get("trailingEps"),
            "52W High":      info.get("fiftyTwoWeekHigh"),
            "52W Low":       info.get("fiftyTwoWeekLow"),
            "Avg Volume":    info.get("averageVolume"),
            "Beta":          info.get("beta"),
            "Div Yield":     info.get("dividendYield"),
            "Sector":        info.get("sector"),
            "Industry":      info.get("industry"),
            "Company":       info.get("longName", ticker),
            "Description":   info.get("longBusinessSummary", ""),
        }
    except Exception:
        return {}


@st.cache_data(ttl=60, show_spinner=False)
def fetch_multiple_quotes(tickers: List[str]) -> Dict[str, Optional[Dict]]:
    """Batch fetch quotes for a list of tickers."""
    results = {}
    for t in tickers:
        results[t] = fetch_quote(t)
    return results


@st.cache_data(ttl=300, show_spinner=False)
def fetch_top_movers(tickers: List[str]) -> Tuple[List[Dict], List[Dict]]:
    """Return top 5 gainers and top 5 losers from a list of tickers."""
    quotes = [fetch_quote(t) for t in tickers if fetch_quote(t)]
    quotes = [q for q in quotes if q]
    gainers = sorted(quotes, key=lambda x: x["pct_change"], reverse=True)[:5]
    losers  = sorted(quotes, key=lambda x: x["pct_change"])[:5]
    return gainers, losers


# ─────────────────────────────────────────────
#  Technical Indicators
# ─────────────────────────────────────────────

def compute_indicators(df: pd.DataFrame, indicators: List[str]) -> pd.DataFrame:
    """Compute requested technical indicators on OHLCV DataFrame."""
    if df is None or df.empty:
        return df

    close  = df["Close"]
    high   = df["High"]
    low    = df["Low"]
    volume = df["Volume"]

    # ── Moving Averages ──
    if "EMA9"  in indicators: df["EMA9"]  = close.ewm(span=9,  adjust=False).mean()
    if "EMA21" in indicators: df["EMA21"] = close.ewm(span=21, adjust=False).mean()
    if "EMA50" in indicators: df["EMA50"] = close.ewm(span=50, adjust=False).mean()
    if "SMA20" in indicators: df["SMA20"] = close.rolling(20).mean()
    if "SMA50" in indicators: df["SMA50"] = close.rolling(50).mean()

    # ── RSI ──
    if "RSI" in indicators:
        delta = close.diff()
        gain  = delta.where(delta > 0, 0).rolling(14).mean()
        loss  = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs    = gain / loss.replace(0, np.nan)
        df["RSI"] = 100 - (100 / (1 + rs))

    # ── MACD ──
    if "MACD" in indicators:
        ema12      = close.ewm(span=12, adjust=False).mean()
        ema26      = close.ewm(span=26, adjust=False).mean()
        df["MACD"]        = ema12 - ema26
        df["MACD_Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
        df["MACD_Hist"]   = df["MACD"] - df["MACD_Signal"]

    # ── Bollinger Bands ──
    if "Bollinger Bands" in indicators:
        sma20         = close.rolling(20).mean()
        std20         = close.rolling(20).std()
        df["BB_Upper"] = sma20 + 2 * std20
        df["BB_Mid"]   = sma20
        df["BB_Lower"] = sma20 - 2 * std20

    # ── VWAP (intraday only) ──
    if "VWAP" in indicators:
        tp = (high + low + close) / 3
        df["VWAP"] = (tp * volume).cumsum() / volume.cumsum()

    # ── Supertrend ──
    if "Supertrend" in indicators:
        df = _compute_supertrend(df)

    return df


def _compute_supertrend(df: pd.DataFrame, period: int = 10, multiplier: float = 3.0) -> pd.DataFrame:
    """Compute Supertrend indicator."""
    high, low, close = df["High"], df["Low"], df["Close"]

    # ATR
    tr1 = high - low
    tr2 = (high - close.shift()).abs()
    tr3 = (low  - close.shift()).abs()
    tr  = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(period).mean()

    hl2 = (high + low) / 2
    upperband = hl2 + multiplier * atr
    lowerband = hl2 - multiplier * atr

    supertrend = [np.nan] * len(df)
    direction  = [1]  * len(df)

    for i in range(1, len(df)):
        if close.iloc[i] > upperband.iloc[i - 1]:
            direction[i] = 1
        elif close.iloc[i] < lowerband.iloc[i - 1]:
            direction[i] = -1
        else:
            direction[i] = direction[i - 1]
            if direction[i] == 1 and lowerband.iloc[i] < lowerband.iloc[i - 1]:
                lowerband.iloc[i] = lowerband.iloc[i - 1]
            if direction[i] == -1 and upperband.iloc[i] > upperband.iloc[i - 1]:
                upperband.iloc[i] = upperband.iloc[i - 1]

        supertrend[i] = lowerband.iloc[i] if direction[i] == 1 else upperband.iloc[i]

    df["Supertrend"]  = supertrend
    df["ST_Direction"] = direction
    return df


def compute_buy_sell_signals(df: pd.DataFrame) -> pd.DataFrame:
    """
    Simple signal logic:
    BUY  – EMA9 crosses above EMA21 + RSI < 60
    SELL – EMA9 crosses below EMA21 + RSI > 40
    """
    df["Signal"] = 0
    if "EMA9" not in df.columns or "EMA21" not in df.columns:
        return df

    cross_above = (df["EMA9"] > df["EMA21"]) & (df["EMA9"].shift() <= df["EMA21"].shift())
    cross_below = (df["EMA9"] < df["EMA21"]) & (df["EMA9"].shift() >= df["EMA21"].shift())

    if "RSI" in df.columns:
        df.loc[cross_above & (df["RSI"] < 60), "Signal"] = 1   # BUY
        df.loc[cross_below & (df["RSI"] > 40), "Signal"] = -1  # SELL
    else:
        df.loc[cross_above, "Signal"] = 1
        df.loc[cross_below, "Signal"] = -1

    return df


# ─────────────────────────────────────────────
#  Charting
# ─────────────────────────────────────────────

CHART_COLORS = {
    "EMA9":           "#00D4AA",
    "EMA21":          "#6366F1",
    "EMA50":          "#F59E0B",
    "SMA20":          "#EC4899",
    "SMA50":          "#8B5CF6",
    "BB_Upper":       "rgba(99,102,241,0.5)",
    "BB_Mid":         "rgba(99,102,241,0.8)",
    "BB_Lower":       "rgba(99,102,241,0.5)",
    "VWAP":           "#F97316",
    "Supertrend_up":  "#00D4AA",
    "Supertrend_dn":  "#FF4B4B",
}


def build_main_chart(
    df: pd.DataFrame,
    ticker: str,
    indicators: List[str],
    show_volume: bool = True,
) -> go.Figure:
    """Build an interactive Plotly candlestick + indicator chart."""
    if df is None or df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No data available", xref="paper", yref="paper",
                           x=0.5, y=0.5, showarrow=False, font=dict(color="#94A3B8", size=16))
        return fig

    # Subplot rows: main + volume (+ RSI if selected + MACD if selected)
    has_rsi  = "RSI"  in indicators and "RSI"  in df.columns
    has_macd = "MACD" in indicators and "MACD" in df.columns

    row_count   = 1 + show_volume + has_rsi + has_macd
    row_heights = [0.55]
    specs       = [[ {"type": "candlestick"} ]]

    if show_volume:
        row_heights.append(0.15)
        specs.append([{"type": "bar"}])
    if has_rsi:
        row_heights.append(0.15)
        specs.append([{"type": "scatter"}])
    if has_macd:
        row_heights.append(0.15)
        specs.append([{"type": "scatter"}])

    subplot_titles = [ticker]
    if show_volume: subplot_titles.append("Volume")
    if has_rsi:     subplot_titles.append("RSI (14)")
    if has_macd:    subplot_titles.append("MACD")

    fig = make_subplots(
        rows=row_count, cols=1,
        shared_xaxes=True,
        row_heights=row_heights,
        specs=specs,
        subplot_titles=subplot_titles,
        vertical_spacing=0.03,
    )

    # ── Candlestick ──
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df["Open"], high=df["High"],
        low=df["Low"],   close=df["Close"],
        name="Price",
        increasing_line_color="#00D4AA",
        decreasing_line_color="#FF4B4B",
        increasing_fillcolor="rgba(0,212,170,0.8)",
        decreasing_fillcolor="rgba(255,75,75,0.8)",
    ), row=1, col=1)

    # ── Overlay indicators ──
    for ind in ["EMA9", "EMA21", "EMA50", "SMA20", "SMA50"]:
        if ind in indicators and ind in df.columns:
            fig.add_trace(go.Scatter(
                x=df.index, y=df[ind], name=ind,
                line=dict(color=CHART_COLORS.get(ind, "#ffffff"), width=1.5),
                opacity=0.85,
            ), row=1, col=1)

    # ── Bollinger Bands ──
    if "Bollinger Bands" in indicators and "BB_Upper" in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df["BB_Upper"], name="BB Upper",
            line=dict(color=CHART_COLORS["BB_Upper"], width=1, dash="dash"),
        ), row=1, col=1)
        fig.add_trace(go.Scatter(
            x=df.index, y=df["BB_Lower"], name="BB Lower",
            line=dict(color=CHART_COLORS["BB_Lower"], width=1, dash="dash"),
            fill="tonexty", fillcolor="rgba(99,102,241,0.06)",
        ), row=1, col=1)
        fig.add_trace(go.Scatter(
            x=df.index, y=df["BB_Mid"], name="BB Mid",
            line=dict(color=CHART_COLORS["BB_Mid"], width=1, dash="dot"),
        ), row=1, col=1)

    # ── VWAP ──
    if "VWAP" in indicators and "VWAP" in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df["VWAP"], name="VWAP",
            line=dict(color=CHART_COLORS["VWAP"], width=2, dash="longdash"),
        ), row=1, col=1)

    # ── Supertrend ──
    if "Supertrend" in indicators and "Supertrend" in df.columns:
        up  = df[df["ST_Direction"] == 1]
        dn  = df[df["ST_Direction"] == -1]
        fig.add_trace(go.Scatter(
            x=up.index, y=up["Supertrend"], name="ST Bull",
            mode="markers", marker=dict(color="#00D4AA", size=4, symbol="triangle-up"),
        ), row=1, col=1)
        fig.add_trace(go.Scatter(
            x=dn.index, y=dn["Supertrend"], name="ST Bear",
            mode="markers", marker=dict(color="#FF4B4B", size=4, symbol="triangle-down"),
        ), row=1, col=1)

    # ── Buy/Sell signals ──
    if "Signal" in df.columns:
        buys  = df[df["Signal"] == 1]
        sells = df[df["Signal"] == -1]
        if not buys.empty:
            fig.add_trace(go.Scatter(
                x=buys.index, y=buys["Low"] * 0.998,
                mode="markers+text",
                name="BUY",
                marker=dict(color="#00D4AA", size=12, symbol="triangle-up"),
                text=["B"] * len(buys), textposition="bottom center",
                textfont=dict(color="#00D4AA", size=8),
            ), row=1, col=1)
        if not sells.empty:
            fig.add_trace(go.Scatter(
                x=sells.index, y=sells["High"] * 1.002,
                mode="markers+text",
                name="SELL",
                marker=dict(color="#FF4B4B", size=12, symbol="triangle-down"),
                text=["S"] * len(sells), textposition="top center",
                textfont=dict(color="#FF4B4B", size=8),
            ), row=1, col=1)

    # ── Volume ──
    vol_row = 2
    if show_volume:
        vol_colors = ["rgba(0,212,170,0.6)" if c >= o else "rgba(255,75,75,0.6)"
                      for c, o in zip(df["Close"], df["Open"])]
        fig.add_trace(go.Bar(
            x=df.index, y=df["Volume"],
            name="Volume", marker_color=vol_colors, showlegend=False,
        ), row=vol_row, col=1)

    # ── RSI ──
    rsi_row = vol_row + 1 if show_volume else vol_row
    if has_rsi:
        fig.add_trace(go.Scatter(
            x=df.index, y=df["RSI"], name="RSI",
            line=dict(color="#6366F1", width=1.5),
        ), row=rsi_row, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="rgba(255,75,75,0.5)",  row=rsi_row, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="rgba(0,212,170,0.5)",  row=rsi_row, col=1)
        fig.update_yaxes(range=[0, 100], row=rsi_row, col=1)

    # ── MACD ──
    macd_row = rsi_row + 1 if has_rsi else rsi_row
    if has_macd:
        fig.add_trace(go.Scatter(
            x=df.index, y=df["MACD"], name="MACD",
            line=dict(color="#00D4AA", width=1.5),
        ), row=macd_row, col=1)
        fig.add_trace(go.Scatter(
            x=df.index, y=df["MACD_Signal"], name="Signal",
            line=dict(color="#F59E0B", width=1.5),
        ), row=macd_row, col=1)
        hist_colors = ["rgba(0,212,170,0.7)" if v >= 0 else "rgba(255,75,75,0.7)"
                       for v in df["MACD_Hist"].fillna(0)]
        fig.add_trace(go.Bar(
            x=df.index, y=df["MACD_Hist"], name="Histogram",
            marker_color=hist_colors, showlegend=False,
        ), row=macd_row, col=1)

    # ── Layout ──
    fig.update_layout(
        height=650,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(14,18,26,0.95)",
        font=dict(color="#94A3B8", family="Space Grotesk"),
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02,
            xanchor="right", x=1,
            bgcolor="rgba(17,24,39,0.8)",
            bordercolor="rgba(255,255,255,0.07)",
            borderwidth=1,
        ),
        xaxis_rangeslider_visible=False,
        margin=dict(l=10, r=10, t=40, b=10),
        hovermode="x unified",
    )
    fig.update_xaxes(
        gridcolor="rgba(255,255,255,0.04)",
        linecolor="rgba(255,255,255,0.1)",
        showspikes=True, spikecolor="#6366F1",
        spikethickness=1, spikedash="dot",
    )
    fig.update_yaxes(
        gridcolor="rgba(255,255,255,0.04)",
        linecolor="rgba(255,255,255,0.1)",
    )

    return fig


def build_portfolio_chart(history: List[Dict]) -> go.Figure:
    """Build a portfolio value over time line chart from transaction history."""
    if not history:
        fig = go.Figure()
        fig.add_annotation(text="No transactions yet", xref="paper", yref="paper",
                           x=0.5, y=0.5, showarrow=False, font=dict(color="#94A3B8", size=14))
        return _style_empty_fig(fig)

    df = pd.DataFrame(history)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["signed_total"] = df.apply(
        lambda r: -r["total"] if r["action"] == "BUY" else r["total"], axis=1
    )
    df = df.sort_values("timestamp")
    df["cumulative"] = df["signed_total"].cumsum()

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["timestamp"], y=df["cumulative"],
        mode="lines+markers",
        line=dict(color="#00D4AA", width=2.5),
        fill="tozeroy", fillcolor="rgba(0,212,170,0.08)",
        marker=dict(size=6, color="#00D4AA"),
        name="Net Cash Flow",
    ))
    fig.update_layout(
        height=300,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(14,18,26,0.95)",
        font=dict(color="#94A3B8", family="Space Grotesk"),
        margin=dict(l=10, r=10, t=20, b=10),
        xaxis=dict(gridcolor="rgba(255,255,255,0.04)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.04)"),
        showlegend=False,
    )
    return fig


def build_allocation_pie(holdings: List[Dict], current_prices: Dict) -> go.Figure:
    labels, values = [], []
    for h in holdings:
        price = current_prices.get(h["ticker"], {})
        price = price.get("price", h["avg_price"]) if price else h["avg_price"]
        val = h["quantity"] * price
        labels.append(h["ticker"].replace(".NS", "").replace(".BO", ""))
        values.append(val)

    if not values:
        return _style_empty_fig(go.Figure())

    colors = ["#00D4AA", "#6366F1", "#F59E0B", "#EC4899", "#8B5CF6",
              "#F97316", "#14B8A6", "#EF4444", "#3B82F6", "#A78BFA"]

    fig = go.Figure(go.Pie(
        labels=labels, values=values,
        hole=0.6,
        marker=dict(colors=colors[:len(labels)], line=dict(color="#0A0E1A", width=2)),
        textinfo="label+percent",
        textfont=dict(color="#E2E8F0", size=11),
    ))
    fig.update_layout(
        height=300,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#94A3B8", family="Space Grotesk"),
        margin=dict(l=10, r=10, t=20, b=10),
        showlegend=False,
    )
    return fig


def _style_empty_fig(fig: go.Figure) -> go.Figure:
    fig.update_layout(
        height=300,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(14,18,26,0.95)",
        font=dict(color="#94A3B8"),
        margin=dict(l=10, r=10, t=20, b=10),
    )
    return fig


# ─────────────────────────────────────────────
#  Backtesting
# ─────────────────────────────────────────────

def simple_backtest(
    ticker: str,
    interval: str = "1d",
    period: str = "6mo",
    strategy: str = "EMA Cross",
) -> Dict:
    """
    Simple backtest: 
    - EMA Cross: Buy on EMA9 > EMA21 crossover, Sell on reverse
    - RSI Mean Revert: Buy RSI < 35, Sell RSI > 65
    Returns performance stats and trade log.
    """
    try:
        df = yf.download(ticker, period=period, interval=interval,
                         progress=False, auto_adjust=True)
        if df.empty:
            return {"error": "No data"}
        df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
        df = df.dropna()

        close = df["Close"]
        trades = []
        position = 0
        entry_price = 0

        if strategy == "EMA Cross":
            df["EMA9"]  = close.ewm(span=9,  adjust=False).mean()
            df["EMA21"] = close.ewm(span=21, adjust=False).mean()
            for i in range(1, len(df)):
                if df["EMA9"].iloc[i] > df["EMA21"].iloc[i] and df["EMA9"].iloc[i-1] <= df["EMA21"].iloc[i-1]:
                    if position == 0:
                        position = 1
                        entry_price = close.iloc[i]
                        trades.append({"type": "BUY", "price": entry_price, "date": df.index[i], "pnl": None})
                elif df["EMA9"].iloc[i] < df["EMA21"].iloc[i] and df["EMA9"].iloc[i-1] >= df["EMA21"].iloc[i-1]:
                    if position == 1:
                        exit_price = close.iloc[i]
                        pnl = (exit_price - entry_price) / entry_price * 100
                        trades[-1]["exit_price"] = exit_price
                        trades.append({"type": "SELL", "price": exit_price, "date": df.index[i], "pnl": pnl})
                        position = 0

        elif strategy == "RSI Mean Revert":
            delta = close.diff()
            gain  = delta.where(delta > 0, 0).rolling(14).mean()
            loss  = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs    = gain / loss.replace(0, np.nan)
            df["RSI"] = 100 - (100 / (1 + rs))
            for i in range(14, len(df)):
                if df["RSI"].iloc[i] < 35 and position == 0:
                    position = 1
                    entry_price = close.iloc[i]
                    trades.append({"type": "BUY", "price": entry_price, "date": df.index[i], "pnl": None})
                elif df["RSI"].iloc[i] > 65 and position == 1:
                    exit_price = close.iloc[i]
                    pnl = (exit_price - entry_price) / entry_price * 100
                    trades.append({"type": "SELL", "price": exit_price, "date": df.index[i], "pnl": pnl})
                    position = 0

        sell_trades = [t for t in trades if t["type"] == "SELL" and t.get("pnl") is not None]
        if not sell_trades:
            return {"error": "No completed trades in selected period", "trades": []}

        pnls  = [t["pnl"] for t in sell_trades]
        wins  = [p for p in pnls if p > 0]
        total_return = sum(pnls)
        win_rate = len(wins) / len(pnls) * 100 if pnls else 0
        avg_win  = np.mean(wins) if wins else 0
        avg_loss = np.mean([p for p in pnls if p <= 0]) if [p for p in pnls if p <= 0] else 0

        return {
            "total_trades":   len(sell_trades),
            "win_rate":       round(win_rate, 1),
            "total_return":   round(total_return, 2),
            "avg_win":        round(avg_win, 2),
            "avg_loss":       round(avg_loss, 2),
            "best_trade":     round(max(pnls), 2) if pnls else 0,
            "worst_trade":    round(min(pnls), 2) if pnls else 0,
            "trades":         trades,
            "df":             df,
        }
    except Exception as e:
        return {"error": str(e)}


# ─────────────────────────────────────────────
#  Stock Recommendations
# ─────────────────────────────────────────────

def recommend_stocks(
    sectors: List[str],
    risk_level: str,
    sector_stocks: Dict,
    max_stocks: int = 6,
) -> List[Dict]:
    """
    Recommend stocks based on user sector preferences and risk level.
    Filters by simple momentum: last-5-day return > 0 for moderate/aggressive.
    """
    if not sectors:
        return []

    candidates = []
    for sector in sectors:
        candidates.extend(sector_stocks.get(sector, []))
    candidates = list(dict.fromkeys(candidates))[:20]  # cap API calls

    results = []
    for ticker in candidates:
        try:
            hist = yf.download(ticker, period="5d", interval="1d", progress=False, auto_adjust=True)
            if hist.empty or len(hist) < 2:
                continue
            hist.columns = [c[0] if isinstance(c, tuple) else c for c in hist.columns]
            ret_5d = (hist["Close"].iloc[-1] - hist["Close"].iloc[0]) / hist["Close"].iloc[0] * 100
            vol    = hist["Volume"].mean()

            # Risk filter
            if risk_level == "Conservative" and ret_5d < 0:
                continue
            if risk_level == "Moderate" and ret_5d < -2:
                continue
            # Aggressive: no filter

            results.append({
                "ticker":    ticker,
                "price":     round(float(hist["Close"].iloc[-1]), 2),
                "ret_5d":    round(float(ret_5d), 2),
                "volume":    int(vol),
                "reason":    f"{ret_5d:+.1f}% (5d momentum)",
            })
        except Exception:
            continue

    results.sort(key=lambda x: x["ret_5d"], reverse=(risk_level != "Conservative"))
    return results[:max_stocks]
