"""
@class WalletService:

Description:

Functionalities:
    - __init__(app_id, app_secret, privy_base_url):
        - set the class variables
    - async initialize():
        description: Initialize the service and its dependencies
        logic:
            - Initializes Privy Client
            - Create new instance of WalletFactory, with __init__(client: PrivyClient)
            - Create new instance of DealerPrivateKeyWallet()
            - Create new instance of UserWalletAggregator() with __init__(client: PrivyClient)
            - validate the instances to be initialized
            - mark the service as initialized

    - async create_user_wallet(db_user_id: str, twitter_user_name: str) -> UserWalletWrapper:
        - create a new wallet using WalletFactory that returns a privy.Wallet instance
        - pass the newly created wallet to UserWalletAggregator.cache_user_wallet to be kept in-memory as cache for future use mapped to the db_user_id, twitter_user_name and wallet_id which returns the UserWalletWrapper instance
        - return the UserWalletWrapper instance

    - async get_user_wallet_wrapper(**kwargs) -> UserWalletWrapper:
        - where **kwargs can be: db_user_id, twitter_user_name or wallet_id
        - get the user wallet details from UserWalletAggregator based on **kwargs stored in the database mapped to the user
        - return the UserWalletWrapper instance

    - async register_user_onchain(db_user_id: str, twitter_user_name: str) -> Tuple[UserWalletWrapper, str]:
        - create a new wallet for the user using this.create_user_wallet
        - send transaction via UserWalletWrapper.send_registration_transaction()
        - return UserWalletWrapper instance and registration transaction hash
        
        Error Handling Strategy:
            - ValidationError: if db_user_id/twitter_user_name is invalid or wallet creation fails
            - NetworkError: if RPC connection fails or transaction broadcast fails
            - ContractError: if contract call fails (user already registered, contract paused, etc.)
            - PrivyError: if Privy SDK fails to send transaction
            
        Recovery Strategy:
            - For NetworkError: retry with exponential backoff (max 3 attempts)
            - For ContractError: return specific error message to caller
            - For ValidationError: return immediately with validation details
            - For PrivyError: log error and return Privy-specific error message
"""



"""

flow:

user: User post tweet "@scottagent let's play"
agent: Check if user is already registered, if not registered, register them, which involes, creating new wallet, register them onchain, add it to db.
agent: if already registered, get the wallet id from db and get the wallet instance from privy.
agent: ask for bet amount
user: replies with bet amount
agent: call contract.startRoundWithBet(bet_amount, game_id) -> on success, deal initial cards
agent: reply to user with the hand state and play game locally
agent: post result and distribute winnings
recovery agent: on no successful game conclusion after 1 hour, refund the bet amount to the user
"""

from .WalletFactory import WalletFactory, WalletCreationError
from .DealerPrivateKeyWallet import DealerPrivateKeyWallet, DealerWalletError
from .UserWalletAggregator import UserWalletAggregator, CacheError, ValidationError as AggregatorValidationError
from .UserWalletWrapper import UserWalletWrapper, TransactionBuildError, PrivyTransactionError
from .transaction_utils import AddressValidationError
from privy import AsyncPrivyAPI
from typing import Tuple, Optional
import logging
import asyncio

logger = logging.getLogger(__name__)

class WalletServiceError(Exception):
    """Base exception for wallet service errors."""
    pass

class ServiceNotInitializedError(WalletServiceError):
    """Raised when service methods are called before initialization."""
    pass

class NetworkError(WalletServiceError):
    """Raised when network/RPC connection fails."""
    pass

class ContractError(WalletServiceError):
    """Raised when contract interaction fails."""
    pass

class WalletService:
    """
    Main wallet service for wallet operations using wallet_id only.
    
    Simplified design: Only manages wallets by wallet_id.
    User-to-wallet mapping should be handled by external services.
    
    Description:

    Functionalities:
        - __init__(app_id, app_secret, privy_base_url):
            - set the class variables
        - async initialize():
            description: Initialize the service and its dependencies
            logic:
                - Initializes Privy Client
                - Create new instance of WalletFactory
                - Create new instance of DealerPrivateKeyWallet
                - Create new instance of UserWalletAggregator
                - validate the instances to be initialized
                - mark the service as initialized

        - async create_wallet() -> UserWalletWrapper:
            - create a new wallet using WalletFactory that returns a privy.Wallet instance
            - cache the wallet in UserWalletAggregator by wallet_id
            - return the UserWalletWrapper instance

        - async get_wallet(wallet_id: str) -> UserWalletWrapper:
            - get the wallet by wallet_id from cache, with fallback to Privy if not cached
            - return the UserWalletWrapper instance

        - async register_user_onchain() -> Tuple[UserWalletWrapper, str]:
            - create a new wallet for the user using this.create_user_wallet
            - send registration transaction via UserWalletWrapper.send_registration_transaction()
            - return UserWalletWrapper instance and registration transaction hash
            
            Error Handling Strategy:
                - NetworkError: if RPC connection fails or transaction broadcast fails
                - ContractError: if contract call fails (user already registered, contract paused, etc.)
                - PrivyError: if Privy SDK fails to send transaction
                
            Recovery Strategy:
                - For NetworkError: return error message to caller
                - For ContractError: return specific error message to caller
                - For ValidationError: return immediately with validation details
                - For PrivyError: log error and return Privy-specific error message
    """
    
    def __init__(self, app_id: str, app_secret: str, privy_base_url: str, environment: str = "production", registration_contract_address: str = "0x0000000000000000000000000000000000000000", caip_chain_id: str = "eip155:10143"):
        """
        Initialize WalletService with Privy configuration.
        
        Args:
            app_id: Privy application ID
            app_secret: Privy application secret
            privy_base_url: Privy API base URL
            environment: Privy environment (production/development)
            
        Raises:
            ValueError: if required parameters are missing
        """
        # Validate required parameters
        if not app_id or not isinstance(app_id, str):
            raise ValueError("app_id must be a non-empty string")
        if not app_secret or not isinstance(app_secret, str):
            raise ValueError("app_secret must be a non-empty string")
        if not privy_base_url or not isinstance(privy_base_url, str):
            raise ValueError("privy_base_url must be a non-empty string")
        if not registration_contract_address or not isinstance(registration_contract_address, str):
            raise ValueError("registration_contract_address must be a non-empty string")
        if not caip_chain_id or not isinstance(caip_chain_id, str):
            raise ValueError("caip_chain_id must be a non-empty string")
            
        # Set class variables
        self.app_id = app_id
        self.app_secret = app_secret
        self.privy_base_url = privy_base_url
        self.environment = environment
        self.registration_contract_address = registration_contract_address
        self.caip_chain_id = caip_chain_id
        
        # Service components (initialized in initialize())
        self.client: Optional[AsyncPrivyAPI] = None
        self.wallet_factory: Optional[WalletFactory] = None
        self.dealer_wallet: Optional[DealerPrivateKeyWallet] = None
        self.user_wallet_aggregator: Optional[UserWalletAggregator] = None
        
        # Service state
        self._initialized = False
        
        logger.info(f"WalletService created with app_id: {app_id}, environment: {environment}")
    
    async def initialize(self):
        """
        Initialize the service and its dependencies.
        
        Logic:
            - Initializes Privy Client
            - Create new instance of WalletFactory
            - Create new instance of DealerPrivateKeyWallet
            - Create new instance of UserWalletAggregator
            - validate the instances to be initialized
            - mark the service as initialized
            
        Raises:
            WalletServiceError: if initialization fails
        """
        logger.info("Initializing WalletService...")
        
        try:
            # Initialize Privy Client
            logger.info("Initializing Privy client...")
            self.client = AsyncPrivyAPI(
                app_id=self.app_id,
                app_secret=self.app_secret,
                environment=self.environment,
                base_url=self.privy_base_url
            )
            
            # Create new instance of WalletFactory
            logger.info("Creating WalletFactory instance...")
            self.wallet_factory = WalletFactory(self.client)
            
            # Create new instance of DealerPrivateKeyWallet
            logger.info("Creating DealerPrivateKeyWallet instance...")
            self.dealer_wallet = DealerPrivateKeyWallet()
            
            # Create new instance of UserWalletAggregator
            logger.info("Creating UserWalletAggregator instance...")
            self.user_wallet_aggregator = UserWalletAggregator(self.client)
            
            # Validate the instances to be initialized
            if not self.client:
                raise WalletServiceError("Failed to initialize Privy client")
            if not self.wallet_factory:
                raise WalletServiceError("Failed to initialize WalletFactory")
            if not self.dealer_wallet:
                raise WalletServiceError("Failed to initialize DealerPrivateKeyWallet")
            if not self.user_wallet_aggregator:
                raise WalletServiceError("Failed to initialize UserWalletAggregator")
            
            # Test dealer wallet connection
            dealer_address = self.dealer_wallet.get_wallet_address()
            logger.info(f"Dealer wallet initialized with address: {dealer_address}")
            
            # Mark the service as initialized
            self._initialized = True
            
            logger.info("WalletService successfully initialized!")
            
        except DealerWalletError as e:
            logger.error(f"Dealer wallet initialization failed: {e}")
            raise WalletServiceError(f"Failed to initialize dealer wallet: {e}") from e
        except Exception as e:
            logger.error(f"Service initialization failed: {e}")
            raise WalletServiceError(f"Failed to initialize WalletService: {e}") from e
    
    def _ensure_initialized(self):
        """Ensure service is initialized before operation."""
        if not self._initialized:
            raise ServiceNotInitializedError("WalletService must be initialized before use. Call initialize() first.")
    
    async def create_wallet(self) -> UserWalletWrapper:
        """
        Create a new wallet and cache it.
        
        Returns:
            UserWalletWrapper: The created and cached wallet wrapper
            
        Raises:
            ServiceNotInitializedError: if service not initialized
            WalletServiceError: if wallet creation or caching fails
        """
        self._ensure_initialized()
        
        logger.info("Creating new wallet")
        
        try:
            # Create a new wallet using WalletFactory
            wallet = await self.wallet_factory.create_wallet()
            wallet_id = wallet.id
            
            # Cache the wallet by wallet_id
            wallet_wrapper = self.user_wallet_aggregator.cache_wallet(wallet)
            
            logger.info(f"Successfully created and cached wallet: {wallet_id}")
            return wallet_wrapper
            
        except WalletCreationError as e:
            logger.error(f"Wallet creation failed: {e}")
            raise WalletServiceError(f"Failed to create wallet: {e}") from e
        except (CacheError, AggregatorValidationError) as e:
            logger.error(f"Wallet caching failed: {e}")
            raise WalletServiceError(f"Failed to cache wallet: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error during wallet creation: {e}")
            raise WalletServiceError(f"Unexpected error creating wallet: {e}") from e
    
    async def get_wallet(self, wallet_id: str) -> UserWalletWrapper:
        """
        Get wallet by wallet_id from cache, with fallback to Privy if not cached.
        
        Args:
            wallet_id: The wallet ID to retrieve
            
        Returns:
            UserWalletWrapper: The cached or fetched wallet wrapper
            
        Raises:
            ServiceNotInitializedError: if service not initialized
            WalletServiceError: if wallet lookup fails
        """
        self._ensure_initialized()
        
        logger.info(f"Getting wallet: {wallet_id}")
        
        try:
            # First, try to get from cache
            wallet_wrapper = self.user_wallet_aggregator.get_wallet(wallet_id)
            logger.info(f"Successfully retrieved wallet from cache: {wallet_id}")
            return wallet_wrapper
            
        except (KeyError, AggregatorValidationError) as cache_miss_error:
            # Cache miss - try to fetch from Privy
            logger.info(f"Cache miss for wallet_id {wallet_id}, attempting to fetch from Privy")
            try:
                # Fetch wallet from Privy
                wallet = await self._fetch_wallet_from_privy(wallet_id)
                
                # Cache the fetched wallet
                wallet_wrapper = self.user_wallet_aggregator.cache_wallet(wallet)
                
                logger.info(f"Successfully fetched and cached wallet from Privy: {wallet_id}")
                return wallet_wrapper
                
            except Exception as privy_error:
                logger.error(f"Failed to fetch wallet from Privy: {privy_error}")
                raise WalletServiceError(f"Wallet not in cache and Privy fetch failed: {privy_error}") from privy_error
                
        except Exception as e:
            logger.error(f"Unexpected error during wallet lookup: {e}")
            raise WalletServiceError(f"Unexpected error getting wallet: {e}") from e

    async def _fetch_wallet_from_privy(self, wallet_id: str):
        """
        Fetch an existing wallet from Privy by wallet_id.
        
        Args:
            wallet_id: The Privy wallet ID to fetch
            
        Returns:
            privy.Wallet: The wallet instance from Privy
            
        Raises:
            WalletServiceError: if fetch fails
        """
        try:
            logger.info(f"Fetching wallet {wallet_id} from Privy")
            wallet = await self.client.wallets.get(wallet_id)
            
            if not wallet:
                raise WalletServiceError(f"Wallet {wallet_id} not found in Privy")
                
            if not hasattr(wallet, 'id') or not hasattr(wallet, 'address'):
                raise WalletServiceError(f"Invalid wallet response from Privy for {wallet_id}")
            
            logger.info(f"Successfully fetched wallet from Privy: {wallet_id} -> {wallet.address}")
            return wallet
            
        except Exception as e:
            logger.error(f"Failed to fetch wallet {wallet_id} from Privy: {e}")
            raise WalletServiceError(f"Privy wallet fetch failed: {e}") from e

    async def register_user_onchain(self) -> Tuple[UserWalletWrapper, str]:
        """
        Register wallet onchain by sending registration transaction.
        
        Returns:
            UserWalletWrapper: The wallet wrapper
            str: Registration transaction hash
            
        Raises:
            ServiceNotInitializedError: if service not initialized
            WalletServiceError: if registration fails
        """
        self._ensure_initialized()
        
        logger.info(f"Creating and registering wallet onchain.")
        
        try:
            # Create a new wallet for the user
            user_wallet = await self.create_wallet()
            
            # Send transaction via UserWalletWrapper.send_registration_transaction()
            transaction_hash = await user_wallet.send_registration_transaction(
                contract_address=self.registration_contract_address,
                caip_chain_id=self.caip_chain_id
            )
            
            logger.info(f"Successfully registered wallet onchain: tx_hash={transaction_hash}")
            return (user_wallet, transaction_hash)
            
        except (TransactionBuildError, AddressValidationError) as e:
            logger.error(f"Validation error during registration: {e}")
            raise WalletServiceError(f"Validation failed: {e}") from e
            
        except PrivyTransactionError as e:
            logger.error(f"Privy transaction error: {e}")
            raise WalletServiceError(f"Privy transaction failed: {e}") from e
            
        except Exception as e:
            logger.error(f"Exception during registration: {e}")
            raise WalletServiceError(f"Registration failed: {e}") from e

    async def register_existing_wallet_onchain(self, wallet_id: str) -> str:
        """
        Register an existing wallet onchain by sending registration transaction.
        
        Args:
            wallet_id: The wallet ID to register
            
        Returns:
            str: Registration transaction hash
            
        Raises:
            ServiceNotInitializedError: if service not initialized
            WalletServiceError: if registration fails
        """
        self._ensure_initialized()
        
        logger.info(f"Registering existing wallet onchain: {wallet_id}")
        
        try:
            # Get the existing wallet (from cache or fetch from Privy)
            user_wallet = await self.get_wallet(wallet_id)
            
            # Send transaction via UserWalletWrapper.send_registration_transaction()
            transaction_hash = await user_wallet.send_registration_transaction(
                contract_address=self.registration_contract_address,
                caip_chain_id=self.caip_chain_id
            )
            
            logger.info(f"Successfully registered existing wallet onchain: wallet_id={wallet_id}, tx_hash={transaction_hash}")
            return transaction_hash
            
        except (TransactionBuildError, AddressValidationError) as e:
            logger.error(f"Validation error during registration: {e}")
            raise WalletServiceError(f"Validation failed: {e}") from e
            
        except PrivyTransactionError as e:
            logger.error(f"Privy transaction error: {e}")
            raise WalletServiceError(f"Privy transaction failed: {e}") from e
            
        except Exception as e:
            logger.error(f"Exception during registration: {e}")
            raise WalletServiceError(f"Registration failed: {e}") from e
    
    def is_initialized(self) -> bool:
        """Check if service is initialized."""
        return self._initialized
    
    def get_service_status(self) -> dict:
        """Get service status for monitoring."""
        status = {
            "initialized": self._initialized,
            "has_client": self.client is not None,
            "has_wallet_factory": self.wallet_factory is not None,
            "has_dealer_wallet": self.dealer_wallet is not None,
            "has_user_aggregator": self.user_wallet_aggregator is not None,
        }
        
        if self.user_wallet_aggregator:
            status["cache_stats"] = self.user_wallet_aggregator.get_cache_stats()
            
        return status
    
    def __str__(self) -> str:
        """String representation of the wallet service."""
        return f"WalletService(app_id={self.app_id}, initialized={self._initialized})"