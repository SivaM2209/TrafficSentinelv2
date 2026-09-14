import sqlite3
from pathlib import Path


# Location of the SQLite database
DATABASE_PATH = Path(__file__).parent / "traffic.db"


def get_connection():
    """
    Create and return a connection to the SQLite database.
    """

    connection = sqlite3.connect(DATABASE_PATH)

    # Allows rows to behave like dictionaries
    connection.row_factory = sqlite3.Row

    return connection


def create_tables():
    """
    Create the required TrafficSentinel database tables.
    """

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vehicles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_id TEXT NOT NULL,
            vehicle_type TEXT NOT NULL,
            camera_id TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    """)

    connection.commit()
    connection.close()


def add_vehicle(
    vehicle_id,
    vehicle_type,
    camera_id,
    timestamp
):
    """
    Add a vehicle record to the database.
    """

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO vehicles (
            vehicle_id,
            vehicle_type,
            camera_id,
            timestamp
        )
        VALUES (?, ?, ?, ?)
    """, (
        vehicle_id,
        vehicle_type,
        camera_id,
        timestamp
    ))

    connection.commit()
    connection.close()


def get_all_vehicles():
    """
    Return all stored vehicle records.
    """

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            vehicle_id,
            vehicle_type,
            camera_id,
            timestamp
        FROM vehicles
        ORDER BY id
    """)

    vehicles = cursor.fetchall()

    connection.close()

    return vehicles
