# backend_flask/db.py
import sqlite3
import os
from flask import current_app, g

DATABASE_FILENAME = 'shopsmarter.sqlite3' # Name of your SQLite database file

def get_db_path():
    return os.path.join(current_app.root_path, DATABASE_FILENAME)

def get_db():
    if 'db' not in g:
        try:
            db_path = get_db_path()
            g.db = sqlite3.connect(
                db_path,
                detect_types=sqlite3.PARSE_DECLTYPES
            )
            g.db.row_factory = sqlite3.Row # Access columns by name
            current_app.logger.info(f"SQLite connection successful to: {db_path}")
        except sqlite3.Error as e:
            current_app.logger.error(f"Failed to connect to SQLite: {e}")
            g.db = None
    return g.db

def close_db(e=None):
    db_conn = g.pop('db', None)
    if db_conn is not None:
        db_conn.close()
        current_app.logger.info("SQLite connection closed.")

def init_db_command_logic():
    """Clear existing data and create new tables."""
    db_conn = get_db()
    if db_conn is None:
        current_app.logger.error("Cannot initialize DB: connection failed.")
        return

    schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
    try:
        with open(schema_path, 'r') as f:
            db_conn.executescript(f.read())
        db_conn.commit() # Commit after executing script
        current_app.logger.info("Initialized the SQLite database with schema.")
    except FileNotFoundError:
        current_app.logger.error(f"Schema file not found at {schema_path}. Cannot initialize DB.")
    except sqlite3.Error as e:
        current_app.logger.error(f"Error executing schema for SQLite: {e}")


def init_app(app):
    app.teardown_appcontext(close_db)
    # Automatically initialize DB if it doesn't exist on first request.
    # In production, you'd typically run a manual command.
    with app.app_context():
        db_path = get_db_path()
        if not os.path.exists(db_path):
            current_app.logger.info(f"Database file not found at {db_path}. Initializing schema...")
            # We need to get a db connection to initialize
            get_db()
            init_db_command_logic()