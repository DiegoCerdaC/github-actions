from typing import Annotated
from utils.firebase import save_ui_message, get_request_ctx, save_agent_thought
from services.transactions import TransactionType
from services.prices import get_token_price_from_provider, PriceProviderType
from services.tokens import tokens_service
from config import FIREBASE_SERVER_ENDPOINT
import requests
from enum import Enum
from solders.pubkey import Pubkey
from services.balances import get_single_token_balance
from services.prices import PriceProviderType
from agents.unified_transfer.transfer_functions import SOL_USDC_ADDRESS
import services.prices as prices_service

# SUPPORTED PERPS COLLATERAL TOKENS
DRIFT_PERPS_COLLATERAL_TOKENS = [
    "SOL",
    "USDC",
    "USDS",
    "USDT",
    "PYUSDC",
    "JUP",
    "DRIFT",
]

# FOR VAULTS AGENT
SUPPORTED_TOKEN_SYMBOL = "USDC"
SUPPORTED_TOKEN_ADDRESS = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"


class QueryType(Enum):
    USER_ACTIVE_VAULTS = "userActiveVaults"
    USDC_VAULTS_INFO = "usdcVaultsInfo"
    GET_PERPS_MARKETS = "getPerpsMarkets"
    CHECK_USER_HAS_DRIFT_USER_ACCOUNT = "checkUserHasDriftUserAccount"
    GET_USER_ACCOUNT_INFO = "getUserAccountInfo"
    GET_ENABLED_COLLATERAL_TOKENS = "getEnabledCollateralTokens"
    GET_USER_ACTIVE_ORDERS = "getUserActiveOrders"
    GET_USER_ACTIVE_PERPS_POSITIONS = "getUserActivePerpsPositions"


class COLLATERAL_TRANSACTION_TYPE(Enum):
    DEPOSIT = "deposit"
    WITHDRAW = "withdraw"


class ORDER_TYPE(Enum):
    MARKET = "market"
    LIMIT = "limit"


class POSITION_TYPE(Enum):
    LONG = "long"
    SHORT = "short"


def is_token_supported(
    mint_address_or_symbol: Annotated[
        str, "The mint address or symbol to check if it is supported by Lulo."
    ],
) -> bool:
    """
    Check if a token is supported based on its symbol or mint address.
    # Parameter:
        mint_address_or_symbol (str): The token's symbol (e.g., 'USDT') or mint address.
    # Returns:
        bool: True if the token is supported, False otherwise.
    """
    normalized_input = mint_address_or_symbol.lower()

    return (
        normalized_input == SUPPORTED_TOKEN_SYMBOL.lower()
        or normalized_input == SUPPORTED_TOKEN_ADDRESS.lower()
    )


def generate_drift_vault_transaction(
    chat_id: Annotated[str, "The current chat id"],
    mint_address_or_symbol: Annotated[
        str, "The address or symbol of the token to deposit."
    ] = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
    vault_address_or_name: Annotated[
        str, "The address or name of the vault to deposit or withdraw."
    ] = "2r81MPMDjGSrbmGRwzDg6aqhe3t3vbKcrYfpes5bXckS",
    amount: Annotated[str, "The amount of the deposit or withdraw."] = None,
    percentage_to_request_withdraw: Annotated[
        float, "The percentage of the deposit to request withdraw."
    ] = None,
    transaction_type: Annotated[
        str, "The type of the transaction to generate."
    ] = "deposit",
    use_frontend_quoting: Annotated[
        bool, "Whether to use frontend quoting or not."
    ] = True,
):
    """
    Generate a new deposit or withdraw transaction on Drift Vaults which the sending wallet can sign and submit.

    # Parameters:
    - chat_id (str): The current chat id
    - mint_address_or_symbol (str): The mint address (token address) or token symbol to deposit.
    - amount (str): The amount of the deposit or request withdraw. None for 'withdraw' transaction type. None for 'request_withdraw' transaction type if percentage_to_request_withdraw is provided.
    - percentage_to_request_withdraw (float) (Optional): The percentage of the deposit to request withdraw. None for 'deposit' or 'withdraw' transaction type.
    None for 'request_withdraw' transaction type if amount is provided.
    - vault_address_or_name (str): The address or name of the vault to deposit or withdraw from.
    - transaction_type (str): The type of the transaction to generate. It can be 'deposit', 'request_withdraw' or 'withdraw'.
    - use_frontend_quoting (bool) (optional): Whether to use frontend quoting or not. By default it's True.

    # Returns:
    - A message indicating whether the deposit transaction was successfully created.
    """
    try:
        save_agent_thought(
            chat_id=chat_id,
            thought=f"Initiating {transaction_type} transaction process...",
        )

        if use_frontend_quoting:
            if transaction_type not in [
                TransactionType.DEPOSIT.value,
                TransactionType.REQUEST_WITHDRAW.value,
                TransactionType.WITHDRAW.value,
            ]:
                save_agent_thought(
                    chat_id=chat_id,
                    thought="Invalid transaction type provided.",
                    isFinalThought=True,
                )
                return "Invalid transaction type. Please specify 'deposit', 'request_withdraw' or 'withdraw'."

            if transaction_type == TransactionType.DEPOSIT.value:
                if not amount or float(amount) == 0:
                    save_agent_thought(
                        chat_id=chat_id,
                        thought="No deposit amount specified.",
                        isFinalThought=True,
                    )
                    return "Please specify the amount you want to deposit"

            if transaction_type == TransactionType.REQUEST_WITHDRAW.value:
                if (
                    not amount or float(amount) == 0
                ) and not percentage_to_request_withdraw:
                    save_agent_thought(
                        chat_id=chat_id,
                        thought="No withdrawal amount or percentage specified.",
                        isFinalThought=True,
                    )
                    return "Please specify the amount or the percentage you want to request withdraw"

            # Check if token is supported
            save_agent_thought(
                chat_id=chat_id,
                thought=f"Checking if token {mint_address_or_symbol} is supported...",
            )
            if not is_token_supported(mint_address_or_symbol):
                save_agent_thought(
                    chat_id=chat_id,
                    thought=f"Token {mint_address_or_symbol} is not supported.",
                    isFinalThought=True,
                )
                return (
                    f"Token {mint_address_or_symbol} not supported yet on Drift Agent"
                )

            save_ui_message(
                chat_id=chat_id,
                component="drift",
                renderData={
                    "currentToken": mint_address_or_symbol,
                    "amount": float(amount) if amount else None,
                    "percentage_to_request_withdraw": (
                        percentage_to_request_withdraw
                        if percentage_to_request_withdraw
                        else None
                    ),
                    "vault_address_or_name": vault_address_or_name,
                    "transaction_type": transaction_type,
                },
                thought="Task completed successfully",
                isFinalThought=True,
            )

            return f"The quoting process for the {transaction_type} transaction was initiated."
        else:
            solana_wallet_address = get_request_ctx(
                parentKey=chat_id, key="solana_wallet_address"
            )
            if not solana_wallet_address:
                return "No wallet address found."
            url = f"{FIREBASE_SERVER_ENDPOINT}/quote"

            params = {
                "chatId": chat_id,
                "userId": get_request_ctx(parentKey=chat_id, key="user_id") or "",
                "protocol": "DRIFT_VAULTS",
                "walletAddress": solana_wallet_address,
                "fromAmount": amount,
                "vaultAddressOrName": vault_address_or_name,
                "percentageToRequestWithdraw": percentage_to_request_withdraw,
                "transactionType": transaction_type,
            }

            response = requests.post(url, json=params)
            if response.status_code != 200:
                response.raise_for_status()
            return response.json()
    except Exception as e:
        save_agent_thought(
            chat_id=chat_id,
            thought=f"Error generating transaction: {str(e)}",
            isFinalThought=True,
        )
        return f"Error generating deposit transaction because: {e}"


def select_vault_to_withdraw_from(
    chat_id: Annotated[str, "The current chat id"],
    transaction_type: Annotated[
        str,
        "The type of the transaction to generate. It can be 'withdraw' or 'request_withdraw'",
    ],
    use_frontend_quoting: Annotated[
        bool, "Whether to use frontend quoting or not."
    ] = True,
):
    """
    Displays the user's vaults to select one to withdraw or request withdrawal from.
    If the user wants to request a withdrawal or withdraw from a vault, but he doesn't provide the vault address or name, use this function to show him the options and ask him to select one.

    # Parameters:
    - chat_id (str): The current chat id
    - transaction_type (str): The type of the transaction to generate. It can be 'withdraw' or 'request_withdraw'
    - use_frontend_quoting (bool) (optional): Whether to use frontend quoting or not. By default it's True.

    # Returns:
    """
    try:
        save_agent_thought(
            chat_id=chat_id,
            thought=f"Fetching available vaults for {transaction_type}...",
        )

        if use_frontend_quoting:
            save_ui_message(
                chat_id=chat_id,
                component="drift_withdraw_options",
                renderData={
                    "token_address": SUPPORTED_TOKEN_ADDRESS,
                    "transaction_type": transaction_type,
                },
                thought="Vault options prepared for selection.",
                isFinalThought=True,
            )

            return f"Please select the vault you want to {transaction_type} from."
        else:
            solana_wallet_address = get_request_ctx(
                parentKey=chat_id, key="solana_wallet_address"
            )
            if not solana_wallet_address:
                return "No wallet address found."

            url = f"{FIREBASE_SERVER_ENDPOINT}/queryDrift?queryType={QueryType.USER_ACTIVE_VAULTS.value}&userWalletAddress={solana_wallet_address}"
            response = requests.get(url)
            if response.status_code != 200:
                response.raise_for_status()
            return response.json()
    except Exception as e:
        save_agent_thought(
            chat_id=chat_id,
            thought=f"Error fetching vaults: {str(e)}",
            isFinalThought=True,
        )
        return f"Error fetching user active vaults because: {e}"


def select_vault_to_deposit_to(
    chat_id: Annotated[str, "The current chat id"],
    use_frontend_quoting: Annotated[bool, "Whether to use frontend quoting or not."],
):
    """
    Displays the user's USDCvaults to select one to deposit to.
    If the user wants to deposit USDC on a vault, but he doesn't provide the vault address or name, use this function to show him the options and ask him to select one.

    # Parameters:
    - chat_id (str): The current chat id
    - use_frontend_quoting (bool): Whether to use frontend quoting or not. If not specified use always TRUE.

    # Returns:
    """
    try:
        save_agent_thought(
            chat_id=chat_id,
            thought="Fetching available USDC vaults for deposit...",
        )

        if use_frontend_quoting:
            save_ui_message(
                chat_id=chat_id,
                component="drift_deposit_options",
                renderData={
                    "token_address": SUPPORTED_TOKEN_ADDRESS,
                },
                thought="Vault options prepared for selection.",
                isFinalThought=True,
            )

            return f"Please select the vault you want to deposit to."
        else:
            solana_wallet_address = get_request_ctx(
                parentKey=chat_id, key="solana_wallet_address"
            )
            if not solana_wallet_address:
                solana_wallet_address = str(
                    Pubkey(bytes([1] * 32))
                )  # Generate a random Solana address using Solders
                # Hardcode one to intitialize the skd

            url = f"{FIREBASE_SERVER_ENDPOINT}/queryDrift?queryType={QueryType.USDC_VAULTS_INFO.value}&userWalletAddress={solana_wallet_address}"
            response = requests.get(url)
            if response.status_code != 200:
                response.raise_for_status()
            usdc_vaults_info = response.json()
            return usdc_vaults_info
    except Exception as e:
        save_agent_thought(
            chat_id=chat_id,
            thought=f"Error fetching USDC vaults: {str(e)}",
            isFinalThought=True,
        )
        return f"Error fetching USDC vaults because: {e}"


def get_user_vaults(
    chat_id: Annotated[str, "The current chat id"],
    use_frontend_quoting: Annotated[
        bool, "Whether to use frontend quoting or not."
    ] = True,
):
    """
    Gets information about the current user's vaults when he asks about his positions/performance/etc

    # Parameters:
    - chat_id (str): The current chat id

    # Returns:
    - A message indicating whether the information was fetched or an error occurred.
    """
    try:
        save_agent_thought(
            chat_id=chat_id,
            thought="Fetching your vault positions...",
        )

        if use_frontend_quoting:
            save_ui_message(
                chat_id=chat_id,
                component="drift_user_vaults",
                renderData={
                    "token_address": SUPPORTED_TOKEN_ADDRESS,
                },
                thought="Vault information prepared.",
                isFinalThought=True,
            )

            return (
                f"I've initiated the process to fetch your current positions on Drift."
            )
        else:
            solana_wallet_address = get_request_ctx(
                parentKey=chat_id, key="solana_wallet_address"
            )
            if not solana_wallet_address:
                return "No wallet address found."

            url = f"{FIREBASE_SERVER_ENDPOINT}/queryDrift?queryType={QueryType.USER_ACTIVE_VAULTS.value}&userWalletAddress={solana_wallet_address}"

            response = requests.get(url)
            if response.status_code != 200:
                response.raise_for_status()
            user_vaults = response.json()
            return user_vaults

    except Exception as e:
        save_agent_thought(
            chat_id=chat_id,
            thought=f"Error fetching vault information: {str(e)}",
            isFinalThought=True,
        )
        return f"Error fetching user vaults because: {e}"


# Perps functions
def check_if_user_has_drift_account(
    chat_id: Annotated[str, "The current chat id"],
    solana_wallet_address: Annotated[str, "The wallet address of the user"],
    skip_drift_account_thought: Annotated[
        bool, "Whether to skip the drift account thought."
    ] = False,
):
    """
    Checks if the user has a drift account.
    """
    try:
        if not skip_drift_account_thought:
            save_agent_thought(
                chat_id=chat_id,
                thought=f"Checking if user has drift account...",
            )

        url = f"{FIREBASE_SERVER_ENDPOINT}/queryDrift?queryType={QueryType.CHECK_USER_HAS_DRIFT_USER_ACCOUNT.value}&userWalletAddress={solana_wallet_address}"
        response = requests.get(url)
        response.raise_for_status()
        user_has_drift_account = response.json()
        return user_has_drift_account
    except Exception as e:
        save_agent_thought(
            chat_id=chat_id,
            thought=f"Error checking if user has drift account",
            isFinalThought=True,
        )
        return f"Error checking if user has drift account because: {e}"


def create_drift_account(
    chat_id: Annotated[str, "The current chat id"],
    token_symbol: Annotated[
        str, "The symbol of the token to deposit as collateral."
    ] = "USDC",
    amount: Annotated[str, "The amount of the token to deposit as collateral."] = None,
    use_frontend_quoting: Annotated[
        bool, "Whether to use frontend quoting or not."
    ] = True,
    already_checked_account_created: Annotated[
        bool, "Whether we already checked if the account was created."
    ] = False,
):
    """
    Creates a new drift account for the user and also deposits the specified COLLATERAL token and amount.
    Call only when the user wants to CREATE an account.
    # Parameters:
    - chat_id (str): The current chat id
    - amount (str | None): The amount of the token to deposit as collateral. Use NONE if not specified (don't ask for it)
    - token_symbol (str): The symbol of the token to deposit as collateral. Use USDC if not specified (don't ask for it)
    - use_frontend_quoting (bool) (optional): Whether to use frontend quoting or not. By default it's True.
    - already_checked_account_created (bool) (optional): Whether we already checked if the account was created. By default it's False.

    # Returns:
    - A message indicating the transaction to create an account is initiated or an error occurred.

    """
    try:

        solana_wallet_address = get_request_ctx(
            parentKey=chat_id, key="solana_wallet_address"
        )

        if not solana_wallet_address:
            return "No wallet address found."

        if not already_checked_account_created:
            user_has_drift_account = check_if_user_has_drift_account(
                chat_id=chat_id,
                solana_wallet_address=solana_wallet_address,
            )

            if user_has_drift_account:
                save_agent_thought(
                    chat_id=chat_id,
                    thought=f"User already has drift account.",
                    isFinalThought=True,
                )
                return "You already have a drift account. You can start depositing collateral or opening positions."

        save_agent_thought(
            chat_id=chat_id,
            thought=f"Checking if token is supported as collateral...",
        )
        if not token_symbol in DRIFT_PERPS_COLLATERAL_TOKENS:
            return f"Token {token_symbol} not supported as collateral. Supported tokens are: {', '.join(DRIFT_PERPS_COLLATERAL_TOKENS)}"

        save_agent_thought(
            chat_id=chat_id,
            thought=f"Checking if amount is valid...",
        )

        token_metadata = tokens_service.get_token_metadata(
            token=token_symbol, chain="SOLANA"
        )
        token_price_response = get_token_price_from_provider(
            "SOLANA", token_metadata["address"], PriceProviderType.JUPITER
        )
        token_price = float(token_price_response["price"])

        # If not amount specified and tokens is USDC, check user balances, if it has more than $5 of USDC use that min amount.
        if not amount and token_symbol == "USDC":
            usdc_balance = get_single_token_balance(
                solana_wallet_address, "SOLANA", "USDC"
            )
            five_dollars_in_usdc = 5 * token_price
            if float(usdc_balance) > five_dollars_in_usdc:
                amount = str(
                    float(five_dollars_in_usdc * 101 / 100)
                )  # add 1% just in case usdc price depeg or it's sligthly lower than 1
            else:
                return f"The minimum required amount to deposit as collateral when creating an account is $5. Add more USDC to your wallet or specify you want to deposit as collateral another token. Supported collateral tokens are {', '.join(DRIFT_PERPS_COLLATERAL_TOKENS)}"

        if not amount or float(amount) == 0:
            return "Please specify the amount you want to deposit as collateral."

        save_agent_thought(
            chat_id=chat_id,
            thought=f"Checking if amount is high enough to create a drift account...",
        )

        new_amount = amount
        amount_in_usd = float(amount) * token_price

        if amount_in_usd < 5:
            new_amount = round(5 / token_price, 5)
            message = f"The minimum amount to create an account is $5. I've adjusted the deposit to {new_amount} {token_symbol} to meet this requirement."

        if use_frontend_quoting:
            save_ui_message(
                chat_id=chat_id,
                component="create_drift_account",
                renderData={
                    "user_wallet_address": solana_wallet_address,
                    "amount": new_amount,
                    "token_symbol": token_symbol,
                },
                thought="Process to create a new drift account initiated successfully.",
                isFinalThought=True,
            )

            return (
                message
                if amount_in_usd < 5
                else f"I've initiated the process to create a new drift account."
            )
        else:
            url = f"{FIREBASE_SERVER_ENDPOINT}/quote"
            params = {
                "chatId": chat_id,
                "userId": get_request_ctx(parentKey=chat_id, key="user_id") or "",
                "protocol": "DRIFT_PERPS",
                "walletAddress": solana_wallet_address,
                "amount": new_amount,
                "fromTokenSymbolOrAddress": token_symbol,
                "perpsTransactionType": "create_account",
            }

            response = requests.post(url, json=params)
            if response.status_code != 200:
                response.raise_for_status()
            return response.json()

    except Exception as e:
        save_agent_thought(
            chat_id=chat_id,
            thought=f"Error creating drift account",
            isFinalThought=True,
        )
        return f"Error creating drift account because: {e}"


def get_drift_perps_account_info(
    chat_id: Annotated[str, "The current chat id"],
    use_frontend_quoting: Annotated[
        bool, "Whether to use frontend quoting or not."
    ] = True,
):
    """
    Gets the information about the user's drift perps account.
    Including the total collateral balance, tokens deposited, max withdrawable amount, etc.
    Util when the user wants to know about his collateral balances, or when he wants to withdraw but doesn't know how much he can withdraw.
    Example prompts:
    - How much can I withdraw from my drift perps account?
    - I want to know how much collateral I have in my drift perps account.
    - I want to withdraw SOL that I have as collateral in my drift perps account.
    - How much can I withdraw from my drift perps account?
    - Withdraw 50% of the USDC I have as collateral in my drift perps account.

    # Parameters:
    - chat_id (str): The current chat id
    - use_frontend_quoting (bool) (optional): Whether to use frontend quoting or not. By default it's True.

    # Returns:
    - A message indicating the account details are being fetched or an error occurred.

    """
    try:
        solana_wallet_address = get_request_ctx(
            parentKey=chat_id, key="solana_wallet_address"
        )

        if not solana_wallet_address:
            return "No wallet address found."

        user_has_drift_account = check_if_user_has_drift_account(
            chat_id=chat_id,
            solana_wallet_address=solana_wallet_address,
        )

        if not user_has_drift_account:
            save_agent_thought(
                chat_id=chat_id,
                thought=f"User doesn't have drift account.",
                isFinalThought=True,
            )
            return "You don't have a drift account. Please create one first."

        if use_frontend_quoting:
            save_ui_message(
                chat_id=chat_id,
                component="drift_account_info",
                renderData={
                    "user_wallet_address": solana_wallet_address,
                },
                thought=f"Process to fetch your account information initiated successfully.",
                isFinalThought=True,
            )

            return f"I've initiated the process to fetch your account information."
        else:
            url = f"{FIREBASE_SERVER_ENDPOINT}/queryDrift?queryType={QueryType.GET_USER_ACCOUNT_INFO.value}&userWalletAddress={solana_wallet_address}"
            response = requests.get(url)
            if response.status_code != 200:
                response.raise_for_status()
            return response.json()

    except Exception as e:
        save_agent_thought(
            chat_id=chat_id,
            thought=f"Error fetching drift perps account information",
            isFinalThought=True,
        )
        return f"Error fetching drift perps account information because: {e}"


def deposit_or_withdraw_collateral(
    token_symbol: Annotated[str, "The symbol of the token to deposit as collateral."],
    amount: Annotated[str, "The amount of the token to deposit as collateral."],
    chat_id: Annotated[str, "The current chat id"],
    transaction_type: Annotated[
        str, "The type of the transaction to generate."
    ] = COLLATERAL_TRANSACTION_TYPE.DEPOSIT.value,
    use_frontend_quoting: Annotated[
        bool, "Whether to use frontend quoting or not."
    ] = True,
):
    """
    Creates a new drift transaction to DEPOSIT or WITHDRAW the specified COLLATERAL token and amount.
    There's no minimum amount once the account is created. So this functions can be used to deposit any amount of the specified token.
    # Parameters:
    - token_symbol (str): The symbol of the token to deposit as collateral.
    - amount (str): The amount of the token to deposit as collateral. (no minimum)
    - chat_id (str): The current chat id
    - transaction_type (str): The type of the transaction to generate. It can be 'deposit' or 'withdraw'
    - use_frontend_quoting (bool) (optional): Whether to use frontend quoting or not. By default it's True.

    # Returns:
    - A message indicating the transaction to create an account is initiated or an error occurred.

    """
    try:
        solana_wallet_address = get_request_ctx(
            parentKey=chat_id, key="solana_wallet_address"
        )

        if not solana_wallet_address:
            return "No wallet address found."

        user_has_drift_account = check_if_user_has_drift_account(
            chat_id=chat_id,
            solana_wallet_address=solana_wallet_address,
        )

        if not user_has_drift_account:
            if transaction_type == COLLATERAL_TRANSACTION_TYPE.WITHDRAW.value:
                save_agent_thought(
                    chat_id=chat_id,
                    thought=f"User doesn't have drift account.",
                    isFinalThought=True,
                )
                return "You don't have a drift account. Please create one first."
            else:
                save_agent_thought(
                    chat_id=chat_id,
                    thought=f"User doesn't have drift account. Starting create and deposit collateral flow...",
                )
                return create_drift_account(
                    token_symbol=token_symbol,
                    amount=amount,
                    chat_id=chat_id,
                    use_frontend_quoting=use_frontend_quoting,
                    already_checked_account_created=True,
                )

        save_agent_thought(
            chat_id=chat_id,
            thought=f"Initiating process to {transaction_type} {amount} {token_symbol} as collateral...",
        )

        # If transaction_type not in COLLATERAL TYPES return an error
        if transaction_type not in [
            COLLATERAL_TRANSACTION_TYPE.DEPOSIT.value,
            COLLATERAL_TRANSACTION_TYPE.WITHDRAW.value,
        ]:
            return "Invalid transaction type. Please specify if you want to 'deposit' or 'withdraw'."

        if not amount or amount == 0:
            return "Please specify the amount you want to deposit or withdraw."

        save_agent_thought(
            chat_id=chat_id,
            thought=f"Checking if token is supported as collateral...",
        )

        if not token_symbol in DRIFT_PERPS_COLLATERAL_TOKENS:
            return f"Token {token_symbol} not supported as collateral. Supported tokens are: {', '.join(DRIFT_PERPS_COLLATERAL_TOKENS)}"

        if use_frontend_quoting:
            save_ui_message(
                chat_id=chat_id,
                component="drift_collateral_transaction",
                renderData={
                    "user_wallet_address": solana_wallet_address,
                    "amount": amount,
                    "token_symbol": token_symbol,
                    "transaction_type": transaction_type,
                },
                thought=f"Process to {transaction_type} {amount} {token_symbol} as collateral initiated successfully.",
                isFinalThought=True,
            )

            return f"I've initiated the process to {transaction_type} {amount} {token_symbol} as collateral."
        else:
            url = f"{FIREBASE_SERVER_ENDPOINT}/quote"
            params = {
                "chatId": chat_id,
                "userId": get_request_ctx(parentKey=chat_id, key="user_id") or "",
                "protocol": "DRIFT_PERPS",
                "walletAddress": solana_wallet_address,
                "amount": amount,
                "fromTokenSymbolOrAddress": token_symbol,
                "perpsTransactionType": f"{transaction_type}_collateral",
            }

            response = requests.post(url, json=params)
            if response.status_code != 200:
                response.raise_for_status()
            return response.json()

    except Exception as e:
        save_agent_thought(
            chat_id=chat_id,
            thought=f"Error during the process to {transaction_type} {amount} {token_symbol} as collateral",
            isFinalThought=True,
        )
        return f"Error adding/withdrawing collateral transaction because: {e}"


def is_valid_market_symbol(symbol: str) -> bool:
    """
    Checks if the given symbol is a valid perps market symbol.
    Returns Boolean in case the symbol is valid or not and a list of all perps markets.
    """
    solana_wallet_address = str(
        Pubkey(bytes([1] * 32))
    )  # Generate a random Solana address using Solders
    url = f"{FIREBASE_SERVER_ENDPOINT}/queryDrift?queryType={QueryType.GET_PERPS_MARKETS.value}&userWalletAddress={solana_wallet_address}"

    response = requests.get(url)
    response.raise_for_status()
    perp_markets = response.json()
    is_valid_market = True
    if symbol not in perp_markets:
        is_valid_market = False

    return {"is_valid_market": is_valid_market, "perp_markets": perp_markets}


def open_perps_position(
    symbol: Annotated[str, "The symbol of the market to open a position on."],
    amount: Annotated[str, "The amount of the token to open a position on."],
    order_type: Annotated[ORDER_TYPE, "The type of the order to open a position on."],
    chat_id: Annotated[str, "The current chat id"],
    trade_direction: Annotated[POSITION_TYPE, "The direction of the position to open."],
    slippage: Annotated[float, "The slippage of the position."] = None,
    limit_price: Annotated[float, "The limit price of the position."] = None,
    take_profit_percentage: Annotated[
        float, "The take profit percentage of the position."
    ] = None,
    stop_loss_percentage: Annotated[
        float, "The stop loss percentage of the position."
    ] = None,
    use_frontend_quoting: Annotated[
        bool, "Whether to use frontend quoting or not."
    ] = True,
):
    """
    Creates a new drift transaction to open a new position on a PERPS market.
    # Parameters:
    - symbol (str): The symbol of the market to open a position on (Example: JUP / SOL / BTC / ETH / etc)
    - amount (str): The amount of the token to open a position on.
    - order_type (str): The type of the order to open a position on. It can be 'market' or 'limit'
    - chat_id (str): The current chat id
    - trade_direction (str): The direction of the position to open. It can be 'long' or 'short'
    - slippage (float) (optional): The slippage of the position. By default it's 0.5%
    - limit_price (float) (optional): The limit price of the position. By default it's None
    - take_profit_percentage (float) (optional): The take profit percentage of the position. By default it's None
    - stop_loss_percentage (float) (optional): The stop loss percentage of the position. By default it's None
    - use_frontend_quoting (bool) (optional): Whether to use frontend quoting or not. By default it's True.

    # Returns:
    - A message indicating the transaction to create an account is initiated or an error occurred.

    """
    try:
        solana_wallet_address = get_request_ctx(
            parentKey=chat_id, key="solana_wallet_address"
        )

        if not solana_wallet_address:
            return "No wallet address found."

        user_has_drift_account = check_if_user_has_drift_account(
            chat_id=chat_id,
            solana_wallet_address=solana_wallet_address,
        )

        if not user_has_drift_account:
            save_agent_thought(
                chat_id=chat_id,
                thought=f"User doesn't have drift account.",
                isFinalThought=True,
            )
            return "You don't have a drift account. You can create one and start depositing collateral or opening positions."

        save_agent_thought(
            chat_id=chat_id,
            thought=f"Initiating process to open a new {trade_direction.value.upper()} position on {symbol}...",
        )

        save_agent_thought(
            chat_id=chat_id,
            thought=f"Checking slippage and amount...",
        )

        if not slippage:
            slippage = 0.25

        if not amount or amount == 0:
            return "Please specify the amount you want to open a position on."

        if order_type == ORDER_TYPE.LIMIT:
            if not limit_price:
                return "Please specify the limit price for the position."

        save_agent_thought(
            chat_id=chat_id,
            thought=f"Checking if market is valid...",
        )

        if not is_valid_market_symbol(symbol)["is_valid_market"]:
            save_agent_thought(
                chat_id=chat_id,
                thought=f"Market {symbol} is not valid.",
                isFinalThought=True,
            )
            return f"Market {symbol} not found. Here's a list of available perp markets: {', '.join(is_valid_market_symbol(symbol)['perp_markets'])}"

        if use_frontend_quoting:
            renderData = {
                "user_wallet_address": solana_wallet_address,
                "trade_direction": trade_direction.value,
                "symbol": symbol,
                "amount": amount,
                "orderType": order_type.value,
            }

            if slippage:
                renderData["slippage"] = slippage

            if limit_price:
                renderData["limitPrice"] = limit_price

            if take_profit_percentage:
                renderData["takeProfitPercentage"] = take_profit_percentage

            if stop_loss_percentage:
                renderData["stopLossPercentage"] = stop_loss_percentage

            save_ui_message(
                chat_id=chat_id,
                component="drift_perp_position",
                renderData=renderData,
                thought=f"Process to open a new {trade_direction.value.upper()} position on {symbol} initiated successfully.",
                isFinalThought=True,
            )
            return f"I've initiated the process to open a new position on {symbol}."
        else:
            url = f"{FIREBASE_SERVER_ENDPOINT}/quote"
            params = {
                "chatId": chat_id,
                "userId": get_request_ctx(parentKey=chat_id, key="user_id") or "",
                "protocol": "DRIFT_PERPS",
                "walletAddress": solana_wallet_address,
                "marketSymbol": symbol,
                "fromAmount": amount,
                "tradeDirection": trade_direction.value,
                "orderType": order_type.value,
                "slippage": slippage,
                "limitPrice": limit_price,
                "takeProfitPercentage": take_profit_percentage,
                "stopLossPercentage": stop_loss_percentage,
                "perpsTransactionType": "open_perp_position",
            }

            response = requests.post(url, json=params)
            if response.status_code != 200:
                response.raise_for_status()
            return response.json()

    except Exception as e:
        save_agent_thought(
            chat_id=chat_id,
            thought=f"Error opening {trade_direction.value.upper()} position on market {symbol}",
            isFinalThought=True,
        )
        return f"Error opening {trade_direction.value.upper()} position on market {symbol} because: {e}"


def close_perps_position(
    symbol: Annotated[str, "The symbol of the market to open a position on."],
    percentage_to_close: Annotated[float, "The percentage of the position to close."],
    chat_id: Annotated[str, "The current chat id"],
    trade_direction: Annotated[POSITION_TYPE, "The direction of the position to open."],
    slippage: Annotated[float, "The slippage of the position."] = None,
    use_frontend_quoting: Annotated[
        bool, "Whether to use frontend quoting or not."
    ] = True,
):
    """
    Creates a transaction to CLOSE a position on a PERPS market.
    Example prompts:
    - Please close 100% of the LONG position I have on JUP-PERPS
    - Close 50% of the SHORT position I have on SOL-PERPS
    - Close all my position on BTC-PERPS on Drift.
    - Close my LONG position on ETH-PERPS on Drift.
    - I want to withdraw 100% of my position on SOL-PERPS on Drift.

    The only needed parameters are:
    # Parameters:
    - symbol (str): The symbol of the market to open a position on (Example: JUP / SOL / BTC / ETH / etc. Without the '-PERPS' part)
    - percentage_to_close (float): The percentage of the position to close.
    - chat_id (str): The current chat id
    - trade_direction (str): The direction of the position to open. It can be 'long' or 'short'
    - slippage (float) (optional): The slippage of the position. By default it's 0.5%
    - use_frontend_quoting (bool) (optional): Whether to use frontend quoting or not. By default it's True.

    # Returns:
    - A message indicating the transaction to create an account is initiated or an error occurred.

    """
    try:
        solana_wallet_address = get_request_ctx(
            parentKey=chat_id, key="solana_wallet_address"
        )
        if not solana_wallet_address:
            return "No wallet address found."

        user_has_drift_account = check_if_user_has_drift_account(
            chat_id=chat_id,
            solana_wallet_address=solana_wallet_address,
        )
        if not user_has_drift_account:
            save_agent_thought(
                chat_id=chat_id,
                thought=f"User doesn't have drift account.",
                isFinalThought=True,
            )
            return (
                "You don't have a drift account. Create one and open a position first."
            )

        save_agent_thought(
            chat_id=chat_id,
            thought=f"Initiating process to close {percentage_to_close}% of the position on {symbol}...",
        )

        save_agent_thought(
            chat_id=chat_id,
            thought=f"Checking slippage and percentage to close...",
        )

        if not slippage:
            slippage = 0.25

        if (
            not percentage_to_close
            or percentage_to_close <= 0
            or percentage_to_close > 100
        ):
            return "Please specify the percentage you want to close the position (between 1 and 100)."

        save_agent_thought(
            chat_id=chat_id,
            thought=f"Checking if market is valid...",
        )

        if not is_valid_market_symbol(symbol)["is_valid_market"]:
            save_agent_thought(
                chat_id=chat_id,
                thought=f"Market {symbol} is not valid.",
                isFinalThought=True,
            )
            return f"Market {symbol} not found. Here's a list of available perp markets: {', '.join(is_valid_market_symbol(symbol)['perp_markets'])}"

        if use_frontend_quoting:
            renderData = {
                "user_wallet_address": solana_wallet_address,
                "symbol": symbol,
                "percentage_to_close": percentage_to_close,
                "trade_direction": trade_direction.value,
                "slippage": slippage,
            }

            save_ui_message(
                chat_id=chat_id,
                component="drift_perp_close",
                renderData=renderData,
                thought=f"Process to close {percentage_to_close}% of the position on {symbol} initiated successfully.",
                isFinalThought=True,
            )
            return f"I've initiated the process to close {percentage_to_close}% of the position on {symbol}."
        else:
            url = f"{FIREBASE_SERVER_ENDPOINT}/quote"
            params = {
                "chatId": chat_id,
                "userId": get_request_ctx(parentKey=chat_id, key="user_id") or "",
                "protocol": "DRIFT_PERPS",
                "walletAddress": solana_wallet_address,
                "marketSymbol": symbol,
                "percentageToClose": percentage_to_close,
                "tradeDirection": trade_direction.value,
                "slippage": slippage,
                "perpsTransactionType": "close_perp_position",
            }

            response = requests.post(url, json=params)
            if response.status_code != 200:
                response.raise_for_status()
            return response.json()

    except Exception as e:
        save_agent_thought(
            chat_id=chat_id,
            thought=f"Error closing perps position on market {symbol}",
            isFinalThought=True,
        )
        return f"Error closing perps position on market {symbol} because: {e}"


def get_user_active_orders(
    chat_id: Annotated[str, "The current chat id"],
    use_frontend_quoting: Annotated[
        bool, "Whether to use frontend quoting or not."
    ] = True,
    skip_drift_account_thought: Annotated[
        bool, "Whether to skip the drift account thought."
    ] = False,
):
    """
    Gets the user active orders from the drift protocol.
    Example prompts:
    - What orders do I have open on Drift Perps?
    - I want to see my open orders on Drift Perps
    - Can you show me my open orders on Drift Perps?
    - Show me my open orders on Drift Perps
    - Do I have any takeProfit / stopLoss orders on Drift Perps?
    - I want to see my Limit orders on Drift Perps

    # Parameters:
    - chat_id (str): The current chat id
    - use_frontend_quoting (bool) (optional): Whether to use frontend quoting or not. By default it's True.
    - skip_drift_account_thought (bool) (optional): Whether to skip the drift account thought. By default it's False.

    # Returns:
    - A message indicating the process to get the user active orders is initiated or an error occurred.

    """
    try:
        solana_wallet_address = get_request_ctx(
            parentKey=chat_id, key="solana_wallet_address"
        )

        if not solana_wallet_address:
            return "No wallet address found."

        user_has_drift_account = check_if_user_has_drift_account(
            chat_id=chat_id,
            solana_wallet_address=solana_wallet_address,
            skip_drift_account_thought=skip_drift_account_thought,
        )

        if not user_has_drift_account:
            save_agent_thought(
                chat_id=chat_id,
                thought=f"User doesn't have drift account.",
                isFinalThought=True,
            )
            return "You don't have any active orders on Drift Perps."

        save_agent_thought(
            chat_id=chat_id,
            thought=f"Initiating process to get user active orders...",
        )

        if use_frontend_quoting:
            save_ui_message(
                chat_id=chat_id,
                component="drift_perp_user_orders",
                renderData={"user_wallet_address": solana_wallet_address},
                thought=f"Process to get user active orders initiated successfully.",
                isFinalThought=True,
            )

            return f"I've initiated the process to get your active orders."
        else:
            url = f"{FIREBASE_SERVER_ENDPOINT}/queryDrift?queryType={QueryType.GET_USER_ACTIVE_ORDERS.value}&userWalletAddress={solana_wallet_address}"
            response = requests.get(url)
            if response.status_code != 200:
                response.raise_for_status()
            return response.json()

    except Exception as e:
        save_agent_thought(
            chat_id=chat_id,
            thought=f"Error getting user active orders",
            isFinalThought=True,
        )
        return f"Error getting user active orders because: {e}"


def close_order_by_id_and_symbol(
    symbol: Annotated[str, "The symbol of the market to close the order on."],
    order_id: Annotated[int, "The id of the order to close."],
    chat_id: Annotated[str, "The current chat id"],
    use_frontend_quoting: Annotated[
        bool, "Whether to use frontend quoting or not."
    ] = True,
):
    """
    Builds a transaction to cancel an order by id and market symbol on Drift Perps.
    # Parameters:
    - symbol (str): The symbol of the market to close the order on. (Example: SUI / SOL , etc) Without the '-PERPS' part.
    - order_id (int): The id of the order to close.
    - chat_id (str): The current chat id
    - use_frontend_quoting (bool) (optional): Whether to use frontend quoting or not. By default it's True.

    # Returns:
    - A message indicating the process to cancel the specific order is initiated or an error occurred.

    """
    try:
        solana_wallet_address = get_request_ctx(
            parentKey=chat_id, key="solana_wallet_address"
        )

        if not solana_wallet_address:
            return "No wallet address found."

        user_has_drift_account = check_if_user_has_drift_account(
            chat_id=chat_id,
            solana_wallet_address=solana_wallet_address,
        )

        if not user_has_drift_account:
            save_agent_thought(
                chat_id=chat_id,
                thought=f"User doesn't have drift account.",
                isFinalThought=True,
            )
            return "You don't have any active orders on Drift Perps."

        save_agent_thought(
            chat_id=chat_id,
            thought=f"Initiating process to cancel order on {symbol}-PERPS market...",
        )

        save_agent_thought(
            chat_id=chat_id,
            thought="Checking if market is valid...",
        )

        if not is_valid_market_symbol(symbol)["is_valid_market"]:
            save_agent_thought(
                chat_id=chat_id,
                thought=f"Market {symbol} not found on Drift Perps",
                isFinalThought=True,
            )
            return f"Market {symbol} not found. Here's a list of available perp markets: {', '.join(is_valid_market_symbol(symbol)['perp_markets'])}"

        if use_frontend_quoting:
            save_ui_message(
                chat_id=chat_id,
                component="drift_perp_cancel_order",
                renderData={
                    "user_wallet_address": solana_wallet_address,
                    "symbol": symbol,
                    "order_id": order_id,
                },
                thought=f"Process to cancel order on {symbol}-PERPS market initiated successfully.",
                isFinalThought=True,
            )

            return f"Process to cancel order on {symbol}-PERPS market is initiated."
        else:
            url = f"{FIREBASE_SERVER_ENDPOINT}/quote"
            params = {
                "chatId": chat_id,
                "userId": get_request_ctx(parentKey=chat_id, key="user_id") or "",
                "protocol": "DRIFT_PERPS",
                "walletAddress": solana_wallet_address,
                "perpsTransactionType": "cancel_order",
                "marketSymbol": symbol,
                "orderId": order_id,
            }

            response = requests.post(url, json=params)
            if response.status_code != 200:
                response.raise_for_status()
            return response.json()

    except Exception as e:
        save_agent_thought(
            chat_id=chat_id,
            thought=f"Error cancelling order on {symbol}",
            isFinalThought=True,
        )
        return f"Error cancelling order {order_id} on {symbol} because: {e}"


def close_all_active_orders(
    chat_id: Annotated[str, "The current chat id"],
    use_frontend_quoting: Annotated[
        bool, "Whether to use frontend quoting or not."
    ] = True,
):
    """
    Builds a transaction to cancel all active orders on Drift Perps.
    Example prompts:
    - Cancel all my active orders on Drift Perps
    - I want to cancel all my open orders on Drift Perps
    - Can you close all my open orders on Drift Perps?
    - Close all my open orders on Drift Perps

    # Parameters:
    - chat_id (str): The current chat id
    - use_frontend_quoting (bool) (optional): Whether to use frontend quoting or not. By default it's True.

    # Returns:
    - A message indicating the process to cancel active orders is initiated or an error occurred.

    """
    try:
        solana_wallet_address = get_request_ctx(
            parentKey=chat_id, key="solana_wallet_address"
        )

        if not solana_wallet_address:
            return "No wallet address found."

        user_has_drift_account = check_if_user_has_drift_account(
            chat_id=chat_id,
            solana_wallet_address=solana_wallet_address,
        )

        if not user_has_drift_account:
            save_agent_thought(
                chat_id=chat_id,
                thought=f"User doesn't have drift account.",
                isFinalThought=True,
            )
            return "You don't have any active orders on Drift Perps."

        save_agent_thought(
            chat_id=chat_id,
            thought=f"Initiating process to cancel all your active orders...",
        )

        if use_frontend_quoting:
            save_ui_message(
                chat_id=chat_id,
                component="drift_perp_cancel_order",
                renderData={
                    "user_wallet_address": solana_wallet_address,
                },
                thought=f"Process to cancel all your active orders initiated successfully.",
                isFinalThought=True,
            )

            return f"Process to cancel all your active orders is initiated."
        else:
            url = f"{FIREBASE_SERVER_ENDPOINT}/quote"
            params = {
                "chatId": chat_id,
                "userId": get_request_ctx(parentKey=chat_id, key="user_id") or "",
                "protocol": "DRIFT_PERPS",
                "walletAddress": solana_wallet_address,
                "perpsTransactionType": "cancel_all_active_orders",
            }
            response = requests.post(url, json=params)
            if response.status_code != 200:
                response.raise_for_status()
            return response.json()

    except Exception as e:
        save_agent_thought(
            chat_id=chat_id,
            thought=f"Error cancelling all your active orders",
            isFinalThought=True,
        )
        return f"Error cancelling all your active orders because: {e}"


def get_user_active_positions(
    chat_id: Annotated[str, "The current chat id"],
    use_frontend_quoting: Annotated[
        bool, "Whether to use frontend quoting or not."
    ] = True,
):
    """
    Gets the user active positions from the drift protocol (this are orders that where already executed and they're now a position)
    Example prompts:
    - I want to see my active PERPS positions
    - Show me my open positions on PERPS
    - What positions do I have open on PERPS?
    - Do I have any LONG / SHORT position on DRIFT ?
    # Parameters:
    - chat_id (str): The current chat id
    - use_frontend_quoting (bool) (optional): Whether to use frontend quoting or not. By default it's True.

    # Returns:
    - A message indicating the process to get the user active positions is initiated or an error occurred.

    """
    try:
        solana_wallet_address = get_request_ctx(
            parentKey=chat_id, key="solana_wallet_address"
        )

        if not solana_wallet_address:
            return "No wallet address found."

        user_has_drift_account = check_if_user_has_drift_account(
            chat_id=chat_id,
            solana_wallet_address=solana_wallet_address,
        )

        if not user_has_drift_account:
            save_agent_thought(
                chat_id=chat_id,
                thought=f"User doesn't have drift account.",
                isFinalThought=True,
            )
            return "You don't have any active positions on Drift Perps."

        save_agent_thought(
            chat_id=chat_id,
            thought=f"Initiating process to get user active positions...",
        )

        if use_frontend_quoting:
            save_ui_message(
                chat_id=chat_id,
                component="drift_perp_user_positions",
                renderData={"user_wallet_address": solana_wallet_address},
                thought=f"Process to get user active positions initiated successfully.",
                isFinalThought=True,
            )

            return f"I've initiated the process to get your active positions."
        else:
            url = f"{FIREBASE_SERVER_ENDPOINT}/queryDrift?queryType={QueryType.GET_USER_ACTIVE_PERPS_POSITIONS.value}&userWalletAddress={solana_wallet_address}"
            response = requests.get(url)
            if response.status_code != 200:
                response.raise_for_status()
            return response.json()

    except Exception as e:
        save_agent_thought(
            chat_id=chat_id,
            thought=f"Error getting user active Perps positions",
            isFinalThought=True,
        )
        return f"Error getting user active Perps positions because: {e}"


def get_perps_markets(
    chat_id: Annotated[str, "The current chat id"],
    use_frontend_quoting: Annotated[
        bool, "Whether to use frontend quoting or not."
    ] = True,
):
    """
    Gets the availables perps markets from Drift Perps Protocol where the user can open positions.
    Usefull if the user wants to open an order or position but he doesn't know the available markets.
    Example prompts:
    - What perps markets are available on Drift Perps?
    - Where can I open a Perps position on Drift Perps?

    # Parameters:
    - chat_id (str): The current chat id
    - use_frontend_quoting (bool) (optional): Whether to use frontend quoting or not. By default it's True.

    # Returns:
    - List of perps markets where the user can open positions.

    """
    try:
        save_agent_thought(
            chat_id=chat_id,
            thought=f"Initiating process to get perps markets...",
        )

        solana_wallet_address = str(
            Pubkey(bytes([1] * 32))
        )  # Generate a random Solana address using Solders
        url = f"{FIREBASE_SERVER_ENDPOINT}/queryDrift?queryType={QueryType.GET_PERPS_MARKETS.value}&userWalletAddress={solana_wallet_address}"

        response = requests.get(url)
        response.raise_for_status()
        perp_markets = response.json()

        if use_frontend_quoting:
            save_agent_thought(
                chat_id=chat_id,
                thought=f"Perps markets retrieved successfully.",
                isFinalThought=True,
            )
            return f"Here is a list of the available perps markets on Drift Perps: {', '.join(perp_markets)}"
        else:
            return perp_markets

    except Exception as e:
        save_agent_thought(
            chat_id=chat_id,
            thought=f"Error getting perps markets",
            isFinalThought=True,
        )
        return f"Error getting perps markets because: {e}"
