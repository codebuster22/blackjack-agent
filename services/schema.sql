-- Blackjack Game Database Schema
-- This file contains the complete database schema for the blackjack game

-- Migration: Rename sessions table to blackjack_sessions to avoid conflicts with ADK
-- Run this if you have an existing database with a 'sessions' table

-- Step 1: Rename existing sessions table (if it exists)
-- Uncomment the following line if you have an existing sessions table:
-- ALTER TABLE sessions RENAME TO blackjack_sessions;

-- Step 2: Drop and recreate if you want a clean slate
-- Uncomment the following lines if you want to start fresh:
-- DROP TABLE IF EXISTS rounds CASCADE;
-- DROP TABLE IF EXISTS blackjack_sessions CASCADE;
-- DROP TABLE IF EXISTS users CASCADE;

-- Users table
CREATE TABLE IF NOT EXISTS users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    current_balance DECIMAL(15,2) NOT NULL DEFAULT 100.0,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT check_balance_non_negative CHECK (current_balance >= 0)
);

-- Blackjack sessions table (renamed from sessions to avoid ADK conflicts)
CREATE TABLE IF NOT EXISTS blackjack_sessions (
    session_id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(user_id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'completed', 'abandoned')),
    CONSTRAINT fk_blackjack_sessions_user FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Rounds table
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

-- PostgreSQL Functions for atomic balance operations
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

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_blackjack_sessions_user_id ON blackjack_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_blackjack_sessions_status ON blackjack_sessions(status);
CREATE INDEX IF NOT EXISTS idx_blackjack_sessions_created_at ON blackjack_sessions(created_at);
CREATE INDEX IF NOT EXISTS idx_rounds_session_id ON rounds(session_id);
CREATE INDEX IF NOT EXISTS idx_rounds_created_at ON rounds(created_at);
