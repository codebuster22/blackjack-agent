# Wallet Service Usage Guide

## Table of Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Installation & Setup](#installation--setup)
- [Configuration](#configuration)
- [Quick Start](#quick-start)
- [API Reference](#api-reference)
- [Usage Examples](#usage-examples)
- [Error Handling](#error-handling)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Overview

The Wallet Service provides a unified interface for managing blockchain wallets, supporting both:
- **User Wallets**: Managed by Privy (custodial, no private key management)
- **Dealer Wallets**: Private key-based wallets for automated operations

### Key Features
- ✅ Wallet creation and management
- ✅ In-memory caching for performance
- ✅ Blockchain transaction sending
- ✅ Registration contract interactions
- ✅ Cache-miss recovery from Privy
- ✅ Comprehensive error handling
- ✅ Async/await support

## Prerequisites

### Required Dependencies
```bash
# Core dependencies
privy-py>=1.0.0
web3>=6.0.0
eth-account>=0.8.0
httpx>=0.24.0

# Environment
python>=3.11
```

### Required Services
1. **Privy Account**: Sign up at [privy.io](https://privy.io)
2. **RPC Endpoint**: Blockchain RPC URL (e.g., Monad Testnet)
3. **Private Key**: For dealer wallet operations (optional)

### Environment Variables
```bash
# Privy Configuration (Required)
PRIVY_APP_ID=your_privy_app_id
PRIVY_APP_SECRET=your_privy_app_secret
PRIVY_ENVIRONMENT=staging  # or 'production'

# Blockchain Configuration (Required)
RPC_URL=https://testnet-rpc.monad.xyz
CAIP_CHAIN_ID=eip155:10143

# Dealer Wallet (Optional)
DEALER_PRIVATE_KEY=0x1234567890abcdef...
ACCESS_TOKEN_FOR_RPC=your_rpc_auth_token  # Optional

# Registration Contract (Required for registration)
REGISTRATION_CONTRACT_ADDRESS=0x1234567890123456789012345678901234567890
```

## Installation & Setup

### 1. Install Dependencies
```bash
# Using uv (recommended)
uv add privy-py web3 eth-account httpx

# Using pip
pip install privy-py web3 eth-account httpx
```

### 2. Environment Setup
Create a `.env` file in your project root:
```bash
# Copy example configuration
cp .env.example .env

# Edit with your values
vim .env
```

### 3. Import the Service
```python
from services.wallet import WalletService
import asyncio
```

## Configuration

### Basic Configuration
```python
# Minimal setup - uses environment variables
service = WalletService()
await service.initialize()
```

### Advanced Configuration
```python
# Custom configuration
service = WalletService(
    app_id="custom_app_id",
    app_secret="custom_secret", 
    environment="production",
    registration_contract_address="0x...",
    caip_chain_id="eip155:1"
)
await service.initialize()
```

## Quick Start

### Basic Wallet Operations
```python
import asyncio
from services.wallet import WalletService

async def main():
    # Initialize service
    service = WalletService()
    await service.initialize()
    
    # Create a new wallet
    user_wallet = await service.create_wallet()
    print(f"Created wallet: {user_wallet.get_wallet_id()}")
    print(f"Address: {user_wallet.get_wallet_address()}")
    
    # Retrieve wallet (from cache or Privy)
    retrieved_wallet = await service.get_wallet(user_wallet.get_wallet_id())
    print(f"Retrieved: {retrieved_wallet.get_wallet_address()}")
    
    # Register wallet onchain (creates new wallet)
    wallet, tx_hash = await service.register_user_onchain()
    print(f"Registration TX: {tx_hash}")
    
    # Register existing wallet onchain  
    tx_hash = await service.register_existing_wallet_onchain(user_wallet.get_wallet_id())
    print(f"Existing wallet TX: {tx_hash}")

if __name__ == "__main__":
    asyncio.run(main())
```

## API Reference

### WalletService

#### Initialization
```python
service = WalletService(
    app_id: Optional[str] = None,           # Privy app ID
    app_secret: Optional[str] = None,       # Privy app secret  
    environment: str = "staging",           # Privy environment
    registration_contract_address: Optional[str] = None,
    caip_chain_id: Optional[str] = None
)

await service.initialize()  # Required before use
```

#### Core Methods

##### `create_wallet() -> UserWalletWrapper`
Creates a new Privy wallet and caches it.
```python
wallet = await service.create_wallet()
wallet_id = wallet.get_wallet_id()
address = wallet.get_wallet_address()
```

##### `get_wallet(wallet_id: str) -> UserWalletWrapper`
Retrieves wallet from cache or fetches from Privy.
```python
wallet = await service.get_wallet("wallet_id_here")
```

##### `register_user_onchain() -> Tuple[UserWalletWrapper, str]`
Creates new wallet and registers it onchain.
```python
wallet, tx_hash = await service.register_user_onchain()
```

##### `register_existing_wallet_onchain(wallet_id: str) -> str`
Registers existing wallet onchain.
```python
tx_hash = await service.register_existing_wallet_onchain(wallet_id)
```

#### Utility Methods
```python
# Check if initialized
is_ready = service.is_initialized()

# Get service status
status = service.get_status()

# Get cache statistics
stats = service.user_wallet_aggregator.get_cache_stats()
```

### UserWalletWrapper

#### Properties
```python
wallet_id = wrapper.get_wallet_id()      # Returns: str
address = wrapper.get_wallet_address()   # Returns: str (0x...)
```

#### Transaction Methods
```python
# Send registration transaction
tx_hash = await wrapper.send_registration_transaction(
    contract_address="0x...",
    caip_chain_id="eip155:10143"
)
```

### Transaction Utilities

#### Address Validation
```python
from services.wallet.transaction_utils import validate_ethereum_address

is_valid = validate_ethereum_address("0x1234...")  # Returns: bool
```

#### Transaction Building
```python
from services.wallet.transaction_utils import build_register_user_transaction_object

tx_obj = build_register_user_transaction_object(
    user_address="0x...",
    contract_address="0x..."
)
# Returns: {"to": "0x...", "data": "0x...", "value": "0x0"}
```

## Usage Examples

### Example 1: Simple Wallet Creation
```python
async def create_user_wallet():
    service = WalletService()
    await service.initialize()
    
    # Create wallet
    wallet = await service.create_wallet()
    
    print(f"Wallet Created!")
    print(f"ID: {wallet.get_wallet_id()}")
    print(f"Address: {wallet.get_wallet_address()}")
    
    return wallet
```

### Example 2: Wallet with Registration
```python
async def create_and_register():
    service = WalletService()
    await service.initialize()
    
    try:
        # Create and register in one step
        wallet, tx_hash = await service.register_user_onchain()
        
        print(f"✅ Wallet registered successfully!")
        print(f"Wallet ID: {wallet.get_wallet_id()}")
        print(f"Address: {wallet.get_wallet_address()}")
        print(f"Transaction: {tx_hash}")
        
        return wallet, tx_hash
        
    except Exception as e:
        print(f"❌ Registration failed: {e}")
        raise
```

### Example 3: Retrieve and Use Existing Wallet
```python
async def use_existing_wallet(wallet_id: str):
    service = WalletService()
    await service.initialize()
    
    try:
        # Get wallet (cache hit or Privy fetch)
        wallet = await service.get_wallet(wallet_id)
        print(f"Found wallet: {wallet.get_wallet_address()}")
        
        # Register it onchain
        tx_hash = await service.register_existing_wallet_onchain(wallet_id)
        print(f"Registration TX: {tx_hash}")
        
        return wallet, tx_hash
        
    except Exception as e:
        print(f"Error: {e}")
        raise
```

### Example 4: Batch Operations
```python
async def create_multiple_wallets(count: int):
    service = WalletService()
    await service.initialize()
    
    wallets = []
    for i in range(count):
        wallet = await service.create_wallet()
        wallets.append({
            'id': wallet.get_wallet_id(),
            'address': wallet.get_wallet_address()
        })
        print(f"Created wallet {i+1}/{count}: {wallet.get_wallet_id()}")
    
    # Check cache stats
    stats = service.user_wallet_aggregator.get_cache_stats()
    print(f"Cache size: {stats['cache_size']}")
    
    return wallets
```

### Example 5: Error Handling & Retry
```python
async def robust_registration(wallet_id: str, max_retries: int = 3):
    service = WalletService()
    await service.initialize()
    
    for attempt in range(max_retries):
        try:
            tx_hash = await service.register_existing_wallet_onchain(wallet_id)
            print(f"✅ Success on attempt {attempt + 1}: {tx_hash}")
            return tx_hash
            
        except Exception as e:
            print(f"❌ Attempt {attempt + 1} failed: {e}")
            if attempt == max_retries - 1:
                print("Max retries reached, giving up")
                raise
            
            # Wait before retry
            await asyncio.sleep(2 ** attempt)
```

## Error Handling

### Common Exceptions

#### `ServiceNotInitializedError`
Service not initialized before use.
```python
try:
    wallet = await service.create_wallet()  # Service not initialized
except ServiceNotInitializedError:
    await service.initialize()
    wallet = await service.create_wallet()
```

#### `WalletServiceError`
General wallet service errors.
```python
try:
    wallet = await service.get_wallet("invalid_id")
except WalletServiceError as e:
    print(f"Wallet error: {e}")
```

#### `PrivyTransactionError`
Privy API transaction failures.
```python
try:
    tx_hash = await service.register_existing_wallet_onchain(wallet_id)
except PrivyTransactionError as e:
    if "insufficient funds" in str(e).lower():
        print("Wallet needs funding before transaction")
    else:
        print(f"Transaction failed: {e}")
```

#### `ValidationError`
Input validation failures.
```python
from services.wallet.transaction_utils import validate_ethereum_address

if not validate_ethereum_address(address):
    raise ValidationError(f"Invalid address: {address}")
```

### Error Recovery Patterns

#### Cache Miss Recovery
```python
async def get_wallet_with_recovery(service, wallet_id):
    try:
        # Try cache first
        return await service.get_wallet(wallet_id)
    except WalletServiceError as e:
        if "not found" in str(e):
            print(f"Wallet {wallet_id} not found in Privy")
            return None
        raise
```

#### Transaction Retry with Backoff
```python
async def send_with_retry(wallet, contract_address, caip_chain_id, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await wallet.send_registration_transaction(
                contract_address, caip_chain_id
            )
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            wait_time = 2 ** attempt
            await asyncio.sleep(wait_time)
```

## Best Practices

### 1. Service Lifecycle
```python
# ✅ Good: Initialize once, reuse
service = WalletService()
await service.initialize()

# Use service multiple times...
wallet1 = await service.create_wallet()
wallet2 = await service.create_wallet()

# ❌ Bad: Initialize multiple times
service1 = WalletService()
await service1.initialize()
service2 = WalletService()  # Unnecessary
await service2.initialize()
```

### 2. Error Handling
```python
# ✅ Good: Specific error handling
try:
    wallet = await service.get_wallet(wallet_id)
except WalletServiceError as e:
    if "not found" in str(e):
        # Handle missing wallet
        pass
    else:
        # Handle other errors
        pass
        
# ❌ Bad: Catch-all exception handling
try:
    wallet = await service.get_wallet(wallet_id)
except Exception:
    pass  # Silent failure
```

### 3. Cache Management
```python
# ✅ Good: Monitor cache stats
stats = service.user_wallet_aggregator.get_cache_stats()
if stats['cache_size'] > 900:  # Near limit
    print("Cache nearly full, consider clearing old entries")

# ✅ Good: Clear cache when appropriate
service.user_wallet_aggregator.clear_cache()
```

### 4. Resource Management
```python
# ✅ Good: Use async context managers
async def wallet_operations():
    service = WalletService()
    try:
        await service.initialize()
        # Perform operations...
        wallet = await service.create_wallet()
        return wallet
    finally:
        # Cleanup if needed
        service.user_wallet_aggregator.clear_cache()
```

### 5. Testing with Funded Wallets
```python
# ✅ Good: Use existing funded wallet for testing
TEST_WALLET_ID = "dpd9wmd1km38ydhj5h2tshog"  # Pre-funded

async def test_registration():
    service = WalletService()
    await service.initialize()
    
    # Use existing funded wallet
    tx_hash = await service.register_existing_wallet_onchain(TEST_WALLET_ID)
    assert tx_hash.startswith("0x")

# ❌ Bad: Create new wallet for testing (will have no funds)
async def test_registration_bad():
    service = WalletService()
    await service.initialize()
    
    wallet = await service.create_wallet()  # No funds!
    # This will fail with "insufficient funds"
    tx_hash = await service.register_existing_wallet_onchain(wallet.get_wallet_id())
```

## Troubleshooting

### Common Issues

#### 1. "Service not initialized"
**Problem**: Calling methods before `initialize()`
```python
# Fix
service = WalletService()
await service.initialize()  # Add this line
wallet = await service.create_wallet()
```

#### 2. "Insufficient funds for gas"
**Problem**: New wallets have no funds
```python
# Fix: Use pre-funded wallet for testing
FUNDED_WALLET_ID = "dpd9wmd1km38ydhj5h2tshog"
tx_hash = await service.register_existing_wallet_onchain(FUNDED_WALLET_ID)
```

#### 3. "Invalid wallet instance"
**Problem**: Privy response format changed
```python
# Check wallet attributes
wallet = await service.create_wallet()
print(f"Has ID: {hasattr(wallet.wallet, 'id')}")
print(f"Has address: {hasattr(wallet.wallet, 'address')}")
```

#### 4. "Cache miss" frequent warnings
**Problem**: Cache being cleared too often
```python
# Monitor cache usage
stats = service.user_wallet_aggregator.get_cache_stats()
print(f"Cache efficiency: {stats}")

# Increase cache size if needed
service.user_wallet_aggregator._max_cache_size = 2000
```

#### 5. RPC Connection Issues
**Problem**: Blockchain RPC unavailable
```python
# Check RPC endpoint
import httpx

async def check_rpc():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://testnet-rpc.monad.xyz",
            json={"method": "eth_blockNumber", "params": [], "id": 1}
        )
        print(f"RPC Status: {response.status_code}")
```

### Environment Issues

#### Missing Environment Variables
```bash
# Check required variables
echo $PRIVY_APP_ID
echo $PRIVY_APP_SECRET  
echo $RPC_URL
echo $CAIP_CHAIN_ID
echo $REGISTRATION_CONTRACT_ADDRESS
```

#### Wrong Environment
```python
# Verify Privy environment
service = WalletService(environment="staging")  # or "production"
```

### Debug Mode
```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('services.wallet')

# Now see detailed logs
service = WalletService()
await service.initialize()
```

---

## Support

For additional help:
1. Check the [manual validation script](./manual_validation.py) for working examples
2. Review error logs with DEBUG level logging enabled
3. Verify all environment variables are set correctly
4. Test with the provided funded wallet ID for transactions

**Last Updated**: December 2024  
**Version**: 2.0.0 (Simplified Wallet-ID-Only Architecture) 