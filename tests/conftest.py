"""
Pytest configuration and fixtures for the blackjack agent tests.
"""
import pytest
import os
from typing import Generator, Dict, Any
from unittest.mock import Mock

from tests.test_helpers import (
    start_test_database,
    stop_test_database,
    wait_for_database,
    reset_database,
    setup_test_environment,
    cleanup_test_environment,
    create_test_user,
    create_test_session,
    TestDataManager,
    get_test_database_connection,
    TEST_DATABASE_URL
)


def pytest_configure(config):
    """Configure pytest with custom markers and setup."""
    # Register custom markers
    config.addinivalue_line("markers", "docker: mark test as requiring Docker Compose")
    config.addinivalue_line("markers", "database: mark test as requiring database")
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "unit: mark test as unit test")
    config.addinivalue_line("markers", "slow: mark test as slow running")


def pytest_sessionstart(session):
    """Set up test environment at the start of the test session."""
    setup_test_environment()


def pytest_sessionfinish(session, exitstatus):
    """Clean up test environment at the end of the test session."""
    cleanup_test_environment()


@pytest.fixture(scope="session")
def docker_compose():
    """
    Session-scoped fixture to manage Docker Compose lifecycle.
    
    Starts the test database at the beginning of the test session
    and stops it at the end.
    """
    # Check if database is already running
    try:
        with get_test_database_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
            # Database is already running, don't start/stop
            yield
            return
    except Exception:
        pass
    
    # Start database if not running
    try:
        start_test_database()
        yield
    finally:
        # Only stop if we started it
        try:
            stop_test_database()
        except Exception:
            pass  # Ignore errors when stopping


@pytest.fixture(scope="session")
def test_database(docker_compose):
    """
    Session-scoped fixture providing database connection.
    
    Depends on docker_compose fixture to ensure database is running.
    """
    # Wait for database to be ready
    wait_for_database()
    
    # Test connection
    with get_test_database_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1")
    
    yield TEST_DATABASE_URL


@pytest.fixture(scope="class")
def class_database(test_database):
    """
    Class-scoped fixture providing clean database state for each test class.
    
    Resets the database before each test class to ensure clean state.
    """
    reset_database()
    yield test_database


@pytest.fixture(scope="function")
def clean_database(class_database):
    """
    Function-scoped fixture providing clean database state for each test.
    
    Resets the database before each test to ensure complete isolation.
    """
    reset_database()
    
    # Reset the service manager to use the test database
    from services.service_manager import service_manager
    from tests.test_helpers import TEST_DATABASE_URL
    service_manager.reset_for_tests(TEST_DATABASE_URL)
    
    yield class_database


@pytest.fixture(scope="function")
def test_data_manager(clean_database):
    """
    Function-scoped fixture providing test data management.
    
    Creates and tracks test data for automatic cleanup.
    """
    # Set up test environment and reload config
    from tests.test_helpers import setup_test_environment
    from config import reload_config, config
    
    setup_test_environment()
    
    # Force config reload by clearing the global config
    import config as config_module
    config_module.config = None
    reload_config()  # Reload config with test environment variables
    
    # Ensure service manager is reset before creating test data
    from services.service_manager import service_manager
    from tests.test_helpers import TEST_DATABASE_URL
    service_manager.reset_for_tests(TEST_DATABASE_URL)
    
    manager = TestDataManager()
    yield manager
    manager.cleanup()


@pytest.fixture(scope="function")
def test_user(test_data_manager):
    """
    Function-scoped fixture providing a standard test user.
    
    Creates a test user with default balance and returns user data.
    """
    return test_data_manager.create_user()


@pytest.fixture(scope="function")
def test_session(test_user, test_data_manager):
    """
    Function-scoped fixture providing a test session for the test user.
    
    Creates a session for the test user and returns session data.
    """
    return test_data_manager.create_session(test_user["user_id"])


@pytest.fixture(scope="function")
def user_manager(clean_database):
    """
    Function-scoped fixture providing a UserManager instance.
    
    Creates a fresh UserManager instance with clean database state.
    """
    from services.user_manager import UserManager
    from services.db import DatabaseService
    
    # Set up environment variables for services
    setup_test_environment()
    
    # Create and initialize database service
    db_service = DatabaseService()
    db_service.init_database()
    
    # Create user manager
    return UserManager(db_service)


@pytest.fixture(scope="function")
def db_service(clean_database):
    """
    Function-scoped fixture providing a database service instance.
    
    Creates a fresh database service instance with clean database state.
    """
    from services.db import DatabaseService
    
    # Set up environment variables for services
    setup_test_environment()
    
    # Create and initialize database service
    db_service = DatabaseService()
    db_service.init_database()
    
    return db_service


@pytest.fixture(scope="function")
def mock_tool_context():
    """
    Function-scoped fixture providing a mock ToolContext.
    
    Creates a mock ToolContext with test user and session data.
    """
    context = Mock()
    context.state = {
        "user_id": "test_user_id",
        "session_id": "test_session_id"
    }
    return context


@pytest.fixture(scope="function")
def mock_tool_context_with_data(test_user, test_session):
    """
    Function-scoped fixture providing a mock ToolContext with real test data.
    
    Creates a mock ToolContext populated with actual test user and session data.
    """
    context = Mock()
    context.state = {
        "user_id": test_user["user_id"],
        "session_id": test_session["session_id"]
    }
    return context


@pytest.fixture(scope="function")
def sample_game_state():
    """
    Function-scoped fixture providing a sample game state.
    
    Creates a sample game state for testing game logic.
    """
    from dealer_agent.tools.dealer import GameState, Hand, Card, Suit, Rank
    
    # Create sample cards
    player_cards = [
        Card(suit=Suit.hearts, rank=Rank.ten),
        Card(suit=Suit.spades, rank=Rank.ace)
    ]
    
    dealer_cards = [
        Card(suit=Suit.diamonds, rank=Rank.king),
        Card(suit=Suit.clubs, rank=Rank.six)
    ]
    
    # Create sample shoe (simplified)
    shoe = [Card(suit=Suit.hearts, rank=Rank.two) for _ in range(10)]
    
    return GameState(
        shoe=shoe,
        player_hand=Hand(cards=player_cards),
        dealer_hand=Hand(cards=dealer_cards),
        bet=25.0,
        chips=75.0,
        history=[]
    )


@pytest.fixture(scope="function")
def sample_hand():
    """
    Function-scoped fixture providing a sample hand.
    
    Creates a sample hand for testing hand evaluation.
    """
    from dealer_agent.tools.dealer import Hand, Card, Suit, Rank
    
    cards = [
        Card(suit=Suit.hearts, rank=Rank.ten),
        Card(suit=Suit.spades, rank=Rank.ace)
    ]
    
    return Hand(cards=cards)


@pytest.fixture(scope="function")
def sample_card():
    """
    Function-scoped fixture providing a sample card.
    
    Creates a sample card for testing card operations.
    """
    from dealer_agent.tools.dealer import Card, Suit, Rank
    
    return Card(suit=Suit.hearts, rank=Rank.ace)


# Database-specific fixtures for integration tests
@pytest.fixture(scope="function")
def database_connection(clean_database):
    """
    Function-scoped fixture providing a database connection.
    
    Provides a direct database connection for integration tests.
    """
    with get_test_database_connection() as conn:
        yield conn


@pytest.fixture(scope="function")
def database_cursor(database_connection):
    """
    Function-scoped fixture providing a database cursor.
    
    Provides a database cursor for direct SQL operations in tests.
    """
    with database_connection.cursor() as cursor:
        yield cursor


# Configuration fixtures
@pytest.fixture(scope="function")
def test_config():
    """
    Function-scoped fixture providing test configuration.
    
    Provides configuration settings for testing.
    """
    return {
        "database_url": TEST_DATABASE_URL,
        "environment": "testing",
        "log_level": "DEBUG",
        "game_starting_chips": 100.0
    }


# Error handling fixtures
@pytest.fixture(scope="function")
def mock_database_error():
    """
    Function-scoped fixture providing a mock database error.
    
    Creates a mock database error for testing error handling.
    """
    from tests.test_helpers import DatabaseError
    return DatabaseError("Mock database error for testing")


@pytest.fixture(scope="function")
def mock_docker_error():
    """
    Function-scoped fixture providing a mock Docker error.
    
    Creates a mock Docker error for testing error handling.
    """
    from tests.test_helpers import DockerComposeError
    return DockerComposeError("Mock Docker error for testing")


# Performance testing fixtures
@pytest.fixture(scope="function")
def performance_timer():
    """
    Function-scoped fixture providing performance timing.
    
    Provides timing utilities for performance testing.
    """
    import time
    
    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None
        
        def start(self):
            self.start_time = time.time()
        
        def stop(self):
            self.end_time = time.time()
        
        def elapsed(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return None
    
    return Timer()


# Cleanup utilities
def pytest_collection_modifyitems(config, items):
    """Add markers to tests based on their names or content."""
    for item in items:
        # Mark tests that require database
        if any(keyword in item.name.lower() for keyword in ["database", "db", "user", "session"]):
            item.add_marker(pytest.mark.database)
        
        # Mark integration tests
        if "integration" in item.name.lower() or "test_" in item.name.lower():
            item.add_marker(pytest.mark.integration)
        
        # Mark unit tests
        if "unit" in item.name.lower():
            item.add_marker(pytest.mark.unit)
        
        # Mark slow tests
        if any(keyword in item.name.lower() for keyword in ["slow", "performance", "stress"]):
            item.add_marker(pytest.mark.slow) 