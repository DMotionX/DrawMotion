import sqlite3
import os
import shutil
from datetime import datetime
from utils.paths import get_app_data_dir

class DBService:
    def __init__(self, db_filename="local_db.sqlite"):
        app_data_dir = get_app_data_dir()
        self.db_path = os.path.join(app_data_dir, db_filename)
        self._init_db()
        
    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS uploads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL,
                    filepath TEXT NOT NULL,
                    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS scene_audio (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scene_index INTEGER NOT NULL,
                    track_type TEXT NOT NULL, 
                    filepath TEXT NOT NULL,
                    start_time REAL DEFAULT 0.0,
                    duration REAL DEFAULT 0.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()

    def get_scene_audio(self, scene_index: int):
        """Returns a list of dicts representing audio tracks for a specific scene"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM scene_audio WHERE scene_index = ? ORDER BY start_time ASC', (scene_index,))
            return [dict(row) for row in cursor.fetchall()]

    def add_audio_track(self, scene_index: int, track_type: str, filepath: str, start_time: float, duration: float) -> dict:
        """Adds a new audio track to a scene in the DB."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO scene_audio (scene_index, track_type, filepath, start_time, duration) 
                VALUES (?, ?, ?, ?, ?)
            ''', (scene_index, track_type, filepath, start_time, duration))
            conn.commit()
            
            cursor.execute('SELECT * FROM scene_audio WHERE id = ?', (cursor.lastrowid,))
            return dict(cursor.fetchone())

    def get_all_uploads(self):
        """Returns a list of dicts representing uploaded images"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM uploads ORDER BY upload_date DESC')
            return [dict(row) for row in cursor.fetchall()]

    def add_upload(self, original_path: str) -> dict:
        """Copies file to AppData/uploads and adds it to the DB. Returns the DB record."""
        app_data_dir = get_app_data_dir()
        uploads_dir = os.path.join(app_data_dir, "uploads")
        os.makedirs(uploads_dir, exist_ok=True)
        
        filename = os.path.basename(original_path)
        # Handle duplicate filenames by prepending timestamp
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        unique_filename = f"{timestamp}_{filename}"
        
        dest_path = os.path.join(uploads_dir, unique_filename)
        shutil.copy2(original_path, dest_path)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('INSERT INTO uploads (filename, filepath) VALUES (?, ?)', 
                           (filename, dest_path))
            conn.commit()
            
            cursor.execute('SELECT * FROM uploads WHERE id = ?', (cursor.lastrowid,))
            return dict(cursor.fetchone())

    def delete_upload(self, upload_id: int):
        """Deletes upload from DB and removes the file"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT filepath FROM uploads WHERE id = ?', (upload_id,))
            row = cursor.fetchone()
            if row:
                filepath = row[0]
                if os.path.exists(filepath):
                    try:
                        os.remove(filepath)
                    except Exception as e:
                        print(f"Failed to delete file {filepath}: {e}")
                cursor.execute('DELETE FROM uploads WHERE id = ?', (upload_id,))
                conn.commit()
