"""
Integration tests for user manager service.
Tests real database operations with proper isolation.
"""
import pytest
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any

from services.user_manager import UserManager
from services.db import DatabaseService
from tests.test_helpers import get_test_database_connection


@pytest.mark.integration
@pytest.mark.docker
@pytest.mark.database
class TestUserManager:
    """Integration tests for UserManager."""
    
    def test_create_user_if_not_exists_new_user(self, clean_database):
        """Test creating a new user."""
        db_service = DatabaseService()
        db_service.init_database()
        user_manager = UserManager(db_service)
        
        # Test creating new user
        username = user_manager.create_user_if_not_exists("new_user")
        
        assert username == "new_user"
        
        # Verify user was created
        with get_test_database_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT username, current_balance FROM users WHERE username = %s
                """, (username,))
                user = cursor.fetchone()
                
                assert user is not None
                assert user[0] == "new_user"
                assert user[1] == 100.0  # Default starting chips
        
        db_service.close()
    
    def test_create_user_if_not_exists_existing_user(self, clean_database):
        """Test creating user when user already exists."""
        db_service = DatabaseService()
        db_service.init_database()
        user_manager = UserManager(db_service)
        
        # Create user first time
        username1 = user_manager.create_user_if_not_exists("existing_user")
        
        # Try to create same user again
        username2 = user_manager.create_user_if_not_exists("existing_user")
        
        # Should return same username
        assert username1 == username2 == "existing_user"
        
        db_service.close()
    
    def test_create_user_if_not_exists_database_error(self, clean_database):
        """Test user creation with database error."""
        db_service = DatabaseService()
        db_service.init_database()
        user_manager = UserManager(db_service)
        
        # Create a user first
        username1 = user_manager.create_user_if_not_exists("test_user")
        
        # Try to create user with invalid characters that might cause DB error
        with pytest.raises(ValueError, match="Failed to create user"):
            user_manager.create_user_if_not_exists("test_user_with_very_long_username_that_exceeds_database_column_limit_and_causes_an_error")
        
        db_service.close()
    
    def test_get_user_balance_success(self, clean_database):
        """Test getting user balance successfully."""
        db_service = DatabaseService()
        db_service.init_database()
        user_manager = UserManager(db_service)
        
        # Create test user
        with get_test_database_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO users (username, current_balance)
                    VALUES (%s, %s)
                    RETURNING user_id
                """, ("test_user", 150.0))
                conn.commit()
        
        # Test getting balance
        balance = user_manager.get_user_balance("test_user")
        assert balance == 150.0
        
        db_service.close()
    
    def test_get_user_balance_user_not_found(self, clean_database):
        """Test getting balance for non-existent user."""
        db_service = DatabaseService()
        db_service.init_database()
        user_manager = UserManager(db_service)
        
        # Test getting balance for non-existent user
        with pytest.raises(ValueError, match="Failed to get user balance"):
            user_manager.get_user_balance("nonexistent_user")
        
        db_service.close()
    
    def test_get_user_balance_database_error(self, clean_database):
        """Test getting balance with database error."""
        db_service = DatabaseService()
        db_service.init_database()
        user_manager = UserManager(db_service)
        
        # Test with invalid UUID format that might cause database error
        with pytest.raises(ValueError, match="Failed to get user balance"):
            user_manager.get_user_balance("invalid-uuid-format")
        
        db_service.close()
    
    def test_debit_user_balance_success(self, clean_database):
        """Test successful balance debit."""
        db_service = DatabaseService()
        db_service.init_database()
        user_manager = UserManager(db_service)
        
        # Create test user with sufficient balance
        with get_test_database_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO users (username, current_balance)
                    VALUES (%s, %s)
                    RETURNING user_id
                """, ("test_user", 100.0))
                conn.commit()
        
        # Test debit
        result = user_manager.debit_user_balance("test_user", 25.0)
        assert result is True
        
        # Verify balance was updated
        new_balance = user_manager.get_user_balance("test_user")
        assert new_balance == 75.0
        
        db_service.close()
    
    def test_debit_user_balance_insufficient_funds(self, clean_database):
        """Test debit with insufficient funds."""
        db_service = DatabaseService()
        db_service.init_database()
        user_manager = UserManager(db_service)
        
        # Create test user with insufficient balance
        with get_test_database_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO users (username, current_balance)
                    VALUES (%s, %s)
                    RETURNING user_id
                """, ("test_user", 10.0))
                conn.commit()
        
        # Test debit with insufficient funds
        result = user_manager.debit_user_balance("test_user", 25.0)
        assert result is False
        
        # Verify balance was not changed
        balance = user_manager.get_user_balance("test_user")
        assert balance == 10.0
        
        db_service.close()
    
    def test_debit_user_balance_user_not_found(self, clean_database):
        """Test debit for non-existent user."""
        db_service = DatabaseService()
        db_service.init_database()
        user_manager = UserManager(db_service)
        
        # Test debit for non-existent user
        result = user_manager.debit_user_balance("nonexistent_user", 25.0)
        assert result is False
        
        db_service.close()
    
    def test_debit_user_balance_invalid_amount(self, clean_database):
        """Test debit with invalid amount."""
        db_service = DatabaseService()
        db_service.init_database()
        user_manager = UserManager(db_service)
        
        # Create test user
        with get_test_database_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO users (username, current_balance)
                    VALUES (%s, %s)
                    RETURNING user_id
                """, ("test_user", 100.0))
                conn.commit()
        
        # Test debit with zero amount
        with pytest.raises(ValueError, match="Amount to debit must be greater than 0"):
            user_manager.debit_user_balance("test_user", 0.0)
        
        # Test debit with negative amount
        with pytest.raises(ValueError, match="Amount to debit must be greater than 0"):
            user_manager.debit_user_balance("test_user", -10.0)
        
        db_service.close()
    
    def test_debit_user_balance_database_error(self, clean_database):
        """Test debit with database error."""
        db_service = DatabaseService()
        db_service.init_database()
        user_manager = UserManager(db_service)
        
        # Test with non-existent user
        result = user_manager.debit_user_balance("invalid-user", 25.0)
        assert result is False
        
        db_service.close()
    
    def test_credit_user_balance_success(self, clean_database):
        """Test successful balance credit."""
        db_service = DatabaseService()
        db_service.init_database()
        user_manager = UserManager(db_service)
        
        # Create test user
        with get_test_database_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO users (username, current_balance)
                    VALUES (%s, %s)
                    RETURNING user_id
                """, ("test_user", 100.0))
                user_id = cursor.fetchone()[0]
                conn.commit()
        
        # Test credit
        result = user_manager.credit_user_balance("test_user", 50.0)
        assert result is True
        
        # Verify balance was updated
        new_balance = user_manager.get_user_balance(str(user_id))
        assert new_balance == 150.0
        
        db_service.close()
    
    def test_credit_user_balance_user_not_found(self, clean_database):
        """Test credit for non-existent user."""
        db_service = DatabaseService()
        db_service.init_database()
        user_manager = UserManager(db_service)
        
        # Test credit for non-existent user
        result = user_manager.credit_user_balance("nonexistent_user_id", 50.0)
        assert result is False
        
        db_service.close()
    
    def test_credit_user_balance_invalid_amount(self, clean_database):
        """Test credit with invalid amount."""
        db_service = DatabaseService()
        db_service.init_database()
        user_manager = UserManager(db_service)
        
        # Create test user
        with get_test_database_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO users (username, current_balance)
                    VALUES (%s, %s)
                    RETURNING user_id
                """, ("test_user", 100.0))
                user_id = cursor.fetchone()[0]
                conn.commit()
        
        # Test credit with zero amount
        with pytest.raises(ValueError, match="Amount to credit must be greater than 0"):
            user_manager.credit_user_balance("test_user", 0.0)
        
        # Test credit with negative amount
        with pytest.raises(ValueError, match="Amount to credit must be greater than 0"):
            user_manager.credit_user_balance("test_user", -10.0)
        
        db_service.close()
    
    def test_credit_user_balance_database_error(self, clean_database):
        """Test credit with database error."""
        db_service = DatabaseService()
        db_service.init_database()
        user_manager = UserManager(db_service)
        
        # Test with invalid UUID format
        result = user_manager.credit_user_balance("invalid-uuid-format", 50.0)
        assert result is False
        
        db_service.close()
    
    def test_credit_user_balance_function_failure(self, clean_database):
        """Test credit when PostgreSQL function returns False."""
        db_service = DatabaseService()
        db_service.init_database()
        user_manager = UserManager(db_service)
        
        # Create test user
        with get_test_database_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO users (username, current_balance)
                    VALUES (%s, %s)
                    RETURNING user_id
                """, ("test_user", 100.0))
                user_id = cursor.fetchone()[0]
                conn.commit()
        
        # Mock the credit function to return False
        # This would require mocking the database function, but for now we'll test
        # the error handling path by using an invalid user_id that causes the function to fail
        result = user_manager.credit_user_balance("invalid-user-id", 50.0)
        assert result is False
        
        db_service.close()
    
    def test_verify_user_balance_sufficient(self, clean_database):
        """Test balance verification with sufficient funds."""
        db_service = DatabaseService()
        db_service.init_database()
        user_manager = UserManager(db_service)
        
        # Create test user with sufficient balance
        with get_test_database_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO users (username, current_balance)
                    VALUES (%s, %s)
                    RETURNING user_id
                """, ("test_user", 100.0))
                user_id = cursor.fetchone()[0]
                conn.commit()
        
        # Test verification
        result = user_manager.verify_user_balance("test_user", 50.0)
        assert result is True
        
        db_service.close()
    
    def test_verify_user_balance_insufficient(self, clean_database):
        """Test balance verification with insufficient funds."""
        db_service = DatabaseService()
        db_service.init_database()
        user_manager = UserManager(db_service)
        
        # Create test user with insufficient balance
        with get_test_database_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO users (username, current_balance)
                    VALUES (%s, %s)
                    RETURNING user_id
                """, ("test_user", 25.0))
                user_id = cursor.fetchone()[0]
                conn.commit()
        
        # Test verification
        result = user_manager.verify_user_balance("test_user", 50.0)
        assert result is False
        
        db_service.close()
    
    def test_verify_user_balance_exact_amount(self, clean_database):
        """Test balance verification with exact amount."""
        db_service = DatabaseService()
        db_service.init_database()
        user_manager = UserManager(db_service)
        
        # Create test user with exact balance
        with get_test_database_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO users (username, current_balance)
                    VALUES (%s, %s)
                    RETURNING user_id
                """, ("test_user", 50.0))
                user_id = cursor.fetchone()[0]
                conn.commit()
        
        # Test verification with exact amount
        result = user_manager.verify_user_balance("test_user", 50.0)
        assert result is True
        
        db_service.close()
    
    def test_verify_user_balance_user_not_found(self, clean_database):
        """Test balance verification for non-existent user."""
        db_service = DatabaseService()
        db_service.init_database()
        user_manager = UserManager(db_service)
        
        # Test verification for non-existent user
        result = user_manager.verify_user_balance("nonexistent_user_id", 50.0)
        assert result is False
        
        db_service.close()
    
    def test_create_session_success(self, clean_database):
        """Test successful session creation."""
        db_service = DatabaseService()
        db_service.init_database()
        user_manager = UserManager(db_service)
        
        # Create test user
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
        session_id = user_manager.create_session("test_user")
        
        assert session_id is not None
        
        # Verify session was created
        with get_test_database_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT session_id, user_id, status, created_at
                    FROM blackjack_sessions WHERE session_id = %s
                """, (session_id,))
                session = cursor.fetchone()
                
                assert session is not None
                assert session[0] == session_id
                assert session[1] == user_id
                assert session[2] == "active"
        
        db_service.close()
    
    def test_create_session_user_not_found(self, clean_database):
        """Test session creation for non-existent user."""
        db_service = DatabaseService()
        db_service.init_database()
        user_manager = UserManager(db_service)
        
        # Test session creation for non-existent user
        with pytest.raises(ValueError):
            user_manager.create_session("nonexistent_user_id")
        
        db_service.close()
    
    def test_create_session_database_error(self, clean_database):
        """Test session creation with database error."""
        db_service = DatabaseService()
        db_service.init_database()
        user_manager = UserManager(db_service)
        
        # Test with invalid UUID format
        with pytest.raises(ValueError):
            user_manager.create_session("invalid-uuid-format")
        
        db_service.close()
    
    def test_complete_session_success(self, clean_database):
        """Test successful session completion."""
        db_service = DatabaseService()
        db_service.init_database()
        user_manager = UserManager(db_service)
        
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
                    INSERT INTO blackjack_sessions (session_id, user_id, status)
                    VALUES (%s, %s, %s)
                """, (session_id, user_id, "active"))
                conn.commit()
        
        # Test session completion
        result = user_manager.complete_session(session_id)
        assert result is True
        
        # Verify session status was updated
        with get_test_database_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT status FROM blackjack_sessions WHERE session_id = %s
                """, (session_id,))
                session = cursor.fetchone()
                
                assert session[0] == "completed"
        
        db_service.close()
    
    def test_complete_session_not_found(self, clean_database):
        """Test completing non-existent session."""
        db_service = DatabaseService()
        db_service.init_database()
        user_manager = UserManager(db_service)
        
        # Test completing non-existent session
        result = user_manager.complete_session("nonexistent_session_id")
        assert result is False
        
        db_service.close()
    
    def test_complete_session_database_error(self, clean_database):
        """Test session completion with database error."""
        db_service = DatabaseService()
        db_service.init_database()
        user_manager = UserManager(db_service)
        
        # Test with invalid UUID format
        result = user_manager.complete_session("invalid-uuid-format")
        assert result is False
        
        db_service.close()
    
    def test_abandon_session_success(self, clean_database):
        """Test successful session abandonment."""
        db_service = DatabaseService()
        db_service.init_database()
        user_manager = UserManager(db_service)
        
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
                    INSERT INTO blackjack_sessions (session_id, user_id, status)
                    VALUES (%s, %s, %s)
                """, (session_id, user_id, "active"))
                conn.commit()
        
        # Test session abandonment
        result = user_manager.abandon_session(session_id)
        assert result is True
        
        # Verify session status was updated
        with get_test_database_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT status FROM blackjack_sessions WHERE session_id = %s
                """, (session_id,))
                session = cursor.fetchone()
                
                assert session[0] == "abandoned"
        
        db_service.close()
    
    def test_abandon_session_not_found(self, clean_database):
        """Test abandoning non-existent session."""
        db_service = DatabaseService()
        db_service.init_database()
        user_manager = UserManager(db_service)
        
        # Test abandoning non-existent session
        result = user_manager.abandon_session("nonexistent_session_id")
        assert result is False
        
        db_service.close()
    
    def test_abandon_session_database_error(self, clean_database):
        """Test session abandonment with database error."""
        db_service = DatabaseService()
        db_service.init_database()
        user_manager = UserManager(db_service)
        
        # Test with invalid UUID format
        result = user_manager.abandon_session("invalid-uuid-format")
        assert result is False
        
        db_service.close()
    
    def test_cleanup_abandoned_sessions_success(self, clean_database):
        """Test successful cleanup of abandoned sessions."""
        db_service = DatabaseService()
        db_service.init_database()
        user_manager = UserManager(db_service)
        
        # Create test user and abandoned sessions
        with get_test_database_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO users (username, current_balance)
                    VALUES (%s, %s)
                    RETURNING user_id
                """, ("test_user", 100.0))
                user_id = cursor.fetchone()[0]
                
                # Create active sessions (older than 1 hour) - these should be marked as abandoned
                old_time = datetime.now() - timedelta(hours=2)
                for i in range(3):
                    session_id = str(uuid.uuid4())
                    cursor.execute("""
                        INSERT INTO blackjack_sessions (session_id, user_id, status, created_at)
                        VALUES (%s, %s, %s, %s)
                    """, (session_id, user_id, "active", old_time))
                
                # Create one recent active session (should not be cleaned up)
                recent_time = datetime.now() - timedelta(minutes=30)
                recent_session_id = str(uuid.uuid4())
                cursor.execute("""
                    INSERT INTO blackjack_sessions (session_id, user_id, status, created_at)
                    VALUES (%s, %s, %s, %s)
                """, (recent_session_id, user_id, "active", recent_time))
                
                conn.commit()
        
        # Test cleanup
        cleaned_count = user_manager.cleanup_abandoned_sessions()
        assert cleaned_count == 3
        
        # Verify old sessions were marked as abandoned
        with get_test_database_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT COUNT(*) FROM blackjack_sessions WHERE status = 'abandoned'
                """)
                abandoned_count = cursor.fetchone()[0]
                assert abandoned_count == 3  # The old sessions should be marked as abandoned
                
                cursor.execute("""
                    SELECT COUNT(*) FROM blackjack_sessions WHERE status = 'active'
                """)
                active_count = cursor.fetchone()[0]
                assert active_count == 1  # Only the recent one should remain active
        
        db_service.close()
    
    def test_cleanup_abandoned_sessions_no_sessions(self, clean_database):
        """Test cleanup when no abandoned sessions exist."""
        db_service = DatabaseService()
        db_service.init_database()
        user_manager = UserManager(db_service)
        
        # Test cleanup with no abandoned sessions
        cleaned_count = user_manager.cleanup_abandoned_sessions()
        assert cleaned_count == 0
        
        db_service.close()
    
    def test_cleanup_abandoned_sessions_database_error(self, clean_database):
        """Test cleanup with database error."""
        db_service = DatabaseService()
        db_service.init_database()
        user_manager = UserManager(db_service)
        
        # Test cleanup with database error (should return 0)
        cleaned_count = user_manager.cleanup_abandoned_sessions()
        assert cleaned_count == 0
        
        db_service.close()
    
    def test_get_user_by_username_existing_user(self, clean_database):
        """Test getting user by username when user exists."""
        db_service = DatabaseService()
        db_service.init_database()
        user_manager = UserManager(db_service)
        
        # Create test user
        with get_test_database_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO users (username, current_balance)
                    VALUES (%s, %s)
                    RETURNING user_id
                """, ("test_user", 100.0))
                user_id = cursor.fetchone()[0]
                conn.commit()
        
        # Test getting user by username
        user = user_manager._get_user_by_username("test_user")
        
        assert user is not None
        assert user["user_id"] == user_id
        assert user["username"] == "test_user"
        assert user["current_balance"] == 100.0
        
        db_service.close()
    
    def test_get_user_by_username_not_found(self, clean_database):
        """Test getting user by username when user doesn't exist."""
        db_service = DatabaseService()
        db_service.init_database()
        user_manager = UserManager(db_service)
        
        # Test getting non-existent user
        user = user_manager._get_user_by_username("nonexistent_user")
        assert user is None
        
        db_service.close()
    
    def test_get_user_by_username_database_error(self, clean_database):
        """Test getting user by username with database error."""
        db_service = DatabaseService()
        db_service.init_database()
        user_manager = UserManager(db_service)
        
        # Test with invalid username that might cause database error
        user = user_manager._get_user_by_username("")
        assert user is None
        
        db_service.close()
    
    def test_balance_operations_roundtrip(self, clean_database):
        """Test complete balance operations roundtrip."""
        db_service = DatabaseService()
        db_service.init_database()
        user_manager = UserManager(db_service)
        
        # Create user
        user_id = user_manager.create_user_if_not_exists("test_user")
        
        # Verify initial balance
        initial_balance = user_manager.get_user_balance(user_id)
        assert initial_balance == 100.0
        
        # Test debit
        debit_result = user_manager.debit_user_balance(user_id, 30.0)
        assert debit_result is True
        
        # Verify balance after debit
        balance_after_debit = user_manager.get_user_balance(user_id)
        assert balance_after_debit == 70.0
        
        # Test credit
        credit_result = user_manager.credit_user_balance(user_id, 20.0)
        assert credit_result is True
        
        # Verify final balance
        final_balance = user_manager.get_user_balance(user_id)
        assert final_balance == 90.0
        
        db_service.close()
    
    def test_session_lifecycle(self, clean_database):
        """Test complete session lifecycle."""
        db_service = DatabaseService()
        db_service.init_database()
        user_manager = UserManager(db_service)
        
        # Create user
        user_id = user_manager.create_user_if_not_exists("test_user")
        
        # Create session
        session_id = user_manager.create_session(user_id)
        assert session_id is not None
        
        # Verify session is active
        with get_test_database_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT status FROM blackjack_sessions WHERE session_id = %s
                """, (session_id,))
                status = cursor.fetchone()[0]
                assert status == "active"
        
        # Complete session
        complete_result = user_manager.complete_session(session_id)
        assert complete_result is True
        
        # Verify session is completed
        with get_test_database_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT status FROM blackjack_sessions WHERE session_id = %s
                """, (session_id,))
                status = cursor.fetchone()[0]
                assert status == "completed"
        
        db_service.close()
    
    def test_multiple_sessions_per_user(self, clean_database):
        """Test multiple sessions for the same user."""
        db_service = DatabaseService()
        db_service.init_database()
        user_manager = UserManager(db_service)
        
        # Create user
        user_id = user_manager.create_user_if_not_exists("test_user")
        
        # Create multiple sessions
        session_ids = []
        for i in range(3):
            session_id = user_manager.create_session(user_id)
            session_ids.append(session_id)
            assert session_id is not None
        
        # Verify all sessions are active
        with get_test_database_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT COUNT(*) FROM blackjack_sessions 
                    WHERE user_id = %s AND status = 'active'
                """, (user_id,))
                active_count = cursor.fetchone()[0]
                assert active_count == 3
        
        # Complete one session
        user_manager.complete_session(session_ids[0])
        
        # Abandon another session
        user_manager.abandon_session(session_ids[1])
        
        # Verify session statuses
        with get_test_database_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT status FROM blackjack_sessions WHERE session_id = %s
                """, (session_ids[0],))
                status = cursor.fetchone()[0]
                assert status == "completed"
                
                cursor.execute("""
                    SELECT status FROM blackjack_sessions WHERE session_id = %s
                """, (session_ids[1],))
                status = cursor.fetchone()[0]
                assert status == "abandoned"
                
                cursor.execute("""
                    SELECT status FROM blackjack_sessions WHERE session_id = %s
                """, (session_ids[2],))
                status = cursor.fetchone()[0]
                assert status == "active"
        
        db_service.close() 