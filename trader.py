# -*- coding: UTF-8 -*-
# @yasinkuyu

from BinanceAPI import *

import config

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


symbol = 'LINKBTC'

print "The crypto money symbol. Sample: %s" % symbol
name = raw_input()

if name != "":
    symbol = name
    
profit = 1.3 #percentage of profit
orderId = None
targetPrice = 0
quantity = 0.1
testMode = True
increasing = 0.00000001

targetProfitPrice = None
print '%%%s started to profit for %s' % (profit, symbol)

if testMode:
    print "Test mode active"
    
while True:

    ret = client.get_ticker(symbol)
    lastPrice = float(ret["lastPrice"])

    ret = client.get_orderbooks(symbol, 5)
    lastBid = float(ret['bids'][0][0])
    lastAsk = float(ret['asks'][0][0])

    buyPrice = lastBid + increasing
    sellPrice = lastAsk - increasing
    checkProfitPrice = buyPrice + (buyPrice * profit / 100)
    
    earnTotal = sellPrice - buyPrice
 
    targetPrice = sellPrice

    if orderId is None:
        
        #orderStatus = checkorder(symbol, orderId) --> illegal karakter hatası
        
        print 'price:%.8f buyp:%.8f sellp:%.8f (bid:%.8f ask:%.8f) ' % (lastPrice, buyPrice, sellPrice, lastBid, lastAsk)

        if lastAsk >= checkProfitPrice:
            
            targetProfitPrice = checkProfitPrice
            
            if not testMode:
                ret = client.buy_limit(symbol, quantity, buyPrice)
                if 'msg' in ret:
                    errexit(ret['msg'])

                orderId = ret['orderId']
            
                print "******************"
                print 'Order Id: %d' % orderId
                
            else:
                orderId = "100000"
                        
            print "Percentage of %s profit. Order created from %.8f. Profit: %.8f BTC" % (profit, sellPrice, earnTotal)
            print "#####################"
            
        else:
            
            targetProfitPrice = None
            
            if orderId is not None:
                
                if not testMode:
                    ret = client.cancel(symbol, orderId)
                    if 'msg' in ret:
                        errexit(ret['msg'])

                print 'Order has been canceled.'
                
    else:
        print "Target sell price: %.8f " % targetProfitPrice 
        
        if lastAsk >= targetProfitPrice:
            
            ret = client.get_open_orders(symbol)
            if 'msg' in ret:
                errexit(ret['msg'])

            print "Orders"
            
            for order in ret:
                price = float(order['price'])
                origQty = float(order['origQty'])
                executedQty = float(order['executedQty'])
                
                if order['orderId'] == orderId and testMode:
                    
                    if not testMode:
                        print "Order: %d: %lf\t%lf\t%lf" % (order['orderId'], price, origQty, executedQty)
                    else:
                        print "Order: 0000"
                        
                    targetProfitPrice = None
                    orderId = None
                    
                    if not testMode:
                        ret = client.sell_limit(symbol, quantity, targetPrice)
                        print 'Sales were made at %s price.' % (targetPrice)
                        print '---------------------------------------------'
                        
                        if 'msg' in ret:
                            errexit(ret['msg'])

                        print ret
                    else:
                        print "Order Id: %s. The test order is complete. Price %s" % (orderId, targetPrice)
                    
                        
        