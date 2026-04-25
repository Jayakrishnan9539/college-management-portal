# 📈 StockVibe – Intraday Analyzer & Paper Trader

> A full-featured Python web application for real-time intraday stock analysis,  
> virtual paper trading, and personalized portfolio tracking — built for Indian markets (NSE & BSE).

---

## 🚀 Quick Start

### 1. Clone / Download the project

```bash
# Place all files in a folder, e.g.:
mkdir stockvibe && cd stockvibe
```

### 2. Create a virtual environment (recommended)

```bash
python -m venv venv

# Activate:
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the app

```bash
streamlit run app.py
```

The app will open at **http://localhost:8501** in your browser.

---

## 📁 Project Structure

```
stockvibe/
├── app.py              # Main Streamlit application (router + UI pages)
├── database.py         # SQLite data layer (auth, holdings, transactions, alerts)
├── analysis.py         # yfinance data fetching + technical indicators + charting
├── utils.py            # Constants, CSS, formatting helpers, market status
├── requirements.txt    # Python dependencies
├── README.md           # This file
├── .streamlit/
│   └── config.toml     # Streamlit theme (dark mode, colors)
└── data/
    └── stockvibe.db    # SQLite database (auto-created on first run)
```

---

## 🔑 Default Demo Account

On first run, register a new account — or use:
- **Username:** `demo`  
- **Password:** `demo123`

*(Register it manually on the login screen the first time)*

---

## 🌟 Features

| Feature | Description |
|---|---|
| 🔐 Auth | Register / Login / Logout with SQLite-backed user accounts |
| 📊 Live Charts | Intraday candlestick charts (1m / 5m / 15m / 1h) with Plotly |
| 📈 Indicators | EMA, SMA, RSI, MACD, Bollinger Bands, VWAP, Supertrend |
| 🛒 Paper Trading | Buy/sell with ₹10,00,000 virtual balance at live prices |
| 💼 Portfolio | Holdings, unrealized P&L, allocation pie chart, transaction log |
| ⭐ Watchlist | Personalized watchlist with live price updates |
| 🔔 Alerts | Price above/below and RSI overbought/oversold alerts |
| 🧪 Backtester | EMA Cross & RSI Mean Revert strategy backtesting |
| 🎯 Recommendations | Stocks recommended based on your sector preferences |
| ⚙️ Preferences | Risk level, sectors, indicators, timeframes – fully customizable |
| 📥 CSV Export | Export holdings and transaction history |

---

## 📡 Data Source: yfinance

StockVibe uses **[yfinance](https://github.com/ranaroussi/yfinance)** (unofficial Yahoo Finance API).

### Ticker formats:
| Exchange | Format | Example |
|---|---|---|
| NSE | `TICKER.NS` | `RELIANCE.NS` |
| BSE | `TICKER.BO` | `RELIANCE.BO` |
| Indices | `^SYMBOL` | `^NSEI` (Nifty 50) |

### ⚠️ Rate Limit Notes:
- yfinance is an **unofficial, free API** with no authentication required
- During heavy usage, Yahoo Finance may throttle requests temporarily
- Data is cached (30 seconds for quotes, 5 minutes for fundamentals) to minimize API calls
- If you see blank charts, wait 30–60 seconds and refresh

---

## 🕐 NSE/BSE Market Hours (IST)

| Session | Time |
|---|---|
| Pre-Market | 9:00 AM – 9:15 AM |
| **Regular Market** | **9:15 AM – 3:30 PM** |
| Post-Market | 3:40 PM – 4:00 PM |
| Closed | Weekends & NSE Holidays |

The app displays a live market status indicator in the sidebar.

---

## 🔧 Configuration

### Change default virtual balance
In `database.py`, find:
```python
virtual_balance REAL DEFAULT 1000000.0,
initial_balance REAL DEFAULT 1000000.0
```
Change `1000000.0` to your desired amount.

### Add API key (future)
If you upgrade to a paid data provider (e.g., Zerodha Kite Connect, Angel One SmartAPI):
1. Create a `.env` file in the project root
2. Add: `KITE_API_KEY=your_key_here`
3. Install `python-dotenv` and load it in `analysis.py`
4. Replace `yfinance` calls with the provider's SDK

### Deployment (Streamlit Cloud)
1. Push to a GitHub repository
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your repo and set `app.py` as the entry point
4. Add SQLite path to Streamlit secrets if needed

---

## 🛠 Tech Stack

| Component | Library |
|---|---|
| Web Framework | Streamlit >= 1.32 |
| Stock Data | yfinance >= 0.2.37 |
| Charts | Plotly >= 5.18 |
| Technical Analysis | Custom (pandas-based, no TA-Lib needed) |
| Database | SQLite3 (built-in Python) |
| Data Processing | pandas, numpy |

---

## ⚠️ Disclaimer

> StockVibe is built for **educational and paper trading purposes only**.  
> It is **not financial advice**. All trades are **virtual/simulated**.  
> Never invest real money based solely on this tool.  
> Past performance of any backtested strategy does not guarantee future results.

---

## 🙏 Credits

Built with ❤️ using Python, Streamlit, yfinance, and Plotly.  
Designed for retail traders in Kerala, India 🇮🇳 and the broader NSE/BSE market.
