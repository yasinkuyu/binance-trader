# -*- coding: UTF-8 -*-
# @yasinkuyu

import os
import sys
import time
import config
import argparse

from BinanceAPI import *

parser = argparse.ArgumentParser()
parser.add_argument("--quantity", type=int, help="Buy/Sell Quantity", default=6)
parser.add_argument("--symbol", type=str, help="Market Symbol (Ex: IOTABTC)", default='IOTABTC')
parser.add_argument("--profit", type=float, help="Target Profit", default=1.3)
parser.add_argument("--orderid", type=int, help="Target Order Id", default=0)
parser.add_argument("--testmode", type=bool, help="Test Mode True/False", default=False)
parser.add_argument("--wait_time", type=int, help="Wait Time (seconds)", default=3)
parser.add_argument("--increasing", type=float, help="Buy Price +Increasing (0.00000001)", default=0.00000001)
parser.add_argument("--decreasing", type=float, help="Sell Price -Decreasing (0.00000001)", default=0.00000001)

option = parser.parse_args()

TEST_MODE = option.testmode

PROFIT = option.profit
ORDER_ID = option.orderid
QUANTITY = option.quantity
WAIT_TIME = option.wait_time  # seconds
TARGET_PRICE = 0
TARGET_PROFITABLE_PRICE = None

client = BinanceAPI(config.api_key, config.api_secret)

def write(data):
    file = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ORDER'), 'w')
    file.write(data)
    
def buy_limit(symbol, quantity, buyPrice):
    global TEST_MODE
    
    if TEST_MODE:
        return "100000"
    
    ret = client.buy_limit(symbol, quantity, buyPrice)
    if 'msg' in ret:
        errexit(ret['msg'])

    orderId = ret['orderId']
    
    write("{}\n".format([symbol, orderId, quantity, buyPrice]))
    
    print ("******************")
    print ('Order Id: %d' % orderId)

    return orderId

def sell_limit(symbol, quantity, orderId):
    global TEST_MODE
    global ORDER_ID
    global TARGET_PRICE
    global TARGET_PROFITABLE_PRICE
    
    ret = client.get_open_orders(symbol)
    if 'msg' in ret:
        errexit(ret['msg'])

    print ("Orders")

    for order in ret:
        price = float(order['price'])
        origQty = float(order['origQty'])
        executedQty = float(order['executedQty'])

        if order['orderId'] == orderId:
            print ("Order: %d: %lf\t%lf\t%lf" % (order['orderId'], price, origQty, executedQty))
     
            TARGET_PROFITABLE_PRICE = None
            ORDER_ID = 0

            if not TEST_MODE:
                ret = client.sell_limit(symbol, quantity, TARGET_PRICE)
                print ('Sales were made at %s price.' % (TARGET_PRICE))
                print ('---------------------------------------------')

                if 'msg' in ret:
                    errexit(ret['msg'])

                print (ret)
            else:
                print ("Order Id: %s. The test order is complete. Price %s" % (orderId, TARGET_PRICE))
                
def cancel_order(symbol, orderId):
    global TEST_MODE
    
    if orderId is not None:

        if not TEST_MODE:
            ret = client.cancel(symbol, orderId)
            if 'msg' in ret:
                errexit(ret['msg'])

        print ('Order has been canceled.')

def check_order(symbol, orderId):

    ret = client.query_order(symbol, orderId)
    if 'msg' in ret:
        errexit(ret['msg'])

    #Canceled #Filled #Partial Fill
    if ret['status'] != "CANCELED":
        print ("%s Order complated. Try sell..." % (orderId))
        return True
        
    print ("%s Order is open..." % (orderId))
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
    lastBid = float(ret['bids'][0][0]) #last buy price
    lastAsk = float(ret['asks'][0][0]) #last sell price
    
    btcPrice = get_ticker("BTCUSDT")
    buyPrice = lastBid + option.increasing #target buy price
    sellPrice = lastAsk - option.decreasing #target sell price
    profitablePrice = buyPrice + (buyPrice * PROFIT / 100) #spread

    earnTotal = sellPrice - buyPrice
    
    TARGET_PRICE = sellPrice

    if ORDER_ID is 0:

        print ('price:%.8f buyp:%.8f sellp:%.8f-bid:%.8f ask:%.8f BTC:$%.1f' % (lastPrice, buyPrice, sellPrice, lastBid, lastAsk, btcPrice))

        # Did profit get caught
        if lastAsk >= profitablePrice:

            TARGET_PROFITABLE_PRICE = profitablePrice

            ORDER_ID = buy_limit(symbol, QUANTITY, buyPrice)

            print ("Percentage of %s profit. Order created from %.8f. Profit: %.8f BTC" % (PROFIT, sellPrice, earnTotal))
            print ("#####################")

        else:

            TARGET_PROFITABLE_PRICE = None
            
    else:
        
        # If the order is complete, try to sell it.
        if check_order(symbol, ORDER_ID):
            
            # Did profit get caught
            if lastAsk >= TARGET_PROFITABLE_PRICE:
 
                print ("Target sell price: %.8f " % TARGET_PROFITABLE_PRICE)
                
                sell_limit(symbol, QUANTITY, ORDER_ID)
                
            #if the profit is lost, cancel order
            else:
                
                print ("%s Cancel order" % (ORDER_ID))
                
                cancel_order(symbol, ORDER_ID)
                
                # Reset order
                ORDER_ID = None
                #empty ORDER file
                write(" ") 

def main():
   
    symbol = option.symbol

    print ("@yasinkuyu, 2017")
    print ("Auto Trading for Binance.com (Beta). Enter your symbol. Ex: %s" % symbol)
    
    name = raw_input()
        
    if name != "":
        symbol = name
    
    print ("trader.py --quantity %s --symbol %s --profit %s --wait_time %s --orderid %s \n" % (option.quantity, symbol, option.profit, option.wait_time, option.orderid))
    
    print ('%%%s profit scanning for %s \n' % (PROFIT, symbol))
    
    if TEST_MODE:
        print ("Test mode active")
    
    while True:
        
        startTime = time.time()
        action(symbol)
        endTime = time.time()

        if endTime - startTime < WAIT_TIME:
            time.sleep(WAIT_TIME - (endTime - startTime))
                   
if __name__ == "__main__":
    main()