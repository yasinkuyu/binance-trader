# -*- coding: UTF-8 -*-
# Bollinger Bands Trading Bot - Main Implementation

import time
import logging
import math
from datetime import datetime
from typing import Optional, Dict

import config
from BinanceAPI import BinanceAPI
from BollingerStrategy import BollingerStrategy
from Orders import Orders
from Database import Database


class BollingerTradingBot:
    """
    Advanced Bollinger Bands Trading Bot for Binance

    Features:
    - Bollinger Bands with RSI and Volume confirmation
    - Dynamic risk management
    - Position sizing
    - Comprehensive logging
    """

    # Commission rates
    TOKEN_COMMISSION = 0.001  # 0.1%
    BNB_COMMISSION = 0.0005   # 0.05%

    def __init__(self, args):
        """
        Initialize the trading bot

        Args:
            args: Parsed command line arguments
        """
        self.args = args
        self.symbol = args.symbol
        self.logger = logging.getLogger(f'BollingerBot-{self.symbol}')

        # Initialize Binance API client
        self.client = BinanceAPI(config.api_key, config.api_secret)

        # Set commission type
        self.commission = self.BNB_COMMISSION if args.commission == 'BNB' else self.TOKEN_COMMISSION

        # Initialize strategy
        strategy_config = {
            'bb_period': args.bb_period,
            'bb_std_dev': args.bb_stddev,
            'rsi_period': args.rsi_period,
            'rsi_oversold': args.rsi_oversold,
            'rsi_overbought': args.rsi_overbought,
            'volume_threshold': args.volume_threshold,
            'stop_loss_atr': args.stop_loss_atr,
            'take_profit': args.take_profit,
            'min_bb_width': args.min_bb_width,
            'max_bb_width': args.max_bb_width
        }
        self.strategy = BollingerStrategy(strategy_config)

        # Trading state
        self.position = None  # Current position {price, quantity, timestamp, order_id}
        self.trades_executed = 0
        self.total_profit = 0.0
        self.winning_trades = 0
        self.losing_trades = 0

        # Market filters (populated during validation)
        self.step_size = 0
        self.tick_size = 0
        self.min_qty = 0
        self.min_notional = 0

    def validate_symbol(self) -> bool:
        """
        Validate symbol and get trading rules

        Returns:
            True if symbol is valid
        """
        try:
            symbol_info = Orders.get_info(self.symbol)

            if not symbol_info:
                self.logger.error(f'Invalid symbol: {self.symbol}')
                return False

            # Extract filters
            filters = {item['filterType']: item for item in symbol_info['filters']}

            self.step_size = float(filters['LOT_SIZE']['stepSize'])
            self.tick_size = float(filters['PRICE_FILTER']['tickSize'])
            self.min_qty = float(filters['LOT_SIZE']['minQty'])
            self.min_notional = float(filters['MIN_NOTIONAL']['minNotional'])

            self.logger.info(f'Symbol validated: {self.symbol}')
            self.logger.debug(f'Step size: {self.step_size}, Tick size: {self.tick_size}')
            self.logger.debug(f'Min qty: {self.min_qty}, Min notional: {self.min_notional}')

            return True

        except Exception as e:
            self.logger.error(f'Symbol validation error: {e}')
            return False

    def format_quantity(self, quantity: float) -> float:
        """Format quantity according to step size"""
        return float(self.step_size * math.floor(quantity / self.step_size))

    def format_price(self, price: float) -> float:
        """Format price according to tick size"""
        return float(self.tick_size * math.floor(price / self.tick_size))

    def get_klines(self) -> list:
        """
        Fetch historical kline data

        Returns:
            List of klines
        """
        try:
            # Calculate time range
            interval_seconds = self._interval_to_seconds(self.args.interval)
            end_time = int(time.time() * 1000)
            start_time = end_time - (interval_seconds * 1000 * self.args.kline_limit)

            klines = self.client.get_klines(
                self.symbol,
                self.args.interval,
                start_time,
                end_time
            )

            return klines

        except Exception as e:
            self.logger.error(f'Error fetching klines: {e}')
            return []

    def _interval_to_seconds(self, interval: str) -> int:
        """Convert interval string to seconds"""
        multipliers = {
            'm': 60,
            'h': 3600,
            'd': 86400
        }
        unit = interval[-1]
        value = int(interval[:-1])
        return value * multipliers.get(unit, 60)

    def analyze_market(self) -> Optional[Dict]:
        """
        Analyze current market conditions

        Returns:
            Analysis result dictionary or None
        """
        try:
            # Get current price and volume
            ticker = self.client.get_ticker(self.symbol)
            current_price = float(ticker['lastPrice'])
            current_volume = float(ticker['volume'])

            # Get historical data
            klines = self.get_klines()

            if not klines:
                self.logger.warning('No kline data available')
                return None

            # Run strategy analysis
            analysis = self.strategy.analyze(klines, current_price, current_volume)

            return analysis

        except Exception as e:
            self.logger.error(f'Market analysis error: {e}')
            return None

    def execute_buy(self, analysis: Dict) -> bool:
        """
        Execute buy order

        Args:
            analysis: Market analysis result

        Returns:
            True if order executed successfully
        """
        if self.args.test_mode:
            self.logger.info(f'[TEST MODE] Would BUY at {analysis["entry_price"]:.8f}')
            self.logger.info(f'[TEST MODE] Stop Loss: {analysis["stop_loss"]:.8f}, Take Profit: {analysis["take_profit"]:.8f}')
            return True

        try:
            # Calculate quantity
            if self.args.quantity > 0:
                quantity = self.args.quantity
            elif self.args.amount > 0:
                quantity = self.args.amount / analysis['entry_price']
            else:
                # Use strategy-based position sizing
                balance = self._get_balance()
                quantity = self.strategy.calculate_position_size(
                    balance,
                    analysis['entry_price'],
                    self.args.risk_per_trade,
                    analysis['stop_loss']
                )

            # Format and validate quantity
            quantity = self.format_quantity(quantity)

            if quantity < self.min_qty:
                self.logger.warning(f'Quantity {quantity} below minimum {self.min_qty}')
                return False

            # Get current order book
            bid_price, ask_price = Orders.get_order_book(self.symbol)
            buy_price = self.format_price(bid_price + self.tick_size)

            # Place buy order
            self.logger.info(f'🔵 Placing BUY order: {quantity} @ {buy_price}')
            order_id = Orders.buy_limit(self.symbol, quantity, buy_price)

            if order_id:
                # Record position
                self.position = {
                    'order_id': order_id,
                    'quantity': quantity,
                    'price': buy_price,
                    'timestamp': datetime.now(),
                    'stop_loss': analysis['stop_loss'],
                    'take_profit': analysis['take_profit']
                }

                # Log to database
                Database.write([
                    order_id,
                    self.symbol,
                    0,
                    buy_price,
                    'BUY',
                    quantity,
                    self.args.risk_per_trade
                ])

                self.logger.info(f'✅ Buy order placed: ID {order_id}')
                self.logger.info(f'   Quantity: {quantity}, Price: {buy_price}')
                self.logger.info(f'   Stop Loss: {analysis["stop_loss"]:.8f}')
                self.logger.info(f'   Take Profit: {analysis["take_profit"]:.8f}')

                return True

        except Exception as e:
            self.logger.error(f'Buy order error: {e}')

        return False

    def execute_sell(self, analysis: Dict, reason: str = 'Signal') -> bool:
        """
        Execute sell order

        Args:
            analysis: Market analysis result
            reason: Reason for selling

        Returns:
            True if order executed successfully
        """
        if not self.position:
            return False

        if self.args.test_mode:
            profit_pct = ((analysis['price'] - self.position['price']) / self.position['price']) * 100
            self.logger.info(f'[TEST MODE] Would SELL at {analysis["price"]:.8f} ({reason})')
            self.logger.info(f'[TEST MODE] Profit: {profit_pct:.2f}%')
            self.position = None
            return True

        try:
            quantity = self.position['quantity']

            # Get current order book
            bid_price, ask_price = Orders.get_order_book(self.symbol)
            sell_price = self.format_price(ask_price - self.tick_size)

            # Place sell order
            self.logger.info(f'🔴 Placing SELL order: {quantity} @ {sell_price} ({reason})')
            sell_order = Orders.sell_limit(self.symbol, quantity, sell_price)

            if sell_order and 'orderId' in sell_order:
                # Calculate profit
                buy_price = self.position['price']
                profit = (sell_price - buy_price) * quantity
                profit_pct = ((sell_price - buy_price) / buy_price) * 100

                # Update statistics
                self.trades_executed += 1
                self.total_profit += profit

                if profit > 0:
                    self.winning_trades += 1
                else:
                    self.losing_trades += 1

                self.logger.info(f'✅ Sell order placed: ID {sell_order["orderId"]}')
                self.logger.info(f'   Profit: {profit:.8f} ({profit_pct:.2f}%)')
                self.logger.info(f'   Buy Price: {buy_price:.8f}, Sell Price: {sell_price:.8f}')

                # Log statistics
                if self.trades_executed > 0:
                    win_rate = (self.winning_trades / self.trades_executed) * 100
                    self.logger.info(f'📊 Stats: {self.trades_executed} trades, Win rate: {win_rate:.1f}%, Total P/L: {self.total_profit:.8f}')

                # Clear position
                self.position = None

                return True

        except Exception as e:
            self.logger.error(f'Sell order error: {e}')

        return False

    def _get_balance(self) -> float:
        """Get available balance for base asset"""
        try:
            # Extract base asset from symbol (e.g., USDT from BTCUSDT)
            # This is simplified - you may need to adjust based on your symbol
            if 'USDT' in self.symbol:
                asset = 'USDT'
            elif 'BTC' in self.symbol:
                asset = 'BTC'
            elif 'ETH' in self.symbol:
                asset = 'ETH'
            elif 'BNB' in self.symbol:
                asset = 'BNB'
            else:
                asset = 'USDT'  # Default

            account = self.client.get_account()
            balances = {item['asset']: item for item in account['balances']}

            if asset in balances:
                return float(balances[asset]['free'])

        except Exception as e:
            self.logger.error(f'Error getting balance: {e}')

        return 0.0

    def run(self):
        """Main bot loop"""
        self.logger.info('Starting Bollinger Bands Trading Bot...')

        # Validate symbol
        if not self.validate_symbol():
            self.logger.error('Symbol validation failed. Exiting.')
            return

        self.logger.info('Bot started successfully. Running...')
        cycle = 0

        try:
            while True:
                cycle += 1

                # Check max trades limit
                if self.args.max_trades > 0 and self.trades_executed >= self.args.max_trades:
                    self.logger.info(f'Max trades limit reached ({self.args.max_trades}). Stopping.')
                    break

                # Analyze market
                analysis = self.analyze_market()

                if not analysis:
                    self.logger.warning('Analysis failed, skipping cycle')
                    time.sleep(self.args.wait_time)
                    continue

                # Log current state
                self.logger.debug(f'Cycle {cycle}: Price={analysis["price"]:.8f}, Signal={analysis["signal"]}, Confidence={analysis["confidence"]:.0f}%')

                # Trading logic
                if self.position is None:
                    # No position - look for buy signal
                    if analysis['signal'] == 'BUY' and analysis['confidence'] >= self.args.min_confidence:
                        self.logger.info(f'📊 BUY Signal: {analysis["reason"]} (Confidence: {analysis["confidence"]:.0f}%)')
                        self.execute_buy(analysis)

                else:
                    # Have position - look for sell signal
                    # Check stop loss
                    if analysis['price'] <= self.position['stop_loss']:
                        self.logger.warning(f'⚠️  Stop Loss triggered at {analysis["price"]:.8f}')
                        self.execute_sell(analysis, 'Stop Loss')

                    # Check take profit
                    elif analysis['price'] >= self.position['take_profit']:
                        self.logger.info(f'🎯 Take Profit target reached at {analysis["price"]:.8f}')
                        self.execute_sell(analysis, 'Take Profit')

                    # Check sell signals
                    elif analysis['signal'] in ['SELL', 'TAKE_PROFIT'] and analysis['confidence'] >= self.args.min_confidence:
                        self.logger.info(f'📊 SELL Signal: {analysis["reason"]} (Confidence: {analysis["confidence"]:.0f}%)')
                        self.execute_sell(analysis, 'Signal')

                # Wait for next cycle
                time.sleep(self.args.wait_time)

        except KeyboardInterrupt:
            self.logger.info('Bot stopped by user')

        except Exception as e:
            self.logger.error(f'Runtime error: {e}', exc_info=True)

        finally:
            self.logger.info('Bot shutdown complete')
