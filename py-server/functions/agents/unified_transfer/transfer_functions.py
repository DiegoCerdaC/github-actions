import requests
from typing import Annotated
from config import FIREBASE_SERVER_ENDPOINT

# Utils
from utils.firebase import (
    get_request_ctx,
    set_request_ctx,
    save_ui_message,
    save_agent_thought,
)

# Services
from services.chains import call_chains_service
from services.tokens import tokens_service
from services.transactions import save_transaction_to_db, TransactionType
from services.evm_services import call_evm_blockchains_service
from utils.firebase import save_ui_message
from services.balances import get_single_token_balance
from utils.blockchain_utils import is_evm, is_solana

# Solana specific imports
from solders.pubkey import Pubkey


# Constants
SOL_NATIVE_ADDRESS = "So11111111111111111111111111111111111111112"
SOL_USDC_ADDRESS = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
SOL_USDC_DECIMALS = 6
COMPUTE_BUDGET_PROGRAM_ID = Pubkey.from_string(
    "ComputeBudget111111111111111111111111111111"
)


def _check_and_record_for_evaluation(function_name: str, params: dict) -> str | None:
    """
    Checks for evaluation_mode. If active, records the function call and may return a status message.

    Args:
    - function_name (str): The name of the function being called.
    - params (dict): A dictionary of the parameters passed to the function (e.g., from locals()).

    Returns:
    - str | None: An evaluation status message if execution should stop, otherwise None.
    """
    chat_id = params.get("chat_id")
    if not chat_id:
        return None

    is_evaluation = get_request_ctx(chat_id, "evaluation_mode") or False
    if not is_evaluation:
        return None

    # We are in evaluation mode (make copy to avoid modifying params when rounding amount)
    params_copy = params.copy()

    if function_name in [
        "create_solana_transfer",
        "handle_create_solana_transfer",
        "handle_usdc_bridge_flow",
    ]:
        if "amount" in params_copy and isinstance(params_copy["amount"], (int, float)):
            params_copy["amount"] = round(params_copy["amount"])

    function_call = {"function": function_name, "parameters": params_copy}
    current_calls = get_request_ctx(chat_id, "function_calls") or []
    current_calls.append(function_call)
    set_request_ctx(chat_id, "function_calls", current_calls)

    # For some functions, recording is enough, as it should call more functions. For others, we stop execution (no extra functions will be called)
    if function_name in [
        "create_evm_transfer",
        "handle_create_solana_transfer",
        "handle_usdc_bridge_flow",
    ]:
        return f"Evaluation mode: {function_name} function called"

    return None


def create_evm_transfer(
    chat_id: Annotated[str, "The current chat id"],
    to_address: Annotated[str, "The recipient's wallet address"],
    amount: Annotated[
        float,
        "The amount to send in human readable format (e.g. 1.5, 3, 200.56, 0.00456)",
    ],
    token_symbol: Annotated[
        str,
        "The symbol of the token to send. If sending native token, use the symbol of the native token (e.g. ETH, BNB, POL)",
    ],
    chain_name: Annotated[str, "The name of the chain"],
    use_frontend_quoting: Annotated[
        bool, "Whether to use frontend quoting or not."
    ] = True,
) -> str:
    """
    Assembles a transaction to transfer or send evm token transaction to another wallet address.

    # Parameters:
    - chat_id (str): The current chat id
    - to_address (str): The recipient's wallet address.
    - amount (float): The amount to send in human readable format (e.g. 1.5, 3, 200.56, 0.00456).
    - token_symbol (str): The symbol of the token to send. If sending native token, use the symbol of the native token (e.g. ETH, BNB, POL).
    - chain_name (str): The name of the chain.
    - use_frontend_quoting (bool): Whether to use frontend quoting or not. By default it's True.

    # Returns:
    - str: A message saying that the transaction was created successfully.
    """
    # Check and record for evaluation. Stop execution if in eval mode.
    eval_message = _check_and_record_for_evaluation("create_evm_transfer", locals())
    if eval_message:
        return eval_message

    try:
        if not is_evm(to_address):
            return "Invalid Destination Wallet Address (not an EVM address)."

        save_agent_thought(
            chat_id=chat_id,
            thought=f"Initiating EVM transfer of {amount} {token_symbol} on {chain_name}...",
        )

        if not amount or amount == 0:
            save_agent_thought(
                chat_id=chat_id,
                thought="Transfer failed: Amount not specified",
                isFinalThought=True,
            )
            return "Please specify the amount you want to transfer"

        if not use_frontend_quoting:
            from_chain_id = call_chains_service(
                method="getChainId", chainName=chain_name.upper()
            )

            if not call_chains_service(method="isEvm", chainId=from_chain_id):
                return f"Chain {chain_name} is not an EVM chain."

            url = f"{FIREBASE_SERVER_ENDPOINT}/transfer"
            params = {
                "userId": get_request_ctx(chat_id, "user_id") or "",
                "protocol": "EVM",
                "walletAddress": get_request_ctx(chat_id, "evm_wallet_address"),
                "toAddress": to_address,
                "fromAmount": str(amount),
                "tokenSymbol": token_symbol,
                "chainName": chain_name,
                "chatId": chat_id,
                "render_ui": False,
            }

            response = requests.post(url, json=params)

            if response.status_code != 200:
                response.raise_for_status()
            return response.json()
        else:
            save_ui_message(
                chat_id=chat_id,
                component=TransactionType.TRANSFER.value,
                renderData={
                    "userId": get_request_ctx(chat_id, "user_id") or "",
                    "from_token": token_symbol,
                    "from_amount": str(amount),
                    "wallet_address": get_request_ctx(chat_id, "evm_wallet_address"),
                    "to_address": to_address,
                    "from_chain": chain_name,
                    "to_chain": chain_name,
                    "transaction_type": TransactionType.TRANSFER.value,
                    "protocol": "EVM",
                    "chatId": chat_id,
                },
                thought="Task completed successfully",
                isFinalThought=True,
            )

            return (
                f"I've started the quoting process for your transfer on {chain_name}."
            )
    except Exception as e:
        save_agent_thought(
            chat_id=chat_id,
            thought=f"Error during EVM transfer: {str(e)}",
            isFinalThought=True,
        )
        return f"There was an error creating the transfer on EVM: {str(e)}, please try again later."


def create_solana_transfer(
    chat_id: Annotated[str, "The current chat id"],
    to_address: Annotated[str, "The recipient's wallet address"],
    amount: Annotated[
        float,
        "The amount to send in human readable format (e.g. 1.5, 3, 200.56, 0.00456)",
    ],
    token_symbol: Annotated[
        str,
        "The symbol of the token to send. If sending native token, use the symbol of the native token (e.g. SOL)",
    ],
    use_frontend_quoting: Annotated[
        bool, "Whether to use frontend quoting or not."
    ] = True,
) -> str:
    """
    Assembles a transaction to transfer or send solana token transaction to another wallet address.

    # Parameters:
    - chat_id (str): The current chat id
    - to_address (str): The recipient's wallet address.
    - amount (float): The amount to send in human readable format (e.g. 1.5, 3, 200.56, 0.00456).
    - token_symbol (str): The symbol of the token to send. If sending native token, use the symbol of the native token (e.g. SOL).
    - use_frontend_quoting (bool): Whether to use frontend quoting or not. By default it's True.

    # Returns:
    - str: A message saying that the transaction was created successfully.
    """
    # Check and record for evaluation. Execution continues even in eval mode.

    try:
        if not is_solana(to_address):
            return "Invalid Destination Wallet Address (not a Solana address)."

        _check_and_record_for_evaluation("create_solana_transfer", locals())

        # The original evaluation logic did not stop execution here, so we proceed.
        save_agent_thought(
            chat_id=chat_id,
            thought=f"Initiating Solana transfer of {amount} {token_symbol}...",
        )

        wallet_address = get_request_ctx(chat_id, "solana_wallet_address")
        if not wallet_address:
            raise Exception(
                "Solana Wallet not detected. Please connect your wallet and try again."
            )

        if not amount or amount == 0:
            save_agent_thought(
                chat_id=chat_id,
                thought="Transfer failed: Amount not specified",
                isFinalThought=True,
            )
            return "Please specify the amount you want to transfer"

        if not use_frontend_quoting:
            if token_symbol == "USDC":
                if (
                    get_request_ctx(chat_id, "evaluation_mode")
                    and get_request_ctx(chat_id, "solana_usdc_balance") is not None
                ):
                    solana_usdc_balance = get_request_ctx(
                        chat_id, "solana_usdc_balance"
                    )
                else:
                    solana_usdc_balance = float(
                        get_single_token_balance(wallet_address, "SOLANA", "USDC")
                    )

                if solana_usdc_balance < amount:
                    evm_wallet_address = get_request_ctx(chat_id, "evm_wallet_address")
                    if not evm_wallet_address:
                        raise Exception(
                            "EVM Wallet not detected. Please connect your wallet and try again."
                        )

                    return handle_usdc_bridge_flow(
                        chat_id,
                        evm_wallet_address,
                        amount,
                        to_address,
                        wallet_address,
                        solana_usdc_balance,
                    )

            return handle_create_solana_transfer(
                chat_id, to_address, amount, token_symbol, True
            )
        else:
            save_ui_message(
                chat_id=chat_id,
                component="transfer",
                renderData={
                    "onlyGetTransaction": False,
                    "wallet_address": wallet_address,
                    "userId": get_request_ctx(chat_id, "user_id") or "",
                    "to_address": to_address,
                    "from_amount": str(amount),
                    "from_token": token_symbol,
                    "from_chain": "SOLANA",
                    "to_chain": "SOLANA",
                    "transaction_type": TransactionType.TRANSFER.value,
                    "protocol": "SOLANA",
                    "chatId": chat_id,
                },
                thought="Task completed successfully",
                isFinalThought=True,
            )

            return f"I've started the quoting process for your transfer on SOLANA."
    except Exception as e:
        save_agent_thought(
            chat_id=chat_id,
            thought=f"Error during Solana transfer: {str(e)}",
            isFinalThought=True,
        )
        return f"There was an error building the quote for your transfer on SOLANA, please try again later. Error: {str(e)}"


def handle_create_solana_transfer(
    chat_id: Annotated[str, "The current chat id"],
    to_address: Annotated[str, "The recipient's wallet address"],
    amount: Annotated[
        float,
        "The amount to send in human readable format (e.g. 1.5, 3, 200.56, 0.00456)",
    ],
    token_symbol: Annotated[
        str,
        "The symbol of the token to send. If sending native token, use the symbol of the native token (e.g. SOL)",
    ],
    only_get_transaction: Annotated[
        bool,
        "If True, only the transaction is returned, otherwise the quote is rendered",
    ] = False,
) -> str:
    """
    Creates a transfer on SOLANA

    Args:
    - chat_id (str): The current chat id
    - to_address (str): The recipient's wallet address.
    - amount (float): The amount to send in human readable format (e.g. 1.5, 3, 200.56, 0.00456).
    - token_symbol (str): The symbol of the token to send. If sending native token, use the symbol of the native token (e.g. SOL).

    Returns:
    - str: A message saying that the transaction was created successfully or an error message if the transaction failed.
    """
    # Check and record for evaluation. Stop execution if in eval mode.
    eval_message = _check_and_record_for_evaluation(
        "handle_create_solana_transfer", locals()
    )
    if eval_message:
        return eval_message

    try:
        url = f"{FIREBASE_SERVER_ENDPOINT}/transfer"
        params = {
            "walletAddress": get_request_ctx(chat_id, "solana_wallet_address"),
            "userId": get_request_ctx(chat_id, "user_id") or "",
            "toAddress": to_address,
            "fromAmount": amount,
            "tokenSymbol": token_symbol,
            "chatId": chat_id,
            "protocol": "SOLANA",
            "onlyGetTransaction": False,
            "render_ui": False,
        }
        response = requests.post(url, json=params)
        if response.status_code != 200:
            response.raise_for_status()

        if only_get_transaction:
            return response.json()

        return f"Transfer for {amount} {token_symbol} on SOLANA to {to_address} created successfully."
    except Exception as e:
        return f"There was an error creating the transfer on SOLANA: {str(e)}, please try again later."


def handle_usdc_bridge_flow(
    chat_id: Annotated[str, "The current chat id"],
    evm_wallet_address: Annotated[str, "The wallet EVM wallet address of the user"],
    amount: Annotated[float, "The amount to bridge"],
    to_address: Annotated[
        str, "The address that finally receives everything (final transfer)"
    ],
    wallet_address: Annotated[str, "The SOLANA wallet address of the user"],
    solana_usdc_balance: Annotated[float, "User Solana USDC balance"],
) -> str:
    # Check and record for evaluation. Stop execution if in eval mode.
    eval_message = _check_and_record_for_evaluation("handle_usdc_bridge_flow", locals())
    if eval_message:
        return eval_message

    try:
        if not evm_wallet_address:
            raise Exception(
                "EVM Wallet not detected. Please connect your wallet and try again."
            )

        # Get USDC Balance from POLYGON and BASE
        amount_to_bridge = float(
            float(amount - solana_usdc_balance) * 105 / 100
        )  # 5% surplus

        chains = ["BASE", "POLYGON"]
        chain_to_bridge_from = None
        for chain in chains:
            usdc_balance = float(
                get_single_token_balance(evm_wallet_address, chain, "USDC")
            )

            if float(usdc_balance) > amount_to_bridge:

                chain_to_bridge_from = chain
                break

        if not chain_to_bridge_from:
            raise Exception(
                "Not enough balance of USDC on SOLANA or Base/Polygon to bridge from"
            )

        transactions = create_bridge_and_transfer(
            chat_id,
            from_chain=chain_to_bridge_from,
            to_chain="SOLANA",
            amount_to_bridge=amount_to_bridge,
            transfer_amount=amount,
            to_wallet_address=wallet_address,
            from_token_symbol="USDC",
            to_token_symbol="USDC",
            to_destination_wallet=to_address,
        )

        sol_usdc_token_metadata = tokens_service.get_token_metadata(
            chain="SOLANA", token="USDC"
        )

        transaction_data = {
            "user_id": get_request_ctx(chat_id, "user_id"),
            "chat_id": chat_id,
            "component": "transfer",
            "from_token": sol_usdc_token_metadata,
            "from_amount": float(amount),
            "to_chain": "SOLANA",
            "from_address": wallet_address,
            "to_address": to_address,
            "estimated_time": 0.5,
            "transactions": transactions,
            "protocol_name": "solana",
            "wallet_address": wallet_address,
            "extra_note": f"This transaction includes a bridge from {chain_to_bridge_from} to SOLANA and then a transfer.",
            "wait_for_balance_chain": "SOLANA",
            "wallet_to_check": wallet_address,
            "token_to_check": "USDC",
            "token_address_to_check": SOL_USDC_ADDRESS,
            "expected_amount_to_check": float(amount),
            "transaction_type": TransactionType.TRANSFER.value,
        }

        save_transaction_to_db(transaction_data)

        transaction_data
    except Exception as e:
        return f"There was an error creating the transfer on SOLANA: {str(e)}, please try again later."


def create_bridge_and_transfer(
    chat_id: Annotated[str, "The current chat id"],
    from_chain: Annotated[str, "The name of the origin chain for the bridge"],
    to_chain: Annotated[str, "The name of the destination chain for the bridge"],
    amount_to_bridge: Annotated[
        str, "The amount of tokens to bridge in a float format"
    ],
    transfer_amount: Annotated[
        str, "The amount of tokens to transfer (after the bridge) in a float format"
    ],
    to_wallet_address: Annotated[
        str, "The destination wallet address of the bridge (user wallet)"
    ],
    from_token_symbol: Annotated[str, "The symbol of the origin token"] = "USDC",
    to_token_symbol: Annotated[str, "The symbol of the destination token"] = "USDC",
    to_destination_wallet: Annotated[
        str, "The destination wallet address of the final transfer"
    ] = None,
) -> str:
    """
    Creates a bridge transaction followed by a transfer transaction.
    Supports bridging and transferring USDC between EVM chains and Solana.

    # Parameters:
    - chat_id (str): The current chat id
    - from_chain (str): The name of the origin chain.
    - to_chain (str): The name of the destination chain.
    - amount_to_bridge (str): The amount of tokens to bridge in a float format.
    - transfer_amount (str): The amount of tokens to transfer in a float format.
    - to_wallet_address (str): The destination wallet address.
    - from_token_symbol (str): The symbol of the origin token. By default is USDC.
    - to_token_symbol (str): The symbol of the destination token. By default is USDC.
    - to_destination_wallet (str): The destination wallet address of the final transfer (user wallet).

    # Returns:
    - The message saying that the bridge and transfer transaction was created successfully.
    """
    try:
        # Import required functions
        from services.chains import call_chains_service
        from utils.bignumber import float_to_bignumber_string
        import requests

        from_chain_id = call_chains_service(
            method="getChainId", chainName=from_chain.upper()
        )

        to_chain_id = call_chains_service(
            method="getChainId", chainName=to_chain.upper()
        )
        from_token = tokens_service.get_token_metadata(
            token=from_token_symbol,
            chain=from_chain,
        )

        to_token = tokens_service.get_token_metadata(
            token=to_token_symbol,
            chain=to_chain,
        )

        if not from_token:
            raise Exception(f"Token {from_token_symbol} not found on {from_chain}")
        if not to_token:
            raise Exception(f"Token {to_token_symbol} not found on {to_chain}")

        from_amount_bn = float_to_bignumber_string(
            float(amount_to_bridge), int(from_token.get("decimals", 18))
        )

        # Get wallet addresses from context
        from_wallet_address = (
            get_request_ctx(chat_id, "evm_wallet_address")
            if call_chains_service(method="isEvm", chainId=from_chain_id)
            else get_request_ctx(chat_id, "solana_wallet_address")
        )

        # Build bridge transaction using LiFi API
        response = requests.get(
            f'https://li.quest/v1/quote?fromChain={from_chain_id}&toChain={to_chain_id}&fromToken={str(from_token.get("address", ""))}&toToken={str(to_token.get("address", ""))}&fromAddress={from_wallet_address}&toAddress={to_wallet_address}&fromAmount={from_amount_bn}&slippage=0.03&allowBridges=mayan&integrator=sphereone'
        )

        if response.status_code == 404:
            raise Exception("No route found for the bridge transaction")

        if response.status_code != 200:
            raise Exception("Failed to get bridge quote")

        quote_data = response.json()

        # Process bridge quote and execute transfer
        transactions = []

        # Add bridge transaction
        if quote_data.get("transactionRequest"):
            # Check if allowance needed
            approval_address = quote_data.get("estimate").get("approvalAddress")
            if approval_address:
                # Create allowance transaction
                allowance = call_evm_blockchains_service(
                    method="getAllowance",
                    chain=from_chain,
                    walletAddress=from_wallet_address,
                    tokenAddress=from_token["address"],
                    spenderAddress=approval_address,
                )

                if not allowance:
                    allowance = 0

                if int(allowance) < int(from_amount_bn):

                    allowance_tx = call_evm_blockchains_service(
                        method="buildAllowanceTx",
                        chain=from_chain,
                        walletAddress=from_wallet_address,
                        tokenAddress=from_token["address"],
                        spenderAddress=approval_address,
                        amountBn=from_amount_bn,
                    )

                    if allowance_tx:
                        transactions.append(allowance_tx)

            transactions.append(quote_data["transactionRequest"])

        # Add transfer transaction based on destination chain
        transfer_tx = None
        if call_chains_service(method="isEvm", chainId=to_chain_id):
            transfer_tx = create_evm_transfer(
                chat_id,
                to_destination_wallet,
                float(transfer_amount),
                to_token_symbol,
                to_chain,
            )
            if transfer_tx:
                transactions.append(transfer_tx)
        else:
            transfer_tx = handle_create_solana_transfer(
                chat_id,
                to_destination_wallet,
                float(transfer_amount),
                to_token_symbol,
                True,
            )

            if transfer_tx:
                transactions.append(transfer_tx)

        return transactions
    except Exception as e:
        return f"There was an error creating transactation that required a Bridge and a Transfer: {str(e)}, please try again later."
