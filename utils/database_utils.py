import sqlite3
from typing import List, Dict, Any, Optional
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DATABASE_FILE = "ai_os_data.db"

def get_db_connection():
    """Establishes and returns a connection to the SQLite database."""
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        conn.row_factory = sqlite3.Row  # This allows accessing columns by name
        return conn
    except sqlite3.Error as e:
        logger.error(f"Database connection error: {e}")
        return None

def initialize_db():
    """Initializes the database schema if tables do not exist."""
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversation_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    sender TEXT NOT NULL,
                    message TEXT NOT NULL,
                    context TEXT
                );
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_preferences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT UNIQUE NOT NULL,
                    preference_key TEXT NOT NULL,
                    preference_value TEXT,
                    UNIQUE(user_id, preference_key)
                );
            """)
            conn.commit()
            logger.info("Database initialized successfully.")
        except sqlite3.Error as e:
            logger.error(f"Database initialization error: {e}")
        finally:
            conn.close()

def insert_conversation_message(timestamp: str, sender: str, message: str, context: Optional[str] = None) -> bool:
    """Inserts a new conversation message into the database."""
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO conversation_history (timestamp, sender, message, context) VALUES (?, ?, ?, ?)",
                (timestamp, sender, message, context)
            )
            conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Error inserting conversation message: {e}")
            return False
        finally:
            conn.close()
    return False

def get_conversation_history(limit: int = 100) -> List[Dict[str, Any]]:
    """Retrieves conversation history from the database."""
    conn = get_db_connection()
    history = []
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT timestamp, sender, message, context FROM conversation_history ORDER BY timestamp DESC LIMIT ?", (limit,))
            for row in cursor.fetchall():
                history.append(dict(row))
        except sqlite3.Error as e:
            logger.error(f"Error retrieving conversation history: {e}")
        finally:
            conn.close()
    return history

def set_user_preference(user_id: str, key: str, value: str) -> bool:
    """Sets or updates a user preference."""
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO user_preferences (user_id, preference_key, preference_value) VALUES (?, ?, ?)",
                (user_id, key, value)
            )
            conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Error setting user preference: {e}")
            return False
        finally:
            conn.close()
    return False

def get_user_preference(user_id: str, key: str) -> Optional[str]:
    """Retrieves a user preference."""
    conn = get_db_connection()
    preference_value = None
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT preference_value FROM user_preferences WHERE user_id = ? AND preference_key = ?", (user_id, key))
            row = cursor.fetchone()
            if row:
                preference_value = row['preference_value']
        except sqlite3.Error as e:
            logger.error(f"Error retrieving user preference: {e}")
        finally:
            conn.close()
    return preference_value

# Initialize the database when the module is imported
initialize_db()