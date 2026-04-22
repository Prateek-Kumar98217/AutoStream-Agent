"""
This module is designed a as mock interface for the lead capture functionality of the agent.
It uses SQLite database as a local placeholder, but the design is intended to be easily replaceable with a real 
backend service.
But something like SQLAlchemy or other database ORM with better integration with FastAPI would be a better 
choice for production.
"""

import sqlite3
import os

class LeadDB:
    def __init__(self, db_path:str):
        """Initialize the database with the given path"""
        self.db_path = db_path
        self.init_db()

    def init_db(self) -> None:
        """Initialize the db if not done already"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok = True)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                    CREATE TABLE IF NOT EXISTS leads(
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        email TEXT NOT NULL UNIQUE,
                        platform TEXT NOT NULL,
                        captured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """
            )
            conn.commit()

    def add_lead(self, name: str, email: str, platform:str)-> bool:
        """Add a new lead to the db, while handling duplicates"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO leads (name, email, platform) VALUES (?,?,?)", (name, email, platform)
                )
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            return False
        except Exception as e:
            print(f"Failed to add lead: {e}")
            return False

    def get_leads(self) -> list[dict]:
        """Retrieve all leads from the database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM leads")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]