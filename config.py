"""
Type-safe configuration management using Pydantic.
Similar to Zod in TypeScript for environment variable validation.
"""

import os
from typing import Optional
from pydantic import BaseModel, Field, validator
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file at module import time
load_dotenv()

class DatabaseConfig(BaseModel):
    """Database configuration with validation."""
    url: str = Field(..., description="PostgreSQL connection URL")
    pool_size: int = Field(default=5, ge=1, le=20, description="Connection pool size")
    timeout: int = Field(default=30, ge=5, le=300, description="Connection timeout in seconds")
    
    @validator('url')
    def validate_database_url(cls, v):
        if not v.startswith(('postgresql://', 'postgres://')):
            raise ValueError('Database URL must start with postgresql:// or postgres://')
        return v

class SessionConfig(BaseModel):
    """Session configuration with validation."""
    namespace: str = Field(default="blackjack-game", description="UUID5 namespace for sessions")
    default_status: str = Field(default="active", description="Default session status")
    
    @validator('default_status')
    def validate_status(cls, v):
        valid_statuses = ['active', 'completed', 'abandoned']
        if v not in valid_statuses:
            raise ValueError(f'Status must be one of: {valid_statuses}')
        return v

class LoggingConfig(BaseModel):
    """Logging configuration with validation."""
    level: str = Field(default="INFO", description="Logging level")
    format: str = Field(default="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    
    @validator('level')
    def validate_log_level(cls, v):
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'Log level must be one of: {valid_levels}')
        return v.upper()

class GameConfig(BaseModel):
    """Game-specific configuration with validation."""
    starting_chips: float = Field(default=100.0, ge=1.0, description="Starting chip balance")
    min_bet: float = Field(default=1.0, ge=0.1, description="Minimum bet amount")
    max_bet: float = Field(default=1000.0, ge=1.0, description="Maximum bet amount")
    shoe_threshold: int = Field(default=50, ge=10, le=100, description="Cards remaining before reshuffle")
    
    @validator('max_bet')
    def validate_max_bet(cls, v, values):
        if 'min_bet' in values and v <= values['min_bet']:
            raise ValueError('max_bet must be greater than min_bet')
        return v

class APIConfig(BaseModel):
    """API configuration for external services."""
    google_genai_use_vertexai: bool = Field(default=False, description="Use Google Vertex AI for Gemini")
    google_api_key: str = Field(default="", description="Google API key for Gemini")
    xai_api_key: str = Field(default="", description="XAI API key")
    
    @validator('google_genai_use_vertexai')
    def validate_google_vertexai(cls, v):
        # Convert string to bool if needed
        if isinstance(v, str):
            return v.lower() in ('true', '1', 'yes', 'on')
        return bool(v)
    
class PrivyConfig(BaseModel):
    """Privy configuration for external services."""
    app_id: str = Field(default="", description="Privy APP ID")
    app_secret: str = Field(default="", description="Privy APP secret")
    base_url: str = Field(default="https://api.client.io/", description="Privy base URL")
    environment: str = Field(default="staging", description="Privy environment")
    registration_contract_address: str = Field(default="0x0000000000000000000000000000000000000000", description="Registration contract address")
    caip_chain_id: str = Field(default="eip155:10143", description="CAIP-2 chain ID")
    
    @validator('app_id')
    def validate_app_id(cls, v):
        if not v:
            raise ValueError("APP ID is required")
        return v
    
    @validator('app_secret')
    def validate_app_secret(cls, v):
        if not v:
            raise ValueError("APP secret is required")
        return v
    
    @validator('base_url')
    def validate_base_url(cls, v):
        if not v.startswith(('https://', 'http://')):
            raise ValueError('Base URL must start with https:// or http://')
        return v
    
    @validator('environment')   
    def validate_environment(cls, v):
        valid_environments = ['staging', 'production']
        if v not in valid_environments:
            raise ValueError(f'Environment must be one of: {valid_environments}')
        return v


class Config(BaseSettings):
    """Main configuration class that loads from environment variables."""
    
    # Database configuration
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    
    # Session configuration
    session: SessionConfig = Field(default_factory=SessionConfig)
    
    # Logging configuration
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    
    # Game configuration
    game: GameConfig = Field(default_factory=GameConfig)
    
    # API configuration
    api: APIConfig = Field(default_factory=APIConfig)

    # Privy configuration
    privy: PrivyConfig = Field(default_factory=PrivyConfig)
    
    # Environment
    environment: str = Field(default="development", description="Environment (development, staging, production)")
    debug: bool = Field(default=False, description="Debug mode")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_nested_delimiter = "__"
        extra = "ignore"  # Allow extra fields to be ignored
        
        # Map environment variables to nested config
        @classmethod
        def customise_sources(cls, init_settings, env_settings, file_secret_settings):
            return (
                init_settings,
                env_settings,
                file_secret_settings,
            )

# Global configuration instance
config: Optional[Config] = None

def load_config() -> Config:
    """
    Load configuration from environment variables.
    
    Returns:
        Config: Validated configuration object
        
    Raises:
        ValueError: If required environment variables are missing or invalid
    """
    global config
    
    # Ensure dotenv is loaded (in case this function is called before module import)
    load_dotenv()
    
    try:
        # Load database URL from environment (try both formats)
        database_url = os.getenv('DATABASE__URL') or os.getenv('DATABASE_URL')
        if not database_url:
            raise ValueError("DATABASE__URL or DATABASE_URL environment variable is required")
        
        # Create database config
        database_config = DatabaseConfig(
            url=database_url,
            pool_size=int(os.getenv('DATABASE__POOL_SIZE', os.getenv('DB_POOL_SIZE', '5'))),
            timeout=int(os.getenv('DATABASE__TIMEOUT', os.getenv('DB_TIMEOUT', '30')))
        )
        
        # Create session config
        session_config = SessionConfig(
            namespace=os.getenv('SESSION__NAMESPACE', os.getenv('SESSION_NAMESPACE', 'blackjack-game')),
            default_status=os.getenv('SESSION__DEFAULT_STATUS', os.getenv('SESSION_DEFAULT_STATUS', 'active'))
        )
        
        # Create logging config
        logging_config = LoggingConfig(
            level=os.getenv('LOGGING__LEVEL', os.getenv('LOG_LEVEL', 'INFO')),
            format=os.getenv('LOGGING__FORMAT', os.getenv('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        )
        
        # Create game config
        game_config = GameConfig(
            starting_chips=float(os.getenv('GAME__STARTING_CHIPS', os.getenv('GAME_STARTING_CHIPS', '100.0'))),
            min_bet=float(os.getenv('GAME__MIN_BET', os.getenv('GAME_MIN_BET', '1.0'))),
            max_bet=float(os.getenv('GAME__MAX_BET', os.getenv('GAME_MAX_BET', '1000.0'))),
            shoe_threshold=int(os.getenv('GAME__SHOE_THRESHOLD', os.getenv('GAME_SHOE_THRESHOLD', '50')))
        )
        
        # Create API config
        api_config = APIConfig(
            google_genai_use_vertexai=os.getenv('API__GOOGLE_GENAI_USE_VERTEXAI', os.getenv('GOOGLE_GENAI_USE_VERTEXAI', 'false')),
            google_api_key=os.getenv('API__GOOGLE_API_KEY', os.getenv('GOOGLE_API_KEY', '')),
            xai_api_key=os.getenv('API__XAI_API_KEY', os.getenv('XAI_API_KEY', ''))
        )

        # Create Privy config
        privy_config = PrivyConfig(
            app_id=os.getenv('PRIVY__API_KEY', os.getenv('PRIVY_APP_ID', '')),
            app_secret=os.getenv('PRIVY__API_SECRET', os.getenv('PRIVY_APP_SECRET', '')),
            base_url=os.getenv('PRIVY__BASE_URL', os.getenv('PRIVY_BASE_URL', 'https://api.client.io/')),
            environment=os.getenv('PRIVY__ENVIRONMENT', os.getenv('PRIVY_ENVIRONMENT', 'staging')),
            registration_contract_address=os.getenv('PRIVY__REGISTRATION_CONTRACT_ADDRESS', os.getenv('PRIVY_REGISTRATION_CONTRACT_ADDRESS', '0x0000000000000000000000000000000000000000')),
            caip_chain_id=os.getenv('PRIVY__CAIP_CHAIN_ID', os.getenv('PRIVY_CAIP_CHAIN_ID', 'eip155:10143'))
        )
        
        # Create main config
        config = Config(
            database=database_config,
            session=session_config,
            logging=logging_config,
            game=game_config,
            api=api_config,
            privy=privy_config,
            environment=os.getenv('ENVIRONMENT', 'development'),
            debug=os.getenv('DEBUG', 'false').lower() == 'true'
        )
        
        return config
        
    except Exception as e:
        raise ValueError(f"Configuration loading failed: {e}")

def get_config() -> Config:
    """
    Get the global configuration instance.
    Loads configuration if not already loaded.
    
    Returns:
        Config: Configuration object
    """
    global config
    
    # Ensure dotenv is loaded
    load_dotenv()
    
    if config is None:
        config = load_config()
    return config

def reload_config() -> Config:
    """
    Reload configuration from environment variables.
    Useful for testing or when environment changes.
    
    Returns:
        Config: Updated configuration object
    """
    global config
    
    # Ensure dotenv is loaded
    load_dotenv()
    
    config = load_config()
    return config 