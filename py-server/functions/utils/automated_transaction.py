import asyncio
from pydantic import BaseModel
from services.delegated_actions import sign_transaction
from services.balances import update_balances_after_transaction
from utils.firebase import update_tx_status, db_save_message, update_unsigned_transactions
from typing import Union, List, Optional


class SupportedToken(BaseModel):
    symbol: str
    name: str 
    decimals: int
    icon_url: str
    logoURI: Optional[str] = None  # backward compatibility
    address: Optional[str] = None  # backward compatibility
    contract_address: str
    chain_name: str
    chain: Optional[str] = None  # backward compatibility
    chain_id: Union[str, int]
    chain_id_lowercase: Optional[str] = None
    protocols: List[str]
    verified: Optional[bool] = None
    class Config:
        extra = "forbid"

# Define the two distinct forms for a transaction item
class SerializedTransactionForm(BaseModel):
    serializedTransaction: str
    class Config:
        extra = "forbid"

class DetailedTransactionForm(BaseModel):
    chain_id: Union[str, int]
    from_address: str
    to_address: str
    value: str
    data: Optional[str] = None
    gas: Optional[str] = None
    gas_price: Optional[Union[int, float, None]] = None
    class Config:
        extra = "forbid"

# TransactionListItem is now a Union of the two forms
TransactionListItem = Union[SerializedTransactionForm, DetailedTransactionForm]

class TransactionData(BaseModel):
    transactionId: str
    fromAddress: str
    toAddress: str
    fromToken: SupportedToken
    fromTokenUsd: str 
    toToken: SupportedToken
    toTokenUsd: str
    fromAmount: Union[str, float]
    toAmount: Union[str, float]
    fromChain: str
    fromChainId: Union[str, int]
    toChain: str
    toChainId: Union[str, int]
    estimatedTime: int
    transactions: List[TransactionListItem]
    tool: str
    providerFee: Optional[str] = None
    gasCost: str
    slippage: str
    protocolName: str
    order: Optional[str]
    agent: str
    order: Optional[str] = None
    priceImpact: Optional[Union[int, float]]
    usedProviders: Optional[str]
    class Config:
        extra = "forbid"


async def perform_automated_transaction(
    transaction_id,
    chat_id,
    user_id,
    transaction_data,
    type,
    action,
    sender_wallet_address,
    chain=None,
):
    # Extract taskId from chat_id
    # chat_id format is f"{userId}-scheduled-{taskId}"
    parts = chat_id.split("-")
    task_id = str(parts[-1]) if len(parts) > 2 and parts[-2] == "scheduled" else ""

    try:        
        chain_id_hex = ""
        if chain:
            chain_id_hex = str(chain) if str(chain).startswith("0x") else f"0x{int(chain):x}"
        hash = sign_transaction(
            transaction_data,
            type,
            action,
            sender_wallet_address,
            chain=chain_id_hex,
        )
        # successful, update tx status, update user balance, create ui message
        # Execute all post-transaction operations in parallel
        await asyncio.gather(
            asyncio.to_thread(update_tx_status, transaction_id=transaction_id, status="success", signature=hash),
            asyncio.to_thread(update_balances_after_transaction, transaction_id=transaction_id),
            asyncio.to_thread(update_unsigned_transactions, user_id=user_id, task_id=task_id, reset=True),
            asyncio.to_thread(db_save_message,
                chat_id=chat_id,
                user_id=user_id,
                content=f"Transaction completed. Here is the transaction hash: {hash}",
                sender="AI",
                message_type="text"
            )
        )
        return hash
    except Exception as e:
        print(f"Error performing automated transaction: {e}")
        # unsuccessful, update tx status, create ui message
        await asyncio.gather(
            asyncio.to_thread(update_tx_status, transaction_id=transaction_id, status="failure", signature=""),
            asyncio.to_thread(db_save_message,
                chat_id=chat_id,
                user_id=user_id,
                content=f"Transaction failed: {str(e)}",
                sender="AI",
                message_type="text"
            )
        )
    return
