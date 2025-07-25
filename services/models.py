"""
Database models and schema for the blackjack game.
"""

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

@dataclass
class User:
    """Database model for a user."""
    user_id: str
    username: str
    created_at: datetime
    current_balance: float
    updated_at: datetime

@dataclass
class Session:
    """Database model for a game session."""
    session_id: str
    user_id: str
    created_at: datetime
    status: str = 'active'  # 'active', 'completed', 'abandoned'

@dataclass
class Round:
    """Database model for a single blackjack round."""
    round_id: str
    session_id: str
    bet_amount: float
    player_hand: str  # JSON string of cards
    dealer_hand: str  # JSON string of cards
    player_total: int
    dealer_total: int
    outcome: str  # 'win', 'loss', 'push'
    payout: float
    chips_before: float
    chips_after: float
    created_at: datetime

# SQL Schema definitions
USERS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    privy_wallet_id VARCHAR(255) UNIQUE NOT NULL,
    privy_wallet_address VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    current_balance DECIMAL(15,2) NOT NULL DEFAULT 100.0,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT check_balance_non_negative CHECK (current_balance >= 0)
);
"""

BLACKJACK_SESSIONS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS blackjack_sessions (
    session_id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(user_id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'completed', 'abandoned')),
    CONSTRAINT fk_blackjack_sessions_user FOREIGN KEY (user_id) REFERENCES users(user_id)
);
"""

ROUNDS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS rounds (
    round_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES blackjack_sessions(session_id),
    bet_amount DECIMAL(15,2) NOT NULL,
    player_hand TEXT NOT NULL,
    dealer_hand TEXT NOT NULL,
    player_total INTEGER NOT NULL,
    dealer_total INTEGER NOT NULL,
    outcome TEXT NOT NULL CHECK (outcome IN ('win', 'loss', 'push')),
    payout DECIMAL(15,2) NOT NULL,
    chips_before DECIMAL(15,2) NOT NULL,
    chips_after DECIMAL(15,2) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT fk_rounds_session FOREIGN KEY (session_id) REFERENCES blackjack_sessions(session_id)
);
"""

# PostgreSQL Functions for atomic balance operations
DEBIT_USER_BALANCE_FUNCTION = """
CREATE OR REPLACE FUNCTION debit_user_balance(
    p_user_id UUID,
    p_amount DECIMAL(15,2)
) RETURNS BOOLEAN AS $$
BEGIN
    UPDATE users 
    SET current_balance = current_balance - p_amount,
        updated_at = NOW()
    WHERE user_id = p_user_id 
    AND current_balance >= p_amount;
    
    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;
"""

CREDIT_USER_BALANCE_FUNCTION = """
CREATE OR REPLACE FUNCTION credit_user_balance(
    p_user_id UUID,
    p_amount DECIMAL(15,2)
) RETURNS BOOLEAN AS $$
BEGIN
    UPDATE users 
    SET current_balance = current_balance + p_amount,
        updated_at = NOW()
    WHERE user_id = p_user_id;
    
    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;
"""

# Indexes for performance
INDEXES_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);",
    "CREATE INDEX IF NOT EXISTS idx_blackjack_sessions_user_id ON blackjack_sessions(user_id);",
    "CREATE INDEX IF NOT EXISTS idx_blackjack_sessions_status ON blackjack_sessions(status);",
    "CREATE INDEX IF NOT EXISTS idx_blackjack_sessions_created_at ON blackjack_sessions(created_at);",
    "CREATE INDEX IF NOT EXISTS idx_rounds_session_id ON rounds(session_id);",
    "CREATE INDEX IF NOT EXISTS idx_rounds_created_at ON rounds(created_at);"
] 