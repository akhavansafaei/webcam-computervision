# File: src\database.py
"""
Database management module for Smart Mirror
"""
import sqlite3
import json
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from src.config import DATABASE_PATH


class Database:
    """SQLite database manager for profiles and records"""
    
    def __init__(self):
        self.db_path = DATABASE_PATH
        self.connection = None
        self.init_database()
    
    def connect(self):
        """Create database connection"""
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row  # Return rows as dictionaries
        return self.connection
    
    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
    
    def init_database(self):
        """Initialize database with required tables"""
        conn = self.connect()
        cursor = conn.cursor()
        
        # Profiles table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                embedding BLOB NOT NULL,
                first_name TEXT DEFAULT 'مهمان',
                first_seen DATETIME NOT NULL,
                last_seen DATETIME NOT NULL,
                total_visits INTEGER DEFAULT 1,
                best_photo TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Records table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                profile_id INTEGER NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                age INTEGER,
                gender TEXT,
                emotion TEXT,
                emotion_scores TEXT,
                photo TEXT,
                session_duration INTEGER DEFAULT 0,
                ai_message TEXT,
                FOREIGN KEY (profile_id) REFERENCES profiles (id)
            )
        """)
        
        # Messages cache table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                profile_id INTEGER NOT NULL,
                context_hash TEXT UNIQUE,
                message TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (profile_id) REFERENCES profiles (id)
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_profiles_last_seen ON profiles(last_seen)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_records_profile ON records(profile_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_records_timestamp ON records(timestamp)")
        
        conn.commit()
        self.close()
        print("✅ Database initialized")
    
    def find_profile_by_embedding(self, embedding: np.ndarray, threshold: float = 0.60) -> Optional[Dict]:
        """
        Find existing profile by face embedding similarity
        
        Args:
            embedding: Face embedding vector (128D)
            threshold: Similarity threshold (0.0-1.0)
        
        Returns:
            Profile dict if found, None otherwise
        """
        from sklearn.metrics.pairwise import cosine_similarity
        
        conn = self.connect()
        cursor = conn.cursor()
        
        # Get all embeddings
        cursor.execute("SELECT id, embedding FROM profiles")
        profiles = cursor.fetchall()
        
        if not profiles:
            self.close()
            return None
        
        # Calculate similarities
        best_match = None
        best_similarity = 0.0
        
        for profile in profiles:
            stored_embedding = np.frombuffer(profile['embedding'], dtype=np.float32)
            similarity = cosine_similarity([embedding], [stored_embedding])[0][0]
            
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = profile['id']
        
        # Check if best match exceeds threshold
        if best_similarity >= threshold:
            cursor.execute("SELECT * FROM profiles WHERE id = ?", (best_match,))
            profile = dict(cursor.fetchone())
            profile['similarity'] = best_similarity
            self.close()
            return profile
        
        self.close()
        return None
    
    def create_profile(self, embedding: np.ndarray, analysis: Dict, photo_path: str) -> int:
        """
        Create new profile
        
        Args:
            embedding: Face embedding vector
            analysis: Analysis results from DeepFace
            photo_path: Path to saved photo
        
        Returns:
            Profile ID
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        now = datetime.now()
        embedding_blob = embedding.astype(np.float32).tobytes()
        
        cursor.execute("""
            INSERT INTO profiles (embedding, first_seen, last_seen, best_photo)
            VALUES (?, ?, ?, ?)
        """, (embedding_blob, now, now, photo_path))
        
        profile_id = cursor.lastrowid
        conn.commit()
        self.close()
        
        return profile_id
    
    def update_profile(self, profile_id: int):
        """Update profile last seen and visit count"""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE profiles 
            SET last_seen = ?, total_visits = total_visits + 1
            WHERE id = ?
        """, (datetime.now(), profile_id))
        
        conn.commit()
        self.close()
    
    def add_record(self, profile_id: int, analysis: Dict, photo_path: str, ai_message: str) -> int:
        """
        Add new record for profile
        
        Args:
            profile_id: Profile ID
            analysis: Analysis results
            photo_path: Path to photo
            ai_message: Generated AI message
        
        Returns:
            Record ID
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO records 
            (profile_id, age, gender, emotion, emotion_scores, photo, ai_message)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            profile_id,
            analysis.get('age'),
            analysis.get('dominant_gender'),
            analysis.get('dominant_emotion'),
            json.dumps(analysis.get('emotion', {})),
            photo_path,
            ai_message
        ))
        
        record_id = cursor.lastrowid
        conn.commit()
        self.close()
        
        return record_id
    
    def get_profile(self, profile_id: int) -> Optional[Dict]:
        """Get profile by ID"""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM profiles WHERE id = ?", (profile_id,))
        profile = cursor.fetchone()
        
        self.close()
        
        if profile:
            return dict(profile)
        return None
    
    def get_previous_record(self, profile_id: int) -> Optional[Dict]:
        """Get most recent record for profile (excluding current session)"""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM records 
            WHERE profile_id = ? 
            ORDER BY timestamp DESC 
            LIMIT 1 OFFSET 1
        """, (profile_id,))
        
        record = cursor.fetchone()
        self.close()
        
        if record:
            return dict(record)
        return None
    
    def get_statistics(self) -> Dict:
        """Get overall statistics"""
        conn = self.connect()
        cursor = conn.cursor()
        
        # Total unique visitors
        cursor.execute("SELECT COUNT(*) as total FROM profiles")
        total_visitors = cursor.fetchone()['total']
        
        # Total visits today
        cursor.execute("""
            SELECT COUNT(*) as total FROM records 
            WHERE DATE(timestamp) = DATE('now')
        """)
        today_visits = cursor.fetchone()['total']
        
        # Most common emotion today
        cursor.execute("""
            SELECT emotion, COUNT(*) as count FROM records 
            WHERE DATE(timestamp) = DATE('now')
            GROUP BY emotion
            ORDER BY count DESC
            LIMIT 1
        """)
        top_emotion_row = cursor.fetchone()
        top_emotion = top_emotion_row['emotion'] if top_emotion_row else 'neutral'
        
        self.close()
        
        return {
            'total_visitors': total_visitors,
            'today_visits': today_visits,
            'top_emotion': top_emotion
        }
    
    def cache_message(self, profile_id: int, context_hash: str, message: str):
        """Cache AI message"""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO messages_cache (profile_id, context_hash, message)
            VALUES (?, ?, ?)
        """, (profile_id, context_hash, message))
        
        conn.commit()
        self.close()
    
    def get_cached_message(self, context_hash: str) -> Optional[str]:
        """Get cached message if exists (within 1 hour)"""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT message FROM messages_cache 
            WHERE context_hash = ? 
            AND datetime(created_at) > datetime('now', '-1 hour')
        """, (context_hash,))
        
        result = cursor.fetchone()
        self.close()
        
        if result:
            return result['message']
        return None


# Global database instance
db = Database()