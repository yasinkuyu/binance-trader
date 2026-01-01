#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# Binance Trader with Advanced Bollinger Bands Strategy

import sys
import argparse
import time
import logging

sys.path.insert(0, './app')

from BollingerTradingBot import BollingerTradingBot


def setup_logging(debug=False):
    """Setup logging configuration"""
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('bollinger_trader.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )


if __name__ == '__main__':
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description='Binance Bollinger Bands Trading Bot - Advanced Strategy',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Basic usage with default settings
  python trader_bollinger.py --symbol BTCUSDT --amount 100

  # Custom Bollinger Bands parameters
  python trader_bollinger.py --symbol ETHUSDT --amount 50 --bb_period 20 --bb_stddev 2.0

  # Aggressive trading with lower RSI threshold
  python trader_bollinger.py --symbol BNBUSDT --quantity 10 --rsi_oversold 35 --rsi_overbought 65

  # Conservative trading with higher confidence requirement
  python trader_bollinger.py --symbol ADAUSDT --amount 100 --min_confidence 70

  # Test mode (no real trades)
  python trader_bollinger.py --symbol BTCUSDT --amount 100 --test_mode
        '''
    )

    # Required parameters
    parser.add_argument('--symbol', type=str, required=True,
                        help='Trading pair symbol (e.g., BTCUSDT, ETHBTC)')

    # Position sizing (choose one)
    parser.add_argument('--quantity', type=float, default=0,
                        help='Fixed quantity to trade (default: 0 = auto-calculate)')
    parser.add_argument('--amount', type=float, default=0,
                        help='Amount in quote currency to trade (e.g., 100 USDT)')

    # Bollinger Bands parameters
    parser.add_argument('--bb_period', type=int, default=20,
                        help='Bollinger Bands period (default: 20)')
    parser.add_argument('--bb_stddev', type=float, default=2.0,
                        help='Bollinger Bands standard deviation (default: 2.0)')

    # RSI parameters
    parser.add_argument('--rsi_period', type=int, default=14,
                        help='RSI period (default: 14)')
    parser.add_argument('--rsi_oversold', type=float, default=30,
                        help='RSI oversold threshold (default: 30)')
    parser.add_argument('--rsi_overbought', type=float, default=70,
                        help='RSI overbought threshold (default: 70)')

    # Volume parameters
    parser.add_argument('--volume_threshold', type=float, default=1.2,
                        help='Volume ratio threshold for confirmation (default: 1.2)')

    # Risk management
    parser.add_argument('--stop_loss_atr', type=float, default=2.0,
                        help='Stop loss as multiple of ATR (default: 2.0)')
    parser.add_argument('--take_profit', type=str, default='middle',
                        help='Take profit target: "middle", "upper", or percentage (default: middle)')
    parser.add_argument('--risk_per_trade', type=float, default=2.0,
                        help='Risk percentage per trade (default: 2.0%%)')

    # Strategy filters
    parser.add_argument('--min_bb_width', type=float, default=1.0,
                        help='Minimum BB width to trade (volatility filter) (default: 1.0)')
    parser.add_argument('--max_bb_width', type=float, default=10.0,
                        help='Maximum BB width to trade (volatility filter) (default: 10.0)')
    parser.add_argument('--min_confidence', type=int, default=50,
                        help='Minimum confidence score to execute trade (default: 50)')

    # Data parameters
    parser.add_argument('--interval', type=str, default='5m',
                        help='Candlestick interval (1m, 3m, 5m, 15m, 30m, 1h, 4h, 1d) (default: 5m)')
    parser.add_argument('--kline_limit', type=int, default=100,
                        help='Number of historical candles to fetch (default: 100)')

    # Bot behavior
    parser.add_argument('--wait_time', type=float, default=10,
                        help='Wait time between analysis cycles (seconds) (default: 10)')
    parser.add_argument('--max_trades', type=int, default=0,
                        help='Maximum number of trades to execute (0 = unlimited) (default: 0)')
    parser.add_argument('--test_mode', action='store_true',
                        help='Test mode - analyze only, no real trades')
    parser.add_argument('--debug', action='store_true',
                        help='Enable debug logging')

    # Commission type
    parser.add_argument('--commission', type=str, default='BNB',
                        help='Commission payment type: BNB or TOKEN (default: BNB)')

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.debug)
    logger = logging.getLogger(__name__)

    # Display configuration
    print('=' * 70)
    print('BINANCE BOLLINGER BANDS TRADING BOT')
    print('=' * 70)
    print(f'\nTrading Symbol: {args.symbol}')
    print(f'Interval: {args.interval}')
    print(f'Test Mode: {"YES - No real trades will be executed" if args.test_mode else "NO - Live trading"}')
    print(f'\n--- Strategy Parameters ---')
    print(f'Bollinger Bands: {args.bb_period} period, {args.bb_stddev} std dev')
    print(f'RSI: {args.rsi_period} period (Oversold: {args.rsi_oversold}, Overbought: {args.rsi_overbought})')
    print(f'Volume Threshold: {args.volume_threshold}x average')
    print(f'BB Width Filter: {args.min_bb_width}% - {args.max_bb_width}%')
    print(f'Minimum Confidence: {args.min_confidence}%')
    print(f'\n--- Risk Management ---')
    print(f'Stop Loss: {args.stop_loss_atr}x ATR')
    print(f'Take Profit: {args.take_profit}')
    print(f'Risk per Trade: {args.risk_per_trade}%')
    print(f'\n--- Position Sizing ---')
    if args.quantity > 0:
        print(f'Fixed Quantity: {args.quantity}')
    elif args.amount > 0:
        print(f'Fixed Amount: {args.amount} (quote currency)')
    else:
        print(f'Dynamic sizing based on risk ({args.risk_per_trade}% per trade)')
    print(f'\n--- Operational Parameters ---')
    print(f'Wait Time: {args.wait_time}s between cycles')
    print(f'Max Trades: {args.max_trades if args.max_trades > 0 else "Unlimited"}')
    print(f'Commission Type: {args.commission}')
    print('=' * 70)
    print()

    # Confirmation for live trading
    if not args.test_mode:
        print('⚠️  WARNING: You are about to start LIVE TRADING with real money!')
        print('⚠️  Make sure you have:')
        print('   1. Configured your API keys in app/config.py')
        print('   2. Enabled trading permissions on your API key')
        print('   3. Tested the strategy in --test_mode first')
        print('   4. Understood the risks involved')
        print()
        response = input('Type "START" to begin live trading, or anything else to exit: ')
        if response.strip().upper() != 'START':
            print('Exiting...')
            sys.exit(0)
        print()

    try:
        # Initialize and run the trading bot
        bot = BollingerTradingBot(args)
        bot.run()

    except KeyboardInterrupt:
        logger.info('\n\nBot stopped by user (Ctrl+C)')
        print('\nBot stopped gracefully. Goodbye!')

    except Exception as e:
        logger.error(f'Fatal error: {e}', exc_info=True)
        print(f'\n❌ Fatal error: {e}')
        print('Check bollinger_trader.log for details')
        sys.exit(1)
