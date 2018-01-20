# Binance Trader (RC 1)

This is an experimental bot for auto trading the binance.com exchange. [@yasinkuyu](https://twitter.com/yasinkuyu)

![Screenshot](https://github.com/yasinkuyu/binance-trader/blob/master/img/screenshot.png)

## Configuration

1. Signup Binance ( Referral url: https://www.binance.com/?ref=10701111 )
2. Enable Two-factor Authentication    
3. Go API Center, https://www.binance.com/userCenter/createApi.html
4. Create New Key

        [✓] Read Info [✓] Enable Trading [X] Enable Withdrawals 
5. Rename config.sample.py to config.py / orders.sample.db to orders.db
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
        import os
        import sys
        import time
        import config
        import argparse
        import threading
        import sqlite3

## Usage

    python trader.py --symbol XVGBTC
    
    Example parameters
    
    # Profit mode (default)
    python trader.py --symbol XVGBTC --quantity 200 --profit 1.3
    or by amount
    python trader.py --symbol XVGBTC --amount 0.0022 --profit 3
    
    # Range mode
    python trader.py --symbol XVGBTC --mode range --quantity 260 --buyprice 0.00000780 --sellprice 0.00000790
    or by amount
    python trader.py --symbol XVGBTC --mode range --amount 0.0022 --buyprice 0.00000780 --sellprice 0.00000790
    
    --quantity     Buy/Sell Quantity (default 0)
    --amount       Buy/Sell Amount (default 0.0022)
    --symbol       Market Symbol ex XVGBTC or TRXETH
    --profit       Target Profit (default 1.3) *Percentage
    --stoploss     Decrease sell price at loss (default 1) *Percentage
    --orderid      Target Order Id (default 0)
    --wait_time    Wait Time (seconds) (default 0.7)
    --increasing   Buy Price Increasing  +(default 0.2) *Percentage
    --decreasing   Sell Price Decreasing -(default 0.2) *Percentage
    --prints       Scanning Profit Screen Print (default True)
    --loop         Loop (default 0 unlimited)
    
    --mode         Working modes profit or range (default profit)
                   profit: Find defined profit, buy and sell. (Ex: 1.3% profit)
                   range: Between target two price, buy and sell. (Ex: <= 0.00000780 buy - >= 0.00000790 sell )
    --buyprice     Buy price (Ex: 0.00000780)
    --sellprice    Buy price (Ex: 0.00000790)

    Symbol structure;
        XXXBTC  (Bitcoin)
        XXXETH  (Ethereum)
        XXXBNB  (Binance Coin)
        XXXUSDT (Tether)

    All binance symbols are supported.
    
    Every coin can be different in --profit and --quantity.
    Total must be at least 0.002 
    
    Variations;
        trader.py --symbol TBNBTC --quantity 50 --profit 3
        trader.py --symbol NEOBTC --amount 0.1 --profit 1.1
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
     
## Contributing

    Fork this Repo
    Commit your changes (git commit -m 'Add some feature')
    Push to the changes (git push)
    Create a new Pull Request
    
    Thanks all for your contributions...
    
## Failure

    Filter failure: MIN_NOTIONAL
    https://support.binance.com/hc/en-us/articles/115000594711-Trading-Rule

    Filter failure: PRICE_FILTER
    https://github.com/binance-exchange/binance-official-api-docs/blob/master/rest-api.md
    
    Timestamp for this request was 1000ms ahead of the server's time.
    https://github.com/yasinkuyu/binance-trader/issues/63#issuecomment-355857901
    
## Roadmap

    - MACD indicator (buy/sell)
    - Stop-Loss implementation
    - Working modes
      - profit: Find defined profit, buy and sell. (Ex: 1.3% profit)
      - range:  Between target two price, buy and sell. (Ex: <= 0.00100 buy - >= 0.00150 sell )
    - Binance/Bittrex/HitBTC Arbitrage  
    
    ...
    
    - October 7, 2017 Beta
    - January 6, 2018 RC
    - January 15, 2018 RC 1
     
## License

    Code released under the MIT License.

#### Tip Box
[Yasin](http://yasinkuyu.net/wallet) 

#### WeSpeakCrypto

    BTC wallet: 182Ew6JK9Mspw4BszdBP7RgpdWf6STe46G
    LTC wallet: LXgNmMPied4AiGKAsE1kY2M9BRaV3yxDC1
    ETH wallet: 0xed8100b70e15d9fcd53f1d989c67775bf55e4475

---