# tests/agents/researcher_agent/test_defi_llama_functions.py
import sys
import types
from unittest.mock import Mock, patch
import pytest
import requests

# Add the current directory to Python path so we can import the modules
sys.path.insert(0, '.')

# Mock data for testing
mock_protocols_data = [
    {
        "name": "Uniswap",
        "tvl": 5000000000.0,
        "url": "https://uniswap.org",
        "description": "Decentralized exchange protocol",
        "category": "Dexes",
        "logo": "https://example.com/uniswap.png",
        "chains": ["Ethereum", "Polygon", "Arbitrum"]
    },
    {
        "name": "Aave",
        "tvl": 8000000000.0,
        "url": "https://aave.com",
        "description": "Lending protocol",
        "category": "Lending",
        "logo": "https://example.com/aave.png",
        "chains": ["Ethereum", "Polygon"]
    },
    {
        "name": "Compound",
        "tvl": 3000000000.0,
        "url": "https://compound.finance",
        "description": "Lending protocol",
        "category": "Lending",
        "logo": "https://example.com/compound.png",
        "chains": ["Ethereum"]
    }
]

mock_chains_data = [
    {"name": "Ethereum", "tvl": 50000000000.0},
    {"name": "BSC", "tvl": 8000000000.0},
    {"name": "Polygon", "tvl": 5000000000.0},
    {"name": "Solana", "tvl": 4000000000.0},
    {"name": "Arbitrum", "tvl": 3000000000.0}
]

mock_dexs_data = {
    "protocols": [
        {
            "name": "Uniswap",
            "logo": "https://example.com/uniswap.png",
            "chains": ["Ethereum", "Polygon"],
            "total24h": 1000000000.0,
            "total7d": 7000000000.0,
            "total30d": 30000000000.0
        },
        {
            "name": "PancakeSwap",
            "logo": "https://example.com/pancake.png",
            "chains": ["BSC", "Ethereum"],
            "total24h": 500000000.0,
            "total7d": 3500000000.0,
            "total30d": 15000000000.0
        },
        {
            "name": "SushiSwap",
            "logo": "https://example.com/sushi.png",
            "chains": ["Ethereum", "Polygon"],
            "total24h": 300000000.0,
            "total7d": 2100000000.0,
            "total30d": 9000000000.0
        }
    ]
}

mock_yields_data = {
    "data": [
        {
            "project": "Aave",
            "symbol": "USDC",
            "chain": "Ethereum",
            "tvlUsd": 500000000.0,
            "apyPct1D": 5.5,
            "apyPct7D": 5.2,
            "apyPct30D": 5.0,
            "ilRisk": "no"
        },
        {
            "project": "Compound",
            "symbol": "DAI",
            "chain": "Ethereum",
            "tvlUsd": 300000000.0,
            "apyPct1D": 4.8,
            "apyPct7D": 4.5,
            "apyPct30D": 4.2,
            "ilRisk": "no"
        },
        {
            "project": "Uniswap V3",
            "symbol": "ETH-USDC",
            "chain": "Ethereum",
            "tvlUsd": 200000000.0,
            "apyPct1D": 8.2,
            "apyPct7D": 7.8,
            "apyPct30D": 7.5,
            "ilRisk": "yes"
        },
        {
            "project": "QuickSwap",
            "symbol": "MATIC-USDC",
            "chain": "Polygon",
            "tvlUsd": 150000000.0,
            "apyPct1D": 12.5,
            "apyPct7D": 11.8,
            "apyPct30D": 11.2,
            "ilRisk": "yes"
        },
        {
            "project": "Low TVL Pool",
            "symbol": "TEST-TOKEN",
            "chain": "Ethereum",
            "tvlUsd": 50000.0,  # Below 100k threshold
            "apyPct1D": 20.0,
            "apyPct7D": 18.0,
            "apyPct30D": 15.0,
            "ilRisk": "yes"
        }
    ]
}

mock_chat_id = "test-chat-123"


class TestGetTopProtocolsByChain:
    """Test suite for get_top_protocols_by_chain_on_defi_llama function"""
    
    def setup_method(self):
        """Setup method that runs before each test"""
        from agents.researcher_agent.functions.defi_llama_functions import get_top_protocols_by_chain_on_defi_llama
        self.get_top_protocols_by_chain = get_top_protocols_by_chain_on_defi_llama
    
    def test_successful_get_protocols_default_limit(self, monkeypatch):
        """Test successful protocols retrieval with default limit"""
        # Mock dependencies
        monkeypatch.setattr('agents.researcher_agent.functions.defi_llama_functions.save_agent_thought', lambda **kwargs: None)
        monkeypatch.setattr('agents.researcher_agent.functions.defi_llama_functions.save_ui_message', lambda **kwargs: None)
        
        # Mock the HTTP request
        mock_response = Mock()
        mock_response.json.return_value = mock_protocols_data
        mock_response.raise_for_status.return_value = None
        
        with patch('agents.researcher_agent.functions.defi_llama_functions.requests.get', return_value=mock_response):
            result = self.get_top_protocols_by_chain("Ethereum", mock_chat_id)
        
        # Verify the result
        assert isinstance(result, list)
        assert len(result) == 3  # All protocols support Ethereum
        assert "Aave" in result  # Should be first due to highest TVL
        assert "Uniswap" in result
        assert "Compound" in result
    
    def test_successful_get_protocols_custom_limit(self, monkeypatch):
        """Test successful protocols retrieval with custom limit"""
        # Mock dependencies
        monkeypatch.setattr('agents.researcher_agent.functions.defi_llama_functions.save_agent_thought', lambda **kwargs: None)
        monkeypatch.setattr('agents.researcher_agent.functions.defi_llama_functions.save_ui_message', lambda **kwargs: None)
        
        # Mock the HTTP request
        mock_response = Mock()
        mock_response.json.return_value = mock_protocols_data
        mock_response.raise_for_status.return_value = None
        
        with patch('agents.researcher_agent.functions.defi_llama_functions.requests.get', return_value=mock_response):
            result = self.get_top_protocols_by_chain("Ethereum", mock_chat_id, limit=2)
        
        # Verify the result
        assert isinstance(result, list)
        assert len(result) == 2  # Limited to 2
    
    def test_get_protocols_chain_not_found(self, monkeypatch):
        """Test protocols retrieval for chain with no protocols"""
        # Mock dependencies
        monkeypatch.setattr('agents.researcher_agent.functions.defi_llama_functions.save_agent_thought', lambda **kwargs: None)
        monkeypatch.setattr('agents.researcher_agent.functions.defi_llama_functions.save_ui_message', lambda **kwargs: None)
        
        # Mock the HTTP request
        mock_response = Mock()
        mock_response.json.return_value = mock_protocols_data
        mock_response.raise_for_status.return_value = None
        
        with patch('agents.researcher_agent.functions.defi_llama_functions.requests.get', return_value=mock_response):
            result = self.get_top_protocols_by_chain("NonExistentChain", mock_chat_id)
        
        # Verify the result
        assert result == "No protocols found on NonExistentChain."
    
    def test_get_protocols_http_error(self, monkeypatch):
        """Test protocols retrieval with HTTP error"""
        # Mock dependencies
        monkeypatch.setattr('agents.researcher_agent.functions.defi_llama_functions.save_agent_thought', lambda **kwargs: None)
        
        # Mock the HTTP request to raise an error
        with patch('agents.researcher_agent.functions.defi_llama_functions.requests.get', side_effect=requests.exceptions.HTTPError("API Error")):
            result = self.get_top_protocols_by_chain("Ethereum", mock_chat_id)
        
        # Verify the result
        assert result == "There was an error fetching the top protocols by chain, try again later."
    
    def test_get_protocols_general_exception(self, monkeypatch):
        """Test protocols retrieval with general exception"""
        # Mock dependencies
        monkeypatch.setattr('agents.researcher_agent.functions.defi_llama_functions.save_agent_thought', lambda **kwargs: None)
        
        # Mock the HTTP request to raise a general error
        with patch('agents.researcher_agent.functions.defi_llama_functions.requests.get', side_effect=Exception("General error")):
            result = self.get_top_protocols_by_chain("Ethereum", mock_chat_id)
        
        # Verify the result
        assert result == "There was an error fetching the top protocols by chain, try again later."
    
    def test_get_protocols_case_insensitive_chain(self, monkeypatch):
        """Test protocols retrieval with case insensitive chain matching"""
        # Mock dependencies
        monkeypatch.setattr('agents.researcher_agent.functions.defi_llama_functions.save_agent_thought', lambda **kwargs: None)
        monkeypatch.setattr('agents.researcher_agent.functions.defi_llama_functions.save_ui_message', lambda **kwargs: None)
        
        # Mock the HTTP request
        mock_response = Mock()
        mock_response.json.return_value = mock_protocols_data
        mock_response.raise_for_status.return_value = None
        
        with patch('agents.researcher_agent.functions.defi_llama_functions.requests.get', return_value=mock_response):
            result = self.get_top_protocols_by_chain("ethereum", mock_chat_id)  # lowercase
        
        # Verify the result
        assert isinstance(result, list)
        assert len(result) == 3  # Should still find Ethereum protocols
    
    def test_get_protocols_limit_enforcement(self, monkeypatch):
        """Test that limit is enforced to maximum of 10"""
        # Mock dependencies
        monkeypatch.setattr('agents.researcher_agent.functions.defi_llama_functions.save_agent_thought', lambda **kwargs: None)
        monkeypatch.setattr('agents.researcher_agent.functions.defi_llama_functions.save_ui_message', lambda **kwargs: None)
        
        # Mock the HTTP request
        mock_response = Mock()
        mock_response.json.return_value = mock_protocols_data
        mock_response.raise_for_status.return_value = None
        
        with patch('agents.researcher_agent.functions.defi_llama_functions.requests.get', return_value=mock_response):
            result = self.get_top_protocols_by_chain("Ethereum", mock_chat_id, limit=15)  # More than 10
        
        # Verify the result - should be limited to available protocols (3 in this case)
        assert isinstance(result, list)
        assert len(result) <= 10


class TestGetTopChainsByTvl:
    """Test suite for get_top_chains_by_tvl_on_defi_llama function"""
    
    def setup_method(self):
        """Setup method that runs before each test"""
        from agents.researcher_agent.functions.defi_llama_functions import get_top_chains_by_tvl_on_defi_llama
        self.get_top_chains_by_tvl = get_top_chains_by_tvl_on_defi_llama
    
    def test_successful_get_chains_default_limit(self, monkeypatch):
        """Test successful chains retrieval with default limit"""
        # Mock dependencies
        monkeypatch.setattr('agents.researcher_agent.functions.defi_llama_functions.save_agent_thought', lambda **kwargs: None)
        
        # Mock the HTTP request
        mock_response = Mock()
        mock_response.json.return_value = mock_chains_data
        mock_response.raise_for_status.return_value = None
        
        with patch('agents.researcher_agent.functions.defi_llama_functions.requests.get', return_value=mock_response):
            result = self.get_top_chains_by_tvl(mock_chat_id)
        
        # Verify the result
        assert isinstance(result, str)
        assert "Top 10 chains and TVLs are:" in result  # Function uses min(limit, 10) but shows actual count
        assert "Ethereum" in result  # Should be first due to highest TVL
    
    def test_successful_get_chains_custom_limit(self, monkeypatch):
        """Test successful chains retrieval with custom limit"""
        # Mock dependencies
        monkeypatch.setattr('agents.researcher_agent.functions.defi_llama_functions.save_agent_thought', lambda **kwargs: None)
        
        # Mock the HTTP request
        mock_response = Mock()
        mock_response.json.return_value = mock_chains_data
        mock_response.raise_for_status.return_value = None
        
        with patch('agents.researcher_agent.functions.defi_llama_functions.requests.get', return_value=mock_response):
            result = self.get_top_chains_by_tvl(mock_chat_id, limit=3)
        
        # Verify the result
        assert isinstance(result, str)
        assert "Top 3 chains and TVLs are:" in result
    
    def test_get_chains_empty_response(self, monkeypatch):
        """Test chains retrieval with empty response"""
        # Mock dependencies
        monkeypatch.setattr('agents.researcher_agent.functions.defi_llama_functions.save_agent_thought', lambda **kwargs: None)
        
        # Mock the HTTP request with empty response
        mock_response = Mock()
        mock_response.json.return_value = []
        mock_response.raise_for_status.return_value = None
        
        with patch('agents.researcher_agent.functions.defi_llama_functions.requests.get', return_value=mock_response):
            result = self.get_top_chains_by_tvl(mock_chat_id)
        
        # Verify the result
        assert result == "Could not find any chains by TVL on DeFiLlama."
    
    def test_get_chains_http_error(self, monkeypatch):
        """Test chains retrieval with HTTP error"""
        # Mock dependencies
        monkeypatch.setattr('agents.researcher_agent.functions.defi_llama_functions.save_agent_thought', lambda **kwargs: None)
        
        # Mock the HTTP request to raise an error
        with patch('agents.researcher_agent.functions.defi_llama_functions.requests.get', side_effect=requests.exceptions.HTTPError("API Error")):
            result = self.get_top_chains_by_tvl(mock_chat_id)
        
        # Verify the result
        assert result == "There was an error fetching the top chains by TVL, try again later."
    
    def test_get_chains_limit_enforcement(self, monkeypatch):
        """Test that limit is enforced to maximum of 10"""
        # Mock dependencies
        monkeypatch.setattr('agents.researcher_agent.functions.defi_llama_functions.save_agent_thought', lambda **kwargs: None)
        
        # Mock the HTTP request
        mock_response = Mock()
        mock_response.json.return_value = mock_chains_data
        mock_response.raise_for_status.return_value = None
        
        with patch('agents.researcher_agent.functions.defi_llama_functions.requests.get', return_value=mock_response):
            result = self.get_top_chains_by_tvl(mock_chat_id, limit=15)  # More than 10
        
        # Verify the result - should mention the actual available chains (5 in this case)
        assert isinstance(result, str)
        assert "Top 10 chains and TVLs are:" in result


class TestGetTopDexsByChain:
    """Test suite for get_top_dexs_by_chain_on_defi_llama function"""
    
    def setup_method(self):
        """Setup method that runs before each test"""
        from agents.researcher_agent.functions.defi_llama_functions import get_top_dexs_by_chain_on_defi_llama
        self.get_top_dexs_by_chain = get_top_dexs_by_chain_on_defi_llama
    
    def test_successful_get_dexs_default_limit(self, monkeypatch):
        """Test successful DEXs retrieval with default limit"""
        # Mock dependencies
        monkeypatch.setattr('agents.researcher_agent.functions.defi_llama_functions.save_agent_thought', lambda **kwargs: None)
        monkeypatch.setattr('agents.researcher_agent.functions.defi_llama_functions.save_ui_message', lambda **kwargs: None)
        
        # Mock the HTTP request
        mock_response = Mock()
        mock_response.json.return_value = mock_dexs_data
        mock_response.raise_for_status.return_value = None
        
        with patch('agents.researcher_agent.functions.defi_llama_functions.requests.get', return_value=mock_response):
            result = self.get_top_dexs_by_chain("Ethereum", mock_chat_id)
        
        # Verify the result
        assert isinstance(result, list)
        assert len(result) == 3  # Uniswap, PancakeSwap and SushiSwap support Ethereum
        assert "Uniswap" in result  # Should be first due to highest volume
        assert "PancakeSwap" in result
        assert "SushiSwap" in result
    
    def test_successful_get_dexs_custom_limit(self, monkeypatch):
        """Test successful DEXs retrieval with custom limit"""
        # Mock dependencies
        monkeypatch.setattr('agents.researcher_agent.functions.defi_llama_functions.save_agent_thought', lambda **kwargs: None)
        monkeypatch.setattr('agents.researcher_agent.functions.defi_llama_functions.save_ui_message', lambda **kwargs: None)
        
        # Mock the HTTP request
        mock_response = Mock()
        mock_response.json.return_value = mock_dexs_data
        mock_response.raise_for_status.return_value = None
        
        with patch('agents.researcher_agent.functions.defi_llama_functions.requests.get', return_value=mock_response):
            result = self.get_top_dexs_by_chain("Ethereum", mock_chat_id, limit=1)
        
        # Verify the result
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0] == "Uniswap"  # Highest volume DEX
    
    def test_get_dexs_chain_not_found(self, monkeypatch):
        """Test DEXs retrieval for chain with no DEXs"""
        # Mock dependencies
        monkeypatch.setattr('agents.researcher_agent.functions.defi_llama_functions.save_agent_thought', lambda **kwargs: None)
        monkeypatch.setattr('agents.researcher_agent.functions.defi_llama_functions.save_ui_message', lambda **kwargs: None)
        
        # Mock the HTTP request
        mock_response = Mock()
        mock_response.json.return_value = mock_dexs_data
        mock_response.raise_for_status.return_value = None
        
        with patch('agents.researcher_agent.functions.defi_llama_functions.requests.get', return_value=mock_response):
            result = self.get_top_dexs_by_chain("NonExistentChain", mock_chat_id)
        
        # Verify the result
        assert result == "Could not find any DEXs on NonExistentChain."
    
    def test_get_dexs_http_error(self, monkeypatch):
        """Test DEXs retrieval with HTTP error"""
        # Mock dependencies
        monkeypatch.setattr('agents.researcher_agent.functions.defi_llama_functions.save_agent_thought', lambda **kwargs: None)
        
        # Mock the HTTP request to raise an error
        with patch('agents.researcher_agent.functions.defi_llama_functions.requests.get', side_effect=requests.exceptions.HTTPError("API Error")):
            result = self.get_top_dexs_by_chain("Ethereum", mock_chat_id)
        
        # Verify the result
        assert result == "There was an error fetching the top DEXs by chain, try again later."
    
    def test_get_dexs_missing_total7d(self, monkeypatch):
        """Test DEXs retrieval with protocols missing total7d field"""
        # Mock dependencies
        monkeypatch.setattr('agents.researcher_agent.functions.defi_llama_functions.save_agent_thought', lambda **kwargs: None)
        monkeypatch.setattr('agents.researcher_agent.functions.defi_llama_functions.save_ui_message', lambda **kwargs: None)
        
        # Create mock data with missing total7d
        mock_dexs_incomplete = {
            "protocols": [
                {
                    "name": "IncompleteDEX",
                    "logo": "https://example.com/incomplete.png",
                    "chains": ["Ethereum"],
                    "total24h": 1000000000.0,
                    # Missing total7d field
                    "total30d": 30000000000.0
                }
            ]
        }
        
        # Mock the HTTP request
        mock_response = Mock()
        mock_response.json.return_value = mock_dexs_incomplete
        mock_response.raise_for_status.return_value = None
        
        with patch('agents.researcher_agent.functions.defi_llama_functions.requests.get', return_value=mock_response):
            result = self.get_top_dexs_by_chain("Ethereum", mock_chat_id)
        
        # Verify the result - should filter out protocols without total7d
        assert result == "Could not find any DEXs on Ethereum."
    
    def test_get_dexs_case_insensitive_chain(self, monkeypatch):
        """Test DEXs retrieval with case insensitive chain matching"""
        # Mock dependencies
        monkeypatch.setattr('agents.researcher_agent.functions.defi_llama_functions.save_agent_thought', lambda **kwargs: None)
        monkeypatch.setattr('agents.researcher_agent.functions.defi_llama_functions.save_ui_message', lambda **kwargs: None)
        
        # Mock the HTTP request
        mock_response = Mock()
        mock_response.json.return_value = mock_dexs_data
        mock_response.raise_for_status.return_value = None
        
        with patch('agents.researcher_agent.functions.defi_llama_functions.requests.get', return_value=mock_response):
            result = self.get_top_dexs_by_chain("ethereum", mock_chat_id)  # lowercase
        
        # Verify the result
        assert isinstance(result, list)
        assert len(result) == 3  # Should still find Ethereum DEXs


class TestGetTopYieldsPoolsByChain:
    """Test suite for get_top_yields_pools_by_chain_on_defi_llama function"""
    
    def setup_method(self):
        """Setup method that runs before each test"""
        from agents.researcher_agent.functions.defi_llama_functions import get_top_yields_pools_by_chain_on_defi_llama
        self.get_top_yields_pools = get_top_yields_pools_by_chain_on_defi_llama
    
    def test_successful_get_yields_default_limit(self, monkeypatch):
        """Test successful yields pools retrieval with default limit"""
        # Mock dependencies
        monkeypatch.setattr('agents.researcher_agent.functions.defi_llama_functions.save_agent_thought', lambda **kwargs: None)
        monkeypatch.setattr('agents.researcher_agent.functions.defi_llama_functions.save_ui_message', lambda **kwargs: None)
        
        # Mock the HTTP request
        mock_response = Mock()
        mock_response.json.return_value = mock_yields_data
        mock_response.raise_for_status.return_value = None
        
        with patch('agents.researcher_agent.functions.defi_llama_functions.requests.get', return_value=mock_response):
            result = self.get_top_yields_pools("Ethereum", mock_chat_id)
        
        # Verify the result
        assert isinstance(result, list)
        assert len(result) == 3  # 3 Ethereum pools with TVL > 100k
        # Should be sorted by APY (highest first)
        assert result[0]["project"] == "Uniswap V3"  # Highest APY (8.2%)
        assert result[1]["project"] == "Aave"  # Second highest APY (5.5%)
        assert result[2]["project"] == "Compound"  # Third highest APY (4.8%)
    
    def test_successful_get_yields_custom_limit(self, monkeypatch):
        """Test successful yields pools retrieval with custom limit"""
        # Mock dependencies
        monkeypatch.setattr('agents.researcher_agent.functions.defi_llama_functions.save_agent_thought', lambda **kwargs: None)
        monkeypatch.setattr('agents.researcher_agent.functions.defi_llama_functions.save_ui_message', lambda **kwargs: None)
        
        # Mock the HTTP request
        mock_response = Mock()
        mock_response.json.return_value = mock_yields_data
        mock_response.raise_for_status.return_value = None
        
        with patch('agents.researcher_agent.functions.defi_llama_functions.requests.get', return_value=mock_response):
            result = self.get_top_yields_pools("Ethereum", mock_chat_id, limit=2)
        
        # Verify the result
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["project"] == "Uniswap V3"  # Highest APY
    
    def test_get_yields_chain_not_found(self, monkeypatch):
        """Test yields pools retrieval for chain with no pools"""
        # Mock dependencies
        monkeypatch.setattr('agents.researcher_agent.functions.defi_llama_functions.save_agent_thought', lambda **kwargs: None)
        monkeypatch.setattr('agents.researcher_agent.functions.defi_llama_functions.save_ui_message', lambda **kwargs: None)
        
        # Mock the HTTP request
        mock_response = Mock()
        mock_response.json.return_value = mock_yields_data
        mock_response.raise_for_status.return_value = None
        
        with patch('agents.researcher_agent.functions.defi_llama_functions.requests.get', return_value=mock_response):
            result = self.get_top_yields_pools("NonExistentChain", mock_chat_id)
        
        # Verify the result
        assert result == "Could not find any pools on NonExistentChain."
    
    def test_get_yields_tvl_filtering(self, monkeypatch):
        """Test that pools with TVL < 100k are filtered out"""
        # Mock dependencies
        monkeypatch.setattr('agents.researcher_agent.functions.defi_llama_functions.save_agent_thought', lambda **kwargs: None)
        monkeypatch.setattr('agents.researcher_agent.functions.defi_llama_functions.save_ui_message', lambda **kwargs: None)
        
        # Mock the HTTP request
        mock_response = Mock()
        mock_response.json.return_value = mock_yields_data
        mock_response.raise_for_status.return_value = None
        
        with patch('agents.researcher_agent.functions.defi_llama_functions.requests.get', return_value=mock_response):
            result = self.get_top_yields_pools("Ethereum", mock_chat_id)
        
        # Verify the result - should not include "Low TVL Pool" (50k TVL)
        assert isinstance(result, list)
        project_names = [pool["project"] for pool in result]
        assert "Low TVL Pool" not in project_names
    
    def test_get_yields_null_apy_filtering(self, monkeypatch):
        """Test that pools with null APY are filtered out"""
        # Mock dependencies
        monkeypatch.setattr('agents.researcher_agent.functions.defi_llama_functions.save_agent_thought', lambda **kwargs: None)
        monkeypatch.setattr('agents.researcher_agent.functions.defi_llama_functions.save_ui_message', lambda **kwargs: None)
        
        # Create mock data with null APY
        mock_yields_with_null = {
            "data": [
                {
                    "project": "NullAPYPool",
                    "symbol": "NULL",
                    "chain": "Ethereum",
                    "tvlUsd": 500000000.0,
                    "apyPct1D": None,  # Null APY
                    "apyPct7D": None,
                    "apyPct30D": None,
                    "ilRisk": "no"
                }
            ]
        }
        
        # Mock the HTTP request
        mock_response = Mock()
        mock_response.json.return_value = mock_yields_with_null
        mock_response.raise_for_status.return_value = None
        
        with patch('agents.researcher_agent.functions.defi_llama_functions.requests.get', return_value=mock_response):
            result = self.get_top_yields_pools("Ethereum", mock_chat_id)
        
        # Verify the result - should filter out pools with null APY
        assert result == "Could not find any pools on Ethereum."
    
    def test_get_yields_http_error(self, monkeypatch):
        """Test yields pools retrieval with HTTP error"""
        # Mock dependencies
        monkeypatch.setattr('agents.researcher_agent.functions.defi_llama_functions.save_agent_thought', lambda **kwargs: None)
        
        # Mock the HTTP request to raise an error
        with patch('agents.researcher_agent.functions.defi_llama_functions.requests.get', side_effect=requests.exceptions.HTTPError("API Error")):
            result = self.get_top_yields_pools("Ethereum", mock_chat_id)
        
        # Verify the result
        assert result == "There was an error fetching the top yields pools by chain, try again later."
    
    def test_get_yields_case_insensitive_chain(self, monkeypatch):
        """Test yields pools retrieval with case insensitive chain matching"""
        # Mock dependencies
        monkeypatch.setattr('agents.researcher_agent.functions.defi_llama_functions.save_agent_thought', lambda **kwargs: None)
        monkeypatch.setattr('agents.researcher_agent.functions.defi_llama_functions.save_ui_message', lambda **kwargs: None)
        
        # Mock the HTTP request
        mock_response = Mock()
        mock_response.json.return_value = mock_yields_data
        mock_response.raise_for_status.return_value = None
        
        with patch('agents.researcher_agent.functions.defi_llama_functions.requests.get', return_value=mock_response):
            result = self.get_top_yields_pools("ethereum", mock_chat_id)  # lowercase
        
        # Verify the result
        assert isinstance(result, list)
        assert len(result) == 3  # Should still find Ethereum pools
    
    def test_get_yields_polygon_chain(self, monkeypatch):
        """Test yields pools retrieval for Polygon chain"""
        # Mock dependencies
        monkeypatch.setattr('agents.researcher_agent.functions.defi_llama_functions.save_agent_thought', lambda **kwargs: None)
        monkeypatch.setattr('agents.researcher_agent.functions.defi_llama_functions.save_ui_message', lambda **kwargs: None)
        
        # Mock the HTTP request
        mock_response = Mock()
        mock_response.json.return_value = mock_yields_data
        mock_response.raise_for_status.return_value = None
        
        with patch('agents.researcher_agent.functions.defi_llama_functions.requests.get', return_value=mock_response):
            result = self.get_top_yields_pools("Polygon", mock_chat_id)
        
        # Verify the result
        assert isinstance(result, list)
        assert len(result) == 1  # Only QuickSwap on Polygon
        assert result[0]["project"] == "QuickSwap"
        assert result[0]["symbol"] == "MATIC-USDC"
    
    def test_get_yields_limit_enforcement(self, monkeypatch):
        """Test that limit is enforced to maximum of 10"""
        # Mock dependencies
        monkeypatch.setattr('agents.researcher_agent.functions.defi_llama_functions.save_agent_thought', lambda **kwargs: None)
        monkeypatch.setattr('agents.researcher_agent.functions.defi_llama_functions.save_ui_message', lambda **kwargs: None)
        
        # Mock the HTTP request
        mock_response = Mock()
        mock_response.json.return_value = mock_yields_data
        mock_response.raise_for_status.return_value = None
        
        with patch('agents.researcher_agent.functions.defi_llama_functions.requests.get', return_value=mock_response):
            result = self.get_top_yields_pools("Ethereum", mock_chat_id, limit=15)  # More than 10
        
        # Verify the result - should be limited to available pools (3 in this case)
        assert isinstance(result, list)
        assert len(result) <= 10
