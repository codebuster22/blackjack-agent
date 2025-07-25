"""
@class UserWalletWrapper:

inherits WalletWrapperBase, doesn't have any additional functionalities

Additional Functionalities:
    - async send_registration_transaction(contract_address: str) -> str:
        - get user wallet address from this.wallet
        - build transaction object using build_register_user_transaction_object() utility
        - send transaction via Privy SDK (unsigned, as Privy handles signing)
        - return transaction hash
        
        Error Handling Strategy:
            - TransactionBuildError: if transaction object construction fails
            - PrivyTransactionError: if Privy fails to send transaction
            - AddressValidationError: if contract_address is invalid
            
        Validation Steps:
            - Validate contract_address format before building transaction
            - Validate wallet instance exists and is active
            - Validate transaction object before sending to Privy
"""
from .WalletWrapperBase import WalletWrapperBase
from .transaction_utils import build_register_user_transaction_object, validate_transaction_object, AddressValidationError
from privy import AsyncPrivyAPI
import logging

logger = logging.getLogger(__name__)

class TransactionBuildError(Exception):
    """Raised when transaction object construction fails."""
    pass

class PrivyTransactionError(Exception):
    """Raised when Privy fails to send transaction."""
    pass

class UserWalletWrapper(WalletWrapperBase):
    """
    User wallet wrapper for Privy-based wallets.
    
    inherits WalletWrapperBase, doesn't have any additional functionalities
    
    Additional Functionalities:
        - async send_registration_transaction(contract_address: str) -> str:
            - get user wallet address from this.wallet
            - build transaction object using build_register_user_transaction_object() utility
            - send transaction via Privy SDK (unsigned, as Privy handles signing)
            - return transaction hash
            
            Error Handling Strategy:
                - TransactionBuildError: if transaction object construction fails
                - PrivyTransactionError: if Privy fails to send transaction
                - AddressValidationError: if contract_address is invalid
                
            Validation Steps:
                - Validate contract_address format before building transaction
                - Validate wallet instance exists and is active
                - Validate transaction object before sending to Privy
    """
    
    def __init__(self, wallet, client: AsyncPrivyAPI):
        """
        Initialize UserWalletWrapper.
        
        Args:
            wallet: privy.Wallet instance
            client: AsyncPrivyAPI client instance
        """
        super().__init__(wallet, client)
        logger.info(f"Initialized UserWalletWrapper for wallet: {wallet.id}")
    
    async def send_registration_transaction(self, contract_address: str, caip_chain_id: str = "eip155:10143") -> str:
        """
        Send registration transaction to register user on blockchain.
        
        Args:
            contract_address: The contract address to register with
            caip_chain_id: The CAIP2 blockchain chain identifier (default: eip155:10143)
            
        Returns:
            str: Transaction hash
            
        Raises:
            TransactionBuildError: if transaction object construction fails
            PrivyTransactionError: if Privy fails to send transaction
            AddressValidationError: if contract_address is invalid
        """
        logger.info(f"Sending registration transaction for wallet {self.wallet.id} to contract {contract_address}")
        
        try:
            # Validation Step 1: Validate wallet instance exists and is active
            if not self.wallet or not hasattr(self.wallet, 'address') or not hasattr(self.wallet, 'id'):
                raise TransactionBuildError("Wallet instance is invalid or inactive")
            
            # Get user wallet address
            user_address = self.get_wallet_address()
            wallet_id = self.get_wallet_id()
            
            logger.info(f"Building transaction for user address: {user_address}")
            
            # Validation Step 2: Build transaction object using utility function
            try:
                transaction_obj = build_register_user_transaction_object(user_address, contract_address)
            except AddressValidationError as e:
                logger.error(f"Address validation failed: {e}")
                raise AddressValidationError(f"Contract address validation failed: {e}") from e
            except Exception as e:
                logger.error(f"Transaction building failed: {e}")
                raise TransactionBuildError(f"Failed to build transaction object: {e}") from e
            
            # Validation Step 3: Validate transaction object before sending to Privy
            if not validate_transaction_object(transaction_obj):
                raise TransactionBuildError("Invalid transaction object generated")
            
            logger.info(f"Sending transaction via Privy: {transaction_obj}")
            
            # Send transaction via Privy SDK (unsigned, as Privy handles signing)
            try:
                rpc_response = await self.client.wallets.rpc(
                    wallet_id=wallet_id,
                    caip2=caip_chain_id,
                    method="eth_sendTransaction",
                    chain_type="ethereum",
                    address=user_address,
                    params={
                        "transaction": {
                            "from": user_address,
                            "to": transaction_obj["to"],
                            "data": transaction_obj["data"],
                            "value": transaction_obj["value"],
                        }
                    }
                )
                
                # Extract transaction hash from response
                if hasattr(rpc_response, 'data') and hasattr(rpc_response.data, 'hash'):
                    transaction_hash = rpc_response.data.hash
                    logger.info(f"Successfully sent registration transaction: {transaction_hash}")
                    return transaction_hash
                else:
                    logger.error(f"Unexpected RPC response format: {rpc_response}")
                    raise PrivyTransactionError("Invalid response format from Privy RPC")
                    
            except Exception as e:
                logger.error(f"Privy RPC call failed: {e}")
                raise PrivyTransactionError(f"Failed to send transaction via Privy: {e}") from e
                
        except (TransactionBuildError, PrivyTransactionError, AddressValidationError):
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            logger.error(f"Unexpected error in send_registration_transaction: {e}")
            raise TransactionBuildError(f"Unexpected error during registration: {e}") from e