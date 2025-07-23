# Test Foundation Setup

This directory contains the test foundation for the blackjack-agent project, including Docker Compose configuration, pytest fixtures, and test helpers.

## Overview

The test foundation provides:

- **Docker Compose** configuration for isolated PostgreSQL testing with in-memory storage
- **Pytest fixtures** for database lifecycle management
- **Test helpers** for common testing operations
- **Test data management** for creating and cleaning up test data
- **Environment management** for test-specific configuration

### In-Memory Database Benefits

- **⚡ Faster Tests**: No disk I/O, all data in RAM
- **🧹 Clean State**: No persistent data between test runs
- **🚀 Quick Startup**: No volume mounting or disk initialization
- **💾 Memory Efficient**: 256MB tmpfs allocation
- **🔄 Instant Reset**: Container restart = fresh database

## Quick Start

### Prerequisites

1. **Docker and Docker Compose** installed and running
2. **Python dependencies** installed (see `pyproject.toml`)
3. **PostgreSQL client** (psycopg2) for database operations

### Running Tests

```bash
# Run all tests (will start Docker Compose automatically)
pytest

# Run only unit tests (no database required)
pytest -m unit

# Run only database tests
pytest -m database

# Run only integration tests
pytest -m integration

# Run tests with verbose output
pytest -v

# Run specific test file
pytest tests/test_foundation.py

# Run tests and stop on first failure
pytest -x
```

### Manual Docker Management

```bash
# Start test database manually
docker-compose -f docker-compose.test.yml up -d

# Check database status
docker-compose -f docker-compose.test.yml ps

# Stop and cleanup
docker-compose -f docker-compose.test.yml down -v
```

## Test Structure

```
tests/
├── conftest.py                 # Pytest fixtures and configuration
├── test_helpers.py             # Test utilities and helpers
├── test_foundation.py          # Foundation verification tests
├── docker-compose.test.yml     # Test database configuration
├── services/                   # Service-specific tests
│   ├── __init__.py
│   ├── test_user_manager.py
│   ├── test_db_service.py
│   └── test_card_utils.py
└── dealer/                     # Dealer agent tests
    ├── integration/
    └── unit/
```

## Fixtures

### Database Fixtures

- **`docker_compose`** (session): Manages Docker Compose lifecycle
- **`test_database`** (session): Provides database connection URL
- **`class_database`** (class): Clean database state per test class
- **`clean_database`** (function): Clean database state per test

### Test Data Fixtures

- **`test_data_manager`** (function): Manages test data creation and cleanup
- **`test_user`** (function): Standard test user with default balance
- **`test_session`** (function): Test session for the test user

### Service Fixtures

- **`user_manager`** (function): Fresh UserManager instance
- **`db_service`** (function): Fresh DatabaseService instance

### Mock Fixtures

- **`mock_tool_context`** (function): Mock ToolContext with test data
- **`mock_tool_context_with_data`** (function): Mock ToolContext with real test data

### Sample Data Fixtures

- **`sample_game_state`** (function): Sample game state for testing
- **`sample_hand`** (function): Sample hand for testing
- **`sample_card`** (function): Sample card for testing

## Test Helpers

### Docker Management

```python
from tests.test_helpers import start_test_database, stop_test_database

# Start database
start_test_database()

# Stop database
stop_test_database()
```

### Database Operations

```python
from tests.test_helpers import get_test_database_connection, reset_database

# Get database connection
with get_test_database_connection() as conn:
    with conn.cursor() as cursor:
        cursor.execute("SELECT 1")

# Reset database
reset_database()
```

### Test Data Creation

```python
from tests.test_helpers import create_test_user, create_test_session

# Create test user
user_data = create_test_user("test_user", 100.0)

# Create test session
session_data = create_test_session(user_data["user_id"])
```

### Test Data Manager

```python
from tests.test_helpers import TestDataManager

# Create manager
manager = TestDataManager()

# Create test data
user = manager.create_user("test_user", 100.0)
session = manager.create_session(user["user_id"])

# Cleanup (automatic in fixtures)
manager.cleanup()
```

## Test Markers

Use pytest markers to categorize and run specific test types:

- **`@pytest.mark.docker`**: Tests requiring Docker Compose
- **`@pytest.mark.database`**: Tests requiring database
- **`@pytest.mark.integration`**: Integration tests
- **`@pytest.mark.unit`**: Unit tests
- **`@pytest.mark.slow`**: Slow-running tests

## Environment Variables

Test environment automatically sets:

- `DATABASE_URL`: Test database connection string
- `ENVIRONMENT`: Set to "testing"
- `LOG_LEVEL`: Set to "DEBUG"
- `GAME_STARTING_CHIPS`: Set to "100.0"

## Database Reset Strategy

### Per Test Class
- Database is reset before each test class
- Maintains database connection across class tests
- Use `@pytest.mark.database` and class-scoped fixtures

### Per Test (When Needed)
- Database is reset before each test function
- Complete isolation between tests
- Use `clean_database` fixture

### Manual Reset
```python
from tests.test_helpers import reset_database

# Reset database manually
reset_database()
```

## Error Handling

The foundation includes comprehensive error handling:

- **DockerComposeError**: Raised when Docker operations fail
- **DatabaseError**: Raised when database operations fail
- **Automatic cleanup**: Fixtures ensure cleanup even on test failures
- **Graceful degradation**: Tests can run without Docker if marked appropriately

## Best Practices

### Writing Tests

1. **Use appropriate fixtures**: Choose the right scope for your needs
2. **Mark tests correctly**: Use markers to categorize tests
3. **Clean up test data**: Use TestDataManager for data creation
4. **Test isolation**: Ensure tests don't interfere with each other
5. **Error handling**: Test both success and failure scenarios

### Test Organization

1. **Group related tests**: Use test classes for related functionality
2. **Clear test names**: Use descriptive test method names
3. **Documentation**: Add docstrings to test methods
4. **Assertions**: Use specific assertions with clear error messages

### Performance

1. **Use appropriate scopes**: Session scope for expensive setup
2. **Minimize database operations**: Batch operations when possible
3. **Mock external dependencies**: Use mocks for unit tests
4. **Parallel testing**: Consider parallel execution for large test suites

## Troubleshooting

### Common Issues

1. **Docker not running**: Ensure Docker is started
2. **Port conflicts**: Check if port 5433 is available
3. **Database connection failures**: Verify Docker Compose is running
4. **Import errors**: Ensure project root is in Python path

### Debug Commands

```bash
# Check Docker status
docker ps

# Check database logs
docker-compose -f docker-compose.test.yml logs postgres-test

# Test database connection manually
psql -h localhost -p 5433 -U test_user -d blackjack_test

# Run tests with maximum verbosity
pytest -vvv --tb=long
```

## Configuration

### Docker Compose

The test database configuration is in `docker-compose.test.yml`:

- **Port**: 5436 (to avoid conflicts with local PostgreSQL)
- **Database**: blackjack_test
- **User**: test_user
- **Password**: test_password
- **Storage**: In-memory (tmpfs) for fast test execution
- **Health check**: Automatic readiness detection

### Pytest Configuration

Pytest configuration is in `pytest.ini`:

- **Test discovery**: Automatically finds test files
- **Markers**: Custom markers for test categorization
- **Output**: Verbose output with colors
- **Warnings**: Filtered warnings for cleaner output

## Future Enhancements

- **Parallel testing**: Support for parallel test execution
- **Test data factories**: More sophisticated test data creation
- **Performance testing**: Built-in performance measurement
- **Coverage reporting**: Integration with coverage tools
- **CI/CD integration**: GitHub Actions or similar 