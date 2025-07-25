# Testing Guidelines

This document outlines how to write tests for the blackjack agent project using our established test foundation.

## Overview

Our testing infrastructure provides:
- **Docker-based PostgreSQL** database for integration tests
- **Comprehensive test helpers** for common testing tasks
- **Pytest fixtures** for dependency injection and test isolation
- **Environment management** for consistent test configuration
- **UV package manager** for dependency management

## Quick Start

Get up and running with the test suite in minutes.

```bash
# Install dependencies with UV
uv sync

# Start test database
make docker-start

# Run all tests
uv run pytest tests/ -v

# Run specific test categories
uv run pytest tests/ -m unit -v
uv run pytest tests/ -m integration -v
uv run pytest tests/ -m docker -v
```

## Test Infrastructure

The foundation that powers our test suite - database, Docker, and configuration.

### Test Database

- **Port**: 5436 (to avoid conflicts with local PostgreSQL)
- **Database**: `blackjack_test`
- **User**: `test_user`
- **Password**: `test_password`
- **Storage**: In-memory (tmpfs) for fast, clean tests

### Docker Commands

Manage the test database container lifecycle.

```bash
# Start test database
make docker-start

# Stop test database
make docker-stop

# Restart test database
make docker-restart

# View database logs
make docker-logs

# Check database status
make docker-status
```

## Test Helpers

Utility functions and classes that simplify common testing tasks and reduce boilerplate code.

### Core Test Functions

#### Database Management

Connect to and manage the test database with automatic cleanup.

```python
from tests.test_helpers import (
    get_test_database_connection,
    reset_database,
    start_test_database,
    stop_test_database
)

# Get database connection
with get_test_database_connection() as conn:
    with conn.cursor() as cursor:
        cursor.execute("SELECT 1")
        result = cursor.fetchone()

# Reset database (drops all tables)
reset_database()

# Manual database control
start_test_database()
stop_test_database()
```

#### Test Data Creation

Create and manage test data with automatic cleanup and tracking.

```python
from tests.test_helpers import (
    create_test_user,
    create_test_session,
    TestDataManager
)

# Create individual test data
user_data = create_test_user("test_user", 100.0)
session_data = create_test_session(user_data["user_id"])

# Use TestDataManager for tracking
manager = TestDataManager()
user = manager.create_user("test_user", 100.0)
session = manager.create_session(user["user_id"])
manager.cleanup()  # Clean up tracked data
```

#### Environment Setup

Configure test environment variables and ensure proper cleanup.

```python
from tests.test_helpers import (
    setup_test_environment,
    cleanup_test_environment
)

# Set up test environment variables
setup_test_environment()

# Your test code here
# ...

# Clean up environment
cleanup_test_environment()
```

### Pytest Fixtures

Pre-configured dependencies and test data that can be injected into your tests.

The test suite provides several fixtures for common testing scenarios:

#### Database Fixtures

```python
@pytest.mark.docker
@pytest.mark.database
def test_with_database(clean_database):
    """Test that uses a clean database."""
    # Database is automatically reset before each test
    pass
```

#### Service Fixtures

```python
def test_with_services(user_manager, db_service, wallet_service):
    """Test that uses initialized services."""
    # Services are properly configured with test environment
    user_id = user_manager.create_user_if_not_exists("test_user", wallet_service)
    assert user_id is not None
```

#### Data Fixtures

```python
def test_with_data(test_user, test_session):
    """Test that uses pre-created test data."""
    assert test_user["username"] is not None
    assert test_session["user_id"] == test_user["user_id"]
```

## Writing New Tests

Guidelines and patterns for writing maintainable, isolated tests that follow our conventions.

### Test Structure Guidelines

#### 1. Test Categories

Organize tests by type and requirements using pytest markers:

```python
@pytest.mark.unit          # Unit tests (no database)
@pytest.mark.integration   # Integration tests (with database)
@pytest.mark.docker        # Tests requiring Docker
@pytest.mark.database      # Tests requiring database
```

#### 2. Database Tests

Integration tests that require database access and automatic cleanup:

```python
@pytest.mark.docker
@pytest.mark.database
class TestUserManagement:
    """Test user management functionality."""
    
    def test_create_user(self, clean_database):
        """Test user creation."""
        from tests.test_helpers import create_test_user
        
        # Test code here
        user_data = create_test_user("test_user", 100.0)
        assert user_data["username"] == "test_user"
        assert user_data["balance"] == 100.0
```

#### 3. Service Tests

Tests that interact with application services (UserManager, DatabaseService):

```python
@pytest.mark.docker
@pytest.mark.database
class TestUserService:
    """Test user service functionality."""
    
    def test_user_creation(self, clean_database, user_manager, wallet_service):
        """Test user creation through service."""
        user_id = user_manager.create_user_if_not_exists("test_user", wallet_service)
        assert user_id is not None
        
        # Verify user was created
        user = user_manager.get_user(user_id)
        assert user["username"] == "test_user"
```

#### 4. Unit Tests

Pure logic tests that don't require database or external dependencies:

```python
@pytest.mark.unit
class TestGameLogic:
    """Test game logic without database."""
    
    def test_hand_evaluation(self):
        """Test hand evaluation logic."""
        # Test pure logic without database
        pass
```

### Best Practices

Essential patterns for writing reliable, maintainable tests:

#### 1. Test Isolation

Ensure tests don't interfere with each other:
- Each test should be independent
- Use `clean_database` fixture for database tests
- Reset any global state in test setup/teardown

#### 2. Test Data Management

Properly create and clean up test data to prevent pollution:

```python
def test_with_cleanup(self, clean_database):
    """Test with proper cleanup."""
    manager = TestDataManager()
    
    try:
        # Create test data
        user = manager.create_user("test_user", 100.0)
        
        # Test logic here
        assert user["balance"] == 100.0
        
    finally:
        # Clean up
        manager.cleanup()
```

#### 3. Environment Variables

Set up and tear down test environment variables properly:

```python
def test_with_environment(self):
    """Test with controlled environment."""
    setup_test_environment()
    
    try:
        # Test code here
        from config import get_config
        config = get_config()
        assert config.environment == "testing"
        
    finally:
        cleanup_test_environment()
```

#### 4. Database Connections

Use context managers for safe database operations:

```python
def test_database_operations(self, clean_database):
    """Test database operations."""
    with get_test_database_connection() as conn:
        with conn.cursor() as cursor:
            # Database operations here
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            assert result[0] == 1
```

### Test File Organization

Recommended structure for organizing test files by type and functionality:

```
tests/
├── conftest.py              # Pytest fixtures and configuration
├── test_helpers.py          # Test utilities and helpers
├── test_foundation.py       # Foundation tests
├── unit/                    # Unit tests (no database)
│   ├── test_game_logic.py
│   └── test_utils.py
├── integration/             # Integration tests (with database)
│   ├── test_user_management.py
│   ├── test_session_management.py
│   └── test_game_flow.py
└── dealer/                  # Dealer-specific tests
    ├── unit/
    └── integration/
```

## Configuration

Settings and environment variables that control test behavior and database connections.

### Environment Variables

The test suite uses the following environment variables (automatically set by `setup_test_environment()`):

```bash
# Database Configuration
DATABASE_URL=postgresql://test_user:test_password@localhost:5436/blackjack_test
DB_POOL_SIZE=5
DB_TIMEOUT=30

# Session Configuration
SESSION_NAMESPACE=blackjack-game
SESSION_DEFAULT_STATUS=active

# Logging Configuration
LOG_LEVEL=DEBUG
LOG_FORMAT=%(asctime)s - %(name)s - %(levelname)s - %(message)s

# Game Configuration
GAME_STARTING_CHIPS=100.0
GAME_MIN_BET=1.0
GAME_MAX_BET=1000.0
GAME_SHOE_THRESHOLD=50

# API Configuration
GOOGLE_GENAI_USE_VERTEXAI=false
GOOGLE_API_KEY=test_key
XAI_API_KEY=test_xai_key

# Environment
ENVIRONMENT=testing
DEBUG=false
```

See `ENVIRONMENT_VARIABLES.md` for complete documentation.

### Test Configuration

Pytest configuration and markers for organizing and running tests:

The test suite is configured via `pytest.ini`:

```ini
[tool:pytest]
markers =
    unit: Unit tests (no database)
    integration: Integration tests (with database)
    docker: Tests requiring Docker
    database: Tests requiring database
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
```

## Running Tests

Commands and options for executing tests with UV and pytest.

### Basic Commands

```bash
# Run all tests
uv run pytest tests/

# Run with verbose output
uv run pytest tests/ -v

# Run with coverage
uv run pytest tests/ --cov=.

# Run specific test file
uv run pytest tests/test_foundation.py

# Run specific test class
uv run pytest tests/test_foundation.py::TestFoundation

# Run specific test method
uv run pytest tests/test_foundation.py::TestFoundation::test_database_connection
```

### Test Categories

Filter and run specific types of tests:

```bash
# Run only unit tests
uv run pytest tests/ -m unit

# Run only integration tests
uv run pytest tests/ -m integration

# Run only database tests
uv run pytest tests/ -m database

# Run only Docker tests
uv run pytest tests/ -m docker

# Run tests excluding Docker
uv run pytest tests/ -m "not docker"
```

### Parallel Execution

Speed up test execution by running tests in parallel:

```bash
# Run tests in parallel (requires pytest-xdist)
uv run pytest tests/ -n auto

# Run with specific number of workers
uv run pytest tests/ -n 4
```

## Debugging Tests

Techniques and tools for troubleshooting test failures and understanding test behavior.

### Database Debugging

```python
def test_debug_database(self, clean_database):
    """Debug database state."""
    with get_test_database_connection() as conn:
        with conn.cursor() as cursor:
            # Check what tables exist
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            tables = cursor.fetchall()
            print(f"Tables: {tables}")
            
            # Check table contents
            cursor.execute("SELECT * FROM users LIMIT 5")
            users = cursor.fetchall()
            print(f"Users: {users}")
```

### Environment Debugging

Inspect environment variables and configuration during tests:

```python
def test_debug_environment(self):
    """Debug environment variables."""
    setup_test_environment()
    
    import os
    print(f"DATABASE_URL: {os.environ.get('DATABASE_URL')}")
    print(f"ENVIRONMENT: {os.environ.get('ENVIRONMENT')}")
    
    from config import get_config
    config = get_config()
    print(f"Config environment: {config.environment}")
    
    cleanup_test_environment()
```

## Test Reports

Generate and view test coverage and result reports.

### Coverage Reports

```bash
# Generate coverage report
uv run pytest tests/ --cov=. --cov-report=html

# View coverage in browser
open htmlcov/index.html
```

### Test Reports

Generate detailed test result reports in various formats:

```bash
# Generate JUnit XML report
uv run pytest tests/ --junitxml=test-results.xml

# Generate HTML report
uv run pytest tests/ --html=test-report.html --self-contained-html
```

## Troubleshooting

Solutions for common problems and issues you might encounter.

### Common Issues

#### Database Connection Issues

Resolve database connectivity and container problems:

```bash
# Check if database is running
make docker-status

# Restart database
make docker-restart

# Check database logs
make docker-logs
```

#### Test Environment Issues

Fix environment variable and configuration problems:

```python
# Ensure environment is set up
setup_test_environment()

# Check configuration loading
from config import get_config
config = get_config()
print(f"Config loaded: {config.environment}")
```

#### Docker Issues

Resolve Docker container and networking problems:

```bash
# Check Docker status
docker ps

# Clean up Docker containers
docker-compose -f docker-compose.test.yml down

# Rebuild containers
docker-compose -f docker-compose.test.yml up --build -d
```

## Additional Resources

External documentation and references for further learning:

- [Environment Variables Reference](ENVIRONMENT_VARIABLES.md)
- [Pytest Documentation](https://docs.pytest.org/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

## Contributing

Guidelines for contributing new tests and maintaining test quality.

When adding new tests:

1. Follow the test structure guidelines
2. Use appropriate pytest markers
3. Ensure test isolation
4. Add proper cleanup
5. Document any new test helpers
6. Update this README if needed

For questions about the testing infrastructure, refer to `tests/test_foundation.py` for examples.
