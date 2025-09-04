# tests/agents/drift/test_drift_functions.py
import sys
import types
from unittest.mock import Mock, patch
from decimal import Decimal

# Add the current directory to Python path so we can import the modules
sys.path.insert(0, '.')

# Mock data for testing
mock_wallet_address = "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"
mock_chat_id = "test-chat-123"
mock_user_id = "user123"

mock_token_metadata = {
    "symbol": "USDC",
    "name": "USD Coin",
    "decimals": 6,
    "address": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
}

mock_vault_info = {
    "address": "2r81MPMDjGSrbmGRwzDg6aqhe3t3vbKcrYfpes5bXckS",
    "name": "Test Vault",
    "apy": 15.5
}

class TestIsTokenSupported:
    """Test suite for is_token_supported function"""
    
    def setup_method(self):
        """Setup method that runs before each test"""
        from agents.drift.drift_functions import is_token_supported
        self.is_token_supported = is_token_supported
    
    def test_supported_token_by_symbol(self):
        """Test with supported token by symbol"""
        result = self.is_token_supported("USDC")
        assert result == True
    
    def test_supported_token_by_address(self):
        """Test with supported token by address"""
        result = self.is_token_supported("EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v")
        assert result == True
    
    def test_unsupported_token(self):
        """Test with unsupported token"""
        result = self.is_token_supported("BTC")
        assert result == False
    
    def test_case_insensitive(self):
        """Test case insensitive matching"""
        result = self.is_token_supported("usdc")
        assert result == True

class TestGenerateDriftVaultTransaction:
    """Test suite for generate_drift_vault_transaction function"""
    
    def setup_method(self):
        """Setup method that runs before each test"""
        from agents.drift.drift_functions import generate_drift_vault_transaction
        self.generate_drift_vault_transaction = generate_drift_vault_transaction
    
    def test_successful_deposit_with_frontend_quoting(self, monkeypatch):
        """Test successful deposit transaction with frontend quoting"""
        # Mock dependencies
        monkeypatch.setattr('agents.drift.drift_functions.save_agent_thought', lambda **kwargs: None)
        monkeypatch.setattr('agents.drift.drift_functions.save_ui_message', lambda **kwargs: None)
        monkeypatch.setattr('agents.drift.drift_functions.is_token_supported', lambda token: True)
        
        # Test the function
        result = self.generate_drift_vault_transaction(
            chat_id=mock_chat_id,
            mint_address_or_symbol="USDC",
            amount="100.0",
            transaction_type="deposit",
            use_frontend_quoting=True
        )
        
        # Verify the result
        assert "quoting process for the deposit transaction was initiated" in result
    
    def test_deposit_without_amount(self, monkeypatch):
        """Test deposit without amount specified"""
        # Mock dependencies
        monkeypatch.setattr('agents.drift.drift_functions.save_agent_thought', lambda **kwargs: None)
        monkeypatch.setattr('agents.drift.drift_functions.is_token_supported', lambda token: True)
        
        # Test the function
        result = self.generate_drift_vault_transaction(
            chat_id=mock_chat_id,
            mint_address_or_symbol="USDC",
            amount=None,
            transaction_type="deposit",
            use_frontend_quoting=True
        )
        
        # Verify the result
        assert "Please specify the amount you want to deposit" in result
    
    def test_unsupported_token(self, monkeypatch):
        """Test with unsupported token"""
        # Mock dependencies
        monkeypatch.setattr('agents.drift.drift_functions.save_agent_thought', lambda **kwargs: None)
        monkeypatch.setattr('agents.drift.drift_functions.is_token_supported', lambda token: False)
        
        # Test the function
        result = self.generate_drift_vault_transaction(
            chat_id=mock_chat_id,
            mint_address_or_symbol="BTC",
            amount="100.0",
            transaction_type="deposit",
            use_frontend_quoting=True
        )
        
        # Verify the result
        assert "not supported yet on Drift Agent" in result
    
    def test_invalid_transaction_type(self, monkeypatch):
        """Test with invalid transaction type"""
        # Mock dependencies
        monkeypatch.setattr('agents.drift.drift_functions.save_agent_thought', lambda **kwargs: None)
        
        # Test the function
        result = self.generate_drift_vault_transaction(
            chat_id=mock_chat_id,
            mint_address_or_symbol="USDC",
            amount="100.0",
            transaction_type="invalid",
            use_frontend_quoting=True
        )
        
        # Verify the result
        assert "Invalid transaction type" in result
    
    def test_exception_handling(self, monkeypatch):
        """Test exception handling"""
        # Mock dependencies to raise exception
        def mock_save_agent_thought_with_exception(**kwargs):
            if "Initiating" in kwargs.get("thought", ""):
                raise Exception("Test error")
        
        monkeypatch.setattr('agents.drift.drift_functions.save_agent_thought', mock_save_agent_thought_with_exception)
        
        # Test the function
        result = self.generate_drift_vault_transaction(
            chat_id=mock_chat_id,
            mint_address_or_symbol="USDC",
            amount="100.0",
            transaction_type="deposit"
        )
        
        # Verify the result
        assert "Error generating deposit transaction because:" in result

class TestSelectVaultToWithdrawFrom:
    """Test suite for select_vault_to_withdraw_from function"""
    
    def setup_method(self):
        """Setup method that runs before each test"""
        from agents.drift.drift_functions import select_vault_to_withdraw_from
        self.select_vault_to_withdraw_from = select_vault_to_withdraw_from
    
    def test_successful_withdraw_selection_with_frontend_quoting(self, monkeypatch):
        """Test successful vault selection for withdrawal with frontend quoting"""
        # Mock dependencies
        monkeypatch.setattr('agents.drift.drift_functions.save_agent_thought', lambda **kwargs: None)
        monkeypatch.setattr('agents.drift.drift_functions.save_ui_message', lambda **kwargs: None)
        
        # Test the function
        result = self.select_vault_to_withdraw_from(
            chat_id=mock_chat_id,
            transaction_type="withdraw",
            use_frontend_quoting=True
        )
        
        # Verify the result
        assert "Please select the vault you want to withdraw from" in result
    
    def test_successful_request_withdraw_selection(self, monkeypatch):
        """Test successful vault selection for request withdrawal"""
        # Mock dependencies
        monkeypatch.setattr('agents.drift.drift_functions.save_agent_thought', lambda **kwargs: None)
        monkeypatch.setattr('agents.drift.drift_functions.save_ui_message', lambda **kwargs: None)
        
        # Test the function
        result = self.select_vault_to_withdraw_from(
            chat_id=mock_chat_id,
            transaction_type="request_withdraw",
            use_frontend_quoting=True
        )
        
        # Verify the result
        assert "Please select the vault you want to request_withdraw from" in result

class TestSelectVaultToDepositTo:
    """Test suite for select_vault_to_deposit_to function"""
    
    def setup_method(self):
        """Setup method that runs before each test"""
        from agents.drift.drift_functions import select_vault_to_deposit_to
        self.select_vault_to_deposit_to = select_vault_to_deposit_to
    
    def test_successful_deposit_selection_with_frontend_quoting(self, monkeypatch):
        """Test successful vault selection for deposit with frontend quoting"""
        # Mock dependencies
        monkeypatch.setattr('agents.drift.drift_functions.save_agent_thought', lambda **kwargs: None)
        monkeypatch.setattr('agents.drift.drift_functions.save_ui_message', lambda **kwargs: None)
        
        # Test the function
        result = self.select_vault_to_deposit_to(
            chat_id=mock_chat_id,
            use_frontend_quoting=True
        )
        
        # Verify the result
        assert "Please select the vault you want to deposit to" in result

class TestGetUserVaults:
    """Test suite for get_user_vaults function"""
    
    def setup_method(self):
        """Setup method that runs before each test"""
        from agents.drift.drift_functions import get_user_vaults
        self.get_user_vaults = get_user_vaults
    
    def test_successful_get_vaults_with_frontend_quoting(self, monkeypatch):
        """Test successful vault information retrieval with frontend quoting"""
        # Mock dependencies
        monkeypatch.setattr('agents.drift.drift_functions.save_agent_thought', lambda **kwargs: None)
        monkeypatch.setattr('agents.drift.drift_functions.save_ui_message', lambda **kwargs: None)
        
        # Test the function
        result = self.get_user_vaults(
            chat_id=mock_chat_id,
            use_frontend_quoting=True
        )
        
        # Verify the result
        assert "I've initiated the process to fetch your current positions on Drift" in result

class TestCheckIfUserHasDriftAccount:
    """Test suite for check_if_user_has_drift_account function"""
    
    def setup_method(self):
        """Setup method that runs before each test"""
        from agents.drift.drift_functions import check_if_user_has_drift_account
        self.check_if_user_has_drift_account = check_if_user_has_drift_account
    
    def test_successful_account_check(self, monkeypatch):
        """Test successful drift account check"""
        # Mock dependencies
        monkeypatch.setattr('agents.drift.drift_functions.save_agent_thought', lambda **kwargs: None)
        
        # Mock successful HTTP response
        mock_response = Mock()
        mock_response.json.return_value = True
        mock_response.raise_for_status.return_value = None
        
        with patch('agents.drift.drift_functions.requests.get', return_value=mock_response):
            result = self.check_if_user_has_drift_account(
                chat_id=mock_chat_id,
                solana_wallet_address=mock_wallet_address
            )
        
        # Verify the result
        assert result == True
    
    def test_account_check_exception_handling(self, monkeypatch):
        """Test account check with exception handling"""
        # Mock dependencies
        monkeypatch.setattr('agents.drift.drift_functions.save_agent_thought', lambda **kwargs: None)
        
        # Mock HTTP request to raise an error
        with patch('agents.drift.drift_functions.requests.get', side_effect=Exception("Network error")):
            result = self.check_if_user_has_drift_account(
                chat_id=mock_chat_id,
                solana_wallet_address=mock_wallet_address
            )
        
        # Verify the result
        assert "Error checking if user has drift account because:" in result

class TestCreateDriftAccount:
    """Test suite for create_drift_account function"""
    
    def setup_method(self):
        """Setup method that runs before each test"""
        from agents.drift.drift_functions import create_drift_account
        self.create_drift_account = create_drift_account
    
    def test_successful_account_creation_with_frontend_quoting(self, monkeypatch):
        """Test successful drift account creation with frontend quoting"""
        # Mock dependencies
        monkeypatch.setattr('agents.drift.drift_functions.get_request_ctx', 
                            lambda *args, **kwargs: mock_wallet_address)
        monkeypatch.setattr('agents.drift.drift_functions.save_agent_thought', lambda **kwargs: None)
        monkeypatch.setattr('agents.drift.drift_functions.save_ui_message', lambda **kwargs: None)
        monkeypatch.setattr('agents.drift.drift_functions.tokens_service.get_token_metadata', 
                            lambda **kwargs: mock_token_metadata)
        monkeypatch.setattr('agents.drift.drift_functions.get_token_price_from_provider', 
                            lambda *args, **kwargs: {"price": "1.0"})
        
        # Test the function
        result = self.create_drift_account(
            chat_id=mock_chat_id,
            token_symbol="USDC",
            amount="10.0",
            use_frontend_quoting=True,
            already_checked_account_created=True
        )
        
        # Verify the result
        assert "I've initiated the process to create a new drift account" in result
    
    def test_account_creation_without_wallet(self, monkeypatch):
        """Test account creation without wallet address"""
        # Mock dependencies
        monkeypatch.setattr('agents.drift.drift_functions.get_request_ctx', 
                            lambda *args, **kwargs: None)
        
        # Test the function
        result = self.create_drift_account(
            chat_id=mock_chat_id,
            token_symbol="USDC",
            amount="10.0"
        )
        
        # Verify the result
        assert "No wallet address found" in result
    
    def test_unsupported_collateral_token(self, monkeypatch):
        """Test with unsupported collateral token"""
        # Mock dependencies
        monkeypatch.setattr('agents.drift.drift_functions.get_request_ctx', 
                            lambda *args, **kwargs: mock_wallet_address)
        monkeypatch.setattr('agents.drift.drift_functions.save_agent_thought', lambda **kwargs: None)
        
        # Test the function
        result = self.create_drift_account(
            chat_id=mock_chat_id,
            token_symbol="BTC",  # Not in DRIFT_PERPS_COLLATERAL_TOKENS
            amount="10.0",
            already_checked_account_created=True
        )
        
        # Verify the result
        assert "not supported as collateral" in result

class TestDepositOrWithdrawCollateral:
    """Test suite for deposit_or_withdraw_collateral function"""
    
    def setup_method(self):
        """Setup method that runs before each test"""
        from agents.drift.drift_functions import deposit_or_withdraw_collateral
        self.deposit_or_withdraw_collateral = deposit_or_withdraw_collateral
    
    def test_successful_deposit_collateral_with_frontend_quoting(self, monkeypatch):
        """Test successful collateral deposit with frontend quoting"""
        # Mock dependencies
        monkeypatch.setattr('agents.drift.drift_functions.get_request_ctx', 
                            lambda *args, **kwargs: mock_wallet_address)
        monkeypatch.setattr('agents.drift.drift_functions.save_agent_thought', lambda **kwargs: None)
        monkeypatch.setattr('agents.drift.drift_functions.save_ui_message', lambda **kwargs: None)
        monkeypatch.setattr('agents.drift.drift_functions.check_if_user_has_drift_account', 
                            lambda **kwargs: True)
        
        # Test the function
        result = self.deposit_or_withdraw_collateral(
            token_symbol="USDC",
            amount="100.0",
            chat_id=mock_chat_id,
            transaction_type="deposit",
            use_frontend_quoting=True
        )
        
        # Verify the result
        assert "I've initiated the process to deposit 100.0 USDC as collateral" in result
    
    def test_withdraw_without_drift_account(self, monkeypatch):
        """Test withdrawal without drift account"""
        # Mock dependencies
        monkeypatch.setattr('agents.drift.drift_functions.get_request_ctx', 
                            lambda *args, **kwargs: mock_wallet_address)
        monkeypatch.setattr('agents.drift.drift_functions.save_agent_thought', lambda **kwargs: None)
        monkeypatch.setattr('agents.drift.drift_functions.check_if_user_has_drift_account', 
                            lambda **kwargs: False)
        
        # Test the function
        result = self.deposit_or_withdraw_collateral(
            token_symbol="USDC",
            amount="100.0",
            chat_id=mock_chat_id,
            transaction_type="withdraw",
            use_frontend_quoting=True
        )
        
        # Verify the result
        assert "You don't have a drift account" in result
    
    def test_invalid_transaction_type(self, monkeypatch):
        """Test with invalid transaction type"""
        # Mock dependencies
        monkeypatch.setattr('agents.drift.drift_functions.get_request_ctx', 
                            lambda *args, **kwargs: mock_wallet_address)
        monkeypatch.setattr('agents.drift.drift_functions.save_agent_thought', lambda **kwargs: None)
        monkeypatch.setattr('agents.drift.drift_functions.check_if_user_has_drift_account', 
                            lambda **kwargs: True)
        
        # Test the function
        result = self.deposit_or_withdraw_collateral(
            token_symbol="USDC",
            amount="100.0",
            chat_id=mock_chat_id,
            transaction_type="invalid",
            use_frontend_quoting=True
        )
        
        # Verify the result
        assert "Invalid transaction type" in result

class TestGetDriftPerpsAccountInfo:
    """Test suite for get_drift_perps_account_info function"""
    
    def setup_method(self):
        """Setup method that runs before each test"""
        from agents.drift.drift_functions import get_drift_perps_account_info
        self.get_drift_perps_account_info = get_drift_perps_account_info
    
    def test_successful_account_info_with_frontend_quoting(self, monkeypatch):
        """Test successful account info retrieval with frontend quoting"""
        # Mock dependencies
        monkeypatch.setattr('agents.drift.drift_functions.get_request_ctx', 
                            lambda *args, **kwargs: mock_wallet_address)
        monkeypatch.setattr('agents.drift.drift_functions.save_agent_thought', lambda **kwargs: None)
        monkeypatch.setattr('agents.drift.drift_functions.save_ui_message', lambda **kwargs: None)
        monkeypatch.setattr('agents.drift.drift_functions.check_if_user_has_drift_account', 
                            lambda **kwargs: True)
        
        # Test the function
        result = self.get_drift_perps_account_info(
            chat_id=mock_chat_id,
            use_frontend_quoting=True
        )
        
        # Verify the result
        assert "I've initiated the process to fetch your account information" in result
    
    def test_account_info_without_drift_account(self, monkeypatch):
        """Test account info retrieval without drift account"""
        # Mock dependencies
        monkeypatch.setattr('agents.drift.drift_functions.get_request_ctx', 
                            lambda *args, **kwargs: mock_wallet_address)
        monkeypatch.setattr('agents.drift.drift_functions.save_agent_thought', lambda **kwargs: None)
        monkeypatch.setattr('agents.drift.drift_functions.check_if_user_has_drift_account', 
                            lambda **kwargs: False)
        
        # Test the function
        result = self.get_drift_perps_account_info(
            chat_id=mock_chat_id,
            use_frontend_quoting=True
        )
        
        # Verify the result
        assert "You don't have a drift account" in result

class TestOpenPerpsPosition:
    """Test suite for open_perps_position function"""
    
    def setup_method(self):
        """Setup method that runs before each test"""
        from agents.drift.drift_functions import open_perps_position, ORDER_TYPE, POSITION_TYPE
        self.open_perps_position = open_perps_position
        self.ORDER_TYPE = ORDER_TYPE
        self.POSITION_TYPE = POSITION_TYPE
    
    def test_successful_open_position_with_frontend_quoting(self, monkeypatch):
        """Test successful perps position opening with frontend quoting"""
        # Mock dependencies
        monkeypatch.setattr('agents.drift.drift_functions.get_request_ctx', 
                            lambda *args, **kwargs: mock_wallet_address)
        monkeypatch.setattr('agents.drift.drift_functions.save_agent_thought', lambda **kwargs: None)
        monkeypatch.setattr('agents.drift.drift_functions.save_ui_message', lambda **kwargs: None)
        monkeypatch.setattr('agents.drift.drift_functions.check_if_user_has_drift_account', 
                            lambda **kwargs: True)
        monkeypatch.setattr('agents.drift.drift_functions.is_valid_market_symbol', 
                            lambda symbol: {"is_valid_market": True, "perp_markets": ["SOL", "BTC"]})
        
        # Test the function
        result = self.open_perps_position(
            symbol="SOL",
            amount="100.0",
            order_type=self.ORDER_TYPE.MARKET,
            chat_id=mock_chat_id,
            trade_direction=self.POSITION_TYPE.LONG,
            use_frontend_quoting=True
        )
        
        # Verify the result
        assert "I've initiated the process to open a new position on SOL" in result
    
    def test_open_position_without_drift_account(self, monkeypatch):
        """Test opening position without drift account"""
        # Mock dependencies
        monkeypatch.setattr('agents.drift.drift_functions.get_request_ctx', 
                            lambda *args, **kwargs: mock_wallet_address)
        monkeypatch.setattr('agents.drift.drift_functions.save_agent_thought', lambda **kwargs: None)
        monkeypatch.setattr('agents.drift.drift_functions.check_if_user_has_drift_account', 
                            lambda **kwargs: False)
        
        # Test the function
        result = self.open_perps_position(
            symbol="SOL",
            amount="100.0",
            order_type=self.ORDER_TYPE.MARKET,
            chat_id=mock_chat_id,
            trade_direction=self.POSITION_TYPE.LONG,
            use_frontend_quoting=True
        )
        
        # Verify the result
        assert "You don't have a drift account" in result
    
    def test_open_position_invalid_market(self, monkeypatch):
        """Test opening position with invalid market"""
        # Mock dependencies
        monkeypatch.setattr('agents.drift.drift_functions.get_request_ctx', 
                            lambda *args, **kwargs: mock_wallet_address)
        monkeypatch.setattr('agents.drift.drift_functions.save_agent_thought', lambda **kwargs: None)
        monkeypatch.setattr('agents.drift.drift_functions.check_if_user_has_drift_account', 
                            lambda **kwargs: True)
        monkeypatch.setattr('agents.drift.drift_functions.is_valid_market_symbol', 
                            lambda symbol: {"is_valid_market": False, "perp_markets": ["SOL", "BTC"]})
        
        # Test the function
        result = self.open_perps_position(
            symbol="INVALID",
            amount="100.0",
            order_type=self.ORDER_TYPE.MARKET,
            chat_id=mock_chat_id,
            trade_direction=self.POSITION_TYPE.LONG,
            use_frontend_quoting=True
        )
        
        # Verify the result
        assert "Market INVALID not found" in result

class TestGetUserActiveOrders:
    """Test suite for get_user_active_orders function"""
    
    def setup_method(self):
        """Setup method that runs before each test"""
        from agents.drift.drift_functions import get_user_active_orders
        self.get_user_active_orders = get_user_active_orders
    
    def test_successful_get_active_orders_with_frontend_quoting(self, monkeypatch):
        """Test successful active orders retrieval with frontend quoting"""
        # Mock dependencies
        monkeypatch.setattr('agents.drift.drift_functions.get_request_ctx', 
                            lambda *args, **kwargs: mock_wallet_address)
        monkeypatch.setattr('agents.drift.drift_functions.save_agent_thought', lambda **kwargs: None)
        monkeypatch.setattr('agents.drift.drift_functions.save_ui_message', lambda **kwargs: None)
        monkeypatch.setattr('agents.drift.drift_functions.check_if_user_has_drift_account', 
                            lambda **kwargs: True)
        
        # Test the function
        result = self.get_user_active_orders(
            chat_id=mock_chat_id,
            use_frontend_quoting=True
        )
        
        # Verify the result
        assert "I've initiated the process to get your active orders" in result
    
    def test_get_active_orders_without_drift_account(self, monkeypatch):
        """Test getting active orders without drift account"""
        # Mock dependencies
        monkeypatch.setattr('agents.drift.drift_functions.get_request_ctx', 
                            lambda *args, **kwargs: mock_wallet_address)
        monkeypatch.setattr('agents.drift.drift_functions.save_agent_thought', lambda **kwargs: None)
        monkeypatch.setattr('agents.drift.drift_functions.check_if_user_has_drift_account', 
                            lambda **kwargs: False)
        
        # Test the function
        result = self.get_user_active_orders(
            chat_id=mock_chat_id,
            use_frontend_quoting=True
        )
        
        # Verify the result
        assert "You don't have any active orders on Drift Perps" in result

class TestGetUserActivePositions:
    """Test suite for get_user_active_positions function"""
    
    def setup_method(self):
        """Setup method that runs before each test"""
        from agents.drift.drift_functions import get_user_active_positions
        self.get_user_active_positions = get_user_active_positions
    
    def test_successful_get_active_positions_with_frontend_quoting(self, monkeypatch):
        """Test successful active positions retrieval with frontend quoting"""
        # Mock dependencies
        monkeypatch.setattr('agents.drift.drift_functions.get_request_ctx', 
                            lambda *args, **kwargs: mock_wallet_address)
        monkeypatch.setattr('agents.drift.drift_functions.save_agent_thought', lambda **kwargs: None)
        monkeypatch.setattr('agents.drift.drift_functions.save_ui_message', lambda **kwargs: None)
        monkeypatch.setattr('agents.drift.drift_functions.check_if_user_has_drift_account', 
                            lambda **kwargs: True)
        
        # Test the function
        result = self.get_user_active_positions(
            chat_id=mock_chat_id,
            use_frontend_quoting=True
        )
        
        # Verify the result
        assert "I've initiated the process to get your active positions" in result

class TestGetPerpsMarkets:
    """Test suite for get_perps_markets function"""
    
    def setup_method(self):
        """Setup method that runs before each test"""
        from agents.drift.drift_functions import get_perps_markets
        self.get_perps_markets = get_perps_markets
    
    def test_successful_get_perps_markets_with_frontend_quoting(self, monkeypatch):
        """Test successful perps markets retrieval with frontend quoting"""
        # Mock dependencies
        monkeypatch.setattr('agents.drift.drift_functions.save_agent_thought', lambda **kwargs: None)
        
        # Mock successful HTTP response
        mock_response = Mock()
        mock_response.json.return_value = ["SOL", "BTC", "ETH", "JUP"]
        mock_response.raise_for_status.return_value = None
        
        with patch('agents.drift.drift_functions.requests.get', return_value=mock_response):
            result = self.get_perps_markets(
                chat_id=mock_chat_id,
                use_frontend_quoting=True
            )
        
        # Verify the result
        assert "Here is a list of the available perps markets on Drift Perps" in result
        assert "SOL, BTC, ETH, JUP" in result
    
    def test_get_perps_markets_exception_handling(self, monkeypatch):
        """Test perps markets retrieval with exception handling"""
        # Mock dependencies
        monkeypatch.setattr('agents.drift.drift_functions.save_agent_thought', lambda **kwargs: None)
        
        # Mock HTTP request to raise an error
        with patch('agents.drift.drift_functions.requests.get', side_effect=Exception("Network error")):
            result = self.get_perps_markets(
                chat_id=mock_chat_id,
                use_frontend_quoting=True
            )
        
        # Verify the result
        assert "Error getting perps markets because:" in result
