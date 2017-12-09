# -*- coding: UTF-8 -*-
# @yasinkuyu

import time
import config
from BinanceAPI import *

TEST_MODE = False

PROFIT = 1.3 #percentage of profit
ORDER_ID = None
TARGET_PRICE = 0
QUANTITY = 0.1
INCREASING = 0.00000001
TARGET_PROFIT_PRICE = None
WAIT_TIME = 1  # seconds

client = BinanceAPI(config.api_key, config.api_secret)

def errexit(msg):
    print("Error: " + msg)
    exit(1)

def lastPrice(symbol):
    ret = client.get_ticker(symbol)
    if 'msg' in ret:
        errexit(ret['msg'])
    
    return float(ret["lastPrice"])

def orderbooks(symbol):
    ret = client.get_orderbooks(symbol, 5)
    if 'msg' in ret:
        errexit(ret['msg'])

    print 'Bids:'
    for (price, volume, dummy) in ret['bids']:
        print '%lf\t%lf' % (float(price), float(volume))

    print 'Asks: '
    for (price, volume, dummy) in ret['asks']:
        print '%lf\t%lf' % (float(price), float(volume))
    print ''
    
def balances():
    balances = client.get_account()

    for balance in balances['balances'] :
        if int(balance["locked"]) > 0 or int(balance["free"]) > 0 :
            print '%s: %s' % (balance['asset'], balance['free'])

def orders(symbol, limit):
    orders = client.get_all_orders(symbol=symbol, limit=limit)
    print orders 

def tickers():
   return client.get_all_tickers()

def server_time():
   return client.get_server_time()

def openorders(symbol):
   return client.get_open_orders(symbol)
 
def checkorder(symbol, orderId):
    ret = client.query_order(symbol, orderId)
    if 'msg' in ret:
        errexit(ret['msg'])

    return ret['status']
  
def action(symbol):
    global ORDER_ID
    global TARGET_PRICE
    global TARGET_PROFIT_PRICE
    
    ret = client.get_ticker(symbol)
    lastPrice = float(ret["lastPrice"])

    ret = client.get_orderbooks(symbol, 5)
    lastBid = float(ret['bids'][0][0])
    lastAsk = float(ret['asks'][0][0])
    
    buyPrice = lastBid + INCREASING
    sellPrice = lastAsk - INCREASING
    checkProfitPrice = buyPrice + (buyPrice * PROFIT / 100)

    earnTotal = sellPrice - buyPrice

    TARGET_PRICE = sellPrice

    if ORDER_ID is None:

        #orderStatus = checkorder(symbol, ORDER_ID) --> illegal karakter hatası

        print 'price:%.8f buyp:%.8f sellp:%.8f (bid:%.8f ask:%.8f) ' % (lastPrice, buyPrice, sellPrice, lastBid, lastAsk)

        if lastAsk >= checkProfitPrice:

            TARGET_PROFIT_PRICE = checkProfitPrice

            if not TEST_MODE:
                ret = client.buy_limit(symbol, QUANTITY, buyPrice)
                if 'msg' in ret:
                    errexit(ret['msg'])

                ORDER_ID = ret['orderId']

                print "******************"
                print 'Order Id: %d' % ORDER_ID

            else:
                ORDER_ID = "100000"
        
            print "Percentage of %s profit. Order created from %.8f. Profit: %.8f BTC" % (PROFIT, sellPrice, earnTotal)
            print "#####################"

        else:

            TARGET_PROFIT_PRICE = None

            if ORDER_ID is not None:

                if not TEST_MODE:
                    ret = client.cancel(symbol, ORDER_ID)
                    if 'msg' in ret:
                        errexit(ret['msg'])

                print 'Order has been canceled.'

    else:
        print "Target sell price: %.8f " % TARGET_PROFIT_PRICE 

        if lastAsk >= TARGET_PROFIT_PRICE:

            ret = client.get_open_orders(symbol)
            if 'msg' in ret:
                errexit(ret['msg'])

            print "Orders"

            for order in ret:
                price = float(order['price'])
                origQty = float(order['origQty'])
                executedQty = float(order['executedQty'])

                if order['orderId'] == ORDER_ID and TEST_MODE:
    
                    if not TEST_MODE:
                        print "Order: %d: %lf\t%lf\t%lf" % (order['orderId'], price, origQty, executedQty)
                    else:
                        print "Order: 0000"
        
                    TARGET_PROFIT_PRICE = None
                    ORDER_ID = None
    
                    if not TEST_MODE:
                        ret = client.sell_limit(symbol, QUANTITY, TARGET_PRICE)
                        print 'Sales were made at %s price.' % (TARGET_PRICE)
                        print '---------------------------------------------'
        
                        if 'msg' in ret:
                            errexit(ret['msg'])

                        print ret
                    else:
                        print "Order Id: %s. The test order is complete. Price %s" % (ORDER_ID, TARGET_PRICE)

      
def main():
    symbol = 'LINKBTC'

    print "@yasinkuyu, 2017"
    print "Auto Trading for Binance.com (Beta). Input your symbol. Ex: %s" % symbol
    
    name = raw_input()

    if name != "":
        symbol = name
    
    print 'Scanning for %%%s %s profit.' % (PROFIT, symbol)

    if TEST_MODE:
        print "Test mode active"
    
    while True:
        
        startTime = time.time()
        action(symbol)
        endTime = time.time()

        if endTime - startTime < WAIT_TIME:
            time.sleep(WAIT_TIME - (endTime - startTime))
                   
if __name__ == "__main__":
    main()