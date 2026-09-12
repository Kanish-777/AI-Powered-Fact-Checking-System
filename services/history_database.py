import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"

DATABASE_FILE = DATA_DIR / "fact_checker.db"


def get_connection():

    DATA_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    connection = sqlite3.connect(
        DATABASE_FILE
    )

    connection.row_factory = sqlite3.Row

    return connection


def initialize_database():

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS claim_history
        (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            claim TEXT NOT NULL,
            verdict TEXT NOT NULL,
            confidence REAL NOT NULL,
            explanation TEXT,
            claim_domain TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    connection.commit()
    connection.close()


def save_claim_result(
    claim,
    verdict,
    confidence,
    explanation,
    claim_domain
):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO claim_history
        (
            claim,
            verdict,
            confidence,
            explanation,
            claim_domain
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            claim,
            verdict,
            confidence,
            explanation,
            claim_domain
        )
    )

    connection.commit()

    inserted_id = cursor.lastrowid

    connection.close()

    return inserted_id


def get_claim_history(
    limit=50
):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            claim,
            verdict,
            confidence,
            explanation,
            claim_domain,
            created_at
        FROM claim_history
        ORDER BY id DESC
        LIMIT ?
        """,
        (
            limit,
        )
    )

    rows = cursor.fetchall()

    connection.close()

    return [
        dict(row)
        for row in rows
    ]


def clear_claim_history():

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        DELETE FROM claim_history
        """
    )

    connection.commit()
    connection.close()