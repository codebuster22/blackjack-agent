"""
User management service for blackjack game.
Handles user creation, balance operations, and session management.
"""

import uuid
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor

from .models import User, Session, Round
from config import get_config

logger = logging.getLogger(__name__)

class UserManager:
    """
    Manages user operations including creation, balance management, and sessions.
    """
    
    def __init__(self, db_service):
        self.db_service = db_service
    
    def create_user_if_not_exists(self, username: str) -> str:
        """
        Create user if not exists, return user_id.
        
        Args:
            username: The username for the user
            
        Returns:
            str: The user_id (existing or newly created)
            
        Raises:
            ValueError: If username is invalid
        """
        try:
            # Check if user exists
            existing_user = self._get_user_by_username(username)
            if existing_user:
                return existing_user['user_id']
            
            # Create new user
            with self.db_service.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO users (username, current_balance)
                        VALUES (%s, %s)
                        RETURNING user_id
                    """, (username, get_config().game.starting_chips))
                    
                    user_id = cursor.fetchone()[0]
                    conn.commit()
                    
                    logger.info(f"Created new user: {username} with ID: {user_id}")
                    return str(user_id)
                    
        except Exception as e:
            logger.error(f"Failed to create user {username}: {e}")
            raise ValueError(f"Failed to create user: {e}")
    
    def get_user_balance(self, user_id: str) -> float:
        """
        Get current user balance.
        
        Args:
            user_id: The user ID
            
        Returns:
            float: Current balance
            
        Raises:
            ValueError: If user not found
        """
        try:
            with self.db_service.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT current_balance FROM users WHERE user_id = %s
                    """, (user_id,))
                    
                    result = cursor.fetchone()
                    if not result:
                        raise ValueError(f"User not found: {user_id}")
                    
                    return float(result[0])
                    
        except Exception as e:
            logger.error(f"Failed to get balance for user {user_id}: {e}")
            raise ValueError(f"Failed to get user balance: {e}")
    
    def debit_user_balance(self, user_id: str, amount: float) -> bool:
        """
        Debit user balance atomically using PostgreSQL function.
        
        Args:
            user_id: The user ID
            amount: Amount to debit
            
        Returns:
            bool: True if successful, False if insufficient balance
        """
        if amount <= 0:
            raise ValueError("Amount to debit must be greater than 0")
        
        try:
            with self.db_service.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT debit_user_balance(%s, %s)
                    """, (user_id, amount))
                    
                    result = cursor.fetchone()[0]
                    conn.commit()
                    
                    if result:
                        logger.info(f"Debited {amount} from user {user_id}")
                    else:
                        logger.warning(f"Insufficient balance for user {user_id} to debit {amount}")
                    
                    return bool(result)
                    
        except Exception as e:
            logger.error(f"Failed to debit balance for user {user_id}: {e}")
            return False
    
    def credit_user_balance(self, user_id: str, amount: float) -> bool:
        """
        Credit user balance atomically using PostgreSQL function.
        
        Args:
            user_id: The user ID
            amount: Amount to credit
            
        Returns:
            bool: True if successful, False if failed
        """
        if amount <= 0:
            raise ValueError("Amount to credit must be greater than 0")

        try:
            with self.db_service.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT credit_user_balance(%s, %s)
                    """, (user_id, amount))
                    
                    result = cursor.fetchone()[0]
                    conn.commit()
                    
                    if result:
                        logger.info(f"Credited {amount} to user {user_id}")
                    else:
                        logger.error(f"Failed to credit {amount} to user {user_id}")
                    
                    return bool(result)
                    
        except Exception as e:
            logger.error(f"Failed to credit balance for user {user_id}: {e}")
            return False
    
    def verify_user_balance(self, user_id: str, required_amount: float) -> bool:
        """
        Verify user has sufficient balance.
        
        Args:
            user_id: The user ID
            required_amount: Required amount
            
        Returns:
            bool: True if sufficient balance, False otherwise
        """
        try:
            current_balance = self.get_user_balance(user_id)
            return current_balance >= required_amount
        except Exception as e:
            logger.error(f"Failed to verify balance for user {user_id}: {e}")
            return False
    
    def create_session(self, user_id: str) -> str:
        """
        Create new session with UUID5 for user.
        
        Args:
            user_id: The user ID
            
        Returns:
            str: The session ID
        """
        try:
            # Generate deterministic UUID5 for session
            timestamp = datetime.now().isoformat()
            namespace_uuid = uuid.uuid5(uuid.NAMESPACE_URL, "blackjack")
            session_id = str(uuid.uuid5(namespace_uuid, f"{user_id}:{timestamp}"))
            
            with self.db_service.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO sessions (session_id, user_id, status)
                        VALUES (%s, %s, 'active')
                    """, (session_id, user_id))
                    
                    conn.commit()
                    logger.info(f"Created session {session_id} for user {user_id}")
                    return session_id
                    
        except Exception as e:
            logger.error(f"Failed to create session for user {user_id}: {e}")
            raise ValueError(f"Failed to create session: {e}")
    
    def complete_session(self, session_id: str) -> bool:
        """
        Mark session as completed.
        
        Args:
            session_id: The session ID
            
        Returns:
            bool: True if successful
        """
        try:
            with self.db_service.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        UPDATE sessions SET status = 'completed' 
                        WHERE session_id = %s
                    """, (session_id,))
                    
                    conn.commit()
                    logger.info(f"Completed session {session_id}")
                    return True
                    
        except Exception as e:
            logger.error(f"Failed to complete session {session_id}: {e}")
            return False
    
    def abandon_session(self, session_id: str) -> bool:
        """
        Mark session as abandoned.
        
        Args:
            session_id: The session ID
            
        Returns:
            bool: True if successful
        """
        try:
            with self.db_service.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        UPDATE sessions SET status = 'abandoned' 
                        WHERE session_id = %s
                    """, (session_id,))
                    
                    conn.commit()
                    logger.info(f"Abandoned session {session_id}")
                    return True
                    
        except Exception as e:
            logger.error(f"Failed to abandon session {session_id}: {e}")
            return False
    
    def cleanup_abandoned_sessions(self) -> int:
        """
        Mark sessions as abandoned after 1 hour of inactivity.
        
        Returns:
            int: Number of sessions marked as abandoned
        """
        try:
            one_hour_ago = datetime.now() - timedelta(hours=1)
            
            with self.db_service.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        UPDATE sessions 
                        SET status = 'abandoned' 
                        WHERE status = 'active' 
                        AND created_at < %s
                    """, (one_hour_ago,))
                    
                    abandoned_count = cursor.rowcount
                    conn.commit()
                    
                    if abandoned_count > 0:
                        logger.info(f"Abandoned {abandoned_count} inactive sessions")
                    
                    return abandoned_count
                    
        except Exception as e:
            logger.error(f"Failed to cleanup abandoned sessions: {e}")
            return 0
    
    def _get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Get user by username.
        
        Args:
            username: The username
            
        Returns:
            Dict: User data or None if not found
        """
        try:
            with self.db_service.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute("""
                        SELECT * FROM users WHERE username = %s
                    """, (username,))
                    
                    result = cursor.fetchone()
                    return dict(result) if result else None
                    
        except Exception as e:
            logger.error(f"Failed to get user by username {username}: {e}")
            return None 