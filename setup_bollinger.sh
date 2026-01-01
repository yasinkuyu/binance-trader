#!/bin/bash
# Bollinger Bands Trading Bot - Setup Script
# This script sets up the environment for the Bollinger Bands trading bot

set -e  # Exit on any error

echo "=========================================="
echo "Bollinger Bands Trading Bot - Setup"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python installation
echo -n "Checking Python installation... "
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    echo -e "${GREEN}Found Python $PYTHON_VERSION${NC}"
else
    echo -e "${RED}FAILED${NC}"
    echo "Python 3 is not installed. Please install Python 3.6 or higher."
    exit 1
fi

# Check pip installation
echo -n "Checking pip installation... "
if command -v pip3 &> /dev/null; then
    PIP_VERSION=$(pip3 --version | cut -d' ' -f2)
    echo -e "${GREEN}Found pip $PIP_VERSION${NC}"
else
    echo -e "${RED}FAILED${NC}"
    echo "pip3 is not installed. Please install pip3."
    exit 1
fi

# Install dependencies
echo ""
echo "Installing dependencies..."
pip3 install -r requirements.txt

if [ $? -eq 0 ]; then
    echo -e "${GREEN}Dependencies installed successfully${NC}"
else
    echo -e "${RED}Failed to install dependencies${NC}"
    exit 1
fi

# Setup config file
echo ""
echo "Setting up configuration..."
if [ ! -f "app/config.py" ]; then
    cp app/config.sample.py app/config.py
    echo -e "${YELLOW}Created app/config.py from template${NC}"
    echo -e "${YELLOW}⚠️  IMPORTANT: Edit app/config.py and add your Binance API keys${NC}"
else
    echo -e "${GREEN}Config file already exists${NC}"
fi

# Setup database
echo ""
echo "Setting up database..."
if [ ! -f "db/orders.db" ]; then
    if [ -f "db/orders.sample.db" ]; then
        cp db/orders.sample.db db/orders.db
        echo -e "${GREEN}Created orders database${NC}"
    else
        touch db/orders.db
        echo -e "${GREEN}Created empty orders database${NC}"
    fi
else
    echo -e "${GREEN}Database already exists${NC}"
fi

# Make scripts executable
echo ""
echo "Making scripts executable..."
chmod +x trader_bollinger.py
chmod +x setup_bollinger.sh
chmod +x run_bollinger_test.sh 2>/dev/null || true
echo -e "${GREEN}Scripts are now executable${NC}"

# Create logs directory
echo ""
echo "Setting up logs directory..."
mkdir -p logs
echo -e "${GREEN}Logs directory created${NC}"

echo ""
echo "=========================================="
echo -e "${GREEN}Setup Complete!${NC}"
echo "=========================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Configure your Binance API keys:"
echo "   nano app/config.py"
echo ""
echo "2. Test the bot (no real trades):"
echo "   python3 trader_bollinger.py --symbol BTCUSDT --amount 100 --test_mode"
echo ""
echo "3. Read the documentation:"
echo "   cat BOLLINGER_README.md"
echo ""
echo "4. When ready, start live trading:"
echo "   python3 trader_bollinger.py --symbol BTCUSDT --amount 100"
echo ""
echo -e "${YELLOW}⚠️  Remember: Always test in --test_mode first!${NC}"
echo ""
