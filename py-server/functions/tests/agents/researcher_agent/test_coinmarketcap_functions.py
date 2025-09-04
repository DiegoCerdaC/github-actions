# tests/agents/researcher_agent/test_coinmarketcap_functions.py
import sys
import types
from unittest.mock import Mock, patch, AsyncMock
import pytest
import requests

# Add the current directory to Python path so we can import the modules
sys.path.insert(0, '.')

# Mock data for testing
mock_crypto_metadata = {
    "id": 1,
    "name": "Bitcoin",
    "symbol": "BTC",
    "slug": "bitcoin",
    "description": "Bitcoin is the first cryptocurrency",
    "logo": "https://example.com/bitcoin.png",
    "urls": {
        "website": ["https://bitcoin.org"],
        "technical_doc": [],
        "twitter": ["https://twitter.com/bitcoin"],
        "reddit": [],
        "message_board": [],
        "announcement": [],
        "chat": [],
        "explorer": [],
        "source_code": []
    },
    "date_added": "2013-04-28T00:00:00.000Z",
    "date_launched": None,
    "tags": ["cryptocurrency", "store-of-value"],
    "platform": None,
    "category": "cryptocurrency"
}

mock_crypto_info = {
    "id": 1,
    "name": "Bitcoin",
    "symbol": "BTC",
    "slug": "bitcoin",
    "num_market_pairs": 500,
    "date_added": "2013-04-28T00:00:00.000Z",
    "tags": ["cryptocurrency"],
    "max_supply": 21000000,
    "circulating_supply": 19000000,
    "total_supply": 19000000,
    "infinite_supply": False,
    "platform": None,
    "cmc_rank": 1,
    "self_reported_circulating_supply": None,
    "self_reported_market_cap": None,
    "tvl_ratio": None,
    "last_updated": "2023-01-01T00:00:00.000Z",
    "quote": {
        "USD": {
            "price": 50000.0,
            "volume_24h": 1000000000.0,
            "volume_change_24h": 5.0,
            "percent_change_1h": 1.0,
            "percent_change_24h": 2.0,
            "percent_change_7d": 10.0,
            "percent_change_30d": 15.0,
            "percent_change_60d": 20.0,
            "percent_change_90d": 25.0,
            "market_cap": 950000000000.0,
            "market_cap_dominance": 45.0,
            "fully_diluted_market_cap": 1050000000000.0,
            "tvl": None,
            "last_updated": "2023-01-01T00:00:00.000Z"
        }
    }
}

mock_crypto_info_with_metadata = {
    **mock_crypto_info,
    "logo": "https://example.com/bitcoin.png"
}

mock_global_metrics = {
    "quote": {
        "USD": {
            "total_market_cap": 2000000000000.0,
            "total_volume_24h": 50000000000.0,
            "total_market_cap_yesterday_percentage_change": 2.5,
            "total_volume_24h_yesterday_percentage_change": -1.2
        }
    },
    "btc_dominance": 45.0,
    "eth_dominance": 18.5,
    "active_cryptocurrencies": 8000
}

mock_solana_data = {
    "quote": {
        "USD": {
            "price": 100.0,
            "volume_24h": 500000000.0,
            "percent_change_24h": 5.0,
            "market_cap": 45000000000.0
        }
    }
}

mock_historical_data = [
    {
        "quote": {
            "USD": {
                "total_market_cap": 1900000000000.0,
                "total_volume_24h": 48000000000.0
            }
        },
        "btc_dominance": 44.0
    },
    {
        "quote": {
            "USD": {
                "total_market_cap": 1950000000000.0,
                "total_volume_24h": 49000000000.0
            }
        },
        "btc_dominance": 44.5
    }
]

mock_search_results = [
    {
        "title": "Market Summary Today",
        "link": "https://example.com/market-summary",
        "snippet": "Markets are showing positive momentum today"
    }
]

mock_chat_id = "test-chat-123"


class TestGetCryptocurrencyById:
    """Test suite for get_cryptocurrency_by_id function"""
    
    def setup_method(self):
        """Setup method that runs before each test"""
        from agents.researcher_agent.functions.coinmarketcap_functions import get_cryptocurrency_by_id
        self.get_cryptocurrency_by_id = get_cryptocurrency_by_id
    
    def test_successful_get_cryptocurrency_by_id(self, monkeypatch):
        """Test successful cryptocurrency retrieval by ID"""
        # Mock the HTTP request
        mock_response = Mock()
        mock_response.json.return_value = {"data": {"1": mock_crypto_metadata}}
        
        with patch('agents.researcher_agent.functions.coinmarketcap_functions.requests.get', return_value=mock_response):
            result = self.get_cryptocurrency_by_id(1)
        
        # Verify the result
        assert result == mock_crypto_metadata
        assert result["name"] == "Bitcoin"
        assert result["symbol"] == "BTC"
    
    def test_get_cryptocurrency_by_id_http_error(self, monkeypatch):
        """Test cryptocurrency retrieval with HTTP error"""
        # Mock the HTTP request to raise an error
        with patch('agents.researcher_agent.functions.coinmarketcap_functions.requests.get', side_effect=requests.exceptions.RequestException("API Error")):
            with pytest.raises(requests.exceptions.RequestException):
                self.get_cryptocurrency_by_id(1)


class TestGetCryptocurrencyBySymbol:
    """Test suite for get_cryptocurrency_by_symbol function"""
    
    def setup_method(self):
        """Setup method that runs before each test"""
        from agents.researcher_agent.functions.coinmarketcap_functions import get_cryptocurrency_by_symbol
        self.get_cryptocurrency_by_symbol = get_cryptocurrency_by_symbol
    
    def test_successful_get_cryptocurrency_by_symbol(self, monkeypatch):
        """Test successful cryptocurrency retrieval by symbol"""
        # Mock dependencies
        monkeypatch.setattr('agents.researcher_agent.functions.coinmarketcap_functions.save_ui_message', lambda **kwargs: None)
        
        # Mock the HTTP requests
        mock_info_response = Mock()
        mock_info_response.json.return_value = {"data": {"BTC": [mock_crypto_metadata]}}
        
        mock_quote_response = Mock()
        mock_quote_response.json.return_value = {"data": {"BTC": [{"quote": {"USD": mock_crypto_info["quote"]["USD"]}}]}}
        
        with patch('agents.researcher_agent.functions.coinmarketcap_functions.requests.get') as mock_get:
            mock_get.side_effect = [mock_info_response, mock_quote_response]
            
            result = self.get_cryptocurrency_by_symbol("BTC", mock_chat_id)
        
        # Verify the result
        assert result is not None
        assert result["name"] == "Bitcoin"
        assert result["symbol"] == "BTC"
        assert "quote" in result
    
    def test_get_cryptocurrency_by_symbol_exception(self, monkeypatch):
        """Test cryptocurrency retrieval with exception"""
        # Mock dependencies
        monkeypatch.setattr('agents.researcher_agent.functions.coinmarketcap_functions.save_ui_message', lambda **kwargs: None)
        
        # Mock the HTTP request to raise an error
        with patch('agents.researcher_agent.functions.coinmarketcap_functions.requests.get', side_effect=Exception("Network error")):
            result = self.get_cryptocurrency_by_symbol("BTC", mock_chat_id)
        
        # Verify the result
        assert result is None
    
    def test_get_cryptocurrency_by_symbol_key_error(self, monkeypatch):
        """Test cryptocurrency retrieval with key error (malformed response)"""
        # Mock dependencies
        monkeypatch.setattr('agents.researcher_agent.functions.coinmarketcap_functions.save_ui_message', lambda **kwargs: None)
        
        # Mock the HTTP request with malformed response
        mock_response = Mock()
        mock_response.json.return_value = {"data": {}}  # Missing expected keys
        
        with patch('agents.researcher_agent.functions.coinmarketcap_functions.requests.get', return_value=mock_response):
            result = self.get_cryptocurrency_by_symbol("INVALID", mock_chat_id)
        
        # Verify the result
        assert result is None


class TestGetHighestCryptocurrenciesGainers:
    """Test suite for get_highest_cryptocurrencies_gainers function"""
    
    def setup_method(self):
        """Setup method that runs before each test"""
        # Mock the config before importing
        import sys
        import types
        if 'config' not in sys.modules:
            fake_config = types.ModuleType("config")
            fake_config.COINMARKETCAP_API_KEY = "fake-api-key"
            sys.modules['config'] = fake_config
        
        from agents.researcher_agent.functions.coinmarketcap_functions import get_highest_cryptocurrencies_gainers
        self.get_highest_cryptocurrencies_gainers = get_highest_cryptocurrencies_gainers
    
    def test_successful_get_gainers_default_params(self, monkeypatch):
        """Test successful gainers retrieval with default parameters"""
        # Mock the HTTP request
        mock_response = Mock()
        mock_response.json.return_value = {"data": [mock_crypto_info, mock_crypto_info]}
        mock_response.raise_for_status.return_value = None
        
        with patch('agents.researcher_agent.functions.coinmarketcap_functions.requests.get', return_value=mock_response):
            result = self.get_highest_cryptocurrencies_gainers()
        
        # Verify the result
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["name"] == "Bitcoin"
    
    def test_successful_get_gainers_custom_params(self, monkeypatch):
        """Test successful gainers retrieval with custom parameters"""
        # Mock the HTTP request
        mock_response = Mock()
        mock_response.json.return_value = {"data": [mock_crypto_info] * 5}
        mock_response.raise_for_status.return_value = None
        
        with patch('agents.researcher_agent.functions.coinmarketcap_functions.requests.get', return_value=mock_response):
            result = self.get_highest_cryptocurrencies_gainers(time_frame="7d", num_results=5)
        
        # Verify the result
        assert isinstance(result, list)
        assert len(result) == 5
    
    def test_get_gainers_http_error(self, monkeypatch):
        """Test gainers retrieval with HTTP error"""
        # Mock the HTTP request to raise an error
        with patch('agents.researcher_agent.functions.coinmarketcap_functions.requests.get', side_effect=requests.exceptions.HTTPError("API Error")):
            result = self.get_highest_cryptocurrencies_gainers()
        
        # Verify the result
        assert isinstance(result, str)
        assert "error fetching the crypto gainers" in result
    
    def test_get_gainers_general_exception(self, monkeypatch):
        """Test gainers retrieval with general exception"""
        # Mock the HTTP request to raise a general error
        with patch('agents.researcher_agent.functions.coinmarketcap_functions.requests.get', side_effect=Exception("General error")):
            result = self.get_highest_cryptocurrencies_gainers()
        
        # Verify the result
        assert isinstance(result, str)
        assert "error fetching the crypto gainers" in result


class TestGetCryptocurrenciesByTags:
    """Test suite for get_cryptocurrencies_by_tags function"""
    
    def setup_method(self):
        """Setup method that runs before each test"""
        # Mock the config before importing
        import sys
        import types
        if 'config' not in sys.modules:
            fake_config = types.ModuleType("config")
            fake_config.COINMARKETCAP_API_KEY = "fake-api-key"
            sys.modules['config'] = fake_config
        
        from agents.researcher_agent.functions.coinmarketcap_functions import get_cryptocurrencies_by_tags, get_cryptocurrency_by_id
        self.get_cryptocurrencies_by_tags = get_cryptocurrencies_by_tags
        self.get_cryptocurrency_by_id = get_cryptocurrency_by_id
    
    def test_successful_get_by_tags_with_frontend_quoting(self, monkeypatch):
        """Test successful cryptocurrencies retrieval by tags with frontend quoting"""
        # Mock dependencies
        monkeypatch.setattr('agents.researcher_agent.functions.coinmarketcap_functions.save_ui_message', lambda **kwargs: None)
        monkeypatch.setattr('agents.researcher_agent.functions.coinmarketcap_functions.get_cryptocurrency_by_id', 
                            lambda crypto_id: {"logo": "https://example.com/logo.png"})
        
        # Create mock crypto with matching tags
        mock_crypto_with_tags = {
            **mock_crypto_info,
            "tags": ["defi", "solana"],
            "id": 1
        }
        
        # Mock the HTTP request
        mock_response = Mock()
        mock_response.json.return_value = {"data": [mock_crypto_with_tags]}
        mock_response.raise_for_status.return_value = None
        
        with patch('agents.researcher_agent.functions.coinmarketcap_functions.requests.get', return_value=mock_response):
            result = self.get_cryptocurrencies_by_tags(
                chat_id=mock_chat_id,
                tags=["defi"],
                use_frontend_quoting=True
            )
        
        # Verify the result
        assert result == "Tokens fetched successfully"
    
    def test_successful_get_by_tags_without_frontend_quoting(self, monkeypatch):
        """Test successful cryptocurrencies retrieval by tags without frontend quoting"""
        # Mock dependencies
        monkeypatch.setattr('agents.researcher_agent.functions.coinmarketcap_functions.get_cryptocurrency_by_id', 
                            lambda crypto_id: {"logo": "https://example.com/logo.png"})
        
        # Create mock crypto with matching tags
        mock_crypto_with_tags = {
            **mock_crypto_info,
            "tags": ["defi", "solana"],
            "id": 1
        }
        
        # Mock the HTTP request
        mock_response = Mock()
        mock_response.json.return_value = {"data": [mock_crypto_with_tags]}
        mock_response.raise_for_status.return_value = None
        
        with patch('agents.researcher_agent.functions.coinmarketcap_functions.requests.get', return_value=mock_response):
            result = self.get_cryptocurrencies_by_tags(
                chat_id=mock_chat_id,
                tags=["defi"],
                use_frontend_quoting=False
            )
        
        # Verify the result
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["name"] == "Bitcoin"
    
    def test_get_by_tags_no_matching_tokens(self, monkeypatch):
        """Test cryptocurrencies retrieval with no matching tags"""
        # Create mock crypto with non-matching tags
        mock_crypto_no_match = {
            **mock_crypto_info,
            "tags": ["other-tag"],
            "id": 1
        }
        
        # Mock the HTTP request
        mock_response = Mock()
        mock_response.json.return_value = {"data": [mock_crypto_no_match]}
        mock_response.raise_for_status.return_value = None
        
        with patch('agents.researcher_agent.functions.coinmarketcap_functions.requests.get', return_value=mock_response):
            result = self.get_cryptocurrencies_by_tags(
                chat_id=mock_chat_id,
                tags=["defi"],
                use_frontend_quoting=False
            )
        
        # Verify the result
        assert result == "No cryptocurrencies found with the given tags"
    
    def test_get_by_tags_http_error(self, monkeypatch):
        """Test cryptocurrencies retrieval with HTTP error"""
        # Mock the HTTP request to raise an error
        with patch('agents.researcher_agent.functions.coinmarketcap_functions.requests.get', side_effect=requests.exceptions.HTTPError("API Error")):
            result = self.get_cryptocurrencies_by_tags(
                chat_id=mock_chat_id,
                tags=["defi"],
                use_frontend_quoting=False
            )
        
        # Verify the result
        assert isinstance(result, str)
        assert "error fetching the cryptocurrencies" in result
    
    def test_get_by_tags_multiple_tags_match(self, monkeypatch):
        """Test cryptocurrencies retrieval with multiple matching tags"""
        # Mock dependencies
        monkeypatch.setattr('agents.researcher_agent.functions.coinmarketcap_functions.get_cryptocurrency_by_id', 
                            lambda crypto_id: {"logo": "https://example.com/logo.png"})
        
        # Create mock crypto with matching tags
        mock_crypto_with_tags = {
            **mock_crypto_info,
            "tags": ["defi", "solana", "gaming"],
            "id": 1
        }
        
        # Mock the HTTP request
        mock_response = Mock()
        mock_response.json.return_value = {"data": [mock_crypto_with_tags]}
        mock_response.raise_for_status.return_value = None
        
        with patch('agents.researcher_agent.functions.coinmarketcap_functions.requests.get', return_value=mock_response):
            result = self.get_cryptocurrencies_by_tags(
                chat_id=mock_chat_id,
                tags=["defi", "gaming"],
                use_frontend_quoting=False
            )
        
        # Verify the result
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["name"] == "Bitcoin"


class TestGetComprehensiveMarketData:
    """Test suite for get_comprehensive_market_data function"""
    
    def setup_method(self):
        """Setup method that runs before each test"""
        # Mock the config before importing
        import sys
        import types
        if 'config' not in sys.modules:
            fake_config = types.ModuleType("config")
            fake_config.COINMARKETCAP_API_KEY = "fake-api-key"
            sys.modules['config'] = fake_config
        
        from agents.researcher_agent.functions.coinmarketcap_functions import get_comprehensive_market_data
        self.get_comprehensive_market_data = get_comprehensive_market_data
    
    @pytest.mark.asyncio
    async def test_successful_market_data_short_summary(self, monkeypatch):
        """Test successful market data retrieval with short summary"""
        # Mock dependencies
        monkeypatch.setattr('agents.researcher_agent.functions.coinmarketcap_functions.save_agent_thought', lambda **kwargs: None)
        monkeypatch.setattr('agents.researcher_agent.functions.coinmarketcap_functions.save_ui_message', lambda **kwargs: None)
        
        # Mock search_on_google as an async function
        async def mock_search_on_google(queries):
            return mock_search_results
        
        monkeypatch.setattr('agents.researcher_agent.functions.coinmarketcap_functions.search_on_google', mock_search_on_google)
        
        # Mock the HTTP requests
        mock_global_response = Mock()
        mock_global_response.json.return_value = {"data": mock_global_metrics}
        
        mock_solana_response = Mock()
        mock_solana_response.json.return_value = {"data": {"SOL": [mock_solana_data]}}
        
        mock_historical_response = Mock()
        mock_historical_response.json.return_value = {"data": {"quotes": mock_historical_data}}
        
        with patch('agents.researcher_agent.functions.coinmarketcap_functions.requests.get') as mock_get:
            mock_get.side_effect = [mock_global_response, mock_solana_response, mock_historical_response]
            
            result = await self.get_comprehensive_market_data(
                chat_id=mock_chat_id,
                detailed_response=False,
                use_frontend_quoting=True
            )
        
        # Verify the result
        assert isinstance(result, str)
        assert "crypto market is valued at" in result
        assert "dominance" in result.lower()
    
    @pytest.mark.asyncio
    async def test_successful_market_data_detailed_response(self, monkeypatch):
        """Test successful market data retrieval with detailed response"""
        # Mock dependencies
        monkeypatch.setattr('agents.researcher_agent.functions.coinmarketcap_functions.save_agent_thought', lambda **kwargs: None)
        monkeypatch.setattr('agents.researcher_agent.functions.coinmarketcap_functions.save_ui_message', lambda **kwargs: None)
        
        # Mock search_on_google as an async function
        async def mock_search_on_google(queries):
            return mock_search_results
        
        monkeypatch.setattr('agents.researcher_agent.functions.coinmarketcap_functions.search_on_google', mock_search_on_google)
        
        # Mock the HTTP requests
        mock_global_response = Mock()
        mock_global_response.json.return_value = {"data": mock_global_metrics}
        
        mock_solana_response = Mock()
        mock_solana_response.json.return_value = {"data": {"SOL": [mock_solana_data]}}
        
        mock_historical_response = Mock()
        mock_historical_response.json.return_value = {"data": {"quotes": mock_historical_data}}
        
        with patch('agents.researcher_agent.functions.coinmarketcap_functions.requests.get') as mock_get:
            mock_get.side_effect = [mock_global_response, mock_solana_response, mock_historical_response]
            
            result = await self.get_comprehensive_market_data(
                chat_id=mock_chat_id,
                detailed_response=True,
                use_frontend_quoting=True
            )
        
        # Verify the result
        assert isinstance(result, str)
        assert len(result) > 500  # Detailed response should be longer
        assert "crypto market is currently valued at" in result
        assert "Solana is trading at" in result
        assert "volatility" in result.lower()
    
    @pytest.mark.asyncio
    async def test_market_data_without_frontend_quoting(self, monkeypatch):
        """Test market data retrieval without frontend quoting"""
        # Mock dependencies
        monkeypatch.setattr('agents.researcher_agent.functions.coinmarketcap_functions.save_agent_thought', lambda **kwargs: None)
        
        # Mock search_on_google as an async function
        async def mock_search_on_google(queries):
            return mock_search_results
        
        monkeypatch.setattr('agents.researcher_agent.functions.coinmarketcap_functions.search_on_google', mock_search_on_google)
        
        # Mock the HTTP requests
        mock_global_response = Mock()
        mock_global_response.json.return_value = {"data": mock_global_metrics}
        
        mock_solana_response = Mock()
        mock_solana_response.json.return_value = {"data": {"SOL": [mock_solana_data]}}
        
        mock_historical_response = Mock()
        mock_historical_response.json.return_value = {"data": {"quotes": mock_historical_data}}
        
        with patch('agents.researcher_agent.functions.coinmarketcap_functions.requests.get') as mock_get:
            mock_get.side_effect = [mock_global_response, mock_solana_response, mock_historical_response]
            
            result = await self.get_comprehensive_market_data(
                chat_id=mock_chat_id,
                detailed_response=False,
                use_frontend_quoting=False
            )
        
        # Verify the result
        assert isinstance(result, str)
        assert "crypto market is valued at" in result
    
    @pytest.mark.asyncio
    async def test_market_data_http_error(self, monkeypatch):
        """Test market data retrieval with HTTP error"""
        # Mock dependencies
        monkeypatch.setattr('agents.researcher_agent.functions.coinmarketcap_functions.save_agent_thought', lambda **kwargs: None)
        
        # Mock the HTTP request to raise an error
        with patch('agents.researcher_agent.functions.coinmarketcap_functions.requests.get', side_effect=requests.exceptions.HTTPError("API Error")):
            result = await self.get_comprehensive_market_data(
                chat_id=mock_chat_id,
                detailed_response=False,
                use_frontend_quoting=True
            )
        
        # Verify the result
        assert result == "Unable to generate market analysis at this time."
    
    @pytest.mark.asyncio
    async def test_market_data_general_exception(self, monkeypatch):
        """Test market data retrieval with general exception"""
        # Mock dependencies
        monkeypatch.setattr('agents.researcher_agent.functions.coinmarketcap_functions.save_agent_thought', lambda **kwargs: None)
        
        # Mock the HTTP request to raise a general error
        with patch('agents.researcher_agent.functions.coinmarketcap_functions.requests.get', side_effect=Exception("General error")):
            result = await self.get_comprehensive_market_data(
                chat_id=mock_chat_id,
                detailed_response=False,
                use_frontend_quoting=True
            )
        
        # Verify the result
        assert result == "Unable to generate market analysis at this time."
    
    @pytest.mark.asyncio
    async def test_market_data_volatility_calculation_error(self, monkeypatch):
        """Test market data retrieval with volatility calculation error"""
        # Mock dependencies
        monkeypatch.setattr('agents.researcher_agent.functions.coinmarketcap_functions.save_agent_thought', lambda **kwargs: None)
        monkeypatch.setattr('agents.researcher_agent.functions.coinmarketcap_functions.save_ui_message', lambda **kwargs: None)
        
        # Mock search_on_google as an async function
        async def mock_search_on_google(queries):
            return mock_search_results
        
        monkeypatch.setattr('agents.researcher_agent.functions.coinmarketcap_functions.search_on_google', mock_search_on_google)
        
        # Mock the HTTP requests with invalid historical data
        mock_global_response = Mock()
        mock_global_response.json.return_value = {"data": mock_global_metrics}
        
        mock_solana_response = Mock()
        mock_solana_response.json.return_value = {"data": {"SOL": [mock_solana_data]}}
        
        mock_historical_response = Mock()
        mock_historical_response.json.return_value = {"data": {"quotes": []}}  # Empty historical data
        
        with patch('agents.researcher_agent.functions.coinmarketcap_functions.requests.get') as mock_get:
            mock_get.side_effect = [mock_global_response, mock_solana_response, mock_historical_response]
            
            result = await self.get_comprehensive_market_data(
                chat_id=mock_chat_id,
                detailed_response=False,
                use_frontend_quoting=True
            )
        
        # Verify the result (should still work with volatility = 0.0)
        assert isinstance(result, str)
        assert "crypto market is valued at" in result


class TestMarketSentimentAnalysis:
    """Test suite for market sentiment analysis in get_comprehensive_market_data"""
    
    def setup_method(self):
        """Setup method that runs before each test"""
        # Mock the config before importing
        import sys
        import types
        if 'config' not in sys.modules:
            fake_config = types.ModuleType("config")
            fake_config.COINMARKETCAP_API_KEY = "fake-api-key"
            sys.modules['config'] = fake_config
        
        from agents.researcher_agent.functions.coinmarketcap_functions import get_comprehensive_market_data
        self.get_comprehensive_market_data = get_comprehensive_market_data
    
    @pytest.mark.asyncio
    async def test_bullish_market_sentiment(self, monkeypatch):
        """Test market analysis with bullish sentiment indicators"""
        # Mock dependencies
        monkeypatch.setattr('agents.researcher_agent.functions.coinmarketcap_functions.save_agent_thought', lambda **kwargs: None)
        monkeypatch.setattr('agents.researcher_agent.functions.coinmarketcap_functions.save_ui_message', lambda **kwargs: None)
        
        # Mock search_on_google as an async function
        async def mock_search_on_google(queries):
            return mock_search_results
        
        monkeypatch.setattr('agents.researcher_agent.functions.coinmarketcap_functions.search_on_google', mock_search_on_google)
        
        # Create bullish market data
        bullish_global_metrics = {
            **mock_global_metrics,
            "quote": {
                "USD": {
                    "total_market_cap": 2000000000000.0,
                    "total_volume_24h": 50000000000.0,
                    "total_market_cap_yesterday_percentage_change": 3.0,  # Strong positive
                    "total_volume_24h_yesterday_percentage_change": 15.0  # High volume increase
                }
            }
        }
        
        # Mock the HTTP requests
        mock_global_response = Mock()
        mock_global_response.json.return_value = {"data": bullish_global_metrics}
        
        mock_solana_response = Mock()
        mock_solana_response.json.return_value = {"data": {"SOL": [mock_solana_data]}}
        
        mock_historical_response = Mock()
        mock_historical_response.json.return_value = {"data": {"quotes": mock_historical_data}}
        
        with patch('agents.researcher_agent.functions.coinmarketcap_functions.requests.get') as mock_get:
            mock_get.side_effect = [mock_global_response, mock_solana_response, mock_historical_response]
            
            result = await self.get_comprehensive_market_data(
                chat_id=mock_chat_id,
                detailed_response=True,
                use_frontend_quoting=True
            )
        
        # Verify bullish sentiment indicators
        assert "strong bullish momentum" in result
    
    @pytest.mark.asyncio
    async def test_bearish_market_sentiment(self, monkeypatch):
        """Test market analysis with bearish sentiment indicators"""
        # Mock dependencies
        monkeypatch.setattr('agents.researcher_agent.functions.coinmarketcap_functions.save_agent_thought', lambda **kwargs: None)
        monkeypatch.setattr('agents.researcher_agent.functions.coinmarketcap_functions.save_ui_message', lambda **kwargs: None)
        
        # Mock search_on_google as an async function
        async def mock_search_on_google(queries):
            return mock_search_results
        
        monkeypatch.setattr('agents.researcher_agent.functions.coinmarketcap_functions.search_on_google', mock_search_on_google)
        
        # Create bearish market data
        bearish_global_metrics = {
            **mock_global_metrics,
            "quote": {
                "USD": {
                    "total_market_cap": 2000000000000.0,
                    "total_volume_24h": 50000000000.0,
                    "total_market_cap_yesterday_percentage_change": -3.0,  # Strong negative
                    "total_volume_24h_yesterday_percentage_change": 15.0  # High volume with selling
                }
            }
        }
        
        # Mock the HTTP requests
        mock_global_response = Mock()
        mock_global_response.json.return_value = {"data": bearish_global_metrics}
        
        mock_solana_response = Mock()
        mock_solana_response.json.return_value = {"data": {"SOL": [mock_solana_data]}}
        
        mock_historical_response = Mock()
        mock_historical_response.json.return_value = {"data": {"quotes": mock_historical_data}}
        
        with patch('agents.researcher_agent.functions.coinmarketcap_functions.requests.get') as mock_get:
            mock_get.side_effect = [mock_global_response, mock_solana_response, mock_historical_response]
            
            result = await self.get_comprehensive_market_data(
                chat_id=mock_chat_id,
                detailed_response=True,
                use_frontend_quoting=True
            )
        
        # Verify bearish sentiment indicators
        assert "heightened selling pressure" in result
    
    @pytest.mark.asyncio
    async def test_high_btc_dominance_analysis(self, monkeypatch):
        """Test market analysis with high BTC dominance"""
        # Mock dependencies
        monkeypatch.setattr('agents.researcher_agent.functions.coinmarketcap_functions.save_agent_thought', lambda **kwargs: None)
        monkeypatch.setattr('agents.researcher_agent.functions.coinmarketcap_functions.save_ui_message', lambda **kwargs: None)
        
        # Mock search_on_google as an async function
        async def mock_search_on_google(queries):
            return mock_search_results
        
        monkeypatch.setattr('agents.researcher_agent.functions.coinmarketcap_functions.search_on_google', mock_search_on_google)
        
        # Create high BTC dominance data
        high_btc_dominance_metrics = {
            **mock_global_metrics,
            "btc_dominance": 55.0  # High dominance
        }
        
        # Mock the HTTP requests
        mock_global_response = Mock()
        mock_global_response.json.return_value = {"data": high_btc_dominance_metrics}
        
        mock_solana_response = Mock()
        mock_solana_response.json.return_value = {"data": {"SOL": [mock_solana_data]}}
        
        mock_historical_response = Mock()
        mock_historical_response.json.return_value = {"data": {"quotes": mock_historical_data}}
        
        with patch('agents.researcher_agent.functions.coinmarketcap_functions.requests.get') as mock_get:
            mock_get.side_effect = [mock_global_response, mock_solana_response, mock_historical_response]
            
            result = await self.get_comprehensive_market_data(
                chat_id=mock_chat_id,
                detailed_response=True,
                use_frontend_quoting=True
            )
        
        # Verify high BTC dominance analysis
        assert "maintain strong market dominance" in result
        assert "risk-off sentiment" in result
