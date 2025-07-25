"""
@class UserWalletAggregator:

Functionalities:
    - __init__(client: PrivyClient):
        - set the class variables

    - cache_user_wallet(db_user_id: str, twitter_user_name: str, user_wallet: privy.Wallet) -> UserWalletWrapper:
        - cache the user wallet in-memory as UserWalletWrapper instance
        - return the UserWalletWrapper instance
        
        Error Handling Strategy:
            - CacheError: if wallet caching fails due to memory constraints
            - ValidationError: if cache_user_wallet receives invalid parameters
            
        Cache Validation:
            - Ensure db_user_id and twitter_user_name are not empty
            - Validate privy.Wallet instance before wrapping
            - Handle cache eviction if memory limits exceeded

    - get_user_wallet(**kwargs) -> UserWalletWrapper:
        - where **kwargs can be: db_user_id, twitter_user_name or wallet_id
        - get the user wallet from the in-memory cache
        - return the UserWalletWrapper instance
        
        Error Handling Strategy:
            - KeyError: if wallet lookup fails for given kwargs
            - ValidationError: if kwargs are invalid or missing required parameters
            
        Lookup Validation:
            - Validate at least one valid identifier is provided in kwargs
            - Return specific error if wallet not found in cache
            - Handle multiple matching wallets scenario
"""
from .UserWalletWrapper import UserWalletWrapper
from privy import AsyncPrivyAPI
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class CacheError(Exception):
    """Raised when wallet caching fails due to memory constraints."""
    pass

class ValidationError(Exception):
    """Raised when validation fails."""
    pass

class UserWalletAggregator:
    """
    Aggregator class for caching and managing user wallets in memory by wallet_id only.
    
    Simplified design: Only caches by wallet_id, no user identity management.
    User-to-wallet mapping should be handled by external services.
    
    Functionalities:
        - __init__(client: AsyncPrivyAPI):
            - set the class variables

        - cache_wallet(wallet_id: str, user_wallet: privy.Wallet) -> UserWalletWrapper:
            - cache the user wallet in-memory as UserWalletWrapper instance by wallet_id
            - return the UserWalletWrapper instance
            
            Error Handling Strategy:
                - CacheError: if wallet caching fails due to memory constraints
                - ValidationError: if cache_wallet receives invalid parameters
                
            Cache Validation:
                - Ensure wallet_id is not empty
                - Validate privy.Wallet instance before wrapping
                - Handle cache eviction if memory limits exceeded

        - get_wallet(wallet_id: str) -> UserWalletWrapper:
            - get the user wallet from the in-memory cache by wallet_id
            - return the UserWalletWrapper instance
            
            Error Handling Strategy:
                - KeyError: if wallet lookup fails for given wallet_id
                - ValidationError: if wallet_id is invalid
                
            Lookup Validation:
                - Validate wallet_id is provided and non-empty
                - Return specific error if wallet not found in cache
    """
    
    def __init__(self, client: AsyncPrivyAPI):
        """
        Initialize UserWalletAggregator with Privy client.
        
        Args:
            client: AsyncPrivyAPI client instance
            
        Raises:
            ValueError: if client is None
        """
        if client is None:
            raise ValueError("Privy client cannot be None")
            
        self.client = client
        
        # Simplified: Single cache index by wallet_id only
        self._cache_by_wallet_id: Dict[str, UserWalletWrapper] = {}
        
        # Statistics for monitoring cache performance
        self._cache_size = 0
        self._max_cache_size = 1000  # Configurable limit
        
        logger.info("Initialized UserWalletAggregator with empty single-index cache")
    
    def cache_wallet(self, user_wallet) -> UserWalletWrapper:
        """
        Cache the user wallet in-memory as UserWalletWrapper instance by wallet_id.
        
        Args:
            user_wallet: privy.Wallet instance to cache
            
        Returns:
            UserWalletWrapper: The wrapped and cached wallet instance
            
        Raises:
            ValidationError: if parameters are invalid
            CacheError: if caching fails due to memory constraints
        """
        
        # Validate privy.Wallet instance before wrapping
        if not user_wallet:
            raise ValidationError("user_wallet cannot be None")
            
        if not hasattr(user_wallet, 'id') or not hasattr(user_wallet, 'address'):
            raise ValidationError("Invalid wallet instance - missing required attributes (id, address)")
        
        try:
            # Handle cache eviction if memory limits exceeded
            if self._cache_size >= self._max_cache_size:
                self._evict_oldest_entries()
            
            # Create UserWalletWrapper instance
            wallet_wrapper = UserWalletWrapper(user_wallet, self.client)
            wallet_id = wallet_wrapper.get_wallet_id()
            
            # Cache by wallet_id only
            self._cache_by_wallet_id[wallet_id] = wallet_wrapper
            self._cache_size += 1
            
            logger.info(f"Successfully cached wallet: wallet_id={wallet_id}, cache_size={self._cache_size}")
            
            return wallet_wrapper
            
        except Exception as e:
            if isinstance(e, ValidationError):
                raise
            else:
                logger.error(f"Cache operation failed: {e}")
                raise CacheError(f"Failed to cache wallet: {str(e)}") from e
    
    def get_wallet(self, wallet_id: str) -> UserWalletWrapper:
        """
        Get the user wallet from the in-memory cache by wallet_id.
        
        Args:
            wallet_id: The wallet ID to lookup
            
        Returns:
            UserWalletWrapper: The cached wallet wrapper instance
            
        Raises:
            ValidationError: if wallet_id is invalid
            KeyError: if wallet not found in cache
        """
        # Lookup Validation: Validate wallet_id is provided and non-empty
        if not wallet_id or not isinstance(wallet_id, str) or wallet_id.strip() == "":
            raise ValidationError("wallet_id must be a non-empty string")
        
        try:
            wallet_wrapper = self._cache_by_wallet_id.get(wallet_id)
            
            # Return specific error if wallet not found in cache
            if wallet_wrapper is None:
                logger.warning(f"Wallet not found in cache for wallet_id={wallet_id}")
                raise KeyError(f"Wallet not found in cache for wallet_id={wallet_id}")
            
            logger.info(f"Successfully retrieved wallet from cache using wallet_id={wallet_id}")
            return wallet_wrapper
            
        except (ValidationError, KeyError):
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            logger.error(f"Unexpected error during wallet lookup: {e}")
            raise KeyError(f"Failed to lookup wallet: {str(e)}") from e
    
    def has_wallet(self, wallet_id: str) -> bool:
        """
        Check if wallet exists in cache.
        
        Args:
            wallet_id: The wallet ID to check
            
        Returns:
            bool: True if wallet is cached, False otherwise
        """
        if not wallet_id or not isinstance(wallet_id, str):
            return False
        return wallet_id in self._cache_by_wallet_id
    
    def remove_wallet(self, wallet_id: str) -> bool:
        """
        Remove wallet from cache.
        
        Args:
            wallet_id: The wallet ID to remove
            
        Returns:
            bool: True if wallet was removed, False if not found
        """
        if wallet_id in self._cache_by_wallet_id:
            del self._cache_by_wallet_id[wallet_id]
            self._cache_size -= 1
            logger.info(f"Removed wallet from cache: {wallet_id}")
            return True
        return False
    
    def _evict_oldest_entries(self, evict_count: int = 100):
        """
        Evict oldest entries from cache to free up memory.
        
        Args:
            evict_count: Number of entries to evict
        """
        logger.warning(f"Cache size limit reached ({self._max_cache_size}), evicting {evict_count} entries")
        
        # Simple eviction strategy: remove first N entries
        # In production, you might want LRU or more sophisticated eviction
        
        evicted = 0
        keys_to_remove = list(self._cache_by_wallet_id.keys())[:evict_count]
        
        for wallet_id in keys_to_remove:
            self._cache_by_wallet_id.pop(wallet_id, None)
            evicted += 1
        
        self._cache_size -= evicted
        logger.info(f"Evicted {evicted} entries, new cache size: {self._cache_size}")
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics for monitoring."""
        return {
            "cache_size": self._cache_size,
            "max_cache_size": self._max_cache_size,
            "wallet_id_entries": len(self._cache_by_wallet_id)
        }
    
    def clear_cache(self):
        """Clear all cached wallets."""
        self._cache_by_wallet_id.clear()
        self._cache_size = 0
        logger.info("Cleared all cached wallets")
    
    def __str__(self) -> str:
        """String representation of the aggregator."""
        return f"UserWalletAggregator(cache_size={self._cache_size}, max_size={self._max_cache_size})"