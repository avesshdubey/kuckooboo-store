import os
import sqlite3
import psycopg2
import psycopg2.extras
from config import Config


class ResultWrapper:
    """
    Allows chaining:
        conn.execute(...).fetchone()
        conn.execute(...).fetchall()
    """

    def __init__(self, cursor, db_type):
        self.cursor = cursor
        self.db_type = db_type

    def fetchone(self):
        row = self.cursor.fetchone()

        if not row:
            return None

        if self.db_type == "sqlite":
            return dict(row)

        return row

    def fetchall(self):
        rows = self.cursor.fetchall()

        if self.db_type == "sqlite":
            return [dict(row) for row in rows]

        return rows


class DatabaseWrapper:
    """
    Unifies SQLite and PostgreSQL behaviour.
    Allows using:
        conn = get_db_connection()
        conn.execute(...).fetchone()
        conn.commit()
        conn.close()
    """

    def __init__(self, conn, db_type):
        self.conn = conn
        self.db_type = db_type

    def execute(self, query, params=None):

        if params is None:
            params = []

        # Convert SQLite-style ? to PostgreSQL %s
        if self.db_type == "postgres":
            query = query.replace("?", "%s")

            cursor = self.conn.cursor(
                cursor_factory=psycopg2.extras.RealDictCursor
            )
        else:
            cursor = self.conn.cursor()

        cursor.execute(query, params)

        return ResultWrapper(cursor, self.db_type)

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()


def get_db_connection():

    # ===============================
    # PostgreSQL (Production - Railway)
    # ===============================
    if Config.DB_TYPE == "postgres":

        database_url = Config.DATABASE_URI

        # Railway may provide postgres://
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
