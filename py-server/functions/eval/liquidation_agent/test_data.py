USER_EVM_WALLET_ADDRESS = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
USER_SOLANA_WALLET_ADDRESS = "4QgpmLTy4CQFZKkYG6PGmQqUjX974T6HnrsXXwmnJT2G"

# Test cases for Liquidation Agent
LIQUIDATION_TEST_CASES = [
    {
        "name": "basic_liquidation_test",
        "description": "Agent should call liquidate_all_assets with default USDC token",
        "task": "liquidate all my assets",
        "expected_function_calls": [
            {
                "function": "liquidate_all_assets",
                "parameters": {
                    "chat_id": "liquidation_eval_test",
                    "to_token": "USDC",
                },
            }
        ],
    },
    {
        "name": "liquidation_with_usdt_test",
        "description": "Agent should call liquidate_all_assets with USDT token specified",
        "task": "convert all my tokens to USDT",
        "expected_function_calls": [
            {
                "function": "liquidate_all_assets",
                "parameters": {
                    "chat_id": "liquidation_eval_test",
                    "to_token": "USDT",
                },
            }
        ],
    },
    {
        "name": "liquidation_polygon_specific_test",
        "description": "Agent should call liquidate_all_assets when user specifies Polygon chain",
        "task": "liquidate all of my assets on Polygon",
        "expected_function_calls": [
            {
                "function": "liquidate_all_assets",
                "parameters": {
                    "chat_id": "liquidation_eval_test",
                    "to_token": "USDC",
                },
            }
        ],
    },
    {
        "name": "liquidation_avalanche_to_solana_test",
        "description": "Agent should call liquidate_all_assets when user specifies Avalanche to Solana conversion",
        "task": "convert all of my tokens on Avalanche to Solana",
        "expected_function_calls": [
            {
                "function": "liquidate_all_assets",
                "parameters": {
                    "chat_id": "liquidation_eval_test",
                    "to_token": "USDC",
                },
            }
        ],
    },
    {
        "name": "liquidation_ethereum_specific_test",
        "description": "Agent should call liquidate_all_assets when user specifies ETH token",
        "task": "liquidate all my ETH",
        "expected_function_calls": [
            {
                "function": "liquidate_all_assets",
                "parameters": {
                    "chat_id": "liquidation_eval_test",
                    "to_token": "USDC",
                },
            }
        ],
    },
    {
        "name": "liquidation_to_dai_test",
        "description": "Agent should call liquidate_all_assets when user specifies DAI as target token",
        "task": "liquidate all my assets to DAI",
        "expected_function_calls": [
            {
                "function": "liquidate_all_assets",
                "parameters": {
                    "chat_id": "liquidation_eval_test",
                    "to_token": "DAI",
                },
            }
        ],
    },
    {
        "name": "liquidation_to_tusd_test",
        "description": "Agent should call liquidate_all_assets when user specifies TUSD as target token",
        "task": "liquidate my assets to TUSD",
        "expected_function_calls": [
            {
                "function": "liquidate_all_assets",
                "parameters": {
                    "chat_id": "liquidation_eval_test",
                    "to_token": "TUSD",
                },
            }
        ],
    },
    {
        "name": "liquidation_to_bnb_test",
        "description": "Agent should call liquidate_all_assets when user specifies BNB as target token",
        "task": "liquidate all my assets to BNB",
        "expected_function_calls": [
            {
                "function": "liquidate_all_assets",
                "parameters": {
                    "chat_id": "liquidation_eval_test",
                    "to_token": "BNB",
                },
            }
        ],
    },
    {
        "name": "liquidation_to_usdt_test",
        "description": "Agent should call liquidate_all_assets when user specifies USDT as target token",
        "task": "liquidate all my assets to USDT",
        "expected_function_calls": [
            {
                "function": "liquidate_all_assets",
                "parameters": {
                    "chat_id": "liquidation_eval_test",
                    "to_token": "USDT",
                },
            }
        ],
    },
    {
        "name": "liquidation_consolidate_test",
        "description": "Agent should call liquidate_all_assets when user wants to consolidate portfolio",
        "task": "consolidate my portfolio",
        "expected_function_calls": [
            {
                "function": "liquidate_all_assets",
                "parameters": {
                    "chat_id": "liquidation_eval_test",
                    "to_token": "USDC",
                },
            }
        ],
    },
    {
        "name": "liquidation_everything_test",
        "description": "Agent should call liquidate_all_assets when user says liquidate everything",
        "task": "liquidate everything",
        "expected_function_calls": [
            {
                "function": "liquidate_all_assets",
                "parameters": {
                    "chat_id": "liquidation_eval_test",
                    "to_token": "USDC",
                },
            }
        ],
    },
    {
        "name": "liquidation_convert_all_test",
        "description": "Agent should call liquidate_all_assets when user wants to convert all tokens",
        "task": "convert all my tokens",
        "expected_function_calls": [
            {
                "function": "liquidate_all_assets",
                "parameters": {
                    "chat_id": "liquidation_eval_test",
                    "to_token": "USDC",
                },
            }
        ],
    },
    {
        "name": "liquidation_portfolio_cleanup_test",
        "description": "Agent should call liquidate_all_assets for portfolio cleanup",
        "task": "clean up my portfolio by liquidating all assets",
        "expected_function_calls": [
            {
                "function": "liquidate_all_assets",
                "parameters": {
                    "chat_id": "liquidation_eval_test",
                    "to_token": "USDC",
                },
            }
        ],
    },
    {
        "name": "liquidation_sell_all_test",
        "description": "Agent should call liquidate_all_assets when user wants to sell all",
        "task": "sell all my tokens",
        "expected_function_calls": [
            {
                "function": "liquidate_all_assets",
                "parameters": {
                    "chat_id": "liquidation_eval_test",
                    "to_token": "USDC",
                },
            }
        ],
    },
    {
        "name": "liquidation_clear_portfolio_test",
        "description": "Agent should call liquidate_all_assets to clear portfolio",
        "task": "clear my portfolio",
        "expected_function_calls": [
            {
                "function": "liquidate_all_assets",
                "parameters": {
                    "chat_id": "liquidation_eval_test",
                    "to_token": "USDC",
                },
            }
        ],
    },
    {
        "name": "liquidation_convert_portfolio_test",
        "description": "Agent should call liquidate_all_assets to convert portfolio",
        "task": "convert my entire portfolio to cash",
        "expected_function_calls": [
            {
                "function": "liquidate_all_assets",
                "parameters": {
                    "chat_id": "liquidation_eval_test",
                    "to_token": "USDC",
                },
            }
        ],
    },
    {
        "name": "liquidation_cash_out_test",
        "description": "Agent should call liquidate_all_assets when user wants to cash out",
        "task": "cash out all my assets",
        "expected_function_calls": [
            {
                "function": "liquidate_all_assets",
                "parameters": {
                    "chat_id": "liquidation_eval_test",
                    "to_token": "USDC",
                },
            }
        ],
    },
    {
        "name": "liquidation_exit_positions_test",
        "description": "Agent should call liquidate_all_assets when user wants to exit all positions",
        "task": "exit all my positions",
        "expected_function_calls": [
            {
                "function": "liquidate_all_assets",
                "parameters": {
                    "chat_id": "liquidation_eval_test",
                    "to_token": "USDC",
                },
            }
        ],
    },
    {
        "name": "liquidation_unwind_portfolio_test",
        "description": "Agent should call liquidate_all_assets when user wants to unwind portfolio",
        "task": "unwind my portfolio",
        "expected_function_calls": [
            {
                "function": "liquidate_all_assets",
                "parameters": {
                    "chat_id": "liquidation_eval_test",
                    "to_token": "USDC",
                },
            }
        ],
    },
    {
        "name": "liquidation_dump_all_test",
        "description": "Agent should call liquidate_all_assets when user uses 'dump' terminology",
        "task": "dump all my assets",
        "expected_function_calls": [
            {
                "function": "liquidate_all_assets",
                "parameters": {
                    "chat_id": "liquidation_eval_test",
                    "to_token": "USDC",
                },
            }
        ],
    },
    {
        "name": "liquidation_offload_test",
        "description": "Agent should call liquidate_all_assets when user wants to offload assets",
        "task": "offload all my tokens",
        "expected_function_calls": [
            {
                "function": "liquidate_all_assets",
                "parameters": {
                    "chat_id": "liquidation_eval_test",
                    "to_token": "USDC",
                },
            }
        ],
    },
    {
        "name": "non_liquidation_request_test",
        "description": "Agent should not call liquidate_all_assets for non-liquidation requests",
        "task": "what's my balance?",
        "expected_function_calls": [],
    },
    {
        "name": "partial_liquidation_request_test",
        "description": "Agent should not call liquidate_all_assets for partial liquidation requests",
        "task": "sell half of my ETH",
        "expected_function_calls": [],
    },
    {
        "name": "specific_token_request_test",
        "description": "Agent should not call liquidate_all_assets for specific token requests",
        "task": "convert my SOL to USDC",
        "expected_function_calls": [],
    },
    {
        "name": "balance_check_request_test",
        "description": "Agent should not call liquidate_all_assets for balance check requests",
        "task": "show me my portfolio",
        "expected_function_calls": [],
    },
    {
        "name": "transfer_request_test",
        "description": "Agent should not call liquidate_all_assets for transfer requests",
        "task": "send 100 USDC to 0x123...",
        "expected_function_calls": [],
    },
    {
        "name": "partial_chain_liquidation_test",
        "description": "Agent should not call liquidate_all_assets for partial chain liquidation",
        "task": "sell some of my tokens on Polygon",
        "expected_function_calls": [],
    },
    {
        "name": "specific_amount_liquidation_test",
        "description": "Agent should not call liquidate_all_assets for specific amount requests",
        "task": "convert 1000 USDC worth of my tokens",
        "expected_function_calls": [],
    },
    {
        "name": "portfolio_rebalance_test",
        "description": "Agent should not call liquidate_all_assets for rebalancing requests",
        "task": "rebalance my portfolio to 60% ETH, 40% USDC",
        "expected_function_calls": [],
    },
]