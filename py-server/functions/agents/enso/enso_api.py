import requests
from typing import Annotated, Dict, List, Union, Any, Optional
from config import ENSO_API_KEY

# Swagger: https://api.enso.finance/api
# Docs: https://api-docs.enso.finance/

BASE_URL = "https://api.enso.finance/api"
HEADERS = {"Authorization": f"Bearer {ENSO_API_KEY}"}


def get_networks(
    name: Optional[Annotated[str, "Title of the network to search for"]] = None,
    chainId: Optional[Annotated[str, "Chain ID of the network to search for"]] = None,
) -> List[Dict[str, Union[str, int]]]:
    """
    Returns networks supported by the API.

    :param name: Title of the network to search for
    :param chainId: Chain ID of the network to search for
    :return: List of networks
    """
    params = {}
    if name:
        params["name"] = name
    if chainId:
        params["chainId"] = chainId
    response = requests.get(f"{BASE_URL}/v1/networks", headers=HEADERS, params=params)
    response.raise_for_status()
    return response.json()


def get_multichain_route(
    fromAddress: Annotated[
        str, "Ethereum address of the wallet to send the transaction from"
    ],
    amountIn: Annotated[List[str], "Amount of tokenIn to swap in wei"],
    tokenIn: Annotated[
        List[str],
        "Ethereum address of the token to swap from. For ETH, use 0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
    ],
    tokenOut: Annotated[
        List[str],
        "Ethereum address of the token to swap to. For ETH, use 0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
    ],
    fromChainId: Annotated[int, "Chain ID of token in"],
    toChainId: Annotated[int, "Chain ID of token out"],
    receiver: Optional[
        Annotated[str, "Ethereum address of the receiver of the tokenOut"]
    ] = None,
    slippage: Optional[
        Annotated[
            str,
            "Slippage in basis points (1/10000). If specified, minAmountOut should not be specified",
        ]
    ] = "300",
) -> Dict[str, Any]:
    """
    Best multichain route from a token to another.

    :param fromAddress: Ethereum address of the wallet to send the transaction from
    :param amountIn: Amount of tokenIn to swap in wei
    :param tokenIn: Ethereum address of the token to swap from. For ETH, use 0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee
    :param tokenOut: Ethereum address of the token to swap to. For ETH, use 0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee
    :param fromChainId: Chain ID of token in
    :param toChainId: Chain ID of token out
    :param receiver: Ethereum address of the receiver of the tokenOut
    :param slippage: Slippage in basis points (1/10000). If specified, minAmountOut should not be specified
    :return: Best multichain route
    """
    params = {
        "fromAddress": fromAddress,
        "amountIn": amountIn,
        "tokenIn": tokenIn,
        "tokenOut": tokenOut,
        "fromChainId": fromChainId,
        "toChainId": toChainId,
    }
    if receiver:
        params["receiver"] = receiver
    if slippage:
        params["slippage"] = slippage
    response = requests.get(
        f"{BASE_URL}/v1/shortcuts/route/multichain", headers=HEADERS, params=params
    )
    response.raise_for_status()
    return response.json()


def get_route(
    fromAddress: Annotated[
        str, "Ethereum address of the wallet to send the transaction from"
    ],
    amountIn: Annotated[List[str], "Amount of tokenIn to swap in wei"],
    tokenIn: Annotated[
        List[str],
        "Ethereum address of the token to swap from. For ETH, use 0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
    ],
    tokenOut: Annotated[
        List[str],
        "Ethereum address of the token to swap to. For ETH, use 0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
    ],
    chainId: Optional[
        Annotated[int, "Chain ID of the network to execute the transaction on"]
    ] = 1,
    routingStrategy: Optional[Annotated[str, "Routing strategy to use"]] = "router",
    priceImpact: Optional[
        Annotated[
            bool,
            "Flag that indicates whether to calculate and return the price impact of the transaction",
        ]
    ] = None,
    receiver: Optional[
        Annotated[str, "Ethereum address of the receiver of the tokenOut"]
    ] = None,
    spender: Optional[
        Annotated[str, "Ethereum address of the spender of the tokenIn"]
    ] = None,
    minAmountOut: Optional[
        Annotated[
            List[str],
            "Minimum amount out in wei. If specified, slippage should not be specified",
        ]
    ] = None,
    slippage: Optional[
        Annotated[
            str,
            "Slippage in basis points (1/10000). If specified, minAmountOut should not be specified",
        ]
    ] = "300",
    fee: Optional[
        Annotated[
            List[str],
            "Fee in basis points (1/10000) for each amountIn value. Must be in range 0-100. If specified, this percentage of each amountIn value will be sent to feeReceiver",
        ]
    ] = None,
    feeReceiver: Optional[
        Annotated[
            str,
            "The Ethereum address that will receive the collected fee. Required if fee is provided",
        ]
    ] = None,
    disableRFQs: Optional[
        Annotated[bool, "A flag indicating whether to exclude RFQ sources from routes"]
    ] = None,
    ignoreAggregators: Optional[
        Annotated[
            List[str], "A list of swap aggregators to be ignored from consideration"
        ]
    ] = None,
    ignoreStandards: Optional[
        Annotated[List[str], "A list of standards to be ignored from consideration"]
    ] = None,
) -> Dict[str, Any]:
    """
    Best route from a token to another.

    :param fromAddress: Ethereum address of the wallet to send the transaction from
    :param amountIn: Amount of tokenIn to swap in wei
    :param tokenIn: Ethereum address of the token to swap from. For ETH, use 0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee
    :param tokenOut: Ethereum address of the token to swap to. For ETH, use 0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee
    :param chainId: Chain ID of the network to execute the transaction on
    :param routingStrategy: Routing strategy to use
    :param priceImpact: Flag that indicates whether to calculate and return the price impact of the transaction
    :param receiver: Ethereum address of the receiver of the tokenOut
    :param spender: Ethereum address of the spender of the tokenIn
    :param minAmountOut: Minimum amount out in wei. If specified, slippage should not be specified
    :param slippage: Slippage in basis points (1/10000). If specified, minAmountOut should not be specified
    :param fee: Fee in basis points (1/10000) for each amountIn value. Must be in range 0-100. If specified, this percentage of each amountIn value will be sent to feeReceiver
    :param feeReceiver: The Ethereum address that will receive the collected fee. Required if fee is provided
    :param disableRFQs: A flag indicating whether to exclude RFQ sources from routes
    :param ignoreAggregators: A list of swap aggregators to be ignored from consideration
    :param ignoreStandards: A list of standards to be ignored from consideration
    :return: Best route
    """
    params = {
        "fromAddress": fromAddress,
        "amountIn": amountIn,
        "tokenIn": tokenIn,
        "tokenOut": tokenOut,
    }
    if chainId:
        params["chainId"] = chainId
    if routingStrategy:
        params["routingStrategy"] = routingStrategy
    if priceImpact:
        params["priceImpact"] = priceImpact
    if receiver:
        params["receiver"] = receiver
    if spender:
        params["spender"] = spender
    if minAmountOut:
        params["minAmountOut"] = minAmountOut
    if slippage:
        params["slippage"] = slippage
    if fee:
        params["fee"] = fee
    if feeReceiver:
        params["feeReceiver"] = feeReceiver
    if disableRFQs:
        params["disableRFQs"] = disableRFQs
    if ignoreAggregators:
        params["ignoreAggregators"] = ignoreAggregators
    if ignoreStandards:
        params["ignoreStandards"] = ignoreStandards
    response = requests.get(
        f"{BASE_URL}/v1/shortcuts/route", headers=HEADERS, params=params
    )
    response.raise_for_status()
    return response.json()


def post_route(
    fromAddress: Annotated[
        str, "Ethereum address of the wallet to send the transaction from"
    ],
    amountIn: Annotated[List[str], "Amount of tokenIn to swap in wei"],
    tokenIn: Annotated[
        List[str],
        "Ethereum address of the token to swap from. For ETH, use 0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
    ],
    tokenOut: Annotated[
        List[str],
        "Ethereum address of the token to swap to. For ETH, use 0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
    ],
    variableEstimates: Annotated[Dict[str, Any], "Variable estimates"],
    chainId: Optional[
        Annotated[int, "Chain ID of the network to execute the transaction on"]
    ] = 1,
    routingStrategy: Optional[Annotated[str, "Routing strategy to use"]] = None,
    priceImpact: Optional[
        Annotated[
            bool,
            "Flag that indicates whether to calculate and return the price impact of the transaction",
        ]
    ] = None,
    receiver: Optional[
        Annotated[str, "Ethereum address of the receiver of the tokenOut"]
    ] = None,
    spender: Optional[
        Annotated[str, "Ethereum address of the spender of the tokenIn"]
    ] = None,
    minAmountOut: Optional[
        Annotated[
            List[str],
            "Minimum amount out in wei. If specified, slippage should not be specified",
        ]
    ] = None,
    slippage: Optional[
        Annotated[
            str,
            "Slippage in basis points (1/10000). If specified, minAmountOut should not be specified",
        ]
    ] = "300",
    fee: Optional[
        Annotated[
            List[str],
            "Fee in basis points (1/10000) for each amountIn value. Must be in range 0-100. If specified, this percentage of each amountIn value will be sent to feeReceiver",
        ]
    ] = None,
    feeReceiver: Optional[
        Annotated[
            str,
            "The Ethereum address that will receive the collected fee. Required if fee is provided",
        ]
    ] = None,
    disableRFQs: Optional[
        Annotated[bool, "A flag indicating whether to exclude RFQ sources from routes"]
    ] = None,
    ignoreAggregators: Optional[
        Annotated[
            List[str], "A list of swap aggregators to be ignored from consideration"
        ]
    ] = None,
    ignoreStandards: Optional[
        Annotated[List[str], "A list of standards to be ignored from consideration"]
    ] = None,
) -> Dict[str, Any]:
    """
    Best route from a token to another.

    :param fromAddress: Ethereum address of the wallet to send the transaction from
    :param amountIn: Amount of tokenIn to swap in wei
    :param tokenIn: Ethereum address of the token to swap from. For ETH, use 0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee
    :param tokenOut: Ethereum address of the token to swap to. For ETH, use 0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee
    :param variableEstimates: Variable estimates
    :param chainId: Chain ID of the network to execute the transaction on
    :param routingStrategy: Routing strategy to use
    :param priceImpact: Flag that indicates whether to calculate and return the price impact of the transaction
    :param receiver: Ethereum address of the receiver of the tokenOut
    :param spender: Ethereum address of the spender of the tokenIn
    :param minAmountOut: Minimum amount out in wei. If specified, slippage should not be specified
    :param slippage: Slippage in basis points (1/10000). If specified, minAmountOut should not be specified
    :param fee: Fee in basis points (1/10000) for each amountIn value. Must be in range 0-100. If specified, this percentage of each amountIn value will be sent to feeReceiver
    :param feeReceiver: The Ethereum address that will receive the collected fee. Required if fee is provided
    :param disableRFQs: A flag indicating whether to exclude RFQ sources from routes
    :param ignoreAggregators: A list of swap aggregators to be ignored from consideration
    :param ignoreStandards: A list of standards to be ignored from consideration
    :return: Best route
    """
    data = {
        "fromAddress": fromAddress,
        "amountIn": amountIn,
        "tokenIn": tokenIn,
        "tokenOut": tokenOut,
        "variableEstimates": variableEstimates,
    }
    if chainId:
        data["chainId"] = chainId
    if routingStrategy:
        data["routingStrategy"] = routingStrategy
    if priceImpact:
        data["priceImpact"] = priceImpact
    if receiver:
        data["receiver"] = receiver
    if spender:
        data["spender"] = spender
    if minAmountOut:
        data["minAmountOut"] = minAmountOut
    if slippage:
        data["slippage"] = slippage
    if fee:
        data["fee"] = fee
    if feeReceiver:
        data["feeReceiver"] = feeReceiver
    if disableRFQs:
        data["disableRFQs"] = disableRFQs
    if ignoreAggregators:
        data["ignoreAggregators"] = ignoreAggregators
    if ignoreStandards:
        data["ignoreStandards"] = ignoreStandards
    response = requests.post(
        f"{BASE_URL}/v1/shortcuts/route", headers=HEADERS, json=data
    )
    response.raise_for_status()
    return response.json()


def get_wallet(
    fromAddress: Annotated[
        str, "Ethereum address of the wallet to send the transaction from"
    ],
    chainId: Optional[
        Annotated[int, "Chain ID of the network to execute the transaction on"]
    ] = 1,
    routingStrategy: Optional[Annotated[str, "Routing strategy to use"]] = None,
) -> List[Dict[str, Union[str, int]]]:
    """
    Returns EnsoWallet address details.

    :param fromAddress: Ethereum address of the wallet to send the transaction from
    :param chainId: Chain ID of the network to execute the transaction on
    :param routingStrategy: Routing strategy to use
    :return: EnsoWallet address details
    """
    params = {
        "fromAddress": fromAddress,
    }
    if chainId:
        params["chainId"] = chainId
    if routingStrategy:
        params["routingStrategy"] = routingStrategy
    response = requests.get(f"{BASE_URL}/v1/wallet", headers=HEADERS, params=params)
    response.raise_for_status()
    return response.json()


def create_approve_transaction(
    fromAddress: Annotated[
        str, "Ethereum address of the wallet to send the transaction from"
    ],
    tokenAddress: Annotated[str, "ERC20 token address of the token to approve"],
    amount: Annotated[str, "Amount of tokens to approve in wei"],
    chainId: Optional[
        Annotated[int, "Chain ID of the network to execute the transaction on"]
    ] = 1,
    routingStrategy: Optional[Annotated[str, "Routing strategy to use"]] = "router",
) -> Dict[str, Any]:
    """
    Returns transaction that approves your EnsoWallet to spend tokens.

    :param fromAddress: Ethereum address of the wallet to send the transaction from
    :param tokenAddress: ERC20 token address of the token to approve
    :param amount: Amount of tokens to approve in wei
    :param chainId: Chain ID of the network to execute the transaction on
    :param routingStrategy: Routing strategy to use
    :return: Transaction that approves your EnsoWallet to spend tokens
    """
    params = {
        "fromAddress": fromAddress,
        "tokenAddress": tokenAddress,
        "amount": amount,
    }
    if chainId:
        params["chainId"] = chainId
    if routingStrategy:
        params["routingStrategy"] = routingStrategy
    response = requests.get(
        f"{BASE_URL}/v1/wallet/approve", headers=HEADERS, params=params
    )
    response.raise_for_status()
    return response.json()


def get_wallet_approvals(
    fromAddress: Annotated[
        str, "Ethereum address of the wallet to send the transaction from"
    ],
    chainId: Optional[
        Annotated[int, "Chain ID of the network to execute the transaction on"]
    ] = 1,
    routingStrategy: Optional[Annotated[str, "Routing strategy to use"]] = None,
) -> List[Dict[str, Union[str, int]]]:
    """
    Returns all approvals for a given wallet.

    :param fromAddress: Ethereum address of the wallet to send the transaction from
    :param chainId: Chain ID of the network to execute the transaction on
    :param routingStrategy: Routing strategy to use
    :return: All approvals for a given wallet
    """
    params = {
        "fromAddress": fromAddress,
    }
    if chainId:
        params["chainId"] = chainId
    if routingStrategy:
        params["routingStrategy"] = routingStrategy
    response = requests.get(
        f"{BASE_URL}/v1/wallet/approvals", headers=HEADERS, params=params
    )
    response.raise_for_status()
    return response.json()


def get_wallet_balances(
    eoaAddress: Annotated[
        str, "Address of the eoa with which to associate the ensoWallet for balances"
    ],
    useEoa: Optional[
        Annotated[
            bool,
            "If true returns balances for the provided eoaAddress, instead of the associated ensoWallet",
        ]
    ] = True,
    chainId: Optional[
        Annotated[int, "Chain ID of the network to execute the transaction on"]
    ] = 1,
) -> Dict[str, Any]:
    """
    Returns balances for a given wallet.

    :param eoaAddress: Address of the eoa with which to associate the ensoWallet for balances
    :param useEoa: If true returns balances for the provided eoaAddress, instead of the associated ensoWallet
    :param chainId: Chain ID of the network to execute the transaction on
    :return: Balances for a given wallet
    """
    params = {
        "eoaAddress": eoaAddress,
        "useEoa": str(useEoa).lower(),
    }
    if chainId:
        params["chainId"] = chainId

    response = requests.get(
        f"{BASE_URL}/v1/wallet/balances", headers=HEADERS, params=params
    )

    response.raise_for_status()

    return response.json()


def get_tokens(
    protocolSlug: Optional[Annotated[str, "Protocol Slug of defi token"]] = None,
    underlyingTokens: Optional[
        Annotated[List[str], "Underlying tokens of defi token"]
    ] = None,
    primaryAddress: Optional[
        Annotated[str, "Ethereum address for contract interaction of defi token"]
    ] = None,
    address: Optional[Annotated[str, "Ethereum address of the token"]] = None,
    chainId: Optional[Annotated[int, "Chain ID of the network of the token"]] = None,
    type: Optional[Annotated[str, "Type of token"]] = None,
    page: Optional[
        Annotated[int, "Pagination page number. Pages are of length 1000"]
    ] = None,
) -> Dict[str, Any]:
    """
    Returns tokens and their details.

    :param protocolSlug: Protocol Slug of defi token
    :param underlyingTokens: Underlying tokens of defi token
    :param primaryAddress: Ethereum address for contract interaction of defi token
    :param address: Ethereum address of the token
    :param chainId: Chain ID of the network of the token
    :param type: Type of token
    :param page: Pagination page number. Pages are of length 1000
    :return: Tokens and their details
    """
    params = {}
    if protocolSlug:
        params["protocolSlug"] = protocolSlug
    if underlyingTokens:
        params["underlyingTokens"] = underlyingTokens
    if primaryAddress:
        params["primaryAddress"] = primaryAddress
    if address:
        params["address"] = address
    if chainId:
        params["chainId"] = chainId
    if type:
        params["type"] = type
    if page:
        params["page"] = page
    response = requests.get(f"{BASE_URL}/v1/tokens", headers=HEADERS, params=params)
    response.raise_for_status()
    return response.json()


def get_actions() -> List[Dict[str, Union[str, int]]]:
    """
    Returns actions available to use in bundle shortcuts.

    :return: Actions available to use in bundle shortcuts
    """
    response = requests.get(f"{BASE_URL}/v1/actions", headers=HEADERS)
    response.raise_for_status()
    return response.json()


def get_standards() -> List[Dict[str, Union[str, int]]]:
    """
    Returns standards and methods available to use in bundle shortcuts.

    :return: Standards and methods available to use in bundle shortcuts
    """
    response = requests.get(f"{BASE_URL}/v1/standards", headers=HEADERS)
    response.raise_for_status()
    return response.json()


def bundle_shortcut_transaction(
    actions: Annotated[
        List[Dict[str, Union[str, Dict[str, Union[str, List[str]]]]]],
        "List of actions to bundle",
    ],
    fromAddress: Annotated[
        str, "Ethereum address of the wallet to send the transaction from"
    ],
    chainId: Optional[
        Annotated[int, "Chain ID of the network to execute the transaction on"]
    ] = 1,
    routingStrategy: Optional[
        Annotated[str, "Routing strategy to use (router cannot be used here)"]
    ] = None,
) -> Dict[str, Any]:
    """
    Bundle a list of actions into a single tx.

    :param actions: List of actions to bundle
    :param fromAddress: Ethereum address of the wallet to send the transaction from
    :param chainId: Chain ID of the network to execute the transaction on
    :param routingStrategy: Routing strategy to use (router cannot be used here)
    :return: Bundled transaction
    """
    params = {
        "fromAddress": fromAddress,
    }
    if chainId:
        params["chainId"] = chainId
    if routingStrategy:
        params["routingStrategy"] = routingStrategy
    response = requests.post(
        f"{BASE_URL}/v1/shortcuts/bundle", headers=HEADERS, json=actions, params=params
    )
    response.raise_for_status()
    return response.json()


def get_quote(
    tokenIn: Annotated[
        List[str],
        "Ethereum address of the token to swap from. For ETH, use 0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
    ],
    tokenOut: Annotated[
        List[str],
        "Ethereum address of the token to swap to. For ETH, use 0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
    ],
    amountIn: Annotated[List[str], "Amount of tokenIn to swap in wei"],
    chainId: Optional[
        Annotated[int, "Chain ID of the network to execute the transaction on"]
    ] = 1,
    fromAddress: Optional[
        Annotated[str, "Ethereum address of the wallet to send the transaction from"]
    ] = None,
    routingStrategy: Optional[Annotated[str, "Routing strategy to use"]] = None,
    fee: Optional[
        Annotated[
            List[str],
            "Fee in basis points (1/10000) for each amountIn value. Must be in range 0-100. If specified, this percentage of each amountIn value will be sent to feeReceiver",
        ]
    ] = None,
    feeReceiver: Optional[
        Annotated[
            str,
            "The Ethereum address that will receive the collected fee. Required if fee is provided",
        ]
    ] = None,
    disableRFQs: Optional[
        Annotated[bool, "A flag indicating whether to exclude RFQ sources from routes"]
    ] = None,
    ignoreAggregators: Optional[
        Annotated[
            List[str], "A list of swap aggregators to be ignored from consideration"
        ]
    ] = None,
    ignoreStandards: Optional[
        Annotated[List[str], "A list of standards to be ignored from consideration"]
    ] = None,
    priceImpact: Optional[
        Annotated[
            bool,
            "Flag that indicates whether to calculate and return the price impact of the transaction",
        ]
    ] = None,
) -> Dict[str, Any]:
    """
    Quote from a token to another.

    :param tokenIn: Ethereum address of the token to swap from. For ETH, use 0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee
    :param tokenOut: Ethereum address of the token to swap to. For ETH, use 0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee
    :param amountIn: Amount of tokenIn to swap in wei
    :param chainId: Chain ID of the network to execute the transaction on
    :param fromAddress: Ethereum address of the wallet to send the transaction from
    :param routingStrategy: Routing strategy to use
    :param fee: Fee in basis points (1/10000) for each amountIn value. Must be in range 0-100. If specified, this percentage of each amountIn value will be sent to feeReceiver
    :param feeReceiver: The Ethereum address that will receive the collected fee. Required if fee is provided
    :param disableRFQs: A flag indicating whether to exclude RFQ sources from routes
    :param ignoreAggregators: A list of swap aggregators to be ignored from consideration
    :param ignoreStandards: A list of standards to be ignored from consideration
    :param priceImpact: Flag that indicates whether to calculate and return the price impact of the transaction
    :return: Quote from a token to another
    """
    params = {
        "tokenIn": tokenIn,
        "tokenOut": tokenOut,
        "amountIn": amountIn,
    }
    if chainId:
        params["chainId"] = chainId
    if fromAddress:
        params["fromAddress"] = fromAddress
    if routingStrategy:
        params["routingStrategy"] = routingStrategy
    if fee:
        params["fee"] = fee
    if feeReceiver:
        params["feeReceiver"] = feeReceiver
    if disableRFQs:
        params["disableRFQs"] = disableRFQs
    if ignoreAggregators:
        params["ignoreAggregators"] = ignoreAggregators
    if ignoreStandards:
        params["ignoreStandards"] = ignoreStandards
    if priceImpact:
        params["priceImpact"] = priceImpact
    response = requests.get(
        f"{BASE_URL}/v1/shortcuts/quote", headers=HEADERS, params=params
    )
    response.raise_for_status()
    return response.json()


def simulate_route(
    route: Annotated[
        List[Dict[str, Union[str, List[str]]]],
        "Ordered array of paths that you want to simulate",
    ],
    chainId: Optional[
        Annotated[int, "Chain ID of the network to execute the transaction on"]
    ] = 1,
    fromAddress: Optional[
        Annotated[str, "Ethereum address of the wallet to send the transaction from"]
    ] = None,
    routingStrategy: Optional[Annotated[str, "Routing strategy to use"]] = None,
    fee: Optional[
        Annotated[
            List[str],
            "Fee in basis points (1/10000) for each route. If specified, this percentage of each amountIn value will be sent to feeReceiver",
        ]
    ] = None,
    feeReceiver: Optional[
        Annotated[
            str,
            "The Ethereum address that will receive the collected fee. Required if fee is provided",
        ]
    ] = None,
    disableRFQs: Optional[
        Annotated[bool, "A flag indicating whether to exclude RFQ sources from routes"]
    ] = None,
    ignoreAggregators: Optional[
        Annotated[
            List[str], "A list of swap aggregators to be ignored from consideration"
        ]
    ] = None,
    blockNumber: Optional[Annotated[str, "Hex string of block number"]] = None,
) -> Dict[str, Any]:
    """
    Simulate a route.

    :param route: Ordered array of paths that you want to simulate
    :param chainId: Chain ID of the network to execute the transaction on
    :param fromAddress: Ethereum address of the wallet to send the transaction from
    :param routingStrategy: Routing strategy to use
    :param fee: Fee in basis points (1/10000) for each route. If specified, this percentage of each amountIn value will be sent to feeReceiver
    :param feeReceiver: The Ethereum address that will receive the collected fee. Required if fee is provided
    :param disableRFQs: A flag indicating whether to exclude RFQ sources from routes
    :param ignoreAggregators: A list of swap aggregators to be ignored from consideration
    :param blockNumber: Hex string of block number
    :return: Simulated route
    """
    data = {
        "route": route,
    }
    if chainId:
        data["chainId"] = chainId
    if fromAddress:
        data["fromAddress"] = fromAddress
    if routingStrategy:
        data["routingStrategy"] = routingStrategy
    if fee:
        data["fee"] = fee
    if feeReceiver:
        data["feeReceiver"] = feeReceiver
    if disableRFQs:
        data["disableRFQs"] = disableRFQs
    if ignoreAggregators:
        data["ignoreAggregators"] = ignoreAggregators
    if blockNumber:
        data["blockNumber"] = blockNumber
    response = requests.post(
        f"{BASE_URL}/v1/shortcuts/quote", headers=HEADERS, json=data
    )
    response.raise_for_status()
    return response.json()


def get_ipor_shortcut_transaction(
    amountIn: Annotated[str, "Amount of tokenIn in wei"],
    tokenIn: Annotated[
        str,
        "Address of the tokenIn. For ETH, use 0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
    ],
    tokenBToBuy: Annotated[str, "Address of the tokenBToBuy"],
    percentageForTokenB: Annotated[
        str, "Percentage of tokenB to buy in basis points (1/10000)"
    ],
    fromAddress: Annotated[
        str, "Ethereum address of the wallet to send the transaction from"
    ],
    chainId: Optional[
        Annotated[int, "Chain ID of the network to execute the transaction on"]
    ] = 1,
    isRouter: Optional[
        Annotated[bool, "Flag that indicates whether to use the shared router"]
    ] = None,
    slippage: Optional[
        Annotated[str, "Slippage in basis points (1/10000). Default is 300"]
    ] = "300",
    simulate: Optional[
        Annotated[
            bool,
            "Flag that indicates whether to simulate the transaction, verify some assertions, return simulationURL and events",
        ]
    ] = False,
) -> Dict[str, Any]:
    """
    Get transaction for IPOR shortcut.

    :param amountIn: Amount of tokenIn in wei
    :param tokenIn: Address of the tokenIn. For ETH, use 0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee
    :param tokenBToBuy: Address of the tokenBToBuy
    :param percentageForTokenB: Percentage of tokenB to buy in basis points (1/10000)
    :param fromAddress: Ethereum address of the wallet to send the transaction from
    :param chainId: Chain ID of the network to execute the transaction on
    :param isRouter: Flag that indicates whether to use the shared router
    :param slippage: Slippage in basis points (1/10000). Default is 300
    :param simulate: Flag that indicates whether to simulate the transaction, verify some assertions, return simulationURL and events
    :return: Transaction for IPOR shortcut
    """
    data = {
        "amountIn": amountIn,
        "tokenIn": tokenIn,
        "tokenBToBuy": tokenBToBuy,
        "percentageForTokenB": percentageForTokenB,
    }
    if chainId:
        data["chainId"] = chainId
    if fromAddress:
        data["fromAddress"] = fromAddress
    if isRouter:
        data["isRouter"] = isRouter
    if slippage:
        data["slippage"] = slippage
    if simulate:
        data["simulate"] = simulate
    response = requests.post(
        f"{BASE_URL}/v1/shortcuts/static/ipor", headers=HEADERS, json=data
    )
    response.raise_for_status()
    return response.json()


def get_protocols(
    slug: Optional[Annotated[str, "slug of the project to search for"]] = None
) -> List[Dict[str, Union[str, int]]]:
    """
    Returns projects and relevant protocols available to use in bundle shortcuts.

    :param slug: slug of the project to search for
    :return: Projects and relevant protocols available to use in bundle shortcuts
    """
    params = {}
    if slug:
        params["slug"] = slug
    response = requests.get(f"{BASE_URL}/v1/protocols", headers=HEADERS, params=params)
    response.raise_for_status()
    return response.json()
