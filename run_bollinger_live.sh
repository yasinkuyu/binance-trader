#!/bin/bash
# Live Trading Script for Bollinger Bands Trading Bot
# USE WITH CAUTION - This script trades with real money!

echo "=========================================="
echo "⚠️  BOLLINGER BANDS BOT - LIVE TRADING ⚠️"
echo "=========================================="
echo ""
echo -e "\033[1;31mWARNING: This will trade with REAL money!\033[0m"
echo ""
echo "Have you:"
echo "  [✓] Tested in --test_mode for at least 1 week?"
echo "  [✓] Configured your API keys in app/config.py?"
echo "  [✓] Understood all parameters and risks?"
echo "  [✓] Started with a small amount you can afford to lose?"
echo ""
read -p "Type 'YES' to continue with live trading: " CONFIRM

if [ "$CONFIRM" != "YES" ]; then
    echo "Exiting. No trades will be made."
    exit 0
fi

echo ""
echo "Select trading configuration:"
echo ""
echo "1) Conservative (Low risk, high confidence)"
echo "2) Balanced (Recommended for most users)"
echo "3) Aggressive (Higher risk/reward)"
echo "4) Custom (specify parameters)"
echo ""
read -p "Enter choice (1-4): " CHOICE

# Default symbol and amount
read -p "Enter symbol (e.g., BTCUSDT): " SYMBOL
read -p "Enter amount to trade: " AMOUNT

case $CHOICE in
    1)
        echo ""
        echo "Starting CONSERVATIVE mode..."
        python3 trader_bollinger.py \
          --symbol "$SYMBOL" \
          --amount "$AMOUNT" \
          --interval 15m \
          --rsi_oversold 25 \
          --rsi_overbought 75 \
          --min_confidence 70 \
          --risk_per_trade 1.0 \
          --bb_stddev 2.5
        ;;
    2)
        echo ""
        echo "Starting BALANCED mode..."
        python3 trader_bollinger.py \
          --symbol "$SYMBOL" \
          --amount "$AMOUNT" \
          --interval 5m \
          --min_confidence 50 \
          --risk_per_trade 2.0
        ;;
    3)
        echo ""
        echo "Starting AGGRESSIVE mode..."
        python3 trader_bollinger.py \
          --symbol "$SYMBOL" \
          --amount "$AMOUNT" \
          --interval 3m \
          --rsi_oversold 35 \
          --rsi_overbought 65 \
          --min_confidence 40 \
          --risk_per_trade 3.0 \
          --bb_stddev 1.5
        ;;
    4)
        echo ""
        read -p "Enter interval (e.g., 5m): " INTERVAL
        read -p "Enter min confidence (50): " CONFIDENCE
        CONFIDENCE=${CONFIDENCE:-50}
        read -p "Enter risk per trade % (2.0): " RISK
        RISK=${RISK:-2.0}

        echo ""
        echo "Starting CUSTOM mode..."
        python3 trader_bollinger.py \
          --symbol "$SYMBOL" \
          --amount "$AMOUNT" \
          --interval "$INTERVAL" \
          --min_confidence "$CONFIDENCE" \
          --risk_per_trade "$RISK"
        ;;
    *)
        echo "Invalid choice. Exiting."
        exit 1
        ;;
esac

echo ""
echo "Bot stopped."
