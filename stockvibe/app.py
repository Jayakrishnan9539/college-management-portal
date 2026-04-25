"""
app.py – StockVibe: Intraday Analyzer & Paper Trader
Main Streamlit application entry point.

Run: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import time
from datetime import datetime
import pytz

# ── Internal modules ──────────────────────────────────────────────────────────
from database import (
    init_db, register_user, login_user, get_preferences, save_preferences,
    get_balance, update_balance, reset_portfolio,
    get_holdings, upsert_holding, reduce_holding,
    log_transaction, get_transactions,
    get_watchlist, add_to_watchlist, remove_from_watchlist,
    get_alerts, add_alert, trigger_alert,
)
from analysis import (
    fetch_quote, fetch_intraday, fetch_fundamentals, fetch_multiple_quotes,
    fetch_top_movers, compute_indicators, compute_buy_sell_signals,
    build_main_chart, build_portfolio_chart, build_allocation_pie,
    simple_backtest, recommend_stocks,
)
from utils import (
    ensure_session_defaults, CUSTOM_CSS, SECTOR_STOCKS, INDEX_TICKERS,
    INDICATOR_OPTIONS, TIMEFRAME_OPTIONS, RISK_LEVELS, ALL_SECTORS,
    market_status_label, is_market_open, get_ist_now,
    fmt_currency, fmt_pct, fmt_number, color_for_change, pct_change_badge,
    normalise_ticker, get_sector_tickers,
)

# ─────────────────────────────────────────────────────────────────────────────
#  Page config (MUST be first Streamlit call)
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="StockVibe – Intraday Analyzer",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
#  Bootstrap
# ─────────────────────────────────────────────────────────────────────────────
init_db()
ensure_session_defaults()
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
#  Auth helpers
# ─────────────────────────────────────────────────────────────────────────────
def do_login(username: str, password: str):
    user = login_user(username, password)
    if user:
        st.session_state.logged_in = True
        st.session_state.user_id   = user["id"]
        st.session_state.username  = user["username"]
        st.session_state.user_name = user["name"]
        st.session_state.preferences = get_preferences(user["id"])
        st.session_state.watchlist   = get_watchlist(user["id"])
        return True
    return False


def do_logout():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    ensure_session_defaults()
    st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
#  Auth Screen (Login / Register)
# ─────────────────────────────────────────────────────────────────────────────
def show_auth_screen():
    st.markdown("""
    <div style="text-align:center; padding: 3rem 0 2rem;">
        <div class="brand-logo" style="font-size:2.8rem; margin-bottom:0.3rem;">📈 StockVibe</div>
        <div class="brand-tagline" style="font-size:0.85rem; color:#6366F1; letter-spacing:0.15em;">
            INTRADAY ANALYZER · PAPER TRADER · NSE/BSE
        </div>
        <p style="color:#94A3B8; margin-top:1rem; font-size:0.95rem;">
            Your intelligent intraday companion for Indian markets
        </p>
    </div>
    """, unsafe_allow_html=True)

    col_left, col_center, col_right = st.columns([1, 1.5, 1])
    with col_center:
        tab_login, tab_reg = st.tabs(["🔑 Login", "✨ Register"])

        with tab_login:
            st.markdown("<br>", unsafe_allow_html=True)
            username = st.text_input("Username", key="login_user", placeholder="Enter username")
            password = st.text_input("Password", type="password", key="login_pass", placeholder="Enter password")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Login →", type="primary", use_container_width=True):
                if username and password:
                    if do_login(username, password):
                        st.success(f"Welcome back, {st.session_state.user_name}! 🎉")
                        time.sleep(0.8)
                        st.rerun()
                    else:
                        st.error("Invalid credentials. Please try again.")
                else:
                    st.warning("Please enter both username and password.")
            st.markdown("""
            <div style="text-align:center; color:#94A3B8; font-size:0.8rem; margin-top:1rem;">
                Demo: username <code>demo</code> / password <code>demo123</code>
            </div>
            """, unsafe_allow_html=True)

        with tab_reg:
            st.markdown("<br>", unsafe_allow_html=True)
            reg_name = st.text_input("Full Name", key="reg_name", placeholder="Your name")
            reg_user = st.text_input("Username",  key="reg_user", placeholder="Choose a username")
            reg_email = st.text_input("Email (optional)", key="reg_email", placeholder="your@email.com")
            reg_pass = st.text_input("Password",  type="password", key="reg_pass", placeholder="Min. 6 characters")
            reg_pass2 = st.text_input("Confirm Password", type="password", key="reg_pass2", placeholder="Re-enter password")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Create Account →", type="primary", use_container_width=True):
                if not all([reg_name, reg_user, reg_pass, reg_pass2]):
                    st.warning("Please fill in all required fields.")
                elif reg_pass != reg_pass2:
                    st.error("Passwords do not match.")
                elif len(reg_pass) < 6:
                    st.error("Password must be at least 6 characters.")
                else:
                    ok, msg = register_user(reg_user, reg_pass, reg_name, reg_email)
                    if ok:
                        st.success(msg)
                        time.sleep(1)
                        if do_login(reg_user, reg_pass):
                            st.rerun()
                    else:
                        st.error(msg)

    # Feature highlights
    st.markdown("<br><br>", unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    for col, icon, title, desc in [
        (c1, "📊", "Live Charts", "Real-time candlesticks with 10+ indicators"),
        (c2, "💰", "Paper Trading", "₹10L virtual fund, zero risk"),
        (c3, "🔔", "Smart Alerts", "Price & RSI alerts, auto-refresh"),
        (c4, "🎯", "Personalised", "Your sectors, your indicators"),
    ]:
        with col:
            st.markdown(f"""
            <div class="metric-card" style="text-align:center;">
                <div style="font-size:2rem; margin-bottom:0.5rem;">{icon}</div>
                <div style="font-weight:600; margin-bottom:0.3rem;">{title}</div>
                <div style="color:#94A3B8; font-size:0.82rem;">{desc}</div>
            </div>
            """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
#  Sidebar (navigation + market status)
# ─────────────────────────────────────────────────────────────────────────────
def show_sidebar():
    with st.sidebar:
        # Branding
        st.markdown("""
        <div style="padding:1rem 0 0.5rem; text-align:center;">
            <div class="brand-logo">📈 StockVibe</div>
            <div class="brand-tagline">NSE · BSE · PAPER TRADING</div>
        </div>
        <hr>
        """, unsafe_allow_html=True)

        # Market status
        status_label, status_color = market_status_label()
        st.markdown(f"""
        <div style="text-align:center; margin-bottom:1rem;">
            <span style="background:rgba(0,0,0,0.3); border:1px solid {status_color}40;
                         color:{status_color}; padding:0.3rem 0.9rem; border-radius:100px;
                         font-size:0.78rem; font-weight:600;">
                {status_label}
            </span>
            <div style="color:#94A3B8; font-size:0.7rem; margin-top:0.4rem;">{get_ist_now()}</div>
        </div>
        """, unsafe_allow_html=True)

        # User info
        st.markdown(f"""
        <div style="background:#141D2E; border:1px solid rgba(255,255,255,0.07);
                    border-radius:10px; padding:0.8rem 1rem; margin-bottom:1rem;">
            <div style="font-weight:600;">👤 {st.session_state.user_name}</div>
            <div style="color:#94A3B8; font-size:0.78rem;">@{st.session_state.username}</div>
        </div>
        """, unsafe_allow_html=True)

        # Navigation
        st.markdown("**Navigation**")
        pages = {
            "🏠 Dashboard":       "Dashboard",
            "🔍 Stock Explorer":  "Explorer",
            "💼 Portfolio":       "Portfolio",
            "⭐ Watchlist":       "Watchlist",
            "🧪 Backtester":      "Backtester",
            "⚙️ Preferences":     "Preferences",
        }
        for label, page_name in pages.items():
            if st.button(label, key=f"nav_{page_name}", use_container_width=True):
                st.session_state.page = page_name
                st.rerun()

        st.markdown("<hr>", unsafe_allow_html=True)

        # Quick balance display
        balance = get_balance(st.session_state.user_id)
        st.markdown(f"""
        <div style="text-align:center; margin-bottom:0.8rem;">
            <div style="color:#94A3B8; font-size:0.75rem; text-transform:uppercase; letter-spacing:0.08em;">Virtual Balance</div>
            <div style="font-size:1.3rem; font-weight:700; color:#00D4AA; font-family:'JetBrains Mono',monospace;">
                {fmt_currency(balance)}
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("🚪 Logout", use_container_width=True):
            do_logout()


# ─────────────────────────────────────────────────────────────────────────────
#  Dashboard Page
# ─────────────────────────────────────────────────────────────────────────────
def page_dashboard():
    st.markdown('<div class="section-header">🏠 Dashboard</div>', unsafe_allow_html=True)

    # ── Index cards ──
    st.markdown("**📊 Market Indices**")
    index_cols = st.columns(len(INDEX_TICKERS))
    for i, (name, ticker) in enumerate(INDEX_TICKERS.items()):
        quote = fetch_quote(ticker)
        with index_cols[i]:
            if quote:
                color = color_for_change(quote["pct_change"])
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">{name}</div>
                    <div class="metric-value" style="font-size:1.3rem;">
                        {fmt_number(quote['price'])}
                    </div>
                    <div class="metric-delta" style="color:{color};">
                        {'▲' if quote['pct_change'] >= 0 else '▼'}
                        {abs(quote['change']):.1f} ({fmt_pct(quote['pct_change'])})
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""<div class="metric-card"><div class="metric-label">Loading…</div></div>""",
                            unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Portfolio summary ──
    user_id  = st.session_state.user_id
    balance  = get_balance(user_id)
    holdings = get_holdings(user_id)

    portfolio_value  = balance
    total_investment = 0
    unrealized_pnl   = 0

    if holdings:
        tickers = [h["ticker"] for h in holdings]
        quotes  = fetch_multiple_quotes(tickers)
        for h in holdings:
            q = quotes.get(h["ticker"])
            curr_price = q["price"] if q else h["avg_price"]
            curr_val   = h["quantity"] * curr_price
            inv_val    = h["quantity"] * h["avg_price"]
            portfolio_value  += curr_val
            total_investment += inv_val
            unrealized_pnl   += (curr_val - inv_val)

    prefs = st.session_state.preferences
    init_balance = prefs.get("initial_balance", 1_000_000)
    total_return_pct = (portfolio_value - init_balance) / init_balance * 100 if init_balance else 0

    st.markdown("**💼 Your Portfolio**")
    p1, p2, p3, p4 = st.columns(4)
    for col, label, value, delta in [
        (p1, "Total Value",      fmt_currency(portfolio_value), None),
        (p2, "Virtual Cash",     fmt_currency(balance), None),
        (p3, "Unrealized P&L",   fmt_currency(unrealized_pnl),
             f"{fmt_pct(unrealized_pnl/total_investment*100) if total_investment else 'N/A'}"),
        (p4, "Total Return",     fmt_pct(total_return_pct), None),
    ]:
        with col:
            color = "var(--accent)" if (delta and "-" not in delta) else "var(--red)"
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">{label}</div>
                <div class="metric-value" style="font-size:1.25rem;">{value}</div>
                {f'<div class="metric-delta" style="color:{color};">{delta}</div>' if delta else ''}
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Top Movers + Watchlist side by side ──
    col_movers, col_watch = st.columns([1.4, 1])

    with col_movers:
        st.markdown('<div class="section-header">🚀 Top Movers (NSE)</div>', unsafe_allow_html=True)
        # Use a subset of stocks to avoid rate limits
        sample_tickers = (
            ["RELIANCE.NS","TCS.NS","HDFCBANK.NS","INFY.NS","ICICIBANK.NS",
             "HINDUNILVR.NS","TATAMOTORS.NS","WIPRO.NS","SBIN.NS","SUNPHARMA.NS",
             "BHARTIARTL.NS","KOTAKBANK.NS","M&M.NS","AXISBANK.NS","MARUTI.NS"]
        )
        with st.spinner("Fetching market data…"):
            gainers, losers = fetch_top_movers(sample_tickers)

        g_col, l_col = st.columns(2)
        with g_col:
            st.markdown("**🟢 Gainers**")
            for g in gainers:
                short = g["ticker"].replace(".NS","").replace(".BO","")
                st.markdown(f"""
                <div class="ticker-card">
                    <div><div class="ticker-name">{short}</div></div>
                    <div class="ticker-price">
                        <div>₹{g['price']:,.1f}</div>
                        <div style="color:#00D4AA; font-size:0.8rem;">▲ {g['pct_change']:.2f}%</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        with l_col:
            st.markdown("**🔴 Losers**")
            for lo in losers:
                short = lo["ticker"].replace(".NS","").replace(".BO","")
                st.markdown(f"""
                <div class="ticker-card">
                    <div><div class="ticker-name">{short}</div></div>
                    <div class="ticker-price">
                        <div>₹{lo['price']:,.1f}</div>
                        <div style="color:#FF4B4B; font-size:0.8rem;">▼ {abs(lo['pct_change']):.2f}%</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    with col_watch:
        st.markdown('<div class="section-header">⭐ Watchlist</div>', unsafe_allow_html=True)
        watchlist = get_watchlist(user_id)
        if watchlist:
            wq = fetch_multiple_quotes(watchlist[:8])
            for ticker, q in wq.items():
                short = ticker.replace(".NS","").replace(".BO","")
                if q:
                    color = color_for_change(q["pct_change"])
                    st.markdown(f"""
                    <div class="ticker-card">
                        <div><div class="ticker-name">{short}</div>
                        <div class="ticker-sub">{ticker}</div></div>
                        <div class="ticker-price">
                            <div>₹{q['price']:,.1f}</div>
                            <div style="color:{color}; font-size:0.8rem;">
                                {'▲' if q['pct_change']>=0 else '▼'} {abs(q['pct_change']):.2f}%
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="color:#94A3B8; text-align:center; padding:2rem 0; font-size:0.9rem;">
                No stocks in watchlist.<br>Add stocks from the Explorer page.
            </div>
            """, unsafe_allow_html=True)

    # ── Recommended stocks ──
    if st.session_state.preferences.get("fav_sectors"):
        st.markdown('<div class="section-header">💡 Recommended For You</div>', unsafe_allow_html=True)
        with st.spinner("Analysing your preferred sectors…"):
            recs = recommend_stocks(
                st.session_state.preferences["fav_sectors"],
                st.session_state.preferences.get("risk_level", "Moderate"),
                SECTOR_STOCKS,
            )
        if recs:
            rec_cols = st.columns(min(len(recs), 3))
            for i, rec in enumerate(recs[:3]):
                short = rec["ticker"].replace(".NS","").replace(".BO","")
                with rec_cols[i]:
                    color = color_for_change(rec["ret_5d"])
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">Recommended</div>
                        <div style="font-size:1.1rem; font-weight:700; margin-bottom:0.2rem;">{short}</div>
                        <div style="font-family:'JetBrains Mono',monospace; font-size:1rem;">₹{rec['price']:,.1f}</div>
                        <div style="color:{color}; font-size:0.82rem; margin-top:0.3rem;">
                            {rec['reason']}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

    # Auto-refresh info
    if is_market_open():
        st.markdown("""
        <div style="color:#94A3B8; font-size:0.75rem; text-align:right; margin-top:1rem;">
            🔄 Data cached for 30s during market hours
        </div>
        """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
#  Stock Explorer Page
# ─────────────────────────────────────────────────────────────────────────────
def page_explorer():
    st.markdown('<div class="section-header">🔍 Stock Explorer & Intraday Analysis</div>',
                unsafe_allow_html=True)

    prefs = st.session_state.preferences
    user_id = st.session_state.user_id

    # ── Search bar ──
    search_col, tf_col, ind_col = st.columns([2.5, 1, 2])
    with search_col:
        ticker_input = st.text_input(
            "Stock Ticker",
            placeholder="e.g. RELIANCE.NS  HDFCBANK.NS  TCS.NS  INFY.BO",
            help="Add .NS for NSE, .BO for BSE. Example: RELIANCE.NS",
            label_visibility="collapsed",
        )
    with tf_col:
        tf_labels = list(TIMEFRAME_OPTIONS.keys())
        default_tf = next(
            (k for k, v in TIMEFRAME_OPTIONS.items() if v == prefs.get("timeframe", "5m")),
            "5 min"
        )
        tf_sel = st.selectbox("Timeframe", tf_labels,
                              index=tf_labels.index(default_tf) if default_tf in tf_labels else 1,
                              label_visibility="collapsed")
        interval = TIMEFRAME_OPTIONS[tf_sel]
    with ind_col:
        pref_inds = prefs.get("indicators", ["EMA9", "EMA21", "RSI", "MACD"])
        sel_inds  = st.multiselect("Indicators", INDICATOR_OPTIONS,
                                   default=[i for i in pref_inds if i in INDICATOR_OPTIONS],
                                   label_visibility="collapsed")

    if not ticker_input:
        # Show popular tickers
        st.markdown("**🔥 Popular NSE Stocks**")
        pop = ["RELIANCE.NS","TCS.NS","HDFCBANK.NS","INFY.NS","ICICIBANK.NS",
               "BHARTIARTL.NS","WIPRO.NS","SBIN.NS","TATAMOTORS.NS","SUNPHARMA.NS"]
        pop_cols = st.columns(5)
        for i, t in enumerate(pop):
            with pop_cols[i % 5]:
                short = t.replace(".NS","")
                if st.button(short, key=f"pop_{t}", use_container_width=True):
                    st.session_state["explorer_ticker"] = t
                    st.rerun()
        # Restore from session if set
        if "explorer_ticker" in st.session_state:
            ticker_input = st.session_state.pop("explorer_ticker")
        else:
            return

    ticker = normalise_ticker(ticker_input)

    # ── Fetch data ──
    with st.spinner(f"Loading {ticker}…"):
        quote = fetch_quote(ticker)
        df    = fetch_intraday(ticker, interval=interval)

    if not quote:
        st.error(f"❌ Could not fetch data for **{ticker}**. Check the ticker symbol and try again.")
        st.info("💡 Tips: Use `.NS` for NSE stocks (e.g. `RELIANCE.NS`) or `.BO` for BSE.")
        return

    # ── Quote header ──
    color = color_for_change(quote["pct_change"])
    short = ticker.replace(".NS","").replace(".BO","")
    h1, h2, h3, h4, h5 = st.columns([2, 1.2, 1, 1, 1.5])
    with h1:
        st.markdown(f"""
        <div>
            <span style="font-size:1.6rem; font-weight:800;">{short}</span>
            <span style="color:#94A3B8; font-size:0.9rem; margin-left:0.5rem;">{ticker}</span>
        </div>
        """, unsafe_allow_html=True)
    with h2:
        st.markdown(f"""
        <div style="font-family:'JetBrains Mono',monospace; font-size:1.8rem; font-weight:700;">
            ₹{quote['price']:,.2f}
        </div>
        """, unsafe_allow_html=True)
    with h3:
        st.markdown(f"""
        <div style="color:{color}; font-size:1.1rem; font-weight:600; margin-top:0.5rem;">
            {'▲' if quote['pct_change']>=0 else '▼'} {abs(quote['change']):.2f}
        </div>
        """, unsafe_allow_html=True)
    with h4:
        st.markdown(f"""
        <div style="color:{color}; font-size:1.1rem; font-weight:600; margin-top:0.5rem;">
            {fmt_pct(quote['pct_change'])}
        </div>
        """, unsafe_allow_html=True)
    with h5:
        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            if st.button("⭐ Watch", key="add_watch", use_container_width=True):
                if add_to_watchlist(user_id, ticker):
                    st.session_state.watchlist = get_watchlist(user_id)
                    st.success(f"Added {ticker} to watchlist!")
                else:
                    st.info("Already in watchlist.")
        with btn_col2:
            if st.button("🔔 Alert", key="add_alert", use_container_width=True):
                st.session_state["alert_ticker"] = ticker
                st.session_state["alert_price"]  = quote["price"]

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── Alert form (toggle) ──
    if st.session_state.get("alert_ticker") == ticker:
        with st.expander("🔔 Set Price Alert", expanded=True):
            a1, a2, a3 = st.columns([1.5, 1, 0.8])
            with a1:
                alert_type = st.selectbox("Alert Type", ["PRICE_ABOVE","PRICE_BELOW","RSI_OB","RSI_OS"])
            with a2:
                alert_val  = st.number_input("Value", value=float(quote["price"]), step=0.5)
            with a3:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("Set Alert ✓", type="primary"):
                    add_alert(user_id, ticker, alert_type, alert_val)
                    st.success("Alert set!")
                    del st.session_state["alert_ticker"]
                    st.rerun()

    # ── Chart ──
    if df is not None and not df.empty:
        df = compute_indicators(df, sel_inds)
        df = compute_buy_sell_signals(df)
        chart = build_main_chart(df, ticker, sel_inds)
        st.plotly_chart(chart, use_container_width=True)
    else:
        st.warning(f"⚠️ No intraday data for {ticker} at {tf_sel} interval. "
                   f"Market may be closed or data unavailable for this interval.")

    # ── Fundamentals + Buy/Sell ──
    fund_col, trade_col = st.columns([1.8, 1])

    with fund_col:
        st.markdown('<div class="section-header">📋 Fundamentals</div>', unsafe_allow_html=True)
        with st.spinner("Loading fundamentals…"):
            fund = fetch_fundamentals(ticker)
        if fund:
            if fund.get("Company"):
                st.markdown(f"**{fund['Company']}**")
            if fund.get("Sector") and fund.get("Industry"):
                st.markdown(f"<span style='color:#94A3B8; font-size:0.85rem;'>{fund['Sector']} → {fund['Industry']}</span>",
                            unsafe_allow_html=True)

            f_rows = {
                "Market Cap":  fmt_currency(fund.get("Market Cap")),
                "P/E Ratio":   f"{fund.get('P/E Ratio', 'N/A'):.1f}" if isinstance(fund.get("P/E Ratio"), float) else "N/A",
                "EPS":         f"₹{fund.get('EPS', 'N/A'):.2f}" if isinstance(fund.get("EPS"), float) else "N/A",
                "52W High":    f"₹{fund.get('52W High', 0):,.2f}" if fund.get("52W High") else "N/A",
                "52W Low":     f"₹{fund.get('52W Low',  0):,.2f}" if fund.get("52W Low")  else "N/A",
                "Beta":        f"{fund.get('Beta', 'N/A'):.2f}" if isinstance(fund.get("Beta"), float) else "N/A",
                "Dividend Yield": f"{fund.get('Div Yield', 0)*100:.2f}%" if fund.get("Div Yield") else "N/A",
                "Avg Volume":  f"{fund.get('Avg Volume', 0):,.0f}" if fund.get("Avg Volume") else "N/A",
            }
            rows_per_col = 4
            sub_cols = st.columns(2)
            items = list(f_rows.items())
            for ci, c in enumerate(sub_cols):
                with c:
                    chunk = items[ci*rows_per_col:(ci+1)*rows_per_col]
                    for label, val in chunk:
                        st.markdown(f"""
                        <div style="display:flex; justify-content:space-between;
                                    padding:0.4rem 0; border-bottom:1px solid rgba(255,255,255,0.05);">
                            <span style="color:#94A3B8; font-size:0.83rem;">{label}</span>
                            <span style="font-weight:600; font-size:0.9rem; font-family:'JetBrains Mono',monospace;">{val}</span>
                        </div>
                        """, unsafe_allow_html=True)
            if fund.get("Description"):
                with st.expander("About the company"):
                    st.write(fund["Description"][:600] + ("…" if len(fund.get("Description","")) > 600 else ""))

    with trade_col:
        st.markdown('<div class="section-header">🛒 Paper Trade</div>', unsafe_allow_html=True)
        current_price = quote["price"]
        balance = get_balance(user_id)

        st.markdown(f"""
        <div class="metric-card" style="margin-bottom:1rem;">
            <div class="metric-label">Available Balance</div>
            <div class="metric-value" style="font-size:1.2rem; color:#00D4AA;">{fmt_currency(balance)}</div>
        </div>
        """, unsafe_allow_html=True)

        order_tab_buy, order_tab_sell = st.tabs(["🟢 Buy", "🔴 Sell"])

        with order_tab_buy:
            buy_qty = st.number_input("Quantity (shares)", min_value=1, value=1, step=1, key="buy_qty")
            buy_total = buy_qty * current_price
            st.markdown(f"""
            <div style="padding:0.6rem 0.8rem; background:rgba(0,212,170,0.08);
                        border-radius:8px; border:1px solid rgba(0,212,170,0.2); margin-bottom:0.8rem;">
                <div style="display:flex; justify-content:space-between; font-size:0.85rem;">
                    <span style="color:#94A3B8;">Price per share</span>
                    <span style="font-family:'JetBrains Mono',monospace;">₹{current_price:,.2f}</span>
                </div>
                <div style="display:flex; justify-content:space-between; font-size:0.95rem; font-weight:700; margin-top:0.3rem;">
                    <span>Total Cost</span>
                    <span style="color:#00D4AA; font-family:'JetBrains Mono',monospace;">{fmt_currency(buy_total)}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            if st.button(f"✅ Buy {buy_qty} × {short}", type="primary", use_container_width=True, key="do_buy"):
                if buy_total > balance:
                    st.error(f"Insufficient balance! Need {fmt_currency(buy_total)}, have {fmt_currency(balance)}.")
                else:
                    upsert_holding(user_id, ticker, buy_qty, current_price)
                    update_balance(user_id, balance - buy_total)
                    log_transaction(user_id, ticker, "BUY", buy_qty, current_price)
                    st.success(f"🎉 Bought {buy_qty} shares of {short} @ ₹{current_price:,.2f}")
                    st.balloons()
                    time.sleep(0.5)
                    st.rerun()

        with order_tab_sell:
            # Check existing holdings
            all_holdings = get_holdings(user_id)
            holding = next((h for h in all_holdings if h["ticker"] == ticker), None)
            if holding:
                avail_qty = int(holding["quantity"])
                st.markdown(f"""
                <div style="color:#94A3B8; font-size:0.83rem; margin-bottom:0.5rem;">
                    You own: <strong style="color:#E2E8F0;">{avail_qty} shares</strong>
                    @ avg ₹{holding['avg_price']:,.2f}
                </div>
                """, unsafe_allow_html=True)
                sell_qty = st.number_input("Quantity to sell", min_value=1,
                                           max_value=avail_qty, value=1, step=1, key="sell_qty")
                sell_total = sell_qty * current_price
                pnl_per = current_price - holding["avg_price"]
                pnl_total = pnl_per * sell_qty
                pnl_color = "#00D4AA" if pnl_total >= 0 else "#FF4B4B"

                st.markdown(f"""
                <div style="padding:0.6rem 0.8rem; background:rgba(255,75,75,0.08);
                            border-radius:8px; border:1px solid rgba(255,75,75,0.2); margin-bottom:0.8rem;">
                    <div style="display:flex; justify-content:space-between; font-size:0.85rem;">
                        <span style="color:#94A3B8;">Total Proceeds</span>
                        <span style="font-family:'JetBrains Mono',monospace;">₹{sell_total:,.2f}</span>
                    </div>
                    <div style="display:flex; justify-content:space-between; font-size:0.85rem; margin-top:0.3rem;">
                        <span style="color:#94A3B8;">Realised P&L</span>
                        <span style="color:{pnl_color}; font-weight:700; font-family:'JetBrains Mono',monospace;">
                            {'▲' if pnl_total>=0 else '▼'} {fmt_currency(abs(pnl_total))}
                        </span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                if st.button(f"✅ Sell {sell_qty} × {short}", type="secondary", use_container_width=True, key="do_sell"):
                    if reduce_holding(user_id, ticker, sell_qty):
                        update_balance(user_id, balance + sell_total)
                        log_transaction(user_id, ticker, "SELL", sell_qty, current_price)
                        st.success(f"Sold {sell_qty} shares @ ₹{current_price:,.2f}. P&L: {fmt_currency(pnl_total)}")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error("Error executing sell order.")
            else:
                st.info(f"You don't own any shares of {short}. Buy some first!")

        # RSI alert indicator
        if df is not None and "RSI" in df.columns and not df["RSI"].dropna().empty:
            rsi_val = df["RSI"].dropna().iloc[-1]
            rsi_color = "#FF4B4B" if rsi_val > 70 else "#00D4AA" if rsi_val < 30 else "#F59E0B"
            rsi_label = "Overbought ⚠️" if rsi_val > 70 else "Oversold 📉" if rsi_val < 30 else "Neutral"
            st.markdown(f"""
            <div style="text-align:center; margin-top:1rem; padding:0.6rem;
                        background:rgba(0,0,0,0.3); border-radius:8px; border:1px solid {rsi_color}30;">
                <div style="color:#94A3B8; font-size:0.75rem;">RSI (14)</div>
                <div style="font-size:1.4rem; font-weight:700; color:{rsi_color};">{rsi_val:.1f}</div>
                <div style="font-size:0.78rem; color:{rsi_color};">{rsi_label}</div>
            </div>
            """, unsafe_allow_html=True)

    # ── Alert checker ──
    _check_alerts(user_id, ticker, quote, df)


def _check_alerts(user_id: int, ticker: str, quote: dict, df):
    """Check price alerts and show in-app toast notifications."""
    alerts = get_alerts(user_id)
    for alert in alerts:
        if alert["ticker"] != ticker:
            continue
        triggered = False
        msg = ""
        if alert["alert_type"] == "PRICE_ABOVE" and quote["price"] > alert["value"]:
            triggered = True
            msg = f"🔔 {ticker} is above ₹{alert['value']:,.2f} (current: ₹{quote['price']:,.2f})"
        elif alert["alert_type"] == "PRICE_BELOW" and quote["price"] < alert["value"]:
            triggered = True
            msg = f"🔔 {ticker} is below ₹{alert['value']:,.2f} (current: ₹{quote['price']:,.2f})"
        elif alert["alert_type"] == "RSI_OB" and df is not None and "RSI" in df.columns:
            rsi = df["RSI"].dropna().iloc[-1] if not df["RSI"].dropna().empty else 50
            if rsi > alert["value"]:
                triggered = True
                msg = f"🔔 {ticker} RSI is overbought ({rsi:.1f} > {alert['value']})"
        elif alert["alert_type"] == "RSI_OS" and df is not None and "RSI" in df.columns:
            rsi = df["RSI"].dropna().iloc[-1] if not df["RSI"].dropna().empty else 50
            if rsi < alert["value"]:
                triggered = True
                msg = f"🔔 {ticker} RSI is oversold ({rsi:.1f} < {alert['value']})"
        if triggered:
            st.toast(msg, icon="🔔")
            trigger_alert(alert["id"])


# ─────────────────────────────────────────────────────────────────────────────
#  Portfolio Page
# ─────────────────────────────────────────────────────────────────────────────
def page_portfolio():
    st.markdown('<div class="section-header">💼 Virtual Portfolio</div>', unsafe_allow_html=True)
    user_id = st.session_state.user_id

    balance  = get_balance(user_id)
    holdings = get_holdings(user_id)
    txns     = get_transactions(user_id, limit=100)

    # Compute current values
    tickers       = [h["ticker"] for h in holdings]
    quotes        = fetch_multiple_quotes(tickers) if tickers else {}
    portfolio_val = balance
    total_inv     = 0
    holdings_data = []

    for h in holdings:
        q          = quotes.get(h["ticker"])
        curr_price = q["price"] if q else h["avg_price"]
        curr_val   = h["quantity"] * curr_price
        inv_val    = h["quantity"] * h["avg_price"]
        pnl        = curr_val - inv_val
        pnl_pct    = (pnl / inv_val * 100) if inv_val else 0
        portfolio_val += curr_val
        total_inv     += inv_val
        holdings_data.append({
            "Ticker":       h["ticker"].replace(".NS","").replace(".BO",""),
            "Full Ticker":  h["ticker"],
            "Qty":          int(h["quantity"]),
            "Avg Price":    h["avg_price"],
            "Curr Price":   curr_price,
            "Invested":     inv_val,
            "Current Val":  curr_val,
            "P&L":          pnl,
            "P&L %":        pnl_pct,
        })

    # ── Summary cards ──
    prefs        = st.session_state.preferences
    init_balance = prefs.get("initial_balance", 1_000_000)
    total_pnl    = portfolio_val - init_balance
    total_pct    = (total_pnl / init_balance * 100) if init_balance else 0

    s1, s2, s3, s4, s5 = st.columns(5)
    for col, lbl, val in [
        (s1, "Portfolio Value",  fmt_currency(portfolio_val)),
        (s2, "Cash Balance",     fmt_currency(balance)),
        (s3, "Invested",         fmt_currency(total_inv)),
        (s4, "Unrealized P&L",   fmt_currency(sum(h["P&L"] for h in holdings_data))),
        (s5, "Total Return",     fmt_pct(total_pct)),
    ]:
        with col:
            val_color = "var(--accent)" if "-" not in val or "₹" in val else "var(--red)"
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">{lbl}</div>
                <div class="metric-value" style="font-size:1.15rem;">{val}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Holdings table + pie chart ──
    tab_hold, tab_txn, tab_chart = st.tabs(["📊 Holdings", "📋 Transactions", "📈 Charts"])

    with tab_hold:
        if holdings_data:
            df_hold = pd.DataFrame(holdings_data)
            display_df = df_hold[["Ticker","Qty","Avg Price","Curr Price","Invested","Current Val","P&L","P&L %"]].copy()
            display_df["Avg Price"]   = display_df["Avg Price"].apply(lambda x: f"₹{x:,.2f}")
            display_df["Curr Price"]  = display_df["Curr Price"].apply(lambda x: f"₹{x:,.2f}")
            display_df["Invested"]    = display_df["Invested"].apply(fmt_currency)
            display_df["Current Val"] = display_df["Current Val"].apply(fmt_currency)
            display_df["P&L"]         = display_df["P&L"].apply(fmt_currency)
            display_df["P&L %"]       = display_df["P&L %"].apply(fmt_pct)
            st.dataframe(display_df, use_container_width=True, hide_index=True)

            # Export button
            csv = df_hold.to_csv(index=False)
            st.download_button(
                label="📥 Export Holdings (CSV)",
                data=csv,
                file_name=f"stockvibe_holdings_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
            )
        else:
            st.markdown("""
            <div style="text-align:center; color:#94A3B8; padding:3rem;">
                No holdings yet. Start trading from the Explorer page!
            </div>
            """, unsafe_allow_html=True)

    with tab_txn:
        if txns:
            df_txn = pd.DataFrame(txns)
            df_txn["Action"] = df_txn["action"].apply(
                lambda a: "🟢 BUY" if a == "BUY" else "🔴 SELL"
            )
            df_txn["Price"]  = df_txn["price"].apply(lambda p: f"₹{p:,.2f}")
            df_txn["Total"]  = df_txn["total"].apply(fmt_currency)
            df_txn["Date"]   = pd.to_datetime(df_txn["timestamp"]).dt.strftime("%d %b %Y %H:%M")
            show_cols = ["Date","ticker","Action","quantity","Price","Total"]
            show_df   = df_txn[show_cols].rename(columns={
                "ticker": "Ticker", "quantity": "Qty"
            })
            st.dataframe(show_df, use_container_width=True, hide_index=True)

            csv_txn = df_txn[["timestamp","ticker","action","quantity","price","total"]].to_csv(index=False)
            st.download_button("📥 Export Transactions (CSV)", csv_txn,
                               f"stockvibe_transactions_{datetime.now().strftime('%Y%m%d')}.csv",
                               "text/csv")
        else:
            st.info("No transactions yet.")

    with tab_chart:
        chart_c, pie_c = st.columns([1.5, 1])
        with chart_c:
            st.markdown("**Portfolio Cash Flow**")
            pf_chart = build_portfolio_chart(txns)
            st.plotly_chart(pf_chart, use_container_width=True)
        with pie_c:
            st.markdown("**Allocation by Value**")
            pie_chart = build_allocation_pie(holdings, quotes)
            st.plotly_chart(pie_chart, use_container_width=True)

    # ── Reset portfolio ──
    st.markdown("<hr>", unsafe_allow_html=True)
    with st.expander("⚠️ Danger Zone"):
        st.warning("Resetting your portfolio will delete all holdings and transactions, and restore your virtual balance to ₹10,00,000.")
        if st.button("🔄 Reset Portfolio", type="secondary"):
            reset_portfolio(user_id)
            st.success("Portfolio reset! Your virtual balance has been restored to ₹10,00,000.")
            time.sleep(1)
            st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
#  Watchlist Page
# ─────────────────────────────────────────────────────────────────────────────
def page_watchlist():
    st.markdown('<div class="section-header">⭐ Watchlist & Alerts</div>', unsafe_allow_html=True)
    user_id   = st.session_state.user_id
    watchlist = get_watchlist(user_id)

    # ── Add to watchlist ──
    add_col, _ = st.columns([2, 3])
    with add_col:
        new_ticker = st.text_input("Add Stock to Watchlist", placeholder="e.g. WIPRO.NS",
                                   label_visibility="visible")
        if st.button("➕ Add", type="primary"):
            if new_ticker:
                t = normalise_ticker(new_ticker)
                q = fetch_quote(t)
                if q:
                    if add_to_watchlist(user_id, t):
                        st.success(f"Added {t} to watchlist!")
                        st.session_state.watchlist = get_watchlist(user_id)
                        st.rerun()
                    else:
                        st.info("Already in watchlist.")
                else:
                    st.error(f"Invalid ticker: {t}")

    st.markdown("<br>", unsafe_allow_html=True)

    if not watchlist:
        st.markdown("""
        <div style="text-align:center; color:#94A3B8; padding:3rem;">
            Your watchlist is empty. Add stocks above or from the Explorer page.
        </div>
        """, unsafe_allow_html=True)
        return

    # ── Live watchlist ──
    with st.spinner("Fetching live prices…"):
        quotes = fetch_multiple_quotes(watchlist)

    cols = st.columns(3)
    for i, ticker in enumerate(watchlist):
        q = quotes.get(ticker)
        short = ticker.replace(".NS","").replace(".BO","")
        with cols[i % 3]:
            if q:
                color = color_for_change(q["pct_change"])
                st.markdown(f"""
                <div class="ticker-card" style="flex-direction:column; align-items:flex-start;">
                    <div style="display:flex; justify-content:space-between; width:100%; align-items:flex-start;">
                        <div>
                            <div class="ticker-name" style="font-size:1.05rem;">{short}</div>
                            <div class="ticker-sub">{ticker}</div>
                        </div>
                        <div class="ticker-price">
                            <div style="font-size:1.1rem;">₹{q['price']:,.2f}</div>
                            <div style="color:{color}; font-size:0.85rem;">
                                {'▲' if q['pct_change']>=0 else '▼'} {abs(q['pct_change']):.2f}%
                            </div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                r_col, _ = st.columns([1, 3])
                with r_col:
                    if st.button("🗑 Remove", key=f"rm_{ticker}", use_container_width=True):
                        remove_from_watchlist(user_id, ticker)
                        st.session_state.watchlist = get_watchlist(user_id)
                        st.rerun()
            else:
                st.markdown(f"""
                <div class="ticker-card">
                    <div class="ticker-name">{short}</div>
                    <div class="ticker-sub">Failed to fetch</div>
                </div>
                """, unsafe_allow_html=True)

    # ── Active Alerts ──
    st.markdown('<div class="section-header" style="margin-top:2rem;">🔔 Active Alerts</div>',
                unsafe_allow_html=True)
    alerts = get_alerts(user_id)
    if alerts:
        for alert in alerts:
            type_labels = {
                "PRICE_ABOVE": "Price above",
                "PRICE_BELOW": "Price below",
                "RSI_OB":      "RSI overbought (>)",
                "RSI_OS":      "RSI oversold (<)",
            }
            st.markdown(f"""
            <div class="alert-toast">
                <strong>{alert['ticker']}</strong> –
                {type_labels.get(alert['alert_type'], alert['alert_type'])}
                <strong>{alert['value']}</strong>
                <span style="color:#94A3B8; font-size:0.78rem; margin-left:0.5rem;">
                    Set: {alert['created_at'][:16]}
                </span>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No active alerts. Set alerts from the Stock Explorer page.")


# ─────────────────────────────────────────────────────────────────────────────
#  Backtester Page
# ─────────────────────────────────────────────────────────────────────────────
def page_backtester():
    st.markdown('<div class="section-header">🧪 Strategy Backtester</div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="color:#94A3B8; font-size:0.88rem; margin-bottom:1.5rem;">
        Simulate a simple trading strategy on historical data to see how it would have performed.
        ⚠️ Past performance does not guarantee future results.
    </div>
    """, unsafe_allow_html=True)

    b1, b2, b3, b4 = st.columns([2, 1.5, 1.5, 1])
    with b1:
        bt_ticker = st.text_input("Ticker", value="RELIANCE.NS", key="bt_ticker")
    with b2:
        strategy  = st.selectbox("Strategy", ["EMA Cross", "RSI Mean Revert"])
    with b3:
        period    = st.selectbox("History Period", ["1mo","3mo","6mo","1y","2y"], index=2)
    with b4:
        st.markdown("<br>", unsafe_allow_html=True)
        run_bt = st.button("▶ Run", type="primary", use_container_width=True)

    if run_bt:
        with st.spinner(f"Running {strategy} backtest on {bt_ticker}…"):
            ticker = normalise_ticker(bt_ticker)
            result = simple_backtest(ticker, interval="1d", period=period, strategy=strategy)

        if "error" in result:
            st.error(f"Backtest failed: {result['error']}")
            return

        # ── Results summary ──
        r1, r2, r3, r4, r5 = st.columns(5)
        for col, label, val, color in [
            (r1, "Total Trades",   str(result["total_trades"]),           None),
            (r2, "Win Rate",       f"{result['win_rate']}%",              "#00D4AA" if result["win_rate"] >= 50 else "#FF4B4B"),
            (r3, "Total Return",   f"{result['total_return']:+.2f}%",     "#00D4AA" if result["total_return"] >= 0 else "#FF4B4B"),
            (r4, "Best Trade",     f"{result['best_trade']:+.2f}%",       "#00D4AA"),
            (r5, "Worst Trade",    f"{result['worst_trade']:+.2f}%",      "#FF4B4B"),
        ]:
            with col:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">{label}</div>
                    <div class="metric-value" style="font-size:1.3rem; color:{color or 'var(--text-primary)'};">{val}</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Chart with trade markers ──
        if "df" in result and result["df"] is not None:
            df_bt = result["df"].copy()
            fig = go.Figure()

            fig.add_trace(go.Scatter(
                x=df_bt.index, y=df_bt["Close"],
                mode="lines", name="Close Price",
                line=dict(color="#6366F1", width=2),
            ))

            trades = result.get("trades", [])
            buy_x  = [t["date"] for t in trades if t["type"] == "BUY"]
            buy_y  = [t["price"] for t in trades if t["type"] == "BUY"]
            sell_x = [t["date"] for t in trades if t["type"] == "SELL"]
            sell_y = [t["price"] for t in trades if t["type"] == "SELL"]

            if buy_x:
                fig.add_trace(go.Scatter(
                    x=buy_x, y=buy_y, mode="markers", name="BUY",
                    marker=dict(color="#00D4AA", size=10, symbol="triangle-up"),
                ))
            if sell_x:
                fig.add_trace(go.Scatter(
                    x=sell_x, y=sell_y, mode="markers", name="SELL",
                    marker=dict(color="#FF4B4B", size=10, symbol="triangle-down"),
                ))

            fig.update_layout(
                height=400, title=f"{strategy} – {ticker} ({period})",
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(14,18,26,0.95)",
                font=dict(color="#94A3B8"), margin=dict(l=10,r=10,t=40,b=10),
                legend=dict(bgcolor="rgba(17,24,39,0.8)", bordercolor="rgba(255,255,255,0.07)", borderwidth=1),
            )
            fig.update_xaxes(gridcolor="rgba(255,255,255,0.04)")
            fig.update_yaxes(gridcolor="rgba(255,255,255,0.04)")
            st.plotly_chart(fig, use_container_width=True)

        # ── Trade log ──
        sell_trades = [t for t in result.get("trades",[]) if t.get("type") == "SELL" and t.get("pnl") is not None]
        if sell_trades:
            df_log = pd.DataFrame(sell_trades)
            df_log["date"]  = pd.to_datetime(df_log["date"]).dt.strftime("%d %b %Y")
            df_log["pnl"]   = df_log["pnl"].apply(lambda p: f"{p:+.2f}%")
            df_log["price"] = df_log["price"].apply(lambda p: f"₹{p:,.2f}")
            st.dataframe(df_log[["date","type","price","pnl"]].rename(columns={
                "date":"Exit Date","type":"Action","price":"Exit Price","pnl":"Return"
            }), use_container_width=True, hide_index=True)


# ─────────────────────────────────────────────────────────────────────────────
#  Preferences Page
# ─────────────────────────────────────────────────────────────────────────────
def page_preferences():
    st.markdown('<div class="section-header">⚙️ Your Preferences</div>', unsafe_allow_html=True)
    user_id = st.session_state.user_id
    prefs   = st.session_state.preferences or get_preferences(user_id)

    with st.form("pref_form"):
        st.markdown("#### 🎯 Trading Profile")
        risk_level = st.radio(
            "Risk Appetite",
            RISK_LEVELS,
            index=RISK_LEVELS.index(prefs.get("risk_level", "Moderate")),
            horizontal=True,
            help="Conservative = lower volatility stocks | Aggressive = high momentum plays",
        )

        st.markdown("#### 📊 Favourite Sectors")
        fav_sectors = st.multiselect(
            "Select the sectors you want to track and get recommendations for",
            ALL_SECTORS,
            default=prefs.get("fav_sectors", ["IT", "Banking"]),
        )

        st.markdown("#### ⏱️ Preferred Timeframe")
        tf_labels   = list(TIMEFRAME_OPTIONS.keys())
        curr_tf_val = prefs.get("timeframe", "5m")
        curr_tf_lbl = next((k for k,v in TIMEFRAME_OPTIONS.items() if v==curr_tf_val), "5 min")
        timeframe_lbl = st.selectbox("Default chart timeframe",
                                     tf_labels,
                                     index=tf_labels.index(curr_tf_lbl) if curr_tf_lbl in tf_labels else 1)
        timeframe = TIMEFRAME_OPTIONS[timeframe_lbl]

        st.markdown("#### 📈 Technical Indicators")
        indicators = st.multiselect(
            "Choose your preferred indicators (these will be pre-selected in charts)",
            INDICATOR_OPTIONS,
            default=[i for i in prefs.get("indicators", ["EMA9","EMA21","RSI","MACD"])
                     if i in INDICATOR_OPTIONS],
        )

        st.markdown("#### 🔔 Alert Defaults")
        rsi_ob_threshold = st.slider("RSI Overbought threshold", 60, 90,
                                     prefs.get("alert_settings", {}).get("rsi_ob", 70))
        rsi_os_threshold = st.slider("RSI Oversold threshold", 10, 40,
                                     prefs.get("alert_settings", {}).get("rsi_os", 30))

        st.markdown("<br>", unsafe_allow_html=True)
        submitted = st.form_submit_button("💾 Save Preferences", type="primary", use_container_width=True)

    if submitted:
        new_prefs = {
            "risk_level":     risk_level,
            "fav_sectors":    fav_sectors,
            "timeframe":      timeframe,
            "indicators":     indicators,
            "alert_settings": {"rsi_ob": rsi_ob_threshold, "rsi_os": rsi_os_threshold},
            "dark_mode":      1,
        }
        save_preferences(user_id, new_prefs)
        st.session_state.preferences = get_preferences(user_id)
        st.success("✅ Preferences saved successfully!")
        time.sleep(0.5)
        st.rerun()

    # ── Account info ──
    st.markdown('<div class="section-header" style="margin-top:2rem;">👤 Account</div>',
                unsafe_allow_html=True)
    st.markdown(f"""
    <div class="metric-card" style="max-width:400px;">
        <div><strong>Name:</strong> {st.session_state.user_name}</div>
        <div style="margin-top:0.4rem;"><strong>Username:</strong> @{st.session_state.username}</div>
        <div style="margin-top:0.4rem; color:#94A3B8; font-size:0.82rem;">
            Member since your first login
        </div>
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
#  Main router
# ─────────────────────────────────────────────────────────────────────────────
def main():
    if not st.session_state.logged_in:
        show_auth_screen()
        return

    show_sidebar()

    page = st.session_state.get("page", "Dashboard")

    # Auto-refresh trigger (only during market hours for Dashboard/Watchlist)
    if is_market_open() and page in ("Dashboard", "Watchlist"):
        st_autorefresh_placeholder = st.empty()
        # We use a timer via st.experimental_rerun after 30s if needed
        # (Streamlit doesn't have built-in autorefresh without external components;
        # we embed a tiny JS snippet for a soft refresh reminder)
        st.markdown("""
        <script>
            setTimeout(function() {
                // Show a refresh notice after 30s
                var el = document.getElementById('refresh-notice');
                if(el) el.style.display = 'block';
            }, 30000);
        </script>
        """, unsafe_allow_html=True)

    if page == "Dashboard":
        page_dashboard()
    elif page == "Explorer":
        page_explorer()
    elif page == "Portfolio":
        page_portfolio()
    elif page == "Watchlist":
        page_watchlist()
    elif page == "Backtester":
        page_backtester()
    elif page == "Preferences":
        page_preferences()
    else:
        page_dashboard()

    # Footer
    st.markdown("""
    <div style="text-align:center; color:#94A3B8; font-size:0.72rem; margin-top:3rem; padding:1rem;
                border-top:1px solid rgba(255,255,255,0.05);">
        📈 StockVibe – For educational & paper trading purposes only.
        Not financial advice. NSE market hours: 9:15 AM – 3:30 PM IST (Mon–Fri).
        <br>Data powered by <strong>yfinance</strong>. Rate limits may apply outside market hours.
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
