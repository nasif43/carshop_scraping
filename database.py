import sqlite3
import os
from config import SQLITE_DB

def init_db():
    conn = sqlite3.connect(SQLITE_DB)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scraped_vehicles (
            vin TEXT PRIMARY KEY,
            title_price_mileage TEXT UNIQUE,
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            has_details BOOLEAN DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

def is_vin_scraped(vin):
    conn = sqlite3.connect(SQLITE_DB)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM scraped_vehicles WHERE vin = ?", (vin,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def is_duplicate(title, price, mileage):
    fingerprint = f"{title}|{price}|{mileage}"
    conn = sqlite3.connect(SQLITE_DB)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM scraped_vehicles WHERE title_price_mileage = ?", (fingerprint,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def mark_vin_scraped(vin, title="", price="", mileage="", has_details=False):
    fingerprint = f"{title}|{price}|{mileage}"
    conn = sqlite3.connect(SQLITE_DB)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO scraped_vehicles (vin, title_price_mileage, has_details)
        VALUES (?, ?, ?)
    """, (vin, fingerprint, has_details))
    conn.commit()
    conn.close()

def get_unprocessed_vins(vins):
    conn = sqlite3.connect(SQLITE_DB)
    cursor = conn.cursor()
    unprocessed = []
    for vin in vins:
        cursor.execute("SELECT has_details FROM scraped_vehicles WHERE vin = ?", (vin,))
        result = cursor.fetchone()
        if result is None or result[0] == 0:
            unprocessed.append(vin)
    conn.close()
    return unprocessed
