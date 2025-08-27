# tests/agents/dex_agent/test_lifi_functions.py
import types
import sys
import os
from unittest.mock import Mock, patch

# Add the current directory to Python path so we can import the modules
sys.path.insert(0, '.')

# Mock data for testing
mock_from_token_info = {
    "symbol": "USDC",
    "name": "USD Coin",
    "decimals": 6,
    "icon_url": "https://raw.githubusercontent.com/trustwallet/assets/master/blockchains/ethereum/assets/0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48/logo.png",
    "logoURI": "https://raw.githubusercontent.com/trustwallet/assets/master/blockchains/ethereum/assets/0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48/logo.png",
    "address": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    "contract_address": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    "chain_name": "ETHEREUM",
    "chain": "ETHEREUM",
    "chain_id": "xQ9PyOHIDlzm2jgUjLoL",
    "protocols": [
      "vTCOPcMINJFUdzil3uiN",
      "GUNIfbSOvIW3V1zueIFv"
    ]
  }

mock_to_token_info = {
    "symbol": "USDT",
    "name": "USDT",
    "decimals": 6,
    "icon_url": "https://raw.githubusercontent.com/trustwallet/assets/master/blockchains/ethereum/assets/0xdAC17F958D2ee523a2206206994597C13D831ec7/logo.png",
    "logoURI": "https://raw.githubusercontent.com/trustwallet/assets/master/blockchains/ethereum/assets/0xdAC17F958D2ee523a2206206994597C13D831ec7/logo.png",
    "address": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
    "contract_address": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
    "chain_name": "ETHEREUM",
    "chain": "ETHEREUM",
    "chain_id": "xQ9PyOHIDlzm2jgUjLoL",
    "protocols": [
      "vTCOPcMINJFUdzil3uiN",
      "GUNIfbSOvIW3V1zueIFv"
    ]
  }

mock_solana_token_info = {
    "symbol": "SOL",
    "name": "SOL",
    "decimals": 9,
    "icon_url": "https://raw.githubusercontent.com/solana-labs/token-list/main/assets/mainnet/So11111111111111111111111111111111111111112/logo.png",
    "logoURI": "https://raw.githubusercontent.com/solana-labs/token-list/main/assets/mainnet/So11111111111111111111111111111111111111112/logo.png",
    "address": "So11111111111111111111111111111111111111112",
    "contract_address": "So11111111111111111111111111111111111111112",
    "chain_name": "SOLANA",
    "chain": "SOLANA",
    "chain_id": "SOL",
    "protocols": [
      "QyCXFIaha8TnSyY1BfCn"
    ],
    "verified": True
  }

mock_evm_wallet_address = "0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6"
mock_solana_wallet_address = "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"
mock_user_id = "user123"

class TestLifiGetQuote:
    """Comprehensive test suite for lifi_get_quote function"""
    
    def setup_method(self):
        """Setup method that runs before each test"""
        # Import the function once for all tests
        from agents.dex_agent.lifi_functions import lifi_get_quote
        self.lifi_get_quote = lifi_get_quote
    
    def test_successful_swap_with_frontend_quoting(self, monkeypatch):
        """Test successful swap (same chain) with frontend quoting enabled"""
        # Mock dependencies
        monkeypatch.setattr('agents.dex_agent.lifi_functions.tokens_service.get_token_metadata',
                            lambda chain, token: mock_from_token_info if token == "USDC" else mock_to_token_info)
        
        monkeypatch.setattr('agents.dex_agent.lifi_functions.get_request_ctx',
                            lambda parentKey, key: mock_evm_wallet_address if key == "evm_wallet_address" else 
                                                 mock_solana_wallet_address if key == "solana_wallet_address" else
                                                 "0.5" if key == "slippage" else "1" if key == "allowance" else mock_user_id)
        
        monkeypatch.setattr('agents.dex_agent.lifi_functions.save_agent_thought', lambda **kwargs: None)
        monkeypatch.setattr('agents.dex_agent.lifi_functions.save_ui_message', lambda **kwargs: None)
        
        # Test the function
        result = self.lifi_get_quote(
            from_chain="ETHEREUM",
            to_chain="ETHEREUM",
            from_token_symbol="USDC",
            to_token_symbol="USDT",
            from_amount="100",
            is_usd=False,
            chat_id="test-chat-123",
            use_frontend_quoting=True
        )
        
        # Verify the result
        assert "I've initiated the quoting proccess for your exchange transaction" in result
        assert "USDC" in result
        assert "USDT" in result
        assert "ETHEREUM" in result
    
    def test_successful_bridge_with_frontend_quoting(self, monkeypatch):
        """Test successful bridge (cross-chain) with frontend quoting enabled"""
        # Mock dependencies
        monkeypatch.setattr('agents.dex_agent.lifi_functions.tokens_service.get_token_metadata',
                            lambda chain, token: mock_from_token_info if token == "USDC" else mock_solana_token_info)
        
        monkeypatch.setattr('agents.dex_agent.lifi_functions.get_request_ctx',
                            lambda parentKey, key: mock_evm_wallet_address if key == "evm_wallet_address" else 
                                                 mock_solana_wallet_address if key == "solana_wallet_address" else
                                                 "0.5" if key == "slippage" else "1" if key == "allowance" else mock_user_id)
        
        monkeypatch.setattr('agents.dex_agent.lifi_functions.save_agent_thought', lambda **kwargs: None)
        monkeypatch.setattr('agents.dex_agent.lifi_functions.save_ui_message', lambda **kwargs: None)
        
        # Test the function
        result = self.lifi_get_quote(
            from_chain="ETHEREUM",
            to_chain="SOLANA",
            from_token_symbol="USDC",
            to_token_symbol="SOL",
            from_amount="100",
            is_usd=False,
            chat_id="test-chat-123",
            use_frontend_quoting=True
        )
        
        # Verify the result
        assert "I've initiated the quoting proccess for your exchange transaction" in result
        assert "USDC" in result
        assert "SOL" in result
        assert "ETHEREUM" in result
        assert "SOLANA" in result
    
    def test_solana_to_evm_bridge(self, monkeypatch):
        """Test bridge from Solana to EVM chain"""
        # Mock dependencies
        monkeypatch.setattr('agents.dex_agent.lifi_functions.tokens_service.get_token_metadata',
                            lambda chain, token: mock_solana_token_info if token == "SOL" else mock_from_token_info)
        
        monkeypatch.setattr('agents.dex_agent.lifi_functions.get_request_ctx',
                            lambda parentKey, key: mock_evm_wallet_address if key == "evm_wallet_address" else 
                                                 mock_solana_wallet_address if key == "solana_wallet_address" else
                                                 "0.5" if key == "slippage" else "1" if key == "allowance" else mock_user_id)
        
        monkeypatch.setattr('agents.dex_agent.lifi_functions.save_agent_thought', lambda **kwargs: None)
        monkeypatch.setattr('agents.dex_agent.lifi_functions.save_ui_message', lambda **kwargs: None)
        
        # Test the function
        result = self.lifi_get_quote(
            from_chain="SOLANA",
            to_chain="ETHEREUM",
            from_token_symbol="SOL",
            to_token_symbol="USDC",
            from_amount="0.01",
            is_usd=False,
            chat_id="test-chat-123",
            use_frontend_quoting=True
        )
        
        # Verify the result
        assert "I've initiated the quoting proccess for your exchange transaction" in result
        assert "SOL" in result
        assert "USDC" in result
        assert "SOLANA" in result
        assert "ETHEREUM" in result
    
    def test_zero_amount(self, monkeypatch):
        """Test with zero amount"""
        # Mock dependencies
        monkeypatch.setattr('agents.dex_agent.lifi_functions.tokens_service.get_token_metadata',
                            lambda chain, token: mock_from_token_info if token == "USDC" else mock_to_token_info)
        
        monkeypatch.setattr('agents.dex_agent.lifi_functions.get_request_ctx',
                            lambda parentKey, key: mock_evm_wallet_address if key == "evm_wallet_address" else 
                                                 mock_solana_wallet_address if key == "solana_wallet_address" else
                                                 "0.5" if key == "slippage" else "1" if key == "allowance" else mock_user_id)
        
        monkeypatch.setattr('agents.dex_agent.lifi_functions.save_agent_thought', lambda **kwargs: None)
        
        # Test the function
        result = self.lifi_get_quote(
            from_chain="ETHEREUM",
            to_chain="ETHEREUM",
            from_token_symbol="USDC",
            to_token_symbol="USDT",
            from_amount="0",
            is_usd=False,
            chat_id="test-chat-123"
        )
        
        # Verify the result
        assert "Please specify the amount you want to bridge or swap" in result
    
    def test_none_amount(self, monkeypatch):
        """Test with None amount"""
        # Mock dependencies
        monkeypatch.setattr('agents.dex_agent.lifi_functions.tokens_service.get_token_metadata',
                            lambda chain, token: mock_from_token_info if token == "USDC" else mock_to_token_info)
        
        monkeypatch.setattr('agents.dex_agent.lifi_functions.get_request_ctx',
                            lambda parentKey, key: mock_evm_wallet_address if key == "evm_wallet_address" else 
                                                 mock_solana_wallet_address if key == "solana_wallet_address" else
                                                 "0.5" if key == "slippage" else "1" if key == "allowance" else mock_user_id)
        
        monkeypatch.setattr('agents.dex_agent.lifi_functions.save_agent_thought', lambda **kwargs: None)
        
        # Test the function
        result = self.lifi_get_quote(
            from_chain="ETHEREUM",
            to_chain="ETHEREUM",
            from_token_symbol="USDC",
            to_token_symbol="USDT",
            from_amount=None,
            is_usd=False,
            chat_id="test-chat-123"
        )
        
        # Verify the result
        assert "Please specify the amount you want to bridge or swap" in result
    
    def test_empty_amount(self, monkeypatch):
        """Test with empty string amount"""
        # Mock dependencies
        monkeypatch.setattr('agents.dex_agent.lifi_functions.tokens_service.get_token_metadata',
                            lambda chain, token: mock_from_token_info if token == "USDC" else mock_to_token_info)
        
        monkeypatch.setattr('agents.dex_agent.lifi_functions.get_request_ctx',
                            lambda parentKey, key: mock_evm_wallet_address if key == "evm_wallet_address" else 
                                                 mock_solana_wallet_address if key == "solana_wallet_address" else
                                                 "0.5" if key == "slippage" else "1" if key == "allowance" else mock_user_id)
        
        monkeypatch.setattr('agents.dex_agent.lifi_functions.save_agent_thought', lambda **kwargs: None)
        
        # Test the function
        result = self.lifi_get_quote(
            from_chain="ETHEREUM",
            to_chain="ETHEREUM",
            from_token_symbol="USDC",
            to_token_symbol="USDT",
            from_amount="",
            is_usd=False,
            chat_id="test-chat-123"
        )
        
        # Verify the result
        assert "Please specify the amount you want to bridge or swap" in result
    
    def test_invalid_input_token(self, monkeypatch):
        """Test with invalid input token"""
        # Mock dependencies - return None for invalid token
        monkeypatch.setattr('agents.dex_agent.lifi_functions.tokens_service.get_token_metadata',
                            lambda chain, token: None if token == "INVALID" else mock_from_token_info)
        
        monkeypatch.setattr('agents.dex_agent.lifi_functions.get_request_ctx',
                            lambda parentKey, key: mock_evm_wallet_address if key == "evm_wallet_address" else 
                                                 mock_solana_wallet_address if key == "solana_wallet_address" else
                                                 "0.5" if key == "slippage" else "1" if key == "allowance" else mock_user_id)
        
        monkeypatch.setattr('agents.dex_agent.lifi_functions.save_agent_thought', lambda **kwargs: None)
        
        # Test the function
        result = self.lifi_get_quote(
            from_chain="ETHEREUM",
            to_chain="ETHEREUM",
            from_token_symbol="INVALID",
            to_token_symbol="USDT",
            from_amount="100",
            is_usd=False,
            chat_id="test-chat-123"
        )
        
        # Verify the result
        assert "The input token INVALID on ETHEREUM is not supported" in result
        assert "Try again with a different token" in result
    
    def test_invalid_output_token(self, monkeypatch):
        """Test with invalid output token"""
        # Mock dependencies - return None for invalid token
        monkeypatch.setattr('agents.dex_agent.lifi_functions.tokens_service.get_token_metadata',
                            lambda chain, token: None if token == "INVALID" else mock_to_token_info)
        
        monkeypatch.setattr('agents.dex_agent.lifi_functions.get_request_ctx',
                            lambda parentKey, key: mock_evm_wallet_address if key == "evm_wallet_address" else 
                                                 mock_solana_wallet_address if key == "solana_wallet_address" else
                                                 "0.5" if key == "slippage" else "1" if key == "allowance" else mock_user_id)
        
        monkeypatch.setattr('agents.dex_agent.lifi_functions.save_agent_thought', lambda **kwargs: None)
        
        # Test the function
        result = self.lifi_get_quote(
            from_chain="ETHEREUM",
            to_chain="ETHEREUM",
            from_token_symbol="USDC",
            to_token_symbol="INVALID",
            from_amount="100",
            is_usd=False,
            chat_id="test-chat-123"
        )
        
        # Verify the result
        assert "The output token INVALID on ETHEREUM is not supported" in result
        assert "Try again with a different token" in result
    
    def test_unsupported_chain(self, monkeypatch):
        """Test with unsupported chain"""
        # Mock dependencies
        monkeypatch.setattr('agents.dex_agent.lifi_functions.tokens_service.get_token_metadata',
                            lambda chain, token: mock_from_token_info if token == "USDC" else mock_to_token_info)
        
        monkeypatch.setattr('agents.dex_agent.lifi_functions.get_request_ctx',
                            lambda parentKey, key: mock_evm_wallet_address if key == "evm_wallet_address" else 
                                                 mock_solana_wallet_address if key == "solana_wallet_address" else
                                                 "0.5" if key == "slippage" else "1" if key == "allowance" else mock_user_id)
        
        monkeypatch.setattr('agents.dex_agent.lifi_functions.save_agent_thought', lambda **kwargs: None)
        
        # Test the function with unsupported chain
        result = self.lifi_get_quote(
            from_chain="UNSUPPORTED_CHAIN",
            to_chain="ETHEREUM",
            from_token_symbol="USDC",
            to_token_symbol="USDT",
            from_amount="100",
            is_usd=False,
            chat_id="test-chat-123"
        )
        
        # Verify the result
        assert "Chains are not supported for bridging" in result
        assert "Available chains are:" in result
    
    def test_usd_amount_conversion(self, monkeypatch):
        """Test USD amount conversion"""
        # Mock dependencies
        monkeypatch.setattr('agents.dex_agent.lifi_functions.tokens_service.get_token_metadata',
                            lambda chain, token: mock_from_token_info if token == "USDC" else mock_to_token_info)
        
        monkeypatch.setattr('agents.dex_agent.lifi_functions.get_request_ctx',
                            lambda parentKey, key: mock_evm_wallet_address if key == "evm_wallet_address" else 
                                                 mock_solana_wallet_address if key == "solana_wallet_address" else
                                                 "0.5" if key == "slippage" else "1" if key == "allowance" else mock_user_id)
        
        monkeypatch.setattr('agents.dex_agent.lifi_functions.save_agent_thought', lambda **kwargs: None)
        monkeypatch.setattr('agents.dex_agent.lifi_functions.save_ui_message', lambda **kwargs: None)
        
        # Mock the USD conversion function
        mock_conversion = Mock(return_value=0.5)
        monkeypatch.setattr('agents.dex_agent.lifi_functions.get_token_amount_from_usd', mock_conversion)
        
        # Test the function
        result = self.lifi_get_quote(
            from_chain="ETHEREUM",
            to_chain="ETHEREUM",
            from_token_symbol="USDC",
            to_token_symbol="USDT",
            from_amount="1",
            is_usd=True,  # Amount is in USD
            chat_id="test-chat-123",
            use_frontend_quoting=True
        )
        
        # Verify the result
        assert "I've initiated the quoting proccess for your exchange transaction" in result
        
        # Verify USD conversion was called
        mock_conversion.assert_called_once_with(chain="ETHEREUM", token=mock_from_token_info, usd_amount="1")
    
    def test_backend_quoting_success(self, monkeypatch):
        """Test successful backend quoting (not frontend)"""
        # Mock dependencies
        monkeypatch.setattr('agents.dex_agent.lifi_functions.tokens_service.get_token_metadata',
                            lambda chain, token: mock_from_token_info if token == "USDC" else mock_to_token_info)
        
        monkeypatch.setattr('agents.dex_agent.lifi_functions.get_request_ctx',
                            lambda parentKey, key: mock_evm_wallet_address if key == "evm_wallet_address" else 
                                                 mock_solana_wallet_address if key == "solana_wallet_address" else
                                                 "0.5" if key == "slippage" else "1" if key == "allowance" else mock_user_id)
        
        monkeypatch.setattr('agents.dex_agent.lifi_functions.save_agent_thought', lambda **kwargs: None)
        
        # Mock the HTTP request
        mock_response = Mock()
        mock_response.json.return_value = {"quote": "success", "amount": "100"}
        mock_response.status_code = 200
        
        with patch('agents.dex_agent.lifi_functions.requests.post', return_value=mock_response):
            # Test the function
            result = self.lifi_get_quote(
                from_chain="ETHEREUM",
                to_chain="ETHEREUM",
                from_token_symbol="USDC",
                to_token_symbol="USDT",
                from_amount="100",
                is_usd=False,
                chat_id="test-chat-123",
                use_frontend_quoting=False
            )
        
        # Verify the result
        assert result == {"quote": "success", "amount": "100"}
    
    def test_no_wallet_addresses(self, monkeypatch):
        """Test without any wallet addresses for backend quoting"""
        # Mock dependencies
        monkeypatch.setattr('agents.dex_agent.lifi_functions.tokens_service.get_token_metadata',
                            lambda chain, token: mock_from_token_info if token == "USDC" else mock_to_token_info)
        
        monkeypatch.setattr('agents.dex_agent.lifi_functions.get_request_ctx',
                            lambda parentKey, key: None if key in ["evm_wallet_address", "solana_wallet_address"] else
                                                 "0.5" if key == "slippage" else "1" if key == "allowance" else mock_user_id)
        
        monkeypatch.setattr('agents.dex_agent.lifi_functions.save_agent_thought', lambda **kwargs: None)
        
        # Test the function
        result = self.lifi_get_quote(
            from_chain="ETHEREUM",
            to_chain="ETHEREUM",
            from_token_symbol="USDC",
            to_token_symbol="USDT",
            from_amount="100",
            is_usd=False,
            chat_id="test-chat-123",
            use_frontend_quoting=False
        )
        
        # Verify the result
        assert "No wallet address found" in result
    
    def test_general_exception_handling(self, monkeypatch):
        """Test general exception handling"""
        # Mock dependencies to raise an exception during token metadata retrieval
        def mock_get_token_metadata_with_exception(chain, token):
            raise Exception("Database error")
        
        monkeypatch.setattr('agents.dex_agent.lifi_functions.tokens_service.get_token_metadata',
                            mock_get_token_metadata_with_exception)
        
        monkeypatch.setattr('agents.dex_agent.lifi_functions.get_request_ctx',
                            lambda parentKey, key: mock_evm_wallet_address if key == "evm_wallet_address" else 
                                                 mock_solana_wallet_address if key == "solana_wallet_address" else
                                                 "0.5" if key == "slippage" else "1" if key == "allowance" else mock_user_id)
        
        monkeypatch.setattr('agents.dex_agent.lifi_functions.save_agent_thought', lambda **kwargs: None)
        
        # Test the function
        result = self.lifi_get_quote(
            from_chain="ETHEREUM",
            to_chain="ETHEREUM",
            from_token_symbol="USDC",
            to_token_symbol="USDT",
            from_amount="100",
            is_usd=False,
            chat_id="test-chat-123"
        )
        
        # Verify the result
        assert "There was an error building the exchange quote" in result
        assert "Database error" in result
    
    def test_supports_bridge_function(self):
        """Test the supports_bridge helper function"""
        from agents.dex_agent.lifi_functions import supports_bridge
        
        # Test supported chains
        assert supports_bridge("ETHEREUM") == True
        assert supports_bridge("SOLANA") == True
        assert supports_bridge("POLYGON") == True
        assert supports_bridge("BINANCE") == True
        
        # Test unsupported chains
        assert supports_bridge("UNSUPPORTED_CHAIN") == False
        assert supports_bridge("FAKE_CHAIN") == False
        
        # Test case sensitivity
        assert supports_bridge("ethereum") == True
        assert supports_bridge("Ethereum") == True
        assert supports_bridge("ETHEREUM") == True
