"""FraudShield — SQLite database for transaction storage."""

import sqlite3
import json
from pathlib import Path

DB_PATH = Path("data/fraudshield.db")


def get_connection() -> sqlite3.Connection:
    """Get a SQLite connection with row factory."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db() -> None:
    """Create transactions table if not exists."""
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL NOT NULL,
            features TEXT NOT NULL DEFAULT '[]',
            fraud_probability REAL NOT NULL,
            is_fraud INTEGER NOT NULL,
            top_features TEXT NOT NULL DEFAULT '[]',
            latency_ms REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def insert_transaction(
    amount: float,
    fraud_probability: float,
    is_fraud: bool,
    latency_ms: float,
    features: list[float] | None = None,
    top_features: list[dict] | None = None,
) -> int:
    """Insert a transaction and return its ID."""
    conn = get_connection()
    cursor = conn.execute(
        """INSERT INTO transactions (amount, features, fraud_probability, is_fraud, top_features, latency_ms)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (
            amount,
            json.dumps(features or []),
            fraud_probability,
            int(is_fraud),
            json.dumps(top_features or []),
            latency_ms,
        ),
    )
    tx_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return tx_id


def get_transaction(tx_id: int) -> dict | None:
    """Get a single transaction by ID."""
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM transactions WHERE id = ?", (tx_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_transactions(limit: int = 50, offset: int = 0) -> list[dict]:
    """Get recent transactions."""
    conn = get_connection()
    rows = conn.execute(
        """SELECT * FROM transactions ORDER BY id DESC LIMIT ? OFFSET ?""",
        (limit, offset),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_stats() -> dict:
    """Get aggregate statistics."""
    conn = get_connection()
    row = conn.execute("""
        SELECT
            COUNT(*) as total_transactions,
            SUM(is_fraud) as total_fraud,
            AVG(CASE WHEN is_fraud=1 THEN fraud_probability END) as avg_fraud_prob,
            AVG(latency_ms) as avg_latency_ms
        FROM transactions
    """).fetchone()
    conn.close()

    d = dict(row)
    total = d["total_transactions"] or 0
    fraud = d["total_fraud"] or 0
    return {
        "total_transactions": total,
        "total_fraud": fraud,
        "fraud_rate": round(fraud / total, 4) if total > 0 else 0.0,
        "avg_latency_ms": round(d["avg_latency_ms"] or 0.0, 2),
    }
