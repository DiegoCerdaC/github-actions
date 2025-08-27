# tests/agents/liquidation_agent/test_liquidation_functions.py
import sys
from unittest.mock import Mock, patch, AsyncMock
import pytest

# Add the current directory to Python path so we can import the modules
sys.path.insert(0, '.')


class TestGetLiquidationNativeTokenAmount:
    """Test suite for get_liquidation_native_token_amount function"""
    
    def setup_method(self):
        """Setup method that runs before each test"""
        from agents.liquidation_agent.liquidation_functions import get_liquidation_native_token_amount
        self.get_liquidation_native_token_amount = get_liquidation_native_token_amount
    
    def test_positive_amount(self):
        """Test with positive amount and price"""
        result = self.get_liquidation_native_token_amount(10.0, 100.0)
        expected = 10.0 - (3.0 / 100.0)  # 10 - 0.03 = 9.97
        assert result == expected
    
    def test_zero_amount(self):
        """Test with zero amount"""
        result = self.get_liquidation_native_token_amount(0.0, 100.0)
        expected = 0.0 - (3.0 / 100.0)  # 0 - 0.03 = -0.03
        assert result == expected
    
    def test_decimal_precision(self):
        """Test decimal precision handling"""
        result = self.get_liquidation_native_token_amount(1.23456789, 2.5)
        expected = 1.23456789 - (3.0 / 2.5)  # 1.23456789 - 1.2 = 0.03456789
        assert abs(result - expected) < 1e-10


class TestLiquidateAllAssets:
    """Test suite for liquidate_all_assets function"""
    
    def setup_method(self):
        """Setup method that runs before each test"""
        from agents.liquidation_agent.liquidation_functions import liquidate_all_assets
        self.liquidate_all_assets = liquidate_all_assets
    
    @pytest.mark.asyncio
    async def test_invalid_to_token(self, monkeypatch):
        """Test with invalid to_token"""
        # Mock AVAILABLE_LIQUIDATION_TOKENS
        mock_tokens = ["USDC", "USDT"]
        monkeypatch.setattr('agents.liquidation_agent.liquidation_functions.AVAILABLE_LIQUIDATION_TOKENS', mock_tokens)
        
        # Mock get_request_ctx to return wallet addresses
        def mock_get_request_ctx_side_effect(*args, **kwargs):
            if len(args) > 1:
                key = args[1]
            else:
                key = kwargs.get("key")
            
            if key == "evm_wallet_address":
                return "0x123"
            elif key == "solana_wallet_address":
                return "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"
            elif key == "user_id":
                return "user123"
            else:
                return None
        
        mock_get_request_ctx = Mock(side_effect=mock_get_request_ctx_side_effect)
        monkeypatch.setattr('agents.liquidation_agent.liquidation_functions.get_request_ctx', mock_get_request_ctx)
        
        result = await self.liquidate_all_assets("test-chat", "INVALID_TOKEN")
        
        assert "Please select a valid FIAT token" in result
        assert "USDC, USDT" in result
    
    @pytest.mark.asyncio
    async def test_no_balances_found(self, monkeypatch):
        """Test when no balances are found"""
        # Mock AVAILABLE_LIQUIDATION_TOKENS
        mock_tokens = ["USDC", "USDT"]
        monkeypatch.setattr('agents.liquidation_agent.liquidation_functions.AVAILABLE_LIQUIDATION_TOKENS', mock_tokens)
        
        # Mock get_request_ctx to return wallet addresses
        def mock_get_request_ctx_side_effect(*args, **kwargs):
            if len(args) > 1:
                key = args[1]
            else:
                key = kwargs.get("key")
            
            if key == "evm_wallet_address":
                return "0x123"
            elif key == "solana_wallet_address":
                return "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"
            elif key == "user_id":
                return "user123"
            else:
                return None
        
        mock_get_request_ctx = Mock(side_effect=mock_get_request_ctx_side_effect)
        monkeypatch.setattr('agents.liquidation_agent.liquidation_functions.get_request_ctx', mock_get_request_ctx)
        
        # Mock all balance functions to return empty lists
        mock_get_wallet_balance = Mock(return_value=[])
        mock_get_user_active_positions = Mock(return_value=[])
        mock_get_user_active_orders = Mock(return_value=[])
        
        monkeypatch.setattr('agents.liquidation_agent.liquidation_functions.get_wallet_balance', mock_get_wallet_balance)
        monkeypatch.setattr('agents.liquidation_agent.liquidation_functions.get_user_active_positions', mock_get_user_active_positions)
        monkeypatch.setattr('agents.liquidation_agent.liquidation_functions.get_user_active_orders', mock_get_user_active_orders)
        
        # Mock other dependencies
        monkeypatch.setattr('agents.liquidation_agent.liquidation_functions.set_attributes', Mock())
        monkeypatch.setattr('agents.liquidation_agent.liquidation_functions.save_agent_thought', Mock())
        monkeypatch.setattr('agents.liquidation_agent.liquidation_functions.set_status_ok', Mock())
        
        result = await self.liquidate_all_assets("test-chat", "USDC")
        
        assert result == "No balances found for this wallet address."
    
    @pytest.mark.asyncio
    async def test_successful_liquidation_with_balances(self, monkeypatch):
        """Test successful liquidation with various balance types"""
        # Mock AVAILABLE_LIQUIDATION_TOKENS
        mock_tokens = ["USDC", "USDT"]
        monkeypatch.setattr('agents.liquidation_agent.liquidation_functions.AVAILABLE_LIQUIDATION_TOKENS', mock_tokens)
        
        # Mock get_request_ctx to return wallet addresses
        def mock_get_request_ctx_side_effect(*args, **kwargs):
            if len(args) > 1:
                key = args[1]
            else:
                key = kwargs.get("key")
            
            if key == "evm_wallet_address":
                return "0x123"
            elif key == "solana_wallet_address":
                return "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"
            elif key == "user_id":
                return "user123"
            else:
                return None
        
        mock_get_request_ctx = Mock(side_effect=mock_get_request_ctx_side_effect)
        monkeypatch.setattr('agents.liquidation_agent.liquidation_functions.get_request_ctx', mock_get_request_ctx)
        
        # Mock balance data
        mock_solana_balances = [
            {
                "symbol": "SOL",
                "usd_amount": 50.0,
                "price": 100.0,
                "amount": 0.5,
                "address": "So11111111111111111111111111111111111111112",
                "logo_uri": "sol-logo.png"
            },
            {
                "symbol": "USDC",
                "usd_amount": 10.0,
                "price": 1.0,
                "amount": 10.0,
                "address": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
                "logo_uri": "usdc-logo.png"
            }
        ]
        
        mock_evm_balances = [
            {
                "chain": "ETHEREUM",
                "symbol": "ETH",
                "usd_amount": 2000.0,
                "price": 2000.0,
                "amount": 1.0,
                "address": "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE",
                "logo_uri": "eth-logo.png"
            }
        ]
        
        mock_drift_balances = [
            {
                "price": 100.0,
                "amount": 0.1,
                "market": "SOL-PERP",
                "direction": "long"
            }
        ]
        
        mock_orders = [
            {
                "orderId": "order123",
                "marketName": "SOL-PERP",
                "baseAssetAmount": 0.2,
                "direction": "short"
            }
        ]
        
        # Mock balance functions
        mock_get_wallet_balance = Mock(side_effect=lambda wallet, service_type: 
            mock_solana_balances if service_type == "SOLANA" else mock_evm_balances)
        mock_get_user_active_positions = Mock(return_value=mock_drift_balances)
        mock_get_user_active_orders = Mock(return_value=mock_orders)
        
        monkeypatch.setattr('agents.liquidation_agent.liquidation_functions.get_wallet_balance', mock_get_wallet_balance)
        monkeypatch.setattr('agents.liquidation_agent.liquidation_functions.get_user_active_positions', mock_get_user_active_positions)
        monkeypatch.setattr('agents.liquidation_agent.liquidation_functions.get_user_active_orders', mock_get_user_active_orders)
        
        # Mock NATIVE_TOKEN_ADDRESS
        mock_native_addresses = ["So11111111111111111111111111111111111111112", "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE"]
        monkeypatch.setattr('agents.liquidation_agent.liquidation_functions.NATIVE_TOKEN_ADDRESS', mock_native_addresses)
        
        # Mock other dependencies
        monkeypatch.setattr('agents.liquidation_agent.liquidation_functions.set_attributes', Mock())
        monkeypatch.setattr('agents.liquidation_agent.liquidation_functions.save_agent_thought', Mock())
        monkeypatch.setattr('agents.liquidation_agent.liquidation_functions.save_ui_message', Mock())
        monkeypatch.setattr('agents.liquidation_agent.liquidation_functions.set_status_ok', Mock())
        
        result = await self.liquidate_all_assets("test-chat", "USDC")
        
        assert "You can now select the tokens you want to liquidate" in result
        assert "USDC is the default fiat token" in result
    
    @pytest.mark.asyncio
    async def test_exception_handling(self, monkeypatch):
        """Test exception handling in liquidate_all_assets"""
        # Mock AVAILABLE_LIQUIDATION_TOKENS
        mock_tokens = ["USDC", "USDT"]
        monkeypatch.setattr('agents.liquidation_agent.liquidation_functions.AVAILABLE_LIQUIDATION_TOKENS', mock_tokens)
        
        # Mock get_request_ctx to return wallet addresses
        def mock_get_request_ctx_side_effect(*args, **kwargs):
            if len(args) > 1:
                key = args[1]
            else:
                key = kwargs.get("key")
            
            if key == "evm_wallet_address":
                return "0x123"
            elif key == "solana_wallet_address":
                return "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"
            elif key == "user_id":
                return "user123"
            else:
                return None
        
        mock_get_request_ctx = Mock(side_effect=mock_get_request_ctx_side_effect)
        monkeypatch.setattr('agents.liquidation_agent.liquidation_functions.get_request_ctx', mock_get_request_ctx)
        
        # Mock get_wallet_balance to raise an exception
        mock_get_wallet_balance = Mock(side_effect=Exception("API Error"))
        mock_get_user_active_positions = Mock(return_value=[])
        mock_get_user_active_orders = Mock(return_value=[])
        
        monkeypatch.setattr('agents.liquidation_agent.liquidation_functions.get_wallet_balance', mock_get_wallet_balance)
        monkeypatch.setattr('agents.liquidation_agent.liquidation_functions.get_user_active_positions', mock_get_user_active_positions)
        monkeypatch.setattr('agents.liquidation_agent.liquidation_functions.get_user_active_orders', mock_get_user_active_orders)
        
        # Mock other dependencies
        monkeypatch.setattr('agents.liquidation_agent.liquidation_functions.set_attributes', Mock())
        monkeypatch.setattr('agents.liquidation_agent.liquidation_functions.save_agent_thought', Mock())
        monkeypatch.setattr('agents.liquidation_agent.liquidation_functions.set_status_error', Mock())
        
        result = await self.liquidate_all_assets("test-chat", "USDC")
        
        # The function handles exceptions gracefully and returns "No balances found"
        assert result == "No balances found for this wallet address."
    
    @pytest.mark.asyncio
    async def test_filter_usdc_usdt_tokens(self, monkeypatch):
        """Test that USDC and USDT tokens are filtered out"""
        # Mock AVAILABLE_LIQUIDATION_TOKENS
        mock_tokens = ["USDC", "USDT"]
        monkeypatch.setattr('agents.liquidation_agent.liquidation_functions.AVAILABLE_LIQUIDATION_TOKENS', mock_tokens)
        
        # Mock get_request_ctx to return wallet addresses
        def mock_get_request_ctx_side_effect(*args, **kwargs):
            if len(args) > 1:
                key = args[1]
            else:
                key = kwargs.get("key")
            
            if key == "evm_wallet_address":
                return "0x123"
            elif key == "solana_wallet_address":
                return "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"
            elif key == "user_id":
                return "user123"
            else:
                return None
        
        mock_get_request_ctx = Mock(side_effect=mock_get_request_ctx_side_effect)
        monkeypatch.setattr('agents.liquidation_agent.liquidation_functions.get_request_ctx', mock_get_request_ctx)
        
        # Mock balance data with USDC and USDT that should be filtered out
        mock_solana_balances = [
            {
                "symbol": "SOL",
                "usd_amount": 50.0,
                "price": 100.0,
                "amount": 0.5,
                "address": "So11111111111111111111111111111111111111112",
                "logo_uri": "sol-logo.png"
            },
            {
                "symbol": "USDC",
                "usd_amount": 10.0,
                "price": 1.0,
                "amount": 10.0,
                "address": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
                "logo_uri": "usdc-logo.png"
            }
        ]
        
        # Mock balance functions
        mock_get_wallet_balance = Mock(side_effect=lambda wallet, service_type: 
            mock_solana_balances if service_type == "SOLANA" else [])
        mock_get_user_active_positions = Mock(return_value=[])
        mock_get_user_active_orders = Mock(return_value=[])
        
        monkeypatch.setattr('agents.liquidation_agent.liquidation_functions.get_wallet_balance', mock_get_wallet_balance)
        monkeypatch.setattr('agents.liquidation_agent.liquidation_functions.get_user_active_positions', mock_get_user_active_positions)
        monkeypatch.setattr('agents.liquidation_agent.liquidation_functions.get_user_active_orders', mock_get_user_active_orders)
        
        # Mock NATIVE_TOKEN_ADDRESS
        mock_native_addresses = ["So11111111111111111111111111111111111111112"]
        monkeypatch.setattr('agents.liquidation_agent.liquidation_functions.NATIVE_TOKEN_ADDRESS', mock_native_addresses)
        
        # Mock other dependencies
        monkeypatch.setattr('agents.liquidation_agent.liquidation_functions.set_attributes', Mock())
        monkeypatch.setattr('agents.liquidation_agent.liquidation_functions.save_agent_thought', Mock())
        monkeypatch.setattr('agents.liquidation_agent.liquidation_functions.save_ui_message', Mock())
        monkeypatch.setattr('agents.liquidation_agent.liquidation_functions.set_status_ok', Mock())
        
        result = await self.liquidate_all_assets("test-chat", "USDC")
        
        # Should only include SOL, not USDC
        assert "You can now select the tokens you want to liquidate" in result
    
    @pytest.mark.asyncio
    async def test_filter_low_usd_amounts(self, monkeypatch):
        """Test that balances with USD amount <= 0.1 are filtered out"""
        # Mock AVAILABLE_LIQUIDATION_TOKENS
        mock_tokens = ["USDC", "USDT"]
        monkeypatch.setattr('agents.liquidation_agent.liquidation_functions.AVAILABLE_LIQUIDATION_TOKENS', mock_tokens)
        
        # Mock get_request_ctx to return wallet addresses
        def mock_get_request_ctx_side_effect(*args, **kwargs):
            if len(args) > 1:
                key = args[1]
            else:
                key = kwargs.get("key")
            
            if key == "evm_wallet_address":
                return "0x123"
            elif key == "solana_wallet_address":
                return "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"
            elif key == "user_id":
                return "user123"
            else:
                return None
        
        mock_get_request_ctx = Mock(side_effect=mock_get_request_ctx_side_effect)
        monkeypatch.setattr('agents.liquidation_agent.liquidation_functions.get_request_ctx', mock_get_request_ctx)
        
        # Mock balance data with low USD amounts
        mock_solana_balances = [
            {
                "symbol": "SOL",
                "usd_amount": 0.05,  # Below threshold
                "price": 100.0,
                "amount": 0.0005,
                "address": "So11111111111111111111111111111111111111112",
                "logo_uri": "sol-logo.png"
            },
            {
                "symbol": "SOL",
                "usd_amount": 0.15,  # Above threshold
                "price": 100.0,
                "amount": 0.05,  # Increased amount to ensure positive result after get_liquidation_native_token_amount
                "address": "So11111111111111111111111111111111111111112",
                "logo_uri": "sol-logo.png"
            }
        ]
        
        # Mock balance functions
        mock_get_wallet_balance = Mock(side_effect=lambda wallet, service_type: 
            mock_solana_balances if service_type == "SOLANA" else [])
        mock_get_user_active_positions = Mock(return_value=[])
        mock_get_user_active_orders = Mock(return_value=[])
        
        monkeypatch.setattr('agents.liquidation_agent.liquidation_functions.get_wallet_balance', mock_get_wallet_balance)
        monkeypatch.setattr('agents.liquidation_agent.liquidation_functions.get_user_active_positions', mock_get_user_active_positions)
        monkeypatch.setattr('agents.liquidation_agent.liquidation_functions.get_user_active_orders', mock_get_user_active_orders)
        
        # Mock NATIVE_TOKEN_ADDRESS
        mock_native_addresses = ["So11111111111111111111111111111111111111112"]
        monkeypatch.setattr('agents.liquidation_agent.liquidation_functions.NATIVE_TOKEN_ADDRESS', mock_native_addresses)
        
        # Mock other dependencies
        monkeypatch.setattr('agents.liquidation_agent.liquidation_functions.set_attributes', Mock())
        monkeypatch.setattr('agents.liquidation_agent.liquidation_functions.save_agent_thought', Mock())
        monkeypatch.setattr('agents.liquidation_agent.liquidation_functions.save_ui_message', Mock())
        monkeypatch.setattr('agents.liquidation_agent.liquidation_functions.set_status_ok', Mock())
        
        result = await self.liquidate_all_assets("test-chat", "USDC")
        
        # Should only include the balance above threshold
        assert "You can now select the tokens you want to liquidate" in result
    
    @pytest.mark.asyncio
    async def test_filter_addresses_with_underscores(self, monkeypatch):
        """Test that addresses with underscores are filtered out"""
        # Mock AVAILABLE_LIQUIDATION_TOKENS
        mock_tokens = ["USDC", "USDT"]
        monkeypatch.setattr('agents.liquidation_agent.liquidation_functions.AVAILABLE_LIQUIDATION_TOKENS', mock_tokens)
        
        # Mock get_request_ctx to return wallet addresses
        def mock_get_request_ctx_side_effect(*args, **kwargs):
            if len(args) > 1:
                key = args[1]
            else:
                key = kwargs.get("key")
            
            if key == "evm_wallet_address":
                return "0x123"
            elif key == "solana_wallet_address":
                return "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"
            elif key == "user_id":
                return "user123"
            else:
                return None
        
        mock_get_request_ctx = Mock(side_effect=mock_get_request_ctx_side_effect)
        monkeypatch.setattr('agents.liquidation_agent.liquidation_functions.get_request_ctx', mock_get_request_ctx)
        
        # Mock balance data with addresses containing underscores
        mock_solana_balances = [
            {
                "symbol": "SOL",
                "usd_amount": 50.0,
                "price": 100.0,
                "amount": 0.5,
                "address": "So11111111111111111111111111111111111111112",  # No underscore
                "logo_uri": "sol-logo.png"
            },
            {
                "symbol": "SOL",
                "usd_amount": 50.0,
                "price": 100.0,
                "amount": 0.5,
                "address": "So11111111111111111111111111111111111111112_lulo",  # With underscore
                "logo_uri": "sol-logo.png"
            }
        ]
        
        # Mock balance functions
        mock_get_wallet_balance = Mock(side_effect=lambda wallet, service_type: 
            mock_solana_balances if service_type == "SOLANA" else [])
        mock_get_user_active_positions = Mock(return_value=[])
        mock_get_user_active_orders = Mock(return_value=[])
        
        monkeypatch.setattr('agents.liquidation_agent.liquidation_functions.get_wallet_balance', mock_get_wallet_balance)
        monkeypatch.setattr('agents.liquidation_agent.liquidation_functions.get_user_active_positions', mock_get_user_active_positions)
        monkeypatch.setattr('agents.liquidation_agent.liquidation_functions.get_user_active_orders', mock_get_user_active_orders)
        
        # Mock NATIVE_TOKEN_ADDRESS
        mock_native_addresses = ["So11111111111111111111111111111111111111112"]
        monkeypatch.setattr('agents.liquidation_agent.liquidation_functions.NATIVE_TOKEN_ADDRESS', mock_native_addresses)
        
        # Mock other dependencies
        monkeypatch.setattr('agents.liquidation_agent.liquidation_functions.set_attributes', Mock())
        monkeypatch.setattr('agents.liquidation_agent.liquidation_functions.save_agent_thought', Mock())
        monkeypatch.setattr('agents.liquidation_agent.liquidation_functions.save_ui_message', Mock())
        monkeypatch.setattr('agents.liquidation_agent.liquidation_functions.set_status_ok', Mock())
        
        result = await self.liquidate_all_assets("test-chat", "USDC")
        
        # Should only include the address without underscore
        assert "You can now select the tokens you want to liquidate" in result
    
    @pytest.mark.asyncio
    async def test_filter_matic_on_polygon(self, monkeypatch):
        """Test that MATIC token on POLYGON chain is filtered out"""
        # Mock AVAILABLE_LIQUIDATION_TOKENS
        mock_tokens = ["USDC", "USDT"]
        monkeypatch.setattr('agents.liquidation_agent.liquidation_functions.AVAILABLE_LIQUIDATION_TOKENS', mock_tokens)
        
        # Mock get_request_ctx to return wallet addresses
        def mock_get_request_ctx_side_effect(*args, **kwargs):
            if len(args) > 1:
                key = args[1]
            else:
                key = kwargs.get("key")
            
            if key == "evm_wallet_address":
                return "0x123"
            elif key == "solana_wallet_address":
                return "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"
            elif key == "user_id":
                return "user123"
            else:
                return None
        
        mock_get_request_ctx = Mock(side_effect=mock_get_request_ctx_side_effect)
        monkeypatch.setattr('agents.liquidation_agent.liquidation_functions.get_request_ctx', mock_get_request_ctx)
        
        # Mock balance data with MATIC on POLYGON
        mock_evm_balances = [
            {
                "chain": "POLYGON",
                "symbol": "MATIC",  # Should be filtered out
                "usd_amount": 50.0,
                "price": 1.0,
                "amount": 50.0,
                "address": "0x0000000000000000000000000000000000001010",
                "logo_uri": "matic-logo.png"
            },
            {
                "chain": "POLYGON",
                "symbol": "POL",  # Should be included
                "usd_amount": 50.0,
                "price": 1.0,
                "amount": 50.0,
                "address": "0x0000000000000000000000000000000000001010",
                "logo_uri": "pol-logo.png"
            }
        ]
        
        # Mock balance functions
        mock_get_wallet_balance = Mock(side_effect=lambda wallet, service_type: 
            [] if service_type == "SOLANA" else mock_evm_balances)
        mock_get_user_active_positions = Mock(return_value=[])
        mock_get_user_active_orders = Mock(return_value=[])
        
        monkeypatch.setattr('agents.liquidation_agent.liquidation_functions.get_wallet_balance', mock_get_wallet_balance)
        monkeypatch.setattr('agents.liquidation_agent.liquidation_functions.get_user_active_positions', mock_get_user_active_positions)
        monkeypatch.setattr('agents.liquidation_agent.liquidation_functions.get_user_active_orders', mock_get_user_active_orders)
        
        # Mock NATIVE_TOKEN_ADDRESS
        mock_native_addresses = ["0x0000000000000000000000000000000000001010"]
        monkeypatch.setattr('agents.liquidation_agent.liquidation_functions.NATIVE_TOKEN_ADDRESS', mock_native_addresses)
        
        # Mock other dependencies
        monkeypatch.setattr('agents.liquidation_agent.liquidation_functions.set_attributes', Mock())
        monkeypatch.setattr('agents.liquidation_agent.liquidation_functions.save_agent_thought', Mock())
        monkeypatch.setattr('agents.liquidation_agent.liquidation_functions.save_ui_message', Mock())
        monkeypatch.setattr('agents.liquidation_agent.liquidation_functions.set_status_ok', Mock())
        
        result = await self.liquidate_all_assets("test-chat", "USDC")
        
        # Should only include POL, not MATIC
        assert "You can now select the tokens you want to liquidate" in result
