# tests/agents/solana_yield_agent/test_lulo_yield_functions.py
import types
import sys
import os
from unittest.mock import Mock, patch
import pytest
import requests

# Add the current directory to Python path so we can import the modules
sys.path.insert(0, '.')

# Mock data for testing
mock_wallet_address = "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"
mock_chat_id = "test-chat-123"
mock_user_id = "user123"

mock_account_info_response = {
    "data": {
        "currentOrders": 2,
        "totalValue": 1500.50,
        "interestEarned": "0.002724 USDC",
        "realtimeApy": 8.5,
        "historicalApy": 7.8,
        "allowedProtocols": ["drift", "kamino", "marginfi", "solend", "kamino_jlp", "kam_alt"],
        "tokenBalances": [
            {
                "mint": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
                "balance": 100.0,
                "symbol": "USDC"
            },
            {
                "mint": "So11111111111111111111111111111111111111112",
                "balance": 2.5,
                "symbol": "SOL"
            }
        ]
    }
}

mock_token_info = {
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

mock_protocol_rates = [
    {
        "protocol": "marginfi",
        "rates": {
            "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v": {
                "address": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
                "logoURI": "https://example.com/usdc.png",
                "name": "USD Coin",
                "symbol": "USDC",
                "decimals": 6,
                "token_minimum_amount": 1,
                "CURRENT": "8.5",
                "1HR": "8.2",
                "24HR": "8.0",
                "7DAY": "7.8",
                "30DAY": "7.5"
            }
        }
    }
]

class TestLuloYieldFunctions:
    """Comprehensive test suite for Lulo yield functions"""
    
    def setup_method(self):
        """Setup method that runs before each test"""
        # Import the functions once for all tests
        from agents.solana_yield_agent.lulo_yield_functions import (
            get_token_symbol_from_address,
            is_token_supported,
            fetch_account_info,
            get_user_deposits,
            get_route_estimate,
            is_account_created,
            generate_deposit_transaction,
            generate_withdrawal_transaction,
            fetch_protocol_rates_raw,
            format_protocol_rates,
            find_and_render_better_rates,
            get_stable_coin_rates
        )
        self.get_token_symbol_from_address = get_token_symbol_from_address
        self.is_token_supported = is_token_supported
        self.fetch_account_info = fetch_account_info
        self.get_user_deposits = get_user_deposits
        self.get_route_estimate = get_route_estimate
        self.is_account_created = is_account_created
        self.generate_deposit_transaction = generate_deposit_transaction
        self.generate_withdrawal_transaction = generate_withdrawal_transaction
        self.fetch_protocol_rates_raw = fetch_protocol_rates_raw
        self.format_protocol_rates = format_protocol_rates
        self.find_and_render_better_rates = find_and_render_better_rates
        self.get_stable_coin_rates = get_stable_coin_rates
    
    def test_get_token_symbol_from_address_success(self):
        """Test successful token symbol retrieval from address"""
        # Test with USDC address
        result = self.get_token_symbol_from_address("EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v")
        assert result == "usdc"
        
        # Test with SOL address
        result = self.get_token_symbol_from_address("So11111111111111111111111111111111111111112")
        assert result == "sol"
    
    def test_get_token_symbol_from_address_not_found(self):
        """Test token symbol retrieval with unknown address"""
        result = self.get_token_symbol_from_address("unknown_address_123")
        assert result == ""
    
    def test_is_token_supported_by_symbol(self):
        """Test token support check by symbol"""
        # Test with supported symbols
        assert self.is_token_supported("USDC") == True
        assert self.is_token_supported("usdc") == True
        assert self.is_token_supported("SOL") == True
        assert self.is_token_supported("sol") == True
        
        # Test with unsupported symbols
        assert self.is_token_supported("BTC") == False
        assert self.is_token_supported("ETH") == False
    
    def test_is_token_supported_by_address(self):
        """Test token support check by address"""
        # Test with supported addresses
        assert self.is_token_supported("EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v") == True
        assert self.is_token_supported("So11111111111111111111111111111111111111112") == True
        
        # Test with unsupported addresses
        assert self.is_token_supported("unknown_address_123") == False
    
    def test_fetch_account_info_success(self, monkeypatch):
        """Test successful account info fetching"""
        # Mock the HTTP request
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_account_info_response
        
        with patch('agents.solana_yield_agent.lulo_yield_functions.requests.get', return_value=mock_response):
            result = self.fetch_account_info(mock_wallet_address, mock_chat_id)
        
        # Verify the result
        assert result == mock_account_info_response
    
    def test_fetch_account_info_http_error(self, monkeypatch):
        """Test account info fetching with HTTP error"""
        # Mock the HTTP request to return error
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.json.return_value = {"message": "Account not found"}
        
        with patch('agents.solana_yield_agent.lulo_yield_functions.requests.get', return_value=mock_response):
            result = self.fetch_account_info(mock_wallet_address, mock_chat_id)
        
        # Verify the error message
        assert "Error fetching user account info" in result
        assert "404" in result
    
    def test_fetch_account_info_network_error(self, monkeypatch):
        """Test account info fetching with network error"""
        # Mock the HTTP request to raise network error
        with patch('agents.solana_yield_agent.lulo_yield_functions.requests.get', side_effect=requests.exceptions.HTTPError("Network Error")):
            result = self.fetch_account_info(mock_wallet_address, mock_chat_id)

        # Verify the error message
        assert "Network error occurred while fetching account info" in result
        assert "Network error" in result
    
    def test_get_user_deposits_success_with_frontend(self, monkeypatch):
        """Test successful user deposits retrieval with frontend quoting"""
        # Mock dependencies
        monkeypatch.setattr('agents.solana_yield_agent.lulo_yield_functions.fetch_account_info',
                            lambda wallet, chat: mock_account_info_response)
        
        monkeypatch.setattr('agents.solana_yield_agent.lulo_yield_functions.tokens_service.get_token_metadata',
                            lambda chain, token: mock_token_info)
        
        monkeypatch.setattr('agents.solana_yield_agent.lulo_yield_functions.save_agent_thought', lambda **kwargs: None)
        monkeypatch.setattr('agents.solana_yield_agent.lulo_yield_functions.save_ui_message', lambda **kwargs: None)
        
        # Test the function
        result = self.get_user_deposits(mock_wallet_address, mock_chat_id, use_frontend_quoting=True)
        
        # Verify the result
        assert "Your current deposits on Lulo were successfully fetched" in result
    
    def test_get_user_deposits_no_deposits(self, monkeypatch):
        """Test user deposits when no deposits exist"""
        # Mock account info with no deposits
        no_deposits_response = {
            "data": {
                "currentOrders": 0,
                "tokenBalances": []
            }
        }
        
        monkeypatch.setattr('agents.solana_yield_agent.lulo_yield_functions.fetch_account_info',
                            lambda wallet, chat: no_deposits_response)
        
        monkeypatch.setattr('agents.solana_yield_agent.lulo_yield_functions.save_agent_thought', lambda **kwargs: None)
        
        # Test the function
        result = self.get_user_deposits(mock_wallet_address, mock_chat_id)
        
        # Verify the result
        assert "You don't have any current deposits on Lulo" in result
    
    def test_get_user_deposits_with_backend(self, monkeypatch):
        """Test user deposits retrieval with backend quoting"""
        # Mock dependencies
        monkeypatch.setattr('agents.solana_yield_agent.lulo_yield_functions.fetch_account_info',
                            lambda wallet, chat: mock_account_info_response)
        
        monkeypatch.setattr('agents.solana_yield_agent.lulo_yield_functions.tokens_service.get_token_metadata',
                            lambda chain, token: mock_token_info)
        
        monkeypatch.setattr('agents.solana_yield_agent.lulo_yield_functions.save_agent_thought', lambda **kwargs: None)
        
        # Test the function
        result = self.get_user_deposits(mock_wallet_address, mock_chat_id, use_frontend_quoting=False)
        
        # Verify the result contains the data
        assert "tokenBalances" in result
        assert len(result["tokenBalances"]) == 2
    
    def test_get_route_estimate_success(self, monkeypatch):
        """Test successful route estimate retrieval"""
        # Mock the HTTP request
        mock_response = Mock()
        mock_response.json.return_value = {"estimate": "route_data"}
        
        with patch('agents.solana_yield_agent.lulo_yield_functions.requests.get', return_value=mock_response):
            result = self.get_route_estimate(1000, "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v", mock_wallet_address)
        
        # Verify the result
        assert result == {"estimate": "route_data"}
    
    def test_get_route_estimate_error(self, monkeypatch):
        """Test route estimate with error"""
        # Mock the HTTP request to raise an exception
        with patch('agents.solana_yield_agent.lulo_yield_functions.requests.get', side_effect=Exception("API Error")):
            result = self.get_route_estimate(1000, "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v", mock_wallet_address)
        
        # Verify the error message
        assert result == "Error getting route estimate"
    
    def test_is_account_created_true(self, monkeypatch):
        """Test account creation check when account exists"""
        # Mock the HTTP request
        mock_response = Mock()
        mock_response.json.return_value = {"accountExists": True}
        
        with patch('agents.solana_yield_agent.lulo_yield_functions.requests.get', return_value=mock_response):
            result = self.is_account_created(mock_wallet_address)
        
        # Verify the result
        assert result == True
    
    def test_is_account_created_false(self, monkeypatch):
        """Test account creation check when account doesn't exist"""
        # Mock the HTTP request
        mock_response = Mock()
        mock_response.json.return_value = {"accountExists": False}
        
        with patch('agents.solana_yield_agent.lulo_yield_functions.requests.get', return_value=mock_response):
            result = self.is_account_created(mock_wallet_address)
        
        # Verify the result
        assert result == False
    
    def test_is_account_created_error(self, monkeypatch):
        """Test account creation check with error"""
        # Mock the HTTP request to raise an exception
        with patch('agents.solana_yield_agent.lulo_yield_functions.requests.get', side_effect=Exception("API Error")):
            result = self.is_account_created(mock_wallet_address)
        
        # Verify the result
        assert result == False
    
    def test_generate_deposit_transaction_success_with_frontend(self, monkeypatch):
        """Test successful deposit transaction generation with frontend quoting"""
        # Mock dependencies
        monkeypatch.setattr('agents.solana_yield_agent.lulo_yield_functions.tokens_service.get_token_metadata',
                            lambda chain, token: mock_token_info)
        
        monkeypatch.setattr('agents.solana_yield_agent.lulo_yield_functions.is_account_created',
                            lambda wallet: True)
        
        monkeypatch.setattr('agents.solana_yield_agent.lulo_yield_functions.save_agent_thought', lambda **kwargs: None)
        monkeypatch.setattr('agents.solana_yield_agent.lulo_yield_functions.save_ui_message', lambda **kwargs: None)
        
        # Test the function
        result = self.generate_deposit_transaction(
            mock_chat_id, 
            mock_wallet_address, 
            "USDC", 
            "100", 
            use_frontend_quoting=True
        )
        
        # Verify the result
        assert "I've initiated the quoting process for your deposit" in result
    
    def test_generate_deposit_transaction_zero_amount(self, monkeypatch):
        """Test deposit transaction generation with zero amount"""
        # Mock dependencies
        monkeypatch.setattr('agents.solana_yield_agent.lulo_yield_functions.tokens_service.get_token_metadata',
                            lambda chain, token: mock_token_info)
        
        monkeypatch.setattr('agents.solana_yield_agent.lulo_yield_functions.save_agent_thought', lambda **kwargs: None)
        
        # Test the function
        result = self.generate_deposit_transaction(
            mock_chat_id, 
            mock_wallet_address, 
            "USDC", 
            "0"
        )
        
        # Verify the result
        assert "Please specify the amount you want to deposit" in result
    
    def test_generate_deposit_transaction_unsupported_token(self, monkeypatch):
        """Test deposit transaction generation with unsupported token"""
        # Mock token info for unsupported token
        unsupported_token_info = {
            "symbol": "BTC",
            "address": "unsupported_address"
        }
        
        monkeypatch.setattr('agents.solana_yield_agent.lulo_yield_functions.tokens_service.get_token_metadata',
                            lambda chain, token: unsupported_token_info)
        
        monkeypatch.setattr('agents.solana_yield_agent.lulo_yield_functions.save_agent_thought', lambda **kwargs: None)
        
        # Test the function
        result = self.generate_deposit_transaction(
            mock_chat_id, 
            mock_wallet_address, 
            "BTC", 
            "100"
        )
        
        # Verify the result
        assert "Token BTC not supported by Lulo" in result
    
    def test_generate_deposit_transaction_insufficient_sol(self, monkeypatch):
        """Test deposit transaction generation with insufficient SOL for fees"""
        # Mock dependencies
        monkeypatch.setattr('agents.solana_yield_agent.lulo_yield_functions.tokens_service.get_token_metadata',
                            lambda chain, token: mock_token_info)
        
        monkeypatch.setattr('agents.solana_yield_agent.lulo_yield_functions.is_account_created',
                            lambda wallet: False)
        
        monkeypatch.setattr('agents.solana_yield_agent.lulo_yield_functions.get_single_token_balance',
                            lambda wallet, chain, token: "0.001")  # Less than 0.005 SOL
        
        monkeypatch.setattr('agents.solana_yield_agent.lulo_yield_functions.save_agent_thought', lambda **kwargs: None)
        
        # Test the function
        result = self.generate_deposit_transaction(
            mock_chat_id, 
            mock_wallet_address, 
            "USDC", 
            "100"
        )
        
        # Verify the result
        assert "Insufficient SOL balance for paying deposit fees" in result
    
    def test_generate_withdrawal_transaction_success_with_frontend(self, monkeypatch):
        """Test successful withdrawal transaction generation with frontend quoting"""
        # Mock dependencies
        monkeypatch.setattr('agents.solana_yield_agent.lulo_yield_functions.fetch_account_info',
                            lambda wallet, chat: mock_account_info_response)
        
        monkeypatch.setattr('agents.solana_yield_agent.lulo_yield_functions.save_agent_thought', lambda **kwargs: None)
        monkeypatch.setattr('agents.solana_yield_agent.lulo_yield_functions.save_ui_message', lambda **kwargs: None)
        
        # Test the function
        result = self.generate_withdrawal_transaction(
            mock_chat_id, 
            mock_wallet_address, 
            "USDC", 
            withdraw_amount="50",
            use_frontend_quoting=True
        )
        
        # Verify the result
        assert "I've initiated the quoting process for your withdrawal" in result
    
    def test_generate_withdrawal_transaction_no_amount_or_percentage(self, monkeypatch):
        """Test withdrawal transaction generation without amount or percentage"""
        # Mock dependencies
        monkeypatch.setattr('agents.solana_yield_agent.lulo_yield_functions.fetch_account_info',
                            lambda wallet, chat: mock_account_info_response)
        
        monkeypatch.setattr('agents.solana_yield_agent.lulo_yield_functions.tokens_service.get_token_metadata',
                            lambda chain, token: mock_token_info)
        
        monkeypatch.setattr('agents.solana_yield_agent.lulo_yield_functions.save_agent_thought', lambda **kwargs: None)
        
        # Test the function without amount or percentage
        result = self.generate_withdrawal_transaction(
            mock_chat_id, 
            mock_wallet_address, 
            "USDC",
            use_frontend_quoting=False
        )
        
        # Verify the result
        assert "Please specify the Amount or Percentage to withdraw" in result
    
    def test_generate_withdrawal_transaction_no_active_orders(self, monkeypatch):
        """Test withdrawal transaction generation with no active orders"""
        # Mock account info with no active orders
        no_orders_response = {
            "data": {
                "currentOrders": 0,
                "tokenBalances": []
            }
        }
        
        monkeypatch.setattr('agents.solana_yield_agent.lulo_yield_functions.fetch_account_info',
                            lambda wallet, chat: no_orders_response)
        
        monkeypatch.setattr('agents.solana_yield_agent.lulo_yield_functions.tokens_service.get_token_metadata',
                            lambda chain, token: mock_token_info)
        
        monkeypatch.setattr('agents.solana_yield_agent.lulo_yield_functions.save_agent_thought', lambda **kwargs: None)
        
        # Test the function
        result = self.generate_withdrawal_transaction(
            mock_chat_id, 
            mock_wallet_address, 
            "USDC", 
            withdraw_amount="50",
            use_frontend_quoting=False
        )
        
        # Verify the result
        assert "No active orders found" in result
    
    def test_fetch_protocol_rates_raw_success(self, monkeypatch):
        """Test successful protocol rates fetching"""
        # Mock the HTTP request
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"rates": {"token1": {"protocol1": {"rate": 8.5}}}}
        
        with patch('agents.solana_yield_agent.lulo_yield_functions.requests.get', return_value=mock_response):
            result = self.fetch_protocol_rates_raw()
        
        # Verify the result
        assert isinstance(result, list)
    
    def test_fetch_protocol_rates_raw_error(self, monkeypatch):
        """Test protocol rates fetching with error"""
        # Mock the HTTP request to raise an exception
        with patch('agents.solana_yield_agent.lulo_yield_functions.requests.get', side_effect=Exception("API Error")):
            result = self.fetch_protocol_rates_raw()
        
        # Verify the result
        assert result == {}
    
    def test_format_protocol_rates(self, monkeypatch):
        """Test protocol rates formatting"""
        # Mock the get_jupiter_token_by_address function
        mock_token_info = {
            "address": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
            "logoURI": "https://example.com/usdc.png",
            "name": "USD Coin",
            "symbol": "USDC",
            "decimals": 6
        }
        
        monkeypatch.setattr('agents.solana_yield_agent.lulo_yield_functions.get_jupiter_token_by_address',
                            lambda address: mock_token_info)
        
        # Test data
        test_pools_info = {
            "rates": {
                "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v": {
                    "marginfi": {
                        "CURRENT": 8.5,
                        "1HR": 8.2,
                        "24HR": 8.0,
                        "7DAY": 7.8,
                        "30DAY": 7.5
                    }
                }
            }
        }
        
        # Test the function
        result = self.format_protocol_rates(test_pools_info)
        
        # Verify the result (function creates one protocol per timeframe, so 5 total)
        assert isinstance(result, list)
        assert len(result) == 5  # One for each timeframe: CURRENT, 1HR, 24HR, 7DAY, 30DAY
        
        # Check that we have the expected protocols
        protocol_names = [p["protocol"] for p in result]
        assert "CURRENT" in protocol_names
        assert "1HR" in protocol_names
        assert "24HR" in protocol_names
        assert "7DAY" in protocol_names
        assert "30DAY" in protocol_names
    
    def test_find_and_render_better_rates_success(self, monkeypatch):
        """Test successful better rates finding"""
        # Mock the fetch_protocol_rates_raw function
        monkeypatch.setattr('agents.solana_yield_agent.lulo_yield_functions.fetch_protocol_rates_raw',
                            lambda: mock_protocol_rates)
        
        # Test the function
        result = self.find_and_render_better_rates(
            "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
            ["marginfi", "kamino"]
        )
        
        # Verify the result
        assert isinstance(result, dict)
        assert result["CURRENT"] == 8.5
        assert result["1HR"] == 8.2
        assert result["24HR"] == 8.0
    
    def test_find_and_render_better_rates_no_match(self, monkeypatch):
        """Test better rates finding with no matching protocols"""
        # Mock the fetch_protocol_rates_raw function
        monkeypatch.setattr('agents.solana_yield_agent.lulo_yield_functions.fetch_protocol_rates_raw',
                            lambda: mock_protocol_rates)
        
        # Test the function with non-allowed protocols
        result = self.find_and_render_better_rates(
            "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
            ["other_protocol"]
        )
        
        # Verify the result (function returns empty list when no matches, not None)
        assert result == []
    
    def test_find_and_render_better_rates_error(self, monkeypatch):
        """Test better rates finding with error"""
        # Mock the fetch_protocol_rates_raw function to raise an exception
        monkeypatch.setattr('agents.solana_yield_agent.lulo_yield_functions.fetch_protocol_rates_raw',
                            lambda: Exception("API Error"))
        
        # Test the function
        result = self.find_and_render_better_rates(
            "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
            ["marginfi"]
        )
        
        # Verify the result
        assert result is None
    
    def test_get_stable_coin_rates(self, monkeypatch):
        """Test stable coin rates retrieval"""
        # Mock the fetch_protocol_rates_raw function
        monkeypatch.setattr('agents.solana_yield_agent.lulo_yield_functions.fetch_protocol_rates_raw',
                            lambda: mock_protocol_rates)
        
        # Test the function
        result = self.get_stable_coin_rates()
        
        # Verify the result
        assert isinstance(result, dict)
        assert "marginfi" in result
        assert "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v" in result["marginfi"]
    
    def test_supported_protocols_structure(self):
        """Test that the supported_protocols list is properly structured"""
        from agents.solana_yield_agent.lulo_yield_functions import supported_protocols
        
        # Verify the structure
        assert isinstance(supported_protocols, list)
        assert len(supported_protocols) > 0
        
        # Check that all values are strings
        for protocol in supported_protocols:
            assert isinstance(protocol, str)
            assert len(protocol) > 0
        
        # Check for specific known protocols
        assert "marginfi" in supported_protocols
        assert "kamino" in supported_protocols
        assert "solend" in supported_protocols
        assert "drift" in supported_protocols
    
    def test_supported_tokens_structure(self):
        """Test that the supported_tokens dictionary is properly structured"""
        from agents.solana_yield_agent.lulo_yield_functions import supported_tokens
        
        # Verify the structure
        assert isinstance(supported_tokens, dict)
        assert len(supported_tokens) > 0
        
        # Check that all keys and values are strings
        for symbol, address in supported_tokens.items():
            assert isinstance(symbol, str)
            assert isinstance(address, str)
            assert len(symbol) > 0
            assert len(address) > 0
        
        # Check for specific known tokens
        assert "usdc" in supported_tokens
        assert "sol" in supported_tokens
        assert supported_tokens["usdc"] == "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
        assert supported_tokens["sol"] == "So11111111111111111111111111111111111111112"
    
    def test_token_minimum_amount_to_deposit_structure(self):
        """Test that the token_minimum_amount_to_deposit dictionary is properly structured"""
        from agents.solana_yield_agent.lulo_yield_functions import token_minimum_amount_to_deposit
        
        # Verify the structure
        assert isinstance(token_minimum_amount_to_deposit, dict)
        assert len(token_minimum_amount_to_deposit) > 0
        
        # Check that all keys are strings and values are numbers
        for symbol, amount in token_minimum_amount_to_deposit.items():
            assert isinstance(symbol, str)
            assert isinstance(amount, (int, float))
            assert len(symbol) > 0
            assert amount > 0
        
        # Check for specific known minimum amounts
        assert "usdc" in token_minimum_amount_to_deposit
        assert "sol" in token_minimum_amount_to_deposit
        assert token_minimum_amount_to_deposit["usdc"] == 1
        assert token_minimum_amount_to_deposit["sol"] == 0.5
