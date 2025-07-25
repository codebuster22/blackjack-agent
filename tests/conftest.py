"""
Pytest configuration and fixtures for the blackjack agent tests.
"""
import pytest
import pytest_asyncio
import asyncio
import subprocess
import time
import os
import sys
from contextlib import contextmanager
from typing import Generator, Dict, Any, Optional
from datetime import datetime, timedelta

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.test_helpers import (
    start_test_database, stop_test_database, wait_for_database,
    get_test_database_url, reset_database, setup_test_environment,
    cleanup_test_environment, TestDataManager
)

# Test database URL for integration tests
TEST_DATABASE_URL = get_test_database_url()


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
    Session-scoped fixture to manage Docker Compose for the test database.
    
    Starts the test database at the beginning of the test session
    and stops it at the end.
    """
    print("Starting test database...")
    start_test_database()
    
    # Wait for database to be ready
    wait_for_database()
    
    yield
    
    print("Stopping test database...")
    stop_test_database()


@pytest_asyncio.fixture(scope="session")
async def test_database(docker_compose):
    """
    Session-scoped fixture providing test database access.
    
    Ensures the test database is running and accessible.
    """
    # Test database connection
    from tests.test_helpers import get_test_database_connection
    
    async with get_test_database_connection() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute("SELECT 1")
            result = await cursor.fetchone()
            assert result[0] == 1
    
    yield test_database


@pytest_asyncio.fixture(scope="function")
async def class_database(test_database):
    """
    Function-scoped fixture providing clean database state for test classes.
    
    Resets the database before each test class to ensure isolation.
    """
    await reset_database()
    yield class_database


@pytest_asyncio.fixture(scope="function")
async def clean_database(class_database):
    """
    Function-scoped fixture providing a clean database state.
    
    Resets the database and service manager before each test.
    """
    await reset_database()
    
    # Reset the service manager to use the test database
    from services.service_manager import service_manager
    from tests.test_helpers import TEST_DATABASE_URL
    await service_manager.reset_for_tests(TEST_DATABASE_URL)
    
    yield class_database


@pytest_asyncio.fixture(scope="function")
async def test_data_manager(clean_database):
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
    await service_manager.reset_for_tests(TEST_DATABASE_URL)
    
    manager = TestDataManager()
    yield manager
    manager.cleanup()


@pytest_asyncio.fixture(scope="function")
async def test_user(test_data_manager):
    """
    Function-scoped fixture providing a standard test user.
    
    Creates a test user with default balance and returns user data.
    """
    return await test_data_manager.create_user()


@pytest_asyncio.fixture(scope="function")
async def test_session(test_user, test_data_manager):
    """
    Function-scoped fixture providing a test session for the test user.
    
    Creates a session for the test user and returns session data.
    """
    return await test_data_manager.create_session(test_user["user_id"])


@pytest_asyncio.fixture(scope="function")
async def user_manager(clean_database):
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
    await db_service.init_database()
    
    # Create user manager
    return UserManager(db_service)


@pytest_asyncio.fixture(scope="function")
async def db_service(clean_database):
    """
    Function-scoped fixture providing a database service instance.
    
    Creates a fresh database service instance with clean database state.
    """
    from services.db import DatabaseService
    
    # Set up environment variables for services
    setup_test_environment()
    
    # Create and initialize database service
    db_service = DatabaseService()
    await db_service.init_database()
    
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


@pytest_asyncio.fixture(scope="function")
async def mock_tool_context_with_data(test_user, test_session):
    """
    Function-scoped fixture providing a mock tool context with test data.
    
    Creates a mock tool context with user and session data for testing.
    """
    from unittest.mock import Mock
    
    mock_context = Mock()
    mock_context.state = {
        "user_id": test_user["username"],  # Use username as user_id
        "session_id": test_session["session_id"]
    }
    
    return mock_context


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