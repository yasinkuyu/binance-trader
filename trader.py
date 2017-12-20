# -*- coding: UTF-8 -*-
# @yasinkuyu

import sys
import time
import config

from BinanceAPI import *

# trader.py --quantity --symbol --profit --wait_time
# ex: trader.py 1 IOTABTC 1.3 1

#int(sys.argv[0]) #quantity
#sys.argv[1] #symbol
#sys.argv[2] #percentage of profit
#sys.argv[3] #wait_time

TEST_MODE = False

PROFIT = 1.3 #percentage of profit
ORDER_ID = None
TARGET_PRICE = 0
QUANTITY = 2
INCREASING = 0.00000001
TARGET_PROFITABLE_PRICE = None
WAIT_TIME = 3  # default 3 seconds

client = BinanceAPI(config.api_key, config.api_secret)

def buy_limit(symbol, quantity, buyPrice):
    global TEST_MODE
    
    if TEST_MODE:
        return "100000"
    
    ret = client.buy_limit(symbol, quantity, buyPrice)
    if 'msg' in ret:
        errexit(ret['msg'])

    orderId = ret['orderId']
    
    file = open("ORDER", "w") 
    file.write("{}\n".format([symbol, orderId, quantity, buyPrice]))
    
    print "******************"
    print 'Order Id: %d' % orderId

    return orderId

def sell_limit(symbol, quantity, orderId):
    global TEST_MODE
    global ORDER_ID
    global TARGET_PRICE
    global TARGET_PROFITABLE_PRICE
    
    ret = client.get_open_orders(symbol)
    if 'msg' in ret:
        errexit(ret['msg'])

    print "Orders"

    for order in ret:
        price = float(order['price'])
        origQty = float(order['origQty'])
        executedQty = float(order['executedQty'])

        if order['orderId'] == orderId:
            print "Order: %d: %lf\t%lf\t%lf" % (order['orderId'], price, origQty, executedQty)
     
            TARGET_PROFITABLE_PRICE = None
            ORDER_ID = None

            if not TEST_MODE:
                ret = client.sell_limit(symbol, quantity, TARGET_PRICE)
                print 'Sales were made at %s price.' % (TARGET_PRICE)
                print '---------------------------------------------'

                if 'msg' in ret:
                    errexit(ret['msg'])

                print ret
            else:
                print "Order Id: %s. The test order is complete. Price %s" % (orderId, TARGET_PRICE)
                
def cancel_order(symbol, orderId):
    global TEST_MODE
    
    if orderId is not None:

        if not TEST_MODE:
            ret = client.cancel(symbol, orderId)
            if 'msg' in ret:
                errexit(ret['msg'])

        print 'Order has been canceled.'

def check_order(symbol, orderId):

    ret = client.query_order(symbol, orderId)
    if 'msg' in ret:
        errexit(ret['msg'])

    #Canceled #Filled #Partial Fill
    if ret['status'] != "CANCELED":
        print "%s Order complated. Try sell..." % (orderId)
        return True
        
    print "%s Order is open..." % (orderId)
    return False
   
def get_ticker(symbol):
    ret = client.get_ticker(symbol)
    return float(ret["lastPrice"])

def errexit(msg):
    print("Error: " + msg)
    exit(1)
   
def action(symbol):
    
    global ORDER_ID
    global QUANTITY
    global TARGET_PRICE
    global TARGET_PROFITABLE_PRICE
    
    file = open("ORDER", "r") 
    #print file.read() 
    
    lastPrice = get_ticker(symbol)

    ret = client.get_orderbooks(symbol, 5)
    lastBid = float(ret['bids'][0][0])
    lastAsk = float(ret['asks'][0][0])
    
    btcPrice = get_ticker("BTCUSDT")
    buyPrice = lastBid + INCREASING
    sellPrice = lastAsk - INCREASING
    profitablePrice = buyPrice + (buyPrice * PROFIT / 100)

    earnTotal = sellPrice - buyPrice
    
    TARGET_PRICE = sellPrice

    if ORDER_ID is None:

        print 'price:%.8f buyp:%.8f sellp:%.8f-bid:%.8f ask:%.8f BTC:$%.1f' % (lastPrice, buyPrice, sellPrice, lastBid, lastAsk, btcPrice)

        # Did profit get caught
        if lastAsk >= profitablePrice:

            TARGET_PROFITABLE_PRICE = profitablePrice

            ORDER_ID = buy_limit(symbol, QUANTITY, buyPrice)

            print "Percentage of %s profit. Order created from %.8f. Profit: %.8f BTC" % (PROFIT, sellPrice, earnTotal)
            print "#####################"

        else:

            TARGET_PROFITABLE_PRICE = None
            
    else:
        
        # If the order is complete, try to sell it.
        if check_order(symbol, ORDER_ID):
            
            # Did profit get caught
            if lastAsk >= TARGET_PROFITABLE_PRICE:
 
                print "Target sell price: %.8f " % TARGET_PROFITABLE_PRICE 
                
                sell_limit(symbol, QUANTITY, ORDER_ID)
                
            #if the profit is lost, cancel order
            else:
                
                print "%s Cancel order3" % (ORDER_ID)
                
                cancel_order(symbol, ORDER_ID)
                
                #Reset order id
                ORDER_ID = None

def main():
    symbol = 'IOTABTC'

    print "@yasinkuyu, 2017"
    print "Auto Trading for Binance.com (Beta). Enter your symbol. Ex: %s" % symbol
    
    name = raw_input()

    if name != "":
        symbol = name
    
    print '%%%s profit scanning for %s' % (PROFIT, symbol)
    
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