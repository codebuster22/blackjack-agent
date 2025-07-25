"""
Manual Validation Module for Wallet Service

This module provides comprehensive testing of all wallet service functionality.
Run this manually to validate that the service is working correctly.

Usage:
    python services/wallet/manual_validation.py

Note: This is NOT a pytest test file - it's designed for manual execution only.
"""

import asyncio
import logging
import sys
import traceback
from typing import Dict, Any, List
from services.wallet import (
    WalletService, WalletServiceError, UserWalletWrapper,
    validate_ethereum_address, build_register_user_transaction_object
)
from config import get_config

# Set up detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ValidationResults:
    """Track validation test results."""
    
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.tests = []
    
    def add_result(self, test_name: str, passed: bool, message: str = ""):
        self.tests.append({
            "name": test_name,
            "passed": passed,
            "message": message
        })
        if passed:
            self.passed += 1
            print(f"✅ {test_name}: PASSED {message}")
        else:
            self.failed += 1
            print(f"❌ {test_name}: FAILED {message}")
    
    def print_summary(self):
        total = self.passed + self.failed
        print(f"\n{'='*60}")
        print(f"VALIDATION SUMMARY")
        print(f"{'='*60}")
        print(f"Total Tests: {total}")
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")
        print(f"Success Rate: {(self.passed/total*100):.1f}%" if total > 0 else "No tests run")
        
        if self.failed > 0:
            print(f"\n❌ FAILED TESTS:")
            for test in self.tests:
                if not test["passed"]:
                    print(f"  - {test['name']}: {test['message']}")
        else:
            print(f"\n🎉 ALL TESTS PASSED!")

# Test configuration - using your specified values
TEST_CONFIG = {
    "existing_wallet_id": "dpd9wmd1km38ydhj5h2tshog",  # Your funded test wallet
    "caip2": "eip155:10143", 
    "test_address": "0x0F0C534749CF5011bc9Bfde1c34451550af890C0",
    "contract_address": "0x1234567890123456789012345678901234567890",  # Dummy contract
}

async def validate_service_initialization(results: ValidationResults) -> WalletService:
    """Test 1: Service Initialization"""
    print(f"\n🔧 Testing Service Initialization...")
    
    try:
        # Get configuration
        config_values = get_config()
        
        # Test service creation
        service = WalletService(
            app_id=config_values.privy.app_id,
            app_secret=config_values.privy.app_secret,
            privy_base_url=config_values.privy.base_url,
            environment=config_values.privy.environment
        )
        results.add_result("Service Creation", True, "WalletService instance created")
        
        # Test initialization
        await service.initialize()
        results.add_result("Service Initialization", True, "All components initialized")
        
        # Test service status
        status = service.get_service_status()
        expected_components = ["has_client", "has_wallet_factory", "has_dealer_wallet", "has_user_aggregator"]
        all_initialized = all(status.get(comp, False) for comp in expected_components)
        results.add_result("Component Validation", all_initialized, f"Status: {status}")
        
        # Test initialization check
        is_initialized = service.is_initialized()
        results.add_result("Initialization Flag", is_initialized, f"Service initialized: {is_initialized}")
        
        return service
        
    except Exception as e:
        results.add_result("Service Initialization", False, f"Error: {str(e)}")
        raise

async def validate_transaction_utils(results: ValidationResults):
    """Test 2: Transaction Utilities"""
    print(f"\n🔧 Testing Transaction Utilities...")
    
    try:
        # Test address validation
        valid_address = TEST_CONFIG["test_address"]
        invalid_addresses = ["0x123", "not_an_address", "0xGGGG567890123456789012345678901234567890"]
        
        # Test valid address
        is_valid = validate_ethereum_address(valid_address)
        results.add_result("Valid Address Check", is_valid, f"Address: {valid_address}")
        
        # Test invalid addresses
        for invalid_addr in invalid_addresses:
            is_invalid = not validate_ethereum_address(invalid_addr)
            results.add_result(f"Invalid Address Check ({invalid_addr[:10]}...)", is_invalid, f"Correctly rejected: {invalid_addr}")
        
        # Test transaction object building
        tx_obj = build_register_user_transaction_object(
            user_address=valid_address,
            contract_address=TEST_CONFIG["contract_address"]
        )
        
        required_fields = ["to", "data", "value"]
        has_all_fields = all(field in tx_obj for field in required_fields)
        results.add_result("Transaction Object Building", has_all_fields, f"Fields: {list(tx_obj.keys())}")
        
        # Validate transaction object structure
        is_valid_format = (
            tx_obj["to"] == TEST_CONFIG["contract_address"] and
            tx_obj["data"].startswith("0x") and
            tx_obj["value"] == "0x0"
        )
        results.add_result("Transaction Object Format", is_valid_format, f"Structure validated")
        
    except Exception as e:
        results.add_result("Transaction Utilities", False, f"Error: {str(e)}")

async def validate_wallet_creation(service: WalletService, results: ValidationResults) -> List[str]:
    """Test 3: Wallet Creation and Caching"""
    print(f"\n💼 Testing Wallet Creation and Caching...")
    
    created_wallet_ids = []
    
    for i in range(3):  # Create 3 test wallets
        try:
            # Test wallet creation (no user parameters needed)
            wallet_wrapper = await service.create_wallet()
            
            # Validate wallet wrapper
            wallet_id = wallet_wrapper.get_wallet_id()
            wallet_address = wallet_wrapper.get_wallet_address()
            
            is_valid_wallet = (
                wallet_id and len(wallet_id) > 0 and
                wallet_address and validate_ethereum_address(wallet_address)
            )
            
            results.add_result(
                f"Wallet Creation {i+1}", 
                is_valid_wallet, 
                f"ID: {wallet_id}, Address: {wallet_address}"
            )
            
            created_wallet_ids.append(wallet_id)
            
        except Exception as e:
            results.add_result(f"Wallet Creation {i+1}", False, f"Error: {str(e)}")
    
    return created_wallet_ids

async def validate_wallet_retrieval(service: WalletService, created_wallet_ids: List[str], results: ValidationResults):
    """Test 4: Wallet Retrieval from Cache"""
    print(f"\n🔍 Testing Wallet Retrieval from Cache...")
    
    for i, wallet_id in enumerate(created_wallet_ids):
        try:
            # Test retrieval by wallet_id (only lookup method now)
            cached_wallet = await service.get_wallet(wallet_id)
            
            # Verify it's the correct wallet
            cached_id = cached_wallet.get_wallet_id()
            cached_address = cached_wallet.get_wallet_address()
            
            is_correct_wallet = cached_id == wallet_id
            results.add_result(
                f"Cache Retrieval Wallet {i+1}",
                is_correct_wallet,
                f"Expected: {wallet_id}, Got: {cached_id}, Address: {cached_address}"
            )
            
        except Exception as e:
            results.add_result(f"Cache Retrieval Wallet {i+1}", False, f"Error: {str(e)}")

async def validate_existing_wallet_fetch(service: WalletService, results: ValidationResults):
    """Test 5: Fetch Existing Wallet from Privy"""
    print(f"\n🔗 Testing Existing Wallet Fetch from Privy...")
    
    existing_wallet_id = TEST_CONFIG["existing_wallet_id"]
    
    try:
        # Fetch the existing funded wallet
        logger.info(f"Fetching existing funded wallet: {existing_wallet_id}")
        wallet_wrapper = await service.get_wallet(existing_wallet_id)
        
        # Validate wallet was fetched
        wallet_address = wallet_wrapper.get_wallet_address()
        wallet_id = wallet_wrapper.get_wallet_id()
        
        # Verify it's the expected test wallet
        is_correct_wallet = wallet_id == existing_wallet_id
        results.add_result(
            "Existing Wallet Fetch",
            is_correct_wallet,
            f"Expected: {existing_wallet_id}, Got: {wallet_id}"
        )
        
        wallet_valid = validate_ethereum_address(wallet_address) and len(wallet_id) > 0
        results.add_result(
            "Existing Wallet Validation",
            wallet_valid,
            f"Address: {wallet_address}, ID: {wallet_id}"
        )
        
    except Exception as e:
        results.add_result("Existing Wallet Fetch", False, f"Error: {str(e)}")

async def validate_registration_transaction(service: WalletService, results: ValidationResults):
    """Test 6: Registration Transaction with Existing Funded Wallet"""
    print(f"\n🔗 Testing Registration Transaction...")
    
    existing_wallet_id = TEST_CONFIG["existing_wallet_id"]
    
    try:
        # Test registration with existing funded wallet
        logger.info(f"Sending registration transaction with funded wallet: {existing_wallet_id}")
        transaction_hash = await service.register_existing_wallet_onchain(existing_wallet_id)
        
        # Validate transaction hash
        tx_hash_valid = (
            transaction_hash and 
            isinstance(transaction_hash, str) and 
            transaction_hash.startswith("0x") and 
            len(transaction_hash) == 66  # Standard Ethereum tx hash length
        )
        results.add_result(
            "Registration Transaction",
            tx_hash_valid,
            f"TX Hash: {transaction_hash}"
        )
        
        # Get the wallet that was used for registration
        registered_wallet = await service.get_wallet(existing_wallet_id)
        registered_address = registered_wallet.get_wallet_address()
        
        is_cached = registered_address and validate_ethereum_address(registered_address)
        results.add_result(
            "Wallet Cached After Registration",
            is_cached,
            f"Wallet remains cached: {registered_address}"
        )
        
    except Exception as e:
        results.add_result("Registration Transaction", False, f"Error: {str(e)}")
        # Print full traceback for registration errors as they're critical
        print(f"Registration Error Details:\n{traceback.format_exc()}")

async def validate_cache_miss_recovery(service: WalletService, results: ValidationResults):
    """Test 7: Cache Miss Recovery from Privy"""
    print(f"\n🔄 Testing Cache Miss Recovery...")
    
    existing_wallet_id = TEST_CONFIG["existing_wallet_id"]
    
    try:
        # First, clear cache by creating a new aggregator instance
        # (simulating a service restart)
        service.user_wallet_aggregator.clear_cache()
        
        # Verify cache is empty
        cache_stats = service.get_service_status()["cache_stats"]
        is_empty = cache_stats["cache_size"] == 0
        results.add_result("Cache Empty After Clear", is_empty, f"Cache size: {cache_stats['cache_size']}")
        
        # Now try to get the wallet - should trigger Privy fetch
        fetched_wallet = await service.get_wallet(existing_wallet_id)
        
        # Validate wallet was fetched from Privy
        fetched_id = fetched_wallet.get_wallet_id()
        fetched_address = fetched_wallet.get_wallet_address()
        
        fetch_success = (
            fetched_id == existing_wallet_id and
            validate_ethereum_address(fetched_address)
        )
        results.add_result(
            "Privy Fetch on Cache Miss",
            fetch_success,
            f"Fetched wallet: {fetched_id} -> {fetched_address}"
        )
        
        # Verify wallet is now cached
        cache_stats_after = service.get_service_status()["cache_stats"]
        is_cached = cache_stats_after["cache_size"] == 1
        results.add_result(
            "Wallet Cached After Fetch",
            is_cached,
            f"Cache size after fetch: {cache_stats_after['cache_size']}"
        )
        
    except Exception as e:
        results.add_result("Cache Miss Recovery", False, f"Error: {str(e)}")

async def validate_error_handling(service: WalletService, results: ValidationResults):
    """Test 8: Error Handling"""
    print(f"\n⚠️  Testing Error Handling...")
    
    # Test invalid wallet retrieval
    try:
        await service.get_wallet("non_existent_wallet_id")
        results.add_result("Invalid Wallet Retrieval", False, "Should have raised error")
    except WalletServiceError:
        results.add_result("Invalid Wallet Retrieval", True, "Correctly raised WalletServiceError")
    except Exception as e:
        results.add_result("Invalid Wallet Retrieval", False, f"Wrong exception type: {type(e)}")
    
    # Test invalid registration parameters
    try:
        await service.register_existing_wallet_onchain("non_existent_wallet_id")
        results.add_result("Invalid Registration", False, "Should have raised error")
    except WalletServiceError:
        results.add_result("Invalid Registration", True, "Correctly raised WalletServiceError")
    except Exception as e:
        results.add_result("Invalid Registration", False, f"Wrong exception type: {type(e)}")

async def validate_cache_statistics(service: WalletService, results: ValidationResults):
    """Test 9: Cache Statistics and Monitoring"""
    print(f"\n📊 Testing Cache Statistics...")
    
    try:
        status = service.get_service_status()
        cache_stats = status.get("cache_stats", {})
        
        # Validate cache stats structure (simplified)
        expected_stats = ["cache_size", "max_cache_size", "wallet_id_entries"]
        has_all_stats = all(stat in cache_stats for stat in expected_stats)
        results.add_result("Cache Stats Structure", has_all_stats, f"Stats: {list(cache_stats.keys())}")
        
        # Validate cache has entries (we created some wallets)
        has_entries = cache_stats.get("cache_size", 0) > 0
        results.add_result("Cache Has Entries", has_entries, f"Cache size: {cache_stats.get('cache_size', 0)}")
        
        # Validate consistency (simplified - only one index now)
        cache_size = cache_stats.get("cache_size", 0)
        wallet_entries = cache_stats.get("wallet_id_entries", 0)
        
        index_consistent = cache_size == wallet_entries
        results.add_result("Cache Index Consistency", index_consistent, 
                         f"Size: {cache_size}, Wallet entries: {wallet_entries}")
        
        print(f"📊 Final Cache Statistics:")
        for key, value in cache_stats.items():
            print(f"   {key}: {value}")
            
    except Exception as e:
        results.add_result("Cache Statistics", False, f"Error: {str(e)}")

async def run_complete_validation():
    """Run all validation tests in sequence."""
    print(f"🚀 STARTING WALLET SERVICE MANUAL VALIDATION (Simplified API)")
    print(f"={'='*60}")
    
    results = ValidationResults()
    service = None
    created_wallet_ids = []
    
    try:
        # Test 1: Service Initialization
        service = await validate_service_initialization(results)
        
        # Test 2: Transaction Utilities
        await validate_transaction_utils(results)
        
        # Test 3: Wallet Creation
        created_wallet_ids = await validate_wallet_creation(service, results)
        
        # Test 4: Wallet Retrieval
        await validate_wallet_retrieval(service, created_wallet_ids, results)
        
        # Test 5: Existing Wallet Fetch
        await validate_existing_wallet_fetch(service, results)
        
        # Test 6: Registration Transaction
        await validate_registration_transaction(service, results)
        
        # Test 7: Cache Miss Recovery
        await validate_cache_miss_recovery(service, results)
        
        # Test 8: Error Handling
        await validate_error_handling(service, results)
        
        # Test 9: Cache Statistics
        await validate_cache_statistics(service, results)
        
    except Exception as e:
        print(f"\n💥 CRITICAL ERROR DURING VALIDATION:")
        print(f"Error: {str(e)}")
        print(f"Traceback:\n{traceback.format_exc()}")
        results.add_result("Critical Error", False, str(e))
    
    finally:
        # Print final results
        results.print_summary()
        
        # Return appropriate exit code
        if results.failed > 0:
            print(f"\n❌ Validation completed with {results.failed} failures.")
            return False
        else:
            print(f"\n✅ All validations passed successfully!")
            return True

def check_environment():
    """Check required environment variables."""
    import os
    
    required_vars = ["DEALER_PRIVATE_KEY", "RPC_URL"]
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print(f"\nPlease set these environment variables before running validation.")
        return False
    
    return True

if __name__ == "__main__":
    print(f"🔧 Wallet Service Manual Validation (Simplified API)")
    print(f"Using test configuration:")
    for key, value in TEST_CONFIG.items():
        print(f"   {key}: {value}")
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    # Run validation
    try:
        success = asyncio.run(run_complete_validation())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n⚠️  Validation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1) 