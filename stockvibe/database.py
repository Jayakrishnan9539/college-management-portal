"""
database.py – StockVibe Database Layer
Handles all SQLite operations via SQLAlchemy + raw sqlite3.
"""

import sqlite3
import json
import hashlib
import os
from datetime import datetime
from typing import Optional, List, Dict, Any

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "stockvibe.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)


# ─────────────────────────────────────────────
#  Connection helper
# ─────────────────────────────────────────────
def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")  # Better concurrency
    return conn


# ─────────────────────────────────────────────
#  Schema initialisation
# ─────────────────────────────────────────────
def init_db():
    """Create all tables if they do not exist."""
    conn = get_connection()
    cur = conn.cursor()

    # Users table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            username    TEXT UNIQUE NOT NULL,
            password    TEXT NOT NULL,          -- bcrypt hash
            name        TEXT NOT NULL,
            email       TEXT,
            created_at  TEXT DEFAULT (datetime('now'))
        )
    """)

    # User preferences
    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_preferences (
            user_id         INTEGER PRIMARY KEY REFERENCES users(id),
            risk_level      TEXT DEFAULT 'Moderate',
            fav_sectors     TEXT DEFAULT '[]',   -- JSON list
            timeframe       TEXT DEFAULT '5m',
            indicators      TEXT DEFAULT '["EMA9","EMA21","RSI","MACD"]',
            alert_settings  TEXT DEFAULT '{}',   -- JSON dict
            dark_mode       INTEGER DEFAULT 1,
            virtual_balance REAL DEFAULT 1000000.0,
            initial_balance REAL DEFAULT 1000000.0
        )
    """)

    # Watchlist
    cur.execute("""
        CREATE TABLE IF NOT EXISTS watchlist (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER REFERENCES users(id),
            ticker     TEXT NOT NULL,
            added_at   TEXT DEFAULT (datetime('now')),
            UNIQUE(user_id, ticker)
        )
    """)

    # Portfolio holdings
    cur.execute("""
        CREATE TABLE IF NOT EXISTS holdings (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id       INTEGER REFERENCES users(id),
            ticker        TEXT NOT NULL,
            quantity      REAL NOT NULL,
            avg_price     REAL NOT NULL,
            last_updated  TEXT DEFAULT (datetime('now')),
            UNIQUE(user_id, ticker)
        )
    """)

    # Transaction log
    cur.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER REFERENCES users(id),
            ticker      TEXT NOT NULL,
            action      TEXT NOT NULL,   -- BUY / SELL
            quantity    REAL NOT NULL,
            price       REAL NOT NULL,
            total       REAL NOT NULL,
            timestamp   TEXT DEFAULT (datetime('now'))
        )
    """)

    # Price alerts
    cur.execute("""
        CREATE TABLE IF NOT EXISTS price_alerts (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER REFERENCES users(id),
            ticker      TEXT NOT NULL,
            alert_type  TEXT NOT NULL,  -- PRICE_ABOVE / PRICE_BELOW / RSI_OB / RSI_OS
            value       REAL NOT NULL,
            triggered   INTEGER DEFAULT 0,
            created_at  TEXT DEFAULT (datetime('now'))
        )
    """)

    conn.commit()
    conn.close()


# ─────────────────────────────────────────────
#  Password utilities
# ─────────────────────────────────────────────
def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


# ─────────────────────────────────────────────
#  User Auth
# ─────────────────────────────────────────────
def register_user(username: str, password: str, name: str, email: str = "") -> tuple[bool, str]:
    """Register a new user. Returns (success, message)."""
    conn = get_connection()
    try:
        hashed = _hash_password(password)
        conn.execute(
            "INSERT INTO users (username, password, name, email) VALUES (?, ?, ?, ?)",
            (username.lower().strip(), hashed, name, email)
        )
        user = conn.execute("SELECT id FROM users WHERE username = ?", (username.lower().strip(),)).fetchone()
        conn.execute(
            "INSERT INTO user_preferences (user_id) VALUES (?)",
            (user["id"],)
        )
        conn.commit()
        return True, "Account created successfully! Please log in."
    except sqlite3.IntegrityError:
        return False, "Username already exists. Please choose another."
    finally:
        conn.close()


def login_user(username: str, password: str) -> Optional[Dict]:
    """Verify credentials and return user dict or None."""
    conn = get_connection()
    hashed = _hash_password(password)
    user = conn.execute(
        "SELECT * FROM users WHERE username = ? AND password = ?",
        (username.lower().strip(), hashed)
    ).fetchone()
    conn.close()
    return dict(user) if user else None


def get_user_by_id(user_id: int) -> Optional[Dict]:
    conn = get_connection()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return dict(user) if user else None


# ─────────────────────────────────────────────
#  Preferences
# ─────────────────────────────────────────────
def get_preferences(user_id: int) -> Dict:
    conn = get_connection()
    prefs = conn.execute(
        "SELECT * FROM user_preferences WHERE user_id = ?", (user_id,)
    ).fetchone()
    conn.close()
    if prefs:
        d = dict(prefs)
        d["fav_sectors"] = json.loads(d["fav_sectors"])
        d["indicators"] = json.loads(d["indicators"])
        d["alert_settings"] = json.loads(d["alert_settings"])
        return d
    return {}


def save_preferences(user_id: int, prefs: Dict):
    conn = get_connection()
    conn.execute("""
        INSERT INTO user_preferences
            (user_id, risk_level, fav_sectors, timeframe, indicators, alert_settings, dark_mode)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            risk_level     = excluded.risk_level,
            fav_sectors    = excluded.fav_sectors,
            timeframe      = excluded.timeframe,
            indicators     = excluded.indicators,
            alert_settings = excluded.alert_settings,
            dark_mode      = excluded.dark_mode
    """, (
        user_id,
        prefs.get("risk_level", "Moderate"),
        json.dumps(prefs.get("fav_sectors", [])),
        prefs.get("timeframe", "5m"),
        json.dumps(prefs.get("indicators", [])),
        json.dumps(prefs.get("alert_settings", {})),
        int(prefs.get("dark_mode", 1))
    ))
    conn.commit()
    conn.close()


# ─────────────────────────────────────────────
#  Virtual Balance
# ─────────────────────────────────────────────
def get_balance(user_id: int) -> float:
    conn = get_connection()
    row = conn.execute(
        "SELECT virtual_balance FROM user_preferences WHERE user_id = ?", (user_id,)
    ).fetchone()
    conn.close()
    return row["virtual_balance"] if row else 1_000_000.0


def update_balance(user_id: int, new_balance: float):
    conn = get_connection()
    conn.execute(
        "UPDATE user_preferences SET virtual_balance = ? WHERE user_id = ?",
        (new_balance, user_id)
    )
    conn.commit()
    conn.close()


def reset_portfolio(user_id: int):
    """Reset virtual balance and clear all holdings & transactions."""
    conn = get_connection()
    conn.execute("UPDATE user_preferences SET virtual_balance = initial_balance WHERE user_id = ?", (user_id,))
    conn.execute("DELETE FROM holdings WHERE user_id = ?", (user_id,))
    conn.execute("DELETE FROM transactions WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()


# ─────────────────────────────────────────────
#  Holdings
# ─────────────────────────────────────────────
def get_holdings(user_id: int) -> List[Dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM holdings WHERE user_id = ? AND quantity > 0", (user_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def upsert_holding(user_id: int, ticker: str, qty: float, avg_price: float):
    conn = get_connection()
    existing = conn.execute(
        "SELECT * FROM holdings WHERE user_id = ? AND ticker = ?", (user_id, ticker)
    ).fetchone()

    if existing:
        new_qty = existing["quantity"] + qty
        new_avg = ((existing["quantity"] * existing["avg_price"]) + (qty * avg_price)) / new_qty
        conn.execute(
            "UPDATE holdings SET quantity = ?, avg_price = ?, last_updated = datetime('now') WHERE user_id = ? AND ticker = ?",
            (new_qty, new_avg, user_id, ticker)
        )
    else:
        conn.execute(
            "INSERT INTO holdings (user_id, ticker, quantity, avg_price) VALUES (?, ?, ?, ?)",
            (user_id, ticker, qty, avg_price)
        )
    conn.commit()
    conn.close()


def reduce_holding(user_id: int, ticker: str, qty: float) -> bool:
    """Reduce quantity; remove row if zero. Returns False if insufficient shares."""
    conn = get_connection()
    existing = conn.execute(
        "SELECT * FROM holdings WHERE user_id = ? AND ticker = ?", (user_id, ticker)
    ).fetchone()
    if not existing or existing["quantity"] < qty:
        conn.close()
        return False
    new_qty = existing["quantity"] - qty
    if new_qty < 0.001:
        conn.execute("DELETE FROM holdings WHERE user_id = ? AND ticker = ?", (user_id, ticker))
    else:
        conn.execute(
            "UPDATE holdings SET quantity = ?, last_updated = datetime('now') WHERE user_id = ? AND ticker = ?",
            (new_qty, user_id, ticker)
        )
    conn.commit()
    conn.close()
    return True


# ─────────────────────────────────────────────
#  Transactions
# ─────────────────────────────────────────────
def log_transaction(user_id: int, ticker: str, action: str, qty: float, price: float):
    conn = get_connection()
    conn.execute(
        "INSERT INTO transactions (user_id, ticker, action, quantity, price, total) VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, ticker, action, qty, price, qty * price)
    )
    conn.commit()
    conn.close()


def get_transactions(user_id: int, limit: int = 50) -> List[Dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM transactions WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?",
        (user_id, limit)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ─────────────────────────────────────────────
#  Watchlist
# ─────────────────────────────────────────────
def get_watchlist(user_id: int) -> List[str]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT ticker FROM watchlist WHERE user_id = ? ORDER BY added_at DESC", (user_id,)
    ).fetchall()
    conn.close()
    return [r["ticker"] for r in rows]


def add_to_watchlist(user_id: int, ticker: str) -> bool:
    conn = get_connection()
    try:
        conn.execute("INSERT INTO watchlist (user_id, ticker) VALUES (?, ?)", (user_id, ticker.upper()))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def remove_from_watchlist(user_id: int, ticker: str):
    conn = get_connection()
    conn.execute("DELETE FROM watchlist WHERE user_id = ? AND ticker = ?", (user_id, ticker.upper()))
    conn.commit()
    conn.close()


# ─────────────────────────────────────────────
#  Price Alerts
# ─────────────────────────────────────────────
def add_alert(user_id: int, ticker: str, alert_type: str, value: float):
    conn = get_connection()
    conn.execute(
        "INSERT INTO price_alerts (user_id, ticker, alert_type, value) VALUES (?, ?, ?, ?)",
        (user_id, ticker, alert_type, value)
    )
    conn.commit()
    conn.close()


def get_alerts(user_id: int) -> List[Dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM price_alerts WHERE user_id = ? AND triggered = 0", (user_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def trigger_alert(alert_id: int):
    conn = get_connection()
    conn.execute("UPDATE price_alerts SET triggered = 1 WHERE id = ?", (alert_id,))
    conn.commit()
    conn.close()
