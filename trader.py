# -*- coding: UTF-8 -*-
# @yasinkuyu

# Define Python imports
import os
import sys
import time
import config
import argparse
import threading
import sqlite3

# Define Custom imports
from BinanceAPI import *

# Define Custom import vars
client = BinanceAPI(config.api_key, config.api_secret)
conn = sqlite3.connect('orders.db')

# Set parser
parser = argparse.ArgumentParser()
parser.add_argument("--quantity", type=int, help="Buy/Sell Quantity", default=200)
parser.add_argument("--symbol", type=str, help="Market Symbol (Ex: XVGBTC)", required=True)
parser.add_argument("--profit", type=float, help="Target Profit", default=1.3)
parser.add_argument("--stoploss", type=float, help="Target Stop-Loss % (If the price drops by 6%, sell market_price.)", default=0) # Not complated (Todo)

parser.add_argument("--increasing", type=float, help="Buy Price +Increasing (0.00000001)", default=0.00000001)
parser.add_argument("--decreasing", type=float, help="Sell Price -Decreasing (0.00000001)", default=0.00000001)

# Manually defined --orderid try to sell 
parser.add_argument("--orderid", type=int, help="Target Order Id (use balance.py)", default=0)

parser.add_argument("--wait_time", type=int, help="Wait Time (seconds)", default=1)
parser.add_argument("--test_mode", type=bool, help="Test Mode True/False", default=False)
parser.add_argument("--prints", type=bool, help="Scanning Profit Screen Print True/False", default=True)
parser.add_argument("--debug", type=bool, help="Debug True/False", default=True)
parser.add_argument("--loop", type=int, help="Loop (0 unlimited)", default=0)

option = parser.parse_args()

# Set globals (Todo)
global DEBUG_MODE
global TEST_MODE

# Define parser vars
DEBUG_MODE = option.debug
TEST_MODE = option.test_mode
PROFIT = option.profit
ORDER_ID = option.orderid
QUANTITY = option.quantity
WAIT_TIME = option.wait_time  # seconds
STOP_LOSS = option.stoploss # percent (When you drop 10%, sell panic.)

# Define static vars
WAIT_TIME_BUY_SELL = 5  # seconds
WAIT_TIME_STOP_LOSS = 20  # seconds
INVALID_ATTEMPTS_LIMIT = 40 # int
MAX_TRADE_SIZE = 10 # int

FEE = 0.0005

# Database
def write(data):
    """    
    Save order
    data = orderid,symbol,amount,price,side,quantity,profit
    Create a database connection
    """
    cur = conn.cursor()
    cur.executemany('''INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?, ?)''', map(tuple, data.tolist()))
    conn.commit()
    conn.close()
    
def read(orderid):
    """
    Query order info by id
    :param orderid: the buy/sell order id
    :return:
    """
    cur = conn.cursor()
    cur.execute("SELECT * FROM orders WHERE orderid = ?", (orderid,))
    return cur.fetchone()
    
def buy_limit(symbol, quantity, buyPrice):
    try:      
        order = client.buy_limit(symbol, quantity, buyPrice)
        
        if 'msg' in order:
            message(order['msg'])
    
        # Order created.
        orderId = order['orderId']
    
        # Database log
        #write([orderId, symbol, 0, buyPrice, "BUY", quantity, option.profit])
    
        print ('Order Id: %d' % orderId)

        return orderId

    except Exception as e:
        print (e)
        time.sleep(WAIT_TIME_BUY_SELL)
        return None

def sell_limit(symbol, quantity, orderId, sell_price, last_price):
    
    """
    The specified limit will try to sell until it reaches.
    If not successful, the order will be canceled.
    """
    
    invalidAttempts = 0

    while invalidAttempts < INVALID_ATTEMPTS_LIMIT:
                
        order = client.sell_limit(symbol, quantity, sell_price)  
                  
        if 'msg' in order:
            message(order['msg'])
       
        print ("Profit: %%%s. Buy: %.8f Sell: %.8f" % (PROFIT, buyPrice, sell_price))
                        
        sell_id = order['orderId']
    
        if sell_id != None:
            
            time.sleep(WAIT_TIME_BUY_SELL)
            
            """
            If all sales trials fail, 
            the grievance is stop-loss.
            """
            if STOP_LOSS > 0:
                
                stop_order = get_order(symbol, sell_id)
                
                stopprice =  calc(float(stop_order['price']))
                
                lossprice = stopprice - (stopprice * STOP_LOSS / 100)

                status = stop_order['status']
                
                # Order status
                if status == "NEW":
                    
                    if cancel_order(symbol, sell_id) == True:
                        
                        # Stop loss
                        if last_price <= lossprice: 
                            
                            sell = client.sell_market(symbol, quantity)  
                  
                            if 'msg' in sell:
                                message(sell['msg'])
                        
                            print ("Stop-loss, sell market, %s" % (lossprice))
                        
                            if sell == True:
                                break
                            else:
                                continue
                        
                            # Wait a while after the sale to the loss.
                            time.sleep (WAIT_TIME_STOP_LOSS)    
                            
                    else:
                        break
                elif status == "FILLED":
                    print("Order filled")
                    break
                elif status == "PARTIALLY_FILLED":
                    print("Order partially filled")
                    break
                else:
                    continue

            invalidAttempts = 0
            break
        else:
            invalidAttempts += 1
            continue

    if invalidAttempts != 0:
        cancel_order(symbol, orderId)
    
def check_buy(symbol, orderId, quantity):
    
    trading_size = 0
    time.sleep(WAIT_TIME_BUY_SELL)
    
    while trading_size < MAX_TRADE_SIZE:
        
        # Order info
        order = get_order(symbol, orderId)

        side  = order['side']
        price = float(order['price'])
        
        # Todo: Sell partial qty
        orig_qty = float(order['origQty']) 
        filled_qty = float(order['executedQty'])
        
        status = order['status']

        print ("Order(buy): %s id:%d, price: %.8f, orig_qty: %.8f" % (symbol, order['orderId'], price, orig_qty))
        
        if status == "NEW":
            
            if cancel_order(symbol, orderId) == True:
            
                buy = client.market_buy(symbol, quantity)
                  
                if 'msg' in buy:
                    message(buy['msg'])
                
                if buy == True:
                    break
                else:
                    trading_size += 1
                    continue
            else:
                break

        elif status == "FILLED":
            break
        elif status == "PARTIALLY_FILLED":
            break
        else:
            trading_size += 1
            continue
         
def cancel_order(symbol, orderId):
    try:
        order = client.cancel(symbol, orderId)
        
        if 'msg' in order:
            message(order['msg'])
       
        print ("Profit loss, called order, %s" % (orderId))
        return True
        
    except Exception as e:
        print (e)
        return False

def get_order_book(symbol):
    try:
        
        orders = client.get_orderbooks(symbol, 5)
        lastBid = float(orders['bids'][0][0]) #last buy price (bid)
        lastAsk = float(orders['asks'][0][0]) #last sell price (ask)
    
        return lastBid, lastAsk
    
    except Exception as e:
        print (e)
        return None, None

def get_order(symbol, orderId):
    try:
        order = client.query_order(symbol, orderId)

        if 'msg' in order:
            message(order['msg'])

        return order

    except Exception as e:
        print (e)
        return False

def get_order_status(symbol, orderId):
    try:
        order = client.query_order(symbol, orderId)
    
        if 'msg' in order:
            message(order['msg'])
        
        return order['status']
 
    except Exception as e:
        print (e)
        return None

def get_ticker(symbol):
    try:
        ticker = client.get_ticker(symbol)
        return float(ticker["lastPrice"])
    except Exception as e:
        print (e)

def analyze(symbol):
    # Todo: Analyze, best price position
    ticker = client.get_ticker(symbol)
    hight = float(ticker["hight"])
    low = float(ticker["low"])
    
    return False
    
def message(msg):
    print ("Error: " + msg)
    exit(1)
    
def calc(lastBid):
    return lastBid + (lastBid * PROFIT / 100)
    
def action(symbol):
        
    # Order amount
    quantity = option.quantity

    # Fetches the ticker price
    lastPrice = get_ticker(symbol)
    
    # Order book prices
    lastBid, lastAsk = get_order_book(symbol)
    
    # Target buy price, add little increase 
    buyPrice = lastBid + option.increasing
    
    # Target sell price, decrease little 
    sellPrice = lastAsk - option.decreasing 
    
    # Spread ( profit )
    profitableSellingPrice = calc(lastBid)
    earnTotal = profitableSellingPrice - buyPrice

    # Screen log
    if option.prints:
        print ('price:%.8f buyp:%.8f sellp:%.8f-bid:%.8f ask:%.8f' % (lastPrice, buyPrice, profitableSellingPrice, lastBid, lastAsk))

    #analyze = threading.Thread(target=analyze, args=(symbol,))
    #analyze.start()

    """
    Did profit get caught
    if ask price is greater than profit price, 
    buy with my buy price,
        
    or --orderid greater than zero
    """
    if lastAsk >= profitableSellingPrice or option.orderid > 0:  
        
        # Manually defined --orderid, try to sell ( use balance.py )
        if option.orderid > 0 :
            orderId = option.orderid
        else:
            orderId = buy_limit(symbol, quantity, buyPrice)
    
        # Order book prices
        newLastBid, newLastAsk = get_order_book(symbol)
        newSellPrice = newLastAsk - option.decreasing 
        
        if orderId is not None:
            
            """            
            If the order is complete, 
            try to sell it.
            """
        
            #Perform buy action
            sellAction = threading.Thread(target=sell_limit, args=(symbol, quantity, orderId, newSellPrice, lastPrice,))
            
            #Perform check/sell action
            checkAction = threading.Thread(target=check_buy, args=(symbol, orderId, quantity,))
            
            sellAction.start()
            checkAction.start()
             
def main():

    cycle = 0
    actions = []

    symbol = option.symbol

    print ("@yasinkuyu, 2017")
    print ("Auto Trading for Binance.com. --symbol: %s" % symbol)
        
    print ("trader.py --symbol %s --quantity %s --profit %s --wait_time %s --orderid %s \n" % (symbol, option.quantity, option.profit, option.wait_time, option.orderid))
    
    print ("%%%s profit scanning for %s" % (PROFIT, symbol))
    print ("... \n")
     
    while (cycle <= option.loop):
          
        startTime = time.time()
        
        actionTrader = threading.Thread(target=action, args=(symbol,))
        actions.append(actionTrader)
        actionTrader.start()
                 
        endTime = time.time()

        if endTime - startTime < WAIT_TIME:
            
            time.sleep(WAIT_TIME - (endTime - startTime))
            
            # 0 = Unlimited loop
            if option.loop > 0:       
                cycle = cycle + 1
                           
if __name__ == "__main__":
    main()