"""
Unit tests for configuration system.
"""
import pytest
import os
from config import load_config, get_config, reload_config


@pytest.mark.unit
class TestConfig:
    """Test configuration loading and validation."""
    
    def test_config_loading(self):
        """Test configuration loading with environment variables."""
        from tests.test_helpers import setup_test_environment, cleanup_test_environment
        
        setup_test_environment()
        
        try:
            # Set test environment variables
            os.environ['DATABASE__URL'] = 'postgresql://test:pass@localhost/testdb'
            os.environ['DATABASE__POOL_SIZE'] = '10'
            os.environ['GAME__STARTING_CHIPS'] = '200.0'
            os.environ['LOGGING__LEVEL'] = 'DEBUG'
            
            # Load configuration
            config = load_config()
            
            # Test database config
            assert config.database.url == 'postgresql://test:pass@localhost/testdb'
            assert config.database.pool_size == 10
            assert config.database.timeout == 30  # default value
            
            # Test game config
            assert config.game.starting_chips == 200.0
            assert config.game.min_bet == 5.0  # test environment default
            assert config.game.max_bet == 1000.0  # default value
            
            # Test logging config
            assert config.logging.level == 'DEBUG'
            
            # Test session config
            assert config.session.namespace == 'blackjack-game'  # default value
            
        finally:
            cleanup_test_environment()
    
    def test_config_validation(self):
        """Test configuration validation."""
        from tests.test_helpers import setup_test_environment, cleanup_test_environment
        
        setup_test_environment()
        
        try:
            # Test invalid database URL
            os.environ['DATABASE__URL'] = 'invalid://url'
            with pytest.raises(ValueError, match="Database URL must start with postgresql://"):
                load_config()
            
            # Test invalid log level
            os.environ['DATABASE__URL'] = 'postgresql://test:pass@localhost/testdb'
            os.environ['LOGGING__LEVEL'] = 'INVALID'
            with pytest.raises(ValueError, match="Log level must be one of"):
                load_config()
            
            # Test invalid game config
            os.environ['LOGGING__LEVEL'] = 'INFO'
            os.environ['GAME__MIN_BET'] = '100.0'
            os.environ['GAME__MAX_BET'] = '50.0'  # Less than min_bet
            with pytest.raises(ValueError, match="max_bet must be greater than min_bet"):
                load_config()
                
        finally:
            cleanup_test_environment()
    
    def test_config_defaults(self):
        """Test configuration defaults."""
        from tests.test_helpers import setup_test_environment, cleanup_test_environment
        
        setup_test_environment()
        
        try:
            # Clear environment variables
            env_vars_to_clear = [
                'DATABASE__POOL_SIZE', 'DATABASE__TIMEOUT', 'SESSION__NAMESPACE', 'SESSION__DEFAULT_STATUS',
                'LOGGING__LEVEL', 'LOGGING__FORMAT', 'GAME__STARTING_CHIPS', 'GAME__MIN_BET',
                'GAME__MAX_BET', 'GAME__SHOE_THRESHOLD', 'ENVIRONMENT', 'DEBUG',
                'GAME__STARTING_CHIPS', 'GAME__MIN_BET', 'GAME__MAX_BET', 'GAME__SHOE_THRESHOLD'
            ]
            
            for var in env_vars_to_clear:
                if var in os.environ:
                    del os.environ[var]
            
            # Set only required variable
            os.environ['DATABASE__URL'] = 'postgresql://test:pass@localhost/testdb'
            
            # Load configuration
            config = load_config()
            
            # Test defaults (some may be overridden by test environment)
            assert config.database.pool_size == 5
            assert config.database.timeout == 30
            assert config.session.namespace == 'blackjack-game'
            assert config.session.default_status == 'active'
            assert config.logging.level == 'INFO'
            assert config.game.starting_chips == 1000.0  # Overridden by test environment
            assert config.game.min_bet == 5.0  # Overridden by test environment
            assert config.game.max_bet == 1000.0
            assert config.game.shoe_threshold == 50
            assert config.environment == 'development'
            assert config.debug == False
            
        finally:
            cleanup_test_environment()
    
    def test_config_singleton(self):
        """Test that config is a singleton."""
        from tests.test_helpers import setup_test_environment, cleanup_test_environment
        
        setup_test_environment()
        
        try:
            # Load config twice
            config1 = get_config()
            config2 = get_config()
            
            # Should be the same instance
            assert config1 is config2
            
            # Reload should create new instance
            config3 = reload_config()
            assert config3 is not config1
            
        finally:
            cleanup_test_environment()
    
    def test_config_serialization(self):
        """Test configuration serialization."""
        from tests.test_helpers import setup_test_environment, cleanup_test_environment
        
        setup_test_environment()
        
        try:
            config = get_config()
            
            # Test dict conversion
            config_dict = config.model_dump()
            assert 'database' in config_dict
            assert 'session' in config_dict
            assert 'logging' in config_dict
            assert 'game' in config_dict
            
            # Test JSON serialization
            config_json = config.model_dump_json()
            assert '"database"' in config_json
            assert '"session"' in config_json
            
        finally:
            cleanup_test_environment() 