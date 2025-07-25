"""
Real Wallet Integration Test

This test file contains a single comprehensive test that validates the complete
wallet integration flow using real blockchain transactions.

This is the ONLY test that should use real blockchain transactions to avoid
costly and slow test execution.
"""

import pytest
import asyncio
from services.service_manager import service_manager
from tests.test_helpers import setup_test_environment, cleanup_test_environment


@pytest.mark.integration
@pytest.mark.real_blockchain
@pytest.mark.slow
class TestRealWalletIntegration:
    """Test real wallet integration with blockchain transactions."""
    
    @pytest.mark.asyncio
    async def test_complete_wallet_integration_flow(self, clean_database):
        """
        Test the complete wallet integration flow with real blockchain transactions.
        
        This test:
        1. Creates a user with real wallet creation
        2. Registers the wallet onchain (real transaction)
        3. Verifies the wallet is properly stored in database
        4. Tests wallet retrieval functionality
        
        This is the ONLY test that should use real blockchain transactions.
        """
        # Setup test environment
        setup_test_environment()
        
        try:
            # Initialize services
            await service_manager.initialize()
            
            # Test username
            test_username = "real_wallet_test_user"
            
            # Step 1: Create user with real wallet service
            # This will create a real wallet and register it onchain
            username = await service_manager.user_manager.create_user_if_not_exists(
                test_username, 
                service_manager.wallet_service
            )
            
            assert username == test_username
            
            # Step 2: Verify user was created in database
            user = await service_manager.user_manager._get_user_by_username(username)
            assert user is not None
            assert user['username'] == test_username
            assert user['privy_wallet_id'] is not None
            assert user['privy_wallet_address'] is not None
            assert user['privy_wallet_address'].startswith('0x')
            
            # Step 3: Test wallet info retrieval
            wallet_info = await service_manager.user_manager.get_user_wallet_info(username)
            assert wallet_info['wallet_id'] == user['privy_wallet_id']
            assert wallet_info['wallet_address'] == user['privy_wallet_address']
            
            # Step 4: Test wallet retrieval by user_id
            wallet_info_by_id = await service_manager.user_manager.get_user_wallet_info(user['user_id'])
            assert wallet_info_by_id['wallet_id'] == user['privy_wallet_id']
            assert wallet_info_by_id['wallet_address'] == user['privy_wallet_address']
            
            # Step 5: Verify wallet exists in Privy (real wallet service)
            real_wallet = await service_manager.wallet_service.get_wallet(user['privy_wallet_id'])
            assert real_wallet.get_wallet_id() == user['privy_wallet_id']
            assert real_wallet.get_wallet_address() == user['privy_wallet_address']
            
            print(f"✅ Real wallet integration test passed!")
            print(f"   Username: {username}")
            print(f"   Wallet ID: {user['privy_wallet_id']}")
            print(f"   Wallet Address: {user['privy_wallet_address']}")
            
        finally:
            # Cleanup test environment
            cleanup_test_environment() 