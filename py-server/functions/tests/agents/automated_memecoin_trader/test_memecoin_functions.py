# tests/test_memecoin_functions.py
import types
import sys
import os

# Add the current directory to Python path so we can import the modules
sys.path.insert(0, '.')

mock_wallets = ['wallet1', 'wallet2', 'wallet3', 'wallet4', 'wallet5']
mock_balances = [{
  "address": "wallet1",
  "amount": 0.002512,
  "name": "BTC",
  "chain": "EVM",
  "symbol": "BTC",
  "decimals": 18,
  "price": 115165,
  "usd_amount": 289.52,
  "logo_uri": "https://example.com/logo.png",
  "wallet_address": "wallet1",
  "wallet_type": "EVM",
  "protocol": "covalent",
  "updatedAt": "2021-01-01T00:00:00Z"
},{
  "address": "wallet2",
  "amount": 0.13571,
  "name": "SOL",
  "chain": "SOLANA",
  "symbol": "SOL",
  "decimals": 9,
  "price": 195,
  "usd_amount": 26.46,
  "logo_uri": "https://example.com/logo.png",
  "wallet_address": "wallet2",
  "wallet_type": "SOLANA",
  "protocol": "covalent",
  "updatedAt": "2021-01-01T00:00:00Z"
}]

def test_get_top_holdings_of_traders(monkeypatch):
    # Import directly from the module file
    from agents.automated_memecoin_trader.memecoin_functions import get_top_holdings_of_traders

    # mocks mínimos del comportamiento
    monkeypatch.setattr('agents.automated_memecoin_trader.memecoin_functions.get_top_traders_wallets', lambda: mock_wallets)
    monkeypatch.setattr('agents.automated_memecoin_trader.memecoin_functions.get_wallet_balance', lambda w, t: mock_balances)

    # determinism in random.sample
    import random
    monkeypatch.setattr('agents.automated_memecoin_trader.memecoin_functions.random', types.SimpleNamespace(sample=lambda seq, n: list(seq)[:n]))

    # enum simulated
    from services.balances import BalanceServiceType
    monkeypatch.setattr('agents.automated_memecoin_trader.memecoin_functions.BalanceServiceType', BalanceServiceType)

    result = get_top_holdings_of_traders()
    
    # Verify the result structure
    assert len(result) == 4  # Should return 4 wallet holdings
    
    # Verify that SOL tokens were filtered out (function filters out SOL tokens)
    for holdings in result:
        for token in holdings:
            assert token["symbol"] != "SOL"
        
        # Verify that results are sorted by USD amount (descending)
        usd_amounts = [token["usd_amount"] for token in holdings]
        assert usd_amounts == sorted(usd_amounts, reverse=True)
