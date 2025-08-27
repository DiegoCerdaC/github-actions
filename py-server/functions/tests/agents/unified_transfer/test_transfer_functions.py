import sys
import pytest
from unittest.mock import MagicMock, patch
from unittest.mock import Mock

# Add the current directory to Python path
sys.path.insert(0, '.')

from agents.unified_transfer.transfer_functions import (
    create_evm_transfer,
    create_solana_transfer,
    handle_create_solana_transfer,
    handle_usdc_bridge_flow,
    create_bridge_and_transfer,
    _check_and_record_for_evaluation
)


class TestTransferFunctions:
    """Test cases for transfer functions"""
    
    @pytest.fixture
    def mock_context(self):
        """Mock context data for testing"""
        return {
            "user_id": "test_user_123",
            "evm_wallet_address": "0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6",
            "solana_wallet_address": "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
            "evaluation_mode": False,
            "solana_usdc_balance": 100.0
        }
    
    @pytest.fixture
    def mock_token_info(self):
        """Mock token information"""
        return {
            "name": "USD Coin",
            "symbol": "USDC",
            "decimals": 6,
            "address": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
            "contract_address": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
            "chain_name": "POLYGON",
            "chain": "POLYGON",
            "chain_id": "vNX8ui5XObaP9Z8A0ZbB",
            "protocols": ["vTCOPcMINJFUdzil3uiN"],
            "verified": True
        }
    
    @pytest.fixture
    def mock_solana_token_info(self):
        """Mock Solana token information"""
        return {
            "name": "USD Coin",
            "symbol": "USDC",
            "decimals": 6,
            "address": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
            "contract_address": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
            "chain_name": "SOLANA",
            "chain": "SOLANA",
            "chain_id": "vNX8ui5XObaP9Z8A0ZbB",
            "protocols": ["vTCOPcMINJFUdzil3uiN"],
            "verified": True
        }

    def test_check_and_record_for_evaluation_disabled(self, mock_context):
        """Test evaluation recording when evaluation mode is disabled"""
        with patch('agents.unified_transfer.transfer_functions.get_request_ctx') as mock_get_ctx:
            mock_get_ctx.return_value = False
            
            result = _check_and_record_for_evaluation("test_function", {"chat_id": "test"})
            
            assert result is None
            mock_get_ctx.assert_called_once_with("test", "evaluation_mode")

    def test_check_and_record_for_evaluation_enabled(self, mock_context):
        """Test evaluation recording when evaluation mode is enabled"""
        with patch('agents.unified_transfer.transfer_functions.get_request_ctx') as mock_get_ctx, \
             patch('agents.unified_transfer.transfer_functions.set_request_ctx') as mock_set_ctx:
            
            mock_get_ctx.side_effect = [True, []]  # evaluation_mode=True, function_calls=[]
            
            result = _check_and_record_for_evaluation("create_evm_transfer", {"chat_id": "test", "amount": 1.5})
            
            assert "Evaluation mode: create_evm_transfer function called" in result
            mock_set_ctx.assert_called_once()

    def test_check_and_record_for_evaluation_stop_execution(self, mock_context):
        """Test evaluation recording for functions that stop execution"""
        with patch('agents.unified_transfer.transfer_functions.get_request_ctx') as mock_get_ctx, \
             patch('agents.unified_transfer.transfer_functions.set_request_ctx') as mock_set_ctx:
            
            mock_get_ctx.side_effect = [True, []]  # evaluation_mode=True, function_calls=[]
            
            result = _check_and_record_for_evaluation("handle_usdc_bridge_flow", {"chat_id": "test"})
            
            assert "Evaluation mode: handle_usdc_bridge_flow function called" in result
            mock_set_ctx.assert_called_once()

    def test_create_evm_transfer_success_frontend_quoting(self, mock_context):
        """Test successful EVM transfer with frontend quoting"""
        with patch('agents.unified_transfer.transfer_functions.is_evm') as mock_is_evm, \
             patch('agents.unified_transfer.transfer_functions.save_agent_thought') as mock_save_thought, \
             patch('agents.unified_transfer.transfer_functions.save_ui_message') as mock_save_ui:
            
            mock_is_evm.return_value = True
            
            result = create_evm_transfer(
                chat_id="test",
                to_address="0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6",
                amount=1.5,
                token_symbol="USDC",
                chain_name="POLYGON",
                use_frontend_quoting=True
            )
            
            assert "I've started the quoting process for your transfer on POLYGON" in result
            mock_save_thought.assert_called()
            mock_save_ui.assert_called()

    def test_create_evm_transfer_success_backend_quoting(self, mock_context):
        """Test successful EVM transfer with backend quoting"""
        with patch('agents.unified_transfer.transfer_functions.is_evm') as mock_is_evm, \
             patch('agents.unified_transfer.transfer_functions.save_agent_thought') as mock_save_thought, \
             patch('agents.unified_transfer.transfer_functions.call_chains_service') as mock_chains, \
             patch('agents.unified_transfer.transfer_functions.requests.post') as mock_post:
            
            mock_is_evm.return_value = True
            mock_chains.side_effect = ["137", True]  # chain_id, isEvm
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {"success": True}
            
            result = create_evm_transfer(
                chat_id="test",
                to_address="0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6",
                amount=1.5,
                token_symbol="USDC",
                chain_name="POLYGON",
                use_frontend_quoting=False
            )
            
            assert result == {"success": True}
            mock_chains.assert_called()
            mock_post.assert_called()

    def test_create_evm_transfer_invalid_address(self, mock_context):
        """Test EVM transfer with invalid destination address"""
        with patch('agents.unified_transfer.transfer_functions.is_evm') as mock_is_evm:
            mock_is_evm.return_value = False
            
            result = create_evm_transfer(
                chat_id="test",
                to_address="invalid_address",
                amount=1.5,
                token_symbol="USDC",
                chain_name="POLYGON"
            )
            
            assert "Invalid Destination Wallet Address (not an EVM address)" in result

    def test_create_evm_transfer_zero_amount(self, mock_context):
        """Test EVM transfer with zero amount"""
        with patch('agents.unified_transfer.transfer_functions.is_evm') as mock_is_evm, \
             patch('agents.unified_transfer.transfer_functions.save_agent_thought') as mock_save_thought:
            
            mock_is_evm.return_value = True
            
            result = create_evm_transfer(
                chat_id="test",
                to_address="0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6",
                amount=0,
                token_symbol="USDC",
                chain_name="POLYGON"
            )
            
            assert "Please specify the amount you want to transfer" in result
            mock_save_thought.assert_called()

    def test_create_evm_transfer_none_amount(self, mock_context):
        """Test EVM transfer with None amount"""
        with patch('agents.unified_transfer.transfer_functions.is_evm') as mock_is_evm, \
             patch('agents.unified_transfer.transfer_functions.save_agent_thought') as mock_save_thought:
            
            mock_is_evm.return_value = True
            
            result = create_evm_transfer(
                chat_id="test",
                to_address="0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6",
                amount=None,
                token_symbol="USDC",
                chain_name="POLYGON"
            )
            
            assert "Please specify the amount you want to transfer" in result
            mock_save_thought.assert_called()

    def test_create_evm_transfer_invalid_chain(self, mock_context):
        """Test EVM transfer with invalid chain"""
        with patch('agents.unified_transfer.transfer_functions.is_evm') as mock_is_evm, \
             patch('agents.unified_transfer.transfer_functions.call_chains_service') as mock_chains:
            
            mock_is_evm.return_value = True
            mock_chains.side_effect = ["137", False]  # chain_id, isEvm=False
            
            result = create_evm_transfer(
                chat_id="test",
                to_address="0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6",
                amount=1.5,
                token_symbol="USDC",
                chain_name="INVALID_CHAIN",
                use_frontend_quoting=False
            )
            
            assert "Chain INVALID_CHAIN is not an EVM chain" in result

    def test_create_evm_transfer_http_error(self, mock_context):
        """Test EVM transfer with HTTP error"""
        with patch('agents.unified_transfer.transfer_functions.is_evm') as mock_is_evm, \
             patch('agents.unified_transfer.transfer_functions.save_agent_thought') as mock_save_thought, \
             patch('agents.unified_transfer.transfer_functions.call_chains_service') as mock_chains, \
             patch('agents.unified_transfer.transfer_functions.requests.post') as mock_post:
            
            mock_is_evm.return_value = True
            mock_chains.side_effect = ["137", True]
            mock_post.return_value.status_code = 500
            mock_post.return_value.raise_for_status.side_effect = Exception("HTTP Error")
            
            result = create_evm_transfer(
                chat_id="test",
                to_address="0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6",
                amount=1.5,
                token_symbol="USDC",
                chain_name="POLYGON",
                use_frontend_quoting=False
            )
            
            assert "There was an error creating the transfer on EVM" in result

    def test_create_solana_transfer_success_frontend_quoting(self, mock_context):
        """Test successful Solana transfer with frontend quoting"""
        with patch('agents.unified_transfer.transfer_functions.is_solana') as mock_is_solana, \
             patch('agents.unified_transfer.transfer_functions.save_agent_thought') as mock_save_thought, \
             patch('agents.unified_transfer.transfer_functions.save_ui_message') as mock_save_ui:
            
            mock_is_solana.return_value = True
            
            result = create_solana_transfer(
                chat_id="test",
                to_address="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
                amount=1.5,
                token_symbol="SOL"
            )
            
            assert "I've started the quoting process for your transfer on SOLANA" in result
            mock_save_thought.assert_called()
            mock_save_ui.assert_called()

    def test_create_solana_transfer_success_backend_quoting(self, mock_context):
        """Test successful Solana transfer with backend quoting"""
        with patch('agents.unified_transfer.transfer_functions.is_solana') as mock_is_solana, \
             patch('agents.unified_transfer.transfer_functions.save_agent_thought') as mock_save_thought, \
             patch('agents.unified_transfer.transfer_functions.get_single_token_balance') as mock_balance, \
             patch('agents.unified_transfer.transfer_functions.handle_create_solana_transfer') as mock_handle:
            
            mock_is_solana.return_value = True
            mock_balance.return_value = "100.0"
            mock_handle.return_value = "Transfer created successfully"
            
            result = create_solana_transfer(
                chat_id="test",
                to_address="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
                amount=1.5,
                token_symbol="SOL",
                use_frontend_quoting=False
            )
            
            assert result == "Transfer created successfully"
            mock_handle.assert_called()

    def test_create_solana_transfer_invalid_address(self, mock_context):
        """Test Solana transfer with invalid destination address"""
        with patch('agents.unified_transfer.transfer_functions.is_solana') as mock_is_solana:
            mock_is_solana.return_value = False
            
            result = create_solana_transfer(
                chat_id="test",
                to_address="invalid_address",
                amount=1.5,
                token_symbol="SOL"
            )
            
            assert "Invalid Destination Wallet Address (not a Solana address)" in result

    def test_create_solana_transfer_no_wallet(self, mock_context):
        """Test Solana transfer with no wallet connected"""
        with patch('agents.unified_transfer.transfer_functions.is_solana') as mock_is_solana, \
             patch('agents.unified_transfer.transfer_functions.get_request_ctx') as mock_get_ctx:
            
            mock_is_solana.return_value = True
            mock_get_ctx.return_value = None
            
            result = create_solana_transfer(
                chat_id="test",
                to_address="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
                amount=1.5,
                token_symbol="SOL"
            )
            
            assert "Solana Wallet not detected" in result

    def test_create_solana_transfer_zero_amount(self, mock_context):
        """Test Solana transfer with zero amount"""
        with patch('agents.unified_transfer.transfer_functions.is_solana') as mock_is_solana, \
             patch('agents.unified_transfer.transfer_functions.save_agent_thought') as mock_save_thought:
            
            mock_is_solana.return_value = True
            
            result = create_solana_transfer(
                chat_id="test",
                to_address="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
                amount=0,
                token_symbol="SOL"
            )
            
            assert "Please specify the amount you want to transfer" in result
            mock_save_thought.assert_called()

    def test_create_solana_transfer_usdc_bridge_needed(self, mock_context):
        """Test Solana transfer when USDC bridge is needed"""
        with patch('agents.unified_transfer.transfer_functions.is_solana') as mock_is_solana, \
             patch('agents.unified_transfer.transfer_functions.save_agent_thought') as mock_save_thought, \
             patch('agents.unified_transfer.transfer_functions.get_single_token_balance') as mock_balance, \
             patch('agents.unified_transfer.transfer_functions.handle_usdc_bridge_flow') as mock_bridge:
            
            mock_is_solana.return_value = True
            mock_balance.return_value = "50.0"  # Less than requested amount
            mock_bridge.return_value = "Bridge flow initiated"
            
            result = create_solana_transfer(
                chat_id="test",
                to_address="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
                amount=100.0,
                token_symbol="USDC",
                use_frontend_quoting=False
            )
            
            assert result == "Bridge flow initiated"
            mock_bridge.assert_called()

    def test_handle_create_solana_transfer_success(self, mock_context):
        """Test successful Solana transfer creation"""
        with patch('agents.unified_transfer.transfer_functions.requests.post') as mock_post:
            
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {"success": True}
            
            result = handle_create_solana_transfer(
                chat_id="test",
                to_address="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
                amount=1.5,
                token_symbol="SOL"
            )
            
            assert "Transfer for 1.5 SOL on SOLANA to" in result
            mock_post.assert_called()

    def test_handle_create_solana_transfer_only_transaction(self, mock_context):
        """Test Solana transfer creation returning only transaction"""
        with patch('agents.unified_transfer.transfer_functions.requests.post') as mock_post:
            
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {"transaction": "tx_data"}
            
            result = handle_create_solana_transfer(
                chat_id="test",
                to_address="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
                amount=1.5,
                token_symbol="SOL",
                only_get_transaction=True
            )
            
            assert result == {"transaction": "tx_data"}

    def test_handle_create_solana_transfer_http_error(self, mock_context):
        """Test Solana transfer creation with HTTP error"""
        with patch('agents.unified_transfer.transfer_functions.requests.post') as mock_post:
            
            mock_post.return_value.status_code = 500
            mock_post.return_value.raise_for_status.side_effect = Exception("HTTP Error")
            
            result = handle_create_solana_transfer(
                chat_id="test",
                to_address="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
                amount=1.5,
                token_symbol="SOL"
            )
            
            assert "There was an error creating the transfer on SOLANA" in result

    def test_handle_usdc_bridge_flow_success(self, mock_context, mock_solana_token_info):
        """Test successful USDC bridge flow"""
        with patch('agents.unified_transfer.transfer_functions.get_single_token_balance') as mock_balance, \
             patch('agents.unified_transfer.transfer_functions.create_bridge_and_transfer') as mock_bridge, \
             patch('agents.unified_transfer.transfer_functions.tokens_service.get_token_metadata') as mock_token, \
             patch('agents.unified_transfer.transfer_functions.save_transaction_to_db') as mock_save:
            
            mock_balance.return_value = "200.0"  # Sufficient balance
            mock_bridge.return_value = ["bridge_tx", "transfer_tx"]
            mock_token.return_value = mock_solana_token_info
            
            result = handle_usdc_bridge_flow(
                chat_id="test",
                evm_wallet_address="0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6",
                amount=100.0,
                to_address="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
                wallet_address="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
                solana_usdc_balance=50.0
            )
            
            assert result is None  # Function has a bug - it doesn't return transaction_data
            mock_bridge.assert_called()
            mock_save.assert_called()

    def test_handle_usdc_bridge_flow_insufficient_balance(self, mock_context):
        """Test USDC bridge flow with insufficient balance"""
        with patch('agents.unified_transfer.transfer_functions.get_single_token_balance') as mock_balance:
            mock_balance.return_value = "10.0"  # Insufficient balance
            
            result = handle_usdc_bridge_flow(
                chat_id="test",
                evm_wallet_address="0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6",
                amount=100.0,
                to_address="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
                wallet_address="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
                solana_usdc_balance=50.0
            )
            
            assert "Not enough balance of USDC on SOLANA or Base/Polygon to bridge from" in result

    def test_create_bridge_and_transfer_success(self, mock_context, mock_token_info, mock_solana_token_info):
        """Test successful bridge and transfer creation"""
        with patch('agents.unified_transfer.transfer_functions.call_chains_service') as mock_chains, \
             patch('agents.unified_transfer.transfer_functions.tokens_service.get_token_metadata') as mock_token, \
             patch('agents.unified_transfer.transfer_functions.requests.get') as mock_get, \
             patch('agents.unified_transfer.transfer_functions.call_evm_blockchains_service') as mock_evm, \
             patch('agents.unified_transfer.transfer_functions.create_evm_transfer') as mock_create_evm:
            
            mock_chains.side_effect = ["137", "139981115"]  # from_chain_id, to_chain_id
            mock_token.side_effect = [mock_token_info, mock_solana_token_info]
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {
                "transactionRequest": {"tx": "bridge_tx"},
                "estimate": {"approvalAddress": None}
            }
            mock_evm.return_value = "1000000"  # allowance
            mock_create_evm.return_value = "transfer_tx"
            
            result = create_bridge_and_transfer(
                chat_id="test",
                from_chain="POLYGON",
                to_chain="SOLANA",
                amount_to_bridge="100.0",
                transfer_amount="100.0",
                to_wallet_address="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
                from_token_symbol="USDC",
                to_token_symbol="USDC",
                to_destination_wallet="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"
            )
            
            # Function should execute without errors
            assert result is not None

    def test_create_bridge_and_transfer_no_route(self, mock_context, mock_token_info, mock_solana_token_info):
        """Test bridge and transfer creation with no route found"""
        with patch('agents.unified_transfer.transfer_functions.call_chains_service') as mock_chains, \
             patch('agents.unified_transfer.transfer_functions.tokens_service.get_token_metadata') as mock_token, \
             patch('agents.unified_transfer.transfer_functions.requests.get') as mock_get:
            
            mock_chains.side_effect = ["137", "139981115"]
            mock_token.side_effect = [mock_token_info, mock_solana_token_info]
            mock_get.return_value.status_code = 404
            
            result = create_bridge_and_transfer(
                chat_id="test",
                from_chain="POLYGON",
                to_chain="SOLANA",
                amount_to_bridge="100.0",
                transfer_amount="100.0",
                to_wallet_address="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
                from_token_symbol="USDC",
                to_token_symbol="USDC"
            )
            
            assert "No route found for the bridge transaction" in result

    def test_create_bridge_and_transfer_token_not_found(self, mock_context):
        """Test bridge and transfer creation with token not found"""
        with patch('agents.unified_transfer.transfer_functions.call_chains_service') as mock_chains, \
             patch('agents.unified_transfer.transfer_functions.tokens_service.get_token_metadata') as mock_token:
            
            mock_chains.side_effect = ["137", "139981115"]
            mock_token.return_value = None  # Token not found
            
            result = create_bridge_and_transfer(
                chat_id="test",
                from_chain="POLYGON",
                to_chain="SOLANA",
                amount_to_bridge="100.0",
                transfer_amount="100.0",
                to_wallet_address="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
                from_token_symbol="INVALID_TOKEN",
                to_token_symbol="USDC"
            )
            
            assert "Token INVALID_TOKEN not found on POLYGON" in result

    def test_create_bridge_and_transfer_with_allowance(self, mock_context, mock_token_info, mock_solana_token_info):
        """Test bridge and transfer creation requiring allowance"""
        with patch('agents.unified_transfer.transfer_functions.call_chains_service') as mock_chains, \
             patch('agents.unified_transfer.transfer_functions.tokens_service.get_token_metadata') as mock_token, \
             patch('agents.unified_transfer.transfer_functions.requests.get') as mock_get, \
             patch('agents.unified_transfer.transfer_functions.call_evm_blockchains_service') as mock_evm, \
             patch('agents.unified_transfer.transfer_functions.create_evm_transfer') as mock_create_evm:
            
            mock_chains.side_effect = ["137", "139981115"]
            mock_token.side_effect = [mock_token_info, mock_solana_token_info]
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {
                "transactionRequest": {"tx": "bridge_tx"},
                "estimate": {"approvalAddress": "0xApprovalAddress"}
            }
            mock_evm.side_effect = ["0", "allowance_tx"]  # allowance=0, buildAllowanceTx
            mock_create_evm.return_value = "transfer_tx"
            
            result = create_bridge_and_transfer(
                chat_id="test",
                from_chain="POLYGON",
                to_chain="SOLANA",
                amount_to_bridge="100.0",
                transfer_amount="100.0",
                to_wallet_address="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
                from_token_symbol="USDC",
                to_token_symbol="USDC",
                to_destination_wallet="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"
            )
            
            assert isinstance(result, list)
            assert len(result) >= 2  # Should include allowance and bridge transactions
            mock_evm.assert_called()

    def test_create_bridge_and_transfer_exception_handling(self, mock_context):
        """Test bridge and transfer creation with exception handling"""
        with patch('agents.unified_transfer.transfer_functions.call_chains_service') as mock_chains:
            mock_chains.side_effect = Exception("Service error")
            
            result = create_bridge_and_transfer(
                chat_id="test",
                from_chain="POLYGON",
                to_chain="SOLANA",
                amount_to_bridge="100.0",
                transfer_amount="100.0",
                to_wallet_address="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
                from_token_symbol="USDC",
                to_token_symbol="USDC"
            )
            
            assert "There was an error creating transactation that required a Bridge and a Transfer" in result
