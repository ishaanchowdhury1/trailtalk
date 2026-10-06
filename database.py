import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "trailtalk.db")

def get_connection():
    """Get database connection with row factory set to sqlite3.Row."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the SQLite database schema for trail walks and sightings."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Sightings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sightings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            species_name TEXT NOT NULL,
            category TEXT NOT NULL,
            confidence TEXT,
            fun_fact TEXT,
            location_note TEXT,
            image_path TEXT,
            audio_path TEXT,
            ai_model_used TEXT,
            notes TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

def add_sighting(species_name, category, fun_fact, location_note="", image_path=None, audio_path=None, confidence="High", ai_model_used="Gemma 3 Vision", notes=""):
    """Insert a new sighting record into the database."""
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    cursor.execute('''
        INSERT INTO sightings (timestamp, species_name, category, confidence, fun_fact, location_note, image_path, audio_path, ai_model_used, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (now, species_name, category, confidence, fun_fact, location_note, image_path, audio_path, ai_model_used, notes))
    
    conn.commit()
    conn.close()

def get_all_sightings():
    """Retrieve all sightings ordered by newest first as list of dicts."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sightings ORDER BY timestamp DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_stats():
    """Calculate summary statistics for the trail walk."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM sightings")
    total_sightings = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(DISTINCT species_name) FROM sightings")
    unique_species = cursor.fetchone()[0]
    
    cursor.execute("SELECT category, COUNT(*) FROM sightings GROUP BY category ORDER BY COUNT(*) DESC")
    category_counts = cursor.fetchall()
    
    conn.close()
    
    return {
        "total": total_sightings,
        "unique": unique_species,
        "categories": dict(category_counts)
    }

def delete_sighting(sighting_id):
    """Delete a sighting by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM sightings WHERE id = ?", (sighting_id,))
    conn.commit()
    conn.close()

def clear_all_sightings():
    """Clear all records from database."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM sightings")
    conn.commit()
    conn.close()
