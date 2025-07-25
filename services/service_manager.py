"""
Service manager for handling database and user manager initialization.
This provides a centralized way to access services throughout the application.
"""

from typing import Optional
from .db import DatabaseService
from .user_manager import UserManager
from config import get_config

class ServiceManager:
    """Manages database and user manager services."""
    
    _instance: Optional['ServiceManager'] = None
    _db_service: Optional[DatabaseService] = None
    _user_manager: Optional[UserManager] = None
    _initialized: bool = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._initialized = False
    
    async def initialize(self, database_url: Optional[str] = None):
        """Initialize the services."""
        if not self._initialized or database_url is not None:
            config = get_config()
            self._db_service = DatabaseService()
            await self._db_service.init_database(database_url=database_url or config.database.url)
            self._user_manager = UserManager(self._db_service)
            self._initialized = True
    
    @property
    def db_service(self) -> DatabaseService:
        """Get the database service."""
        if not self._initialized:
            raise RuntimeError("ServiceManager not initialized. Call initialize() first.")
        return self._db_service
    
    @property
    def user_manager(self) -> UserManager:
        """Get the user manager."""
        if not self._initialized:
            raise RuntimeError("ServiceManager not initialized. Call initialize() first.")
        return self._user_manager
    
    async def reset_for_tests(self, database_url: str):
        """Reset the service manager for testing with a specific database URL."""
        self._db_service = None
        self._user_manager = None
        self._initialized = False
        await self.initialize(database_url=database_url)

# Global service manager instance
service_manager = ServiceManager() 