import logging
import sys
from binance import Client
from binance.enums import *
import argparse
from decimal import Decimal, ROUND_DOWN
import time

# Configure logging
logging.basicConfig(
    filename='trading_bot.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Hardcoded Binance Testnet API credentials (replace with new credentials after revoking the exposed ones)
API_KEY = '9ab7776ed3734a4dd1e6dfa13b1efc988bea90f16a1c6fd673c5bb62f2680490'
API_SECRET = 'a51a6ed6055620e121bcd43ee92e8c608590f40be86b9f94ed79db111e72a384'

class TradingBot:
    def __init__(self, testnet=True):
        """Initialize the trading bot with hardcoded Binance API credentials."""
        try:
            self.client = Client(API_KEY, API_SECRET, testnet=True)
            self.base_url = 'https://testnet.binancefuture.com'
            # Synchronize local time with Binance server time
            server_time = self.client.get_server_time()['serverTime']
            local_time = int(round(time.time() * 1000))
            self.client.timestamp_offset = server_time - local_time
            logging.info(f"TradingBot initialized successfully and time synchronized with Binance server. Offset: {self.client.timestamp_offset} ms")
        except Exception as e:
            logging.error(f"Initialization error: {str(e)}")
            raise

    def validate_input(self, symbol, side, order_type, quantity, price=None, stop_price=None):
        """Validate user input parameters."""
        try:
            if not symbol or not isinstance(symbol, str):
                raise ValueError("Symbol must be a non-empty string")
            if side not in ['BUY', 'SELL']:
                raise ValueError("Side must be either 'BUY' or 'SELL'")
            if order_type not in ['MARKET', 'LIMIT', 'STOP']:
                raise ValueError("Order type must be 'MARKET', 'LIMIT', or 'STOP'")
            quantity = Decimal(str(quantity))
            if quantity <= 0:
                raise ValueError("Quantity must be positive")
            if price is not None:
                price = Decimal(str(price))
                if price <= 0:
                    raise ValueError("Price must be positive")
            if stop_price is not None:
                stop_price = Decimal(str(stop_price))
                if stop_price <= 0:
                    raise ValueError("Stop price must be positive")
        except ValueError as e:
            logging.error(f"Input validation error: {str(e)}")
            raise
        return symbol.upper(), side, order_type, quantity, price, stop_price

    def place_market_order(self, symbol, side, quantity):
        """Place a market order."""
        try:
            order = self.client.create_order(
                symbol=symbol,
                side=side,
                type=ORDER_TYPE_MARKET,
                quantity=str(quantity)
            )
            logging.info(f"Market order placed: {order}")
            return order
        except Exception as e:
            logging.error(f"Error placing market order: {str(e)}")
            raise

    def place_limit_order(self, symbol, side, quantity, price):
        """Place a limit order."""
        try:
            order = self.client.create_order(
                symbol=symbol,
                side=side,
                type=ORDER_TYPE_LIMIT,
                timeInForce=TIME_IN_FORCE_GTC,
                quantity=str(quantity),
                price=str(price.quantize(Decimal('0.01'), rounding=ROUND_DOWN))
            )
            logging.info(f"Limit order placed: {order}")
            return order
        except Exception as e:
            logging.error(f"Error placing limit order: {str(e)}")
            raise

    def place_stop_limit_order(self, symbol, side, quantity, price, stop_price):
        """Place a stop-limit order."""
        try:
            order = self.client.create_order(
                symbol=symbol,
                side=side,
                type=ORDER_TYPE_STOP,
                timeInForce=TIME_IN_FORCE_GTC,
                quantity=str(quantity),
                price=str(price.quantize(Decimal('0.01'), rounding=ROUND_DOWN)),
                stopPrice=str(stop_price.quantize(Decimal('0.01'), rounding=ROUND_DOWN))
            )
            logging.info(f"Stop-limit order placed: {order}")
            return order
        except Exception as e:
            logging.error(f"Error placing stop-limit order: {str(e)}")
            raise

    def get_order_status(self, symbol, order_id):
        """Retrieve the status of an order."""
        try:
            status = self.client.get_order(symbol=symbol, orderId=order_id)
            logging.info(f"Order status retrieved: {status}")
            return status
        except Exception as e:
            logging.error(f"Error retrieving order status: {str(e)}")
            raise

def main():
    parser = argparse.ArgumentParser(description="Binance Futures Testnet Trading Bot")
    parser.add_argument('--symbol', default='BTCUSDT', help="Trading pair (default: BTCUSDT)")
    parser.add_argument('--side', choices=['BUY', 'SELL'], required=True, help="Order side: BUY or SELL")
    parser.add_argument('--type', choices=['MARKET', 'LIMIT', 'STOP'], required=True, help="Order type: MARKET, LIMIT, or STOP")
    parser.add_argument('--quantity', type=float, required=True, help="Order quantity")
    parser.add_argument('--price', type=float, help="Limit price (required for LIMIT and STOP orders)")
    parser.add_argument('--stop_price', type=float, help="Stop price (required for STOP orders)")

    args = parser.parse_args()

    try:
        bot = TradingBot(testnet=True)
        # Test API connectivity by fetching account info
        print("Fetching account info...")
        account_info = bot.client.get_account()
        print(f"Account Info: {account_info}")
        logging.info(f"Account Info: {account_info}")
        # Check symbol trading rules
        print("Fetching symbol info for BTCUSDT...")
        symbol_info = bot.client.get_symbol_info('BTCUSDT')
        print(f"Symbol Info: {symbol_info}")
        logging.info(f"Symbol Info: {symbol_info}")

        symbol, side, order_type, quantity, price, stop_price = bot.validate_input(
            args.symbol, args.side, args.type, args.quantity, args.price, args.stop_price
        )

        # Validate quantity against symbol info
        for filter in symbol_info['filters']:
            if filter['filterType'] == 'LOT_SIZE':
                min_qty = Decimal(filter['minQty'])
                if quantity < min_qty:
                    raise ValueError(f"Quantity {quantity} is below minimum {min_qty} for {symbol}")

        if order_type == 'MARKET':
            order = bot.place_market_order(symbol, side, quantity)
        elif order_type == 'LIMIT':
            if price is None:
                raise ValueError("Price is required for LIMIT orders")
            order = bot.place_limit_order(symbol, side, quantity, price)
        elif order_type == 'STOP':
            if price is None or stop_price is None:
                raise ValueError("Both price and stop_price are required for STOP orders")
            order = bot.place_stop_limit_order(symbol, side, quantity, price, stop_price)

        # Retrieve and display order status
        status = bot.get_order_status(symbol, order['orderId'])
        print(f"Order Details: {order}")
        print(f"Order Status: {status}")

    except Exception as e:
        logging.error(f"Main execution error: {str(e)}")
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()