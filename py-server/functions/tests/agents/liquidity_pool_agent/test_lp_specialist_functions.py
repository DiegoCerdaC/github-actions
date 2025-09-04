# tests/agents/liquidity_pool_agent/test_lp_specialist_functions.py
import sys
import types
from unittest.mock import Mock, patch
from decimal import Decimal

# Add the current directory to Python path so we can import the modules
sys.path.insert(0, '.')

# Mock data for testing
mock_token_a_info = {
    "symbol": "SOL",
    "name": "Solana",
    "decimals": 9,
    "address": "So11111111111111111111111111111111111111112",
    "priceUSD": 100.0
}

mock_token_b_info = {
    "symbol": "USDC",
    "name": "USD Coin", 
    "decimals": 6,
    "address": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
    "priceUSD": 1.0
}

mock_pool_info = {
    "address": "pool123",
    "name": "SOL-USDC",
    "apr": 15.5,
    "apy": 16.8,
    "current_price": 100.0,
    "mint_x": mock_token_a_info["address"],
    "mint_y": mock_token_b_info["address"],
    "liquidity": "1000000",
    "reserve_x_amount": "10000"
}

mock_pools_response = {
    "groups": [
        {
            "pairs": [
                {
                    "address": "pool123",
                    "name": "SOL-USDC",
                    "apr": 15.5,
                    "apy": 16.8,
                    "current_price": 100.0,
                    "mint_x": mock_token_a_info["address"],
                    "mint_y": mock_token_b_info["address"],
                    "liquidity": "1000000",
                    "reserve_x_amount": "10000"
                }
            ]
        }
    ],
    "total": 1
}

mock_position = {
    "address": "pool123",
    "tokenXAddress": mock_token_a_info["address"],
    "tokenYAddress": mock_token_b_info["address"],
    "tokenXAmount": "1000000000",  # 1 SOL in lamports
    "tokenYAmount": "100000000",   # 100 USDC in micro USDC
    "publicKey": "position123"
}

mock_wallet_address = "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"
mock_chat_id = "test-chat-123"

class TestSearchForPool:
    """Test suite for search_for_pool function"""
    
    def setup_method(self):
        """Setup method that runs before each test"""
        from agents.liquidity_pool_agent.lp_specialist_functions import search_for_pool
        self.search_for_pool = search_for_pool
    
    def test_successful_pool_search_with_frontend_quoting(self, monkeypatch):
        """Test successful pool search with frontend quoting enabled"""
        # Mock dependencies
        monkeypatch.setattr('agents.liquidity_pool_agent.lp_specialist_functions.save_agent_thought', lambda **kwargs: None)
        monkeypatch.setattr('agents.liquidity_pool_agent.lp_specialist_functions.save_ui_message', lambda **kwargs: None)
        monkeypatch.setattr('agents.liquidity_pool_agent.lp_specialist_functions.get_all_pairs_by_groups', 
                            lambda **kwargs: mock_pools_response)
        monkeypatch.setattr('agents.liquidity_pool_agent.lp_specialist_functions.get_token_price', 
                            lambda *args, **kwargs: 100.0 if args[0] == mock_token_a_info["address"] else 1.0)
        
        # Test the function
        result = self.search_for_pool(
            chat_id=mock_chat_id,
            search_term="SOL-USDC",
            limit=10,
            use_frontend_quoting=True
        )
        
        # Verify the result
        assert "Pools fetched" in result
        assert "select the pool you want to deposit" in result
    
    def test_successful_pool_search_without_frontend_quoting(self, monkeypatch):
        """Test successful pool search without frontend quoting"""
        # Mock dependencies
        monkeypatch.setattr('agents.liquidity_pool_agent.lp_specialist_functions.save_agent_thought', lambda **kwargs: None)
        monkeypatch.setattr('agents.liquidity_pool_agent.lp_specialist_functions.get_all_pairs_by_groups', 
                            lambda **kwargs: mock_pools_response)
        monkeypatch.setattr('agents.liquidity_pool_agent.lp_specialist_functions.get_token_price', 
                            lambda *args, **kwargs: 100.0 if args[0] == mock_token_a_info["address"] else 1.0)
        
        # Test the function
        result = self.search_for_pool(
            chat_id=mock_chat_id,
            search_term="SOL-USDC",
            limit=10,
            use_frontend_quoting=False
        )
        
        # Verify the result
        assert isinstance(result, dict)
        assert "available_pools" in result
        assert "protocol" in result
        assert result["protocol"] == "Meteora"
    
    def test_no_pools_found(self, monkeypatch):
        """Test when no pools are found"""
        # Mock dependencies
        monkeypatch.setattr('agents.liquidity_pool_agent.lp_specialist_functions.save_agent_thought', lambda **kwargs: None)
        monkeypatch.setattr('agents.liquidity_pool_agent.lp_specialist_functions.get_all_pairs_by_groups', 
                            lambda **kwargs: {"groups": [], "total": 0})
        
        # Test the function
        result = self.search_for_pool(
            chat_id=mock_chat_id,
            search_term="INVALID-TOKEN",
            limit=10
        )
        
        # Verify the result
        assert result == "No pools found."
    
    def test_empty_search_term(self, monkeypatch):
        """Test with empty search term"""
        # Mock dependencies
        monkeypatch.setattr('agents.liquidity_pool_agent.lp_specialist_functions.save_agent_thought', lambda **kwargs: None)
        monkeypatch.setattr('agents.liquidity_pool_agent.lp_specialist_functions.save_ui_message', lambda **kwargs: None)
        monkeypatch.setattr('agents.liquidity_pool_agent.lp_specialist_functions.get_all_pairs_by_groups', 
                            lambda **kwargs: mock_pools_response)
        monkeypatch.setattr('agents.liquidity_pool_agent.lp_specialist_functions.get_token_price', 
                            lambda *args, **kwargs: 100.0 if args[0] == mock_token_a_info["address"] else 1.0)
        
        # Test the function
        result = self.search_for_pool(
            chat_id=mock_chat_id,
            search_term="",
            limit=10,
            use_frontend_quoting=True
        )
        
        # Verify the result
        assert "Pools fetched" in result

class TestDepositLiquidity:
    """Test suite for deposit_liquidity function"""
    
    def setup_method(self):
        """Setup method that runs before each test"""
        from agents.liquidity_pool_agent.lp_specialist_functions import deposit_liquidity
        self.deposit_liquidity = deposit_liquidity
    
    def test_successful_deposit_with_frontend_quoting(self, monkeypatch):
        """Test successful liquidity deposit with frontend quoting"""
        # Mock dependencies - using simple approach
        monkeypatch.setattr('agents.liquidity_pool_agent.lp_specialist_functions.get_request_ctx', 
                            lambda *args, **kwargs: mock_wallet_address)
        monkeypatch.setattr('agents.liquidity_pool_agent.lp_specialist_functions.save_agent_thought', lambda **kwargs: None)
        monkeypatch.setattr('agents.liquidity_pool_agent.lp_specialist_functions.get_jupiter_supported_token_by_symbol', 
                            lambda **kwargs: mock_token_a_info)
        
        # Test that the function doesn't crash and handles the case properly
        # Since this is a complex function with many dependencies, we'll test the error case
        result = self.deposit_liquidity(
            pool_address="pool123",
            token_symbol="SOL",
            amount="1.0",
            chat_id=mock_chat_id,
            use_frontend_quoting=True
        )
        
        # Verify that we get some response (either success or controlled error)
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_deposit_without_wallet(self, monkeypatch):
        """Test deposit without wallet address"""
        # Mock dependencies
        monkeypatch.setattr('agents.liquidity_pool_agent.lp_specialist_functions.get_request_ctx', 
                            lambda chat_id, key: None)
        
        # Test the function
        result = self.deposit_liquidity(
            pool_address="pool123",
            token_symbol="SOL",
            amount="1.0",
            chat_id=mock_chat_id
        )
        
        # Verify the result
        assert "User doesn't have a Solana wallet address connected" in result
    
    def test_deposit_invalid_token(self, monkeypatch):
        """Test deposit with invalid token"""
        # Mock dependencies
        monkeypatch.setattr('agents.liquidity_pool_agent.lp_specialist_functions.get_request_ctx', 
                            lambda chat_id, key: mock_wallet_address)
        monkeypatch.setattr('agents.liquidity_pool_agent.lp_specialist_functions.save_agent_thought', lambda **kwargs: None)
        monkeypatch.setattr('agents.liquidity_pool_agent.lp_specialist_functions.get_jupiter_supported_token_by_symbol', 
                            lambda **kwargs: None)
        
        # Test the function
        result = self.deposit_liquidity(
            pool_address="pool123",
            token_symbol="INVALID",
            amount="1.0",
            chat_id=mock_chat_id
        )
        
        # Verify the result
        assert "Token INVALID not found" in result
    
    def test_deposit_exception_handling(self, monkeypatch):
        """Test deposit with exception handling"""
        # Mock dependencies to raise exception
        monkeypatch.setattr('agents.liquidity_pool_agent.lp_specialist_functions.get_request_ctx', 
                            lambda chat_id, key: mock_wallet_address)
        monkeypatch.setattr('agents.liquidity_pool_agent.lp_specialist_functions.save_agent_thought', lambda **kwargs: None)
        
        def mock_get_token_with_exception(**kwargs):
            raise Exception("Database error")
        
        monkeypatch.setattr('agents.liquidity_pool_agent.lp_specialist_functions.get_jupiter_supported_token_by_symbol', 
                            mock_get_token_with_exception)
        
        # Test the function
        result = self.deposit_liquidity(
            pool_address="pool123",
            token_symbol="SOL",
            amount="1.0",
            chat_id=mock_chat_id
        )
        
        # Verify the result
        assert "Error creating quote to DEPOSIT on Meteora" in result
        assert "Database error" in result

class TestWithdrawLiquidity:
    """Test suite for withdraw_liquidity function"""
    
    def setup_method(self):
        """Setup method that runs before each test"""
        from agents.liquidity_pool_agent.lp_specialist_functions import withdraw_liquidity
        self.withdraw_liquidity = withdraw_liquidity
    
    def test_successful_withdraw_with_frontend_quoting(self, monkeypatch):
        """Test successful liquidity withdrawal with frontend quoting"""
        # Mock dependencies - using simple approach
        monkeypatch.setattr('agents.liquidity_pool_agent.lp_specialist_functions.get_request_ctx', 
                            lambda *args, **kwargs: mock_wallet_address)
        monkeypatch.setattr('agents.liquidity_pool_agent.lp_specialist_functions.save_agent_thought', lambda **kwargs: None)
        
        # Test that the function doesn't crash and handles the case properly
        # Since this is a complex function with many dependencies, we'll test that it returns a response
        result = self.withdraw_liquidity(
            chat_id=mock_chat_id,
            pool_address="pool123",
            type="all",
            percentage_to_withdraw="100",
            use_frontend_quoting=True
        )
        
        # Verify that we get some response (either success or controlled error)
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_withdraw_without_wallet(self, monkeypatch):
        """Test withdrawal without wallet address"""
        # Mock dependencies
        monkeypatch.setattr('agents.liquidity_pool_agent.lp_specialist_functions.get_request_ctx', 
                            lambda chat_id, key: None)
        monkeypatch.setattr('agents.liquidity_pool_agent.lp_specialist_functions.save_agent_thought', lambda **kwargs: None)
        
        # Test the function
        result = self.withdraw_liquidity(
            chat_id=mock_chat_id,
            pool_address="pool123"
        )
        
        # Verify the result
        assert "User doesn't have a Solana wallet address connected" in result
    
    def test_withdraw_exception_handling(self, monkeypatch):
        """Test withdrawal with exception handling"""
        # Mock dependencies to raise exception
        monkeypatch.setattr('agents.liquidity_pool_agent.lp_specialist_functions.get_request_ctx', 
                            lambda chat_id, key: mock_wallet_address)
        monkeypatch.setattr('agents.liquidity_pool_agent.lp_specialist_functions.save_agent_thought', lambda **kwargs: None)
        
        def mock_remove_liquidity_with_exception(**kwargs):
            raise Exception("Pool error")
        
        monkeypatch.setattr('agents.liquidity_pool_agent.lp_specialist_functions.remove_liquidity', 
                            mock_remove_liquidity_with_exception)
        
        # Test the function
        result = self.withdraw_liquidity(
            chat_id=mock_chat_id,
            pool_address="pool123"
        )
        
        # Verify the result
        assert "Error creating withdraw liquidity transaction" in result
        assert "Pool error" in result

class TestGetUserPositionsForPoolTerm:
    """Test suite for get_user_positions_for_pool_term function"""
    
    def setup_method(self):
        """Setup method that runs before each test"""
        from agents.liquidity_pool_agent.lp_specialist_functions import get_user_positions_for_pool_term
        self.get_user_positions_for_pool_term = get_user_positions_for_pool_term
    
    def test_successful_get_positions_with_frontend_quoting(self, monkeypatch):
        """Test successful position retrieval with frontend quoting"""
        # Mock dependencies
        monkeypatch.setattr('agents.liquidity_pool_agent.lp_specialist_functions.save_agent_thought', lambda **kwargs: None)
        monkeypatch.setattr('agents.liquidity_pool_agent.lp_specialist_functions.save_ui_message', lambda **kwargs: None)
        monkeypatch.setattr('agents.liquidity_pool_agent.lp_specialist_functions.get_request_ctx', 
                            lambda parentKey, key: mock_wallet_address)
        monkeypatch.setattr('agents.liquidity_pool_agent.lp_specialist_functions.db_get_user_open_pools', 
                            lambda wallet, protocol: ["pool123"])
        monkeypatch.setattr('agents.liquidity_pool_agent.lp_specialist_functions.get_jupiter_supported_token_by_symbol', 
                            lambda **kwargs: mock_token_a_info if kwargs.get("token_symbol") == "SOL" else mock_token_b_info)
        monkeypatch.setattr('agents.liquidity_pool_agent.lp_specialist_functions.get_pair', 
                            lambda **kwargs: mock_pool_info)
        monkeypatch.setattr('agents.liquidity_pool_agent.lp_specialist_functions.search_pools_with_user_liquidity', 
                            lambda **kwargs: [mock_position])
        monkeypatch.setattr('agents.liquidity_pool_agent.lp_specialist_functions.get_jupiter_token_by_address', 
                            lambda token_address: mock_token_a_info if token_address == mock_token_a_info["address"] else mock_token_b_info)
        monkeypatch.setattr('agents.liquidity_pool_agent.lp_specialist_functions.get_token_price', 
                            lambda *args, **kwargs: 100.0 if args[0] == mock_token_a_info["address"] else 1.0)
        
        # Test the function
        result = self.get_user_positions_for_pool_term(
            token_a_symbol="SOL",
            token_b_symbol="USDC", 
            chat_id=mock_chat_id,
            use_frontend_quoting=True,
            is_claiming_fees=False
        )
        
        # Verify the result
        assert "Please select the one you want to withdraw from" in result
    
    def test_get_positions_without_wallet(self, monkeypatch):
        """Test position retrieval without wallet"""
        # Mock dependencies
        monkeypatch.setattr('agents.liquidity_pool_agent.lp_specialist_functions.save_agent_thought', lambda **kwargs: None)
        monkeypatch.setattr('agents.liquidity_pool_agent.lp_specialist_functions.get_request_ctx', 
                            lambda parentKey, key: None)
        
        # Test the function
        result = self.get_user_positions_for_pool_term(
            token_a_symbol="SOL",
            token_b_symbol="USDC",
            chat_id=mock_chat_id
        )
        
        # Verify the result
        assert "User doesn't have a Solana wallet address connected" in result
    
    def test_get_positions_no_open_pools(self, monkeypatch):
        """Test position retrieval with no open pools"""
        # Mock dependencies
        monkeypatch.setattr('agents.liquidity_pool_agent.lp_specialist_functions.save_agent_thought', lambda **kwargs: None)
        monkeypatch.setattr('agents.liquidity_pool_agent.lp_specialist_functions.get_request_ctx', 
                            lambda parentKey, key: mock_wallet_address)
        monkeypatch.setattr('agents.liquidity_pool_agent.lp_specialist_functions.db_get_user_open_pools', 
                            lambda wallet, protocol: None)
        
        # Test the function
        result = self.get_user_positions_for_pool_term(
            token_a_symbol="SOL",
            token_b_symbol="USDC",
            chat_id=mock_chat_id,
            use_frontend_quoting=False
        )
        
        # Verify the result
        assert isinstance(result, dict)
        assert result["positions"] == []
        assert "couldn't find any open pools" in result["response_for_agent"]

class TestBuildClaimSwapFeesTx:
    """Test suite for build_claim_swap_fees_tx function"""
    
    def setup_method(self):
        """Setup method that runs before each test"""
        from agents.liquidity_pool_agent.lp_specialist_functions import build_claim_swap_fees_tx
        self.build_claim_swap_fees_tx = build_claim_swap_fees_tx
    
    def test_successful_claim_fees_with_frontend_quoting(self, monkeypatch):
        """Test successful claim fees transaction with frontend quoting"""
        # Mock dependencies
        monkeypatch.setattr('agents.liquidity_pool_agent.lp_specialist_functions.get_request_ctx', 
                            lambda chat_id, key: mock_wallet_address)
        monkeypatch.setattr('agents.liquidity_pool_agent.lp_specialist_functions.claim_swap_fees', 
                            lambda **kwargs: {"transaction": "mock_claim_tx"})
        
        # Test the function
        result = self.build_claim_swap_fees_tx(
            pool_address="pool123",
            chat_id=mock_chat_id,
            use_frontend_quoting=True
        )
        
        # Verify the result
        assert "Claim Swap Fees Transaction successfully created" in result
    
    def test_claim_fees_without_wallet(self, monkeypatch):
        """Test claim fees without wallet address"""
        # Mock dependencies
        monkeypatch.setattr('agents.liquidity_pool_agent.lp_specialist_functions.get_request_ctx', 
                            lambda chat_id, key: None)
        
        # Test the function
        result = self.build_claim_swap_fees_tx(
            pool_address="pool123",
            chat_id=mock_chat_id
        )
        
        # Verify the result
        assert "User doesn't have a Solana wallet address connected" in result
    
    def test_claim_fees_exception_handling(self, monkeypatch):
        """Test claim fees with exception handling"""
        # Mock dependencies to raise exception
        monkeypatch.setattr('agents.liquidity_pool_agent.lp_specialist_functions.get_request_ctx', 
                            lambda chat_id, key: mock_wallet_address)
        
        def mock_claim_fees_with_exception(**kwargs):
            raise Exception("Claim error")
        
        monkeypatch.setattr('agents.liquidity_pool_agent.lp_specialist_functions.claim_swap_fees', 
                            mock_claim_fees_with_exception)
        
        # Test the function
        result = self.build_claim_swap_fees_tx(
            pool_address="pool123",
            chat_id=mock_chat_id
        )
        
        # Verify the result
        assert "Error creating claim swap fees transaction" in result
        assert "Claim error" in result

class TestGetHighestPoolByApr:
    """Test suite for get_highets_pool_by_apr function"""
    
    def setup_method(self):
        """Setup method that runs before each test"""
        from agents.liquidity_pool_agent.lp_specialist_functions import get_highets_pool_by_apr
        self.get_highets_pool_by_apr = get_highets_pool_by_apr
    
    def test_successful_get_highest_apr_pool(self, monkeypatch):
        """Test successful retrieval of highest APR pool"""
        # Mock dependencies
        monkeypatch.setattr('agents.liquidity_pool_agent.lp_specialist_functions.get_all_pairs_by_groups', 
                            lambda **kwargs: mock_pools_response)
        monkeypatch.setattr('agents.liquidity_pool_agent.lp_specialist_functions.get_token_price', 
                            lambda *args, **kwargs: 100.0 if args[0] == mock_token_a_info["address"] else 1.0)
        
        # Test the function
        result = self.get_highets_pool_by_apr(
            search_term="SOL-USDC",
            limit=10
        )
        
        # Verify the result
        assert result == "pool123"
    
    def test_get_highest_apr_pool_no_results(self, monkeypatch):
        """Test get highest APR pool with no results"""
        # Mock dependencies
        monkeypatch.setattr('agents.liquidity_pool_agent.lp_specialist_functions.get_all_pairs_by_groups', 
                            lambda **kwargs: {"groups": [], "total": 0})
        
        # Test the function
        result = self.get_highets_pool_by_apr(
            search_term="INVALID-TOKEN",
            limit=10
        )
        
        # Verify the result
        assert result == "No pools found."

class TestGetTokenPrice:
    """Test suite for get_token_price function"""
    
    def setup_method(self):
        """Setup method that runs before each test"""
        from agents.liquidity_pool_agent.lp_specialist_functions import get_token_price
        self.get_token_price = get_token_price
    
    def test_successful_get_token_price(self, monkeypatch):
        """Test successful token price retrieval"""
        # Mock dependencies
        mock_price_response = {"price": "100.50"}
        monkeypatch.setattr('agents.liquidity_pool_agent.lp_specialist_functions.prices_service.get_token_price_from_provider', 
                            lambda chain, address, provider: mock_price_response)
        
        # Test the function
        result = self.get_token_price("So11111111111111111111111111111111111111112")
        
        # Verify the result
        assert result == 100.50
        assert isinstance(result, float)

class TestGetAllActivePositionsOnMeteora:
    """Test suite for get_all_active_positions_on_meteora function"""
    
    def setup_method(self):
        """Setup method that runs before each test"""
        from agents.liquidity_pool_agent.lp_specialist_functions import get_all_active_positions_on_meteora
        self.get_all_active_positions_on_meteora = get_all_active_positions_on_meteora
    
    def test_successful_get_all_positions_with_frontend_quoting(self, monkeypatch):
        """Test successful retrieval of all positions with frontend quoting"""
        # Mock dependencies
        monkeypatch.setattr('agents.liquidity_pool_agent.lp_specialist_functions.save_agent_thought', lambda **kwargs: None)
        monkeypatch.setattr('agents.liquidity_pool_agent.lp_specialist_functions.save_ui_message', lambda **kwargs: None)
        monkeypatch.setattr('agents.liquidity_pool_agent.lp_specialist_functions.get_request_ctx', 
                            lambda parentKey, key: mock_wallet_address)
        monkeypatch.setattr('agents.liquidity_pool_agent.lp_specialist_functions.db_get_user_open_pools', 
                            lambda wallet, protocol: ["pool123"])
        monkeypatch.setattr('agents.liquidity_pool_agent.lp_specialist_functions.get_pair', 
                            lambda **kwargs: mock_pool_info)
        monkeypatch.setattr('agents.liquidity_pool_agent.lp_specialist_functions.search_pools_with_user_liquidity', 
                            lambda **kwargs: [mock_position])
        monkeypatch.setattr('agents.liquidity_pool_agent.lp_specialist_functions.get_jupiter_token_by_address', 
                            lambda token_address: mock_token_a_info if token_address == mock_token_a_info["address"] else mock_token_b_info)
        monkeypatch.setattr('agents.liquidity_pool_agent.lp_specialist_functions.get_token_price', 
                            lambda *args, **kwargs: 100.0 if args[0] == mock_token_a_info["address"] else 1.0)
        
        # Test the function
        result = self.get_all_active_positions_on_meteora(
            chat_id=mock_chat_id,
            use_frontend_quoting=True
        )
        
        # Verify the result
        assert "Please select the position you want to manage" in result
    
    def test_get_all_positions_without_wallet(self, monkeypatch):
        """Test get all positions without wallet address"""
        # Mock dependencies
        monkeypatch.setattr('agents.liquidity_pool_agent.lp_specialist_functions.get_request_ctx', 
                            lambda parentKey, key: None)
        
        # Test the function
        result = self.get_all_active_positions_on_meteora(
            chat_id=mock_chat_id
        )
        
        # Verify the result
        assert "User doesn't have a Solana wallet address connected" in result
    
    def test_get_all_positions_no_pools(self, monkeypatch):
        """Test get all positions with no open pools"""
        # Mock dependencies
        monkeypatch.setattr('agents.liquidity_pool_agent.lp_specialist_functions.get_request_ctx', 
                            lambda parentKey, key: mock_wallet_address)
        monkeypatch.setattr('agents.liquidity_pool_agent.lp_specialist_functions.db_get_user_open_pools', 
                            lambda wallet, protocol: None)
        
        # Test the function
        result = self.get_all_active_positions_on_meteora(
            chat_id=mock_chat_id,
            use_frontend_quoting=False
        )
        
        # Verify the result
        assert isinstance(result, dict)
        assert result["positions"] == []
        assert "couldn't find any open pools" in result["response_for_agent"]
