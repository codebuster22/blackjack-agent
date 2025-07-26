"""
User management service for blackjack game.
Handles user creation, balance operations, and session management.
"""

import uuid
import logging
from typing import Optional, Dict, Any, Union
from datetime import datetime, timedelta
import psycopg
from psycopg.rows import dict_row

from .models import User, Session, Round
from config import get_config

logger = logging.getLogger(__name__)

class UserManager:
    """
    Manages user operations including creation, balance management, and sessions.
    """
    
    def __init__(self, db_service):
        self.db_service = db_service
    
    async def create_user_if_not_exists(self, username: str, wallet_service) -> str:
        """
        Create user if not exists, return username.
        Creates a wallet and registers it onchain before creating the user.
        
        Args:
            username: The username for the user
            wallet_service: WalletService instance for creating wallets
            
        Returns:
            str: The username (existing or newly created)
            
        Raises:
            ValueError: If username is invalid or wallet creation fails
        """
        try:
            # Check if user exists
            existing_user = await self._get_user_by_username(username)
            if existing_user:
                return username
            
            # Create wallet and register onchain
            logger.info(f"Creating wallet for new user: {username}")
            wallet, tx_hash = await wallet_service.register_user_onchain()
            wallet_id = wallet.get_wallet_id()
            wallet_address = wallet.get_wallet_address()
            
            logger.info(f"Wallet created for {username}: {wallet_id} at {wallet_address}")
            logger.info(f"Registration transaction: {tx_hash}")
            
            # Create new user with wallet information
            async with self.db_service.get_connection() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute("""
                        INSERT INTO users (username, privy_wallet_id, privy_wallet_address, current_balance)
                        VALUES (%s, %s, %s, %s)
                        RETURNING user_id
                    """, (username, wallet_id, wallet_address, get_config().game.starting_chips))
                    
                    result = await cursor.fetchone()
                    user_id = result[0]
                    await conn.commit()
                    
                    logger.info(f"Created new user: {username} with ID: {user_id} and wallet: {wallet_id}")
                    return username
                    
        except Exception as e:
            logger.error(f"Failed to create user {username}: {e}")
            raise ValueError(f"Failed to create user: {e}")
    
    async def _get_user_id_by_username(self, username: str) -> str:
        """
        Get user UUID by username.
        
        Args:
            username: The username
            
        Returns:
            str: The user UUID
            
        Raises:
            ValueError: If user not found
        """
        user = await self._get_user_by_username(username)
        if not user:
            raise ValueError(f"User not found: {username}")
        return str(user['user_id'])

    async def get_user_balance(self, username: str) -> float:
        """
        Get current user balance.
        
        Args:
            username: The username
            
        Returns:
            float: Current balance
            
        Raises:
            ValueError: If user not found
        """
        try:
            user_id = await self._get_user_id_by_username(username)
            async with self.db_service.get_connection() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute("""
                        SELECT current_balance FROM users WHERE user_id = %s
                    """, (user_id,))
                    
                    result = await cursor.fetchone()
                    if not result:
                        raise ValueError(f"User not found: {username}")
                    
                    return float(result[0])
                    
        except Exception as e:
            logger.error(f"Failed to get balance for user {username}: {e}")
            raise ValueError(f"Failed to get user balance: {e}")
    
    async def debit_user_balance(self, username: str, amount: float) -> bool:
        """
        Debit user balance atomically using PostgreSQL function.
        
        Args:
            username: The username
            amount: Amount to debit
            
        Returns:
            bool: True if successful, False if insufficient balance
        """
        if amount <= 0:
            raise ValueError("Amount to debit must be greater than 0")
        
        try:
            user_id = await self._get_user_id_by_username(username)
            async with self.db_service.get_connection() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute("""
                        SELECT debit_user_balance(%s::UUID, %s::DECIMAL(15,2))
                    """, (user_id, amount))
                    
                    result = await cursor.fetchone()
                    await conn.commit()
                    
                    if result[0]:
                        logger.info(f"Debited {amount} from user {username}")
                    else:
                        logger.warning(f"Insufficient balance for user {username} to debit {amount}")
                    
                    return bool(result[0])
                    
        except Exception as e:
            logger.error(f"Failed to debit balance for user {username}: {e}")
            return False
    
    async def credit_user_balance(self, username: str, amount: float) -> bool:
        """
        Credit user balance atomically using PostgreSQL function.
        
        Args:
            username: The username
            amount: Amount to credit
            
        Returns:
            bool: True if successful, False if failed
        """
        if amount <= 0:
            raise ValueError("Amount to credit must be greater than 0")

        try:
            user_id = await self._get_user_id_by_username(username)
            async with self.db_service.get_connection() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute("""
                        SELECT credit_user_balance(%s::UUID, %s::DECIMAL(15,2))
                    """, (user_id, amount))
                    
                    result = await cursor.fetchone()
                    await conn.commit()
                    
                    if result[0]:
                        logger.info(f"Credited {amount} to user {username}")
                    else:
                        logger.error(f"Failed to credit {amount} to user {username}")
                    
                    return bool(result[0])
                    
        except Exception as e:
            logger.error(f"Failed to credit balance for user {username}: {e}")
            return False
    
    async def verify_user_balance(self, username: str, required_amount: float) -> bool:
        """
        Verify user has sufficient balance.
        
        Args:
            username: The username
            required_amount: Required amount
            
        Returns:
            bool: True if sufficient balance, False otherwise
        """
        try:
            current_balance = await self.get_user_balance(username)
            return current_balance >= required_amount
        except Exception as e:
            logger.error(f"Failed to verify balance for user {username}: {e}")
            return False
    
    async def create_session(self, username: str) -> str:
        """
        Create new session with UUID5 for user.
        
        Args:
            username: The username
            
        Returns:
            str: The session ID
        """
        try:
            user_id = await self._get_user_id_by_username(username)
            
            # Generate deterministic UUID5 for session
            timestamp = datetime.now().isoformat()
            namespace_uuid = uuid.uuid5(uuid.NAMESPACE_URL, "blackjack")
            session_id = str(uuid.uuid5(namespace_uuid, f"{user_id}:{timestamp}"))
            
            async with self.db_service.get_connection() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute("""
                        INSERT INTO blackjack_sessions (session_id, user_id, status)
                        VALUES (%s, %s, 'active')
                    """, (session_id, user_id))
                    
                    await conn.commit()
                    logger.info(f"Created session {session_id} for user {username}")
                    return session_id
                    
        except Exception as e:
            logger.error(f"Failed to create session for user {username}: {e}")
            raise ValueError(f"Failed to create session: {e}")
    
    async def complete_session(self, session_id: str) -> bool:
        """
        Mark session as completed.
        
        Args:
            session_id: The session ID
            
        Returns:
            bool: True if successful
        """
        try:
            async with self.db_service.get_connection() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute("""
                        UPDATE blackjack_sessions SET status = 'completed' 
                        WHERE session_id = %s
                    """, (session_id,))
                    
                    await conn.commit()
                    logger.info(f"Completed session {session_id}")
                    return True
                    
        except Exception as e:
            logger.error(f"Failed to complete session {session_id}: {e}")
            return False
    
    async def abandon_session(self, session_id: str) -> bool:
        """
        Mark session as abandoned.
        
        Args:
            session_id: The session ID
            
        Returns:
            bool: True if successful
        """
        try:
            async with self.db_service.get_connection() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute("""
                        UPDATE blackjack_sessions SET status = 'abandoned' 
                        WHERE session_id = %s
                    """, (session_id,))
                    
                    await conn.commit()
                    logger.info(f"Abandoned session {session_id}")
                    return True
                    
        except Exception as e:
            logger.error(f"Failed to abandon session {session_id}: {e}")
            return False
    
    async def cleanup_abandoned_sessions(self) -> int:
        """
        Mark sessions as abandoned after 1 hour of inactivity.
        
        Returns:
            int: Number of sessions marked as abandoned
        """
        try:
            one_hour_ago = datetime.now() - timedelta(hours=1)
            
            async with self.db_service.get_connection() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute("""
                        UPDATE blackjack_sessions 
                        SET status = 'abandoned' 
                        WHERE status = 'active' 
                        AND created_at < %s
                    """, (one_hour_ago,))
                    
                    abandoned_count = cursor.rowcount
                    await conn.commit()
                    
                    if abandoned_count > 0:
                        logger.info(f"Abandoned {abandoned_count} inactive sessions")
                    
                    return abandoned_count
                    
        except Exception as e:
            logger.error(f"Failed to cleanup abandoned sessions: {e}")
            return 0
    
    async def get_user_wallet_info(self, identifier: Union[str, uuid.UUID]) -> Dict[str, str]:
        """
        Get wallet information by username or user_id.
        
        Args:
            identifier: Username (str) or user_id (str or UUID)
            
        Returns:
            Dict: Contains 'wallet_id' and 'wallet_address'
            
        Raises:
            ValueError: If user not found
        """
        try:
            async with self.db_service.get_connection() as conn:
                async with conn.cursor(row_factory=dict_row) as cursor:
                    # Try to find by username first, then by user_id
                    # Check if identifier looks like a UUID
                    
                    # Handle case where identifier is already a UUID object
                    if isinstance(identifier, uuid.UUID):
                        # It's already a UUID object, search by user_id
                        await cursor.execute("""
                            SELECT privy_wallet_id, privy_wallet_address 
                            FROM users 
                            WHERE user_id = %s
                        """, (identifier,))
                    else:
                        # It's a string, check if it's a UUID string or username
                        try:
                            # Try to parse as UUID string
                            uuid.UUID(identifier)
                            # It's a UUID string, search by user_id
                            await cursor.execute("""
                                SELECT privy_wallet_id, privy_wallet_address 
                                FROM users 
                                WHERE user_id = %s
                            """, (identifier,))
                        except ValueError:
                            # It's not a UUID string, search by username
                            await cursor.execute("""
                                SELECT privy_wallet_id, privy_wallet_address 
                                FROM users 
                                WHERE username = %s
                            """, (identifier,))
                    
                    result = await cursor.fetchone()
                    if not result:
                        raise ValueError(f"User not found: {identifier}")
                    
                    return {
                        'wallet_id': result['privy_wallet_id'],
                        'wallet_address': result['privy_wallet_address']
                    }
                    
        except Exception as e:
            logger.error(f"Failed to get wallet info for {identifier}: {e}")
            raise ValueError(f"Failed to get wallet info: {e}")

    async def _get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Get user by username.
        
        Args:
            username: The username
            
        Returns:
            Dict: User data or None if not found
        """
        try:
            async with self.db_service.get_connection() as conn:
                async with conn.cursor(row_factory=dict_row) as cursor:
                    await cursor.execute("""
                        SELECT * FROM users WHERE username = %s
                    """, (username,))
                    
                    result = await cursor.fetchone()
                    return dict(result) if result else None
                    
        except Exception as e:
            logger.error(f"Failed to get user by username {username}: {e}")
            return None 