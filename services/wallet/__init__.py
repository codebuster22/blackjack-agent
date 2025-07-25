"""
Wallet Service Module

This module provides a simplified wallet management system for Privy-based wallets
and private key wallets, using wallet_id only for identification.

Simplified Architecture:
- Wallet service only manages wallets by wallet_id
- User-to-wallet mapping should be handled by external services
- Single-index caching for reliability and simplicity

Main Components:
- WalletService: Main orchestrator for wallet operations (wallet_id only)
- UserWalletWrapper: Privy-based user wallet with transaction capabilities
- DealerPrivateKeyWallet: Private key-based dealer wallet
- WalletFactory: Factory for creating Privy wallets (no user context)
- UserWalletAggregator: Single-index cache by wallet_id with cache-miss recovery
- transaction_utils: Utilities for building blockchain transactions

Key Features:
- Simplified wallet creation (no user parameters)
- Single-index caching by wallet_id only
- Reliable cache-miss recovery (fetches from Privy if not cached)
- Blockchain transaction sending for wallet registration
- Clean separation of concerns (wallets vs user management)

Usage:
    from services.wallet import WalletService
    
    # Initialize service
    service = WalletService(app_id, app_secret, base_url)
    await service.initialize()
    
    # Create new wallet
    wallet = await service.create_wallet()
    wallet_id = wallet.get_wallet_id()
    
    # Get existing wallet (checks cache, fetches from Privy if needed)
    wallet = await service.get_wallet(wallet_id)
    
    # Register wallet onchain
    tx_hash = await service.register_existing_wallet_onchain(wallet_id)

External Integration:
    # User-to-wallet mapping should be handled externally:
    # 1. UserService manages user_id -> wallet_id mappings
    # 2. WalletService manages wallet_id -> wallet operations
    # 3. Clean separation of responsibilities
"""

# Main service class
from .WalletService import WalletService, WalletServiceError, ServiceNotInitializedError, NetworkError, ContractError

# Wallet wrapper classes
from .UserWalletWrapper import UserWalletWrapper, TransactionBuildError, PrivyTransactionError
from .WalletWrapperBase import WalletWrapperBase
from .DealerPrivateKeyWallet import DealerPrivateKeyWallet, DealerWalletError

# Factory and aggregator
from .WalletFactory import WalletFactory, WalletCreationError
from .UserWalletAggregator import UserWalletAggregator, CacheError

# Utilities
from .transaction_utils import (
    build_register_user_transaction_object,
    validate_ethereum_address,
    validate_transaction_object,
    AddressValidationError,
    EncodingError
)

# Version info
__version__ = "2.0.0"  # Major version bump for simplified API

# Public API - what gets imported with "from services.wallet import *"
__all__ = [
    # Main service
    "WalletService",
    "WalletServiceError",
    "ServiceNotInitializedError", 
    "NetworkError",
    "ContractError",
    
    # Wallet components
    "UserWalletWrapper",
    "WalletWrapperBase", 
    "DealerPrivateKeyWallet",
    "WalletFactory",
    "UserWalletAggregator",
    
    # Errors
    "TransactionBuildError",
    "PrivyTransactionError",
    "DealerWalletError",
    "WalletCreationError",
    "CacheError",
    "AddressValidationError",
    "EncodingError",
    
    # Utilities
    "build_register_user_transaction_object",
    "validate_ethereum_address", 
    "validate_transaction_object",
] 