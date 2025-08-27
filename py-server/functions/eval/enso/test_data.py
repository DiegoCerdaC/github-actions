"""
Test data for Enso Agent evaluation.
Contains test cases to verify correct function calls and parameters for DeFi transactions.
"""

USER_EVM_WALLET_ADDRESS = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"

# Test cases for Enso Agent - categorized by type for easier evaluation
ENSO_TEST_CASES = {
    "DEPOSITS": [
        {
            "name": "basic_deposit_test",
            "description": "Agent should call defi_quote with correct parameters for basic deposit",
            "task": "Deposit 15 USDC on aave",
            "expected_function_calls": [
                {
                    "function": "defi_quote",
                    "parameters": {
                        "token": "USDC",
                        "chat_id": "enso_eval_test",
                        "is_withdraw": False,
                        "amount": "15",
                        "from_chain": None,
                        "protocol": "aave",
                        "defi_token_symbol": None,
                        "use_frontend_quoting": True,
                    },
                }
            ],
        },
        {
            "name": "different_prompt_deposit_test",
            "description": "Agent should understand natural language deposit request",
            "task": "I want to put 15 USDC on aave to get some yield",
            "expected_function_calls": [
                {
                    "function": "defi_quote",
                    "parameters": {
                        "token": "USDC",
                        "chat_id": "enso_eval_test",
                        "is_withdraw": False,
                        "amount": "15",
                        "from_chain": None,
                        "protocol": "aave",
                        "defi_token_symbol": None,
                        "use_frontend_quoting": True,
                    },
                }
            ],
        },
        {
            "name": "default_token_test",
            "description": "Agent should use USDC as default when no token specified",
            "task": "Deposit 25 on morpho",
            "expected_function_calls": [
                {
                    "function": "defi_quote",
                    "parameters": {
                        "token": "USDC",
                        "chat_id": "enso_eval_test",
                        "is_withdraw": False,
                        "amount": "25",
                        "from_chain": None,
                        "protocol": "morpho",
                        "defi_token_symbol": None,
                        "use_frontend_quoting": True,
                    },
                }
            ],
        },
        {
            "name": "default_amount_test",
            "description": "Agent should use None as amount when no amount specified",
            "task": "Deposit USDT on aave",
            "expected_function_calls": [
                {
                    "function": "defi_quote",
                    "parameters": {
                        "token": "USDT",
                        "chat_id": "enso_eval_test",
                        "is_withdraw": False,
                        "amount": None,
                        "from_chain": None,
                        "protocol": "aave",
                        "defi_token_symbol": None,
                        "use_frontend_quoting": True,
                    },
                }
            ],
        },
        {
            "name": "chain_specified_test",
            "description": "Agent should handle chain specification correctly",
            "task": "Deposit 50 USDC on aave on Base",
            "expected_function_calls": [
                {
                    "function": "defi_quote",
                    "parameters": {
                        "token": "USDC",
                        "chat_id": "enso_eval_test",
                        "is_withdraw": False,
                        "amount": "50",
                        "from_chain": "BASE",
                        "protocol": "aave",
                        "defi_token_symbol": None,
                        "use_frontend_quoting": True,
                    },
                }
            ],
        },
        {
            "name": "weth_deposit_test",
            "description": "Agent should handle ETH deposits correctly",
            "task": "I want to deposit 1 ETH on aave to earn interest",
            "expected_function_calls": [
                {
                    "function": "defi_quote",
                    "parameters": {
                        "token": "ETH",
                        "chat_id": "enso_eval_test",
                        "is_withdraw": False,
                        "amount": "1",
                        "from_chain": None,
                        "protocol": "aave",
                        "defi_token_symbol": None,
                        "use_frontend_quoting": True,
                    },
                }
            ],
        },
        {
            "name": "casual_language_test",
            "description": "Agent should understand casual language expressions",
            "task": "Hey, can you help me put some money in aave? I have 30 USDC",
            "expected_function_calls": [
                {
                    "function": "defi_quote",
                    "parameters": {
                        "token": "USDC",
                        "chat_id": "enso_eval_test",
                        "is_withdraw": False,
                        "amount": "30",
                        "from_chain": None,
                        "protocol": "aave",
                        "defi_token_symbol": None,
                        "use_frontend_quoting": True,
                    },
                }
            ],
        },
        {
            "name": "yield_farming_test",
            "description": "Agent should understand yield farming terminology",
            "task": "I want to start yield farming with 500 USDC on morpho",
            "expected_function_calls": [
                {
                    "function": "defi_quote",
                    "parameters": {
                        "token": "USDC",
                        "chat_id": "enso_eval_test",
                        "is_withdraw": False,
                        "amount": "500",
                        "from_chain": None,
                        "protocol": "morpho",
                        "defi_token_symbol": None,
                        "use_frontend_quoting": True,
                    },
                }
            ],
        },
        {
            "name": "liquidity_provision_test",
            "description": "Agent should understand liquidity provision requests",
            "task": "Add 200 USDT to my aave position on BASE",
            "expected_function_calls": [
                {
                    "function": "defi_quote",
                    "parameters": {
                        "token": "USDT",
                        "chat_id": "enso_eval_test",
                        "is_withdraw": False,
                        "amount": "200",
                        "from_chain": "BASE",
                        "protocol": "aave",
                        "defi_token_symbol": None,
                        "use_frontend_quoting": True,
                    },
                }
            ],
        },
        {
            "name": "defi_token_specified_test",
            "description": "Agent should handle specific DeFi token symbol",
            "task": "Deposit 100 USDC to get aBaseUSDC on aave",
            "expected_function_calls": [
                {
                    "function": "defi_quote",
                    "parameters": {
                        "token": "USDC",
                        "chat_id": "enso_eval_test",
                        "is_withdraw": False,
                        "amount": "100",
                        "from_chain": None,
                        "protocol": "aave",
                        "defi_token_symbol": "aBaseUSDC",
                        "use_frontend_quoting": True,
                    },
                }
            ],
        },
    ],
    "WITHDRAW": [
        {
            "name": "withdraw_test",
            "description": "Agent should call defi_quote with correct parameters for withdrawal",
            "task": "Withdraw 10 USDC from morpho",
            "expected_function_calls": [
                {
                    "function": "defi_quote",
                    "parameters": {
                        "token": "USDC",
                        "chat_id": "enso_eval_test",
                        "is_withdraw": True,
                        "amount": "10",
                        "from_chain": None,
                        "protocol": "morpho",
                        "defi_token_symbol": None,
                        "use_frontend_quoting": True,
                    },
                }
            ],
        },
        {
            "name": "withdraw_natural_language_test",
            "description": "Agent should understand natural language withdrawal request",
            "task": "I need to take out 10 USDC from my morpho position",
            "expected_function_calls": [
                {
                    "function": "defi_quote",
                    "parameters": {
                        "token": "USDC",
                        "chat_id": "enso_eval_test",
                        "is_withdraw": True,
                        "amount": "10",
                        "from_chain": None,
                        "protocol": "morpho",
                        "defi_token_symbol": None,
                        "use_frontend_quoting": True,
                    },
                }
            ],
        },
        {
            "name": "emergency_withdraw_test",
            "description": "Agent should understand urgent withdrawal requests",
            "task": "Emergency! I need to pull out all my USDC from aave right now",
            "expected_function_calls": [
                {
                    "function": "defi_quote",
                    "parameters": {
                        "token": "USDC",
                        "chat_id": "enso_eval_test",
                        "is_withdraw": True,
                        "amount": None,
                        "from_chain": None,
                        "protocol": "aave",
                        "defi_token_symbol": None,
                        "use_frontend_quoting": True,
                    },
                }
            ],
        },
        {
            "name": "withdraw_specific_amount_and_protocol_test",
            "description": "Agent should handle specific withdrawal amounts with different tokens",
            "task": "Withdraw 25 USDT from my morpho position on Base",
            "expected_function_calls": [
                {
                    "function": "defi_quote",
                    "parameters": {
                        "token": "USDT",
                        "chat_id": "enso_eval_test",
                        "is_withdraw": True,
                        "amount": "25",
                        "from_chain": "BASE",
                        "protocol": "morpho",
                        "defi_token_symbol": None,
                        "use_frontend_quoting": True,
                    },
                }
            ],
        },
        {
            "name": "withdraw_casual_language_test",
            "description": "Agent should understand casual withdrawal language",
            "task": "Hey, I want to take my money out of aave, I want to get USDT back",
            "expected_function_calls": [
                {
                    "function": "defi_quote",
                    "parameters": {
                        "token": "USDT",
                        "chat_id": "enso_eval_test",
                        "is_withdraw": True,
                        "amount": None,
                        "from_chain": None,
                        "protocol": "aave",
                        "defi_token_symbol": None,
                        "use_frontend_quoting": True,
                    },
                }
            ],
        },
    ],
    "SEMANTIC_CHECK": [
        {
            "name": "wrong_spelling_protocol_test",
            "description": "Agent should handle wrong spelling of protocol",
            "task": "Deposit 50 USDC on morfo on base",
            "expected_function_calls": [
                {
                    "function": "defi_quote",
                    "parameters": {
                        "token": "USDC",
                        "chat_id": "enso_eval_test",
                        "is_withdraw": False,
                        "amount": "50",
                        "from_chain": "Base",
                        "protocol": "morpho",
                        "defi_token_symbol": None,
                        "use_frontend_quoting": True,
                    },
                }
            ],
        },
        {
            "name": "multiple_spelling_errors_test",
            "description": "Agent should handle multiple spelling mistakes in one request",
            "task": "Depsoit 25 USDC on avee on Bse",  # "Depsoit", "avee", "Bse"
            "expected_function_calls": [
                {
                    "function": "defi_quote",
                    "parameters": {
                        "token": "USDC",
                        "chat_id": "enso_eval_test",
                        "is_withdraw": False,
                        "amount": "25",
                        "from_chain": "Base",  # Corrected from "Bse"
                        "protocol": "aave",  # Corrected from "avee"
                        "defi_token_symbol": None,
                        "use_frontend_quoting": True,
                    },
                }
            ],
        },
        {
            "name": "action_word_variations_test",
            "description": "Agent should understand different action words for deposits",
            "task": "Put 75 USDC into aave to earn yield",
            "expected_function_calls": [
                {
                    "function": "defi_quote",
                    "parameters": {
                        "token": "USDC",
                        "chat_id": "enso_eval_test",
                        "is_withdraw": False,
                        "amount": "75",
                        "from_chain": None,
                        "protocol": "aave",
                        "defi_token_symbol": None,
                        "use_frontend_quoting": True,
                    },
                }
            ],
        },
        {
            "name": "withdrawal_synonyms_test",
            "description": "Agent should understand withdrawal synonyms and variations",
            "task": "Pull out my morpho position and give me back USDT",
            "expected_function_calls": [
                {
                    "function": "defi_quote",
                    "parameters": {
                        "token": "USDT",
                        "chat_id": "enso_eval_test",
                        "is_withdraw": True,
                        "amount": None,
                        "from_chain": None,
                        "protocol": "morpho",
                        "defi_token_symbol": None,
                        "use_frontend_quoting": True,
                    },
                }
            ],
        },
    ],
    "ERROR_HANDLING": [
        {
            "name": "not_supported_chain_test",
            "description": "Agent should handle not supported chain",
            "task": "Depsoit 5 USDC on aave on POLYGON",
            "expected_function_calls": [],
        },
        {
            "name": "not_supported_protocol_test",
            "description": "Agent should handle not supported protocol",
            "task": "Deposit 5 USDC on Beefy on BASE",
            "expected_function_calls": [],
        },
        {
            "name": "nonsense_text_on_agent_test",
            "description": "Agent should handle nonsense text on agent",
            "task": "Ramadam ramadam non ipsicus text",
            "expected_function_calls": [],
        },
    ],
}
