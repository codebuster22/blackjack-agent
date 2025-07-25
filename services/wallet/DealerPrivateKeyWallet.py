import os
from web3 import Web3
from eth_account import Account
import logging

logger = logging.getLogger(__name__)

class DealerWalletError(Exception):
    """Raised when dealer wallet operations fail."""
    pass

class DealerPrivateKeyWallet:
    """
    Dealer wallet implementation using private key and web3.py.
    Independent of Privy-based wallet system.
    
    Functionalities:
        - __init__():
            - Access the env DEALER_PRIVATE_KEY, RPC_URL, ACCESS_TOKEN_FOR_RPC
            - initializes web3 instance using web3.py
            - initializes the wallet instance using web3.py

        - async get_wallet_address() -> str:
            - return the wallet address of the dealer wallet
    """
    
    def __init__(self):
        """
        Initialize DealerPrivateKeyWallet with environment variables.
        
        Raises:
            DealerWalletError: if required environment variables are missing or invalid
        """
        logger.info("Initializing DealerPrivateKeyWallet")
        
        # Access environment variables
        self.private_key = os.getenv('DEALER_PRIVATE_KEY')
        self.rpc_url = os.getenv('RPC_URL')
        self.access_token = os.getenv('ACCESS_TOKEN_FOR_RPC')
        
        # Validate required environment variables
        if not self.private_key:
            raise DealerWalletError("DEALER_PRIVATE_KEY environment variable is required")
            
        if not self.rpc_url:
            raise DealerWalletError("RPC_URL environment variable is required")
        
        # ACCESS_TOKEN_FOR_RPC is optional, some RPCs don't require it
        if not self.access_token:
            logger.warning("ACCESS_TOKEN_FOR_RPC not provided, using RPC without authentication")
        
        try:
            # Validate private key format
            if not self.private_key.startswith('0x'):
                # Add 0x prefix if missing
                self.private_key = '0x' + self.private_key
            
            # Initialize web3 instance
            if self.access_token:
                # Use authentication headers if token is provided
                headers = {'Authorization': f'Bearer {self.access_token}'}
                self.web3 = Web3(Web3.HTTPProvider(self.rpc_url, request_kwargs={'headers': headers}))
            else:
                self.web3 = Web3(Web3.HTTPProvider(self.rpc_url))
            
            # Test web3 connection
            if not self.web3.is_connected():
                raise DealerWalletError(f"Failed to connect to RPC at {self.rpc_url}")
            
            # Initialize wallet instance using web3.py
            try:
                self.account = Account.from_key(self.private_key)
                self.wallet_address = self.account.address
            except Exception as e:
                raise DealerWalletError(f"Invalid private key format: {str(e)}") from e
            
            logger.info(f"Successfully initialized DealerPrivateKeyWallet with address: {self.wallet_address}")
            logger.info(f"Connected to RPC: {self.rpc_url}")
            
        except DealerWalletError:
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            logger.error(f"Unexpected error during dealer wallet initialization: {e}")
            raise DealerWalletError(f"Failed to initialize dealer wallet: {str(e)}") from e
    
    def get_wallet_address(self) -> str:
        """
        Get the wallet address of the dealer wallet.
        
        Returns:
            str: The dealer wallet address
            
        Raises:
            DealerWalletError: if wallet is not properly initialized
        """
        if not hasattr(self, 'wallet_address') or not self.wallet_address:
            raise DealerWalletError("Dealer wallet not properly initialized - missing address")
        
        logger.debug(f"Returning dealer wallet address: {self.wallet_address}")
        return self.wallet_address

    def __str__(self) -> str:
        """String representation of the dealer wallet."""
        try:
            return f"DealerPrivateKeyWallet(address={self.wallet_address}, rpc={self.rpc_url})"
        except AttributeError:
            return "DealerPrivateKeyWallet(not_initialized)" 