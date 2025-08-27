# tests/agents/dex_agent/test_stake_functions.py
import types
import sys
import os
from unittest.mock import Mock, patch
import pytest

# Add the current directory to Python path so we can import the modules
sys.path.insert(0, '.')

# Mock data for testing
mock_wallet_address = "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"

mock_solana_balances = [
    {
        "address": "mSoLzYCxHdYgdzU16g5QSh3i5K3z3KZK7ytfqcJm7So",
        "amount": 10.5,
        "symbol": "mSOL",
        "name": "Marinade Staked SOL",
        "decimals": 9,
        "usd_amount": 2100.0
    },
    {
        "address": "J1toso1uCk3RLmjorhTtrVwY9HJ7X8V9yYac6Y7kGCPn",
        "amount": 5.2,
        "symbol": "jitoSOL",
        "name": "Jito Staked SOL",
        "decimals": 9,
        "usd_amount": 1040.0
    },
    {
        "address": "bSo13r4TkiE4KumL71LsHTPpL2euBYLFx6h9HP3piy1",
        "amount": 0,
        "symbol": "bSOL",
        "name": "BlazeStake Staked SOL",
        "decimals": 9,
        "usd_amount": 0.0
    }
]

mock_stake_pools_info = [
    {
        "name": "Marinade",
        "ticker": "msol",
        "average_apy": 7.2
    },
    {
        "name": "Jito",
        "ticker": "jitosol",
        "average_apy": 8.1
    },
    {
        "name": "BlazeStake",
        "ticker": "bsol",
        "average_apy": 6.8
    },
    {
        "name": "Jupiter",
        "ticker": "JupSOL",
        "average_apy": 7.5
    }
]

class TestStakeFunctions:
    """Comprehensive test suite for stake functions"""
    
    def setup_method(self):
        """Setup method that runs before each test"""
        # Import the functions once for all tests
        from agents.dex_agent.stake_functions import (
            get_user_staked_balances,
            get_stake_pools_information,
            get_pool_with_highest_apy
        )
        self.get_user_staked_balances = get_user_staked_balances
        self.get_stake_pools_information = get_stake_pools_information
        self.get_pool_with_highest_apy = get_pool_with_highest_apy
    
    def test_get_user_staked_balances_success(self, monkeypatch):
        """Test successful retrieval of user staked balances"""
        # Mock dependencies
        monkeypatch.setattr('agents.dex_agent.stake_functions.get_wallet_balance',
                            lambda wallet, service: mock_solana_balances)
        
        monkeypatch.setattr('agents.dex_agent.stake_functions.get_stake_pools_information',
                            lambda: mock_stake_pools_info)
        
        monkeypatch.setattr('agents.dex_agent.stake_functions.tokens_service.get_token_metadata',
                            lambda token, chain: {
                                "address": "mSoLzYCxHdYgdzU16g5QSh3i5K3z3KZK7ytfqcJm7So" if token == "msol" else
                                "J1toso1uCk3RLmjorhTtrVwY9HJ7X8V9yYac6Y7kGCPn" if token == "jitosol" else
                                "bSo13r4TkiE4KumL71LsHTPpL2euBYLFx6h9HP3piy1" if token == "bsol" else None
                            })
        
        # Test the function
        result = self.get_user_staked_balances(mock_wallet_address)
        
        # Verify the result
        assert isinstance(result, dict)
        assert "Marinade" in result
        assert "Jito" in result
        assert result["Marinade"]["balance"] == 10.5
        assert result["Marinade"]["apy"] == 7.2
        assert result["Marinade"]["token_symbol"] == "msol"
        assert result["Jito"]["balance"] == 5.2
        assert result["Jito"]["apy"] == 8.1
    
    def test_get_user_staked_balances_no_stakes(self, monkeypatch):
        """Test when user has no staked balances"""
        # Mock dependencies - return empty balances
        monkeypatch.setattr('agents.dex_agent.stake_functions.get_wallet_balance',
                            lambda wallet, service: [])
        
        monkeypatch.setattr('agents.dex_agent.stake_functions.get_stake_pools_information',
                            lambda: mock_stake_pools_info)
        
        monkeypatch.setattr('agents.dex_agent.stake_functions.tokens_service.get_token_metadata',
                            lambda token, chain: {"address": "fake_address"})
        
        # Test the function
        result = self.get_user_staked_balances(mock_wallet_address)
        
        # Verify the result
        assert result == "User doesn't have staked values"
    
    def test_get_user_staked_balances_partial_stakes(self, monkeypatch):
        """Test when user has some staked balances but not all pools"""
        # Mock dependencies - return only some balances
        partial_balances = [mock_solana_balances[0]]  # Only mSOL
        
        monkeypatch.setattr('agents.dex_agent.stake_functions.get_wallet_balance',
                            lambda wallet, service: partial_balances)
        
        monkeypatch.setattr('agents.dex_agent.stake_functions.get_stake_pools_information',
                            lambda: mock_stake_pools_info)
        
        monkeypatch.setattr('agents.dex_agent.stake_functions.tokens_service.get_token_metadata',
                            lambda token, chain: {
                                "address": "mSoLzYCxHdYgdzU16g5QSh3i5K3z3KZK7ytfqcJm7So" if token == "msol" else
                                {"address": "fake_address"}
                            })
        
        # Test the function
        result = self.get_user_staked_balances(mock_wallet_address)
        
        # Verify the result
        assert isinstance(result, dict)
        assert "Marinade" in result
        assert len(result) == 1  # Only one pool with stakes
        assert result["Marinade"]["balance"] == 10.5
    
    def test_get_user_staked_balances_exception_handling(self, monkeypatch):
        """Test exception handling in get_user_staked_balances"""
        # Mock dependencies to raise an exception
        monkeypatch.setattr('agents.dex_agent.stake_functions.get_wallet_balance',
                            lambda wallet, service: Exception("Balance service error"))
        
        # Test the function
        with pytest.raises(Exception) as exc_info:
            self.get_user_staked_balances(mock_wallet_address)
        
        # Verify the exception message
        assert "There was an error getting your staked balances" in str(exc_info.value)
    
    def test_get_stake_pools_information_success(self, monkeypatch):
        """Test successful retrieval of stake pools information"""
        # Mock the HTTP requests
        mock_validators_response = Mock()
        mock_validators_response.json.return_value = {
            "stake_pools": [
                {
                    "name": "Marinade",
                    "ticker": "msol",
                    "average_apy": 7.2
                },
                {
                    "name": "Jito",
                    "ticker": "jitosol",
                    "average_apy": 8.1
                }
            ]
        }
        mock_validators_response.raise_for_status.return_value = None
        
        mock_sanctum_response = Mock()
        mock_sanctum_response.json.return_value = {
            "apys": {
                "JupSOL": 0.075,
                "INF": 0.068,
                "dSOL": 0.072
            }
        }
        mock_sanctum_response.raise_for_status.return_value = None
        
        with patch('agents.dex_agent.stake_functions.requests.get') as mock_get:
            mock_get.side_effect = [mock_validators_response, mock_sanctum_response]
            
            # Test the function
            result = self.get_stake_pools_information()
        
        # Verify the result
        assert isinstance(result, list)
        assert len(result) >= 2  # At least the validators.app pools
        
        # Check for validators.app pools
        marinade_pool = next((p for p in result if p["name"] == "Marinade"), None)
        assert marinade_pool is not None
        assert marinade_pool["ticker"] == "msol"
        assert marinade_pool["average_apy"] == 7.2
        
        # Check for sanctum.so pools
        jup_sol_pool = next((p for p in result if p["ticker"] == "JupSOL"), None)
        assert jup_sol_pool is not None
        assert jup_sol_pool["average_apy"] == 7.5  # 0.075 * 100
    
    def test_get_stake_pools_information_empty_response(self, monkeypatch):
        """Test handling of empty response from validators.app"""
        # Mock the HTTP request to return empty stake pools
        mock_response = Mock()
        mock_response.json.return_value = {"stake_pools": []}
        mock_response.raise_for_status.return_value = None
        
        with patch('agents.dex_agent.stake_functions.requests.get', return_value=mock_response):
            # Test the function
            with pytest.raises(Exception) as exc_info:
                self.get_stake_pools_information()
            
            # Verify the exception message
            assert "There was an error while obtaining the staking pools" in str(exc_info.value)
    
    def test_get_stake_pools_information_http_error(self, monkeypatch):
        """Test handling of HTTP errors in get_stake_pools_information"""
        # Mock the HTTP request to raise an error
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("HTTP Error")
        
        with patch('agents.dex_agent.stake_functions.requests.get', return_value=mock_response):
            # Test the function
            with pytest.raises(Exception) as exc_info:
                self.get_stake_pools_information()
            
            # Verify the exception message
            assert "There was an error getting the stake pools information" in str(exc_info.value)
    
    def test_get_pool_with_highest_apy(self, monkeypatch):
        """Test getting the pool with highest APY"""
        # Mock the stake pools information
        monkeypatch.setattr('agents.dex_agent.stake_functions.get_stake_pools_information',
                            lambda: mock_stake_pools_info)
        
        # Test the function
        result = self.get_pool_with_highest_apy()
        
        # Verify the result
        assert isinstance(result, dict)
        assert result["name"] == "Jito"  # Should have highest APY (8.1)
        assert result["average_apy"] == 8.1
        assert result["ticker"] == "jitosol"
    
    def test_get_pool_with_highest_apy_single_pool(self, monkeypatch):
        """Test getting highest APY when there's only one pool"""
        single_pool = [mock_stake_pools_info[0]]  # Only Marinade
        
        monkeypatch.setattr('agents.dex_agent.stake_functions.get_stake_pools_information',
                            lambda: single_pool)
        
        # Test the function
        result = self.get_pool_with_highest_apy()
        
        # Verify the result
        assert result["name"] == "Marinade"
        assert result["average_apy"] == 7.2
    
    def test_get_pool_with_highest_apy_equal_apys(self, monkeypatch):
        """Test getting highest APY when multiple pools have equal APY"""
        equal_apy_pools = [
            {"name": "Pool1", "ticker": "t1", "average_apy": 7.0},
            {"name": "Pool2", "ticker": "t2", "average_apy": 7.0},
            {"name": "Pool3", "ticker": "t3", "average_apy": 6.0}
        ]
        
        monkeypatch.setattr('agents.dex_agent.stake_functions.get_stake_pools_information',
                            lambda: equal_apy_pools)
        
        # Test the function
        result = self.get_pool_with_highest_apy()
        
        # Verify the result (should return the first one with max APY)
        assert result["average_apy"] == 7.0
        assert result["name"] in ["Pool1", "Pool2"]
    
    def test_supported_pools_and_tickers_structure(self):
        """Test that the supported_pools_and_tickers dictionary is properly structured"""
        from agents.dex_agent.stake_functions import supported_pools_and_tickers
        
        # Verify the structure
        assert isinstance(supported_pools_and_tickers, dict)
        assert len(supported_pools_and_tickers) > 0
        
        # Check that all values are strings
        for pool_name, ticker in supported_pools_and_tickers.items():
            assert isinstance(pool_name, str)
            assert isinstance(ticker, str)
            assert len(pool_name) > 0
            assert len(ticker) > 0
        
        # Check for specific known pools
        assert "Marinade" in supported_pools_and_tickers
        assert "Jupiter" in supported_pools_and_tickers
        assert "Jito" in supported_pools_and_tickers
        assert supported_pools_and_tickers["Marinade"] == "msol"
        assert supported_pools_and_tickers["Jupiter"] == "jupSol"
