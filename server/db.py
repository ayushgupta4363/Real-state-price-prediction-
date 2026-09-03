import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "users.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Create table if not present
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT,
            auth_provider TEXT DEFAULT 'local',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()

    # 2. Add auth_provider column if upgrading an existing older table
    cursor.execute("PRAGMA table_info(users)")
    columns = [col[1] for col in cursor.fetchall()]
    if "auth_provider" not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN auth_provider TEXT DEFAULT 'local'")
        conn.commit()

    conn.close()

def get_user_by_email(email: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT email, password_hash, auth_provider FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    conn.close()
    return user

def register_user(email: str, password_hash: str = None, provider: str = 'local') -> bool:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (email, password_hash, auth_provider) VALUES (?, ?, ?)",
            (email, password_hash, provider)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()