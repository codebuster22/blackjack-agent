"""
@class WalletFactory:

Functionalities:
    - __init__(client: PrivyClient):
        - set the class variables

    - async create_wallet(user_id: str, twitter_user_name: str) -> privy.Wallet:
        - create a new wallet for the user
        - return the Wallet instance
"""
from privy import AsyncPrivyAPI
import logging

logger = logging.getLogger(__name__)

class WalletCreationError(Exception):
    """Raised when wallet creation fails."""
    pass

class WalletFactory:
    """
    Factory class for creating Privy-based wallets.
    
    Simplified design: Just creates wallets without user context.
    User-to-wallet mapping should be handled by external services.
    
    Functionalities:
        - __init__(client: AsyncPrivyAPI):
            - set the class variables

        - async create_wallet() -> privy.Wallet:
            - create a new Ethereum wallet using Privy
            - return the Wallet instance
    """
    
    def __init__(self, client: AsyncPrivyAPI):
        """
        Initialize WalletFactory with Privy client.
        
        Args:
            client: AsyncPrivyAPI client instance
            
        Raises:
            ValueError: if client is None
        """
        if client is None:
            raise ValueError("Privy client cannot be None")
            
        self.client = client
        logger.info("Initialized WalletFactory with Privy client")
    
    async def create_wallet(self):
        """
        Create a new Ethereum wallet using Privy.
        
        Returns:
            privy.Wallet: The created wallet instance
            
        Raises:
            WalletCreationError: if wallet creation fails
        """
        logger.info("Creating new wallet")
        
        try:
            # Create a new wallet for the Ethereum chain using Privy
            wallet = await self.client.wallets.create(chain_type="ethereum")
            
            # Validate wallet creation response
            if not wallet:
                raise WalletCreationError("Privy returned null wallet")
                
            if not hasattr(wallet, 'id') or not hasattr(wallet, 'address'):
                raise WalletCreationError("Invalid wallet response from Privy - missing required attributes")
            
            logger.info(f"Successfully created wallet: wallet_id={wallet.id}, address={wallet.address}")
            
            return wallet
            
        except Exception as e:
            if isinstance(e, WalletCreationError):
                # Re-raise our custom exceptions
                raise
            else:
                logger.error(f"Unexpected error during wallet creation: {e}")
                raise WalletCreationError(f"Failed to create wallet via Privy: {str(e)}") from e
    
    def __str__(self) -> str:
        """String representation of the wallet factory."""
        return f"WalletFactory(client={self.client})"