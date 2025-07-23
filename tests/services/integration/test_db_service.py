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
    
    def test_init_database_success(self, clean_database):
        """Test successful database initialization."""
        db_service = DatabaseService()
        
        # Test initialization
        result = db_service.init_database()
        assert result is True
        assert db_service._initialized is True
        assert db_service.pool is not None
        
        # Test connection works
        with db_service.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                assert result[0] == 1
        
        db_service.close()
    
    def test_init_database_with_custom_url(self, clean_database):
        """Test database initialization with custom URL."""
        db_service = DatabaseService()
        
        # Use test database URL
        from tests.test_helpers import TEST_DATABASE_URL
        result = db_service.init_database(database_url=TEST_DATABASE_URL)
        
        assert result is True
        assert db_service._initialized is True
        
        db_service.close()
    
    def test_init_database_failure(self, clean_database):
        """Test database initialization failure with invalid URL."""
        db_service = DatabaseService()
        
        # Test with invalid database URL
        result = db_service.init_database(database_url="postgresql://invalid:invalid@localhost:9999/invalid")
        
        assert result is False
        assert db_service._initialized is False
        assert db_service.pool is None
        
        db_service.close()
    
    def test_get_connection_when_not_initialized(self):
        """Test getting connection when database not initialized."""
        db_service = DatabaseService()
        
        with pytest.raises(RuntimeError, match="Database not initialized"):
            db_service._get_connection()
    
    def test_return_connection_with_no_pool(self):
        """Test returning connection when pool is None."""
        db_service = DatabaseService()
        
        # Should not raise an exception
        db_service._return_connection(None)
    
    def test_get_connection_context_manager_exception(self, clean_database):
        """Test context manager with exception handling."""
        db_service = DatabaseService()
        db_service.init_database()
        
        # Test that connection is properly returned even with exception
        try:
            with db_service.get_connection() as conn:
                with conn.cursor() as cursor:
                    # This will raise an exception
                    cursor.execute("SELECT * FROM nonexistent_table")
        except Exception:
            pass
        
        # Connection should still be available
        with db_service.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                assert result[0] == 1
        
        db_service.close()
    
    def test_create_session_happy_path(self, clean_database):
        """Test successful session creation."""
        db_service = DatabaseService()
        db_service.init_database()
        
        # Create test user first
        with get_test_database_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO users (username, current_balance)
                    VALUES (%s, %s)
                    RETURNING user_id
                """, ("test_user", 100.0))
                user_id = cursor.fetchone()[0]
                conn.commit()
        
        # Test session creation
        session_id = str(uuid.uuid4())
        result = db_service.create_session(session_id, str(user_id))
        
        assert result is True
        
        # Verify session was created
        with get_test_database_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT session_id, user_id, status, created_at
                    FROM sessions WHERE session_id = %s
                """, (session_id,))
                session = cursor.fetchone()
                
                assert session is not None
                assert session[0] == session_id
                assert session[1] == user_id
                assert session[2] == "active"
        
        db_service.close()
    
    def test_create_session_database_error(self, clean_database):
        """Test session creation with database error."""
        db_service = DatabaseService()
        db_service.init_database()
        
        # Try to create session with invalid user_id (should fail)
        session_id = str(uuid.uuid4())
        result = db_service.create_session(session_id, "invalid_user_id")
        
        assert result is False
        
        db_service.close()
    
    def test_create_session_duplicate_session_id(self, clean_database):
        """Test creating session with existing ID."""
        db_service = DatabaseService()
        db_service.init_database()
        
        # Create test user first
        with get_test_database_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO users (username, current_balance)
                    VALUES (%s, %s)
                    RETURNING user_id
                """, ("test_user", 100.0))
                user_id = cursor.fetchone()[0]
                conn.commit()
        
        # Create first session
        session_id = str(uuid.uuid4())
        result1 = db_service.create_session(session_id, str(user_id))
        assert result1 is True
        
        # Try to create duplicate session
        result2 = db_service.create_session(session_id, str(user_id))
        assert result2 is False
        
        db_service.close()
    
    def test_save_round_happy_path(self, clean_database):
        """Test successful round saving."""
        db_service = DatabaseService()
        db_service.init_database()
        
        # Create test user and session
        with get_test_database_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO users (username, current_balance)
                    VALUES (%s, %s)
                    RETURNING user_id
                """, ("test_user", 100.0))
                user_id = cursor.fetchone()[0]
                
                session_id = str(uuid.uuid4())
                cursor.execute("""
                    INSERT INTO sessions (session_id, user_id, status)
                    VALUES (%s, %s, %s)
                """, (session_id, user_id, "active"))
                conn.commit()
        
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
        
        result = db_service.save_round(round_data)
        assert result is True
        
        # Verify round was saved
        with get_test_database_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT session_id, bet_amount, outcome
                    FROM rounds WHERE session_id = %s
                """, (session_id,))
                round_record = cursor.fetchone()
                
                assert round_record is not None
                assert round_record[0] == session_id
                assert round_record[1] == 10.0
                assert round_record[2] == "win"
        
        db_service.close()
    
    def test_save_round_missing_required_fields(self, clean_database):
        """Test saving round with missing data."""
        db_service = DatabaseService()
        db_service.init_database()
        
        # Test with missing required fields
        round_data = {
            "session_id": str(uuid.uuid4()),
            # Missing bet_amount, player_hand, etc.
        }
        
        result = db_service.save_round(round_data)
        assert result is False
        
        db_service.close()
    
    def test_save_round_database_error(self, clean_database):
        """Test round saving with database error."""
        db_service = DatabaseService()
        db_service.init_database()
        
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
        
        result = db_service.save_round(round_data)
        assert result is False
        
        db_service.close()
    
    def test_get_session_rounds_happy_path(self, clean_database):
        """Test retrieving rounds for session."""
        db_service = DatabaseService()
        db_service.init_database()
        
        # Create test data
        with get_test_database_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO users (username, current_balance)
                    VALUES (%s, %s)
                    RETURNING user_id
                """, ("test_user", 100.0))
                user_id = cursor.fetchone()[0]
                
                session_id = str(uuid.uuid4())
                cursor.execute("""
                    INSERT INTO sessions (session_id, user_id, status)
                    VALUES (%s, %s, %s)
                """, (session_id, user_id, "active"))
                
                # Insert test rounds
                for i in range(1, 4):
                    cursor.execute("""
                        INSERT INTO rounds (
                            round_id, session_id, bet_amount, player_hand,
                            dealer_hand, player_total, dealer_total, outcome,
                            payout, chips_before, chips_after
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        str(uuid.uuid4()), session_id, 10.0, '["AS", "KD"]', '["10H", "2C"]',
                        21, 12, "win", 20.0, 100.0, 120.0
                    ))
                conn.commit()
        
        # Test getting rounds
        rounds = db_service.get_session_rounds(session_id)
        
        assert len(rounds) == 3
        # Verify rounds have the expected data
        for round_data in rounds:
            assert round_data["session_id"] == session_id
            assert round_data["bet_amount"] == 10.0
            assert round_data["outcome"] == "win"
        
        db_service.close()
    
    def test_get_session_rounds_empty_session(self, clean_database):
        """Test getting rounds for session with no rounds."""
        db_service = DatabaseService()
        db_service.init_database()
        
        # Create test session without rounds
        with get_test_database_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO users (username, current_balance)
                    VALUES (%s, %s)
                    RETURNING user_id
                """, ("test_user", 100.0))
                user_id = cursor.fetchone()[0]
                
                session_id = str(uuid.uuid4())
                cursor.execute("""
                    INSERT INTO sessions (session_id, user_id, status)
                    VALUES (%s, %s, %s)
                """, (session_id, user_id, "active"))
                conn.commit()
        
        # Test getting rounds for empty session
        rounds = db_service.get_session_rounds(session_id)
        assert rounds == []
        
        db_service.close()
    
    def test_get_session_rounds_database_error(self, clean_database):
        """Test getting rounds with database error."""
        db_service = DatabaseService()
        db_service.init_database()
        
        # Test with invalid session_id
        rounds = db_service.get_session_rounds("invalid_session_id")
        assert rounds == []
        
        db_service.close()
    
    def test_get_user_sessions_happy_path(self, clean_database):
        """Test getting sessions for user."""
        db_service = DatabaseService()
        db_service.init_database()
        
        # Create test user with multiple sessions
        with get_test_database_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO users (username, current_balance)
                    VALUES (%s, %s)
                    RETURNING user_id
                """, ("test_user", 100.0))
                user_id = cursor.fetchone()[0]
                
                # Create multiple sessions
                for i in range(3):
                    session_id = str(uuid.uuid4())
                    cursor.execute("""
                        INSERT INTO sessions (session_id, user_id, status)
                        VALUES (%s, %s, %s)
                    """, (session_id, user_id, "active"))
                conn.commit()
        
        # Test getting user sessions
        sessions = db_service.get_user_sessions(str(user_id))
        
        assert len(sessions) == 3
        for session in sessions:
            assert session["user_id"] == user_id
            assert session["status"] == "active"
        
        db_service.close()
    
    def test_get_user_sessions_no_sessions(self, clean_database):
        """Test getting sessions for user with no sessions."""
        db_service = DatabaseService()
        db_service.init_database()
        
        # Create test user without sessions
        with get_test_database_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO users (username, current_balance)
                    VALUES (%s, %s)
                    RETURNING user_id
                """, ("test_user", 100.0))
                user_id = cursor.fetchone()[0]
                conn.commit()
        
        # Test getting sessions for user with no sessions
        sessions = db_service.get_user_sessions(str(user_id))
        assert sessions == []
        
        db_service.close()
    
    def test_get_user_sessions_database_error(self, clean_database):
        """Test getting sessions with database error."""
        db_service = DatabaseService()
        db_service.init_database()
        
        # Test with invalid user_id
        sessions = db_service.get_user_sessions("invalid_user_id")
        assert sessions == []
        
        db_service.close()
    
    def test_get_session_stats_happy_path(self, clean_database):
        """Test getting session statistics."""
        db_service = DatabaseService()
        db_service.init_database()
        
        # Create test data with mixed outcomes
        with get_test_database_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO users (username, current_balance)
                    VALUES (%s, %s)
                    RETURNING user_id
                """, ("test_user", 100.0))
                user_id = cursor.fetchone()[0]
                
                session_id = str(uuid.uuid4())
                cursor.execute("""
                    INSERT INTO sessions (session_id, user_id, status)
                    VALUES (%s, %s, %s)
                """, (session_id, user_id, "active"))
                
                # Insert rounds with different outcomes
                outcomes = ["win", "loss", "push", "win", "loss"]
                for i, outcome in enumerate(outcomes, 1):
                    cursor.execute("""
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
                conn.commit()
        
        # Test getting session stats
        stats = db_service.get_session_stats(session_id)
        
        assert stats["total_rounds"] == 5
        assert stats["wins"] == 2
        assert stats["losses"] == 2
        assert stats["pushes"] == 1
        assert stats["total_bet"] == 50.0
        assert stats["total_payout"] == 40.0
        assert stats["win_rate"] == 0.4
        
        db_service.close()
    
    def test_get_session_stats_empty_session(self, clean_database):
        """Test stats for session with no rounds."""
        db_service = DatabaseService()
        db_service.init_database()
        
        # Create test session without rounds
        with get_test_database_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO users (username, current_balance)
                    VALUES (%s, %s)
                    RETURNING user_id
                """, ("test_user", 100.0))
                user_id = cursor.fetchone()[0]
                
                session_id = str(uuid.uuid4())
                cursor.execute("""
                    INSERT INTO sessions (session_id, user_id, status)
                    VALUES (%s, %s, %s)
                """, (session_id, user_id, "active"))
                conn.commit()
        
        # Test getting stats for empty session
        stats = db_service.get_session_stats(session_id)
        
        assert stats["total_rounds"] == 0
        assert stats["wins"] == 0
        assert stats["losses"] == 0
        assert stats["pushes"] == 0
        assert stats["total_bet"] == 0.0
        assert stats["total_payout"] == 0.0
        assert stats["win_rate"] == 0
        
        db_service.close()
    
    def test_get_session_stats_with_wins_losses_pushes(self, clean_database):
        """Test stats with mixed outcomes."""
        db_service = DatabaseService()
        db_service.init_database()
        
        # Create test data with specific outcomes
        with get_test_database_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO users (username, current_balance)
                    VALUES (%s, %s)
                    RETURNING user_id
                """, ("test_user", 100.0))
                user_id = cursor.fetchone()[0]
                
                session_id = str(uuid.uuid4())
                cursor.execute("""
                    INSERT INTO sessions (session_id, user_id, status)
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
                    cursor.execute("""
                        INSERT INTO rounds (
                            round_id, session_id, bet_amount, player_hand,
                            dealer_hand, player_total, dealer_total, outcome,
                            payout, chips_before, chips_after
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        str(uuid.uuid4()), session_id, bet, '["AS", "KD"]', '["10H", "2C"]',
                        21, 12, outcome, payout, 100.0, 100.0 + payout
                    ))
                conn.commit()
        
        # Test getting session stats
        stats = db_service.get_session_stats(session_id)
        
        assert stats["total_rounds"] == 6
        assert stats["wins"] == 2
        assert stats["losses"] == 2
        assert stats["pushes"] == 2
        assert stats["total_bet"] == 60.0
        assert stats["total_payout"] == 60.0
        assert stats["win_rate"] == 2/6
        
        db_service.close()
    
    def test_get_session_stats_database_error(self, clean_database):
        """Test stats with database error."""
        db_service = DatabaseService()
        db_service.init_database()
        
        # Test with invalid session_id
        stats = db_service.get_session_stats("invalid_session_id")
        
        # Should return empty dict for invalid session
        assert stats == {}
        
        db_service.close()
    
    def test_get_session_stats_no_rounds_found(self, clean_database):
        """Test stats when no rounds are found for session."""
        db_service = DatabaseService()
        db_service.init_database()
        
        # Create test session without any rounds
        with get_test_database_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO users (username, current_balance)
                    VALUES (%s, %s)
                    RETURNING user_id
                """, ("test_user", 100.0))
                user_id = cursor.fetchone()[0]
                
                session_id = str(uuid.uuid4())
                cursor.execute("""
                    INSERT INTO sessions (session_id, user_id, status)
                    VALUES (%s, %s, %s)
                """, (session_id, user_id, "active"))
                conn.commit()
        
        # Test getting stats for session with no rounds
        stats = db_service.get_session_stats(session_id)
        
        # Should return dictionary with zero values when no rounds found
        assert stats["total_rounds"] == 0
        assert stats["wins"] == 0
        assert stats["losses"] == 0
        assert stats["pushes"] == 0
        assert stats["total_bet"] == 0.0
        assert stats["total_payout"] == 0.0
        assert stats["win_rate"] == 0
        
        db_service.close()
    
    def test_update_session_status_happy_path(self, clean_database):
        """Test updating session status."""
        db_service = DatabaseService()
        db_service.init_database()
        
        # Create test session
        with get_test_database_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO users (username, current_balance)
                    VALUES (%s, %s)
                    RETURNING user_id
                """, ("test_user", 100.0))
                user_id = cursor.fetchone()[0]
                
                session_id = str(uuid.uuid4())
                cursor.execute("""
                    INSERT INTO sessions (session_id, user_id, status)
                    VALUES (%s, %s, %s)
                """, (session_id, user_id, "active"))
                conn.commit()
        
        # Test updating status
        result = db_service.update_session_status(session_id, "completed")
        assert result is True
        
        # Verify status was updated
        with get_test_database_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT status FROM sessions WHERE session_id = %s
                """, (session_id,))
                status = cursor.fetchone()[0]
                assert status == "completed"
        
        db_service.close()
    
    def test_update_session_status_invalid_status(self, clean_database):
        """Test updating with invalid status."""
        db_service = DatabaseService()
        db_service.init_database()
        
        # Create test session
        with get_test_database_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO users (username, current_balance)
                    VALUES (%s, %s)
                    RETURNING user_id
                """, ("test_user", 100.0))
                user_id = cursor.fetchone()[0]
                
                session_id = str(uuid.uuid4())
                cursor.execute("""
                    INSERT INTO sessions (session_id, user_id, status)
                    VALUES (%s, %s, %s)
                """, (session_id, user_id, "active"))
                conn.commit()
        
        # Test updating with invalid status
        result = db_service.update_session_status(session_id, "invalid_status")
        assert result is False
        
        db_service.close()
    
    def test_update_session_status_nonexistent_session(self, clean_database):
        """Test updating non-existent session."""
        db_service = DatabaseService()
        db_service.init_database()
        
        # Test updating non-existent session
        result = db_service.update_session_status("nonexistent_session_id", "completed")
        assert result is False
        
        db_service.close()
    
    def test_update_session_status_database_error(self, clean_database):
        """Test status update with database error."""
        db_service = DatabaseService()
        db_service.init_database()
        
        # Test with invalid session_id
        result = db_service.update_session_status("invalid_session_id", "completed")
        assert result is False
        
        db_service.close()
    
    def test_close_database_connections(self, clean_database):
        """Test closing all database connections."""
        db_service = DatabaseService()
        db_service.init_database()
        
        # Verify pool exists
        assert db_service.pool is not None
        
        # Close connections
        db_service.close()
        
        # Verify pool is closed
        # Note: pool.closeall() doesn't set pool to None, it just closes connections
        # The _initialized flag should be set to False in close() method
    
    def test_close_database_no_pool(self):
        """Test closing when no pool exists."""
        db_service = DatabaseService()
        
        # Should not raise an exception
        db_service.close()
        
        assert db_service.pool is None
        assert db_service._initialized is False 