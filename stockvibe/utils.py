"""
utils.py – StockVibe Utility Functions
Market status, formatting, constants, and shared helpers.
"""

import pytz
from datetime import datetime, time as dtime
import pandas as pd
import streamlit as st

# ─────────────────────────────────────────────
#  Constants
# ─────────────────────────────────────────────
IST = pytz.timezone("Asia/Kolkata")

# NSE market hours
MARKET_OPEN  = dtime(9, 15)
MARKET_CLOSE = dtime(15, 30)

# Popular NSE tickers grouped by sector
SECTOR_STOCKS = {
    "IT": ["TCS.NS", "INFY.NS", "WIPRO.NS", "HCLTECH.NS", "TECHM.NS", "LTI.NS", "MPHASIS.NS"],
    "Banking": ["HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "KOTAKBANK.NS", "AXISBANK.NS", "BANDHANBNK.NS", "IDFCFIRSTB.NS"],
    "Auto": ["MARUTI.NS", "TATAMOTORS.NS", "M&M.NS", "BAJAJ-AUTO.NS", "HEROMOTOCO.NS", "EICHERMOT.NS"],
    "Pharma": ["SUNPHARMA.NS", "DRREDDY.NS", "CIPLA.NS", "DIVISLAB.NS", "BIOCON.NS", "LUPIN.NS"],
    "FMCG": ["HINDUNILVR.NS", "ITC.NS", "NESTLEIND.NS", "BRITANNIA.NS", "DABUR.NS", "MARICO.NS"],
    "Energy": ["RELIANCE.NS", "ONGC.NS", "BPCL.NS", "IOC.NS", "GAIL.NS", "POWERGRID.NS"],
    "Metals": ["TATASTEEL.NS", "JSWSTEEL.NS", "HINDALCO.NS", "VEDL.NS", "COAL.NS", "NMDC.NS"],
    "Telecom": ["BHARTIARTL.NS", "IDEA.NS", "TATACOMM.NS"],
}

# Nifty 50 index + Sensex tickers
INDEX_TICKERS = {
    "Nifty 50": "^NSEI",
    "Sensex": "^BSESN",
    "Nifty Bank": "^NSEBANK",
    "Nifty IT": "^CNXIT",
}

# Available indicators
INDICATOR_OPTIONS = [
    "EMA9", "EMA21", "EMA50",
    "SMA20", "SMA50",
    "RSI", "MACD",
    "Bollinger Bands",
    "VWAP",
    "Supertrend",
]

# Timeframe options
TIMEFRAME_OPTIONS = {
    "1 min":  "1m",
    "5 min":  "5m",
    "15 min": "15m",
    "30 min": "30m",
    "1 Hour": "1h",
    "1 Day":  "1d",
}

RISK_LEVELS = ["Conservative", "Moderate", "Aggressive"]

ALL_SECTORS = list(SECTOR_STOCKS.keys())


# ─────────────────────────────────────────────
#  Market Status
# ─────────────────────────────────────────────
def is_market_open() -> bool:
    """Check if NSE/BSE market is currently open (Mon–Fri, 9:15–15:30 IST)."""
    now_ist = datetime.now(IST)
    if now_ist.weekday() >= 5:  # Saturday=5, Sunday=6
        return False
    current_time = now_ist.time()
    return MARKET_OPEN <= current_time <= MARKET_CLOSE


def market_status_label() -> tuple[str, str]:
    """Return (label, color) for market status badge."""
    if is_market_open():
        return "🟢 MARKET OPEN", "#00D4AA"
    now = datetime.now(IST)
    if now.weekday() >= 5:
        return "🔴 MARKET CLOSED (Weekend)", "#FF4B4B"
    if now.time() < MARKET_OPEN:
        return "🟡 PRE-MARKET", "#FFD700"
    return "🔴 MARKET CLOSED", "#FF4B4B"


def get_ist_now() -> str:
    return datetime.now(IST).strftime("%d %b %Y, %I:%M:%S %p IST")


# ─────────────────────────────────────────────
#  Formatting helpers
# ─────────────────────────────────────────────
def fmt_currency(value: float, symbol: str = "₹") -> str:
    """Format number as Indian currency with crore/lakh suffixes."""
    if value is None:
        return "N/A"
    abs_val = abs(value)
    sign = "-" if value < 0 else ""
    if abs_val >= 1e7:
        return f"{sign}{symbol}{abs_val/1e7:.2f} Cr"
    elif abs_val >= 1e5:
        return f"{sign}{symbol}{abs_val/1e5:.2f} L"
    elif abs_val >= 1000:
        return f"{sign}{symbol}{abs_val:,.2f}"
    return f"{sign}{symbol}{abs_val:.2f}"


def fmt_pct(value: float) -> str:
    if value is None:
        return "N/A"
    sign = "+" if value >= 0 else ""
    return f"{sign}{value:.2f}%"


def fmt_number(value: float, decimals: int = 2) -> str:
    if value is None:
        return "N/A"
    return f"{value:,.{decimals}f}"


def color_for_change(change: float) -> str:
    return "#00D4AA" if change >= 0 else "#FF4B4B"


def pct_change_badge(pct: float) -> str:
    arrow = "▲" if pct >= 0 else "▼"
    color = color_for_change(pct)
    return f'<span style="color:{color};font-weight:600">{arrow} {abs(pct):.2f}%</span>'


# ─────────────────────────────────────────────
#  Ticker helpers
# ─────────────────────────────────────────────
def normalise_ticker(ticker: str) -> str:
    """Add .NS suffix if no exchange suffix present."""
    ticker = ticker.strip().upper()
    if "." not in ticker and not ticker.startswith("^"):
        ticker = ticker + ".NS"
    return ticker


def get_sector_tickers(sectors: list) -> list:
    """Return tickers for a list of sectors (de-duplicated)."""
    tickers = []
    for s in sectors:
        tickers.extend(SECTOR_STOCKS.get(s, []))
    return list(dict.fromkeys(tickers))


# ─────────────────────────────────────────────
#  Session state helpers
# ─────────────────────────────────────────────
def ensure_session_defaults():
    defaults = {
        "logged_in": False,
        "user_id": None,
        "username": None,
        "user_name": None,
        "preferences": {},
        "page": "Dashboard",
        "watchlist": [],
        "last_refresh": None,
        "dark_mode": True,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


# ─────────────────────────────────────────────
#  Custom CSS
# ─────────────────────────────────────────────
CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── Root & global ─────────────────────────────── */
:root {
    --bg-primary:    #0A0E1A;
    --bg-secondary:  #111827;
    --bg-card:       #141D2E;
    --bg-card-hover: #1A2538;
    --accent:        #00D4AA;
    --accent-2:      #6366F1;
    --accent-3:      #F59E0B;
    --red:           #FF4B4B;
    --green:         #00D4AA;
    --text-primary:  #E2E8F0;
    --text-muted:    #94A3B8;
    --border:        rgba(255,255,255,0.07);
    --font-main:     'Space Grotesk', sans-serif;
    --font-mono:     'JetBrains Mono', monospace;
    --radius:        12px;
    --radius-sm:     8px;
    --shadow:        0 4px 24px rgba(0,0,0,0.4);
}

* { font-family: var(--font-main) !important; }
code, .mono { font-family: var(--font-mono) !important; }

.stApp { background: var(--bg-primary); }

/* ── Sidebar ─────────────────────────────────── */
section[data-testid="stSidebar"] {
    background: var(--bg-secondary) !important;
    border-right: 1px solid var(--border);
}
section[data-testid="stSidebar"] .stButton button {
    width: 100%;
    text-align: left;
    background: transparent;
    border: none;
    color: var(--text-muted);
    padding: 0.6rem 1rem;
    border-radius: var(--radius-sm);
    transition: all 0.2s;
    font-size: 0.9rem;
}
section[data-testid="stSidebar"] .stButton button:hover {
    background: rgba(0,212,170,0.1);
    color: var(--accent);
}

/* ── Metric cards ─────────────────────────────── */
.metric-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.2rem 1.4rem;
    transition: all 0.25s ease;
    position: relative;
    overflow: hidden;
}
.metric-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, var(--accent), var(--accent-2));
}
.metric-card:hover {
    background: var(--bg-card-hover);
    transform: translateY(-2px);
    box-shadow: var(--shadow);
}
.metric-label { color: var(--text-muted); font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.3rem; }
.metric-value { color: var(--text-primary); font-size: 1.6rem; font-weight: 700; }
.metric-delta { font-size: 0.85rem; margin-top: 0.2rem; }

/* ── Stock ticker card ─────────────────────────── */
.ticker-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1rem 1.2rem;
    margin-bottom: 0.5rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    transition: all 0.2s;
}
.ticker-card:hover { background: var(--bg-card-hover); border-color: var(--accent); }
.ticker-name { font-weight: 600; font-size: 0.95rem; }
.ticker-sub  { color: var(--text-muted); font-size: 0.75rem; }
.ticker-price { font-family: var(--font-mono) !important; font-size: 1.05rem; font-weight: 600; text-align: right; }

/* ── Section headers ─────────────────────────── */
.section-header {
    font-size: 1.25rem;
    font-weight: 700;
    color: var(--text-primary);
    margin: 1.5rem 0 1rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}
.section-header::after {
    content: '';
    flex: 1;
    height: 1px;
    background: var(--border);
    margin-left: 0.5rem;
}

/* ── Status badge ─────────────────────────────── */
.status-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    padding: 0.3rem 0.8rem;
    border-radius: 100px;
    font-size: 0.78rem;
    font-weight: 600;
    letter-spacing: 0.05em;
}

/* ── Alert toast ──────────────────────────────── */
.alert-toast {
    background: linear-gradient(135deg, #1A2538, #141D2E);
    border-left: 3px solid var(--accent-3);
    border-radius: var(--radius-sm);
    padding: 0.8rem 1rem;
    margin-bottom: 0.5rem;
    font-size: 0.88rem;
}

/* ── Table styling ─────────────────────────────── */
.stDataFrame { background: var(--bg-card) !important; border-radius: var(--radius) !important; }

/* ── Input styling ─────────────────────────────── */
.stTextInput input, .stSelectbox select, .stNumberInput input {
    background: var(--bg-card) !important;
    border-color: var(--border) !important;
    color: var(--text-primary) !important;
    border-radius: var(--radius-sm) !important;
}

/* ── Button overrides ──────────────────────────── */
.stButton button {
    border-radius: var(--radius-sm) !important;
    font-weight: 600 !important;
    transition: all 0.2s !important;
}
.stButton button[kind="primary"] {
    background: linear-gradient(135deg, var(--accent), #00A88A) !important;
    border: none !important;
    color: #0A0E1A !important;
}
.stButton button:hover { transform: translateY(-1px) !important; box-shadow: 0 4px 12px rgba(0,212,170,0.3) !important; }

/* ── Logo / branding ─────────────────────────────── */
.brand-logo {
    font-size: 1.4rem;
    font-weight: 800;
    background: linear-gradient(135deg, var(--accent), var(--accent-2));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: -0.02em;
}
.brand-tagline { color: var(--text-muted); font-size: 0.72rem; letter-spacing: 0.08em; text-transform: uppercase; }

/* ── P&L colors ──────────────────────────────────── */
.pnl-positive { color: #00D4AA; }
.pnl-negative { color: #FF4B4B; }

/* ── Divider ─────────────────────────────────────── */
hr { border-color: var(--border) !important; margin: 1rem 0 !important; }

/* ── Scrollbar ─────────────────────────────────── */
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: var(--bg-primary); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 10px; }
::-webkit-scrollbar-thumb:hover { background: var(--accent); }

/* ── Tooltip ─────────────────────────────────── */
[data-tooltip]:hover::after {
    content: attr(data-tooltip);
    position: absolute;
    background: #1A2538;
    color: var(--text-primary);
    padding: 0.4rem 0.7rem;
    border-radius: var(--radius-sm);
    font-size: 0.78rem;
    border: 1px solid var(--border);
    z-index: 1000;
    white-space: nowrap;
}
</style>
"""
