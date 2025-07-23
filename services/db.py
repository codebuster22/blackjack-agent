"""
Database service for blackjack game persistence.
Handles PostgreSQL connections and operations.
"""

import os
import json
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from contextlib import contextmanager
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool

from .models import (
    USERS_TABLE_SQL, BLACKJACK_SESSIONS_TABLE_SQL, ROUNDS_TABLE_SQL, 
    DEBIT_USER_BALANCE_FUNCTION, CREDIT_USER_BALANCE_FUNCTION,
    INDEXES_SQL, User, Session, Round
)
from config import get_config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseService:
    """
    Database service for blackjack game persistence.
    Handles PostgreSQL connections and operations with graceful error handling.
    """
    
    def __init__(self):
        self.pool = None
        self._initialized = False
    
    def init_database(self, database_url: Optional[str] = None, pool_size: Optional[int] = None) -> bool:
        """
        Initialize database connection and create tables.
        
        Args:
            database_url: PostgreSQL connection string (optional, uses config if not provided)
            pool_size: Connection pool size (optional, uses config if not provided)
            
        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            # Get configuration
            config = get_config()
            
            # Use provided parameters or fall back to config
            db_url = database_url or config.database.url
            pool_size_val = pool_size or config.database.pool_size
            
            # Create connection pool
            self.pool = SimpleConnectionPool(
                minconn=1,
                maxconn=pool_size_val,
                dsn=db_url
            )
            
            # Test connection and create tables
            with self.pool.getconn() as conn:
                with conn.cursor() as cursor:
                    # Create tables
                    cursor.execute(USERS_TABLE_SQL)
                    cursor.execute(BLACKJACK_SESSIONS_TABLE_SQL)
                    cursor.execute(ROUNDS_TABLE_SQL)
                    
                    # Create PostgreSQL functions
                    cursor.execute(DEBIT_USER_BALANCE_FUNCTION)
                    cursor.execute(CREDIT_USER_BALANCE_FUNCTION)
                    
                    # Create indexes
                    for index_sql in INDEXES_SQL:
                        cursor.execute(index_sql)
                    
                    conn.commit()
            
            self._initialized = True
            logger.info("Database initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            self._initialized = False
            return False
    
    def _get_connection(self):
        """Get a connection from the pool."""
        if not self._initialized or not self.pool:
            raise RuntimeError("Database not initialized")
        return self.pool.getconn()
    
    def _return_connection(self, conn):
        """Return a connection to the pool."""
        if self.pool:
            self.pool.putconn(conn)
    
    @contextmanager
    def get_connection(self):
        """Get a connection from the pool with automatic cleanup."""
        conn = None
        try:
            conn = self._get_connection()
            yield conn
        finally:
            if conn:
                self._return_connection(conn)
    
    def create_session(self, session_id: str, user_id: str) -> bool:
        """
        Create a new session in the database.
        
        Args:
            session_id: The session ID to create
            user_id: The user ID for the session
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO blackjack_sessions (session_id, user_id, created_at, status) VALUES (%s, %s, %s, %s)",
                        (session_id, user_id, datetime.now(), 'active')
                    )
                    conn.commit()
                    logger.info(f"Session {session_id} created successfully for user {user_id}")
                    return True
                    
        except Exception as e:
            logger.error(f"Failed to create session {session_id}: {e}")
            return False
    
    def save_round(self, round_data: Dict[str, Any]) -> bool:
        """
        Save a round to the database.
        
        Args:
            round_data: Dictionary containing round information
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO rounds (
                            round_id, session_id, bet_amount,
                            player_hand, dealer_hand, player_total, dealer_total,
                            outcome, payout, chips_before, chips_after, created_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        round_data['round_id'],
                        round_data['session_id'],
                        round_data['bet_amount'],
                        round_data['player_hand'],
                        round_data['dealer_hand'],
                        round_data['player_total'],
                        round_data['dealer_total'],
                        round_data['outcome'],
                        round_data['payout'],
                        round_data['chips_before'],
                        round_data['chips_after'],
                        datetime.now()
                    ))
                    conn.commit()
                    logger.info(f"Round {round_data['round_id']} saved successfully")
                    return True
                    
        except Exception as e:
            logger.error(f"Failed to save round {round_data.get('round_id', 'unknown')}: {e}")
            return False
    
    def get_session_rounds(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Get all rounds for a session.
        
        Args:
            session_id: The session ID
            
        Returns:
            List[Dict]: List of round data dictionaries
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute("""
                        SELECT * FROM rounds 
                        WHERE session_id = %s 
                        ORDER BY created_at
                    """, (session_id,))
                    
                    rounds = []
                    for row in cursor.fetchall():
                        rounds.append(dict(row))
                    
                    return rounds
                    
        except Exception as e:
            logger.error(f"Failed to get rounds for session {session_id}: {e}")
            return []
    
    def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all sessions for a user.
        
        Args:
            user_id: The user ID
            
        Returns:
            List[Dict]: List of session data dictionaries
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute("""
                        SELECT * FROM blackjack_sessions 
                        WHERE user_id = %s 
                        ORDER BY created_at DESC
                    """, (user_id,))
                    
                    sessions = []
                    for row in cursor.fetchall():
                        sessions.append(dict(row))
                    
                    return sessions
                    
        except Exception as e:
            logger.error(f"Failed to get sessions for user {user_id}: {e}")
            return []
    
    def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """
        Get statistics for a session.
        
        Args:
            session_id: The session ID
            
        Returns:
            Dict: Session statistics
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT 
                            COUNT(*) as total_rounds,
                            SUM(CASE WHEN outcome = 'win' THEN 1 ELSE 0 END) as wins,
                            SUM(CASE WHEN outcome = 'loss' THEN 1 ELSE 0 END) as losses,
                            SUM(CASE WHEN outcome = 'push' THEN 1 ELSE 0 END) as pushes,
                            SUM(bet_amount) as total_bet,
                            SUM(payout) as total_payout
                        FROM rounds 
                        WHERE session_id = %s
                    """, (session_id,))
                    
                    row = cursor.fetchone()
                    if row:
                        return {
                            'total_rounds': row[0] or 0,
                            'wins': row[1] or 0,
                            'losses': row[2] or 0,
                            'pushes': row[3] or 0,
                            'total_bet': float(row[4] or 0),
                            'total_payout': float(row[5] or 0),
                            'win_rate': (row[1] or 0) / (row[0] or 1) if row[0] else 0
                        }
                    return {}
                    
        except Exception as e:
            logger.error(f"Failed to get stats for session {session_id}: {e}")
            return {}
    
    def update_session_status(self, session_id: str, status: str) -> bool:
        """
        Update session status.
        
        Args:
            session_id: The session ID
            status: New status ('active', 'completed', 'abandoned')
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "UPDATE blackjack_sessions SET status = %s WHERE session_id = %s",
                        (status, session_id)
                    )
                    conn.commit()
                    logger.info(f"Session {session_id} status updated to {status}")
                    return True
                    
        except Exception as e:
            logger.error(f"Failed to update session {session_id} status: {e}")
            return False
    
    def close(self):
        """Close database connections."""
        if self.pool:
            self.pool.closeall()
            self._initialized = False
            logger.info("Database connections closed")

# Global database service instance
db_service = DatabaseService()

# Global user manager instance
from .user_manager import UserManager
user_manager = UserManager(db_service)
