# -*- coding: UTF-8 -*-
# @yasinkuyu

import os
import sys
import time
import config
import argparse

from BinanceAPI import *

parser = argparse.ArgumentParser()
parser.add_argument("--quantity", type=float, help="Buy/Sell Quantity", default=6)
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
WAIT_TIME_SELL = 4  # seconds

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
        message(ret['msg'])
    
    #Order created.
    orderId = ret['orderId']
    
    write("%s,%d,%lf,%lf" % (symbol, orderId, quantity, buyPrice))
    
    print ('Order Id: %d' % orderId)

    return orderId

def sell_limit(symbol, orderId, lastPrice, sell_price):
    global TEST_MODE

    if TEST_MODE:
        print ("Test sell price: %.8f " % sell_price)
        return 0

    # Get active order info
    order = get_order(symbol, orderId)
    
    # Sell price
    price = float(order['price'])
    
    filled_qty = float(order['executedQty'])
    
    # Todo: check filled or remaining qty.
    quantity = float(order['origQty']) #executedQty

    print ("Order(buy): %s %d: %.8f" % (symbol, order['orderId'], price))

    #Wait 4 seconds to be sold.
    time.sleep(WAIT_TIME_SELL)
    
    # Did profit get caught
    if sell_price >= lastPrice:

        if filled_qty > 0:
            ret = client.sell_limit(symbol, filled_qty, sell_price)
    
            print ("Sales were made at %.8f price." % (sell_price))

            if 'msg' in ret:
                message(ret['msg'])
    
            print ("symbol: %.8f executedQty: %.8f origQty: %.8f" % (ret['symbol'], ret['executedQty'], ret['origQty']))
        
        else:
            
            print ("Wait fill/partial fill. filledQty: %s " % (filled_qty))
        
    else:

        cancel_order(symbol, ORDER_ID)

        # Reset order id
        ORDER_ID = 0
    
        # Empty ORDER file
        write(" ")                        
                  
def cancel_order(symbol, orderId):

    ret = client.cancel(symbol, orderId)
    if 'msg' in ret:
        message(ret['msg'])

def get_order(symbol, orderId):

    ret = client.query_order(symbol, orderId)
    if 'msg' in ret:
        message(ret['msg'])
        return False

    # Canceled #Filled #Partial Fill
    if ret['status'] != "CANCELED":
        return ret
 
def get_ticker(symbol):
    ret = client.get_ticker(symbol)
    return float(ret["lastPrice"])

def message(msg):
    print ("Error: " + msg)
    exit(1)
    
def calc(lastBid):
    return lastBid + (lastBid * PROFIT / 100)
      
def action(symbol):
    
    global ORDER_ID
    
    # Order amount
    quantity = option.quantity

    lastPrice = get_ticker(symbol)
    btcPrice = get_ticker("BTCUSDT")
    
    ret = client.get_orderbooks(symbol, 5)
    lastBid = float(ret['bids'][0][0]) #last buy price (bid)
    lastAsk = float(ret['asks'][0][0]) #last sell price (ask)
    
    buyPrice = lastBid + option.increasing #target buy price
    sellPrice = lastAsk - option.decreasing #target sell price
    
    # Spread 
    profitableSellingPrice = calc(lastBid)
    earnTotal = profitableSellingPrice - buyPrice
     
    if ORDER_ID is 0:

        print ('price:%.8f buyp:%.8f sellp:%.8f-bid:%.8f ask:%.8f BTC:$%.1f' % (lastPrice, buyPrice, profitableSellingPrice, lastBid, lastAsk, btcPrice))

        # Did profit get caught
        if lastAsk >= profitableSellingPrice:
            
            try:

                ORDER_ID = buy_limit(symbol, quantity, buyPrice)

                print ("Percentage of %s profit. Order created from %.8f. Earn: %.8f satoshi" % (PROFIT, buyPrice, earnTotal))

            except:
                print ("... buy try again...")

    else:
        
        try:
 
            # Order information will be kept on file
            file = open("ORDER", "r") 
            data = file.read().split(',')
            
            profitableSellingPrice_file = calc(data[3]) #stored buyPrice
            
            # If the order is complete, try to sell it.
            ORDER_ID = sell_limit(symbol, ORDER_ID, lastPrice, profitableSellingPrice_file)

            print ("Profit is lost, order canceled %s" % (ORDER_ID))

        except:
            print ("... sell try again...")
        
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