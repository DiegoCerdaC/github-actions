# tests/agents/enso/test_enso_functions.py
import sys
from unittest.mock import Mock, patch, AsyncMock
import pytest

# Add the current directory to Python path so we can import the modules
sys.path.insert(0, '.')


class TestIsProtocolSupported:
    """Test suite for is_protocol_supported function"""
    
    def setup_method(self):
        """Setup method that runs before each test"""
        from agents.enso.enso_functions import is_protocol_supported
        self.is_protocol_supported = is_protocol_supported
    
    def test_exact_match(self, monkeypatch):
        """Test exact protocol match"""
        mock_supported_protocols = {
            "1": {
                "protocols": ["aave-v3", "morpho", "compound"]
            },
            "8453": {
                "protocols": ["aave-v3", "compound-v3"]
            }
        }
        
        mock_get_enso_supported_chains_and_protocols = Mock(return_value=mock_supported_protocols)
        monkeypatch.setattr('agents.enso.enso_functions.get_enso_supported_chains_and_protocols', mock_get_enso_supported_chains_and_protocols)
        
        result = self.is_protocol_supported("aave-v3")
        assert result is True
    
    def test_partial_match_startswith(self, monkeypatch):
        """Test partial match where protocol starts with the search term"""
        mock_supported_protocols = {
            "1": {
                "protocols": ["aave-v3", "aave-v2", "compound"]
            }
        }
        
        mock_get_enso_supported_chains_and_protocols = Mock(return_value=mock_supported_protocols)
        monkeypatch.setattr('agents.enso.enso_functions.get_enso_supported_chains_and_protocols', mock_get_enso_supported_chains_and_protocols)
        
        result = self.is_protocol_supported("aave")
        assert result is True
    
    def test_partial_match_contains(self, monkeypatch):
        """Test partial match where search term is contained in protocol"""
        mock_supported_protocols = {
            "1": {
                "protocols": ["aave-v3", "compound-v3", "morpho"]
            }
        }
        
        mock_get_enso_supported_chains_and_protocols = Mock(return_value=mock_supported_protocols)
        monkeypatch.setattr('agents.enso.enso_functions.get_enso_supported_chains_and_protocols', mock_get_enso_supported_chains_and_protocols)
        
        result = self.is_protocol_supported("v3")
        assert result is True
    
    def test_case_insensitive_match(self, monkeypatch):
        """Test case insensitive matching"""
        mock_supported_protocols = {
            "1": {
                "protocols": ["AAVE-V3", "MORPHO", "COMPOUND"]
            }
        }
        
        mock_get_enso_supported_chains_and_protocols = Mock(return_value=mock_supported_protocols)
        monkeypatch.setattr('agents.enso.enso_functions.get_enso_supported_chains_and_protocols', mock_get_enso_supported_chains_and_protocols)
        
        result = self.is_protocol_supported("aave")
        assert result is True
    
    def test_no_match(self, monkeypatch):
        """Test when no protocol matches"""
        mock_supported_protocols = {
            "1": {
                "protocols": ["aave-v3", "compound", "morpho"]
            }
        }
        
        mock_get_enso_supported_chains_and_protocols = Mock(return_value=mock_supported_protocols)
        monkeypatch.setattr('agents.enso.enso_functions.get_enso_supported_chains_and_protocols', mock_get_enso_supported_chains_and_protocols)
        
        result = self.is_protocol_supported("uniswap")
        assert result is False


class TestIsChainSupported:
    """Test suite for is_chain_supported function"""
    
    def setup_method(self):
        """Setup method that runs before each test"""
        from agents.enso.enso_functions import is_chain_supported
        self.is_chain_supported = is_chain_supported
    
    def test_chain_id_direct_match(self, monkeypatch):
        """Test direct chain ID match"""
        mock_supported_chains_and_protocols = {
            "1": {"chain_name": "ethereum", "protocols": ["aave"]},
            "8453": {"chain_name": "base", "protocols": ["compound"]}
        }
        
        mock_get_enso_supported_chains_and_protocols = Mock(return_value=mock_supported_chains_and_protocols)
        monkeypatch.setattr('agents.enso.enso_functions.get_enso_supported_chains_and_protocols', mock_get_enso_supported_chains_and_protocols)
        
        result = self.is_chain_supported("1")
        assert result is True
    
    def test_chain_name_match(self, monkeypatch):
        """Test chain name match"""
        mock_supported_chains_and_protocols = {
            "1": {"chain_name": "ethereum", "protocols": ["aave"]},
            "8453": {"chain_name": "base", "protocols": ["compound"]}
        }
        
        mock_get_enso_supported_chains_and_protocols = Mock(return_value=mock_supported_chains_and_protocols)
        monkeypatch.setattr('agents.enso.enso_functions.get_enso_supported_chains_and_protocols', mock_get_enso_supported_chains_and_protocols)
        
        result = self.is_chain_supported("ethereum")
        assert result is True
    
    def test_chain_name_case_insensitive(self, monkeypatch):
        """Test case insensitive chain name matching"""
        mock_supported_chains_and_protocols = {
            "1": {"chain_name": "Ethereum", "protocols": ["aave"]}
        }
        
        mock_get_enso_supported_chains_and_protocols = Mock(return_value=mock_supported_chains_and_protocols)
        monkeypatch.setattr('agents.enso.enso_functions.get_enso_supported_chains_and_protocols', mock_get_enso_supported_chains_and_protocols)
        
        result = self.is_chain_supported("ethereum")
        assert result is True
    
    def test_chain_id_from_service(self, monkeypatch):
        """Test getting chain ID from chains service"""
        mock_supported_chains_and_protocols = {
            "1": {"chain_name": "polygon", "protocols": ["aave"]}  # Different chain name to avoid direct match
        }
        
        mock_get_enso_supported_chains_and_protocols = Mock(return_value=mock_supported_chains_and_protocols)
        mock_call_chains_service = Mock(return_value="1")
        
        monkeypatch.setattr('agents.enso.enso_functions.get_enso_supported_chains_and_protocols', mock_get_enso_supported_chains_and_protocols)
        monkeypatch.setattr('agents.enso.enso_functions.call_chains_service', mock_call_chains_service)
        
        result = self.is_chain_supported("ethereum")
        assert result is True
        mock_call_chains_service.assert_called_once_with(method="getChainId", chainName="ethereum")
    
    def test_chain_not_supported(self, monkeypatch):
        """Test when chain is not supported"""
        mock_supported_chains_and_protocols = {
            "1": {"chain_name": "ethereum", "protocols": ["aave"]}
        }
        
        mock_get_enso_supported_chains_and_protocols = Mock(return_value=mock_supported_chains_and_protocols)
        mock_call_chains_service = Mock(return_value=None)
        
        monkeypatch.setattr('agents.enso.enso_functions.get_enso_supported_chains_and_protocols', mock_get_enso_supported_chains_and_protocols)
        monkeypatch.setattr('agents.enso.enso_functions.call_chains_service', mock_call_chains_service)
        
        result = self.is_chain_supported("unsupported_chain")
        assert result is False
    
    def test_empty_supported_chains(self, monkeypatch):
        """Test when no supported chains are available"""
        mock_get_enso_supported_chains_and_protocols = Mock(return_value={})
        monkeypatch.setattr('agents.enso.enso_functions.get_enso_supported_chains_and_protocols', mock_get_enso_supported_chains_and_protocols)
        
        result = self.is_chain_supported("ethereum")
        assert result is False
    
    def test_exception_handling(self, monkeypatch):
        """Test exception handling"""
        mock_get_enso_supported_chains_and_protocols = Mock(side_effect=Exception("Database error"))
        monkeypatch.setattr('agents.enso.enso_functions.get_enso_supported_chains_and_protocols', mock_get_enso_supported_chains_and_protocols)
        
        result = self.is_chain_supported("ethereum")
        assert result is False


class TestDefiQuote:
    """Test suite for defi_quote function"""
    
    def setup_method(self):
        """Setup method that runs before each test"""
        from agents.enso.enso_functions import defi_quote
        self.defi_quote = defi_quote
    
    def test_frontend_quoting_deposit(self, monkeypatch):
        """Test frontend quoting for deposit"""
        # Mock dependencies
        mock_get_matching_defi_tokens = Mock(return_value=[
            {"token": {"address": "0x123"}, "apy": 5.2}
        ])
        mock_is_chain_supported = Mock(return_value=True)
        mock_get_request_ctx = Mock(side_effect=lambda chat_id, key: {
            "evm_wallet_address": "0x456",
            "slippage": 0.5,
            "user_id": "user123"
        }.get(key))
        mock_save_agent_thought = Mock()
        mock_save_ui_message = Mock()
        
        monkeypatch.setattr('agents.enso.enso_functions.get_matching_defi_tokens', mock_get_matching_defi_tokens)
        monkeypatch.setattr('agents.enso.enso_functions.is_chain_supported', mock_is_chain_supported)
        monkeypatch.setattr('agents.enso.enso_functions.get_request_ctx', mock_get_request_ctx)
        monkeypatch.setattr('agents.enso.enso_functions.save_agent_thought', mock_save_agent_thought)
        monkeypatch.setattr('agents.enso.enso_functions.save_ui_message', mock_save_ui_message)
        
        result = self.defi_quote(
            token="USDC",
            chat_id="test-chat",
            is_withdraw=False,
            amount="100",
            from_chain="ethereum",
            protocol="aave",
            use_frontend_quoting=True
        )
        
        assert "started the process to make your deposit succesfully" in result
        mock_save_ui_message.assert_called_once()
    
    def test_frontend_quoting_withdraw(self, monkeypatch):
        """Test frontend quoting for withdraw"""
        # Mock dependencies
        mock_get_matching_defi_tokens = Mock(return_value=[
            {"token": {"address": "0x123"}, "apy": 5.2}
        ])
        mock_is_chain_supported = Mock(return_value=True)
        mock_get_request_ctx = Mock(side_effect=lambda chat_id, key: {
            "evm_wallet_address": "0x456",
            "slippage": 0.5,
            "user_id": "user123"
        }.get(key))
        mock_save_agent_thought = Mock()
        mock_save_ui_message = Mock()
        
        monkeypatch.setattr('agents.enso.enso_functions.get_matching_defi_tokens', mock_get_matching_defi_tokens)
        monkeypatch.setattr('agents.enso.enso_functions.is_chain_supported', mock_is_chain_supported)
        monkeypatch.setattr('agents.enso.enso_functions.get_request_ctx', mock_get_request_ctx)
        monkeypatch.setattr('agents.enso.enso_functions.save_agent_thought', mock_save_agent_thought)
        monkeypatch.setattr('agents.enso.enso_functions.save_ui_message', mock_save_ui_message)
        
        result = self.defi_quote(
            token="USDC",
            chat_id="test-chat",
            is_withdraw=True,
            amount="100",
            from_chain="ethereum",
            protocol="aave",
            use_frontend_quoting=True
        )
        
        assert "started the process to make your withdraw succesfully" in result
    
    def test_backend_quoting_success(self, monkeypatch):
        """Test successful backend quoting"""
        # Mock dependencies
        mock_get_matching_defi_tokens = Mock(return_value=[
            {"token": {"address": "0x123"}, "apy": 5.2}
        ])
        mock_is_chain_supported = Mock(return_value=True)
        mock_get_request_ctx = Mock(side_effect=lambda chat_id, key: {
            "evm_wallet_address": "0x456",
            "slippage": 0.5,
            "user_id": "user123",
            "allowance": "unlimited"
        }.get(key))
        mock_save_agent_thought = Mock()
        
        # Mock requests
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"quote": "test_quote"}
        mock_requests_post = Mock(return_value=mock_response)
        
        monkeypatch.setattr('agents.enso.enso_functions.get_matching_defi_tokens', mock_get_matching_defi_tokens)
        monkeypatch.setattr('agents.enso.enso_functions.is_chain_supported', mock_is_chain_supported)
        monkeypatch.setattr('agents.enso.enso_functions.get_request_ctx', mock_get_request_ctx)
        monkeypatch.setattr('agents.enso.enso_functions.save_agent_thought', mock_save_agent_thought)
        monkeypatch.setattr('requests.post', mock_requests_post)
        
        result = self.defi_quote(
            token="USDC",
            chat_id="test-chat",
            is_withdraw=False,
            amount="100",
            from_chain="ethereum",
            protocol="aave",
            use_frontend_quoting=False
        )
        
        assert result == {"quote": "test_quote"}
        mock_requests_post.assert_called_once()
    
    def test_no_matching_tokens(self, monkeypatch):
        """Test when no matching tokens are found"""
        mock_get_matching_defi_tokens = Mock(return_value=[])
        mock_save_agent_thought = Mock()
        
        monkeypatch.setattr('agents.enso.enso_functions.get_matching_defi_tokens', mock_get_matching_defi_tokens)
        monkeypatch.setattr('agents.enso.enso_functions.save_agent_thought', mock_save_agent_thought)
        
        with pytest.raises(ValueError, match="No matching tokens found for the specified criteria"):
            self.defi_quote(
                token="USDC",
                chat_id="test-chat",
                is_withdraw=False,
                amount="100",
                from_chain="ethereum",
                protocol="aave"
            )
    
    def test_chain_not_supported(self, monkeypatch):
        """Test when chain is not supported"""
        mock_get_matching_defi_tokens = Mock(return_value=[
            {"token": {"address": "0x123"}, "apy": 5.2}
        ])
        mock_is_chain_supported = Mock(return_value=False)
        mock_save_agent_thought = Mock()
        
        monkeypatch.setattr('agents.enso.enso_functions.get_matching_defi_tokens', mock_get_matching_defi_tokens)
        monkeypatch.setattr('agents.enso.enso_functions.is_chain_supported', mock_is_chain_supported)
        monkeypatch.setattr('agents.enso.enso_functions.save_agent_thought', mock_save_agent_thought)
        
        with pytest.raises(ValueError, match="Chain ethereum is not supported"):
            self.defi_quote(
                token="USDC",
                chat_id="test-chat",
                is_withdraw=False,
                amount="100",
                from_chain="ethereum",
                protocol="aave"
            )
    
    def test_backend_quoting_missing_amount(self, monkeypatch):
        """Test backend quoting without amount"""
        mock_get_matching_defi_tokens = Mock(return_value=[
            {"token": {"address": "0x123"}, "apy": 5.2}
        ])
        mock_is_chain_supported = Mock(return_value=True)
        mock_get_request_ctx = Mock(side_effect=lambda chat_id, key: {
            "evm_wallet_address": "0x456",
            "slippage": 0.5,
            "user_id": "user123"
        }.get(key))
        mock_save_agent_thought = Mock()
        
        monkeypatch.setattr('agents.enso.enso_functions.get_matching_defi_tokens', mock_get_matching_defi_tokens)
        monkeypatch.setattr('agents.enso.enso_functions.is_chain_supported', mock_is_chain_supported)
        monkeypatch.setattr('agents.enso.enso_functions.get_request_ctx', mock_get_request_ctx)
        monkeypatch.setattr('agents.enso.enso_functions.save_agent_thought', mock_save_agent_thought)
        
        with pytest.raises(ValueError, match="Amount is required when using backend quoting"):
            self.defi_quote(
                token="USDC",
                chat_id="test-chat",
                is_withdraw=False,
                from_chain="ethereum",
                protocol="aave",
                use_frontend_quoting=False
            )
    
    def test_backend_quoting_missing_chain(self, monkeypatch):
        """Test backend quoting without chain"""
        mock_get_matching_defi_tokens = Mock(return_value=[
            {"token": {"address": "0x123"}, "apy": 5.2}
        ])
        mock_save_agent_thought = Mock()
        
        monkeypatch.setattr('agents.enso.enso_functions.get_matching_defi_tokens', mock_get_matching_defi_tokens)
        monkeypatch.setattr('agents.enso.enso_functions.save_agent_thought', mock_save_agent_thought)
        
        with pytest.raises(ValueError, match="From chain is required when using backend quoting"):
            self.defi_quote(
                token="USDC",
                chat_id="test-chat",
                is_withdraw=False,
                amount="100",
                protocol="aave",
                use_frontend_quoting=False
            )


class TestGetMatchingDefiTokens:
    """Test suite for get_matching_defi_tokens function"""
    
    def setup_method(self):
        """Setup method that runs before each test"""
        from agents.enso.enso_functions import get_matching_defi_tokens
        self.get_matching_defi_tokens = get_matching_defi_tokens
    
    def test_with_all_filters(self, monkeypatch):
        """Test with all filters applied"""
        mock_call_chains_service = Mock(return_value="1")
        mock_get_enso_supported_tokens = Mock(return_value=[
            {"token": {"address": "0x123"}, "apy": 5.2}
        ])
        
        monkeypatch.setattr('agents.enso.enso_functions.call_chains_service', mock_call_chains_service)
        monkeypatch.setattr('agents.enso.enso_functions.get_enso_supported_tokens', mock_get_enso_supported_tokens)
        
        result = self.get_matching_defi_tokens(
            chain_name="ethereum",
            protocol="aave",
            symbol="USDC"
        )
        
        assert len(result) == 1
        assert result[0]["token"]["address"] == "0x123"
        mock_call_chains_service.assert_called_once_with(method="getChainId", chainName="ethereum")
        mock_get_enso_supported_tokens.assert_called_once_with(
            chain_id="1",
            project="aave",
            symbol="USDC"
        )
    
    def test_with_chain_filter_only(self, monkeypatch):
        """Test with only chain filter"""
        mock_call_chains_service = Mock(return_value="8453")
        mock_get_enso_supported_tokens = Mock(return_value=[
            {"token": {"address": "0x456"}, "apy": 4.8}
        ])
        
        monkeypatch.setattr('agents.enso.enso_functions.call_chains_service', mock_call_chains_service)
        monkeypatch.setattr('agents.enso.enso_functions.get_enso_supported_tokens', mock_get_enso_supported_tokens)
        
        result = self.get_matching_defi_tokens(chain_name="base")
        
        assert len(result) == 1
        mock_get_enso_supported_tokens.assert_called_once_with(
            chain_id="8453",
            project=None,
            symbol=None
        )
    
    def test_with_protocol_filter_only(self, monkeypatch):
        """Test with only protocol filter"""
        mock_get_enso_supported_tokens = Mock(return_value=[
            {"token": {"address": "0x789"}, "apy": 6.1}
        ])
        
        monkeypatch.setattr('agents.enso.enso_functions.get_enso_supported_tokens', mock_get_enso_supported_tokens)
        
        result = self.get_matching_defi_tokens(protocol="morpho")
        
        assert len(result) == 1
        mock_get_enso_supported_tokens.assert_called_once_with(
            chain_id=None,
            project="morpho",
            symbol=None
        )
    
    def test_with_symbol_filter_only(self, monkeypatch):
        """Test with only symbol filter"""
        mock_get_enso_supported_tokens = Mock(return_value=[
            {"token": {"address": "0xabc"}, "apy": 3.9}
        ])
        
        monkeypatch.setattr('agents.enso.enso_functions.get_enso_supported_tokens', mock_get_enso_supported_tokens)
        
        result = self.get_matching_defi_tokens(symbol="ETH")
        
        assert len(result) == 1
        mock_get_enso_supported_tokens.assert_called_once_with(
            chain_id=None,
            project=None,
            symbol="ETH"
        )
    
    def test_no_filters(self, monkeypatch):
        """Test with no filters"""
        mock_get_enso_supported_tokens = Mock(return_value=[
            {"token": {"address": "0xdef"}, "apy": 7.2}
        ])
        
        monkeypatch.setattr('agents.enso.enso_functions.get_enso_supported_tokens', mock_get_enso_supported_tokens)
        
        result = self.get_matching_defi_tokens()
        
        assert len(result) == 1
        mock_get_enso_supported_tokens.assert_called_once_with(
            chain_id=None,
            project=None,
            symbol=None
        )
    
    def test_fallback_to_all_tokens(self, monkeypatch):
        """Test fallback when filtered results are empty"""
        mock_call_chains_service = Mock(return_value="1")
        mock_get_enso_supported_tokens = Mock(side_effect=[
            [],  # First call with filters returns empty
            [{"token": {"address": "0x123"}, "apy": 5.2}]  # Second call returns all tokens
        ])
        
        monkeypatch.setattr('agents.enso.enso_functions.call_chains_service', mock_call_chains_service)
        monkeypatch.setattr('agents.enso.enso_functions.get_enso_supported_tokens', mock_get_enso_supported_tokens)
        
        result = self.get_matching_defi_tokens(
            chain_name="ethereum",
            protocol="aave"
        )
        
        assert len(result) == 1
        assert mock_get_enso_supported_tokens.call_count == 2
    
    def test_chain_service_exception(self, monkeypatch):
        """Test when chains service throws exception"""
        mock_call_chains_service = Mock(side_effect=Exception("Service error"))
        mock_get_enso_supported_tokens = Mock(return_value=[
            {"token": {"address": "0x123"}, "apy": 5.2}
        ])
        
        monkeypatch.setattr('agents.enso.enso_functions.call_chains_service', mock_call_chains_service)
        monkeypatch.setattr('agents.enso.enso_functions.get_enso_supported_tokens', mock_get_enso_supported_tokens)
        
        result = self.get_matching_defi_tokens(chain_name="ethereum")
        
        assert len(result) == 1
        mock_get_enso_supported_tokens.assert_called_once_with(
            chain_id=None,
            project=None,
            symbol=None
        )


class TestGetTokenUsdAmount:
    """Test suite for get_token_usd_amount function"""
    
    def setup_method(self):
        """Setup method that runs before each test"""
        from agents.enso.enso_functions import get_token_usd_amount
        self.get_token_usd_amount = get_token_usd_amount
    
    def test_calculate_usd_amount(self, monkeypatch):
        """Test USD amount calculation"""
        mock_price_response = {"price": "2000.50"}
        mock_get_token_price_from_provider = Mock(return_value=mock_price_response)
        
        monkeypatch.setattr('agents.enso.enso_functions.prices_service.get_token_price_from_provider', mock_get_token_price_from_provider)
        
        result = self.get_token_usd_amount("ethereum", "0x123", 2.5)
        
        # 2000.50 * 2.5 = 5001.25
        assert result == 5001.25
        mock_get_token_price_from_provider.assert_called_once_with(
            "ethereum", "0x123", "LIFI"
        )
    
    def test_zero_amount(self, monkeypatch):
        """Test with zero amount"""
        mock_price_response = {"price": "100.00"}
        mock_get_token_price_from_provider = Mock(return_value=mock_price_response)
        
        monkeypatch.setattr('agents.enso.enso_functions.prices_service.get_token_price_from_provider', mock_get_token_price_from_provider)
        
        result = self.get_token_usd_amount("ethereum", "0x123", 0)
        
        assert result == 0.0
    
    def test_decimal_precision(self, monkeypatch):
        """Test decimal precision handling"""
        mock_price_response = {"price": "1.23456789"}
        mock_get_token_price_from_provider = Mock(return_value=mock_price_response)
        
        monkeypatch.setattr('agents.enso.enso_functions.prices_service.get_token_price_from_provider', mock_get_token_price_from_provider)
        
        result = self.get_token_usd_amount("ethereum", "0x123", 3.14159)
        
        # 1.23456789 * 3.14159 = 3.878509
        expected = 1.23456789 * 3.14159
        assert abs(result - expected) < 1e-6
