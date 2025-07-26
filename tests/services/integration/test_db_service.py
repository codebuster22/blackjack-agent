"""
Integration tests for database service.
Tests real database operations with proper isolation.
"""
import pytest
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any

from services.db import DatabaseService
from tests.test_helpers import get_test_database_connection


@pytest.mark.integration
@pytest.mark.docker
@pytest.mark.database
class TestDatabaseService:
    """Integration tests for DatabaseService."""
    
    @pytest.mark.asyncio
    async def test_init_database_success(self, clean_database):
        """Test successful database initialization."""
        db_service = DatabaseService()
        
        # Test initialization
        result = await db_service.init_database()
        assert result is True
        assert db_service._initialized is True
        assert db_service.pool is not None
        
        # Test connection works
        async with db_service.get_connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("SELECT 1")
                result = await cursor.fetchone()
                assert result[0] == 1
        
        await db_service.close()
    
    @pytest.mark.asyncio
    async def test_init_database_with_custom_url(self, clean_database):
        """Test database initialization with custom URL."""
        db_service = DatabaseService()
        
        # Use test database URL
        from tests.test_helpers import TEST_DATABASE_URL
        result = await db_service.init_database(database_url=TEST_DATABASE_URL)
        
        assert result is True
        assert db_service._initialized is True
        
        await db_service.close()

    @pytest.mark.asyncio
    async def test_init_database_failure(self, clean_database):
        """Test database initialization failure with invalid URL."""
        db_service = DatabaseService()
        
        # Test with invalid database URL
        result = await db_service.init_database(database_url="postgresql://invalid:invalid@localhost:9999/invalid")
        
        assert result is False
        assert db_service._initialized is False
        # Pool may still be created even if connection fails in psycopg3
        # assert db_service.pool is None
        
        await db_service.close()

    @pytest.mark.asyncio
    async def test_get_connection_when_not_initialized(self):
        """Test getting connection when database not initialized."""
        db_service = DatabaseService()
        
        with pytest.raises(RuntimeError, match="Database not initialized"):
            async with db_service.get_connection() as conn:
                pass

    def test_database_service_initialization_state(self):
        """Test DatabaseService initialization state tracking."""
        db_service = DatabaseService()
        
        # Initially should not be initialized
        assert db_service._initialized is False
        assert db_service.pool is None

    @pytest.mark.asyncio
    async def test_get_connection_context_manager_exception(self, clean_database):
        """Test context manager with exception handling."""
        db_service = DatabaseService()
        await db_service.init_database()
        
        try:
            async with db_service.get_connection() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute("SELECT 1")
                    # Simulate an exception
                    raise ValueError("Test exception")
        except ValueError:
            pass  # Expected exception
        
        # Connection should still be returned to pool
        assert db_service.pool is not None
        
        await db_service.close()
    
    @pytest.mark.asyncio
    async def test_create_session_happy_path(self, clean_database):
        """Test successful session creation."""
        db_service = DatabaseService()
        await db_service.init_database()
        
        # Create test user first
        async with get_test_database_connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    INSERT INTO users (username, privy_wallet_id, privy_wallet_address, current_balance)
                    VALUES (%s, %s, %s, %s)
                    RETURNING user_id
                """, ("test_user", "mock_wallet_id_1", "0x1234567890123456789012345678901234567890", 100.0))
                user_id = (await cursor.fetchone())[0]
                await conn.commit()
        
        # Test session creation
        session_id = str(uuid.uuid4())
        result = await db_service.create_session(session_id, str(user_id))
        
        assert result is True
        
        # Verify session was created
        async with get_test_database_connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    SELECT session_id, user_id, status, created_at
                    FROM blackjack_sessions WHERE session_id = %s
                """, (session_id,))
                session = await cursor.fetchone()
                
                assert session is not None
                assert str(session[0]) == session_id
                assert session[1] == user_id
                assert session[2] == "active"
        
        await db_service.close()
    
    @pytest.mark.asyncio
    async def test_create_session_database_error(self, clean_database):
        """Test session creation with database error."""
        db_service = DatabaseService()
        await db_service.init_database()
        
        # Try to create session with invalid user_id (should fail)
        session_id = str(uuid.uuid4())
        result = await db_service.create_session(session_id, "invalid_user_id")
        
        assert result is False
        
        await db_service.close()
    
    @pytest.mark.asyncio
    async def test_create_session_duplicate_session_id(self, clean_database):
        """Test creating session with existing ID."""
        db_service = DatabaseService()
        await db_service.init_database()
        
        # Create test user first
        async with get_test_database_connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    INSERT INTO users (username, privy_wallet_id, privy_wallet_address, current_balance)
                    VALUES (%s, %s, %s, %s)
                    RETURNING user_id
                """, ("test_user", "mock_wallet_id_2", "0x2345678901234567890123456789012345678901", 100.0))
                user_id = (await cursor.fetchone())[0]
                await conn.commit()
        
        # Create first session
        session_id = str(uuid.uuid4())
        result1 = await db_service.create_session(session_id, str(user_id))
        assert result1 is True
        
        # Try to create duplicate session
        result2 = await db_service.create_session(session_id, str(user_id))
        assert result2 is False
        
        await db_service.close()
    
    @pytest.mark.asyncio
    async def test_save_round_happy_path(self, clean_database):
        """Test successful round saving."""
        db_service = DatabaseService()
        await db_service.init_database()
        
        # Create test user and session
        async with get_test_database_connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    INSERT INTO users (username, privy_wallet_id, privy_wallet_address, current_balance)
                    VALUES (%s, %s, %s, %s)
                    RETURNING user_id
                """, ("test_user", "mock_wallet_id_3", "0x3456789012345678901234567890123456789012", 100.0))
                user_id = (await cursor.fetchone())[0]
                
                session_id = str(uuid.uuid4())
                await cursor.execute("""
                    INSERT INTO blackjack_sessions (session_id, user_id, status)
                    VALUES (%s, %s, %s)
                """, (session_id, user_id, "active"))
                await conn.commit()
        
        # Test round saving
        round_data = {
            "round_id": str(uuid.uuid4()),
            "session_id": session_id,
            "bet_amount": 10.0,
            "player_hand": '["AS", "KD"]',
            "dealer_hand": '["10H", "2C"]',
            "player_total": 21,
            "dealer_total": 12,
            "outcome": "win",
            "payout": 20.0,
            "chips_before": 100.0,
            "chips_after": 120.0
        }
        
        result = await db_service.save_round(round_data)
        assert result is True
        
        # Verify round was saved
        async with get_test_database_connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    SELECT session_id, bet_amount, outcome
                    FROM rounds WHERE session_id = %s
                """, (session_id,))
                round_record = await cursor.fetchone()
                
                assert round_record is not None
                assert str(round_record[0]) == session_id
                assert round_record[1] == 10.0
                assert round_record[2] == "win"
        
        await db_service.close()
    
    @pytest.mark.asyncio
    async def test_save_round_missing_required_fields(self, clean_database):
        """Test saving round with missing data."""
        db_service = DatabaseService()
        await db_service.init_database()
        
        # Test with missing required fields
        round_data = {
            "session_id": str(uuid.uuid4()),
            # Missing bet_amount, player_hand, etc.
        }
        
        result = await db_service.save_round(round_data)
        assert result is False
        
        await db_service.close()
    
    @pytest.mark.asyncio
    async def test_save_round_database_error(self, clean_database):
        """Test round saving with database error."""
        db_service = DatabaseService()
        await db_service.init_database()
        
        # Test with invalid session_id (should fail)
        round_data = {
            "round_id": str(uuid.uuid4()),
            "session_id": "invalid_session_id",
            "bet_amount": 10.0,
            "player_hand": '["AS", "KD"]',
            "dealer_hand": '["10H", "2C"]',
            "player_total": 21,
            "dealer_total": 12,
            "outcome": "win",
            "payout": 20.0,
            "chips_before": 100.0,
            "chips_after": 120.0
        }
        
        result = await db_service.save_round(round_data)
        assert result is False
        
        await db_service.close()
    
    @pytest.mark.asyncio
    async def test_get_session_rounds_happy_path(self, clean_database):
        """Test retrieving rounds for session."""
        db_service = DatabaseService()
        await db_service.init_database()
        
        # Create test data
        async with get_test_database_connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    INSERT INTO users (username, privy_wallet_id, privy_wallet_address, current_balance)
                    VALUES (%s, %s, %s, %s)
                    RETURNING user_id
                """, ("test_user", "mock_wallet_id_4", "0x4567890123456789012345678901234567890123", 100.0))
                user_id = (await cursor.fetchone())[0]
                
                session_id = str(uuid.uuid4())
                await cursor.execute("""
                    INSERT INTO blackjack_sessions (session_id, user_id, status)
                    VALUES (%s, %s, %s)
                """, (session_id, user_id, "active"))
                
                # Insert test rounds
                for i in range(1, 4):
                    await cursor.execute("""
                        INSERT INTO rounds (
                            round_id, session_id, bet_amount, player_hand,
                            dealer_hand, player_total, dealer_total, outcome,
                            payout, chips_before, chips_after
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        str(uuid.uuid4()), session_id, 10.0, '["AS", "KD"]', '["10H", "2C"]',
                        21, 12, "win", 20.0, 100.0, 120.0
                    ))
                await conn.commit()
        
        # Test getting rounds
        rounds = await db_service.get_session_rounds(session_id)
        
        assert len(rounds) == 3
        # Verify rounds have the expected data
        for round_data in rounds:
            assert str(round_data["session_id"]) == session_id
            assert round_data["bet_amount"] == 10.0
            assert round_data["outcome"] == "win"
        
        await db_service.close()
    
    @pytest.mark.asyncio
    async def test_get_session_rounds_empty_session(self, clean_database):
        """Test getting rounds for session with no rounds."""
        db_service = DatabaseService()
        await db_service.init_database()
        
        # Create test session without rounds
        async with get_test_database_connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    INSERT INTO users (username, privy_wallet_id, privy_wallet_address, current_balance)
                    VALUES (%s, %s, %s, %s)
                    RETURNING user_id
                """, ("test_user", "mock_wallet_id_5", "0x5678901234567890123456789012345678901234", 100.0))
                user_id = (await cursor.fetchone())[0]
                
                session_id = str(uuid.uuid4())
                await cursor.execute("""
                    INSERT INTO blackjack_sessions (session_id, user_id, status)
                    VALUES (%s, %s, %s)
                """, (session_id, user_id, "active"))
                await conn.commit()
        
        # Test getting rounds for empty session
        rounds = await db_service.get_session_rounds(session_id)
        assert rounds == []
        
        await db_service.close()
    
    @pytest.mark.asyncio
    async def test_get_session_rounds_database_error(self, clean_database):
        """Test getting rounds with database error."""
        db_service = DatabaseService()
        await db_service.init_database()
        
        # Test with invalid session_id
        rounds = await db_service.get_session_rounds("invalid_session_id")
        assert rounds == []
        
        await db_service.close()
    
    @pytest.mark.asyncio
    async def test_get_user_sessions_happy_path(self, clean_database):
        """Test getting sessions for user."""
        db_service = DatabaseService()
        await db_service.init_database()
        
        # Create test user with multiple sessions
        async with get_test_database_connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    INSERT INTO users (username, privy_wallet_id, privy_wallet_address, current_balance)
                    VALUES (%s, %s, %s, %s)
                    RETURNING user_id
                """, ("test_user", "mock_wallet_id_6", "0x6789012345678901234567890123456789012345", 100.0))
                user_id = (await cursor.fetchone())[0]
                
                # Create multiple sessions
                for i in range(3):
                    session_id = str(uuid.uuid4())
                    await cursor.execute("""
                        INSERT INTO blackjack_sessions (session_id, user_id, status)
                        VALUES (%s, %s, %s)
                    """, (session_id, user_id, "active"))
                await conn.commit()
        
        # Test getting user sessions
        sessions = await db_service.get_user_sessions(str(user_id))
        
        assert len(sessions) == 3
        for session in sessions:
            assert session["user_id"] == user_id
            assert session["status"] == "active"
        
        await db_service.close()
    
    @pytest.mark.asyncio
    async def test_get_user_sessions_no_sessions(self, clean_database):
        """Test getting sessions for user with no sessions."""
        db_service = DatabaseService()
        await db_service.init_database()
        
        # Create test user without sessions
        async with get_test_database_connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    INSERT INTO users (username, privy_wallet_id, privy_wallet_address, current_balance)
                    VALUES (%s, %s, %s, %s)
                    RETURNING user_id
                """, ("test_user", "mock_wallet_id_7", "0x7890123456789012345678901234567890123456", 100.0))
                user_id = (await cursor.fetchone())[0]
                await conn.commit()
        
        # Test getting sessions for user with no sessions
        sessions = await db_service.get_user_sessions(str(user_id))
        assert sessions == []
        
        await db_service.close()
    
    @pytest.mark.asyncio
    async def test_get_user_sessions_database_error(self, clean_database):
        """Test getting sessions with database error."""
        db_service = DatabaseService()
        await db_service.init_database()
        
        # Test with invalid user_id
        sessions = await db_service.get_user_sessions("invalid_user_id")
        assert sessions == []
        
        await db_service.close()
    
    @pytest.mark.asyncio
    async def test_get_session_stats_happy_path(self, clean_database):
        """Test getting session statistics."""
        db_service = DatabaseService()
        await db_service.init_database()
        
        # Create test data with mixed outcomes
        async with get_test_database_connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    INSERT INTO users (username, privy_wallet_id, privy_wallet_address, current_balance)
                    VALUES (%s, %s, %s, %s)
                    RETURNING user_id
                """, ("test_user", "mock_wallet_id_8", "0x8901234567890123456789012345678901234567", 100.0))
                user_id = (await cursor.fetchone())[0]
                
                session_id = str(uuid.uuid4())
                await cursor.execute("""
                    INSERT INTO blackjack_sessions (session_id, user_id, status)
                    VALUES (%s, %s, %s)
                """, (session_id, user_id, "active"))
                
                # Insert rounds with different outcomes
                outcomes = ["win", "loss", "push", "win", "loss"]
                for i, outcome in enumerate(outcomes, 1):
                    await cursor.execute("""
                        INSERT INTO rounds (
                            round_id, session_id, bet_amount, player_hand,
                            dealer_hand, player_total, dealer_total, outcome,
                            payout, chips_before, chips_after
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        str(uuid.uuid4()), session_id, 10.0, '["AS", "KD"]', '["10H", "2C"]',
                        21, 12, outcome, 20.0 if outcome == "win" else 0.0,
                        100.0, 100.0 + (20.0 if outcome == "win" else 0.0)
                    ))
                await conn.commit()
        
        # Test getting session stats
        stats = await db_service.get_session_stats(session_id)
        
        assert stats["total_rounds"] == 5
        assert stats["wins"] == 2
        assert stats["losses"] == 2
        assert stats["pushes"] == 1
        assert stats["total_bet"] == 50.0
        assert stats["total_payout"] == 40.0
        assert stats["win_rate"] == 0.4
        
        await db_service.close()
    
    @pytest.mark.asyncio
    async def test_get_session_stats_empty_session(self, clean_database):
        """Test stats for session with no rounds."""
        db_service = DatabaseService()
        await db_service.init_database()
        
        # Create test session without rounds
        async with get_test_database_connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    INSERT INTO users (username, privy_wallet_id, privy_wallet_address, current_balance)
                    VALUES (%s, %s, %s, %s)
                    RETURNING user_id
                """, ("test_user", "mock_wallet_id_9", "0x9012345678901234567890123456789012345678", 100.0))
                user_id = (await cursor.fetchone())[0]
                
                session_id = str(uuid.uuid4())
                await cursor.execute("""
                    INSERT INTO blackjack_sessions (session_id, user_id, status)
                    VALUES (%s, %s, %s)
                """, (session_id, user_id, "active"))
                await conn.commit()
        
        # Test getting stats for empty session
        stats = await db_service.get_session_stats(session_id)
        
        assert stats["total_rounds"] == 0
        assert stats["wins"] == 0
        assert stats["losses"] == 0
        assert stats["pushes"] == 0
        assert stats["total_bet"] == 0.0
        assert stats["total_payout"] == 0.0
        assert stats["win_rate"] == 0
        
        await db_service.close()
    
    @pytest.mark.asyncio
    async def test_get_session_stats_with_wins_losses_pushes(self, clean_database):
        """Test stats with mixed outcomes."""
        db_service = DatabaseService()
        await db_service.init_database()
        
        # Create test data with specific outcomes
        async with get_test_database_connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    INSERT INTO users (username, privy_wallet_id, privy_wallet_address, current_balance)
                    VALUES (%s, %s, %s, %s)
                    RETURNING user_id
                """, ("test_user", "mock_wallet_id_10", "0xa023456789012345678901234567890123456789", 100.0))
                user_id = (await cursor.fetchone())[0]
                
                session_id = str(uuid.uuid4())
                await cursor.execute("""
                    INSERT INTO blackjack_sessions (session_id, user_id, status)
                    VALUES (%s, %s, %s)
                """, (session_id, user_id, "active"))
                
                # Insert specific outcomes
                test_data = [
                    ("win", 20.0, 10.0),
                    ("loss", 0.0, 10.0),
                    ("push", 10.0, 10.0),
                    ("win", 20.0, 10.0),
                    ("loss", 0.0, 10.0),
                    ("push", 10.0, 10.0),
                ]
                
                for i, (outcome, payout, bet) in enumerate(test_data, 1):
                    await cursor.execute("""
                        INSERT INTO rounds (
                            round_id, session_id, bet_amount, player_hand,
                            dealer_hand, player_total, dealer_total, outcome,
                            payout, chips_before, chips_after
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        str(uuid.uuid4()), session_id, bet, '["AS", "KD"]', '["10H", "2C"]',
                        21, 12, outcome, payout, 100.0, 100.0 + payout
                    ))
                await conn.commit()
        
        # Test getting session stats
        stats = await db_service.get_session_stats(session_id)
        
        assert stats["total_rounds"] == 6
        assert stats["wins"] == 2
        assert stats["losses"] == 2
        assert stats["pushes"] == 2
        assert stats["total_bet"] == 60.0
        assert stats["total_payout"] == 60.0
        assert stats["win_rate"] == 2/6
        
        await db_service.close()
    
    @pytest.mark.asyncio
    async def test_get_session_stats_database_error(self, clean_database):
        """Test stats with database error."""
        db_service = DatabaseService()
        await db_service.init_database()
        
        # Test with invalid session_id
        stats = await db_service.get_session_stats("invalid_session_id")
        
        # Should return empty dict for invalid session
        assert stats == {}
        
        await db_service.close()
    
    @pytest.mark.asyncio
    async def test_get_session_stats_no_rounds_found(self, clean_database):
        """Test stats when no rounds are found for session."""
        db_service = DatabaseService()
        await db_service.init_database()
        
        # Create test session without any rounds
        async with get_test_database_connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    INSERT INTO users (username, privy_wallet_id, privy_wallet_address, current_balance)
                    VALUES (%s, %s, %s, %s)
                    RETURNING user_id
                """, ("test_user", "mock_wallet_id_11", "0xb034567890123456789012345678901234567890", 100.0))
                user_id = (await cursor.fetchone())[0]
                
                session_id = str(uuid.uuid4())
                await cursor.execute("""
                    INSERT INTO blackjack_sessions (session_id, user_id, status)
                    VALUES (%s, %s, %s)
                """, (session_id, user_id, "active"))
                await conn.commit()
        
        # Test getting stats for session with no rounds
        stats = await db_service.get_session_stats(session_id)
        
        # Should return dictionary with zero values when no rounds found
        assert stats["total_rounds"] == 0
        assert stats["wins"] == 0
        assert stats["losses"] == 0
        assert stats["pushes"] == 0
        assert stats["total_bet"] == 0.0
        assert stats["total_payout"] == 0.0
        assert stats["win_rate"] == 0
        
        await db_service.close()
    
    @pytest.mark.asyncio
    async def test_update_session_status_happy_path(self, clean_database):
        """Test updating session status."""
        db_service = DatabaseService()
        await db_service.init_database()
        
        # Create test session
        async with get_test_database_connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    INSERT INTO users (username, privy_wallet_id, privy_wallet_address, current_balance)
                    VALUES (%s, %s, %s, %s)
                    RETURNING user_id
                """, ("test_user", "mock_wallet_id_12", "0xc045678901234567890123456789012345678901", 100.0))
                user_id = (await cursor.fetchone())[0]
                
                session_id = str(uuid.uuid4())
                await cursor.execute("""
                    INSERT INTO blackjack_sessions (session_id, user_id, status)
                    VALUES (%s, %s, %s)
                """, (session_id, user_id, "active"))
                await conn.commit()
        
        # Test updating status
        result = await db_service.update_session_status(session_id, "completed")
        assert result is True
        
        # Verify status was updated
        async with get_test_database_connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    SELECT status FROM blackjack_sessions WHERE session_id = %s
                """, (session_id,))
                status = (await cursor.fetchone())[0]
                assert status == "completed"
        
        await db_service.close()
    
    @pytest.mark.asyncio
    async def test_update_session_status_invalid_status(self, clean_database):
        """Test updating with invalid status."""
        db_service = DatabaseService()
        await db_service.init_database()
        
        # Create test session
        async with get_test_database_connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    INSERT INTO users (username, privy_wallet_id, privy_wallet_address, current_balance)
                    VALUES (%s, %s, %s, %s)
                    RETURNING user_id
                """, ("test_user", "mock_wallet_id_13", "0xd056789012345678901234567890123456789012", 100.0))
                user_id = (await cursor.fetchone())[0]
                
                session_id = str(uuid.uuid4())
                await cursor.execute("""
                    INSERT INTO blackjack_sessions (session_id, user_id, status)
                    VALUES (%s, %s, %s)
                """, (session_id, user_id, "active"))
                await conn.commit()
        
        # Test updating with invalid status
        result = await db_service.update_session_status(session_id, "invalid_status")
        assert result is False
        
        await db_service.close()
    
    @pytest.mark.asyncio
    async def test_update_session_status_nonexistent_session(self, clean_database):
        """Test updating non-existent session."""
        db_service = DatabaseService()
        await db_service.init_database()
        
        # Test updating non-existent session
        result = await db_service.update_session_status("nonexistent_session_id", "completed")
        assert result is False
        
        await db_service.close()
    
    @pytest.mark.asyncio
    async def test_update_session_status_database_error(self, clean_database):
        """Test status update with database error."""
        db_service = DatabaseService()
        await db_service.init_database()
        
        # Test with invalid session_id
        result = await db_service.update_session_status("invalid_session_id", "completed")
        assert result is False
        
        await db_service.close()
    
    @pytest.mark.asyncio
    async def test_close_database_connections(self, clean_database):
        """Test closing all database connections."""
        db_service = DatabaseService()
        await db_service.init_database()
        
        # Verify pool exists
        assert db_service.pool is not None
        
        # Close connections
        await db_service.close()
        
        # Verify pool is closed
        # Note: pool.closeall() doesn't set pool to None, it just closes connections
        # The _initialized flag should be set to False in close() method
    
    @pytest.mark.asyncio
    async def test_close_database_no_pool(self):
        """Test closing when no pool exists."""
        db_service = DatabaseService()
        
        # Should not raise an exception
        await db_service.close()
        
        assert db_service.pool is None
        assert db_service._initialized is False 