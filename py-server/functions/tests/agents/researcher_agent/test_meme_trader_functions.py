# tests/agents/researcher_agent/test_meme_trader_functions.py
import sys
import types
from unittest.mock import Mock, patch
import pytest
import requests
import pandas as pd
from datetime import datetime, timedelta

# Add the current directory to Python path so we can import the modules
sys.path.insert(0, '.')

# Mock data for testing
mock_coinmarketcap_response = {
    "data": [
        {
            "id": 1,
            "name": "Dogecoin",
            "symbol": "DOGE",
            "tags": ["memes", "solana-ecosystem"],
            "platform": {
                "name": "Solana",
                "token_address": "So11111111111111111111111111111111111111112"
            },
            "quote": {
                "USD": {
                    "price": 0.08,
                    "volume_24h": 500000000.0,
                    "percent_change_24h": 15.5,
                    "percent_change_7d": 25.2,
                    "market_cap": 10000000000.0
                }
            }
        },
        {
            "id": 2,
            "name": "Shiba Inu",
            "symbol": "SHIB",
            "tags": ["memes", "solana-ecosystem"],
            "platform": {
                "name": "Solana",
                "token_address": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
            },
            "quote": {
                "USD": {
                    "price": 0.000025,
                    "volume_24h": 300000000.0,
                    "percent_change_24h": 8.2,
                    "percent_change_7d": 12.8,
                    "market_cap": 8000000000.0
                }
            }
        },
        {
            "id": 3,
            "name": "Pepe",
            "symbol": "PEPE",
            "tags": ["memes", "solana-ecosystem"],
            "platform": {
                "name": "Solana",
                "token_address": "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"
            },
            "quote": {
                "USD": {
                    "price": 0.000012,
                    "volume_24h": 200000000.0,
                    "percent_change_24h": 22.8,
                    "percent_change_7d": 35.1,
                    "market_cap": 5000000000.0
                }
            }
        },
        {
            "id": 4,
            "name": "Floki",
            "symbol": "FLOKI",
            "tags": ["memes", "ethereum-ecosystem"],  # Different ecosystem
            "platform": {
                "name": "Ethereum",
                "token_address": "0x43f6a1be992dee408721748490772b15143ce0a7"
            },
            "quote": {
                "USD": {
                    "price": 0.00005,
                    "volume_24h": 100000000.0,
                    "percent_change_24h": 5.2,
                    "percent_change_7d": 8.1,
                    "market_cap": 3000000000.0
                }
            }
        },
        {
            "id": 5,
            "name": "Incomplete Token",
            "symbol": "INCOMPLETE",
            "tags": ["memes", "solana-ecosystem"],
            # Missing platform info - should cause KeyError
            "quote": {
                "USD": {
                    "price": 0.001,
                    "volume_24h": 50000000.0,
                    "percent_change_24h": 3.5,
                    "percent_change_7d": 5.2,
                    "market_cap": 1000000000.0
                }
            }
        }
    ]
}

mock_historical_prices_response = {
    "data": {
        "1": {
            "quotes": [
                {"timestamp": "2023-12-01T00:00:00Z", "quote": {"USD": {"price": 0.075}}},
                {"timestamp": "2023-12-01T01:00:00Z", "quote": {"USD": {"price": 0.076}}},
                {"timestamp": "2023-12-01T02:00:00Z", "quote": {"USD": {"price": 0.078}}},
                {"timestamp": "2023-12-01T03:00:00Z", "quote": {"USD": {"price": 0.077}}},
                {"timestamp": "2023-12-01T04:00:00Z", "quote": {"USD": {"price": 0.079}}},
                {"timestamp": "2023-12-01T05:00:00Z", "quote": {"USD": {"price": 0.081}}},
                {"timestamp": "2023-12-01T06:00:00Z", "quote": {"USD": {"price": 0.080}}},
                {"timestamp": "2023-12-01T07:00:00Z", "quote": {"USD": {"price": 0.082}}},
                {"timestamp": "2023-12-01T08:00:00Z", "quote": {"USD": {"price": 0.083}}},
                {"timestamp": "2023-12-01T09:00:00Z", "quote": {"USD": {"price": 0.081}}},
                {"timestamp": "2023-12-01T10:00:00Z", "quote": {"USD": {"price": 0.084}}},
                {"timestamp": "2023-12-01T11:00:00Z", "quote": {"USD": {"price": 0.085}}},
                {"timestamp": "2023-12-01T12:00:00Z", "quote": {"USD": {"price": 0.083}}},
                {"timestamp": "2023-12-01T13:00:00Z", "quote": {"USD": {"price": 0.086}}},
                {"timestamp": "2023-12-01T14:00:00Z", "quote": {"USD": {"price": 0.088}}},
                {"timestamp": "2023-12-01T15:00:00Z", "quote": {"USD": {"price": 0.087}}},
                {"timestamp": "2023-12-01T16:00:00Z", "quote": {"USD": {"price": 0.089}}},
                {"timestamp": "2023-12-01T17:00:00Z", "quote": {"USD": {"price": 0.091}}},
                {"timestamp": "2023-12-01T18:00:00Z", "quote": {"USD": {"price": 0.090}}},
                {"timestamp": "2023-12-01T19:00:00Z", "quote": {"USD": {"price": 0.092}}},
                {"timestamp": "2023-12-01T20:00:00Z", "quote": {"USD": {"price": 0.094}}},
                {"timestamp": "2023-12-01T21:00:00Z", "quote": {"USD": {"price": 0.093}}},
                {"timestamp": "2023-12-01T22:00:00Z", "quote": {"USD": {"price": 0.095}}},
                {"timestamp": "2023-12-01T23:00:00Z", "quote": {"USD": {"price": 0.080}}}  # Final price for 24h
            ]
        }
    }
}

mock_price_chart = [
    {"timestamp": "2023-12-01T00:00:00Z", "price": 100.0},
    {"timestamp": "2023-12-01T01:00:00Z", "price": 102.0},
    {"timestamp": "2023-12-01T02:00:00Z", "price": 98.0},
    {"timestamp": "2023-12-01T03:00:00Z", "price": 105.0},
    {"timestamp": "2023-12-01T04:00:00Z", "price": 103.0},
    {"timestamp": "2023-12-01T05:00:00Z", "price": 107.0},
    {"timestamp": "2023-12-01T06:00:00Z", "price": 101.0},
    {"timestamp": "2023-12-01T07:00:00Z", "price": 109.0},
    {"timestamp": "2023-12-01T08:00:00Z", "price": 106.0},
    {"timestamp": "2023-12-01T09:00:00Z", "price": 104.0},
    {"timestamp": "2023-12-01T10:00:00Z", "price": 108.0},
    {"timestamp": "2023-12-01T11:00:00Z", "price": 110.0},
    {"timestamp": "2023-12-01T12:00:00Z", "price": 112.0},
    {"timestamp": "2023-12-01T13:00:00Z", "price": 108.0},
    {"timestamp": "2023-12-01T14:00:00Z", "price": 115.0},
    {"timestamp": "2023-12-01T15:00:00Z", "price": 113.0}
]

mock_chat_id = "test-chat-123"


class TestGetCryptocurrenciesByTagsMeme:
    """Test suite for get_cryptocurrencies_by_tags function in meme_trader_functions"""
    
    def setup_method(self):
        """Setup method that runs before each test"""
        from agents.researcher_agent.functions.meme_trader_functions import get_cryptocurrencies_by_tags
        self.get_cryptocurrencies_by_tags = get_cryptocurrencies_by_tags
    
    def test_successful_get_cryptocurrencies_default_params(self, monkeypatch):
        """Test successful cryptocurrencies retrieval with default parameters"""
        # Mock the HTTP request
        mock_response = Mock()
        mock_response.json.return_value = mock_coinmarketcap_response
        
        with patch('agents.researcher_agent.functions.meme_trader_functions.requests.get', return_value=mock_response):
            result = self.get_cryptocurrencies_by_tags()
        
        # Verify the result
        assert isinstance(result, list)
        assert len(result) == 3  # Only tokens with both "memes" and "solana-ecosystem" tags
        
        # Verify the structure of returned data
        for token in result:
            assert "coinmarketcap_id" in token
            assert "name" in token
            assert "symbol" in token
            assert "price" in token
            assert "chain" in token
            assert "token_address" in token
            assert "volume_24h" in token
            assert "percent_change_24h" in token
        
        # Verify sorting by percent_change_24h (descending)
        assert result[0]["symbol"] == "PEPE"  # Highest percent_change_24h (22.8%)
        assert result[1]["symbol"] == "DOGE"  # Second highest (15.5%)
        assert result[2]["symbol"] == "SHIB"  # Third highest (8.2%)
    
    def test_get_cryptocurrencies_custom_tags(self, monkeypatch):
        """Test cryptocurrencies retrieval with custom tags"""
        # Mock the HTTP request
        mock_response = Mock()
        mock_response.json.return_value = mock_coinmarketcap_response
        
        with patch('agents.researcher_agent.functions.meme_trader_functions.requests.get', return_value=mock_response):
            result = self.get_cryptocurrencies_by_tags(tags=["memes"])  # Only memes tag
        
        # Verify the result - should include all tokens with "memes" tag
        assert isinstance(result, list)
        assert len(result) == 4  # All tokens except "Incomplete Token" (due to missing platform)
    
    def test_get_cryptocurrencies_custom_sort_and_limit(self, monkeypatch):
        """Test cryptocurrencies retrieval with custom sort and limit"""
        # Mock the HTTP request
        mock_response = Mock()
        mock_response.json.return_value = mock_coinmarketcap_response
        
        with patch('agents.researcher_agent.functions.meme_trader_functions.requests.get', return_value=mock_response):
            result = self.get_cryptocurrencies_by_tags(
                tags=["memes", "solana-ecosystem"],
                sort_by="volume_24h",
                num_results=2
            )
        
        # Verify the result
        assert isinstance(result, list)
        assert len(result) == 2  # Limited to 2 results
        
        # Verify sorting by volume_24h (descending)
        assert result[0]["symbol"] == "DOGE"  # Highest volume (500M)
        assert result[1]["symbol"] == "SHIB"  # Second highest volume (300M)
    
    def test_get_cryptocurrencies_with_key_error(self, monkeypatch):
        """Test cryptocurrencies retrieval handling KeyError for incomplete data"""
        # Mock the HTTP request
        mock_response = Mock()
        mock_response.json.return_value = mock_coinmarketcap_response
        
        with patch('agents.researcher_agent.functions.meme_trader_functions.requests.get', return_value=mock_response):
            result = self.get_cryptocurrencies_by_tags(
                tags=["memes", "solana-ecosystem"],
                num_results=10  # Request more than available valid tokens
            )
        
        # Verify the result - should exclude tokens with missing platform info
        assert isinstance(result, list)
        assert len(result) == 3  # Should exclude "Incomplete Token" due to KeyError
        
        # Verify that incomplete token is not included
        symbols = [token["symbol"] for token in result]
        assert "INCOMPLETE" not in symbols
    
    def test_get_cryptocurrencies_no_matching_tags(self, monkeypatch):
        """Test cryptocurrencies retrieval with no matching tags"""
        # Mock the HTTP request
        mock_response = Mock()
        mock_response.json.return_value = mock_coinmarketcap_response
        
        with patch('agents.researcher_agent.functions.meme_trader_functions.requests.get', return_value=mock_response):
            result = self.get_cryptocurrencies_by_tags(tags=["nonexistent-tag"])
        
        # Verify the result
        assert isinstance(result, list)
        assert len(result) == 0  # No tokens match the nonexistent tag
    
    def test_get_cryptocurrencies_http_error(self, monkeypatch):
        """Test cryptocurrencies retrieval with HTTP error"""
        # Mock the HTTP request to raise an error
        with patch('agents.researcher_agent.functions.meme_trader_functions.requests.get', side_effect=requests.exceptions.HTTPError("API Error")):
            with pytest.raises(requests.exceptions.HTTPError):
                self.get_cryptocurrencies_by_tags()


class TestGetTop3Memes:
    """Test suite for get_top_3_memes function"""
    
    def setup_method(self):
        """Setup method that runs before each test"""
        from agents.researcher_agent.functions.meme_trader_functions import get_top_3_memes
        self.get_top_3_memes = get_top_3_memes
    
    def test_successful_get_top_3_memes(self, monkeypatch):
        """Test successful retrieval of top 3 memes with scoring"""
        # Mock dependencies
        monkeypatch.setattr('agents.researcher_agent.functions.meme_trader_functions.save_agent_thought', lambda **kwargs: None)
        
        # Mock get_cryptocurrencies_by_tags to return mock data
        def mock_get_cryptocurrencies_by_tags(**kwargs):
            return [
                {
                    "coinmarketcap_id": 1,
                    "name": "Dogecoin",
                    "symbol": "DOGE",
                    "price": 0.08,
                    "chain": "Solana",
                    "token_address": "So11111111111111111111111111111111111111112",
                    "volume_24h": 500000000.0,
                    "percent_change_24h": 15.5
                },
                {
                    "coinmarketcap_id": 2,
                    "name": "Shiba Inu",
                    "symbol": "SHIB",
                    "price": 0.000025,
                    "chain": "Solana",
                    "token_address": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
                    "volume_24h": 300000000.0,
                    "percent_change_24h": 8.2
                },
                {
                    "coinmarketcap_id": 3,
                    "name": "Pepe",
                    "symbol": "PEPE",
                    "price": 0.000012,
                    "chain": "Solana",
                    "token_address": "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
                    "volume_24h": 200000000.0,
                    "percent_change_24h": 22.8
                }
            ]
        
        monkeypatch.setattr('agents.researcher_agent.functions.meme_trader_functions.get_cryptocurrencies_by_tags', mock_get_cryptocurrencies_by_tags)
        
        # Mock technical indicator functions
        monkeypatch.setattr('agents.researcher_agent.functions.meme_trader_functions.get_24h_prices_history', lambda token_id: mock_price_chart)
        monkeypatch.setattr('agents.researcher_agent.functions.meme_trader_functions.calculate_rsi', lambda chart: 45.0)  # Neutral RSI
        monkeypatch.setattr('agents.researcher_agent.functions.meme_trader_functions.calculate_sma', lambda chart: 50.0)  # Neutral SMA
        monkeypatch.setattr('agents.researcher_agent.functions.meme_trader_functions.calculate_ema', lambda chart: 48.0)  # Slightly lower EMA
        
        result = self.get_top_3_memes(mock_chat_id)
        
        # Verify the result
        assert isinstance(result, list)
        assert len(result) <= 3  # Should return up to 3 tokens
        
        # Verify that each token has technical indicators and scores
        for token in result:
            assert "price_chart" in token
            assert "rsi" in token
            assert "sma" in token
            assert "ema" in token
            assert "score" in token
            assert token["score"] >= 0  # Valid tokens should have non-negative scores
    
    def test_get_top_3_memes_with_invalid_price_data(self, monkeypatch):
        """Test get_top_3_memes handling tokens with invalid price data"""
        # Mock dependencies
        monkeypatch.setattr('agents.researcher_agent.functions.meme_trader_functions.save_agent_thought', lambda **kwargs: None)
        
        # Mock get_cryptocurrencies_by_tags to return mock data
        def mock_get_cryptocurrencies_by_tags(**kwargs):
            return [
                {
                    "coinmarketcap_id": 1,
                    "name": "Valid Token",
                    "symbol": "VALID",
                    "price": 0.08,
                    "chain": "Solana",
                    "token_address": "So11111111111111111111111111111111111111112",
                    "volume_24h": 500000000.0,
                    "percent_change_24h": 15.5
                },
                {
                    "coinmarketcap_id": 2,
                    "name": "Invalid Token",
                    "symbol": "INVALID",
                    "price": 0.000025,
                    "chain": "Solana",
                    "token_address": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
                    "volume_24h": 300000000.0,
                    "percent_change_24h": 8.2
                }
            ]
        
        monkeypatch.setattr('agents.researcher_agent.functions.meme_trader_functions.get_cryptocurrencies_by_tags', mock_get_cryptocurrencies_by_tags)
        
        # Mock get_24h_prices_history to return empty data for invalid token
        def mock_get_24h_prices_history(token_id):
            if token_id == 1:
                return mock_price_chart
            else:
                return []  # Invalid/empty price data
        
        monkeypatch.setattr('agents.researcher_agent.functions.meme_trader_functions.get_24h_prices_history', mock_get_24h_prices_history)
        monkeypatch.setattr('agents.researcher_agent.functions.meme_trader_functions.calculate_rsi', lambda chart: 45.0)
        monkeypatch.setattr('agents.researcher_agent.functions.meme_trader_functions.calculate_sma', lambda chart: 50.0)
        monkeypatch.setattr('agents.researcher_agent.functions.meme_trader_functions.calculate_ema', lambda chart: 48.0)
        
        result = self.get_top_3_memes(mock_chat_id)
        
        # Verify the result - should only include tokens with valid price data
        assert isinstance(result, list)
        assert len(result) == 1  # Only the valid token
        assert result[0]["symbol"] == "VALID"
    
    def test_get_top_3_memes_scoring_algorithm(self, monkeypatch):
        """Test the scoring algorithm for token ranking"""
        # Mock dependencies
        monkeypatch.setattr('agents.researcher_agent.functions.meme_trader_functions.save_agent_thought', lambda **kwargs: None)
        
        # Mock get_cryptocurrencies_by_tags to return one token
        def mock_get_cryptocurrencies_by_tags(**kwargs):
            return [
                {
                    "coinmarketcap_id": 1,
                    "name": "Test Token",
                    "symbol": "TEST",
                    "price": 0.08,
                    "chain": "Solana",
                    "token_address": "So11111111111111111111111111111111111111112",
                    "volume_24h": 500000000.0,
                    "percent_change_24h": 15.5
                }
            ]
        
        monkeypatch.setattr('agents.researcher_agent.functions.meme_trader_functions.get_cryptocurrencies_by_tags', mock_get_cryptocurrencies_by_tags)
        monkeypatch.setattr('agents.researcher_agent.functions.meme_trader_functions.get_24h_prices_history', lambda token_id: mock_price_chart)
        
        # Test with optimal indicators for high score
        monkeypatch.setattr('agents.researcher_agent.functions.meme_trader_functions.calculate_rsi', lambda chart: 30.0)  # RSI < 35 = +2 points
        monkeypatch.setattr('agents.researcher_agent.functions.meme_trader_functions.calculate_sma', lambda chart: 25.0)  # SMA < 30 = +2 points
        monkeypatch.setattr('agents.researcher_agent.functions.meme_trader_functions.calculate_ema', lambda chart: 20.0)  # EMA < 30 = +2 points, SMA > EMA = +1 point
        
        result = self.get_top_3_memes(mock_chat_id)
        
        # Verify the result and score calculation
        assert isinstance(result, list)
        assert len(result) == 1
        token = result[0]
        assert token["score"] == 7  # 2 (RSI) + 1 (SMA>EMA) + 2 (SMA<30) + 2 (EMA<30) = 7 points


class TestGet24hPricesHistory:
    """Test suite for get_24h_prices_history function"""
    
    def setup_method(self):
        """Setup method that runs before each test"""
        from agents.researcher_agent.functions.meme_trader_functions import get_24h_prices_history
        self.get_24h_prices_history = get_24h_prices_history
    
    def test_successful_get_prices_history(self, monkeypatch):
        """Test successful retrieval of 24h price history"""
        # Mock the HTTP request
        mock_response = Mock()
        mock_response.json.return_value = mock_historical_prices_response
        
        with patch('agents.researcher_agent.functions.meme_trader_functions.requests.get', return_value=mock_response):
            result = self.get_24h_prices_history(1)
        
        # Verify the result
        assert isinstance(result, list)
        assert len(result) == 24  # 24 hourly data points
        
        # Verify structure of returned data
        for price_point in result:
            assert "timestamp" in price_point
            assert "price" in price_point
            assert isinstance(price_point["price"], (int, float))
        
        # Verify first and last data points
        assert result[0]["price"] == 0.075
        assert result[-1]["price"] == 0.080
    
    def test_get_prices_history_no_data(self, monkeypatch):
        """Test price history retrieval when no data is available"""
        # Mock the HTTP request with no data
        mock_response = Mock()
        mock_response.json.return_value = {"data": {}}
        
        with patch('agents.researcher_agent.functions.meme_trader_functions.requests.get', return_value=mock_response):
            result = self.get_24h_prices_history(999)  # Non-existent token ID
        
        # Verify the result
        assert isinstance(result, list)
        assert len(result) == 0
    
    def test_get_prices_history_empty_quotes(self, monkeypatch):
        """Test price history retrieval with empty quotes"""
        # Mock the HTTP request with empty quotes
        mock_response = Mock()
        mock_response.json.return_value = {"data": {"1": {"quotes": []}}}
        
        with patch('agents.researcher_agent.functions.meme_trader_functions.requests.get', return_value=mock_response):
            result = self.get_24h_prices_history(1)
        
        # Verify the result
        assert isinstance(result, list)
        assert len(result) == 0
    
    def test_get_prices_history_exception(self, monkeypatch):
        """Test price history retrieval with exception"""
        # Mock the HTTP request to raise an exception
        with patch('agents.researcher_agent.functions.meme_trader_functions.requests.get', side_effect=Exception("Network error")):
            result = self.get_24h_prices_history(1)
        
        # Verify the result
        assert isinstance(result, list)
        assert len(result) == 0


class TestCalculateRSI:
    """Test suite for calculate_rsi function"""
    
    def setup_method(self):
        """Setup method that runs before each test"""
        from agents.researcher_agent.functions.meme_trader_functions import calculate_rsi
        self.calculate_rsi = calculate_rsi
    
    def test_calculate_rsi_normal_case(self):
        """Test RSI calculation with normal price data"""
        # Create test data with known price movements
        test_prices = []
        base_price = 100.0
        
        # Create 20 price points with some upward and downward movements
        for i in range(20):
            if i < 10:
                price = base_price + i * 2  # Upward trend
            else:
                price = base_price + 20 - (i - 10) * 1.5  # Downward trend
            test_prices.append({"timestamp": f"2023-12-01T{i:02d}:00:00Z", "price": price})
        
        result = self.calculate_rsi(test_prices)
        
        # Verify the result
        assert isinstance(result, (int, float))
        assert 0 <= result <= 100  # RSI should be between 0 and 100
    
    def test_calculate_rsi_all_gains(self):
        """Test RSI calculation with only price gains"""
        # Create test data with only upward price movements
        test_prices = []
        for i in range(20):
            test_prices.append({"timestamp": f"2023-12-01T{i:02d}:00:00Z", "price": 100.0 + i * 5})
        
        result = self.calculate_rsi(test_prices)
        
        # Verify the result - should be close to 100 (overbought)
        assert isinstance(result, (int, float))
        assert result > 80  # Should indicate overbought condition
        assert result <= 100
    
    def test_calculate_rsi_all_losses(self):
        """Test RSI calculation with only price losses"""
        # Create test data with only downward price movements
        test_prices = []
        for i in range(20):
            test_prices.append({"timestamp": f"2023-12-01T{i:02d}:00:00Z", "price": 200.0 - i * 5})
        
        result = self.calculate_rsi(test_prices)
        
        # Verify the result - should be close to 0 (oversold)
        assert isinstance(result, (int, float))
        assert result < 20  # Should indicate oversold condition
        assert result >= 0
    
    def test_calculate_rsi_custom_period(self):
        """Test RSI calculation with custom period"""
        # Create test data
        test_prices = []
        for i in range(30):
            test_prices.append({"timestamp": f"2023-12-01T{i:02d}:00:00Z", "price": 100.0 + (i % 5) * 2})
        
        result = self.calculate_rsi(test_prices, period=10)
        
        # Verify the result
        assert isinstance(result, (int, float))
        assert 0 <= result <= 100


class TestCalculateSMA:
    """Test suite for calculate_sma function"""
    
    def setup_method(self):
        """Setup method that runs before each test"""
        from agents.researcher_agent.functions.meme_trader_functions import calculate_sma
        self.calculate_sma = calculate_sma
    
    def test_calculate_sma_normal_case(self):
        """Test SMA calculation with normal price data"""
        # Create test data with known prices
        test_prices = [
            {"timestamp": "2023-12-01T00:00:00Z", "price": 100.0},
            {"timestamp": "2023-12-01T01:00:00Z", "price": 102.0},
            {"timestamp": "2023-12-01T02:00:00Z", "price": 98.0},
            {"timestamp": "2023-12-01T03:00:00Z", "price": 104.0},
            {"timestamp": "2023-12-01T04:00:00Z", "price": 96.0},
        ]
        
        result = self.calculate_sma(test_prices, period=3)
        
        # Verify the result
        assert isinstance(result, (int, float))
        # Last 3 prices: 98, 104, 96 -> SMA = (98 + 104 + 96) / 3 = 99.33
        assert abs(result - 99.33333333333333) < 0.01
    
    def test_calculate_sma_ascending_prices(self):
        """Test SMA calculation with ascending prices"""
        # Create test data with ascending prices
        test_prices = []
        for i in range(20):
            test_prices.append({"timestamp": f"2023-12-01T{i:02d}:00:00Z", "price": 100.0 + i * 2})
        
        result = self.calculate_sma(test_prices, period=14)
        
        # Verify the result
        assert isinstance(result, (int, float))
        assert result > 100  # Should be higher than the starting price
    
    def test_calculate_sma_stable_prices(self):
        """Test SMA calculation with stable prices"""
        # Create test data with the same price
        stable_price = 150.0
        test_prices = []
        for i in range(15):
            test_prices.append({"timestamp": f"2023-12-01T{i:02d}:00:00Z", "price": stable_price})
        
        result = self.calculate_sma(test_prices, period=10)
        
        # Verify the result - should equal the stable price
        assert isinstance(result, (int, float))
        assert abs(result - stable_price) < 0.01


class TestCalculateEMA:
    """Test suite for calculate_ema function"""
    
    def setup_method(self):
        """Setup method that runs before each test"""
        from agents.researcher_agent.functions.meme_trader_functions import calculate_ema
        self.calculate_ema = calculate_ema
    
    def test_calculate_ema_normal_case(self):
        """Test EMA calculation with normal price data"""
        # Create test data with known prices
        test_prices = [
            {"timestamp": "2023-12-01T00:00:00Z", "price": 100.0},
            {"timestamp": "2023-12-01T01:00:00Z", "price": 102.0},
            {"timestamp": "2023-12-01T02:00:00Z", "price": 98.0},
            {"timestamp": "2023-12-01T03:00:00Z", "price": 104.0},
            {"timestamp": "2023-12-01T04:00:00Z", "price": 96.0},
        ]
        
        result = self.calculate_ema(test_prices, period=3)
        
        # Verify the result
        assert isinstance(result, (int, float))
        assert result > 0  # Should be positive
    
    def test_calculate_ema_ascending_prices(self):
        """Test EMA calculation with ascending prices"""
        # Create test data with ascending prices
        test_prices = []
        for i in range(20):
            test_prices.append({"timestamp": f"2023-12-01T{i:02d}:00:00Z", "price": 100.0 + i * 2})
        
        result = self.calculate_ema(test_prices, period=14)
        
        # Verify the result
        assert isinstance(result, (int, float))
        assert result > 100  # Should be higher than the starting price
        # EMA should be closer to recent prices than SMA
    
    def test_calculate_ema_vs_sma_responsiveness(self):
        """Test that EMA is more responsive to recent price changes than SMA"""
        from agents.researcher_agent.functions.meme_trader_functions import calculate_sma
        
        # Create test data with recent price spike
        test_prices = []
        for i in range(15):
            if i < 10:
                test_prices.append({"timestamp": f"2023-12-01T{i:02d}:00:00Z", "price": 100.0})
            else:
                test_prices.append({"timestamp": f"2023-12-01T{i:02d}:00:00Z", "price": 120.0})  # Price spike
        
        ema_result = self.calculate_ema(test_prices, period=10)
        sma_result = calculate_sma(test_prices, period=10)
        
        # Verify that EMA is more responsive (closer to recent high prices)
        assert isinstance(ema_result, (int, float))
        assert isinstance(sma_result, (int, float))
        assert ema_result > sma_result  # EMA should be higher due to recent price spike
    
    def test_calculate_ema_stable_prices(self):
        """Test EMA calculation with stable prices"""
        # Create test data with the same price
        stable_price = 150.0
        test_prices = []
        for i in range(15):
            test_prices.append({"timestamp": f"2023-12-01T{i:02d}:00:00Z", "price": stable_price})
        
        result = self.calculate_ema(test_prices, period=10)
        
        # Verify the result - should equal the stable price
        assert isinstance(result, (int, float))
        assert abs(result - stable_price) < 0.01
