# tests/agents/copy_trading/test_copy_trading_functions.py
import sys
from unittest.mock import Mock, patch, AsyncMock
import pytest

# Add the current directory to Python path so we can import the modules
sys.path.insert(0, '.')


class TestCopyTrading:
    """Test suite for copy_trading function"""
    
    def setup_method(self):
        """Setup method that runs before each test"""
        from agents.copy_trading.copy_trading_functions import copy_trading
        self.copy_trading = copy_trading
    
    def test_valid_solana_address(self, monkeypatch):
        """Test with valid Solana address"""
        mock_is_solana = Mock(return_value=True)
        mock_get_swaps_by_wallet_address = Mock(return_value="swaps_result")
        
        monkeypatch.setattr('agents.copy_trading.copy_trading_functions.is_solana', mock_is_solana)
        monkeypatch.setattr('agents.copy_trading.copy_trading_functions.get_swaps_by_wallet_address', mock_get_swaps_by_wallet_address)
        
        result = self.copy_trading(
            user_wallet_address="0x123",
            tracked_wallet_address="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
            chat_id="test-chat"
        )
        
        assert result == "swaps_result"
        mock_is_solana.assert_called_once_with("9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM")
        mock_get_swaps_by_wallet_address.assert_called_once_with(
            "test-chat", "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM", use_frontend_quoting=True, limit=5
        )
    
    def test_invalid_evm_address(self, monkeypatch):
        """Test with invalid EVM address"""
        mock_is_solana = Mock(return_value=False)
        
        monkeypatch.setattr('agents.copy_trading.copy_trading_functions.is_solana', mock_is_solana)
        
        result = self.copy_trading(
            user_wallet_address="0x123",
            tracked_wallet_address="0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6",
            chat_id="test-chat"
        )
        
        assert "Invalid Tracked Wallet Address (not a Solana address)" in result
        mock_is_solana.assert_called_once_with("0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6")
    
    def test_exception_handling(self, monkeypatch):
        """Test exception handling"""
        mock_is_solana = Mock(side_effect=Exception("Test error"))
        
        monkeypatch.setattr('agents.copy_trading.copy_trading_functions.is_solana', mock_is_solana)
        
        result = self.copy_trading(
            user_wallet_address="0x123",
            tracked_wallet_address="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
            chat_id="test-chat"
        )
        
        assert result == "Error saving transaction to database"
    
    def test_wallet_address_lowercase(self, monkeypatch):
        """Test that user wallet address is converted to lowercase"""
        mock_is_solana = Mock(return_value=True)
        mock_get_swaps_by_wallet_address = Mock(return_value="swaps_result")
        
        monkeypatch.setattr('agents.copy_trading.copy_trading_functions.is_solana', mock_is_solana)
        monkeypatch.setattr('agents.copy_trading.copy_trading_functions.get_swaps_by_wallet_address', mock_get_swaps_by_wallet_address)
        
        result = self.copy_trading(
            user_wallet_address="0XABC123",
            tracked_wallet_address="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
            chat_id="test-chat"
        )
        
        assert result == "swaps_result"
        # The function should handle the uppercase address internally


class TestGetLastSwapByWalletAddress:
    """Test suite for get_last_swap_by_wallet_address function"""
    
    def setup_method(self):
        """Setup method that runs before each test"""
        from agents.copy_trading.copy_trading_functions import get_last_swap_by_wallet_address
        self.get_last_swap_by_wallet_address = get_last_swap_by_wallet_address
    
    def test_successful_swap_retrieval(self, monkeypatch):
        """Test successful swap retrieval"""
        mock_swaps_result = {
            "result": [
                {"transactionHash": "hash1", "amount": 100},
                {"transactionHash": "hash2", "amount": 200}
            ]
        }
        mock_get_swaps_by_wallet_address = Mock(return_value=mock_swaps_result)
        
        monkeypatch.setattr('agents.copy_trading.copy_trading_functions.get_swaps_by_wallet_address', mock_get_swaps_by_wallet_address)
        
        result = self.get_last_swap_by_wallet_address("9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM", "test-chat")
        
        assert result == {"transactionHash": "hash1", "amount": 100}
        mock_get_swaps_by_wallet_address.assert_called_once_with("9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM", limit=1, chat_id="test-chat")
    
    def test_empty_swaps_result(self, monkeypatch):
        """Test when no swaps are found"""
        mock_swaps_result = {"result": []}
        mock_get_swaps_by_wallet_address = Mock(return_value=mock_swaps_result)
        
        monkeypatch.setattr('agents.copy_trading.copy_trading_functions.get_swaps_by_wallet_address', mock_get_swaps_by_wallet_address)
        
        result = self.get_last_swap_by_wallet_address("9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM", "test-chat")
        
        assert result is None
    
    def test_no_result_key(self, monkeypatch):
        """Test when result key is missing"""
        mock_swaps_result = {"other_key": []}
        mock_get_swaps_by_wallet_address = Mock(return_value=mock_swaps_result)
        
        monkeypatch.setattr('agents.copy_trading.copy_trading_functions.get_swaps_by_wallet_address', mock_get_swaps_by_wallet_address)
        
        result = self.get_last_swap_by_wallet_address("9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM", "test-chat")
        
        assert result is None
    
    def test_exception_handling(self, monkeypatch):
        """Test exception handling"""
        mock_get_swaps_by_wallet_address = Mock(side_effect=Exception("Test error"))
        
        monkeypatch.setattr('agents.copy_trading.copy_trading_functions.get_swaps_by_wallet_address', mock_get_swaps_by_wallet_address)
        
        result = self.get_last_swap_by_wallet_address("9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM", "test-chat")
        
        assert result is None


class TestGetLatestSwapsByWalletAddress:
    """Test suite for get_latest_swaps_by_wallet_address function"""
    
    def setup_method(self):
        """Setup method that runs before each test"""
        from agents.copy_trading.copy_trading_functions import get_latest_swaps_by_wallet_address
        self.get_latest_swaps_by_wallet_address = get_latest_swaps_by_wallet_address
    
    def test_new_swaps_found(self, monkeypatch):
        """Test when new swaps are found"""
        mock_swaps = [
            {"transactionHash": "hash1", "amount": 100},
            {"transactionHash": "hash2", "amount": 200},
            {"transactionHash": "hash3", "amount": 300}
        ]
        mock_get_swaps_by_wallet_address = Mock(return_value=mock_swaps)
        
        monkeypatch.setattr('agents.copy_trading.copy_trading_functions.get_swaps_by_wallet_address', mock_get_swaps_by_wallet_address)
        
        result = self.get_latest_swaps_by_wallet_address(
            "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
            "2024-01-01",
            "hash1",
            "test-chat"
        )
        
        # Should return swaps with different transaction hash
        assert len(result) == 2
        assert result[0]["transactionHash"] == "hash2"
        assert result[1]["transactionHash"] == "hash3"
        
        mock_get_swaps_by_wallet_address.assert_called_once_with(
            "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM", limit=100, from_date="2024-01-01", chat_id="test-chat"
        )
    
    def test_no_new_swaps(self, monkeypatch):
        """Test when no new swaps are found"""
        mock_swaps = [
            {"transactionHash": "hash1", "amount": 100}
        ]
        mock_get_swaps_by_wallet_address = Mock(return_value=mock_swaps)
        
        monkeypatch.setattr('agents.copy_trading.copy_trading_functions.get_swaps_by_wallet_address', mock_get_swaps_by_wallet_address)
        
        result = self.get_latest_swaps_by_wallet_address(
            "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
            "2024-01-01",
            "hash1",
            "test-chat"
        )
        
        assert result == []
    
    def test_no_swaps_returned(self, monkeypatch):
        """Test when no swaps are returned from the service"""
        mock_get_swaps_by_wallet_address = Mock(return_value=None)
        
        monkeypatch.setattr('agents.copy_trading.copy_trading_functions.get_swaps_by_wallet_address', mock_get_swaps_by_wallet_address)
        
        result = self.get_latest_swaps_by_wallet_address(
            "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
            "2024-01-01",
            "hash1",
            "test-chat"
        )
        
        assert result is None
    
    def test_exception_handling(self, monkeypatch):
        """Test exception handling"""
        mock_get_swaps_by_wallet_address = Mock(side_effect=Exception("Test error"))
        
        monkeypatch.setattr('agents.copy_trading.copy_trading_functions.get_swaps_by_wallet_address', mock_get_swaps_by_wallet_address)
        
        result = self.get_latest_swaps_by_wallet_address(
            "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
            "2024-01-01",
            "hash1",
            "test-chat"
        )
        
        assert result is None


class TestGetSwapsByWalletAddress:
    """Test suite for get_swaps_by_wallet_address function"""
    
    def setup_method(self):
        """Setup method that runs before each test"""
        from agents.copy_trading.copy_trading_functions import get_swaps_by_wallet_address
        self.get_swaps_by_wallet_address = get_swaps_by_wallet_address
    
    def test_successful_swaps_retrieval(self, monkeypatch):
        """Test successful swaps retrieval"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "result": [
                {
                    "transactionHash": "hash1",
                    "sold": {"symbol": "SOL", "amount": 1.0},
                    "bought": {"symbol": "USDC", "amount": 100.0}
                },
                {
                    "transactionHash": "hash2",
                    "sold": {"symbol": "USDC", "amount": 50.0},
                    "bought": {"symbol": "GRIFT", "amount": 1000.0}
                }
            ]
        }
        mock_response.raise_for_status.return_value = None
        
        mock_requests_get = Mock(return_value=mock_response)
        mock_save_agent_thought = Mock()
        mock_save_ui_message = Mock()
        
        monkeypatch.setattr('agents.copy_trading.copy_trading_functions.requests.get', mock_requests_get)
        monkeypatch.setattr('agents.copy_trading.copy_trading_functions.save_agent_thought', mock_save_agent_thought)
        monkeypatch.setattr('agents.copy_trading.copy_trading_functions.save_ui_message', mock_save_ui_message)
        
        result = self.get_swaps_by_wallet_address(
            chat_id="test-chat",
            wallet_address="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
            use_frontend_quoting=True
        )
        
        assert result == "Swaps retrieved successfully"
        assert mock_save_agent_thought.call_count == 2
        mock_save_ui_message.assert_called_once()
        
        # Verify the request was made with correct parameters
        mock_requests_get.assert_called_once()
        call_args = mock_requests_get.call_args
        assert "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM" in call_args[0][0]
        assert call_args[1]["headers"]["X-API-KEY"] == "fake-moralis-api-key"
    
    def test_successful_swaps_retrieval_no_frontend(self, monkeypatch):
        """Test successful swaps retrieval without frontend quoting"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "result": [
                {
                    "transactionHash": "hash1",
                    "sold": {"symbol": "SOL", "amount": 1.0},
                    "bought": {"symbol": "USDC", "amount": 100.0}
                }
            ]
        }
        mock_response.raise_for_status.return_value = None
        
        mock_requests_get = Mock(return_value=mock_response)
        mock_save_agent_thought = Mock()
        
        monkeypatch.setattr('agents.copy_trading.copy_trading_functions.requests.get', mock_requests_get)
        monkeypatch.setattr('agents.copy_trading.copy_trading_functions.save_agent_thought', mock_save_agent_thought)
        
        result = self.get_swaps_by_wallet_address(
            chat_id="test-chat",
            wallet_address="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
            use_frontend_quoting=False
        )
        
        assert len(result) == 1
        assert result[0]["transactionHash"] == "hash1"
        assert result[0]["sold"]["logo"] == "https://s2.coinmarketcap.com/static/img/coins/64x64/5426.png"
        assert result[0]["bought"]["logo"] == "https://assets.coingecko.com/coins/images/6319/standard/usdc.png?1696506694"
    
    def test_invalid_wallet_address(self, monkeypatch):
        """Test with invalid wallet address"""
        mock_is_solana = Mock(return_value=False)
        mock_save_agent_thought = Mock()
        
        monkeypatch.setattr('agents.copy_trading.copy_trading_functions.is_solana', mock_is_solana)
        monkeypatch.setattr('agents.copy_trading.copy_trading_functions.save_agent_thought', mock_save_agent_thought)
        
        result = self.get_swaps_by_wallet_address(
            chat_id="test-chat",
            wallet_address="0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6"
        )
        
        assert "Invalid Wallet Address (not a Solana address)" in result
    
    def test_duplicate_transaction_hashes(self, monkeypatch):
        """Test handling of duplicate transaction hashes"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "result": [
                {
                    "transactionHash": "hash1",
                    "sold": {"symbol": "SOL", "amount": 1.0},
                    "bought": {"symbol": "USDC", "amount": 100.0}
                },
                {
                    "transactionHash": "hash1",  # Duplicate hash
                    "sold": {"symbol": "SOL", "amount": 2.0},
                    "bought": {"symbol": "USDC", "amount": 200.0}
                },
                {
                    "transactionHash": "hash2",
                    "sold": {"symbol": "USDC", "amount": 50.0},
                    "bought": {"symbol": "GRIFT", "amount": 1000.0}
                }
            ]
        }
        mock_response.raise_for_status.return_value = None
        
        mock_requests_get = Mock(return_value=mock_response)
        mock_save_agent_thought = Mock()
        
        monkeypatch.setattr('agents.copy_trading.copy_trading_functions.requests.get', mock_requests_get)
        monkeypatch.setattr('agents.copy_trading.copy_trading_functions.save_agent_thought', mock_save_agent_thought)
        
        result = self.get_swaps_by_wallet_address(
            chat_id="test-chat",
            wallet_address="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"
        )
        
        # Should only return 2 unique swaps
        assert len(result) == 2
        assert result[0]["transactionHash"] == "hash1"
        assert result[1]["transactionHash"] == "hash2"
    
    def test_unknown_symbols_no_logo(self, monkeypatch):
        """Test handling of unknown symbols without logo mapping"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "result": [
                {
                    "transactionHash": "hash1",
                    "sold": {"symbol": "UNKNOWN", "amount": 1.0},
                    "bought": {"symbol": "RARE", "amount": 100.0}
                }
            ]
        }
        mock_response.raise_for_status.return_value = None
        
        mock_requests_get = Mock(return_value=mock_response)
        mock_save_agent_thought = Mock()
        
        monkeypatch.setattr('agents.copy_trading.copy_trading_functions.requests.get', mock_requests_get)
        monkeypatch.setattr('agents.copy_trading.copy_trading_functions.save_agent_thought', mock_save_agent_thought)
        
        result = self.get_swaps_by_wallet_address(
            chat_id="test-chat",
            wallet_address="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"
        )
        
        assert len(result) == 1
        # Unknown symbols should not have logo added
        assert "logo" not in result[0]["sold"]
        assert "logo" not in result[0]["bought"]
    
    def test_http_error(self, monkeypatch):
        """Test HTTP error handling"""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("HTTP Error")
        
        mock_requests_get = Mock(return_value=mock_response)
        mock_save_agent_thought = Mock()
        
        monkeypatch.setattr('agents.copy_trading.copy_trading_functions.requests.get', mock_requests_get)
        monkeypatch.setattr('agents.copy_trading.copy_trading_functions.save_agent_thought', mock_save_agent_thought)
        
        result = self.get_swaps_by_wallet_address(
            chat_id="test-chat",
            wallet_address="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"
        )
        
        assert "Error in getting swap transactions for wallet" in result
        assert "HTTP Error" in result
    
    def test_requests_exception(self, monkeypatch):
        """Test requests exception handling"""
        mock_requests_get = Mock(side_effect=Exception("Network Error"))
        mock_save_agent_thought = Mock()
        
        monkeypatch.setattr('agents.copy_trading.copy_trading_functions.requests.get', mock_requests_get)
        monkeypatch.setattr('agents.copy_trading.copy_trading_functions.save_agent_thought', mock_save_agent_thought)
        
        result = self.get_swaps_by_wallet_address(
            chat_id="test-chat",
            wallet_address="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"
        )
        
        assert "Error in getting swap transactions for wallet" in result
        assert "Network Error" in result
    
    def test_with_all_parameters(self, monkeypatch):
        """Test with all optional parameters"""
        mock_response = Mock()
        mock_response.json.return_value = {"result": []}
        mock_response.raise_for_status.return_value = None
        
        mock_requests_get = Mock(return_value=mock_response)
        mock_save_agent_thought = Mock()
        
        monkeypatch.setattr('agents.copy_trading.copy_trading_functions.requests.get', mock_requests_get)
        monkeypatch.setattr('agents.copy_trading.copy_trading_functions.save_agent_thought', mock_save_agent_thought)
        
        result = self.get_swaps_by_wallet_address(
            chat_id="test-chat",
            wallet_address="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
            network="devnet",
            from_date="2024-01-01",
            to_date="2024-12-31",
            cursor="cursor123",
            limit=50,
            order="ASC",
            transaction_types="buy",
            token_address="0x123"
        )
        
        assert result == []
        mock_requests_get.assert_called_once()
        call_args = mock_requests_get.call_args
        
        # Verify all parameters were passed correctly
        params = call_args[1]["params"]
        assert params["fromDate"] == "2024-01-01"
        assert params["toDate"] == "2024-12-31"
        assert params["cursor"] == "cursor123"
        assert params["limit"] == 50
        assert params["order"] == "ASC"
        assert params["transactionTypes"] == "buy"
        assert params["tokenAddress"] == "0x123"
