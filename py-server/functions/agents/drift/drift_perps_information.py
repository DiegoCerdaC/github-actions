drift_perps_explanation = """
How Perpetual Futures (Perps) Work on Drift Protocol

Drift Protocol is a decentralized platform on the Solana blockchain that allows you to trade perpetual futures (perps), a type of derivative contract that lets you speculate on the price of assets like SOL, BTC, or ETH without owning them and without an expiration date. Below is a basic guide on how to trade perps on Drift using our app.
There's no need to download or setup a wallet, and it's not needed to visit Drift website. Everything is doable within our application and Orbit (our specialized assistant).
1. Creating an Account
- This is the first step to start trading perps on Drift.
- Cost of creation: The first time you interact with Drift, you need to create an on-chain account, this requires 0.0314 SOL
- Refundable: If you delete your Drift account, you can recover this 0.0314 SOL.
- How to do it:
  1. Ask Orbit to help you creating an account by specifying the token you want to use as collateral and the amount.

2. Depositing Collateral
- What is collateral: To trade perps, you need to deposit funds as collateral to back your positions. Drift accepts various assets, like SOL, USDC, BTC, ETH, BONK, and more.
- Minimum initial deposit: The first time, you must deposit at least the equivalent of $5 in the token of your choice (e.g., ~0.03 SOL or 5 USDC, depending on prices). Subsequent deposits have no minimum.
- How to do it:
  1. Ask Orbit to deposit collateral to your Drift account specifying the token you want to deposit and the amount
- Note: Your collateral supports all your positions (cross-margin), meaning you can use the same funds for multiple trades.

3. Trading Perpetual Futures
Once you have collateral, you can start trading perps. Here's how it works and the options available:

- Selecting a market: Drift offers over 40 perp markets, like SOL-PERP, BTC-PERP, or WIF-PERP. Choose the asset you want to trade.
- Leverage: You can trade with leverage up to 20x (or 50x in some markets like SOL or BTC). Leverage amplifies gains but also losses.
- Position types:
  - Long: You bet the asset's price will go up.
  - Short: You bet the asset's price will go down.

How to open a position:
- You can ask Orbit to open a position using natural language. Here are some examples:
  - "Open a long position on SOL-PERP with 5x leverage, using a market order, with 0.15 SOL."
  - "Please open a SHORT limit order on the market SUI-PERPS, with a leverage of 10x, starting with 10 SUI and a takeProfit of 50%"

- Order types:
  - Market Order: Buys or sells at the current market price. It's fast, but there may be slight slippage (price difference).
  - Limit Order: You set a specific price to buy or sell. It only executes if the market hits that price, giving you more control.

- Risk management options:
  - Stop-Loss: An automatic order that closes your position if the price moves against you to a level you set, limiting losses.
  - Take-Profit: An automatic order that closes your position when you reach a desired profit.
  - You can just ask Orbit to set a stop-loss or take-profit percentage when opening a position.

- Monitoring and closing: If you want to check your current positions/orders, just ask Orbit to show you your open positions or orders on Drift Perps.
- Closing a Position:
    - If you have open orders or positions, you can ask Orbit to close them. Here are some examples:
        - "Close 50 % of my long market position on SOL-PERPS on Drift Perps"
        - "Orbit please close 100% of my LONG Limit position on SUI-PERPS on Drift Perps"
        - "Plase cancell all my open orders on Drift Perps"


4. Withdrawing Funds
- To withdraw collateral or profits, just ask Orbit to withdraw the amount you want to withdraw from your collateral. Here are some examples:
    - "Orbit please withdraw 0.15 SOL from my Drift Perps account collateral"
    - "I want to withdraw 10 USDC of the collateral I have on my Drift Perps account"

Summary
To trade perps on Drift using our app, you can simply ask Orbit to help you with it
1. Create an account and deposit collateral (minimum $5 equivalent first time).
2. Deposit or Withdraw collateral to increase/decrease your possible positions size.
3. Choose a market, set up a position (long or short) with leverage, and use market or limit orders. You can also set a stop-loss or take-profit percentage.
4. Manage risk with stop-loss and take-profit.
5. Monitor funding rates and liquidation risk.

Drift is fast and low-cost thanks to Solana, but perp trading is risky. If you're new, use low leverage (1x-5x) and start with small amounts.
"""
