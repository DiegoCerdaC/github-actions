# tests/agents/researcher_agent/test_dexscreener_functions.py
import sys
import types
from unittest.mock import Mock, patch
import pytest
import requests
from datetime import datetime, timedelta

# Add the current directory to Python path so we can import the modules
sys.path.insert(0, '.')

# Mock data for testing
mock_token_info_response = {
    "pairs": [
        {
            "baseToken": {
                "name": "Test Token",
                "symbol": "TEST",
                "address": "So11111111111111111111111111111111111111112"
            },
            "quoteToken": {
                "name": "Solana",
                "symbol": "SOL",
                "address": "So11111111111111111111111111111111111111112"
            },
            "priceUsd": "0.08",
            "priceNative": "0.000123",
            "volume": {"h24": 1000000.0},
            "marketCap": 50000000.0
        }
    ]
}

mock_latest_tokens_response = [
    {
        "tokenAddress": "So11111111111111111111111111111111111111112",
        "chainId": "solana",
        "icon": "https://example.com/icon1.png",
        "description": "Test token description",
        "url": "https://dexscreener.com/solana/test1",
        "links": [
            {"label": "Website", "url": "https://test1.com"},
            {"type": "twitter", "url": "https://twitter.com/test1"}
        ]
    },
    {
        "tokenAddress": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
        "chainId": "solana",
        "icon": "https://example.com/icon2.png",
        "description": "Another test token",
        "url": "https://dexscreener.com/solana/test2",
        "links": [
            {"label": "Website", "url": "https://test2.com"}
        ]
    }
]

mock_boosted_tokens_response = [
    {
        "tokenAddress": "So11111111111111111111111111111111111111112",
        "chainId": "solana",
        "totalAmount": 1000.0,
        "icon": "https://example.com/icon1.png",
        "description": "Boosted test token",
        "links": [
            {"label": "Website", "url": "https://boosted1.com"},
            {"type": "twitter", "url": "https://twitter.com/boosted1"}
        ]
    },
    {
        "tokenAddress": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
        "chainId": "solana",
        "totalAmount": 500.0,
        "icon": "https://example.com/icon2.png",
        "description": "Another boosted token",
        "links": [
            {"label": "Website", "url": "https://boosted2.com"}
        ]
    },
    {
        "tokenAddress": "So11111111111111111111111111111111111111112",  # Duplicate
        "chainId": "solana",
        "totalAmount": 750.0,  # Lower amount - should be filtered out
        "icon": "https://example.com/icon1.png",
        "description": "Duplicate boosted token",
        "links": []
    }
]

mock_token_pairs_search_response = {
    "pairs": [
        {
            "baseToken": {
                "name": "Test Token",
                "symbol": "TEST",
                "address": "So11111111111111111111111111111111111111112"
            },
            "quoteToken": {
                "name": "Solana",
                "symbol": "SOL",
                "address": "So11111111111111111111111111111111111111113"
            },
            "priceUsd": "0.08",
            "priceNative": "0.000123",
            "volume": {"h24": 1000000.0},
            "marketCap": 50000000.0,
            "dexId": "raydium",
            "txns": {
                "h24": {
                    "buys": 150,
                    "sells": 100
                }
            },
            "priceChange": {
                "h24": 15.5
            },
            "url": "https://dexscreener.com/solana/test-sol",
            "info": {
                "imageUrl": "https://example.com/logo.png"
            }
        },
        {
            "baseToken": {
                "name": "Solana",
                "symbol": "SOL",
                "address": "So11111111111111111111111111111111111111113"
            },
            "quoteToken": {
                "name": "Test Token",
                "symbol": "TEST",
                "address": "So11111111111111111111111111111111111111112"
            },
            "priceUsd": "120.0",
            "priceNative": "1.0",
            "volume": {"h24": 5000000.0},
            "marketCap": 150000000.0,
            "dexId": "raydium",
            "txns": {
                "h24": {
                    "buys": 300,
                    "sells": 200
                }
            },
            "priceChange": {
                "h24": -5.2
            },
            "url": "https://dexscreener.com/solana/sol-test",
            "info": {
                "imageUrl": "https://example.com/sol-logo.png"
            }
        }
    ]
}

mock_token_pairs_by_chain_response = [
    {
        "baseToken": {
            "name": "Test Token",
            "symbol": "TEST",
            "address": "So11111111111111111111111111111111111111112"
        },
        "quoteToken": {
            "name": "USD Coin",
            "symbol": "USDC",
            "address": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
        },
        "priceUsd": "0.08",
        "priceNative": "0.08",
        "volume": {"h24": 2000000.0},
        "marketCap": 80000000.0,
        "dexId": "orca",
        "txns": {
            "h24": {
                "buys": 200,
                "sells": 150
            }
        },
        "priceChange": {
            "h24": 8.3
        },
        "url": "https://dexscreener.com/solana/test-usdc",
        "info": {
            "imageUrl": "https://example.com/test-logo.png"
        }
    }
]

mock_rugcheck_response = {
    "score": 1500  # Score > 1000 indicates possible rug
}

mock_rugcheck_safe_response = {
    "score": 500  # Score <= 1000 indicates safe
}

mock_chat_id = "test-chat-123"


class TestGetTokenInfo:
    """Test suite for get_token_info function"""
    
    def setup_method(self):
        """Setup method that runs before each test"""
        from agents.researcher_agent.functions.dexscreener_functions import get_token_info
        self.get_token_info = get_token_info
    
    def test_successful_get_token_info(self):
        """Test successful token info retrieval"""
        # Mock the HTTP request
        mock_response = Mock()
        mock_response.json.return_value = mock_token_info_response
        
        with patch('agents.researcher_agent.functions.dexscreener_functions.requests.get', return_value=mock_response):
            result = self.get_token_info("So11111111111111111111111111111111111111112")
        
        # Verify the result
        assert result == mock_token_info_response
        assert "pairs" in result
        assert len(result["pairs"]) == 1
        assert result["pairs"][0]["baseToken"]["name"] == "Test Token"
    
    def test_get_token_info_exception(self):
        """Test token info retrieval with exception"""
        # Mock the HTTP request to raise an exception
        with patch('agents.researcher_agent.functions.dexscreener_functions.requests.get', side_effect=Exception("Network error")):
            result = self.get_token_info("invalid_address")
        
        # Verify the result
        assert result is None


class TestGetDexscreenerLatestTokens:
    """Test suite for get_dexscreener_latest_tokens function"""
    
    def setup_method(self):
        """Setup method that runs before each test"""
        from agents.researcher_agent.functions.dexscreener_functions import get_dexscreener_latest_tokens
        self.get_dexscreener_latest_tokens = get_dexscreener_latest_tokens
    
    def test_successful_get_latest_tokens_with_frontend_quoting(self, monkeypatch):
        """Test successful latest tokens retrieval with frontend quoting"""
        # Mock save_ui_message
        monkeypatch.setattr('agents.researcher_agent.functions.dexscreener_functions.save_ui_message', lambda **kwargs: None)
        
        # Mock HTTP requests
        def mock_get(url, headers):
            mock_response = Mock()
            if "token-profiles/latest" in url:
                mock_response.json.return_value = mock_latest_tokens_response
            else:  # get_token_info calls
                mock_response.json.return_value = mock_token_info_response
            return mock_response
        
        with patch('agents.researcher_agent.functions.dexscreener_functions.requests.get', side_effect=mock_get):
            result = self.get_dexscreener_latest_tokens(mock_chat_id, use_frontend_quoting=True)
        
        # Verify the result
        assert isinstance(result, str)
        assert "latest tokens added on Dexscreener were fetched succesfully" in result
        # The actual response includes the token data directly, not as "list_to_return"
        assert "Test Token" in result  # Should include token data in the response
    
    def test_successful_get_latest_tokens_without_frontend_quoting(self, monkeypatch):
        """Test successful latest tokens retrieval without frontend quoting"""
        # Mock HTTP requests
        def mock_get(url, headers):
            mock_response = Mock()
            if "token-profiles/latest" in url:
                mock_response.json.return_value = mock_latest_tokens_response
            else:  # get_token_info calls
                mock_response.json.return_value = mock_token_info_response
            return mock_response
        
        with patch('agents.researcher_agent.functions.dexscreener_functions.requests.get', side_effect=mock_get):
            result = self.get_dexscreener_latest_tokens(mock_chat_id, use_frontend_quoting=False)
        
        # Verify the result
        assert isinstance(result, list)
        assert len(result) == 2  # Should return both tokens
        
        # Verify structure of returned data
        for token in result:
            assert "name" in token
            assert "symbol" in token
            assert "address" in token
            assert "chain" in token
            assert "logoUri" in token
            assert "description" in token
            assert "dexscreener_url" in token
            assert "website" in token
            assert "twitter" in token
        
        # Verify specific data
        assert result[0]["name"] == "Test Token"
        assert result[0]["symbol"] == "TEST"
        assert result[0]["chain"] == "solana"
        assert result[0]["website"] == "https://test1.com"
        assert result[0]["twitter"] == "https://twitter.com/test1"
        assert result[1]["twitter"] is None  # Second token has no twitter
    
    def test_get_latest_tokens_with_failed_token_info(self, monkeypatch):
        """Test latest tokens retrieval when some token info fails"""
        # Mock HTTP requests - first token_info call fails, second succeeds
        call_count = 0
        def mock_get(url, headers):
            nonlocal call_count
            mock_response = Mock()
            if "token-profiles/latest" in url:
                mock_response.json.return_value = mock_latest_tokens_response
            else:  # get_token_info calls
                call_count += 1
                if call_count == 1:
                    raise Exception("Token info failed")
                else:
                    mock_response.json.return_value = mock_token_info_response
            return mock_response
        
        with patch('agents.researcher_agent.functions.dexscreener_functions.requests.get', side_effect=mock_get):
            result = self.get_dexscreener_latest_tokens(mock_chat_id, use_frontend_quoting=False)
        
        # Verify the result - should only include the successful token
        assert isinstance(result, list)
        assert len(result) == 1  # Only one token should be included
        assert result[0]["name"] == "Test Token"
    
    def test_get_latest_tokens_api_error(self):
        """Test latest tokens retrieval with API error"""
        # Mock the HTTP request to raise an exception
        with patch('agents.researcher_agent.functions.dexscreener_functions.requests.get', side_effect=Exception("API Error")):
            result = self.get_dexscreener_latest_tokens(mock_chat_id)
        
        # Verify the result
        assert isinstance(result, str)
        assert "There was an error fetching the latest tokens" in result
        assert "API Error" in result


class TestProcessBoostedTokens:
    """Test suite for process_boosted_tokens function"""
    
    def setup_method(self):
        """Setup method that runs before each test"""
        from agents.researcher_agent.functions.dexscreener_functions import process_boosted_tokens
        self.process_boosted_tokens = process_boosted_tokens
    
    def test_process_boosted_tokens_basic_functionality(self):
        """Test boosted tokens processing basic functionality"""
        result = self.process_boosted_tokens(mock_boosted_tokens_response)
        
        # Verify the result
        assert isinstance(result, list)
        assert len(result) == 2  # Should remove duplicate and keep only 2 unique tokens
        
        # Verify deduplication - addresses should be unique
        addresses = [token["tokenAddress"] for token in result]
        assert len(addresses) == len(set(addresses))  # All addresses should be unique
    
    def test_process_boosted_tokens_empty_list(self):
        """Test boosted tokens processing with empty list"""
        result = self.process_boosted_tokens([])
        
        # Verify the result
        assert isinstance(result, list)
        assert len(result) == 0
    
    def test_process_boosted_tokens_single_token(self):
        """Test boosted tokens processing with single token"""
        single_token = [mock_boosted_tokens_response[0]]
        result = self.process_boosted_tokens(single_token)
        
        # Verify the result
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["totalAmount"] == 1000.0


class TestGetDexscreenerLatestBoostedTokens:
    """Test suite for get_dexscreener_latest_boosted_tokens function"""
    
    def setup_method(self):
        """Setup method that runs before each test"""
        from agents.researcher_agent.functions.dexscreener_functions import get_dexscreener_latest_boosted_tokens
        self.get_dexscreener_latest_boosted_tokens = get_dexscreener_latest_boosted_tokens
    
    def test_successful_get_latest_boosted_tokens_with_frontend_quoting(self, monkeypatch):
        """Test successful latest boosted tokens retrieval with frontend quoting"""
        # Mock save_ui_message
        monkeypatch.setattr('agents.researcher_agent.functions.dexscreener_functions.save_ui_message', lambda **kwargs: None)
        
        # Mock HTTP requests
        def mock_get(url, headers):
            mock_response = Mock()
            if "token-boosts/latest" in url:
                mock_response.json.return_value = mock_boosted_tokens_response
            else:  # get_token_info calls
                mock_response.json.return_value = mock_token_info_response
            return mock_response
        
        with patch('agents.researcher_agent.functions.dexscreener_functions.requests.get', side_effect=mock_get):
            result = self.get_dexscreener_latest_boosted_tokens(mock_chat_id, use_frontend_quoting=True)
        
        # Verify the result
        assert isinstance(result, str)
        assert "latest boosted tokens on Dexscreener were fetched" in result
    
    def test_successful_get_latest_boosted_tokens_without_frontend_quoting(self, monkeypatch):
        """Test successful latest boosted tokens retrieval without frontend quoting"""
        # Mock HTTP requests
        def mock_get(url, headers):
            mock_response = Mock()
            if "token-boosts/latest" in url:
                mock_response.json.return_value = mock_boosted_tokens_response
            else:  # get_token_info calls
                mock_response.json.return_value = mock_token_info_response
            return mock_response
        
        with patch('agents.researcher_agent.functions.dexscreener_functions.requests.get', side_effect=mock_get):
            result = self.get_dexscreener_latest_boosted_tokens(mock_chat_id, use_frontend_quoting=False)
        
        # Verify the result
        assert isinstance(result, list)
        assert len(result) == 2  # Should return processed (deduplicated) tokens
        
        # Verify structure of returned data
        for token in result:
            assert "name" in token
            assert "symbol" in token
            assert "address" in token
            assert "chain" in token
            assert "logoUri" in token
            assert "description" in token
            assert "boostedAmount" in token
            assert "website" in token
            assert "twitter" in token
        
        # Verify boosted amounts are included
        boosted_amounts = [token["boostedAmount"] for token in result]
        assert len(boosted_amounts) == 2  # Should have boosted amounts for both tokens
        assert all(isinstance(amount, (int, float)) for amount in boosted_amounts)  # All should be numbers
        assert all(amount > 0 for amount in boosted_amounts)  # All should be positive
    
    def test_get_latest_boosted_tokens_api_error(self):
        """Test latest boosted tokens retrieval with API error"""
        # Mock the HTTP request to raise an exception
        with patch('agents.researcher_agent.functions.dexscreener_functions.requests.get', side_effect=Exception("API Error")):
            result = self.get_dexscreener_latest_boosted_tokens(mock_chat_id)
        
        # Verify the result
        assert isinstance(result, str)
        assert "There was an error fetching the latest boosted tokens" in result
        assert "API Error" in result


class TestGetDexscreenerMostBoostedTokens:
    """Test suite for get_dexscreener_most_boosted_tokens function"""
    
    def setup_method(self):
        """Setup method that runs before each test"""
        from agents.researcher_agent.functions.dexscreener_functions import get_dexscreener_most_boosted_tokens
        self.get_dexscreener_most_boosted_tokens = get_dexscreener_most_boosted_tokens
    
    def test_successful_get_most_boosted_tokens_with_frontend_quoting(self, monkeypatch):
        """Test successful most boosted tokens retrieval with frontend quoting"""
        # Mock save_ui_message
        monkeypatch.setattr('agents.researcher_agent.functions.dexscreener_functions.save_ui_message', lambda **kwargs: None)
        
        # Mock HTTP requests
        def mock_get(url, headers):
            mock_response = Mock()
            if "token-boosts/top" in url:
                mock_response.json.return_value = mock_boosted_tokens_response[:2]  # Remove duplicate for this test
            else:  # get_token_info calls
                mock_response.json.return_value = mock_token_info_response
            return mock_response
        
        with patch('agents.researcher_agent.functions.dexscreener_functions.requests.get', side_effect=mock_get):
            result = self.get_dexscreener_most_boosted_tokens(mock_chat_id, use_frontend_quoting=True)
        
        # Verify the result
        assert isinstance(result, str)
        assert "top 10 most boosted tokens on Dexscreener were fetched" in result
    
    def test_successful_get_most_boosted_tokens_without_frontend_quoting(self, monkeypatch):
        """Test successful most boosted tokens retrieval without frontend quoting"""
        # Mock HTTP requests
        def mock_get(url, headers):
            mock_response = Mock()
            if "token-boosts/top" in url:
                mock_response.json.return_value = mock_boosted_tokens_response[:2]  # Remove duplicate for this test
            else:  # get_token_info calls
                mock_response.json.return_value = mock_token_info_response
            return mock_response
        
        with patch('agents.researcher_agent.functions.dexscreener_functions.requests.get', side_effect=mock_get):
            result = self.get_dexscreener_most_boosted_tokens(mock_chat_id, use_frontend_quoting=False)
        
        # Verify the result
        assert isinstance(result, list)
        assert len(result) == 2
        
        # Verify structure of returned data
        for token in result:
            assert "name" in token
            assert "symbol" in token
            assert "address" in token
            assert "chain" in token
            assert "logoUri" in token
            assert "description" in token
            assert "boostedAmount" in token
            assert "website" in token
            assert "twitter" in token
        
        # Verify boosted amounts are included
        assert result[0]["boostedAmount"] == 1000.0
        assert result[1]["boostedAmount"] == 500.0
    
    def test_get_most_boosted_tokens_api_error(self):
        """Test most boosted tokens retrieval with API error"""
        # Mock the HTTP request to raise an exception
        with patch('agents.researcher_agent.functions.dexscreener_functions.requests.get', side_effect=Exception("API Error")):
            result = self.get_dexscreener_most_boosted_tokens(mock_chat_id)
        
        # Verify the result
        assert isinstance(result, str)
        assert "There was an error fetching the most boosted tokens" in result
        assert "API Error" in result


class TestGetDexscreenerTokenPairInfo:
    """Test suite for get_dexscreener_token_pair_info function"""
    
    def setup_method(self):
        """Setup method that runs before each test"""
        from agents.researcher_agent.functions.dexscreener_functions import get_dexscreener_token_pair_info
        self.get_dexscreener_token_pair_info = get_dexscreener_token_pair_info
    
    def test_successful_get_token_pair_info_direct_match(self, monkeypatch):
        """Test successful token pair info retrieval with direct match"""
        # Mock get_all_native_tokens
        monkeypatch.setattr('agents.researcher_agent.functions.dexscreener_functions.get_all_native_tokens', lambda: ["SOL", "ETH", "BTC"])
        # Mock save_ui_message
        monkeypatch.setattr('agents.researcher_agent.functions.dexscreener_functions.save_ui_message', lambda **kwargs: None)
        
        # Mock HTTP requests
        def mock_get(url, headers):
            mock_response = Mock()
            if "search?q=" in url:
                mock_response.json.return_value = mock_token_pairs_search_response
            else:  # get_token_info calls
                mock_response.json.return_value = mock_token_info_response
            return mock_response
        
        with patch('agents.researcher_agent.functions.dexscreener_functions.requests.get', side_effect=mock_get):
            result = self.get_dexscreener_token_pair_info(mock_chat_id, "TEST", "SOL")
        
        # Verify the result
        assert isinstance(result, dict)
        assert "token_a_name" in result
        assert "token_a_symbol" in result
        assert "token_a_address" in result
        assert "token_b_name" in result
        assert "token_b_symbol" in result
        assert "token_b_address" in result
        assert "marketCap" in result
        assert "volume" in result
        assert "priceNative" in result
        assert "priceUsd" in result
        assert "dexId" in result
        assert "24_hrs_buys" in result
        assert "24_hrs_sells" in result
        assert "24_hrs_price_change" in result
        assert "url" in result
        
        # Verify specific values
        assert result["token_a_name"] == "Test Token"
        assert result["token_a_symbol"] == "TEST"
        assert result["token_b_name"] == "Test Token"  # From mock token info
        assert result["token_b_symbol"] == "TEST"      # From mock token info
        assert result["marketCap"] == 50.0  # 50000000 / 10^6
        assert result["volume"] == 1000000.0
        assert result["dexId"] == "raydium"
        assert result["24_hrs_buys"] == 150
        assert result["24_hrs_sells"] == 100
        assert result["24_hrs_price_change"] == 15.5
    
    def test_successful_get_token_pair_info_reverse_match(self, monkeypatch):
        """Test successful token pair info retrieval with reverse match"""
        # Mock get_all_native_tokens
        monkeypatch.setattr('agents.researcher_agent.functions.dexscreener_functions.get_all_native_tokens', lambda: ["SOL", "ETH", "BTC"])
        # Mock save_ui_message
        monkeypatch.setattr('agents.researcher_agent.functions.dexscreener_functions.save_ui_message', lambda **kwargs: None)
        
        # Mock HTTP requests
        def mock_get(url, headers):
            mock_response = Mock()
            if "search?q=" in url:
                mock_response.json.return_value = mock_token_pairs_search_response
            else:  # get_token_info calls
                mock_response.json.return_value = mock_token_info_response
            return mock_response
        
        with patch('agents.researcher_agent.functions.dexscreener_functions.requests.get', side_effect=mock_get):
            result = self.get_dexscreener_token_pair_info(mock_chat_id, "SOL", "TEST")
        
        # Verify the result - should find the reverse match
        assert isinstance(result, dict)
        assert result["token_a_name"] == "Test Token"  # From token info
        assert result["token_b_name"] == "Test Token"  # From token info
        assert result["marketCap"] == 150.0  # 150000000 / 10^6 from reverse pair
        assert result["volume"] == 5000000.0  # From reverse pair
        assert result["24_hrs_price_change"] == -5.2  # From reverse pair
    
    def test_get_token_pair_info_no_match_found(self, monkeypatch):
        """Test token pair info retrieval when no matching pair is found"""
        # Mock get_all_native_tokens
        monkeypatch.setattr('agents.researcher_agent.functions.dexscreener_functions.get_all_native_tokens', lambda: ["SOL", "ETH", "BTC"])
        
        # Mock HTTP requests - return empty pairs
        def mock_get(url, headers):
            mock_response = Mock()
            if "search?q=" in url:
                mock_response.json.return_value = {"pairs": []}
            return mock_response
        
        with patch('agents.researcher_agent.functions.dexscreener_functions.requests.get', side_effect=mock_get):
            result = self.get_dexscreener_token_pair_info(mock_chat_id, "NONEXISTENT", "TOKEN")
        
        # Verify the result
        assert isinstance(result, str)
        assert "We couldn't find any pair with the tokens you provided" in result
    
    def test_get_token_pair_info_api_error(self, monkeypatch):
        """Test token pair info retrieval with API error"""
        # Mock get_all_native_tokens
        monkeypatch.setattr('agents.researcher_agent.functions.dexscreener_functions.get_all_native_tokens', lambda: ["SOL", "ETH", "BTC"])
        
        # Mock the HTTP request to raise an exception
        with patch('agents.researcher_agent.functions.dexscreener_functions.requests.get', side_effect=Exception("API Error")):
            result = self.get_dexscreener_token_pair_info(mock_chat_id, "TEST", "SOL")
        
        # Verify the result
        assert isinstance(result, str)
        assert "There was an error fetching the token pair info" in result
        assert "API Error" in result


class TestGetDexscreenerTokenPairInfoByChainAndTokenAddress:
    """Test suite for get_dexscreener_token_pair_info_by_chain_and_token_address function"""
    
    def setup_method(self):
        """Setup method that runs before each test"""
        from agents.researcher_agent.functions.dexscreener_functions import get_dexscreener_token_pair_info_by_chain_and_token_address
        self.get_dexscreener_token_pair_info_by_chain_and_token_address = get_dexscreener_token_pair_info_by_chain_and_token_address
    
    def test_successful_get_token_pair_info_by_chain_and_address(self, monkeypatch):
        """Test successful token pair info retrieval by chain and address"""
        # Mock save_ui_message
        monkeypatch.setattr('agents.researcher_agent.functions.dexscreener_functions.save_ui_message', lambda **kwargs: None)
        
        # Mock HTTP requests
        def mock_get(url, headers):
            mock_response = Mock()
            if "token-pairs/v1/" in url:
                mock_response.json.return_value = mock_token_pairs_by_chain_response
            else:  # get_token_info calls
                mock_response.json.return_value = mock_token_info_response
            return mock_response
        
        with patch('agents.researcher_agent.functions.dexscreener_functions.requests.get', side_effect=mock_get):
            result = self.get_dexscreener_token_pair_info_by_chain_and_token_address(
                mock_chat_id, "solana", "So11111111111111111111111111111111111111112"
            )
        
        # Verify the result
        assert isinstance(result, dict)
        assert "token_a_name" in result
        assert "token_a_symbol" in result
        assert "token_a_address" in result
        assert "token_b_name" in result
        assert "token_b_symbol" in result
        assert "token_b_address" in result
        assert "marketCap" in result
        assert "volume" in result
        assert "priceNative" in result
        assert "priceUsd" in result
        assert "dexId" in result
        assert "24_hrs_buys" in result
        assert "24_hrs_sells" in result
        assert "24_hrs_price_change" in result
        assert "url" in result
        
        # Verify specific values from mock data
        assert result["token_a_name"] == "Test Token"
        assert result["token_a_symbol"] == "TEST"
        assert result["token_b_name"] == "USD Coin"
        assert result["token_b_symbol"] == "USDC"
        assert result["marketCap"] == 80.0  # 80000000 / 10^6
        assert result["volume"] == 2000000.0
        assert result["dexId"] == "orca"
        assert result["24_hrs_buys"] == 200
        assert result["24_hrs_sells"] == 150
        assert result["24_hrs_price_change"] == 8.3
    
    def test_get_token_pair_info_by_chain_and_address_no_pairs(self, monkeypatch):
        """Test token pair info retrieval when no pairs are found"""
        # Mock HTTP requests - return empty array
        def mock_get(url, headers):
            mock_response = Mock()
            mock_response.json.return_value = []
            return mock_response
        
        with patch('agents.researcher_agent.functions.dexscreener_functions.requests.get', side_effect=mock_get):
            result = self.get_dexscreener_token_pair_info_by_chain_and_token_address(
                mock_chat_id, "solana", "invalid_address"
            )
        
        # Verify the result
        assert isinstance(result, str)
        assert "We couldn't find any pair with the tokens you provided" in result
    
    def test_get_token_pair_info_by_chain_and_address_no_market_cap(self, monkeypatch):
        """Test token pair info retrieval when pairs have no market cap"""
        # Mock save_ui_message
        monkeypatch.setattr('agents.researcher_agent.functions.dexscreener_functions.save_ui_message', lambda **kwargs: None)
        
        # Mock HTTP requests - return pairs without market cap
        def mock_get(url, headers):
            mock_response = Mock()
            if "token-pairs/v1/" in url:
                pairs_without_market_cap = [{
                    "baseToken": {"name": "Test", "symbol": "TEST", "address": "addr1"},
                    "quoteToken": {"name": "USDC", "symbol": "USDC", "address": "addr2"},
                    # Missing marketCap field
                }]
                mock_response.json.return_value = pairs_without_market_cap
            return mock_response
        
        with patch('agents.researcher_agent.functions.dexscreener_functions.requests.get', side_effect=mock_get):
            result = self.get_dexscreener_token_pair_info_by_chain_and_token_address(
                mock_chat_id, "solana", "test_address"
            )
        
        # Verify the result
        assert isinstance(result, str)
        assert "We couldn't find a pair with market cap information" in result
    
    def test_get_token_pair_info_by_chain_and_address_failed_token_info(self, monkeypatch):
        """Test token pair info retrieval when token info calls fail"""
        # Mock HTTP requests
        def mock_get(url, headers):
            mock_response = Mock()
            if "token-pairs/v1/" in url:
                mock_response.json.return_value = mock_token_pairs_by_chain_response
            else:  # get_token_info calls fail
                return None
            return mock_response
        
        with patch('agents.researcher_agent.functions.dexscreener_functions.requests.get', side_effect=mock_get):
            # Mock get_token_info to return None
            with patch('agents.researcher_agent.functions.dexscreener_functions.get_token_info', return_value=None):
                result = self.get_dexscreener_token_pair_info_by_chain_and_token_address(
                    mock_chat_id, "solana", "test_address"
                )
        
        # Verify the result
        assert isinstance(result, str)
        assert "We couldn't fetch complete token information" in result
    
    def test_get_token_pair_info_by_chain_and_address_api_error(self):
        """Test token pair info retrieval with API error"""
        # Mock the HTTP request to raise an exception
        with patch('agents.researcher_agent.functions.dexscreener_functions.requests.get', side_effect=Exception("API Error")):
            result = self.get_dexscreener_token_pair_info_by_chain_and_token_address(
                mock_chat_id, "solana", "test_address"
            )
        
        # Verify the result
        assert isinstance(result, str)
        assert "There was an error fetching the token pair info" in result
        assert "API Error" in result


class TestGetMultipleTokensPairInfo:
    """Test suite for get_multiple_tokens_pair_info function"""
    
    def setup_method(self):
        """Setup method that runs before each test"""
        from agents.researcher_agent.functions.dexscreener_functions import get_multiple_tokens_pair_info
        self.get_multiple_tokens_pair_info = get_multiple_tokens_pair_info
    
    def test_successful_get_multiple_tokens_pair_info(self, monkeypatch):
        """Test successful multiple tokens pair info retrieval"""
        # Mock the get_dexscreener_token_pair_info function
        def mock_get_pair_info(chat_id, token_a_symbol, token_b_symbol):
            return {
                "token_a_name": f"{token_a_symbol} Token",
                "token_a_symbol": token_a_symbol,
                "token_a_address": f"address_{token_a_symbol.lower()}",
                "token_b_name": "Solana",
                "token_b_symbol": "SOL",
                "token_b_address": "sol_address",
                "marketCap": 50.0,
                "volume": 1000000.0,
                "priceNative": "0.000123",
                "priceUsd": "0.08",
                "dexId": "raydium",
                "24_hrs_buys": 150,
                "24_hrs_sells": 100,
                "24_hrs_price_change": 15.5,
                "url": f"https://dexscreener.com/solana/{token_a_symbol.lower()}-sol"
            }
        
        # Mock the is_possible_rug function
        def mock_is_possible_rug(token_address):
            return "test" in token_address.lower()  # TEST token is flagged as possible rug
        
        monkeypatch.setattr('agents.researcher_agent.functions.dexscreener_functions.get_dexscreener_token_pair_info', mock_get_pair_info)
        monkeypatch.setattr('agents.researcher_agent.functions.dexscreener_functions.is_possible_rug', mock_is_possible_rug)
        
        result = self.get_multiple_tokens_pair_info(["TEST", "SAFE"], mock_chat_id)
        
        # Verify the result
        assert isinstance(result, dict)
        assert len(result) == 2
        assert "TEST" in result
        assert "SAFE" in result
        
        # Verify structure and content
        for symbol, pair_info in result.items():
            assert "token_a_name" in pair_info
            assert "token_a_symbol" in pair_info
            assert "token_a_address" in pair_info
            assert "is_possible_rug" in pair_info
            assert pair_info["token_a_symbol"] == symbol
        
        # Verify rug check results
        assert result["TEST"]["is_possible_rug"] == True   # Contains "test"
        assert result["SAFE"]["is_possible_rug"] == False  # Doesn't contain "test"
    
    def test_get_multiple_tokens_pair_info_with_failures(self, monkeypatch):
        """Test multiple tokens pair info retrieval with some failures"""
        # Mock the get_dexscreener_token_pair_info function - some calls fail
        def mock_get_pair_info(chat_id, token_a_symbol, token_b_symbol):
            if token_a_symbol == "FAIL":
                return "Error: Token not found"  # Non-dict return indicates failure
            return {
                "token_a_name": f"{token_a_symbol} Token",
                "token_a_symbol": token_a_symbol,
                "token_a_address": f"address_{token_a_symbol.lower()}",
                "marketCap": 50.0,
                "volume": 1000000.0
            }
        
        # Mock the is_possible_rug function
        monkeypatch.setattr('agents.researcher_agent.functions.dexscreener_functions.get_dexscreener_token_pair_info', mock_get_pair_info)
        monkeypatch.setattr('agents.researcher_agent.functions.dexscreener_functions.is_possible_rug', lambda x: False)
        
        result = self.get_multiple_tokens_pair_info(["SUCCESS", "FAIL", "ANOTHER"], mock_chat_id)
        
        # Verify the result - should only include successful tokens
        assert isinstance(result, dict)
        assert len(result) == 2  # Only SUCCESS and ANOTHER should be included
        assert "SUCCESS" in result
        assert "ANOTHER" in result
        assert "FAIL" not in result  # Failed token should be excluded
    
    def test_get_multiple_tokens_pair_info_missing_address(self, monkeypatch):
        """Test multiple tokens pair info retrieval when token address is missing"""
        # Mock the get_dexscreener_token_pair_info function - return dict without token_a_address
        def mock_get_pair_info(chat_id, token_a_symbol, token_b_symbol):
            if token_a_symbol == "NO_ADDRESS":
                return {
                    "token_a_name": "No Address Token",
                    "token_a_symbol": token_a_symbol,
                    # Missing token_a_address
                    "marketCap": 50.0
                }
            return {
                "token_a_name": f"{token_a_symbol} Token",
                "token_a_symbol": token_a_symbol,
                "token_a_address": f"address_{token_a_symbol.lower()}",
                "marketCap": 50.0
            }
        
        monkeypatch.setattr('agents.researcher_agent.functions.dexscreener_functions.get_dexscreener_token_pair_info', mock_get_pair_info)
        monkeypatch.setattr('agents.researcher_agent.functions.dexscreener_functions.is_possible_rug', lambda x: False)
        
        result = self.get_multiple_tokens_pair_info(["GOOD", "NO_ADDRESS"], mock_chat_id)
        
        # Verify the result - should only include token with address
        assert isinstance(result, dict)
        assert len(result) == 1
        assert "GOOD" in result
        assert "NO_ADDRESS" not in result  # Token without address should be excluded
    
    def test_get_multiple_tokens_pair_info_empty_list(self):
        """Test multiple tokens pair info retrieval with empty token list"""
        result = self.get_multiple_tokens_pair_info([], mock_chat_id)
        
        # Verify the result
        assert isinstance(result, dict)
        assert len(result) == 0


class TestIsPossibleRug:
    """Test suite for is_possible_rug function"""
    
    def setup_method(self):
        """Setup method that runs before each test"""
        from agents.researcher_agent.functions.dexscreener_functions import is_possible_rug
        self.is_possible_rug = is_possible_rug
    
    def test_is_possible_rug_high_score(self):
        """Test rug check with high score (possible rug)"""
        # Mock the HTTP request to return high score
        mock_response = Mock()
        mock_response.json.return_value = mock_rugcheck_response  # score: 1500
        mock_response.raise_for_status = Mock()
        
        with patch('agents.researcher_agent.functions.dexscreener_functions.requests.get', return_value=mock_response):
            result = self.is_possible_rug("So11111111111111111111111111111111111111112")
        
        # Verify the result
        assert result == True  # Score > 1000 indicates possible rug
    
    def test_is_possible_rug_low_score(self):
        """Test rug check with low score (safe)"""
        # Mock the HTTP request to return low score
        mock_response = Mock()
        mock_response.json.return_value = mock_rugcheck_safe_response  # score: 500
        mock_response.raise_for_status = Mock()
        
        with patch('agents.researcher_agent.functions.dexscreener_functions.requests.get', return_value=mock_response):
            result = self.is_possible_rug("EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v")
        
        # Verify the result
        assert result == False  # Score <= 1000 indicates safe
    
    def test_is_possible_rug_missing_score(self):
        """Test rug check when score is missing"""
        # Mock the HTTP request to return response without score
        mock_response = Mock()
        mock_response.json.return_value = {}  # No score field
        mock_response.raise_for_status = Mock()
        
        with patch('agents.researcher_agent.functions.dexscreener_functions.requests.get', return_value=mock_response):
            result = self.is_possible_rug("test_address")
        
        # Verify the result
        assert result == False  # Default to safe when score is missing
    
    def test_is_possible_rug_api_error(self):
        """Test rug check with API error"""
        # Mock the HTTP request to raise an exception
        with patch('agents.researcher_agent.functions.dexscreener_functions.requests.get', side_effect=Exception("API Error")):
            result = self.is_possible_rug("test_address")
        
        # Verify the result
        assert result == False  # Default to safe on error
    
    def test_is_possible_rug_http_error(self):
        """Test rug check with HTTP error"""
        # Mock the HTTP request to raise HTTPError
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Not Found")
        
        with patch('agents.researcher_agent.functions.dexscreener_functions.requests.get', return_value=mock_response):
            result = self.is_possible_rug("invalid_address")
        
        # Verify the result
        assert result == False  # Default to safe on HTTP error
