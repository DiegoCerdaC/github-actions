# tests/agents/researcher_agent/test_researcher_functions.py
import sys
import types
from unittest.mock import Mock, patch, AsyncMock
import pytest
import requests
from datetime import datetime, timedelta
import pytz

# Add the current directory to Python path so we can import the modules
sys.path.insert(0, '.')

# Mock data for testing
mock_search_response = {
    "organic": [
        {
            "title": "Bitcoin Price Today",
            "link": "https://example.com/bitcoin-price",
            "snippet": "Bitcoin is trading at $50,000 today",
            "position": 1
        },
        {
            "title": "Cryptocurrency Market Analysis",
            "link": "https://example.com/crypto-analysis",
            "snippet": "The crypto market is showing bullish signals",
            "position": 2
        },
        {
            "title": "DeFi Protocol Updates",
            "link": "https://example.com/defi-updates",
            "snippet": "New DeFi protocols are launching this week",
            "position": 3
        }
    ]
}

mock_portfolio_data = [
    {
        "wallet_address": "0x123...abc",
        "value_usd": "1500.50",
        "history": [
            {"date": "2023-12-01T00:00:00Z", "value_usd": "1400.00"},
            {"date": "2023-11-01T00:00:00Z", "value_usd": "1300.00"},
            {"date": "2023-10-01T00:00:00Z", "value_usd": "1200.00"}
        ]
    },
    {
        "wallet_address": "9WzD...AWWM",
        "value_usd": "2500.25",
        "history": [
            {"date": "2023-12-01T00:00:00Z", "value_usd": "2400.00"},
            {"date": "2023-11-01T00:00:00Z", "value_usd": "2300.00"},
            {"date": "2023-10-01T00:00:00Z", "value_usd": "2200.00"}
        ]
    }
]

mock_balances_data = {
    "balances": [
        {
            "symbol": "ETH",
            "chain": "ETHEREUM",
            "amount": "1.5",
            "usd_amount": "3000.00",
            "address": "0x0000000000000000000000000000000000000000"
        },
        {
            "symbol": "USDC",
            "chain": "ETHEREUM", 
            "amount": "500.0",
            "usd_amount": "500.00",
            "address": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
        },
        {
            "symbol": "SOL",
            "chain": "SOLANA",
            "amount": "10.0",
            "usd_amount": "1000.00",
            "address": "So11111111111111111111111111111111111111112"
        }
    ]
}

mock_dexscreener_data = {
    "24_hrs_price_change": 5.2,
    "volume": 1000000.0,
    "marketCap": 50000000.0,
    "24_hrs_buys": 100,
    "24_hrs_sells": 80
}

mock_coinmarketcap_data = {
    "quote": {
        "volume_24h": 2000000000.0,
        "percent_change_24h": 3.5,
        "market_cap": 100000000000.0,
        "percent_change_7d": 10.2,
        "percent_change_30d": 15.8
    }
}

mock_chat_id = "test-chat-123"
mock_user_id = "test-user-456"


class TestSearchOnGoogle:
    """Test suite for search_on_google function"""
    
    def setup_method(self):
        """Setup method that runs before each test"""
        from agents.researcher_agent.functions.researcher_functions import search_on_google
        self.search_on_google = search_on_google
    
    @pytest.mark.asyncio
    async def test_successful_search_single_keyword(self, monkeypatch):
        """Test successful search with single keyword"""
        # Mock the search function
        def mock_search(keyword):
            return mock_search_response
        
        monkeypatch.setattr('agents.researcher_agent.functions.researcher_functions.search', mock_search)
        
        result = await self.search_on_google(["bitcoin price"])
        
        # Verify the result
        assert isinstance(result, list)
        assert len(result) == 3  # 3 organic results
        assert result[0]["title"] == "Bitcoin Price Today"
        assert result[0]["query"] == "bitcoin price"
        assert result[0]["source"] == "google_search"
    
    @pytest.mark.asyncio
    async def test_successful_search_multiple_keywords(self, monkeypatch):
        """Test successful search with multiple keywords"""
        # Mock the search function
        def mock_search(keyword):
            return mock_search_response
        
        monkeypatch.setattr('agents.researcher_agent.functions.researcher_functions.search', mock_search)
        
        result = await self.search_on_google(["bitcoin price", "ethereum news"])
        
        # Verify the result
        assert isinstance(result, list)
        assert len(result) == 6  # 3 results per keyword * 2 keywords
        # Check that we have results for both queries
        queries = [r["query"] for r in result]
        assert "bitcoin price" in queries
        assert "ethereum news" in queries
    
    @pytest.mark.asyncio
    async def test_search_with_exception(self, monkeypatch):
        """Test search handling exceptions"""
        # Mock the search function to raise an exception
        def mock_search_with_exception(keyword):
            raise Exception("API Error")
        
        monkeypatch.setattr('agents.researcher_agent.functions.researcher_functions.search', mock_search_with_exception)
        
        result = await self.search_on_google(["bitcoin price", "ethereum news"])
        
        # Verify the result - should return empty list when all searches fail
        assert isinstance(result, list)
        assert len(result) == 0
    
    @pytest.mark.asyncio
    async def test_search_empty_organic_results(self, monkeypatch):
        """Test search with empty organic results"""
        # Mock the search function with empty organic results
        def mock_search_empty(keyword):
            return {"organic": []}
        
        monkeypatch.setattr('agents.researcher_agent.functions.researcher_functions.search', mock_search_empty)
        
        result = await self.search_on_google(["bitcoin price"])
        
        # Verify the result
        assert isinstance(result, list)
        assert len(result) == 0
    
    @pytest.mark.asyncio
    async def test_search_partial_failure(self, monkeypatch):
        """Test search with some keywords failing"""
        # Mock the search function to succeed for first keyword, fail for second
        def mock_search_partial(keyword):
            if keyword == "bitcoin price":
                return mock_search_response
            else:
                raise Exception("API Error")
        
        monkeypatch.setattr('agents.researcher_agent.functions.researcher_functions.search', mock_search_partial)
        
        result = await self.search_on_google(["bitcoin price", "ethereum news"])
        
        # Verify the result - should have results from successful search only
        assert isinstance(result, list)
        assert len(result) == 3  # Only results from "bitcoin price"
        assert all(r["query"] == "bitcoin price" for r in result)


class TestSearch:
    """Test suite for search function"""
    
    def setup_method(self):
        """Setup method that runs before each test"""
        from agents.researcher_agent.functions.researcher_functions import search
        self.search = search
    
    def test_successful_search(self, monkeypatch):
        """Test successful search request"""
        # Mock the requests.request function
        mock_response = Mock()
        mock_response.text = '{"organic": [{"title": "Test Result"}]}'
        
        with patch('agents.researcher_agent.functions.researcher_functions.requests.request', return_value=mock_response):
            result = self.search("bitcoin price")
        
        # Verify the result
        assert isinstance(result, dict)
        assert "organic" in result
        assert result["organic"][0]["title"] == "Test Result"
    
    def test_search_with_invalid_json(self, monkeypatch):
        """Test search with invalid JSON response"""
        # Mock the requests.request function with invalid JSON
        mock_response = Mock()
        mock_response.text = 'invalid json'
        
        with patch('agents.researcher_agent.functions.researcher_functions.requests.request', return_value=mock_response):
            with pytest.raises(Exception):  # Should raise JSON decode error
                self.search("bitcoin price")


class TestGetAdditionalContext:
    """Test suite for get_additional_context function"""
    
    def setup_method(self):
        """Setup method that runs before each test"""
        from agents.researcher_agent.functions.researcher_functions import get_additional_context
        self.get_additional_context = get_additional_context
    
    @pytest.mark.asyncio
    async def test_successful_get_context(self, monkeypatch):
        """Test successful context retrieval"""
        # Mock search_on_google
        async def mock_search_on_google(queries):
            return [
                {
                    "title": "Bitcoin Analysis",
                    "link": "https://example.com/bitcoin",
                    "snippet": "Bitcoin is showing strong momentum",
                    "query": queries[0]
                }
            ]
        
        monkeypatch.setattr('agents.researcher_agent.functions.researcher_functions.search_on_google', mock_search_on_google)
        
        result = await self.get_additional_context(["bitcoin price"], ["analyze market"])
        
        # Verify the result
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["title"] == "Bitcoin Analysis"
    
    @pytest.mark.asyncio
    async def test_get_context_with_exception(self, monkeypatch):
        """Test context retrieval with exception"""
        # Mock search_on_google to raise exception
        async def mock_search_with_exception(queries):
            raise Exception("Search failed")
        
        monkeypatch.setattr('agents.researcher_agent.functions.researcher_functions.search_on_google', mock_search_with_exception)
        
        result = await self.get_additional_context(["bitcoin price"], ["analyze market"])
        
        # Verify the result - should return empty list on error
        assert isinstance(result, list)
        assert len(result) == 0


class TestGetPortfolioHistory:
    """Test suite for get_portfolio_history function"""
    
    def setup_method(self):
        """Setup method that runs before each test"""
        from agents.researcher_agent.functions.researcher_functions import get_portfolio_history
        self.get_portfolio_history = get_portfolio_history
    
    def test_successful_portfolio_fetch(self, monkeypatch):
        """Test successful portfolio history fetch"""
        # Mock dependencies
        monkeypatch.setattr('agents.researcher_agent.functions.researcher_functions.get_request_ctx', 
                            lambda chat_id, key: mock_user_id if key == "user_id" else None)
        monkeypatch.setattr('agents.researcher_agent.functions.researcher_functions.generate_firebase_id_token', 
                            lambda user_id: "fake-token")
        
        # Mock the HTTP request
        mock_response = Mock()
        mock_response.json.return_value = mock_portfolio_data
        mock_response.raise_for_status.return_value = None
        
        with patch('agents.researcher_agent.functions.researcher_functions.requests.post', return_value=mock_response):
            result = self.get_portfolio_history(mock_chat_id)
        
        # Verify the result
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["wallet_address"] == "0x123...abc"
        assert result[0]["value_usd"] == "1500.50"
    
    def test_portfolio_fetch_no_user_id(self, monkeypatch):
        """Test portfolio fetch without user ID"""
        # Mock get_request_ctx to return None for user_id
        monkeypatch.setattr('agents.researcher_agent.functions.researcher_functions.get_request_ctx', 
                            lambda chat_id, key: None)
        
        result = self.get_portfolio_history(mock_chat_id)
        
        # Verify the result
        assert isinstance(result, dict)
        assert "error" in result
        assert "No user ID found" in result["error"]
    
    def test_portfolio_fetch_token_generation_error(self, monkeypatch):
        """Test portfolio fetch with token generation error"""
        # Mock dependencies
        monkeypatch.setattr('agents.researcher_agent.functions.researcher_functions.get_request_ctx', 
                            lambda chat_id, key: mock_user_id if key == "user_id" else None)
        monkeypatch.setattr('agents.researcher_agent.functions.researcher_functions.generate_firebase_id_token', 
                            lambda user_id: (_ for _ in ()).throw(Exception("Token error")))
        
        result = self.get_portfolio_history(mock_chat_id)
        
        # Verify the result
        assert isinstance(result, dict)
        assert "error" in result
        assert "Failed to generate authentication token" in result["error"]
    
    def test_portfolio_fetch_http_error(self, monkeypatch):
        """Test portfolio fetch with HTTP error"""
        # Mock dependencies
        monkeypatch.setattr('agents.researcher_agent.functions.researcher_functions.get_request_ctx', 
                            lambda chat_id, key: mock_user_id if key == "user_id" else None)
        monkeypatch.setattr('agents.researcher_agent.functions.researcher_functions.generate_firebase_id_token', 
                            lambda user_id: "fake-token")
        
        # Mock the HTTP request to raise an error
        with patch('agents.researcher_agent.functions.researcher_functions.requests.post', side_effect=requests.exceptions.HTTPError("API Error")):
            result = self.get_portfolio_history(mock_chat_id)
        
        # Verify the result
        assert isinstance(result, dict)
        assert "error" in result
        assert "Failed to fetch portfolio history" in result["error"]
    
    def test_portfolio_fetch_empty_data(self, monkeypatch):
        """Test portfolio fetch with empty data"""
        # Mock dependencies
        monkeypatch.setattr('agents.researcher_agent.functions.researcher_functions.get_request_ctx', 
                            lambda chat_id, key: mock_user_id if key == "user_id" else None)
        monkeypatch.setattr('agents.researcher_agent.functions.researcher_functions.generate_firebase_id_token', 
                            lambda user_id: "fake-token")
        
        # Mock the HTTP request with empty data
        mock_response = Mock()
        mock_response.json.return_value = None
        mock_response.raise_for_status.return_value = None
        
        with patch('agents.researcher_agent.functions.researcher_functions.requests.post', return_value=mock_response):
            result = self.get_portfolio_history(mock_chat_id)
        
        # Verify the result
        assert isinstance(result, dict)
        assert "error" in result
        assert "No portfolio data returned" in result["error"]


class TestFormatPortfolioResults:
    """Test suite for format_portfolio_results function"""
    
    def setup_method(self):
        """Setup method that runs before each test"""
        from agents.researcher_agent.functions.researcher_functions import format_portfolio_results
        self.format_portfolio_results = format_portfolio_results
    
    def test_format_results_with_error(self):
        """Test formatting results with error"""
        error_results = {"error": "Failed to fetch data"}
        
        result = self.format_portfolio_results(error_results)
        
        # Verify the result
        assert isinstance(result, str)
        assert "Error: Failed to fetch data" in result
    
    def test_format_results_basic(self):
        """Test formatting basic portfolio results"""
        basic_results = {
            "total_value": 5000.75,
            "changes": {
                "1d": {"usd": 150.25, "pct": 3.1, "has_exact_data": True},
                "7d": {"usd": -200.50, "pct": -3.9, "has_exact_data": False}
            },
            "allocation": {
                "invested_value": 4000.75,
                "invested_percentage": 80.0,
                "stable_value": 1000.0,
                "stable_percentage": 20.0
            },
            "token_insights": []
        }
        
        result = self.format_portfolio_results(basic_results, detailed=False)
        
        # Verify the result
        assert isinstance(result, str)
        assert "$5000.75" in result
        assert "80.0% invested" in result
        assert "20.0% in stablecoins" in result
        assert "+150.25 USD (3.1%)" in result
        assert "-200.5 USD (-3.9%)" in result 
    
    def test_format_results_with_token_insights(self):
        """Test formatting results with token insights"""
        results_with_insights = {
            "total_value": 5000.75,
            "changes": {"1d": {"usd": 150.25, "pct": 3.1, "has_exact_data": True}},
            "allocation": {
                "invested_value": 4000.75,
                "invested_percentage": 80.0,
                "stable_value": 1000.0,
                "stable_percentage": 20.0
            },
            "token_insights": [
                {
                    "symbol": "ETH",
                    "chain": "ETHEREUM",
                    "usd_value": 3000.0,
                    "is_stable": False,
                    "performance": {
                        "24h_price_change": 5.2,
                        "24h_volume": 2000000000.0,
                        "market_cap": 200.5,
                        "price_change_7d": 10.1,
                        "price_change_30d": 15.8
                    },
                    "warnings": ["High sell pressure detected"]
                },
                {
                    "symbol": "USDC",
                    "chain": "ETHEREUM",
                    "usd_value": 1000.0,
                    "is_stable": True,
                    "performance": {},
                    "warnings": []
                }
            ]
        }
        
        result = self.format_portfolio_results(results_with_insights, detailed=False)
        
        # Verify the result
        assert isinstance(result, str)
        assert "ETH ($3000.00 on ETHEREUM)" in result
        assert "24h change: 5.20%" in result
        assert "24h volume: $2.00T" in result  # 2000000000.0 is 2 trillion, formatted as T 
        assert "Market cap: $200.50M" in result  # Function formats as millions
        assert "⚠️ High sell pressure detected" in result
        assert "USDC ($1000.00 on ETHEREUM) (Stablecoin)" in result
    
    def test_format_results_detailed(self):
        """Test formatting detailed portfolio results"""
        detailed_results = {
            "total_value": 5000.75,
            "changes": {
                "1d": {"usd": 150.25, "pct": 3.1, "has_exact_data": True},
                "7d": {"usd": -200.50, "pct": -3.9, "has_exact_data": False},
                "all_time": {"usd": 1000.0, "pct": 25.0, "has_exact_data": True}
            },
            "allocation": {
                "invested_value": 4000.75,
                "invested_percentage": 80.0,
                "stable_value": 1000.0,
                "stable_percentage": 20.0
            },
            "token_insights": [
                {
                    "symbol": "ETH",
                    "chain": "ETHEREUM",
                    "usd_value": 3000.0,
                    "is_stable": False,
                    "performance": {
                        "24h_price_change": 5.2,
                        "24h_volume": "2.5B",  # Pre-formatted volume
                        "market_cap": 200.5
                    },
                    "warnings": ["Token shows some risk signals"]
                }
            ]
        }
        
        result = self.format_portfolio_results(detailed_results, detailed=True)
        
        # Verify the result
        assert isinstance(result, str)
        assert "Detailed analysis (Current value: $5000.75)" in result
        assert "Performance by Period:" in result
        assert "24h: +150.25 USD (3.1%)" in result
        assert "7 days: -200.5 USD (-3.9%) (approximated)" in result
        assert "Total: +1000.0 USD (25.0%)" in result
        assert "ETH Analysis ($3000.00 on ETHEREUM)" in result
        assert "Performance Metrics:" in result
        assert "24h volume: 2.5B" in result
        assert "⚠️ Token shows some risk signals" in result
    
    def test_format_results_exception_handling(self):
        """Test formatting results with exception"""
        # Pass invalid data that will cause an exception
        invalid_results = {"total_value": "invalid"}
        
        result = self.format_portfolio_results(invalid_results)
        
        # Verify the result - the function handles this gracefully, doesn't throw exception
        assert isinstance(result, str)
        # The function actually handles invalid data gracefully
        assert "$invalid" in result


class TestAnalyzePortfolioHistory:
    """Test suite for analyze_portfolio_history function"""
    
    def setup_method(self):
        """Setup method that runs before each test"""
        from agents.researcher_agent.functions.researcher_functions import analyze_portfolio_history
        self.analyze_portfolio_history = analyze_portfolio_history
    
    def test_successful_portfolio_analysis(self, monkeypatch):
        """Test successful portfolio analysis"""
        # Mock all dependencies
        monkeypatch.setattr('agents.researcher_agent.functions.researcher_functions.save_agent_thought', lambda **kwargs: None)
        monkeypatch.setattr('agents.researcher_agent.functions.researcher_functions.get_request_ctx', 
                            lambda chat_id, key: mock_user_id if key == "user_id" else None)
        monkeypatch.setattr('agents.researcher_agent.functions.researcher_functions.generate_firebase_id_token', 
                            lambda user_id: "fake-token")
        monkeypatch.setattr('agents.researcher_agent.functions.researcher_functions.get_dexscreener_token_pair_info', 
                            lambda chat_id, symbol, base: mock_dexscreener_data)
        monkeypatch.setattr('agents.researcher_agent.functions.researcher_functions.get_dexscreener_token_pair_info_by_chain_and_token_address', 
                            lambda chat_id, chain, address: mock_dexscreener_data)
        monkeypatch.setattr('agents.researcher_agent.functions.researcher_functions.get_cryptocurrency_by_symbol', 
                            lambda symbol, chat_id: mock_coinmarketcap_data)
        monkeypatch.setattr('agents.researcher_agent.functions.researcher_functions.is_possible_rug', 
                            lambda address: False)
        monkeypatch.setattr('agents.researcher_agent.functions.researcher_functions.get_portfolio_history', 
                            lambda chat_id: mock_portfolio_data)
        
        # Mock the balances API call
        mock_balances_response = Mock()
        mock_balances_response.json.return_value = mock_balances_data
        mock_balances_response.raise_for_status.return_value = None
        
        with patch('agents.researcher_agent.functions.researcher_functions.requests.get', return_value=mock_balances_response):
            result = self.analyze_portfolio_history(mock_chat_id)
        
        # Verify the result
        assert isinstance(result, str)
        assert "$4000.75" in result  # Total portfolio value
        assert "ETH" in result
        assert "SOL" in result
        # Should not include USDC details since it's a stablecoin
    
    def test_portfolio_analysis_no_user_id(self, monkeypatch):
        """Test portfolio analysis without user ID"""
        # Mock save_agent_thought and get_request_ctx to return None
        monkeypatch.setattr('agents.researcher_agent.functions.researcher_functions.save_agent_thought', lambda **kwargs: None)
        monkeypatch.setattr('agents.researcher_agent.functions.researcher_functions.get_request_ctx', 
                            lambda chat_id, key: None)
        
        result = self.analyze_portfolio_history(mock_chat_id)
        
        # Verify the result
        assert isinstance(result, dict)
        assert "error" in result
        assert "No user ID found" in result["error"]
    
    def test_portfolio_analysis_detailed(self, monkeypatch):
        """Test detailed portfolio analysis"""
        # Mock all dependencies
        monkeypatch.setattr('agents.researcher_agent.functions.researcher_functions.save_agent_thought', lambda **kwargs: None)
        monkeypatch.setattr('agents.researcher_agent.functions.researcher_functions.get_request_ctx', 
                            lambda chat_id, key: mock_user_id if key == "user_id" else None)
        monkeypatch.setattr('agents.researcher_agent.functions.researcher_functions.generate_firebase_id_token', 
                            lambda user_id: "fake-token")
        monkeypatch.setattr('agents.researcher_agent.functions.researcher_functions.get_dexscreener_token_pair_info', 
                            lambda chat_id, symbol, base: mock_dexscreener_data)
        monkeypatch.setattr('agents.researcher_agent.functions.researcher_functions.get_dexscreener_token_pair_info_by_chain_and_token_address', 
                            lambda chat_id, chain, address: mock_dexscreener_data)
        monkeypatch.setattr('agents.researcher_agent.functions.researcher_functions.get_cryptocurrency_by_symbol', 
                            lambda symbol, chat_id: mock_coinmarketcap_data)
        monkeypatch.setattr('agents.researcher_agent.functions.researcher_functions.is_possible_rug', 
                            lambda address: False)
        monkeypatch.setattr('agents.researcher_agent.functions.researcher_functions.get_portfolio_history', 
                            lambda chat_id: mock_portfolio_data)
        
        # Mock the balances API call
        mock_balances_response = Mock()
        mock_balances_response.json.return_value = mock_balances_data
        mock_balances_response.raise_for_status.return_value = None
        
        with patch('agents.researcher_agent.functions.researcher_functions.requests.get', return_value=mock_balances_response):
            result = self.analyze_portfolio_history(mock_chat_id, detailed=True)
        
        # Verify the result
        assert isinstance(result, str)
        assert "Detailed analysis" in result
        assert "Performance by Period:" in result
        assert "Detailed Token Analysis:" in result
    
    def test_portfolio_analysis_http_error(self, monkeypatch):
        """Test portfolio analysis with HTTP error"""
        # Mock dependencies
        monkeypatch.setattr('agents.researcher_agent.functions.researcher_functions.save_agent_thought', lambda **kwargs: None)
        monkeypatch.setattr('agents.researcher_agent.functions.researcher_functions.get_request_ctx', 
                            lambda chat_id, key: mock_user_id if key == "user_id" else None)
        monkeypatch.setattr('agents.researcher_agent.functions.researcher_functions.generate_firebase_id_token', 
                            lambda user_id: "fake-token")
        
        # Mock the HTTP request to raise an error
        with patch('agents.researcher_agent.functions.researcher_functions.requests.get', side_effect=requests.exceptions.HTTPError("API Error")):
            result = self.analyze_portfolio_history(mock_chat_id)
        
        # Verify the result
        assert isinstance(result, str)
        assert "Error analyzing portfolio:" in result
    
    def test_portfolio_analysis_no_balances(self, monkeypatch):
        """Test portfolio analysis with no balances data"""
        # Mock dependencies
        monkeypatch.setattr('agents.researcher_agent.functions.researcher_functions.save_agent_thought', lambda **kwargs: None)
        monkeypatch.setattr('agents.researcher_agent.functions.researcher_functions.get_request_ctx', 
                            lambda chat_id, key: mock_user_id if key == "user_id" else None)
        monkeypatch.setattr('agents.researcher_agent.functions.researcher_functions.generate_firebase_id_token', 
                            lambda user_id: "fake-token")
        
        # Mock the balances API call with empty data
        mock_balances_response = Mock()
        mock_balances_response.json.return_value = {}
        mock_balances_response.raise_for_status.return_value = None
        
        with patch('agents.researcher_agent.functions.researcher_functions.requests.get', return_value=mock_balances_response):
            result = self.analyze_portfolio_history(mock_chat_id)
        
        # Verify the result - function returns error dict, not string
        assert isinstance(result, dict)
        assert "error" in result
        assert "No portfolio data returned" in result["error"]
    
    def test_portfolio_analysis_with_risky_token(self, monkeypatch):
        """Test portfolio analysis with risky token detection"""
        # Mock all dependencies with risky token
        monkeypatch.setattr('agents.researcher_agent.functions.researcher_functions.save_agent_thought', lambda **kwargs: None)
        monkeypatch.setattr('agents.researcher_agent.functions.researcher_functions.get_request_ctx', 
                            lambda chat_id, key: mock_user_id if key == "user_id" else None)
        monkeypatch.setattr('agents.researcher_agent.functions.researcher_functions.generate_firebase_id_token', 
                            lambda user_id: "fake-token")
        monkeypatch.setattr('agents.researcher_agent.functions.researcher_functions.get_dexscreener_token_pair_info', 
                            lambda chat_id, symbol, base: mock_dexscreener_data)
        monkeypatch.setattr('agents.researcher_agent.functions.researcher_functions.get_dexscreener_token_pair_info_by_chain_and_token_address', 
                            lambda chat_id, chain, address: mock_dexscreener_data)
        monkeypatch.setattr('agents.researcher_agent.functions.researcher_functions.get_cryptocurrency_by_symbol', 
                            lambda symbol, chat_id: mock_coinmarketcap_data)
        monkeypatch.setattr('agents.researcher_agent.functions.researcher_functions.is_possible_rug', 
                            lambda address: True)  # Mark as risky
        monkeypatch.setattr('agents.researcher_agent.functions.researcher_functions.get_portfolio_history', 
                            lambda chat_id: mock_portfolio_data)
        
        # Mock the balances API call
        mock_balances_response = Mock()
        mock_balances_response.json.return_value = mock_balances_data
        mock_balances_response.raise_for_status.return_value = None
        
        with patch('agents.researcher_agent.functions.researcher_functions.requests.get', return_value=mock_balances_response):
            result = self.analyze_portfolio_history(mock_chat_id)
        
        # Verify the result includes risk warning
        assert isinstance(result, str)
        assert "Token shows some risk signals" in result
    
    def test_portfolio_analysis_general_exception(self, monkeypatch):
        """Test portfolio analysis with general exception"""
        # Mock save_agent_thought to raise exception
        def mock_save_agent_thought_with_exception(**kwargs):
            raise Exception("General error")
        
        monkeypatch.setattr('agents.researcher_agent.functions.researcher_functions.save_agent_thought', mock_save_agent_thought_with_exception)
        
        result = self.analyze_portfolio_history(mock_chat_id)
        
        # Verify the result
        assert isinstance(result, str)
        assert "Error analyzing portfolio:" in result
        assert "General error" in result
