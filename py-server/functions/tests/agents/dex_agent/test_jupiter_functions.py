# tests/agents/dex_agent/test_dex_functions.py
import types
import sys
import os
from unittest.mock import Mock, patch
import requests

# Add the current directory to Python path so we can import the modules
sys.path.insert(0, '.')

# Mock data for testing
mock_from_token_info = {
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

mock_to_token_info = {
    "symbol": "USDC",
    "name": "USD Coin",
    "decimals": 6,
    "icon_url": "https://raw.githubusercontent.com/trustwallet/assets/master/blockchains/ethereum/assets/0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48/logo.png",
    "logoURI": "https://raw.githubusercontent.com/trustwallet/assets/master/blockchains/ethereum/assets/0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48/logo.png",
    "address": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
    "contract_address": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
    "chain_name": "SOLANA",
    "chain": "SOLANA",
    "chain_id": "vNX8ui5XObaP9Z8A0ZbB",
    "protocols": [
      "vTCOPcMINJFUdzil3uiN",
      "QyCXFIaha8TnSyY1BfCn"
    ],
    "verified": True
  }

mock_wallet_address = "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"
mock_user_id = "user123"

class TestJupiterGetQuotes:
    """Comprehensive test suite for jupiter_get_quotes function"""
    
    def setup_method(self):
        """Setup method that runs before each test"""
        # Import the function once for all tests
        from agents.dex_agent.jupiter_functions import jupiter_get_quotes
        self.jupiter_get_quotes = jupiter_get_quotes
    
    def test_successful_swap_with_frontend_quoting(self, monkeypatch):
        """Test successful swap with frontend quoting enabled"""
        # Mock dependencies
        monkeypatch.setattr('agents.dex_agent.jupiter_functions.tokens_service.get_token_metadata',
                            lambda chain, token: mock_from_token_info if token == "SOL" else mock_to_token_info)
        
        monkeypatch.setattr('agents.dex_agent.jupiter_functions.get_request_ctx',
                            lambda parentKey, key: mock_wallet_address if key == "solana_wallet_address" else mock_user_id)
        
        monkeypatch.setattr('agents.dex_agent.jupiter_functions.save_agent_thought', lambda **kwargs: None)
        monkeypatch.setattr('agents.dex_agent.jupiter_functions.save_ui_message', lambda **kwargs: None)
        
        # Test the function
        result = self.jupiter_get_quotes(
            input_token="SOL",
            output_token="USDC",
            amount=1,
            is_usd=False,
            chat_id="test-chat-123",
            transaction_type="swap",
            use_frontend_quoting=True
        )
        
        # Verify the result
        assert "I've initiated the quoting process for your swap" in result
        assert "swap" in result.lower()
    
    def test_successful_stake_with_frontend_quoting(self, monkeypatch):
        """Test successful stake with frontend quoting enabled"""
        # Mock dependencies
        monkeypatch.setattr('agents.dex_agent.jupiter_functions.tokens_service.get_token_metadata',
                            lambda chain, token: mock_from_token_info if token == "SOL" else mock_to_token_info)
        
        monkeypatch.setattr('agents.dex_agent.jupiter_functions.get_request_ctx',
                            lambda parentKey, key: mock_wallet_address if key == "solana_wallet_address" else mock_user_id)
        
        monkeypatch.setattr('agents.dex_agent.jupiter_functions.save_agent_thought', lambda **kwargs: None)
        monkeypatch.setattr('agents.dex_agent.jupiter_functions.save_ui_message', lambda **kwargs: None)
        
        # Test the function
        result = self.jupiter_get_quotes(
            input_token="SOL",
            output_token="jupSOL",
            amount=0.5,
            is_usd=False,
            chat_id="test-chat-123",
            transaction_type="stake",
            use_frontend_quoting=True
        )
        
        # Verify the result
        assert "I've initiated the quoting process for your stake" in result
        assert "stake" in result.lower()
    
    def test_successful_unstake_with_frontend_quoting(self, monkeypatch):
        """Test successful unstake with frontend quoting enabled"""
        # Mock dependencies
        monkeypatch.setattr('agents.dex_agent.jupiter_functions.tokens_service.get_token_metadata',
                            lambda chain, token: mock_from_token_info if token == "mSOL" else mock_to_token_info)
        
        monkeypatch.setattr('agents.dex_agent.jupiter_functions.get_request_ctx',
                            lambda parentKey, key: mock_wallet_address if key == "solana_wallet_address" else mock_user_id)
        
        monkeypatch.setattr('agents.dex_agent.jupiter_functions.save_agent_thought', lambda **kwargs: None)
        monkeypatch.setattr('agents.dex_agent.jupiter_functions.save_ui_message', lambda **kwargs: None)
        
        # Test the function
        result = self.jupiter_get_quotes(
            input_token="mSOL",
            output_token="SOL",
            amount=0.3,
            is_usd=False,
            chat_id="test-chat-123",
            transaction_type="unstake",
            use_frontend_quoting=True
        )
        
        # Verify the result
        assert "I've initiated the quoting process for your unstake" in result
        assert "unstake" in result.lower()
    
    def test_zero_amount_swap(self, monkeypatch):
        """Test swap with zero amount"""
        # Mock dependencies
        monkeypatch.setattr('agents.dex_agent.jupiter_functions.tokens_service.get_token_metadata',
                            lambda chain, token: mock_from_token_info if token == "SOL" else mock_to_token_info)
        
        monkeypatch.setattr('agents.dex_agent.jupiter_functions.get_request_ctx',
                            lambda parentKey, key: mock_wallet_address if key == "solana_wallet_address" else mock_user_id)
        
        monkeypatch.setattr('agents.dex_agent.jupiter_functions.save_agent_thought', lambda **kwargs: None)
        
        # Test the function
        result = self.jupiter_get_quotes(
            input_token="SOL",
            output_token="USDC",
            amount=0,
            is_usd=False,
            chat_id="test-chat-123",
            transaction_type="swap"
        )
        
        # Verify the result
        assert "Please specify the amount you want to swap" in result
    
    def test_zero_amount_stake(self, monkeypatch):
        """Test stake with zero amount"""
        # Mock dependencies
        monkeypatch.setattr('agents.dex_agent.jupiter_functions.tokens_service.get_token_metadata',
                            lambda chain, token: mock_from_token_info if token == "SOL" else mock_to_token_info)
        
        monkeypatch.setattr('agents.dex_agent.jupiter_functions.get_request_ctx',
                            lambda parentKey, key: mock_wallet_address if key == "solana_wallet_address" else mock_user_id)
        
        monkeypatch.setattr('agents.dex_agent.jupiter_functions.save_agent_thought', lambda **kwargs: None)
        
        # Test the function
        result = self.jupiter_get_quotes(
            input_token="SOL",
            output_token="jupSOL",
            amount=0,
            is_usd=False,
            chat_id="test-chat-123",
            transaction_type="stake"
        )
        
        # Verify the result
        assert "Please specify the amount you want to stake" in result
    
    def test_zero_amount_unstake(self, monkeypatch):
        """Test unstake with zero amount"""
        # Mock dependencies
        monkeypatch.setattr('agents.dex_agent.jupiter_functions.tokens_service.get_token_metadata',
                            lambda chain, token: mock_from_token_info if token == "mSOL" else mock_to_token_info)
        
        monkeypatch.setattr('agents.dex_agent.jupiter_functions.get_request_ctx',
                            lambda parentKey, key: mock_wallet_address if key == "solana_wallet_address" else mock_user_id)
        
        monkeypatch.setattr('agents.dex_agent.jupiter_functions.save_agent_thought', lambda **kwargs: None)
        
        # Test the function
        result = self.jupiter_get_quotes(
            input_token="mSOL",
            output_token="SOL",
            amount=0,
            is_usd=False,
            chat_id="test-chat-123",
            transaction_type="unstake"
        )
        
        # Verify the result
        assert "Please specify the amount you want to unstake" in result
    
    def test_none_amount(self, monkeypatch):
        """Test with None amount"""
        # Mock dependencies
        monkeypatch.setattr('agents.dex_agent.jupiter_functions.tokens_service.get_token_metadata',
                            lambda chain, token: mock_from_token_info if token == "SOL" else mock_to_token_info)
        
        monkeypatch.setattr('agents.dex_agent.jupiter_functions.get_request_ctx',
                            lambda parentKey, key: mock_wallet_address if key == "solana_wallet_address" else mock_user_id)
        
        monkeypatch.setattr('agents.dex_agent.jupiter_functions.save_agent_thought', lambda **kwargs: None)
        
        # Test the function
        result = self.jupiter_get_quotes(
            input_token="SOL",
            output_token="USDC",
            amount=None,
            is_usd=False,
            chat_id="test-chat-123",
            transaction_type="swap"
        )
        
        # Verify the result
        assert "Please specify the amount you want to swap" in result
    
    def test_invalid_input_token(self, monkeypatch):
        """Test with invalid input token"""
        # Mock dependencies - return None for invalid token
        monkeypatch.setattr('agents.dex_agent.jupiter_functions.tokens_service.get_token_metadata',
                            lambda chain, token: None if token == "INVALID" else mock_from_token_info)
        
        monkeypatch.setattr('agents.dex_agent.jupiter_functions.get_request_ctx',
                            lambda parentKey, key: mock_wallet_address if key == "solana_wallet_address" else mock_user_id)
        
        monkeypatch.setattr('agents.dex_agent.jupiter_functions.save_agent_thought', lambda **kwargs: None)
        
        # Test the function
        result = self.jupiter_get_quotes(
            input_token="INVALID",
            output_token="USDC",
            amount=1.0,
            is_usd=False,
            chat_id="test-chat-123",
            transaction_type="swap"
        )
        
        # Verify the result
        assert "The input token INVALID is not supported" in result
        assert "Try again with a different token" in result
    
    def test_invalid_output_token(self, monkeypatch):
        """Test with invalid output token"""
        # Mock dependencies - return None for invalid token
        monkeypatch.setattr('agents.dex_agent.jupiter_functions.tokens_service.get_token_metadata',
                            lambda chain, token: None if token == "INVALID" else mock_to_token_info)
        
        monkeypatch.setattr('agents.dex_agent.jupiter_functions.get_request_ctx',
                            lambda parentKey, key: mock_wallet_address if key == "solana_wallet_address" else mock_user_id)
        
        monkeypatch.setattr('agents.dex_agent.jupiter_functions.save_agent_thought', lambda **kwargs: None)
        
        # Test the function
        result = self.jupiter_get_quotes(
            input_token="SOL",
            output_token="INVALID",
            amount=1.0,
            is_usd=False,
            chat_id="test-chat-123",
            transaction_type="swap"
        )
        
        # Verify the result
        assert "The output token INVALID is not supported" in result
        assert "Try again with a different token" in result
    
    def test_no_wallet_address(self, monkeypatch):
        """Test without wallet address"""
        # Mock dependencies - return None for wallet address
        monkeypatch.setattr('agents.dex_agent.jupiter_functions.tokens_service.get_token_metadata',
                            lambda chain, token: mock_from_token_info if token == "SOL" else mock_to_token_info)
        
        monkeypatch.setattr('agents.dex_agent.jupiter_functions.get_request_ctx',
                            lambda parentKey, key: None if key == "solana_wallet_address" else mock_user_id)
        
        monkeypatch.setattr('agents.dex_agent.jupiter_functions.save_agent_thought', lambda **kwargs: None)
        
        # Test the function
        result = self.jupiter_get_quotes(
            input_token="SOL",
            output_token="USDC",
            amount=1.0,
            is_usd=False,
            chat_id="test-chat-123",
            transaction_type="swap"
        )
        
        # Verify the result
        assert "No Solana wallet address found" in result
    
    def test_usd_amount_conversion(self, monkeypatch):
        """Test USD amount conversion"""
        # Mock dependencies
        monkeypatch.setattr('agents.dex_agent.jupiter_functions.tokens_service.get_token_metadata',
                            lambda chain, token: mock_from_token_info if token == "SOL" else mock_to_token_info)
        
        monkeypatch.setattr('agents.dex_agent.jupiter_functions.get_request_ctx',
                            lambda parentKey, key: mock_wallet_address if key == "solana_wallet_address" else mock_user_id)
        
        monkeypatch.setattr('agents.dex_agent.jupiter_functions.save_agent_thought', lambda **kwargs: None)
        monkeypatch.setattr('agents.dex_agent.jupiter_functions.save_ui_message', lambda **kwargs: None)
        
        # Mock the USD conversion function
        mock_conversion = Mock(return_value=0.005)
        monkeypatch.setattr('agents.dex_agent.jupiter_functions.get_token_amount_from_usd', mock_conversion)
        
        # Test the function
        result = self.jupiter_get_quotes(
            input_token="SOL",
            output_token="USDC",
            amount=1.0,
            is_usd=True,  # Amount is in USD
            chat_id="test-chat-123",
            transaction_type="swap",
            use_frontend_quoting=True
        )
        
        # Verify the result
        assert "I've initiated the quoting process for your swap" in result
        
        # Verify USD conversion was called with named arguments
        mock_conversion.assert_called_once_with(usd_amount=1.0, token_address=mock_from_token_info["contract_address"])
    
    def test_backend_quoting_success(self, monkeypatch):
        """Test successful backend quoting (not frontend)"""
        # Mock dependencies
        monkeypatch.setattr('agents.dex_agent.jupiter_functions.tokens_service.get_token_metadata',
                            lambda chain, token: mock_from_token_info if token == "SOL" else mock_to_token_info)
        
        monkeypatch.setattr('agents.dex_agent.jupiter_functions.get_request_ctx',
                            lambda parentKey, key: mock_wallet_address if key == "solana_wallet_address" else mock_user_id)
        
        monkeypatch.setattr('agents.dex_agent.jupiter_functions.save_agent_thought', lambda **kwargs: None)
        
        # Mock the HTTP request
        mock_response = Mock()
        mock_response.json.return_value = {"quote": "success", "amount": "100"}
        mock_response.raise_for_status.return_value = None
        
        with patch('agents.dex_agent.jupiter_functions.requests.post', return_value=mock_response):
            # Test the function
            result = self.jupiter_get_quotes(
                input_token="SOL",
                output_token="USDC",
                amount=1.0,
                is_usd=False,
                chat_id="test-chat-123",
                transaction_type="swap",
                use_frontend_quoting=False
            )
        
        # Verify the result
        assert result == {"quote": "success", "amount": "100"}
    
    def test_backend_quoting_http_error(self, monkeypatch):
        """Test backend quoting with HTTP error"""
        # Mock dependencies
        monkeypatch.setattr('agents.dex_agent.jupiter_functions.tokens_service.get_token_metadata',
                            lambda chain, token: mock_from_token_info if token == "SOL" else mock_to_token_info)
        
        monkeypatch.setattr('agents.dex_agent.jupiter_functions.get_request_ctx',
                            lambda parentKey, key: mock_wallet_address if key == "solana_wallet_address" else mock_user_id)
        
        monkeypatch.setattr('agents.dex_agent.jupiter_functions.save_agent_thought', lambda **kwargs: None)
        
        # Mock the HTTP request to raise an error
        mock_response = Mock()
        mock_response.content = b"Error message"
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("HTTP Error")
        
        with patch('agents.dex_agent.jupiter_functions.requests.post', return_value=mock_response):
            # Test the function
            result = self.jupiter_get_quotes(
                input_token="SOL",
                output_token="USDC",
                amount=1.0,
                is_usd=False,
                chat_id="test-chat-123",
                transaction_type="swap",
                use_frontend_quoting=False
            )
        
        # Verify the result
        assert "There was an error building the swap quote on Solana" in result
        assert "Error message" in result
    
    def test_general_exception_handling(self, monkeypatch):
        """Test general exception handling"""
        # Mock dependencies to raise an exception during token metadata retrieval
        def mock_get_token_metadata_with_exception(chain, token):
            raise Exception("Database error")
        
        monkeypatch.setattr('agents.dex_agent.jupiter_functions.tokens_service.get_token_metadata',
                            mock_get_token_metadata_with_exception)
        
        monkeypatch.setattr('agents.dex_agent.jupiter_functions.get_request_ctx',
                            lambda parentKey, key: mock_wallet_address if key == "solana_wallet_address" else mock_user_id)
        
        monkeypatch.setattr('agents.dex_agent.jupiter_functions.save_agent_thought', lambda **kwargs: None)
        
        # Test the function
        result = self.jupiter_get_quotes(
            input_token="SOL",
            output_token="USDC",
            amount=1.0,
            is_usd=False,
            chat_id="test-chat-123",
            transaction_type="swap"
        )
        
        # Verify the result
        assert "There was an error building the swap quote on Solana" in result
        assert "Database error" in result
    
    def test_negative_amount(self, monkeypatch):
        """Test with negative amount"""
        # Mock dependencies
        monkeypatch.setattr('agents.dex_agent.jupiter_functions.tokens_service.get_token_metadata',
                            lambda chain, token: mock_from_token_info if token == "SOL" else mock_to_token_info)
        
        monkeypatch.setattr('agents.dex_agent.jupiter_functions.get_request_ctx',
                            lambda parentKey, key: mock_wallet_address if key == "solana_wallet_address" else mock_user_id)
        
        monkeypatch.setattr('agents.dex_agent.jupiter_functions.save_agent_thought', lambda **kwargs: None)
        
        # Test the function
        result = self.jupiter_get_quotes(
            input_token="SOL",
            output_token="USDC",
            amount=-1.0,
            is_usd=False,
            chat_id="test-chat-123",
            transaction_type="swap"
        )
        
        # Verify the result (negative amounts are treated as valid in Python, so this should work)
        # The function only checks for 0 or None, not negative numbers
        assert "I've initiated the quoting process for your swap" in result
    
