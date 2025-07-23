"""
Unit tests for dotenv integration with configuration system.
"""
import pytest
import os
import tempfile
from config import load_config, get_config


@pytest.mark.unit
class TestDotenvConfig:
    """Test dotenv integration with configuration system."""
    
    def test_dotenv_loading(self):
        """Test that dotenv loads environment variables from .env file."""
        
        # Create a temporary .env file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("""
DATABASE_URL=postgresql://dotenv:test@localhost/dotenv_db
DB_POOL_SIZE=15
GAME_STARTING_CHIPS=500.0
LOG_LEVEL=WARNING
SESSION_NAMESPACE=test-blackjack
ENVIRONMENT=testing
DEBUG=true
            """.strip())
            env_file = f.name
        
        try:
            # Temporarily change to the directory with the .env file
            original_cwd = os.getcwd()
            env_dir = os.path.dirname(env_file)
            os.chdir(env_dir)
            
            # Clear any existing environment variables
            env_vars_to_clear = [
                'DATABASE_URL', 'DB_POOL_SIZE', 'GAME_STARTING_CHIPS', 'LOG_LEVEL',
                'SESSION_NAMESPACE', 'ENVIRONMENT', 'DEBUG'
            ]
            
            for var in env_vars_to_clear:
                if var in os.environ:
                    del os.environ[var]
            
            # Manually load dotenv from the temporary file
            from dotenv import load_dotenv
            load_dotenv(env_file)
            
            # Load configuration
            config = load_config()
            
            # Verify values from .env file
            assert config.database.url == 'postgresql://dotenv:test@localhost/dotenv_db'
            assert config.database.pool_size == 15
            assert config.game.starting_chips == 500.0
            assert config.logging.level == 'WARNING'
            assert config.session.namespace == 'test-blackjack'
            assert config.environment == 'testing'
            assert config.debug == True
            
            # Change back to original directory
            os.chdir(original_cwd)
            
        finally:
            # Clean up temporary file
            os.unlink(env_file)
    
    def test_environment_override(self):
        """Test that environment variables override .env file values."""
        # Set environment variable that should override .env
        os.environ['DATABASE_URL'] = 'postgresql://override:test@localhost/override_db'
        os.environ['GAME_STARTING_CHIPS'] = '1000.0'
        
        try:
            # Load configuration
            config = load_config()
            
            # Verify environment variables take precedence
            assert config.database.url == 'postgresql://override:test@localhost/override_db'
            assert config.game.starting_chips == 1000.0
            
        finally:
            # Clean up
            if 'DATABASE_URL' in os.environ:
                del os.environ['DATABASE_URL']
            if 'GAME_STARTING_CHIPS' in os.environ:
                del os.environ['GAME_STARTING_CHIPS']
    
    def test_dotenv_automatic_loading(self):
        """Test that dotenv loads automatically when importing config."""
        # Clear environment variables
        if 'DATABASE_URL' in os.environ:
            del os.environ['DATABASE_URL']
        
        # Set a test environment variable
        os.environ['DATABASE_URL'] = 'postgresql://auto:test@localhost/auto_db'
        
        try:
            # Reset the global config to force reload
            from config import reload_config
            
            # Reload config (should automatically load dotenv)
            config = reload_config()
            
            # Verify it loaded correctly
            assert config.database.url == 'postgresql://auto:test@localhost/auto_db'
            
        finally:
            # Clean up
            if 'DATABASE_URL' in os.environ:
                del os.environ['DATABASE_URL'] 