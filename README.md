# Binance Trader (Beta)
@yasinkuyu - 2017

This is an experimental bot for auto trading the binance.com exchange.

![Screenshot](https://github.com/yasinkuyu/binance-trader/blob/master/screenshot.png)

## Configuration

1. Signup Binance ( Referral url: https://www.binance.com/?ref=10701111 )
2. Enable Two-factor Authentication    
3. Go API Center, https://www.binance.com/userCenter/createApi.html
4. Create New Key

        [✓] Read Info [✓] Enable Trading [X] Enable Withdrawals 
5. Rename config.sample.py to config.py
6. Get an API and Secret Key, insert into config.py

        API key for account access
        api_key = ''
        Secret key for account access
        api_secret = ''

        API Docs: https://www.binance.com/restapipub.html
7. Optional: run as an excutable application in Docker containers


## Requirements

    sudo easy_install -U requests
    or 
    sudo pip install requests
    
    Python 2.7
        import sys
        import time
        import config
        import argparse

## Usage

    python trader.py 
    
    With option parameters

    python trader.py --quantity 6 --symbol IOTABTC --profit 1.3 --wait_time 3 --orderid 0
    
    --quantity     Buy/Sell Quantity (default 6)
    --symbol       Market Symbol (default IOTABTC)
    --profit       Target Profit (default 1.3)
    --orderid      Target Order Id (default 0)
    --testmode     Test Mode True/False (default False)
    --wait_time    Wait Time (seconds) (default 3)
    --increasing   Buy Price Increasing  +(default 0.00000001)
    --decreasing   Sell Price Decreasing -(default 0.00000001)

    Symbol structure;
        XXXBTC  (Bitcoin)
        XXXETH  (Ethereum)
        XXXBNB  (Binance Coin)
        XXXUSDT (Tether)

    All binance symbols are supported.
    
    Every coin can be different in --profit and --quantity.
    Total must be at least 0.001 
    
    Variations;
        trader.py --symbol TBNBTC --quantity 50 --profit 3
        trader.py --symbol NEOBTC --quantity 3 --profit 1.1
        trader.py --symbol ETHUSDT --quantity 0.3 --profit 1.5
        ...
    
## Run in a Docker container

    docker build -t trader .

    docker run trader
 
## DISCLAIMER

    I am not responsible for anything done with this bot. 
    You use it at your own risk. 
    There are no warranties or guarantees expressed or implied. 
    You assume all responsibility and liability.
     
## License

    Code released under the MIT License.

## Contributing

    Fork this Repo
    Commit your changes (git commit -m 'Add some feature')
    Push to the changes (git push)
    Create a new Pull Request
    
    Thanks all for your contributions...
    
## Roadmap

    - Order tracking (list open orders)
    - Symbol check balance 
    - Find best sell price
    - MACD Indicator (buy/sell)
    - Stop-Loss Implementation
    - Maximum (open) order limit
    - Binance/Bittrex/HitBTC/Liqui Arbitrage  

---