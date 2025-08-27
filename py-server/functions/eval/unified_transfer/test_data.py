"""
Test data for Unified Transfer Agent evaluation.
Contains test cases to verify correct function calls and parameters.
"""

USER_EVM_WALLET_ADDRESS = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
USER_SOLANA_WALLET_ADDRESS = "4QgpmLTy4CQFZKkYG6PGmQqUjX974T6HnrsXXwmnJT2G"

# Test cases for Unified Transfer Agent
TRANSFER_TEST_CASES = [
    {
        "name": "evm_transfer_test",
        "description": "Agent should call create_evm_transfer with correct parameters for EVM chain transfer",
        "task": "send 12 USDC to 0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6 on Polygon",
        "expected_function_calls": [
            {
                "function": "create_evm_transfer",
                "parameters": {
                    "chat_id": "unified_transfer_eval_test",
                    "to_address": "0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6",
                    "amount": 12,
                    "token_symbol": "USDC",
                    "chain_name": "Polygon",
                    "use_frontend_quoting": False,
                },
            }
        ],
    },
    {
        "name": "solana_transfer_test",
        "description": "Agent should call create_solana_transfer with correct parameters for Solana chain transfer",
        "task": "I want to send 5 USDT to 9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM on Solana",
        "expected_function_calls": [
            {
                "function": "create_solana_transfer",
                "parameters": {
                    "chat_id": "unified_transfer_eval_test",
                    "to_address": "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
                    "amount": 5,
                    "token_symbol": "USDT",
                    "use_frontend_quoting": False,
                },
            },
            {
                "function": "handle_create_solana_transfer",
                "parameters": {
                    "chat_id": "unified_transfer_eval_test",
                    "to_address": "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
                    "amount": 5,
                    "token_symbol": "USDT",
                    "only_get_transaction": True,
                },
            },
        ],
    },
    {
        "name": "solana_usdc_bridge_transfer_test",
        "description": "Agent should call create_bridge_and_transfer with correct parameters for Solana USDC transfer",
        "task": "I need to transfer 250 USDC to 9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM on Solana",
        "solana_usdc_balance": 1,
        "expected_function_calls": [
            {
                "function": "create_solana_transfer",
                "parameters": {
                    "chat_id": "unified_transfer_eval_test",
                    "to_address": "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
                    "amount": 250,
                    "token_symbol": "USDC",
                    "use_frontend_quoting": False,
                },
            },
            {
                "function": "handle_usdc_bridge_flow",
                "parameters": {
                    "chat_id": "unified_transfer_eval_test",
                    "evm_wallet_address": USER_EVM_WALLET_ADDRESS,
                    "amount": 250,
                    "to_address": "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
                    "wallet_address": USER_SOLANA_WALLET_ADDRESS,
                    "solana_usdc_balance": 1,
                },
            },
        ],
    },
    {
        "name": "wrong_chain_wallet_test",
        "description": "Agent should not call any function when trying to transfer on BASE with a Solana destination wallet",
        "task": "Please send 0.5 ETH to 9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM on BASE",
        "expected_function_calls": [],
    },
    {
        "name": "incomplete_destination_address_evm_test",
        "description": "Agent should not call any function when trying to transfer on BASE with an incomplete destination address",
        "task": "Can you transfer 0.5 ETH to 0x742d35Cc6634C0532925a3b8D4C9db96C4b4d on BASE",
        "expected_function_calls": [],
    },
    {
        "name": "incomplete_destination_address_solana_test",
        "description": "Agent should not call any function when trying to transfer on SOLANA with a incomplete destination address",
        "task": "I'd like to send 10 USDC to 9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYzYtAWWM on Solana",
        "expected_function_calls": [],
    },
    {
        "name": "transfer_negative_amount_test",
        "description": "Agent should not call any function when trying to transfer negative amount",
        "task": "Transfer -5 USDC to 0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6 on Avalanche for me",
        "expected_function_calls": [],
    },
    {
        "name": "transfer_zero_amount_test",
        "description": "Agent should not call any function when trying to transfer zero amount",
        "task": "Send 0 AERO to 0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6 on BASE please",
        "expected_function_calls": [],
    },
    {
        "name": "unsupported_chain_test",
        "description": "Agent should not call any function when trying to transfer on unsupported chain",
        "task": "I want to transfer 10 USDC to 0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6 on COSMOS",
        "expected_function_calls": [],
    },
    {
        "name": "malformed_task_test",
        "description": "Agent should not call any function when trying to transfer with malformed request",
        "task": "send money to someone",
        "expected_function_calls": [],
    },
    {
        "name": "very_small_amount_test",
        "description": "Agent should call create_evm_transfer with correct parameters even with very small amount",
        "task": "Please transfer 0.0001 USDC to 0x23eD50dB3e7469695DD30FFD22a7B42716A338FC on BINANCE",
        "expected_function_calls": [
            {
                "function": "create_evm_transfer",
                "parameters": {
                    "chat_id": "unified_transfer_eval_test",
                    "to_address": "0x23eD50dB3e7469695DD30FFD22a7B42716A338FC",
                    "amount": 0.0001,
                    "token_symbol": "USDC",
                    "chain_name": "BINANCE",
                    "use_frontend_quoting": False,
                },
            }
        ],
    },
    {
        "name": "very_large_amount_test",
        "description": "Agent should call create_solana_transfer with correct parameters even with very large amount",
        "task": "I need to send 123456789 GRIFT to 9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM on SOLANA",
        "expected_function_calls": [
            {
                "function": "create_solana_transfer",
                "parameters": {
                    "chat_id": "unified_transfer_eval_test",
                    "to_address": "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
                    "amount": 123456789,
                    "token_symbol": "GRIFT",
                    "use_frontend_quoting": False,
                },
            },
            {
                "function": "handle_create_solana_transfer",
                "parameters": {
                    "chat_id": "unified_transfer_eval_test",
                    "to_address": "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
                    "amount": 123456789,
                    "token_symbol": "GRIFT",
                    "only_get_transaction": True,
                },
            },
        ],
    },
    {
        "name": "two_transfers_same_prompt",
        "description": "Agent should call the correct functions even if 2 transfers are requested in the same prompt",
        "task": "Please transfer 5 BNB to 0x23eD50dB3e7469695DD30FFD22a7B42716A338FC on BINANCE and 1 USDT on Solana to 9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
        "expected_function_calls": [
            {
                "function": "create_evm_transfer",
                "parameters": {
                    "chat_id": "unified_transfer_eval_test",
                    "to_address": "0x23eD50dB3e7469695DD30FFD22a7B42716A338FC",
                    "amount": 5,
                    "token_symbol": "BNB",
                    "chain_name": "BINANCE",
                    "use_frontend_quoting": False,
                },
            },
            {
                "function": "create_solana_transfer",
                "parameters": {
                    "chat_id": "unified_transfer_eval_test",
                    "to_address": "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
                    "amount": 1,
                    "token_symbol": "USDT",
                    "use_frontend_quoting": False,
                },
            },
            {
                "function": "handle_create_solana_transfer",
                "parameters": {
                    "chat_id": "unified_transfer_eval_test",
                    "to_address": "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
                    "amount": 1,
                    "token_symbol": "USDT",
                    "only_get_transaction": True,
                },
            },
        ],
    },
    {
        "name": "different_prompting_test_1",
        "description": "Agent should handle different ways to ask for a transfer",
        "task": "Move 1 SOL to 9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM using the Solana blockchain",
        "expected_function_calls": [
            {
                "function": "create_solana_transfer",
                "parameters": {
                    "chat_id": "unified_transfer_eval_test",
                    "to_address": "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
                    "amount": 1,
                    "token_symbol": "SOL",
                    "use_frontend_quoting": False,
                },
            },
            {
                "function": "handle_create_solana_transfer",
                "parameters": {
                    "chat_id": "unified_transfer_eval_test",
                    "to_address": "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
                    "amount": 1,
                    "token_symbol": "SOL",
                    "only_get_transaction": True,
                },
            },
        ],
    },
    {
        "name": "different_prompting_test_2",
        "description": "Agent should handle different ways to ask for a transfer",
        "task": "Initiate a transfer of 1 USDT to wallet 9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM on the blockchain of Solana",
        "expected_function_calls": [
            {
                "function": "create_solana_transfer",
                "parameters": {
                    "chat_id": "unified_transfer_eval_test",
                    "to_address": "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
                    "amount": 1,
                    "token_symbol": "USDT",
                    "use_frontend_quoting": False,
                },
            },
            {
                "function": "handle_create_solana_transfer",
                "parameters": {
                    "chat_id": "unified_transfer_eval_test",
                    "to_address": "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
                    "amount": 1,
                    "token_symbol": "USDT",
                    "only_get_transaction": True,
                },
            },
        ],
    },
    {
        "name": "different_prompting_test_3",
        "description": "Agent should handle different ways to ask for a transfer",
        "task": "Take out 5 USDT of my wallet and move it to 0x23eD50dB3e7469695DD30FFD22a7B42716A338FC on POLGYON",
        "expected_function_calls": [
            {
                "function": "create_evm_transfer",
                "parameters": {
                    "chat_id": "unified_transfer_eval_test",
                    "to_address": "0x23eD50dB3e7469695DD30FFD22a7B42716A338FC",
                    "amount": 5,
                    "token_symbol": "USDT",
                    "chain_name": "POLYGON",
                    "use_frontend_quoting": False,
                },
            }
        ],
    },
    {
        "name": "different_prompting_test_4",
        "description": "Agent should handle different ways to ask for a transfer",
        "task": "Forward 2.5 USDC to 0x23eD50dB3e7469695DD30FFD22a7B42716A338FC on Avalanche",
        "expected_function_calls": [
            {
                "function": "create_evm_transfer",
                "parameters": {
                    "chat_id": "unified_transfer_eval_test",
                    "to_address": "0x23eD50dB3e7469695DD30FFD22a7B42716A338FC",
                    "amount": 2.5,
                    "token_symbol": "USDC",
                    "chain_name": "Avalanche",
                    "use_frontend_quoting": False,
                },
            }
        ],
    },
    {
        "name": "no_chain_evm_test",
        "description": "Agent should handle missing source chain by asking user or using default",
        "task": "Send 10 USDC to 0x23eD50dB3e7469695DD30FFD22a7B42716A338FC",
        "expected_function_calls": [],
    },
    {
        "name": "nonexistent_token_test",
        "description": "Agent should handle nonexistent token gracefully (function may be called but will fail internally)",
        "task": "Send 50 TINMONTOK to 0x23eD50dB3e7469695DD30FFD22a7B42716A338FC on Polygon",
        "expected_function_calls": [
            {
                "function": "create_evm_transfer",
                "parameters": {
                    "chat_id": "unified_transfer_eval_test",
                    "to_address": "0x23eD50dB3e7469695DD30FFD22a7B42716A338FC",
                    "amount": 50,
                    "token_symbol": "TINMONTOK",
                    "chain_name": "Polygon",
                    "use_frontend_quoting": False,
                },
            }
        ],  # Function will be called but will fail internally due to nonexistent token
    },
    {
        "name": "nonexistent_chain_test",
        "description": "Agent should handle nonexistent chain gracefully (function may be called but will fail internally)",
        "task": "Transfer 25 USDC to 0x23eD50dB3e7469695DD30FFD22a7B42716A338FC on DOODOOCHAIN",
        "expected_function_calls": [],
    },
]
