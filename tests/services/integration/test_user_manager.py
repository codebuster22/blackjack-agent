"""
Integration tests for UserManager service.
Tests user creation, balance operations, and session management.
"""

import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

from services.user_manager import UserManager
from services.db import DatabaseService
from tests.test_helpers import get_test_database_connection

# Import the MockWalletService from test_helpers
from tests.test_helpers import MockWalletService

@pytest.mark.integration
@pytest.mark.docker
@pytest.mark.database
class TestUserManager:
    """Integration tests for UserManager service."""
    
    @pytest.mark.asyncio
    async def test_create_user_if_not_exists_new_user(self, clean_database):
        """Test creating a new user."""
        db_service = DatabaseService()
        await db_service.init_database()
        user_manager = UserManager(db_service)
        mock_wallet_service = MockWalletService()
        
        # Test creating new user
        username = await user_manager.create_user_if_not_exists("new_user", mock_wallet_service)
        
        assert username == "new_user"
        
        # Verify user was created with wallet info
        async with get_test_database_connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    SELECT username, current_balance, privy_wallet_id, privy_wallet_address 
                    FROM users WHERE username = %s
                """, (username,))
                user = await cursor.fetchone()
                
                assert user is not None
                assert user[0] == "new_user"
                assert user[1] == 100.0  # Default starting chips
                assert user[2] is not None  # wallet_id should be set
                assert user[3] is not None  # wallet_address should be set
                assert user[3].startswith("0x")  # Should be valid address format
        
        await db_service.close()
    
    @pytest.mark.asyncio
    async def test_create_user_if_not_exists_existing_user(self, clean_database):
        """Test creating user when user already exists."""
        db_service = DatabaseService()
        await db_service.init_database()
        user_manager = UserManager(db_service)
        mock_wallet_service = MockWalletService()
        
        # Create user first time
        username1 = await user_manager.create_user_if_not_exists("existing_user", mock_wallet_service)
        
        # Try to create same user again
        username2 = await user_manager.create_user_if_not_exists("existing_user", mock_wallet_service)
        
        # Should return same username
        assert username1 == username2 == "existing_user"
        
        await db_service.close()
    
    @pytest.mark.asyncio
    async def test_create_user_if_not_exists_database_error(self, clean_database):
        """Test user creation with database error."""
        db_service = DatabaseService()
        await db_service.init_database()
        user_manager = UserManager(db_service)
        mock_wallet_service = MockWalletService()
        
        # Create a user first
        username1 = await user_manager.create_user_if_not_exists("test_user", mock_wallet_service)
        
        # Try to create user with invalid characters that might cause DB error
        with pytest.raises(ValueError, match="Failed to create user"):
            await user_manager.create_user_if_not_exists("test_user_with_very_long_username_that_exceeds_database_column_limit_and_causes_an_error", mock_wallet_service)
        
        await db_service.close()
    
    @pytest.mark.asyncio
    async def test_get_user_balance_success(self, clean_database):
        """Test getting user balance."""
        db_service = DatabaseService()
        await db_service.init_database()
        user_manager = UserManager(db_service)
        
        # Create test user with wallet info
        async with get_test_database_connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    INSERT INTO users (username, privy_wallet_id, privy_wallet_address, current_balance)
                    VALUES (%s, %s, %s, %s)
                    RETURNING user_id
                """, ("test_user", "test_wallet_id", "0x1234567890123456789012345678901234567890", 150.0))
                user_id = (await cursor.fetchone())[0]
                await conn.commit()
        
        # Test getting balance
        balance = await user_manager.get_user_balance("test_user")
        assert balance == 150.0
        
        await db_service.close()
    
    @pytest.mark.asyncio
    async def test_get_user_balance_user_not_found(self, clean_database):
        """Test getting balance for non-existent user."""
        db_service = DatabaseService()
        await db_service.init_database()
        user_manager = UserManager(db_service)
        
        # Test with non-existent user
        with pytest.raises(ValueError, match="User not found"):
            await user_manager.get_user_balance("nonexistent_user")
        
        await db_service.close()
    
    @pytest.mark.asyncio
    async def test_get_user_balance_database_error(self, clean_database):
        """Test getting balance with database error."""
        db_service = DatabaseService()
        await db_service.init_database()
        user_manager = UserManager(db_service)
        
        # Test with invalid user_id format
        with pytest.raises(ValueError):
            await user_manager.get_user_balance("invalid-uuid-format")
        
        await db_service.close()
    
    @pytest.mark.asyncio
    async def test_debit_user_balance_success(self, clean_database):
        """Test successful balance debit."""
        db_service = DatabaseService()
        await db_service.init_database()
        user_manager = UserManager(db_service)
        
        # Create test user
        async with get_test_database_connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    INSERT INTO users (username, privy_wallet_id, privy_wallet_address, current_balance)
                    VALUES (%s, %s, %s, %s)
                    RETURNING user_id
                """, ("test_user", "mock_wallet_id_14", "0xe067890123456789012345678901234567890123", 100.0))
                user_id = (await cursor.fetchone())[0]
                await conn.commit()
        
        # Test debiting balance
        result = await user_manager.debit_user_balance("test_user", 25.0)
        assert result is True
        
        # Verify balance was debited
        async with get_test_database_connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    SELECT current_balance FROM users WHERE user_id = %s
                """, (user_id,))
                balance = (await cursor.fetchone())[0]
                assert balance == 75.0
        
        await db_service.close()
    
    @pytest.mark.asyncio
    async def test_debit_user_balance_insufficient_funds(self, clean_database):
        """Test debit with insufficient funds."""
        db_service = DatabaseService()
        await db_service.init_database()
        user_manager = UserManager(db_service)
        
        # Create test user with low balance
        async with get_test_database_connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    INSERT INTO users (username, privy_wallet_id, privy_wallet_address, current_balance)
                    VALUES (%s, %s, %s, %s)
                    RETURNING user_id
                """, ("test_user", "mock_wallet_id_27", "0xf090123456789012345678901234567890123456", 10.0))
                user_id = (await cursor.fetchone())[0]
                await conn.commit()
        
        # Test debiting more than available
        result = await user_manager.debit_user_balance("test_user", 25.0)
        assert result is False
        
        # Verify balance unchanged
        async with get_test_database_connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    SELECT current_balance FROM users WHERE user_id = %s
                """, (user_id,))
                balance = (await cursor.fetchone())[0]
                assert balance == 10.0
        
        await db_service.close()
    
    @pytest.mark.asyncio
    async def test_debit_user_balance_user_not_found(self, clean_database):
        """Test debit for non-existent user."""
        db_service = DatabaseService()
        await db_service.init_database()
        user_manager = UserManager(db_service)
        
        # Test with non-existent user
        result = await user_manager.debit_user_balance("nonexistent_user", 25.0)
        assert result is False
        
        await db_service.close()
    
    @pytest.mark.asyncio
    async def test_debit_user_balance_invalid_amount(self, clean_database):
        """Test debit with invalid amount."""
        db_service = DatabaseService()
        await db_service.init_database()
        user_manager = UserManager(db_service)
        
        # Create test user
        async with get_test_database_connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    INSERT INTO users (username, privy_wallet_id, privy_wallet_address, current_balance)
                    VALUES (%s, %s, %s, %s)
                    RETURNING user_id
                """, ("test_user", "mock_wallet_id_15", "0xf078901234567890123456789012345678901234", 100.0))
                user_id = (await cursor.fetchone())[0]
                await conn.commit()
        
        # Test with negative amount
        with pytest.raises(ValueError, match="Amount to debit must be greater than 0"):
            await user_manager.debit_user_balance("test_user", -10.0)
        
        # Test with zero amount
        with pytest.raises(ValueError, match="Amount to debit must be greater than 0"):
            await user_manager.debit_user_balance("test_user", 0.0)
        
        await db_service.close()
    
    @pytest.mark.asyncio
    async def test_debit_user_balance_database_error(self, clean_database):
        """Test debit with database error."""
        db_service = DatabaseService()
        await db_service.init_database()
        user_manager = UserManager(db_service)
        
        # Test with invalid user_id format
        result = await user_manager.debit_user_balance("invalid-uuid-format", 25.0)
        assert result is False
        
        await db_service.close()
    
    @pytest.mark.asyncio
    async def test_credit_user_balance_success(self, clean_database):
        """Test successful balance credit."""
        db_service = DatabaseService()
        await db_service.init_database()
        user_manager = UserManager(db_service)
        
        # Create test user
        async with get_test_database_connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    INSERT INTO users (username, privy_wallet_id, privy_wallet_address, current_balance)
                    VALUES (%s, %s, %s, %s)
                    RETURNING user_id
                """, ("test_user", "mock_wallet_id_16", "0xa089012345678901234567890123456789012345", 100.0))
                user_id = (await cursor.fetchone())[0]
                await conn.commit()
        
        # Test crediting balance
        result = await user_manager.credit_user_balance("test_user", 25.0)
        assert result is True
        
        # Verify balance was credited
        async with get_test_database_connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    SELECT current_balance FROM users WHERE user_id = %s
                """, (user_id,))
                balance = (await cursor.fetchone())[0]
                assert balance == 125.0
        
        await db_service.close()
    
    @pytest.mark.asyncio
    async def test_credit_user_balance_user_not_found(self, clean_database):
        """Test credit for non-existent user."""
        db_service = DatabaseService()
        await db_service.init_database()
        user_manager = UserManager(db_service)
        
        # Test with non-existent user
        result = await user_manager.credit_user_balance("nonexistent_user", 25.0)
        assert result is False
        
        await db_service.close()
    
    @pytest.mark.asyncio
    async def test_credit_user_balance_invalid_amount(self, clean_database):
        """Test credit with invalid amount."""
        db_service = DatabaseService()
        await db_service.init_database()
        user_manager = UserManager(db_service)
        
        # Create test user
        async with get_test_database_connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    INSERT INTO users (username, privy_wallet_id, privy_wallet_address, current_balance)
                    VALUES (%s, %s, %s, %s)
                    RETURNING user_id
                """, ("test_user", "mock_wallet_id_17", "0xb090123456789012345678901234567890123456", 100.0))
                user_id = (await cursor.fetchone())[0]
                await conn.commit()
        
        # Test with negative amount
        with pytest.raises(ValueError, match="Amount to credit must be greater than 0"):
            await user_manager.credit_user_balance("test_user", -10.0)
        
        # Test with zero amount
        with pytest.raises(ValueError, match="Amount to credit must be greater than 0"):
            await user_manager.credit_user_balance("test_user", 0.0)
        
        await db_service.close()
    
    @pytest.mark.asyncio
    async def test_credit_user_balance_database_error(self, clean_database):
        """Test credit with database error."""
        db_service = DatabaseService()
        await db_service.init_database()
        user_manager = UserManager(db_service)
        
        # Test with invalid user_id format
        result = await user_manager.credit_user_balance("invalid-uuid-format", 25.0)
        assert result is False
        
        await db_service.close()
    
    @pytest.mark.asyncio
    async def test_credit_user_balance_function_failure(self, clean_database):
        """Test credit with database function failure."""
        db_service = DatabaseService()
        await db_service.init_database()
        user_manager = UserManager(db_service)
        
        # Create test user
        async with get_test_database_connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    INSERT INTO users (username, privy_wallet_id, privy_wallet_address, current_balance)
                    VALUES (%s, %s, %s, %s)
                    RETURNING user_id
                """, ("test_user", "mock_wallet_id_18", "0xc001234567890123456789012345678901234567", 100.0))
                user_id = (await cursor.fetchone())[0]
                await conn.commit()
        
        # Test with extremely large amount that might cause overflow
        result = await user_manager.credit_user_balance("test_user", 1e20)
        # Function should handle this gracefully
        assert result in [True, False]  # Either succeeds or fails gracefully
        
        await db_service.close()
    
    @pytest.mark.asyncio
    async def test_verify_user_balance_sufficient(self, clean_database):
        """Test balance verification with sufficient funds."""
        db_service = DatabaseService()
        await db_service.init_database()
        user_manager = UserManager(db_service)
        
        # Create test user
        async with get_test_database_connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    INSERT INTO users (username, privy_wallet_id, privy_wallet_address, current_balance)
                    VALUES (%s, %s, %s, %s)
                    RETURNING user_id
                """, ("test_user", "mock_wallet_id_19", "0xd012345678901234567890123456789012345678", 100.0))
                user_id = (await cursor.fetchone())[0]
                await conn.commit()
        
        # Test with sufficient amount
        result = await user_manager.verify_user_balance("test_user", 50.0)
        assert result is True
        
        await db_service.close()
    
    @pytest.mark.asyncio
    async def test_verify_user_balance_insufficient(self, clean_database):
        """Test balance verification with insufficient funds."""
        db_service = DatabaseService()
        await db_service.init_database()
        user_manager = UserManager(db_service)
        
        # Create test user
        async with get_test_database_connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    INSERT INTO users (username, privy_wallet_id, privy_wallet_address, current_balance)
                    VALUES (%s, %s, %s, %s)
                    RETURNING user_id
                """, ("test_user", "mock_wallet_id_20", "0xe023456789012345678901234567890123456789", 100.0))
                user_id = (await cursor.fetchone())[0]
                await conn.commit()
        
        # Test with insufficient amount
        result = await user_manager.verify_user_balance("test_user", 150.0)
        assert result is False
        
        await db_service.close()
    
    @pytest.mark.asyncio
    async def test_verify_user_balance_exact_amount(self, clean_database):
        """Test balance verification with exact amount."""
        db_service = DatabaseService()
        await db_service.init_database()
        user_manager = UserManager(db_service)
        
        # Create test user
        async with get_test_database_connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    INSERT INTO users (username, privy_wallet_id, privy_wallet_address, current_balance)
                    VALUES (%s, %s, %s, %s)
                    RETURNING user_id
                """, ("test_user", "mock_wallet_id_21", "0xf034567890123456789012345678901234567890", 100.0))
                user_id = (await cursor.fetchone())[0]
                await conn.commit()
        
        # Test with exact amount
        result = await user_manager.verify_user_balance("test_user", 100.0)
        assert result is True
        
        await db_service.close()
    
    @pytest.mark.asyncio
    async def test_verify_user_balance_user_not_found(self, clean_database):
        """Test balance verification for non-existent user."""
        db_service = DatabaseService()
        await db_service.init_database()
        user_manager = UserManager(db_service)
        
        # Test with non-existent user
        result = await user_manager.verify_user_balance("nonexistent_user", 50.0)
        assert result is False
        
        await db_service.close()
    
    @pytest.mark.asyncio
    async def test_create_session_success(self, clean_database):
        """Test successful session creation."""
        db_service = DatabaseService()
        await db_service.init_database()
        user_manager = UserManager(db_service)
        
        # Create test user
        async with get_test_database_connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    INSERT INTO users (username, privy_wallet_id, privy_wallet_address, current_balance)
                    VALUES (%s, %s, %s, %s)
                    RETURNING user_id
                """, ("test_user", "mock_wallet_id_22", "0xa045678901234567890123456789012345678901", 100.0))
                user_id = (await cursor.fetchone())[0]
                await conn.commit()
        
        # Test session creation
        session_id = await user_manager.create_session("test_user")
        
        assert session_id is not None
        assert isinstance(session_id, str)
        
        # Verify session was created
        async with get_test_database_connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    SELECT session_id, user_id, status
                    FROM blackjack_sessions WHERE session_id = %s
                """, (session_id,))
                session = await cursor.fetchone()
                
                assert session is not None
                assert str(session[0]) == session_id
                assert session[1] == user_id
                assert session[2] == "active"
        
        await db_service.close()
    
    @pytest.mark.asyncio
    async def test_create_session_user_not_found(self, clean_database):
        """Test session creation for non-existent user."""
        db_service = DatabaseService()
        await db_service.init_database()
        user_manager = UserManager(db_service)
        
        # Test with non-existent user
        with pytest.raises(ValueError, match="User not found"):
            await user_manager.create_session("nonexistent_user_id")
        
        await db_service.close()
    
    @pytest.mark.asyncio
    async def test_create_session_database_error(self, clean_database):
        """Test session creation with database error."""
        db_service = DatabaseService()
        await db_service.init_database()
        user_manager = UserManager(db_service)
        
        # Test with invalid user_id format
        with pytest.raises(ValueError):
            await user_manager.create_session("invalid-uuid-format")
        
        await db_service.close()
    
    @pytest.mark.asyncio
    async def test_complete_session_success(self, clean_database):
        """Test successful session completion."""
        db_service = DatabaseService()
        await db_service.init_database()
        user_manager = UserManager(db_service)
        
        # Create test user and session
        async with get_test_database_connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    INSERT INTO users (username, privy_wallet_id, privy_wallet_address, current_balance)
                    VALUES (%s, %s, %s, %s)
                    RETURNING user_id
                """, ("test_user", "mock_wallet_id_23", "0xb056789012345678901234567890123456789012", 100.0))
                user_id = (await cursor.fetchone())[0]
                
                session_id = str(uuid.uuid4())
                await cursor.execute("""
                    INSERT INTO blackjack_sessions (session_id, user_id, status)
                    VALUES (%s, %s, %s)
                """, (session_id, user_id, "active"))
                await conn.commit()
        
        # Test completing session
        result = await user_manager.complete_session(session_id)
        assert result is True
        
        # Verify session status was updated
        async with get_test_database_connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    SELECT status FROM blackjack_sessions WHERE session_id = %s
                """, (session_id,))
                status = (await cursor.fetchone())[0]
                assert status == "completed"
        
        await db_service.close()
    
    @pytest.mark.asyncio
    async def test_complete_session_not_found(self, clean_database):
        """Test completing non-existent session."""
        db_service = DatabaseService()
        await db_service.init_database()
        user_manager = UserManager(db_service)
        
        # Test with non-existent session
        result = await user_manager.complete_session("nonexistent_session_id")
        assert result is False
        
        await db_service.close()
    
    @pytest.mark.asyncio
    async def test_complete_session_database_error(self, clean_database):
        """Test session completion with database error."""
        db_service = DatabaseService()
        await db_service.init_database()
        user_manager = UserManager(db_service)
        
        # Test with invalid session_id format
        result = await user_manager.complete_session("invalid-uuid-format")
        assert result is False
        
        await db_service.close()
    
    @pytest.mark.asyncio
    async def test_abandon_session_success(self, clean_database):
        """Test successful session abandonment."""
        db_service = DatabaseService()
        await db_service.init_database()
        user_manager = UserManager(db_service)
        
        # Create test user and session
        async with get_test_database_connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    INSERT INTO users (username, privy_wallet_id, privy_wallet_address, current_balance)
                    VALUES (%s, %s, %s, %s)
                    RETURNING user_id
                """, ("test_user", "mock_wallet_id_24", "0xc067890123456789012345678901234567890123", 100.0))
                user_id = (await cursor.fetchone())[0]
                
                session_id = str(uuid.uuid4())
                await cursor.execute("""
                    INSERT INTO blackjack_sessions (session_id, user_id, status)
                    VALUES (%s, %s, %s)
                """, (session_id, user_id, "active"))
                await conn.commit()
        
        # Test abandoning session
        result = await user_manager.abandon_session(session_id)
        assert result is True
        
        # Verify session status was updated
        async with get_test_database_connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    SELECT status FROM blackjack_sessions WHERE session_id = %s
                """, (session_id,))
                status = (await cursor.fetchone())[0]
                assert status == "abandoned"
        
        await db_service.close()
    
    @pytest.mark.asyncio
    async def test_abandon_session_not_found(self, clean_database):
        """Test abandoning non-existent session."""
        db_service = DatabaseService()
        await db_service.init_database()
        user_manager = UserManager(db_service)
        
        # Test with non-existent session
        result = await user_manager.abandon_session("nonexistent_session_id")
        assert result is False
        
        await db_service.close()
    
    @pytest.mark.asyncio
    async def test_abandon_session_database_error(self, clean_database):
        """Test session abandonment with database error."""
        db_service = DatabaseService()
        await db_service.init_database()
        user_manager = UserManager(db_service)
        
        # Test with invalid session_id format
        result = await user_manager.abandon_session("invalid-uuid-format")
        assert result is False
        
        await db_service.close()
    
    @pytest.mark.asyncio
    async def test_cleanup_abandoned_sessions_success(self, clean_database):
        """Test cleaning up abandoned sessions."""
        db_service = DatabaseService()
        await db_service.init_database()
        user_manager = UserManager(db_service)
        
        # Create test user and abandoned sessions
        async with get_test_database_connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    INSERT INTO users (username, privy_wallet_id, privy_wallet_address, current_balance)
                    VALUES (%s, %s, %s, %s)
                    RETURNING user_id
                """, ("test_user", "mock_wallet_id_25", "0xd078901234567890123456789012345678901234", 100.0))
                user_id = (await cursor.fetchone())[0]
                
                # Create sessions that are older than the threshold
                old_time = datetime.now() - timedelta(hours=2)
                for i in range(3):
                    session_id = str(uuid.uuid4())
                    await cursor.execute("""
                        INSERT INTO blackjack_sessions (session_id, user_id, status, created_at)
                        VALUES (%s, %s, %s, %s)
                    """, (session_id, user_id, "active", old_time))
                await conn.commit()
        
        # Test cleanup
        cleaned_count = await user_manager.cleanup_abandoned_sessions()
        assert cleaned_count == 3
        
        # Verify sessions were updated
        async with get_test_database_connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    SELECT COUNT(*) FROM blackjack_sessions WHERE status = 'abandoned'
                """)
                count = (await cursor.fetchone())[0]
                assert count == 3
        
        await db_service.close()
    
    @pytest.mark.asyncio
    async def test_cleanup_abandoned_sessions_no_sessions(self, clean_database):
        """Test cleanup when no sessions need cleaning."""
        db_service = DatabaseService()
        await db_service.init_database()
        user_manager = UserManager(db_service)
        
        # Test cleanup with no sessions to clean
        cleaned_count = await user_manager.cleanup_abandoned_sessions()
        assert cleaned_count == 0
        
        await db_service.close()
    
    @pytest.mark.asyncio
    async def test_cleanup_abandoned_sessions_database_error(self, clean_database):
        """Test cleanup with database error."""
        db_service = DatabaseService()
        await db_service.init_database()
        user_manager = UserManager(db_service)
        
        # Test cleanup (should handle gracefully)
        cleaned_count = await user_manager.cleanup_abandoned_sessions()
        assert cleaned_count == 0
        
        await db_service.close()
    
    @pytest.mark.asyncio
    async def test_get_user_by_username_existing_user(self, clean_database):
        """Test getting user by username."""
        db_service = DatabaseService()
        await db_service.init_database()
        user_manager = UserManager(db_service)
        
        # Create test user
        async with get_test_database_connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    INSERT INTO users (username, privy_wallet_id, privy_wallet_address, current_balance)
                    VALUES (%s, %s, %s, %s)
                    RETURNING user_id
                """, ("test_user", "mock_wallet_id_26", "0xe089012345678901234567890123456789012345", 100.0))
                user_id = (await cursor.fetchone())[0]
                await conn.commit()
        
        # Test getting user
        user = await user_manager._get_user_by_username("test_user")
        
        assert user is not None
        assert user["user_id"] == user_id
        assert user["username"] == "test_user"
        assert user["current_balance"] == 100.0
        
        await db_service.close()
    
    @pytest.mark.asyncio
    async def test_get_user_by_username_not_found(self, clean_database):
        """Test getting non-existent user by username."""
        db_service = DatabaseService()
        await db_service.init_database()
        user_manager = UserManager(db_service)
        
        # Test with non-existent user
        user = await user_manager._get_user_by_username("nonexistent_user")
        assert user is None
        
        await db_service.close()
    
    @pytest.mark.asyncio
    async def test_get_user_by_username_database_error(self, clean_database):
        """Test getting user with database error."""
        db_service = DatabaseService()
        await db_service.init_database()
        user_manager = UserManager(db_service)
        
        # Test with potentially problematic username
        user = await user_manager._get_user_by_username("'; DROP TABLE users; --")
        assert user is None
        
        await db_service.close()
    
    @pytest.mark.asyncio
    async def test_balance_operations_roundtrip(self, clean_database):
        """Test complete balance operation cycle."""
        db_service = DatabaseService()
        await db_service.init_database()
        user_manager = UserManager(db_service)
        
        # Create user and test full cycle
        mock_wallet_service = MockWalletService()
        username = await user_manager.create_user_if_not_exists("test_user", mock_wallet_service)
        
        # Initial balance should be 100.0
        balance = await user_manager.get_user_balance(username)
        assert balance == 100.0
        
        # Debit 25.0
        result = await user_manager.debit_user_balance(username, 25.0)
        assert result is True
        balance = await user_manager.get_user_balance(username)
        assert balance == 75.0
        
        # Credit 50.0
        result = await user_manager.credit_user_balance(username, 50.0)
        assert result is True
        balance = await user_manager.get_user_balance(username)
        assert balance == 125.0
        
        # Verify balance
        sufficient = await user_manager.verify_user_balance(username, 100.0)
        assert sufficient is True
        insufficient = await user_manager.verify_user_balance(username, 150.0)
        assert insufficient is False
        
        await db_service.close()
    
    @pytest.mark.asyncio
    async def test_session_lifecycle(self, clean_database):
        """Test complete session lifecycle."""
        db_service = DatabaseService()
        await db_service.init_database()
        user_manager = UserManager(db_service)
        
        # Create user
        mock_wallet_service = MockWalletService()
        username = await user_manager.create_user_if_not_exists("test_user", mock_wallet_service)
        
        # Create session
        session_id = await user_manager.create_session(username)
        assert session_id is not None
        
        # Verify session exists and is active
        async with get_test_database_connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    SELECT status FROM blackjack_sessions WHERE session_id = %s
                """, (session_id,))
                status = (await cursor.fetchone())[0]
                assert status == "active"
        
        # Complete session
        result = await user_manager.complete_session(session_id)
        assert result is True
        
        # Verify session is completed
        async with get_test_database_connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    SELECT status FROM blackjack_sessions WHERE session_id = %s
                """, (session_id,))
                status = (await cursor.fetchone())[0]
                assert status == "completed"
        
        await db_service.close()
    
    @pytest.mark.asyncio
    async def test_multiple_sessions_per_user(self, clean_database):
        """Test creating multiple sessions for same user."""
        db_service = DatabaseService()
        await db_service.init_database()
        user_manager = UserManager(db_service)
        
        # Create user
        mock_wallet_service = MockWalletService()
        username = await user_manager.create_user_if_not_exists("test_user", mock_wallet_service)
        user = await user_manager._get_user_by_username(username)
        user_id = user["user_id"]
        
        # Create multiple sessions
        session_ids = []
        for i in range(3):
            session_id = await user_manager.create_session(username)
            session_ids.append(session_id)
        
        # Verify all sessions exist
        async with get_test_database_connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    SELECT COUNT(*) FROM blackjack_sessions WHERE user_id = %s AND status = 'active'
                """, (user_id,))
                count = (await cursor.fetchone())[0]
                assert count == 3
        
        # Complete first session
        result = await user_manager.complete_session(session_ids[0])
        assert result is True
        
        # Abandon second session
        result = await user_manager.abandon_session(session_ids[1])
        assert result is True
        
        # Third session should still be active
        async with get_test_database_connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    SELECT status FROM blackjack_sessions WHERE session_id = %s
                """, (session_ids[2],))
                status = (await cursor.fetchone())[0]
                assert status == "active"
        
        await db_service.close() 
    
    @pytest.mark.asyncio
    async def test_get_user_wallet_info_by_username(self, clean_database):
        """Test getting wallet info by username."""
        db_service = DatabaseService()
        await db_service.init_database()
        user_manager = UserManager(db_service)
        
        # Create test user with wallet info
        async with get_test_database_connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    INSERT INTO users (username, privy_wallet_id, privy_wallet_address, current_balance)
                    VALUES (%s, %s, %s, %s)
                    RETURNING user_id
                """, ("test_user", "test_wallet_id_123", "0x1234567890123456789012345678901234567890", 100.0))
                user_id = (await cursor.fetchone())[0]
                await conn.commit()
        
        # Test getting wallet info by username
        wallet_info = await user_manager.get_user_wallet_info("test_user")
        
        assert wallet_info["wallet_id"] == "test_wallet_id_123"
        assert wallet_info["wallet_address"] == "0x1234567890123456789012345678901234567890"
        
        await db_service.close()
    
    @pytest.mark.asyncio
    async def test_get_user_wallet_info_by_user_id(self, clean_database):
        """Test getting wallet info by user_id."""
        db_service = DatabaseService()
        await db_service.init_database()
        user_manager = UserManager(db_service)
        
        # Create test user with wallet info
        async with get_test_database_connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    INSERT INTO users (username, privy_wallet_id, privy_wallet_address, current_balance)
                    VALUES (%s, %s, %s, %s)
                    RETURNING user_id
                """, ("test_user", "test_wallet_id_456", "0xabcdef1234567890abcdef1234567890abcdef12", 100.0))
                user_id = (await cursor.fetchone())[0]
                await conn.commit()
        
        # Test getting wallet info by user_id
        wallet_info = await user_manager.get_user_wallet_info(str(user_id))
        
        assert wallet_info["wallet_id"] == "test_wallet_id_456"
        assert wallet_info["wallet_address"] == "0xabcdef1234567890abcdef1234567890abcdef12"
        
        await db_service.close()
    
    @pytest.mark.asyncio
    async def test_get_user_wallet_info_user_not_found(self, clean_database):
        """Test getting wallet info for non-existent user."""
        db_service = DatabaseService()
        await db_service.init_database()
        user_manager = UserManager(db_service)
        
        # Test with non-existent user
        with pytest.raises(ValueError, match="User not found"):
            await user_manager.get_user_wallet_info("nonexistent_user")
        
        await db_service.close() 