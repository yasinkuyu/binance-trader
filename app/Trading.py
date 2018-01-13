# -*- coding: UTF-8 -*-
# @yasinkuyu

# Define Python imports
import os
import sys
import time
import config 
import threading
import fixpath

# Define Custom imports
from Database import Database
from Orders import Orders
from colorama import init, Fore, Back, Style

init(autoreset=True)

class Trading():
    
    # Define trade vars  
    order_id = 0
    order_data = None
    
    buy_filled = True
    sell_filled = True
    
    buy_filled_qty = 0
    sell_filled_qty = 0
    
    # percent (When you drop 10%, sell panic.)
    stop_loss = 0
    
    # Buy/Sell qty
    quantity = 0
    
    # Define static vars
    WAIT_TIME_BUY_SELL = 5 # seconds
    WAIT_TIME_STOP_LOSS = 20 # seconds
    INVALID_ATTEMPTS_LIMIT = 20 # int
    MAX_TRADE_SIZE = 10 # int
    
    def __init__(self, option):
                
        # Get argument parse options
        self.option = option
        
        # Define parser vars
        self.order_id = self.option.orderid
        self.quantity = self.option.quantity
        self.wait_time = self.option.wait_time
        self.stop_loss = self.option.stoploss  
    
    def buy(self, symbol, quantity, buyPrice):
        
        try: 
                
            # Create order
            orderId = Orders.buy_limit(symbol, quantity, buyPrice)
                
            # Database log
            Database.write([orderId, symbol, 0, buyPrice, 'BUY', quantity, self.option.profit])
                            
            print (Fore.GREEN + "'Order Id: '+ Fore.RESET' %d' % orderId")
        
            return orderId

        except Exception as e:
            print ('bl: %s' % (e))
            time.sleep(self.WAIT_TIME_BUY_SELL)
            return None

    def sell(self, symbol, quantity, orderId, sell_price, last_price):
        
        '''
        The specified limit will try to sell until it reaches.
        If not successful, the order will be canceled.

        check_order = Orders.get_order(symbol, orderId)

        if check_order['status'] == 'FILLED':

            self.buy_filled_qty = float(order['executedQty'])

            break

        '''

        invalidAttempts = 0
         
        while invalidAttempts < self.INVALID_ATTEMPTS_LIMIT:
            
            sell_order = Orders.sell_limit(symbol, quantity, sell_price)  
              
            print (Fore.YELLOW+ "'Order (Filled) Id: ' + Fore.RESET +'%d' % orderId")
            print (Fore.YELLOW + 'LastPrice : %.8f' % last_price)
            print (Fore.GREEN + 'Profit: %%%s. Buy price: %.8f Sell price: %.8f' % (self.option.profit, float(sell_order['price']), sell_price))
                        
            sell_id = sell_order['orderId']
        
            if sell_order['status'] == 'FILLED':
                break
        
            if sell_id != None:
            
                time.sleep(self.WAIT_TIME_BUY_SELL)
            
                '''
                If all sales trials fail, 
                the grievance is stop-loss.
                '''
                if self.stop_loss > 0:
                                    
                    if self.stop(symbol, quantity, sell_id):
                        break
                    else:
                        continue

                invalidAttempts = 0
                break
            else:
                invalidAttempts += 1
                continue

        if invalidAttempts != 0:
            Orders.cancel_order(symbol, orderId)
            self.order_id = 0
            self.order_data = None

    def stop(symbol, quantity, sell_id):
    
        stop_order = Orders.get_order(symbol, sell_id)
    
        stopprice =  self.calc(float(stop_order['price']))
    
        lossprice = stopprice - (stopprice * self.stop_loss / 100)

        status = stop_order['status']
    
        # Order status
        if status == 'NEW':
            
            cancel = Orders.cancel_order(symbol, sell_id)
            
            if cancel:
            
                # Stop loss
                if last_price <= lossprice: 
                
                    sello = Orders.sell_market(symbol, quantity)  
       
                    print ('Stop-loss, sell market, %s' % (lossprice))
            
                    self.order_id = sello['orderId']
                    self.order_data = sello
                    
                    if sello == True:
                        return True
                    else:
                        return False
            
                    # Wait a while after the sale to the loss.
                    time.sleep (self.WAIT_TIME_STOP_LOSS)    
                
            else:
                return True
                
        elif status == 'FILLED':
            self.order_id = 0
            self.order_data = ""
            print('Order filled')
            return True
        elif status == 'PARTIALLY_FILLED':
            print('Order partially filled')
            return True
        else:
            return False

    def check(self, symbol, orderId, quantity):
    
        trading_size = 0
        time.sleep(self.WAIT_TIME_BUY_SELL)
    
        while trading_size < self.MAX_TRADE_SIZE:
        
            # Order info
            order = Orders.get_order(symbol, orderId)

            side  = order['side']
            price = float(order['price'])
        
            # Todo: Sell partial qty
            orig_qty = float(order['origQty']) 
            self.buy_filled_qty = float(order['executedQty'])
        
            status = order['status']

            print ('Wait buy order: %s id:%d, price: %.8f, orig_qty: %.8f' % (symbol, order['orderId'], price, orig_qty))
        
            if status == 'NEW':
            
                if Orders.cancel_order(symbol, orderId) == True:
            
                    buyo = Orders.buy_market(symbol, quantity)
                
                    print ('Buy market order')
                
                    self.order_id = buyo['orderId']
                    self.order_data = buyo
                                
                    if buyo == True:
                        break
                    else:
                        trading_size += 1
                        continue
                else:
                    break

            elif status == 'FILLED':
            
                self.order_id = order['orderId']
                self.order_data = order
                
                break
            elif status == 'PARTIALLY_FILLED':
                break
            else:
                trading_size += 1
                continue
         
    def calc(self, lastBid):
        try:

            return lastBid + (lastBid * self.option.profit / 100)

        except Exception as e:
            print ('c: %s' % (e))
            return 
            
    def action(self, symbol):
        
        # Order amount
        quantity = self.quantity
        
        # Fetches the ticker price
        lastPrice = Orders.get_ticker(symbol)
    
        # Order book prices
        lastBid, lastAsk = Orders.get_order_book(symbol)
    
        # Target buy price, add little increase #87
        buyPrice = lastBid + self.option.increasing
    
        # Target sell price, decrease little 
        sellPrice = lastAsk - self.option.decreasing 
        
        # Spread ( profit )
        profitableSellingPrice = self.calc(lastBid)

        # Check working mode
        if self.option.mode == 'range':

            buyPrice = self.option.buyprice
            sellPrice = self.option.sellprice
            profitableSellingPrice = sellPrice
    
        # Screen log
        if self.option.prints and self.order_id == 0:
            print ('price:%.8f buyp:%.8f sellp:%.8f-bid:%.8f ask:%.8f' % (lastPrice, buyPrice, profitableSellingPrice, lastBid, lastAsk))

        # analyze = threading.Thread(target=analyze, args=(symbol,))
        # analyze.start()
        
        if self.order_id > 0:
                        
            # Profit mode
            if self.order_data is not None:
                
                order = self.order_data;
            
                # Last control
                newProfitableSellingPrice = self.calc(float(order['price']))
                         
                if (lastAsk >= newProfitableSellingPrice):
                    profitableSellingPrice = newProfitableSellingPrice
                
            # range mode
            if self.option.mode == 'range':
                profitableSellingPrice = self.option.sellprice

            '''            
            If the order is complete, 
            try to sell it.
            '''
                
            # Perform buy action
            sellAction = threading.Thread(target=self.sell, args=(symbol, quantity, self.order_id, profitableSellingPrice, lastPrice,))
            sellAction.start()
            
            return

        '''
        Did profit get caught
        if ask price is greater than profit price, 
        buy with my buy price,    
        '''
        if (lastAsk >= profitableSellingPrice and self.option.mode == 'profit') or \
           (lastPrice <= self.option.buyprice and self.option.mode == 'range'):
                       
            if self.order_id == 0:
                self.order_id = self.buy(symbol, quantity, buyPrice)
            
            # Perform check/sell action
            checkAction = threading.Thread(target=self.check, args=(symbol, self.order_id, quantity,))
            checkAction.start()
    
    def logic(self):
        return 0
        
    def filters(self):
        
        symbol = self.option.symbol

        # Get symbol exchance info
        symbol_info = Orders.get_info(symbol)
        
        if not symbol_info:
            print (Fore.RED + Style.BRIGHT + "Invalid symbol, please try again...")
            exit(1)

        symbol_info['filters'] = {item['filterType']: item for item in symbol_info['filters']}
 
        return symbol_info
    
    def validate(self):
        
        symbol = self.option.symbol
        
        valid = True
        quantity = float(self.option.quantity)
        
        lastPrice = Orders.get_ticker(symbol)
        
        minQty = float(self.filters()['filters']['LOT_SIZE']['minQty'])
        minPrice = float(self.filters()['filters']['PRICE_FILTER']['minPrice'])
        minNotional = float(self.filters()['filters']['MIN_NOTIONAL']['minNotional'])
        
        price = lastPrice
        notional = lastPrice * quantity
        
        # minQty = minimum order quantity
        if quantity < minQty:
            print (Fore.RED + Style.BRIGHT + "Invalid quantity, minQty: %.8f (u: %.8f)" % (minQty, quantity))
            valid = False
        
        if price < minPrice:
            print (Fore.RED + Style.BRIGHT + "Invalid price, minPrice: %.8f (u: %.8f)" % (minQty, price))
            valid = False
        
        # minNotional = minimum order value (price * quantity)
        if notional < minNotional:
            print (Fore.RED + Style.BRIGHT + "Invalid price, minNotional: %.8f (u: %.8f)" % (minNotional, notional))
            valid = False
        
        if not valid:
            exit(1)
             
    def run(self):
        
        cycle = 0
        actions = []

        symbol = self.option.symbol

        print (Back.WHITE + Fore.BLUE + Style.BRIGHT +'@yasinkuyu, 2018')
        print (Back.WHITE + Fore.BLUE + Style.BRIGHT +'Auto Trading for Binance.com. --symbol: %s\n' % symbol)

        # Validate symbol
        self.validate()
        
        if self.option.mode == 'range':

           if self.option.buyprice == 0 or self.option.sellprice == 0:
               print ('Plese enter --buyprice / --sellprice\n')
               exit(1)

           print ('Wait buyprice:%.8f sellprice:%.8f' % (self.option.buyprice, self.option.sellprice))

        else:
           print (Fore.GREEN + Style.BRIGHT + '%s%% profit scanning for %s\n' % (self.option.profit, symbol))
        print ('... \n')

        while (cycle <= self.option.loop):

           startTime = time.time()
           
           actionTrader = threading.Thread(target=self.action, args=(symbol,))
           actions.append(actionTrader)
           actionTrader.start()
     
           endTime = time.time()

           if endTime - startTime < self.wait_time:

               time.sleep(self.wait_time - (endTime - startTime))

               # 0 = Unlimited loop
               if self.option.loop > 0:       
                   cycle = cycle + 1
               

   