"""
Test helpers for Docker management, database operations, and test data creation.
"""
import os
import time
import subprocess
import uuid
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager
from datetime import datetime
import psycopg
import pytest

# Test database configuration
TEST_DB_CONFIG = {
    "host": "localhost",
    "port": 5436,
    "dbname": "blackjack_test",
    "user": "test_user",
    "password": "test_password"
}

TEST_DATABASE_URL = f"postgresql://{TEST_DB_CONFIG['user']}:{TEST_DB_CONFIG['password']}@{TEST_DB_CONFIG['host']}:{TEST_DB_CONFIG['port']}/{TEST_DB_CONFIG['dbname']}"


class DockerComposeError(Exception):
    """Raised when Docker Compose operations fail."""
    pass


class DatabaseError(Exception):
    """Raised when database operations fail."""
    pass


def run_docker_compose_command(command: str, compose_file: str = "docker-compose.test.yml") -> subprocess.CompletedProcess:
    """
    Run a Docker Compose command and return the result.
    
    Args:
        command: Docker Compose command (e.g., "up", "down", "ps")
        compose_file: Path to the Docker Compose file
        
    Returns:
        subprocess.CompletedProcess: The result of the command
        
    Raises:
        DockerComposeError: If the command fails
    """
    try:
        result = subprocess.run(
            ["docker", "compose", "-f", compose_file] + command.split(),
            capture_output=True,
            text=True,
            check=True
        )
        return result
    except subprocess.CalledProcessError as e:
        raise DockerComposeError(f"Docker Compose command '{command}' failed: {e.stderr}")


def start_test_database() -> None:
    """
    Start the test database using Docker Compose.
    
    Raises:
        DockerComposeError: If starting the database fails
    """
    try:
        print("Starting test database...")
        run_docker_compose_command("up -d")
        wait_for_database()
        print("Test database started successfully")
    except Exception as e:
        raise DockerComposeError(f"Failed to start test database: {e}")


def stop_test_database() -> None:
    """
    Stop and cleanup the test database using Docker Compose.
    
    Raises:
        DockerComposeError: If stopping the database fails
    """
    try:
        print("Stopping test database...")
        run_docker_compose_command("down -v")
        print("Test database stopped successfully")
    except Exception as e:
        raise DockerComposeError(f"Failed to stop test database: {e}")


def wait_for_database(timeout: int = 60, interval: float = 2.0) -> None:
    """
    Wait for the database to be ready by verifying actual database connectivity.
    
    This function ensures:
    - PostgreSQL server is accepting connections
    - The test database exists and is accessible
    - The test user can connect and perform operations
    - Basic schema operations work
    
    Args:
        timeout: Maximum time to wait in seconds
        interval: Time between polls in seconds
        
    Raises:
        DatabaseError: If the database doesn't become ready within timeout
    """
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            # Test actual database connectivity using the DATABASE_URL
            database_url = get_test_database_url()
            
            # Try connecting using psycopg3 async connection
            async def test_database_ready():
                try:
                    conn = await psycopg.AsyncConnection.connect(database_url)
                    async with conn.cursor() as cursor:
                        # Test basic operations
                        await cursor.execute("SELECT 1")
                        result = await cursor.fetchone()
                        assert result[0] == 1
                        
                        # Test that we can create and drop a table (verify permissions)
                        await cursor.execute("CREATE TABLE IF NOT EXISTS _test_connectivity (id INTEGER)")
                        await cursor.execute("DROP TABLE IF EXISTS _test_connectivity")
                        await conn.commit()
                    
                    await conn.close()
                    return True
                except Exception:
                    return False
            
            # Run the async test
            import asyncio
            if asyncio.run(test_database_ready()):
                print("✅ Database is ready and accessible")
                return
                    
        except Exception as e:
            # Log the specific error for debugging
            print(f"Database not ready yet: {e}")
        
        time.sleep(interval)
    
    raise DatabaseError(f"Database did not become ready within {timeout} seconds")


def get_test_database_url() -> str:
    """
    Get the test database connection URL.
    
    Returns:
        str: The database connection URL
    """
    return TEST_DATABASE_URL


@asynccontextmanager
async def get_test_database_connection():
    """
    Get a connection to the test database using DATABASE_URL.
    
    Yields:
        psycopg.AsyncConnection: Database connection
        
    Raises:
        DatabaseError: If connection fails
    """
    conn = None
    try:
        # Use DATABASE_URL directly for consistency
        database_url = get_test_database_url()
        conn = await psycopg.AsyncConnection.connect(database_url)
        yield conn
    except Exception as e:
        raise DatabaseError(f"Failed to connect to test database: {e}")
    finally:
        if conn:
            await conn.close()


async def reset_database() -> None:
    """
    Reset the database by dropping all tables and recreating them.
    
    Raises:
        DatabaseError: If reset fails
    """
    try:
        async with get_test_database_connection() as conn:
            async with conn.cursor() as cursor:
                # Drop all tables in public schema
                await cursor.execute("""
                    DO $$ 
                    DECLARE 
                        r RECORD;
                    BEGIN
                        FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP
                            EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
                        END LOOP;
                    END $$;
                """)
                
                # Drop all sequences
                await cursor.execute("""
                    DO $$ 
                    DECLARE 
                        r RECORD;
                    BEGIN
                        FOR r IN (SELECT sequence_name FROM information_schema.sequences WHERE sequence_schema = 'public') LOOP
                            EXECUTE 'DROP SEQUENCE IF EXISTS ' || quote_ident(r.sequence_name) || ' CASCADE';
                        END LOOP;
                    END $$;
                """)
                
                await conn.commit()
    except Exception as e:
        raise DatabaseError(f"Failed to reset database: {e}")


async def create_test_user(username: Optional[str] = None, initial_balance: float = 100.0) -> Dict[str, Any]:
    """
    Create a test user with the given username and initial balance.
    
    Args:
        username: Username for the test user (generates UUID5 if None)
        initial_balance: Initial chip balance
        
    Returns:
        Dict[str, Any]: User data including user_id and username
        
    Raises:
        DatabaseError: If user creation fails
    """
    if username is None:
        username = f"test_user_{uuid.uuid4().hex[:8]}"
    
    try:
        from services.service_manager import service_manager
        
        # Create user using the service manager (which should be configured for tests)
        username = await service_manager.user_manager.create_user_if_not_exists(username)
        
        # Set initial balance if different from default
        if initial_balance != 100.0:  # Default from config
            await service_manager.user_manager.credit_user_balance(username, initial_balance - 100.0)
        
        return {
            "user_id": username,  # For backward compatibility, return username as user_id
            "username": username,
            "balance": initial_balance
        }
    except Exception as e:
        raise DatabaseError(f"Failed to create test user: {e}")


async def create_test_session(username: str) -> Dict[str, Any]:
    """
    Create a test session for the given username.

    Args:
        username: Username for the test user

    Returns:
        Dict[str, Any]: Session data including session_id

    Raises:
        DatabaseError: If session creation fails
    """
    try:
        from services.service_manager import service_manager

        # Create session using the service manager
        session_id = await service_manager.user_manager.create_session(username)

        return {
            "session_id": session_id,
            "user_id": username,  # For backward compatibility
            "status": "active"
        }
    except Exception as e:
        raise DatabaseError(f"Failed to create test session: {e}")


def get_test_balance() -> float:
    """
    Get the standard test starting balance.
    
    Returns:
        float: Standard test balance (100.0)
    """
    return 100.0


def setup_test_environment() -> None:
    """
    Set up the test environment by setting all required environment variables.
    """
    # Database Configuration (using nested format expected by config)
    os.environ["DATABASE__URL"] = TEST_DATABASE_URL
    os.environ["DATABASE__POOL_SIZE"] = "20"  # Increased for tests
    os.environ["DATABASE__TIMEOUT"] = "30"
    
    # Session Configuration
    os.environ["SESSION__NAMESPACE"] = "blackjack-game"
    os.environ["SESSION__DEFAULT_STATUS"] = "active"
    
    # Logging Configuration
    os.environ["LOGGING__LEVEL"] = "DEBUG"
    os.environ["LOGGING__FORMAT"] = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Game Configuration
    os.environ["GAME__STARTING_CHIPS"] = "100.0"
    os.environ["GAME__MIN_BET"] = "5.0"
    os.environ["GAME__MAX_BET"] = "1000.0"
    os.environ["GAME__SHOE_THRESHOLD"] = "50"
    
    # Environment
    os.environ["ENVIRONMENT"] = "testing"
    os.environ["DEBUG"] = "false"
    
    # API Configuration
    os.environ["API__GOOGLE_GENAI_USE_VERTEXAI"] = "false"
    os.environ["API__GOOGLE_API_KEY"] = "test_key"
    os.environ["API__XAI_API_KEY"] = "test_xai_key"


def cleanup_test_environment() -> None:
    """
    Clean up test environment variables.
    """
    test_env_vars = [
        # Database Configuration
        "DATABASE__URL", "DATABASE__POOL_SIZE", "DATABASE__TIMEOUT",
        # Session Configuration
        "SESSION__NAMESPACE", "SESSION__DEFAULT_STATUS",
        # Logging Configuration
        "LOGGING__LEVEL", "LOGGING__FORMAT",
        # Game Configuration
        "GAME__STARTING_CHIPS", "GAME__MIN_BET", "GAME__MAX_BET", "GAME__SHOE_THRESHOLD",
        # Environment
        "ENVIRONMENT", "DEBUG",
        # API Configuration
        "API__GOOGLE_GENAI_USE_VERTEXAI", "API__GOOGLE_API_KEY", "API__XAI_API_KEY"
    ]
    
    for key in test_env_vars:
        os.environ.pop(key, None)


class TestDataManager:  # noqa: N801
    """Manager for creating and managing test data."""
    
    # Exclude from pytest collection since this is not a test class
    __test__ = False
    
    def __init__(self):
        self.created_users = []
        self.created_sessions = []
    
    async def create_user(self, username: Optional[str] = None, balance: float = 100.0) -> Dict[str, Any]:
        """Create a test user and track it for cleanup."""
        user_data = await create_test_user(username, balance)
        self.created_users.append(user_data)
        return user_data
    
    async def create_session(self, user_id: str) -> Dict[str, Any]:
        """Create a test session and track it for cleanup."""
        session_data = await create_test_session(user_id)
        self.created_sessions.append(session_data)
        return session_data
    
    def cleanup(self) -> None:
        """Clean up all created test data."""
        # Sessions are automatically cleaned up by the database
        # Users can be left as they don't interfere with tests
        self.created_users.clear()
        self.created_sessions.clear()


# Pytest markers for test categorization
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "docker: mark test as requiring Docker Compose"
    )
    config.addinivalue_line(
        "markers", "database: mark test as requiring database"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as unit test"
    ) 