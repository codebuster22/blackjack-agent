# Environment Variables Reference

This document lists all environment variables required for the blackjack agent application.

## Database Configuration

| Variable | Type | Default | Description | Required |
|----------|------|---------|-------------|----------|
| `DATABASE_URL` | string | - | PostgreSQL connection URL | ✅ Yes |
| `DB_POOL_SIZE` | integer | 5 | Connection pool size (1-20) | No |
| `DB_TIMEOUT` | integer | 30 | Connection timeout in seconds (5-300) | No |

## Session Configuration

| Variable | Type | Default | Description | Required |
|----------|------|---------|-------------|----------|
| `SESSION_NAMESPACE` | string | "blackjack-game" | UUID5 namespace for sessions | No |
| `SESSION_DEFAULT_STATUS` | string | "active" | Default session status | No |

## Logging Configuration

| Variable | Type | Default | Description | Required |
|----------|------|---------|-------------|----------|
| `LOG_LEVEL` | string | "INFO" | Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL) | No |
| `LOG_FORMAT` | string | "%(asctime)s - %(name)s - %(levelname)s - %(message)s" | Log message format | No |

## Game Configuration

| Variable | Type | Default | Description | Required |
|----------|------|---------|-------------|----------|
| `GAME_STARTING_CHIPS` | float | 100.0 | Starting chip balance | No |
| `GAME_MIN_BET` | float | 1.0 | Minimum bet amount | No |
| `GAME_MAX_BET` | float | 1000.0 | Maximum bet amount | No |
| `GAME_SHOE_THRESHOLD` | integer | 50 | Cards remaining before reshuffle (10-100) | No |

## API Configuration

| Variable | Type | Default | Description | Required |
|----------|------|---------|-------------|----------|
| `GOOGLE_GENAI_USE_VERTEXAI` | boolean | false | Use Google Vertex AI for Gemini | No |
| `GOOGLE_API_KEY` | string | "" | Google API key for Gemini | No |
| `XAI_API_KEY` | string | "" | XAI API key | No |

## Environment

| Variable | Type | Default | Description | Required |
|----------|------|---------|-------------|----------|
| `ENVIRONMENT` | string | "development" | Environment (development, staging, production) | No |
| `DEBUG` | boolean | false | Debug mode | No |

## Example .env File

```bash
# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/blackjack_db
DB_POOL_SIZE=5
DB_TIMEOUT=30

# Session Configuration
SESSION_NAMESPACE=blackjack-game
SESSION_DEFAULT_STATUS=active

# Logging Configuration
LOG_LEVEL=INFO
LOG_FORMAT=%(asctime)s - %(name)s - %(levelname)s - %(message)s

# Game Configuration
GAME_STARTING_CHIPS=100.0
GAME_MIN_BET=1.0
GAME_MAX_BET=1000.0
GAME_SHOE_THRESHOLD=50

# API Configuration
GOOGLE_GENAI_USE_VERTEXAI=false
GOOGLE_API_KEY=your_google_api_key_here
XAI_API_KEY=your_xai_api_key_here

# Environment
ENVIRONMENT=development
DEBUG=false
```

## Test Environment Variables

For testing, the following additional variables are set automatically:

- `DATABASE_URL` is set to the test database URL
- `ENVIRONMENT` is set to "testing"
- `LOG_LEVEL` is set to "DEBUG"
- API keys are set to test values

## Validation Rules

- `DATABASE_URL` must start with `postgresql://` or `postgres://`
- `SESSION_DEFAULT_STATUS` must be one of: `active`, `completed`, `abandoned`
- `LOG_LEVEL` must be one of: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`
- `GAME_MAX_BET` must be greater than `GAME_MIN_BET`
- `GOOGLE_GENAI_USE_VERTEXAI` accepts boolean values: `true`, `false`, `1`, `0`, `yes`, `no`, `on`, `off` 