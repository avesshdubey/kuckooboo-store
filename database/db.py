import os
import sqlite3
import psycopg2
import psycopg2.extras
from config import Config


class DatabaseWrapper:
    """
    Unifies SQLite and PostgreSQL behaviour.
    Allows using:
        conn = get_db_connection()
        conn.execute(...)
        conn.commit()
        conn.close()
    """

    def __init__(self, conn, db_type):
        self.conn = conn
        self.db_type = db_type

        if db_type == "postgres":
            self.cursor = conn.cursor(
                cursor_factory=psycopg2.extras.RealDictCursor
            )
        else:
            self.cursor = conn.cursor()

    def execute(self, query, params=None):

        # Convert SQLite placeholders to PostgreSQL style
        if self.db_type == "postgres":
            query = query.replace("?", "%s")

        if params:
            self.cursor.execute(query, params)
        else:
            self.cursor.execute(query)

        return self.cursor

    def commit(self):
        self.conn.commit()

    def close(self):
        self.cursor.close()
        self.conn.close()


def get_db_connection():

    # ===============================
    # PostgreSQL (Production - Railway)
    # ===============================
    if Config.DB_TYPE == "postgres":

        database_url = Config.DATABASE_URI

        # Railway sometimes provides postgres:// instead of postgresql://
        if database_url.startswith("postgres://"):
            database_url = database_url.replace(
                "postgres://", "postgresql://", 1
            )

        conn = psycopg2.connect(database_url)
        conn.autocommit = False

        return DatabaseWrapper(conn, "postgres")

    # ===============================
    # SQLite (Local Development)
    # ===============================
    else:
        os.makedirs(os.path.dirname(Config.DATABASE_URI), exist_ok=True)

        conn = sqlite3.connect(Config.DATABASE_URI)
        conn.row_factory = sqlite3.Row

        return DatabaseWrapper(conn, "sqlite")
