# Trading_bot

please Run the command "pip install" - It will install all neccessary dependencies required to run the application
like python-binance

Go to https://testnet.binancefuture.com

Login or register a new account.

Navigate to Dashboard → API Management

Create a new API key (e.g., "Test Bot")

Copy:
      API Key
      API Secret

ADD YOUR CREDENTIALS to trading_bot
API_KEY = "YOUR_TESTNET_API_KEY"
API_SECRET = "YOUR_TESTNET_API_SECRET"

Then Run The command:
python trading_bot.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01 cmd
