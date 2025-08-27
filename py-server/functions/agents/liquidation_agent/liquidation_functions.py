from typing import Annotated
from services.balances import get_wallet_balance, BalanceServiceType
from services.tracing import set_status_ok, set_status_error, tracer, set_attributes
from utils.firebase import get_request_ctx, save_ui_message, save_agent_thought, set_request_ctx
from services.transactions import TransactionType
from agents.drift.drift_functions import get_user_active_orders, get_user_active_positions
from utils.constants import NATIVE_TOKEN_ADDRESS, AVAILABLE_LIQUIDATION_TOKENS
from concurrent.futures import ThreadPoolExecutor, as_completed


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

    # We are in evaluation mode - record the function call
    function_call = {"function": function_name, "parameters": params}
    current_calls = get_request_ctx(chat_id, "function_calls") or []
    current_calls.append(function_call)
    set_request_ctx(chat_id, "function_calls", current_calls)

    # For liquidation, we stop execution in evaluation mode to avoid making real API calls
    return f"Evaluation mode: {function_name} function called"


def get_liquidation_native_token_amount(amount: float, price: float) -> float:
    hold_amount_in_usd = 3 # We are going to hold 3$ in native token
    tokens_to_liquidate =  amount - (hold_amount_in_usd / price)

    return tokens_to_liquidate
    

@tracer.start_as_current_span("liquidate_all_assets")
async def liquidate_all_assets(
    chat_id: Annotated[str, "The current chat id"],
    to_token: Annotated[str, "The token to liquidate to"] = "USDC",
) -> str:
    """
    Liquidates all user assets by showing the liquidation interface.
    This function gets all balances and displays them for liquidation.
    1. Get all user balances from both Solana and EVM chains
    2. Show the liquidation interface with all tokens
    3. Allow users to liquidate everything with decimal precision
    
    Args:
        chat_id: The current chat id
        to_token: The token to liquidate to
    Returns:
        str: Confirmation that liquidation interface is ready
    """
    # Check and record for evaluation. Stop execution if in eval mode.
    eval_message = _check_and_record_for_evaluation("liquidate_all_assets", locals())
    if eval_message:
        return eval_message

    try:
        if to_token not in AVAILABLE_LIQUIDATION_TOKENS:
            return f"Please select a valid FIAT token. ({', '.join(AVAILABLE_LIQUIDATION_TOKENS)})"
        
        evm_wallet_address = get_request_ctx(parentKey=chat_id, key="evm_wallet_address")
        solana_wallet_address = get_request_ctx(parentKey=chat_id, key="solana_wallet_address")
        
        set_attributes({
            "chat_id": chat_id,
        })
        
        save_agent_thought(
            chat_id=chat_id,
            thought="Fetching complete wallet balances for liquidation..."
        )

        tasks = {
            "solana": lambda: get_wallet_balance(solana_wallet_address, BalanceServiceType.SOLANA.value),
            "evm": lambda: get_wallet_balance(evm_wallet_address, BalanceServiceType.EVM.value) if evm_wallet_address else [],
            "drift_balances": lambda: get_user_active_positions(chat_id, False),
            "orders": lambda: get_user_active_orders(chat_id, False, True)
        }

        results = {}
        
        all_balances = []

        with ThreadPoolExecutor(max_workers=2) as executor:
            future_to_key = {executor.submit(task): key for key, task in tasks.items()}

            for future in as_completed(future_to_key):
                key = future_to_key[future]
                try:
                    results[key] = future.result()
                except Exception as e:
                    print(f"Error fetching {key} balances: {str(e)}")
                    results[key] = []

        solana_balances = results.get("solana", [])
        evm_balances = results.get("evm", [])
        drift_balances = results.get("drift_balances", [])
        orders = results.get("orders", [])

        # Process Drift orders
        for order in orders:
            order_id = order.get("orderId", None)
            if not order_id:
                continue
            
            all_balances.append({
                "chain": "SOLANA",
                "address": f"drift-order-{order_id}-{order.get('marketName', '')}",
                "symbol": order.get('marketName', ''),
                "amount": order.get('baseAssetAmount', 0),
                "logo": "https://coin-images.coingecko.com/coins/images/37509/large/DRIFT.png?1715842607",
                "orderId": order_id,
                "direction": order.get("direction", ""),
            })

        # Process Drift balances
        for balance in drift_balances:
            usd_amount = balance.get("price", 0)
            amount = balance.get("amount", 0)
            market = balance.get("market", "")
            all_balances.append({
                    "direction": balance.get("direction", ""),
                    "chain": "SOLANA",
                    "address": f"drift-{market}",
                    "symbol": market,
                    "amount": amount,
                    "logo": "https://coin-images.coingecko.com/coins/images/37509/large/DRIFT.png?1715842607"
                })
        
        # Process Solana balances
        for balance in solana_balances:
            symbol = balance.get("symbol", "")
            if symbol.lower() in ["usdc", "usdt"]:
                continue
            
            usd_amount = balance.get("usd_amount", 0)
            price = balance.get("price", 0)
            amount = balance.get("amount", 0)
            address = balance.get("address", "")
            if usd_amount > 0.1 and "_" not in address:
                if address in NATIVE_TOKEN_ADDRESS:
                    amount = get_liquidation_native_token_amount(amount, price)
                    if (amount < 0):
                        continue

                all_balances.append({
                    "chain": "SOLANA",
                    "address": address,
                    "symbol": balance.get("symbol", ""),
                    "amount": amount,
                    "logo": balance.get("logo_uri", "")
                })
                
        
        # Process EVM balances
        for balance in evm_balances:
            chain = balance.get("chain", "")
            symbol = balance.get("symbol", "")
            if symbol.lower() in ["usdc", "usdt"]:
                continue

            # We need to skip MATIC because covalent returns duplicate balances with POL
            if chain == "POLYGON" and symbol == "MATIC":
                continue
            usd_amount = balance.get("usd_amount", 0)
            price = balance.get("price", 0)
            amount = balance.get("amount", 0)
            address = balance.get("address", "")
            if usd_amount > 0.1:
                if address in NATIVE_TOKEN_ADDRESS:
                    amount = get_liquidation_native_token_amount(amount, price)
                    if (amount < 0):
                        continue

                all_balances.append({
                    "chain": chain,
                    "address": address,
                    "symbol": symbol,
                    "amount": amount,
                    "logo": balance.get("logo_uri", "")
                })
        
        if not all_balances:
            return "No balances found for this wallet address."
        
        save_ui_message(
                chat_id=chat_id,
                component=TransactionType.LIQUIDATION.value,
                renderData={
                    "userId": get_request_ctx(chat_id, "user_id") or "",
                    "evm_wallet_address": get_request_ctx(chat_id, "evm_wallet_address"),
                    "solana_wallet_address": get_request_ctx(chat_id, "solana_wallet_address"),
                    "transaction_type": TransactionType.LIQUIDATION.value,
                    "chatId": chat_id,
                    "liquidation_tokens": all_balances,
                    "to_token_symbol": to_token
                },
                thought="Task completed successfully",
                isFinalThought=True,
            )

        set_status_ok()
        return (
                f"You can now select the tokens you want to liquidate. Note that all liquidated tokens will be converted to fiat token. USDC is the default fiat token."
            )
        
    except Exception as e:
        set_status_error(e)
        return f"Error getting complete wallet balances: {str(e)}"



