"""
SQLite database for tracking migration history and known states.
"""

import os
import sqlite3
from typing import List, Dict, Any, Optional
from datetime import datetime


class Database:
    """SQLite database for tracking migration history and known states."""

    def __init__(self, db_path: str = "migration/migration.db"):
        """Initialize the database."""
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        
        # Ensure the migration directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Connect to the database
        self._connect()
        
        # Create tables if they don't exist
        self._create_tables()

    def _connect(self) -> None:
        """Connect to the SQLite database."""
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

    def _create_tables(self) -> None:
        """Create database tables if they don't exist."""
        # Create migrations table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS migrations (
                id TEXT PRIMARY KEY,
                description TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                status TEXT NOT NULL
            )
        """)
        
        # Create migration_changes table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS migration_changes (
                migration_id TEXT NOT NULL,
                change_id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_type TEXT NOT NULL,
                entity_id TEXT NOT NULL,
                change_type TEXT NOT NULL,
                details TEXT,
                FOREIGN KEY (migration_id) REFERENCES migrations (id)
            )
        """)
        
        # Create known_states table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS known_states (
                entity_id TEXT PRIMARY KEY,
                entity_type TEXT NOT NULL,
                name TEXT,
                area TEXT,
                last_seen TEXT NOT NULL,
                current_state TEXT,
                attributes TEXT
            )
        """)
        
        # Create migration_history table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS migration_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                migration_id TEXT NOT NULL,
                applied_at TEXT NOT NULL,
                status TEXT NOT NULL,
                details TEXT,
                FOREIGN KEY (migration_id) REFERENCES migrations (id)
            )
        """)
        
        self.conn.commit()

    def add_migration(self, migration_id: str, description: str) -> None:
        """Add a new migration to the database."""
        timestamp = datetime.now().isoformat()
        self.cursor.execute(
            "INSERT INTO migrations (id, description, timestamp, status) VALUES (?, ?, ?, ?)",
            (migration_id, description, timestamp, "pending")
        )
        self.conn.commit()

    def update_migration_status(self, migration_id: str, status: str) -> None:
        """Update the status of a migration."""
        self.cursor.execute(
            "UPDATE migrations SET status = ? WHERE id = ?",
            (status, migration_id)
        )
        self.conn.commit()

    def add_migration_change(self, migration_id: str, entity_type: str, entity_id: str,
                             change_type: str, details: str) -> None:
        """Add a change to a migration."""
        self.cursor.execute(
            """
            INSERT INTO migration_changes (migration_id, entity_type, entity_id, change_type, details)
            VALUES (?, ?, ?, ?, ?)
            """,
            (migration_id, entity_type, entity_id, change_type, details)
        )
        self.conn.commit()

    def record_known_state(self, entity_id: str, entity_type: str, name: str = None,
                          room: str = None, current_state: str = None,
                          attributes: Dict[str, Any] = None) -> None:
        """Record a known state of an entity."""
        last_seen = datetime.now().isoformat()
        attributes_str = str(attributes) if attributes else None
        
        # Check if the entity already exists
        self.cursor.execute(
            "SELECT entity_id FROM known_states WHERE entity_id = ?",
            (entity_id,)
        )
        exists = self.cursor.fetchone() is not None
        
        if exists:
            # Update existing record
            self.cursor.execute(
                """
                UPDATE known_states
                SET entity_type = ?, name = ?, area = ?, last_seen = ?, 
                    current_state = ?, attributes = ?
                WHERE entity_id = ?
                """,
                (entity_type, name, area, last_seen, current_state, attributes_str, entity_id)
            )
        else:
            # Insert new record
            self.cursor.execute(
                """
                INSERT INTO known_states (entity_id, entity_type, name, area, last_seen, 
                                         current_state, attributes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (entity_id, entity_type, name, area, last_seen, current_state, attributes_str)
            )
        
        self.conn.commit()

    def get_known_states(self) -> List[Dict[str, Any]]:
        """Get all known states from the database."""
        self.cursor.execute("SELECT * FROM known_states")
        rows = self.cursor.fetchall()
        
        result = []
        for row in rows:
            result.append({
                "entity_id": row[0],
                "entity_type": row[1],
                "name": row[2],
                "area": row[3],
                "last_seen": row[4],
                "current_state": row[5],
                "attributes": row[6],
            })
        
        return result

    def get_migrations(self) -> List[Dict[str, Any]]:
        """Get all migrations from the database."""
        self.cursor.execute("SELECT * FROM migrations")
        rows = self.cursor.fetchall()
        
        result = []
        for row in rows:
            result.append({
                "id": row[0],
                "description": row[1],
                "timestamp": row[2],
                "status": row[3],
            })
        
        return result

    def get_migration_changes(self, migration_id: str) -> List[Dict[str, Any]]:
        """Get all changes for a specific migration."""
        self.cursor.execute(
            "SELECT * FROM migration_changes WHERE migration_id = ?",
            (migration_id,)
        )
        rows = self.cursor.fetchall()
        
        result = []
        for row in rows:
            result.append({
                "migration_id": row[0],
                "change_id": row[1],
                "entity_type": row[2],
                "entity_id": row[3],
                "change_type": row[4],
                "details": row[5],
            })
        
        return result

    def record_migration_history(self, migration_id: str, status: str,
                                 details: str = None) -> None:
        """Record the history of a migration application."""
        applied_at = datetime.now().isoformat()
        self.cursor.execute(
            """
            INSERT INTO migration_history (migration_id, applied_at, status, details)
            VALUES (?, ?, ?, ?)
            """,
            (migration_id, applied_at, status, details)
        )
        self.conn.commit()

    def close(self) -> None:
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()