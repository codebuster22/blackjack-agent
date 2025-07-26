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
import asyncio
import logging
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock

import psycopg
from psycopg.rows import dict_row
from web3 import Web3
from eth_account import Account

from config import get_config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        
        # Use mock wallet service for tests to avoid real blockchain transactions
        mock_wallet_service = MockWalletService()
        
        # Create user using the mock wallet service
        username = await service_manager.user_manager.create_user_if_not_exists(username, mock_wallet_service)
        
        # Get wallet info (from mock)
        wallet_info = await service_manager.user_manager.get_user_wallet_info(username)
        wallet_address = wallet_info['wallet_address']
        
        # Set initial balance if different from default
        if initial_balance != 100.0:  # Default from config
            await service_manager.user_manager.credit_user_balance(username, initial_balance - 100.0)
        
        return {
            "user_id": username,  # For backward compatibility, return username as user_id
            "username": username,
            "balance": initial_balance,
            "wallet_address": wallet_address,
            "funded": True  # Mock wallets are always "funded"
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


async def fund_wallet_with_eth(wallet_address: str, amount_eth: float = 0.005) -> bool:
    """
    Fund a wallet with ETH using the dealer's private key.
    
    Args:
        wallet_address: The wallet address to fund
        amount_eth: Amount of ETH to send (default: 0.002 ETH)
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Get dealer private key from environment
        dealer_private_key = os.getenv('DEALER_PRIVATE_KEY')
        if not dealer_private_key:
            logger.warning("DEALER_PRIVATE_KEY not found, skipping wallet funding")
            return False
        
        # Get RPC URL from config
        config = get_config()
        rpc_url = os.getenv('RPC_URL', 'https://testnet-rpc.monad.xyz')
        
        # Initialize Web3
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        
        # Create account from private key
        dealer_account = Account.from_key(dealer_private_key)
        dealer_address = dealer_account.address
        
        logger.info(f"Funding wallet {wallet_address} with {amount_eth} ETH from {dealer_address}")
        
        # Convert ETH to Wei
        amount_wei = w3.to_wei(amount_eth, 'ether')
        
        # Get current gas price
        gas_price = w3.eth.gas_price
        
        # Estimate gas for the transaction
        gas_estimate = w3.eth.estimate_gas({
            'from': dealer_address,
            'to': wallet_address,
            'value': amount_wei
        })
        
        # Build transaction
        transaction = {
            'from': dealer_address,
            'to': wallet_address,
            'value': amount_wei,
            'gas': gas_estimate,
            'gasPrice': gas_price,
            'nonce': w3.eth.get_transaction_count(dealer_address),
        }
        
        # Sign transaction
        signed_txn = w3.eth.account.sign_transaction(transaction, dealer_private_key)
        
        # Send transaction
        tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
        
        # Wait for transaction to be mined
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
        
        if tx_receipt.status == 1:
            logger.info(f"Successfully funded wallet {wallet_address} with {amount_eth} ETH. TX: {tx_hash.hex()}")
            return True
        else:
            logger.error(f"Transaction failed for wallet {wallet_address}")
            return False
            
    except Exception as e:
        logger.error(f"Failed to fund wallet {wallet_address}: {e}")
        return False


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
    
    # Privy Configuration
    os.environ["PRIVY__APP_ID"] = "cmdiixr3500b6js0j81dkty6g"
    os.environ["PRIVY__APP_SECRET"] = "4qgfY9qPy8vzjE4XVzk24y2NzXmvMMtRquQZYJds2kXF1t73g9y7LKzvy7eKsYXC25eurz71TGcrtXXxoMhasLr7"
    os.environ["PRIVY__BASE_URL"] = "https://api.privy.io/"
    os.environ["PRIVY__ENVIRONMENT"] = "staging"
    os.environ["PRIVY__REGISTRATION_CONTRACT_ADDRESS"] = "0x0000000000000000000000000000000000000000"
    os.environ["PRIVY__CAIP_CHAIN_ID"] = "eip155:10143"
    
    # Blockchain Configuration
    os.environ["RPC_URL"] = "https://testnet-rpc.monad.xyz"


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
        "API__GOOGLE_GENAI_USE_VERTEXAI", "API__GOOGLE_API_KEY", "API__XAI_API_KEY",
        # Privy Configuration
        "PRIVY__APP_ID", "PRIVY__APP_SECRET", "PRIVY__BASE_URL", "PRIVY__ENVIRONMENT",
        "PRIVY__REGISTRATION_CONTRACT_ADDRESS", "PRIVY__CAIP_CHAIN_ID",
        # Blockchain Configuration
        "RPC_URL"
    ]
    
    for key in test_env_vars:
        os.environ.pop(key, None)


# Mock Wallet Service for testing
class MockWalletService:
    """Mock wallet service for testing user creation."""
    
    def __init__(self):
        self.created_wallets = {}
    
    async def register_user_onchain(self):
        """Mock wallet creation and registration - no real blockchain transaction."""
        # Generate mock wallet data
        wallet_id = f"mock_wallet_{uuid.uuid4().hex[:8]}"
        wallet_address = f"0x{uuid.uuid4().hex[:40]}"
        
        # Create mock wallet wrapper
        mock_wallet = MagicMock()
        mock_wallet.get_wallet_id.return_value = wallet_id
        mock_wallet.get_wallet_address.return_value = wallet_address
        
        # Store for potential future use
        self.created_wallets[wallet_id] = wallet_address
        
        # Mock transaction hash (no real transaction)
        tx_hash = f"0x{uuid.uuid4().hex[:64]}"
        
        return mock_wallet, tx_hash
    
    async def create_wallet(self):
        """Mock wallet creation."""
        wallet_id = f"mock_wallet_{uuid.uuid4().hex[:8]}"
        wallet_address = f"0x{uuid.uuid4().hex[:40]}"
        
        mock_wallet = MagicMock()
        mock_wallet.get_wallet_id.return_value = wallet_id
        mock_wallet.get_wallet_address.return_value = wallet_address
        
        self.created_wallets[wallet_id] = wallet_address
        return mock_wallet
    
    async def get_wallet(self, wallet_id: str):
        """Mock wallet retrieval."""
        if wallet_id in self.created_wallets:
            mock_wallet = MagicMock()
            mock_wallet.get_wallet_id.return_value = wallet_id
            mock_wallet.get_wallet_address.return_value = self.created_wallets[wallet_id]
            return mock_wallet
        else:
            raise ValueError(f"Wallet {wallet_id} not found")
    
    def is_initialized(self):
        """Mock initialization check."""
        return True


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