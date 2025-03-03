import psycopg2
from contextlib import contextmanager
from bot.config import DB_URL

conn = psycopg2.connect(
    DB_URL,
    sslmode="require"
)

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
                    original_text TEXT NOT NULL,
                    reply_text TEXT NOT NULL,
                    user_id BIGINT NOT NULL,  -- Исправлено на BIGINT
                    message_date TIMESTAMP DEFAULT NOW()
                );
                
                CREATE TABLE IF NOT EXISTS authorized_users (
                    user_id BIGINT PRIMARY KEY,  -- Исправлено на BIGINT
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

# def get_user_messages(user_id):
#     with get_db_connection() as conn:
#         with conn.cursor() as cur:
#             cur.execute("""
#                 SELECT original_text, reply_text, message_date 
#                 FROM messages 
#                 WHERE user_id = %s
#             """, (user_id,))
#             return cur.fetchall()

def get_all_messages():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT original_text, reply_text, message_date 
                FROM messages
                ORDER BY message_date DESC
            """)
            return cur.fetchall()

def is_user_authorized(user_id: int):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 1 
                FROM authorized_users 
                WHERE user_id = %s
            """, (user_id,))
            return cur.fetchone() is not None
