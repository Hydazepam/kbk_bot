import psycopg2
from contextlib import contextmanager
from config import DB_URL

@contextmanager
def get_db_connection():
    conn = psycopg2.connect(DB_URL)
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id SERIAL PRIMARY KEY,
                    original_text TEXT,
                    reply_text TEXT,
                    user_id INTEGER,
                    message_date TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS authorized_users (
                    user_id INTEGER PRIMARY KEY,
                    username VARCHAR(255)
                );
            """)
            conn.commit()

def save_message(original_text, reply_text, user_id):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO messages (original_text, reply_text, user_id, message_date)
                VALUES (%s, %s, %s, NOW())
            """, (original_text, reply_text, user_id))
            conn.commit()

def get_user_messages(user_id):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT original_text, reply_text, message_date 
                FROM messages 
                WHERE user_id = %s
            """, (user_id,))
            return cur.fetchall()

def is_user_authorized(user_id):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 1 FROM authorized_users 
                WHERE user_id = %s
            """, (user_id,))
            return cur.fetchone() is not None