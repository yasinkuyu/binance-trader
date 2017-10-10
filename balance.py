# -*- coding: UTF-8 -*-
# @yasinkuyu

from BinanceAPI import *

import config
 
class Binance:

    def __init__(self):
        self.client = BinanceAPI(config.api_key, config.api_secret)
    
    def balances(self):
        balances = self.client.get_account()
    
        for balance in balances['balances'] :
            if int(balance["locked"]) > 0 or int(balance["free"]) > 0 :
                print '%s: %s' % (balance['asset'], balance['free'])

    def orders(self, symbol, limit):
        orders = self.client.get_all_orders(symbol=symbol, limit=limit)

        print orders 
    
    def tickers(self):
       return self.client.get_all_tickers()

    def server_time(self):
       return self.client.get_server_time()

    def openorders(self):
       return self.client.get_open_orders()
 
try:
    
    m = Binance()
    #m.balances()
    m.orders('WTCBTC',10)

except BinanceAPIException as e:
    print e.status_code
    print e.message
     

