"""
@module transaction_utils:

Utility functions for building blockchain transaction objects

Functions:
    - build_register_user_transaction_object(user_address: str, contract_address: str) -> dict:
        - encode the contract call: registerUser(user_address)
        - return transaction object: {to: contract_address, data: encoded_call, value: 0}
        
        Error Handling:
            - AddressValidationError: if user_address or contract_address format is invalid
            - EncodingError: if contract call encoding fails
            
        Validation:
            - Validate user_address is valid Ethereum address
            - Validate contract_address is valid Ethereum address
            - Validate encoded call data is properly formatted
""" 
from eth_abi import encode
from eth_utils import function_signature_to_4byte_selector
import re
import logging

logger = logging.getLogger(__name__)

# ABI for the registerUser function
REGISTER_USER_ABI = {
    "name": "registerUser",
    "type": "function",
    "inputs": [
        {"name": "userAddress", "type": "address"}
    ]
}

class AddressValidationError(Exception):
    """Raised when address validation fails."""
    pass

class EncodingError(Exception):
    """Raised when contract call encoding fails."""
    pass

def validate_ethereum_address(address: str) -> bool:
    """
    Validate Ethereum address format.
    
    Args:
        address: The address to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    # Check if address is 42 characters long and starts with 0x
    if not isinstance(address, str):
        return False
    
    if len(address) != 42:
        return False
        
    if not address.startswith('0x'):
        return False
        
    # Check if the rest are valid hex characters
    hex_part = address[2:]
    return re.match(r'^[0-9a-fA-F]+$', hex_part) is not None

def build_register_user_transaction_object(user_address: str, contract_address: str) -> dict:
    """
    Build transaction object for user registration on blockchain.
    
    Args:
        user_address: The user's wallet address to register
        contract_address: The contract address to call
        
    Returns:
        dict: Transaction object with {to, data, value} format
        
    Raises:
        AddressValidationError: if user_address or contract_address format is invalid
        EncodingError: if contract call encoding fails
        
    Validation:
        - Validate user_address is valid Ethereum address
        - Validate contract_address is valid Ethereum address
        - Validate encoded call data is properly formatted
    """
    logger.info(f"Building registration transaction for user: {user_address}, contract: {contract_address}")
    
    # Validate addresses
    if not validate_ethereum_address(user_address):
        raise AddressValidationError(f"Invalid user address format: {user_address}")
        
    if not validate_ethereum_address(contract_address):
        raise AddressValidationError(f"Invalid contract address format: {contract_address}")
    
    try:
        # Create function signature
        function_signature = "registerUser(address)"
        
        # Get function selector (first 4 bytes of keccak256 hash)
        function_selector = function_signature_to_4byte_selector(function_signature)
        
        # Encode the parameters
        # Convert user_address to bytes format for encoding
        user_address_bytes = bytes.fromhex(user_address[2:])  # Remove 0x prefix
        
        # Encode the address parameter
        encoded_params = encode(['address'], [user_address])
        
        # Combine selector and encoded parameters
        encoded_data = "0x" + function_selector.hex() + encoded_params.hex()
        
        # Build transaction object
        transaction_object = {
            "to": contract_address,
            "data": encoded_data,
            "value": "0x0"  # No ETH value for registration
        }
        
        logger.info(f"Successfully built transaction object: {transaction_object}")
        return transaction_object
        
    except Exception as e:
        logger.error(f"Failed to encode contract call: {e}")
        raise EncodingError(f"Failed to encode registerUser call: {str(e)}") from e

def validate_transaction_object(transaction_obj: dict) -> bool:
    """
    Validate that transaction object has required fields.
    
    Args:
        transaction_obj: Transaction object to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    required_fields = ["to", "data", "value"]
    
    if not isinstance(transaction_obj, dict):
        return False
        
    for field in required_fields:
        if field not in transaction_obj:
            return False
            
    # Validate 'to' field is valid address
    if not validate_ethereum_address(transaction_obj["to"]):
        return False
        
    # Validate 'data' field starts with 0x
    if not isinstance(transaction_obj["data"], str) or not transaction_obj["data"].startswith("0x"):
        return False
        
    return True 