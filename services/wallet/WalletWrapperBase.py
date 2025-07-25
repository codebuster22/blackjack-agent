from privy import AsyncPrivyAPI
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class WalletWrapperBase:
    """
    Base class for wallet wrappers that provides common interface for Privy-based wallets.
    
    Functionalities:
        - __init__(wallet: privy.Wallet, client: AsyncPrivyAPI):
            - set the class variables
            - this.wallet and this.client are necessary class variables

        - async get_wallet_id() -> str:
            - return the wallet id

        - async get_wallet_address() -> str:
            - return the wallet address

        - async get_wallet_instance() -> privy.Wallet:
            - return the wallet instance
    """
    
    def __init__(self, wallet, client: AsyncPrivyAPI):
        """
        Initialize wallet wrapper with Privy wallet instance and client.
        
        Args:
            wallet: privy.Wallet instance
            client: AsyncPrivyAPI client instance
            
        Raises:
            ValueError: if wallet or client is None
        """
        if wallet is None:
            raise ValueError("Wallet instance cannot be None")
        if client is None:
            raise ValueError("Privy client cannot be None")
            
        self.wallet = wallet
        self.client = client
        logger.info(f"Initialized wallet wrapper for wallet ID: {wallet.id}")
    
    def get_wallet_id(self) -> str:
        """
        Get the wallet ID.
        
        Returns:
            str: The wallet ID
            
        Raises:
            AttributeError: if wallet instance is invalid
        """
        try:
            return self.wallet.id
        except AttributeError as e:
            logger.error(f"Failed to get wallet ID: {e}")
            raise AttributeError("Invalid wallet instance - missing ID attribute") from e
    
    def get_wallet_address(self) -> str:
        """
        Get the wallet address.
        
        Returns:
            str: The wallet address
            
        Raises:
            AttributeError: if wallet instance is invalid
        """
        try:
            return self.wallet.address
        except AttributeError as e:
            logger.error(f"Failed to get wallet address: {e}")
            raise AttributeError("Invalid wallet instance - missing address attribute") from e
    
    def get_wallet_instance(self):
        """
        Get the wallet instance.
        
        Returns:
            privy.Wallet: The wallet instance
        """
        return self.wallet
    
    def __str__(self) -> str:
        """String representation of the wallet wrapper."""
        try:
            return f"WalletWrapper(id={self.wallet.id}, address={self.wallet.address})"
        except AttributeError:
            return "WalletWrapper(invalid_wallet)"