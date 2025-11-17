#!/bin/bash
# Quick Test Script for Bollinger Bands Trading Bot
# Runs the bot in test mode with default parameters

echo "=========================================="
echo "Bollinger Bands Bot - Test Mode"
echo "=========================================="
echo ""
echo "This will run the bot in TEST MODE (no real trades)"
echo ""

# Default parameters (can be overridden)
SYMBOL=${1:-BTCUSDT}
AMOUNT=${2:-100}
INTERVAL=${3:-5m}

echo "Configuration:"
echo "  Symbol: $SYMBOL"
echo "  Amount: $AMOUNT"
echo "  Interval: $INTERVAL"
echo ""
echo "Press Ctrl+C to stop the bot at any time"
echo ""
echo "Starting in 3 seconds..."
sleep 1
echo "2..."
sleep 1
echo "1..."
sleep 1
echo "Starting!"
echo ""

# Run the bot in test mode with debug output
python3 trader_bollinger.py \
  --symbol "$SYMBOL" \
  --amount "$AMOUNT" \
  --interval "$INTERVAL" \
  --test_mode \
  --debug

echo ""
echo "Bot stopped."
