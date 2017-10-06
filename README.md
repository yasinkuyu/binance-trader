# BinanceTrader 

Rename config.sample.py to config.py

Get an API and Secret Key, insert into coinfig.py

    https://www.binance.com/restapipub.html

## Install Python Binance
    https://github.com/sammchardy/python-binance

    pip install python-binance


https://github.com/sammchardy/python-binance/blob/master/binance/client.py

## Some error solutions:

NameError: global name 'BinanceAPIException' is not defined
    
    from binance.exceptions import BinanceAPIException

NameError: global name 'Client' is not defined

    Set path
    export PYTHONPATH="$PYTHONPATH:/Users/yasin/Desktop/binance-trader/binance"


    
    
    
    