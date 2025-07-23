"""
Test to verify the foundation setup works correctly.
"""
import pytest
import os
from tests.test_helpers import (
    TEST_DATABASE_URL,
    setup_test_environment,
    cleanup_test_environment,
    get_test_database_connection
)


@pytest.mark.docker
@pytest.mark.database
class TestFoundation:
    """Test that the foundation setup works correctly."""
    
    def test_environment_setup(self):
        """Test that test environment variables are set correctly."""
        setup_test_environment()
        
        assert os.environ["DATABASE__URL"] == TEST_DATABASE_URL
        assert os.environ["ENVIRONMENT"] == "testing"
        assert os.environ["LOGGING__LEVEL"] == "DEBUG"
        assert os.environ["GAME__STARTING_CHIPS"] == "100.0"
        
        cleanup_test_environment()
    
    def test_database_connection(self, clean_database):
        """Test that we can connect to the test database."""
        with get_test_database_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1 as test_value")
                result = cursor.fetchone()
                assert result[0] == 1
    
    def test_database_reset(self, clean_database):
        """Test that database reset works."""
        from tests.test_helpers import reset_database
        
        # Create a test table to verify reset works
        with get_test_database_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS test_reset (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(50)
                    )
                """)
                cursor.execute("INSERT INTO test_reset (name) VALUES ('test')")
                conn.commit()
                
                # Verify data exists
                cursor.execute("SELECT COUNT(*) FROM test_reset")
                count_before = cursor.fetchone()[0]
                assert count_before > 0
        
        # Reset database
        reset_database()
        
        # Verify table is dropped (data is gone)
        with get_test_database_connection() as conn:
            with conn.cursor() as cursor:
                try:
                    cursor.execute("SELECT COUNT(*) FROM test_reset")
                    assert False, "Table should not exist after reset"
                except Exception as e:
                    # Expected: table should be dropped
                    assert "test_reset" in str(e) or "does not exist" in str(e)
    
    def test_test_user_creation(self, clean_database, test_data_manager):
        """Test that test user creation works."""
        user_data = test_data_manager.create_user("test_user_123", 200.0)
        
        assert user_data["username"] == "test_user_123"
        assert user_data["balance"] == 200.0
        assert "user_id" in user_data
    
    def test_test_session_creation(self, clean_database, test_data_manager):
        """Test that test session creation works."""
        user_data = test_data_manager.create_user()
        session_data = test_data_manager.create_session(user_data["user_id"])
        
        assert session_data["user_id"] == user_data["user_id"]
        assert "session_id" in session_data
        assert "created_at" in session_data


@pytest.mark.unit
class TestFoundationUnit:
    """Unit tests for foundation components."""
    
    def test_test_balance(self):
        """Test that test balance helper works."""
        from tests.test_helpers import get_test_balance
        assert get_test_balance() == 100.0
    
    def test_test_data_manager(self):
        """Test that TestDataManager works correctly."""
        from tests.test_helpers import TestDataManager
        
        manager = TestDataManager()
        assert len(manager.created_users) == 0
        assert len(manager.created_sessions) == 0
        
        manager.cleanup()
        assert len(manager.created_users) == 0
        assert len(manager.created_sessions) == 0 