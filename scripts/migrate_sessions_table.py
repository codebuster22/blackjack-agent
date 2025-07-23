#!/usr/bin/env python3
"""
Migration script to rename the sessions table to blackjack_sessions.
This script handles the database schema change to avoid conflicts with Google ADK.
"""

import psycopg2
import logging
from config import get_config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_sessions_table():
    """
    Migrate the sessions table to blackjack_sessions.
    """
    config = get_config()
    
    try:
        # Connect to database
        conn = psycopg2.connect(config.database.url)
        cursor = conn.cursor()
        
        # Check if sessions table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'sessions'
            );
        """)
        
        sessions_exists = cursor.fetchone()[0]
        
        if sessions_exists:
            logger.info("Found existing 'sessions' table. Renaming to 'blackjack_sessions'...")
            
            # Check if blackjack_sessions already exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'blackjack_sessions'
                );
            """)
            
            blackjack_sessions_exists = cursor.fetchone()[0]
            
            if blackjack_sessions_exists:
                logger.warning("'blackjack_sessions' table already exists. Dropping it first...")
                cursor.execute("DROP TABLE blackjack_sessions CASCADE;")
            
            # Rename sessions to blackjack_sessions
            cursor.execute("ALTER TABLE sessions RENAME TO blackjack_sessions;")
            
            # Update foreign key constraints in rounds table
            cursor.execute("""
                ALTER TABLE rounds 
                DROP CONSTRAINT IF EXISTS fk_rounds_session;
            """)
            
            cursor.execute("""
                ALTER TABLE rounds 
                ADD CONSTRAINT fk_rounds_session 
                FOREIGN KEY (session_id) REFERENCES blackjack_sessions(session_id);
            """)
            
            # Update indexes
            cursor.execute("DROP INDEX IF EXISTS idx_sessions_user_id;")
            cursor.execute("DROP INDEX IF EXISTS idx_sessions_status;")
            cursor.execute("DROP INDEX IF EXISTS idx_sessions_created_at;")
            
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_blackjack_sessions_user_id ON blackjack_sessions(user_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_blackjack_sessions_status ON blackjack_sessions(status);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_blackjack_sessions_created_at ON blackjack_sessions(created_at);")
            
            conn.commit()
            logger.info("Successfully migrated 'sessions' table to 'blackjack_sessions'")
            
        else:
            logger.info("No existing 'sessions' table found. Creating new 'blackjack_sessions' table...")
            
            # Create the new table structure
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS blackjack_sessions (
                    session_id UUID PRIMARY KEY,
                    user_id UUID NOT NULL REFERENCES users(user_id),
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'completed', 'abandoned')),
                    CONSTRAINT fk_blackjack_sessions_user FOREIGN KEY (user_id) REFERENCES users(user_id)
                );
            """)
            
            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_blackjack_sessions_user_id ON blackjack_sessions(user_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_blackjack_sessions_status ON blackjack_sessions(status);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_blackjack_sessions_created_at ON blackjack_sessions(created_at);")
            
            conn.commit()
            logger.info("Successfully created 'blackjack_sessions' table")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise

if __name__ == "__main__":
    migrate_sessions_table() 