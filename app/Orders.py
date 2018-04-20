# -*- coding: UTF-8 -*-
# @yasinkuyu
import config 

from BinanceAPI import BinanceAPI
from Messages import Messages

# Define Custom import vars
client = BinanceAPI(config.api_key, config.api_secret)

class Orders():
 
    @staticmethod
    def buy_limit(symbol, quantity, buyPrice):

        order = client.buy_limit(symbol, quantity, buyPrice)

        if 'msg' in order:
            Messages.get(order['msg'])

        # Buy order created.
        return order['orderId']

    @staticmethod
    def sell_limit(symbol, quantity, sell_price):

        order = client.sell_limit(symbol, quantity, sell_price)  

        if 'msg' in order:
            Messages.get(order['msg'])

        return order

    @staticmethod
    def buy_market(symbol, quantity):

        order = client.buy_market(symbol, quantity)  

        if 'msg' in order:
            Messages.get(order['msg'])

        return order

    @staticmethod
    def sell_market(symbol, quantity):

        order = client.sell_market(symbol, quantity)  

        if 'msg' in order:
            Messages.get(order['msg'])

        return order

    @staticmethod
    def cancel_order(symbol, orderId):
        
        try:
            
            order = client.cancel(symbol, orderId)
            if 'msg' in order:
                Messages.get(order['msg'])
            
            print('Profit loss, called order, %s' % (orderId))
        
            return True
        
        except Exception as e:
            print('cancel_order Exception: %s' % e)
            return False

    @staticmethod
    def get_order_book(symbol):
        try:

            orders = client.get_order_books(symbol, 5)
            lastBid = float(orders['bids'][0][0]) #last buy price (bid)
            lastAsk = float(orders['asks'][0][0]) #last sell price (ask)
     
            return lastBid, lastAsk
    
        except Exception as e:
            print('get_order_book Exception: %s' % e)
            return 0, 0

    @staticmethod
    def get_order(symbol, orderId):
        try:

            order = client.query_order(symbol, orderId)

            if 'msg' in order:
                #import ipdb; ipdb.set_trace()
                Messages.get(order['msg']) # TODO
                return False

            return order

        except Exception as e:
            print('get_order Exception: %s' % e)
            return False
    
    @staticmethod
    def get_order_status(symbol, orderId):
        try:

            order = client.query_order(symbol, orderId)
    
            if 'msg' in order:
                Messages.get(order['msg'])
        
            return order['status']
 
        except Exception as e:
            print('get_order_status Exception: %s' % e)
            return None
    
    @staticmethod
    def get_ticker(symbol):
        try:        
    
            ticker = client.get_ticker(symbol)
 
            return float(ticker['lastPrice'])
        except Exception as e:
            print('Get Ticker Exeption: %s' % e)
    
    @staticmethod
    def get_info(symbol):
        try:        
    
            info = client.get_exchange_info()
            
            if symbol != "":
                return [market for market in info['symbols'] if market['symbol'] == symbol][0]
 
            return info
            
        except Exception as e:
            print('get_info Exception: %s' % e)