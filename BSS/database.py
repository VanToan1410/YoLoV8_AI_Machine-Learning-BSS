import logging
import sqlite3
import os
import time
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "plates.db")


def get_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


@contextmanager
def db_connection():
    conn = get_db()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    with db_connection() as conn:
        conn.executescript("""
        -- Cameras / Video sources
        CREATE TABLE IF NOT EXISTS cameras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            source TEXT NOT NULL,
            location TEXT DEFAULT '',
            zone TEXT DEFAULT 'default',
            direction TEXT DEFAULT 'in' CHECK(direction IN ('in', 'out', 'both')),
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        -- Vehicles master list
        CREATE TABLE IF NOT EXISTS vehicles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            license_plate TEXT NOT NULL UNIQUE,
            vehicle_type TEXT DEFAULT 'unknown',
            owner_name TEXT DEFAULT '',
            owner_phone TEXT DEFAULT '',
            owner_company TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            total_visits INTEGER DEFAULT 0,
            first_seen REAL,
            last_seen REAL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        -- Detection events / records
        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            license_plate TEXT NOT NULL,
            vehicle_id INTEGER,
            camera_id INTEGER,
            direction TEXT DEFAULT 'in' CHECK(direction IN ('in', 'out', 'unknown')),
            confidence REAL DEFAULT 0,
            image_path TEXT DEFAULT '',
            plate_image_path TEXT DEFAULT '',
            timestamp REAL NOT NULL,
            date_str TEXT NOT NULL,
            time_str TEXT NOT NULL,
            is_matched INTEGER DEFAULT 0,
            notes TEXT DEFAULT '',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (vehicle_id) REFERENCES vehicles(id),
            FOREIGN KEY (camera_id) REFERENCES cameras(id)
        );

        -- Watchlist (VIP, Blacklist, Whitelist)
        CREATE TABLE IF NOT EXISTS watchlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            license_plate TEXT NOT NULL,
            category TEXT NOT NULL DEFAULT 'normal' CHECK(category IN ('vip', 'blacklist', 'whitelist', 'normal')),
            label TEXT DEFAULT '',
            color TEXT DEFAULT '#3b82f6',
            alert_enabled INTEGER DEFAULT 0,
            alert_sound INTEGER DEFAULT 0,
            owner_name TEXT DEFAULT '',
            owner_phone TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        -- Parking sessions (entry/exit tracking)
        CREATE TABLE IF NOT EXISTS parking_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            license_plate TEXT NOT NULL,
            vehicle_id INTEGER,
            entry_record_id INTEGER,
            exit_record_id INTEGER,
            entry_time REAL,
            exit_time REAL,
            duration_minutes REAL DEFAULT 0,
            entry_image TEXT DEFAULT '',
            exit_image TEXT DEFAULT '',
            entry_camera TEXT DEFAULT '',
            exit_camera TEXT DEFAULT '',
            status TEXT DEFAULT 'parked' CHECK(status IN ('parked', 'exited', 'unknown')),
            fee REAL DEFAULT 0,
            notes TEXT DEFAULT '',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (vehicle_id) REFERENCES vehicles(id),
            FOREIGN KEY (entry_record_id) REFERENCES records(id),
            FOREIGN KEY (exit_record_id) REFERENCES records(id)
        );

        -- System settings
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            description TEXT DEFAULT '',
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        -- Activity log
        CREATE TABLE IF NOT EXISTS activity_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action TEXT NOT NULL,
            entity_type TEXT DEFAULT '',
            entity_id INTEGER,
            details TEXT DEFAULT '',
            timestamp REAL NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        -- Indexes
        CREATE INDEX IF NOT EXISTS idx_records_plate ON records(license_plate);
        CREATE INDEX IF NOT EXISTS idx_records_timestamp ON records(timestamp);
        CREATE INDEX IF NOT EXISTS idx_records_date ON records(date_str);
        CREATE INDEX IF NOT EXISTS idx_records_vehicle ON records(vehicle_id);
        CREATE INDEX IF NOT EXISTS idx_records_camera ON records(camera_id);
        CREATE INDEX IF NOT EXISTS idx_vehicles_plate ON vehicles(license_plate);
        CREATE INDEX IF NOT EXISTS idx_watchlist_plate ON watchlist(license_plate);
        CREATE INDEX IF NOT EXISTS idx_watchlist_category ON watchlist(category);
        CREATE INDEX IF NOT EXISTS idx_parking_plate ON parking_sessions(license_plate);
        CREATE INDEX IF NOT EXISTS idx_parking_status ON parking_sessions(status);
        CREATE INDEX IF NOT EXISTS idx_activity_timestamp ON activity_log(timestamp);

        -- Default settings
        INSERT OR IGNORE INTO settings (key, value, description) VALUES
            ('site_name', 'BSS Parking Management', 'System name'),
            ('duplicate_filter_seconds', '5', 'Ignore same plate within N seconds'),
            ('confidence_threshold', '0.25', 'Min detection confidence'),
            ('auto_match_vehicle', '1', 'Auto-link detections to vehicles'),
            ('parking_fee_per_hour', '10000', 'Parking fee per hour (VND)'),
            ('timezone', 'Asia/Ho_Chi_Minh', 'System timezone'),
            ('alert_blacklist', '1', 'Alert on blacklisted vehicles'),
            ('alert_vip', '1', 'Alert on VIP vehicles'),
            ('max_fps', '15', 'Maximum processing FPS');

        -- Default camera (webcam)
        INSERT OR IGNORE INTO cameras (id, name, source, location, direction)
            VALUES (1, 'Camera 1 - Main Gate', '0', 'Cổng chính', 'in');
        """)

    logging.getLogger("bss.database").info("Database initialized")


init_db()
