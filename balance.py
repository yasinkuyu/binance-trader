#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# @yasinkuyu

import sys

sys.path.insert(0, './app')

import time
import config
from datetime import timedelta, datetime
from BinanceAPI import BinanceAPI

class Binance:

    def __init__(self):
        self.client = BinanceAPI(config.api_key, config.api_secret)

    def balances(self):
        balances = self.client.get_account()
      
        for balance in balances['balances']:
            if float(balance['locked']) > 0 or float(balance['free']) > 0:
                print('%s: %s' % (balance['asset'], balance['free']))

    def balance(self, asset='BTC'):
        balances = self.client.get_account()
        balances['balances'] = {item['asset']: item for item in balances['balances']}
        print(balances['balances'][asset]['free'])

    def orders(self, symbol, limit):
        orders = self.client.get_open_orders(symbol, limit)
        print(orders)

    def tickers(self):
        
        return self.client.get_all_tickers()

    def server_status(self):
        systemT=int(time.time()*1000)           #timestamp when requested was launch
        serverT= self.client.get_server_time()  #timestamp when server replied
        lag=int(serverT['serverTime']-systemT)

        print('System timestamp: %d' % systemT)
        print('Server timestamp: %d' % serverT['serverTime'])
        print('Lag: %d' % lag)

        if lag>1000:
            print('\nNot good. Excessive lag (lag > 1000ms)')
        elif lag<0:
            print('\nNot good. System time ahead server time (lag < 0ms)')
        else:  
            print('\nGood (0ms > lag > 1000ms)')              
        return

    def openorders(self):
        
        return self.client.get_open_orders()

    def profits(self, asset='BTC'):
        coins = self.client.get_products()
        
        for coin in coins['data']:
            if coin['quoteAsset'] == asset:
                orders = self.client.get_order_books(coin['symbol'], 5)             
                if len(orders['bids'])>0 and len(orders['asks'])>0: 
                    lastBid = float(orders['bids'][0][0]) #last buy price (bid)
                    lastAsk = float(orders['asks'][0][0]) #last sell price (ask)
                    
                    if lastBid!=0: 
                        profit = (lastAsk - lastBid) /  lastBid * 100
                    else:
                        profit = 0
                    print('%6.2f%% profit : %s (bid: %.8f / ask: %.8f)' % (profit, coin['symbol'], lastBid, lastAsk))
                else:
                    print('---.--%% profit : %s (No bid/ask info retrieved)' % (coin['symbol']))

    def market_value(self, symbol, kline_size, dateS, dateF="" ):                 
        dateS=datetime.strptime(dateS, "%d/%m/%Y %H:%M:%S")
        
        if dateF!="":
            dateF=datetime.strptime(dateF, "%d/%m/%Y %H:%M:%S")
        else:
            dateF=dateS + timedelta(seconds=59)

        print('Retrieving values...\n')    
        klines = self.client.get_klines(symbol, kline_size, int(dateS.timestamp()*1000), int(dateF.timestamp()*1000))

        if len(klines)>0:
            for kline in klines:
                print('[%s] Open: %s High: %s Low: %s Close: %s' % (datetime.fromtimestamp(kline[0]/1000), kline[1], kline[2], kline[3], kline[4]))

        return
    
try:

    while True:
        m = Binance()

        print('\n')
        print('1 >> Print orders')
        print('2 >> Scan profits')
        print('3 >> List balances')
        print('4 >> Check balance')
        print('-----------------------------')
        print('5 >> Market value (specific)')
        print('6 >> Market value (range)')
        print('-----------------------------')
        print('7 >> Server status')
        print('-----------------------------')
        print('0 >> Exit')
        print('\nEnter option number:')

        option = input()

        print('\n')

        if option=='1':
            print('Enter pair: (i.e. XVGBTC)')
            symbol = input()
            print('%s Orders' % (symbol))
            
            m.orders(symbol, 10)

        elif option=='2':      
            print('Enter asset (i.e. BTC, ETH, BNB)')
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

        elif option=='5':
            print('Enter pair: (i.e. BTCUSDT)')
            symbol = input()
            print('Enter date/time: (dd/mm/yyyy hh:mm:ss)')
            dateS = input()

            klines=m.market_value(symbol,"1m", dateS)

        elif option=='6':
            print('Enter pair: (i.e. BTCUSDT)')
            symbol = input()
            print('Enter start date/time: (dd/mm/yyyy hh:mm:ss)')
            dateS = input()
            print('Enter end date/time: (dd/mm/yyyy hh:mm:ss)')
            dateF = input()
            print('Enter interval as in exchange (i.e. 5m, 1d):')
            interval = input()

            klines=m.market_value(symbol, interval, dateS, dateF)

        elif option=='7':
            lag=m.server_status()

        elif option=='0':
            break
        
        else:
            print('Option not reconigzed')


except Exception as e:
    print('Exception: %s' % e)
