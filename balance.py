#!/usr/bin/env python3
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

        print(balances['balances'][asset]['free'])

    def orders(self, symbol, limit):
        orders = self.client.get_open_orders(symbol, limit)
        print(orders)

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

    while True:
        m = Binance()

        print('\n')
        print('1 >> Print orders')
        print('2 >> Scan profits')
        print('3 >> List balances')
        print('4 >> Check balance')
        print('------------------')
        print('0 >> Exit')
        print('\nEnter option number:')

        option = input()

        if option=='1':
            print('Enter symbol: (i.e. XVGBTC)')

            symbol = input()

            # Orders
            print('%s Orders' % (symbol))
            m.orders(symbol, 10)

        elif option=='2':      
            print('Enter Asset (i.e. BTC, ETH, BNB)')

            asset = input()

            print('Profits scanning...')
            m.profits(asset)
            
        elif option=='3':      
            m.balances()
            
        elif option=='4':
            print('Enter asset: (i.e. BTC)')

            symbol = input()

            print('%s balance' % (symbol))

            m.balance(symbol)

        elif option=='0':
            break
        
        else:
            print('Option not reconigzed')


except Exception as e:
    print('Exception: %s' % e)
