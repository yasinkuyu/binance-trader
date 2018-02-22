#!/usr/bin/python2.7
# -*- coding: UTF-8 -*-
# @yasinkuyu

import sys

sys.path.insert(0, './app')

from BinanceAPI import BinanceAPI

import config

class Binance:

    def __init__(self):
        self.client = BinanceAPI(config.api_key, config.api_secret)

    def balances(self):
        balances = self.client.get_account()

        for balance in balances['balances']:
            if float(balance['locked']) > 0 or float(balance['free']) > 0:
                print('%s: %s' % (balance['asset'], balance['free']))

    def balance(self, asset="BTC"):
        balances = self.client.get_account()

        balances['balances'] = {item['asset']: item for item in balances['balances']}
        
        print balances['balances'][asset]['free']
                 
    def orders(self, symbol, limit):
        orders = self.client.get_open_orders(symbol, limit)
        print orders

    def tickers(self):
        return self.client.get_all_tickers()

    def server_time(self):
        return self.client.get_server_time()

    def openorders(self):
        return self.client.get_open_orders()
        
    def profits(self, asset='BTC'):
        
        coins = self.client.get_products()

        for coin in coins['data']:
            
            if coin['quoteAsset'] == asset:
                    
                orders = self.client.get_order_books(coin['symbol'], 5)
                lastBid = float(orders['bids'][0][0]) #last buy price (bid)
                lastAsk = float(orders['asks'][0][0]) #last sell price (ask)
    
                profit = (lastAsk - lastBid) /  lastBid * 100
            
                print('%.2f%% profit : %s (bid:%.8f-ask%.8f)' % (profit, coin['symbol'], lastBid, lastAsk))
            
try:

    m = Binance()

    print('1 -) Print orders')
    print('2 -) Scan profits')
    print('3 -) List balances')
    print('4 -) Check balance')
    print('Enter option number: Ex: 2')

    option = raw_input()
    
    if option is '1':
        
        print('Enter symbol: Ex: XVGBTC')
        
        symbol = raw_input()
        
        # Orders
        print('%s Orders' % (symbol))
        m.orders(symbol, 10)
    
    elif option is '3':
        m.balances()
    elif option is '4':
        
        print('Enter asset: Ex: BTC')
        
        symbol = raw_input()
        
        print('%s balance' % (symbol))
        
        m.balance(symbol)
    else:
        
        print('Enter Asset (Ex: BTC, ETC, BNB, USDT)')
        
        asset = raw_input()
        
        print 'Profits scanning...'
        m.profits(asset)

except 'BinanceAPIException' as e:
    print(e.status_code)
    print(e.message)