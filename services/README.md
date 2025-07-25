# Database Service

This directory contains the database service for persistent storage of blackjack game data.

## Architecture

### Files

- `models.py` - Database models and schema definitions
- `user_manager.py` - User and session management with UUID5
- `db.py` - Main database service with PostgreSQL operations
- `card_utils.py` - Card conversion utilities for database storage
- `__init__.py` - Package exports

### Database Schema

#### Sessions Table
```sql
CREATE TABLE sessions (
    session_id UUID PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'completed', 'abandoned'))
);
```

#### Rounds Table
```sql
CREATE TABLE rounds (
    round_id UUID PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES sessions(session_id),
    round_number INTEGER NOT NULL,
    bet_amount DECIMAL(10,2) NOT NULL,
    player_hand TEXT NOT NULL,
    dealer_hand TEXT NOT NULL,
    player_total INTEGER NOT NULL,
    dealer_total INTEGER NOT NULL,
    outcome TEXT NOT NULL CHECK (outcome IN ('win', 'loss', 'push')),
    payout DECIMAL(10,2) NOT NULL,
    chips_before DECIMAL(10,2) NOT NULL,
    chips_after DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(session_id, round_number)
);
```

## Usage

### 1. Initialize Database
```python
from services.db import db_service

# Initialize with PostgreSQL connection string
success = db_service.init_database("postgresql://user:pass@localhost/dbname")
```

### 2. User and Session Management
```python
from services import user_manager

# Create user if not exists (requires wallet_service)
user_id = user_manager.create_user_if_not_exists(username, wallet_service)

# Create a new session
session_id = user_manager.create_session(user_id)

# Complete session
user_manager.complete_session(session_id)

# Abandon session
user_manager.abandon_session(session_id)
```

### 3. Card Conversion
```python
from services.card_utils import card_to_string, string_to_card
from dealer_agent.tools.dealer import Card, Suit, Rank

# Convert Card to string
card = Card(suit=Suit.hearts, rank=Rank.ace)
card_str = card_to_string(card)  # Returns "AH"

# Convert string back to Card
card_back = string_to_card("AH")
```

### 4. Database Operations
```python
# Create user and session
user_id = user_manager.create_user_if_not_exists(username, wallet_service)
session_id = user_manager.create_session(user_id)

# Save round data
round_data = {
    'round_id': str(uuid.uuid4()),
    'session_id': session_id,
    'bet_amount': 25.0,
    'player_hand': '["AS", "KH"]',
    'dealer_hand': '["10H", "5D"]',
    'player_total': 21,
    'dealer_total': 15,
    'outcome': 'win',
    'payout': 50.0,
    'chips_before': 100.0,
    'chips_after': 125.0
}
db_service.save_round(round_data)

# Get session rounds
rounds = db_service.get_session_rounds(session_id)

# Get user sessions
sessions = db_service.get_user_sessions(user_id)

# Get session statistics
stats = db_service.get_session_stats(session_id)
```

## Testing

Run the test script to verify functionality:

```bash
# Option 1: Set environment variables directly
export DATABASE_URL="postgresql://user:pass@localhost/dbname"
python test_db_service.py

# Option 2: Use .env file (recommended)
cp env.example .env
# Edit .env with your database URL
python test_db_service.py
```

## Configuration

The system uses a type-safe configuration system with dotenv support:

```bash
# Create .env file from template
cp env.example .env

# Edit .env with your settings
DATABASE_URL=postgresql://user:pass@localhost/dbname
DB_POOL_SIZE=5
GAME_STARTING_CHIPS=100.0
LOG_LEVEL=INFO
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | **Required** | PostgreSQL connection string |
| `DB_POOL_SIZE` | 5 | Connection pool size (1-20) |
| `DB_TIMEOUT` | 30 | Connection timeout in seconds |
| `SESSION_NAMESPACE` | blackjack-game | UUID5 namespace for sessions |
| `LOG_LEVEL` | INFO | Logging level |
| `GAME_STARTING_CHIPS` | 100.0 | Starting chip balance |
| `GAME_MIN_BET` | 1.0 | Minimum bet amount |
| `GAME_MAX_BET` | 1000.0 | Maximum bet amount |
| `ENVIRONMENT` | development | Environment (dev/staging/prod) |
| `DEBUG` | false | Debug mode |

## Future Enhancements

### Shoe Tracking
- `shoe_states` table for deterministic verification
- Seed-based shoe generation
- Round-to-shoe mapping

### Analytics
- Aggregated statistics views
- Performance metrics
- Player behavior analysis

## Error Handling

The database service implements graceful error handling:
- Database failures don't crash the application
- Errors are logged for debugging
- Fallback to in-memory state if needed
- Connection pooling for performance

## Dependencies

- `psycopg2-binary` - PostgreSQL adapter
- Standard library modules: `json`, `uuid`, `datetime`, `logging` 