# -*- coding: UTF-8 -*-
# @yasinkuyu

# Define Python imports
import os
import sys
import time
import config
import threading

# Define Custom imports
from Database import Database
from Orders import Orders
from Tools import Tools

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

    # float(step_size * math.floor(float(free)/step_size))
    step_size = 0

    # Satoshi decimal places count
    satoshi_count = 0

    # Checker for flood threading
    is_thread_open = False

    # Define static vars
    WAIT_TIME_BUY_SELL = 1 # seconds
    WAIT_TIME_CHECK_BUY = 0.2 # seconds
    WAIT_TIME_CHECK_SELL = 5 # seconds
    WAIT_TIME_STOP_LOSS = 20 # seconds

    MAX_TRADE_SIZE = 7 # int

    def __init__(self, option):
                
        # Get argument parse options
        self.option = option
        
        # Define parser vars
        self.order_id = self.option.orderid
        self.quantity = self.option.quantity
        self.wait_time = self.option.wait_time
        self.stop_loss = self.option.stop_loss

        # Buy amount
        self.amount = self.option.amount
        
        #BTC amount
        self.amount = self.option.amount
        
        self.increasing = self.option.increasing
        self.decreasing = self.option.decreasing
    
    def buy(self, symbol, quantity, buyPrice):

        # Do you have an open order?
        self.checkorder()

        try:

            # Create order
            orderId = Orders.buy_limit(symbol, quantity, buyPrice)

            # Database log
            Database.write([orderId, symbol, 0, buyPrice, 'BUY', quantity, self.option.profit])

            print ('Buy order created id:%d, q:%.8f, p:%.8f' % (orderId, quantity, float(buyPrice)))

            self.order_id = orderId

            return orderId

        except Exception as e:
            print ('bl: %s' % (e))
            time.sleep(self.WAIT_TIME_BUY_SELL)
            return None

    def sell(self, symbol, quantity, orderId, sell_price, last_price):

        '''
        The specified limit will try to sell until it reaches.
        If not successful, the order will be canceled.
        '''

        buy_order = Orders.get_order(symbol, orderId)

        if buy_order['status'] == 'FILLED' and buy_order['side'] == "BUY":
            print ("Buy order filled... Try sell...")
        else:
            time.sleep(self.WAIT_TIME_CHECK_BUY)
            if buy_order['status'] == 'FILLED' and buy_order['side'] == "BUY":
                print ("Buy order filled after 0.2 second... Try sell...")
            elif buy_order['status'] == 'PARTIALLY_FILLED' and buy_order['side'] == "BUY":
                print ("Buy order partially filled... Try sell... Cancel remaining buy...")
                self.cancel(symbol, orderId)
            else:
                self.cancel(symbol, orderId)
                print ("Buy order fail (Not filled) Cancel order...")
                self.order_id = 0
                self.is_thread_open = False
                return

        # Format quantity
        stepsize = quantity % float(self.step_size)
        quantity = quantity - stepsize

        sell_order = Orders.sell_limit(symbol, quantity, sell_price)

        sell_id = sell_order['orderId']
        print ('Sell order create id: %d' % sell_id)

        # 5 seconds wait time before checking sell order
        time.sleep(self.WAIT_TIME_CHECK_SELL)

        if sell_order['status'] == 'FILLED':

            print ('Sell order (Filled) id: %d' % sell_id)
            print ('LastPrice : %.8f' % last_price)
            print ('Profit: %%%s. Buy price: %.8f Sell price: %.8f' % (self.option.profit, float(buy_order['price']), sell_price))

            self.order_id = 0
            self.order_data = None
            self.is_thread_open = False

            return

        '''
        If all sales trials fail,
        the grievance is stop-loss.
        '''

        if self.stop_loss > 0:

            # If sell order failed after 5 seconds, 5 seconds more wait time before selling at loss
            time.sleep(self.WAIT_TIME_CHECK_SELL)

            if self.stop(symbol, quantity, sell_id, sell_price):

                if Orders.get_order(symbol, sell_id)['status'] != 'FILLED':
                    print ('We apologize... Sold at loss...')

            else:
                print ('We apologize... Cant sell even at loss... Please sell manually... Stopping program...')
                self.cancel(symbol, sell_id)
                quit()
        else:
            sell_status = 'NEW'

            while (sell_status != "FILLED"):
                time.sleep(self.WAIT_TIME_CHECK_SELL)
                sell_status = Orders.get_order(symbol, sell_id)['status']
                lastPrice = Orders.get_ticker(symbol)
                print ('Status: %s Current price: %.8f Sell price: %.8f' % (sell_status, lastPrice, sell_price))

            print ('Sold! Continue trading...')

        self.order_id = 0
        self.order_data = None
        self.is_thread_open = False

    def stop(self, symbol, quantity, orderId, sell_price):
        # If the target is not reached, stop-loss.
        stop_order = Orders.get_order(symbol, orderId)

        lossprice = sell_price - (sell_price * self.stop_loss / 100)

        status = stop_order['status']

        # Order status
        if status == 'NEW' or status == 'PARTIALLY_FILLED':

            if self.cancel(symbol, orderId):

                # Stop loss
                lastBid, lastAsk = Orders.get_order_book(symbol)

                if lastAsk >= lossprice:

                    sello = Orders.sell_market(symbol, quantity)

                    print ('Stop-loss, sell market, %s' % (lastAsk))

                    sell_id = sello['orderId']

                    if sello == True:
                        return True
                    else:
                        # Wait a while after the sale to the loss.
                        time.sleep(self.WAIT_TIME_STOP_LOSS)
                        statusloss = sello['status']
                        if statusloss != 'NEW':
                            print ('Stop-loss, sold')
                            return True
                        else:
                            self.cancel(symbol, sell_id)
                            return False
                else:
                    sello = Orders.sell_limit(symbol, quantity, lossprice)
                    print ('Stop-loss, sell limit, %s' % (lossprice))
                    time.sleep(self.WAIT_TIME_STOP_LOSS)
                    statusloss = sello['status']
                    if statusloss != 'NEW':
                        print ('Stop-loss, sold')
                        return True
                    else:
                        self.cancel(symbol, sell_id)
                        return False
            else:
                print ('Cancel did not work... Might have been sold before stop loss...')
                return True

        elif status == 'FILLED':
            self.order_id = 0
            self.order_data = None
            print('Order filled')
            return True
        else:
            return False

    def check(self, symbol, orderId, quantity):
        # If profit is available and there is no purchase from the specified price, take it with the market.

        # Do you have an open order?
        self.checkorder()

        trading_size = 0
        time.sleep(self.WAIT_TIME_BUY_SELL)

        while trading_size < self.MAX_TRADE_SIZE:

            # Order info
            order = Orders.get_order(symbol, orderId)

            side  = order['side']
            price = float(order['price'])

            # TODO: Sell partial qty
            orig_qty = float(order['origQty']) 
            self.buy_filled_qty = float(order['executedQty'])

            status = order['status']

            print ('Wait buy order: %s id:%d, price: %.8f, orig_qty: %.8f' % (symbol, order['orderId'], price, orig_qty))

            if status == 'NEW':

                if self.cancel(symbol, orderId):

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
                print ("Filled")
                break
            elif status == 'PARTIALLY_FILLED':
                print ("Partial filled")
                break
            else:
                trading_size += 1
                continue

    def cancel(self,symbol, orderId):
        # If order is not filled, cancel it.
        check_order = Orders.get_order(symbol, orderId)
        
        if not check_order:
            self.order_id = 0
            self.order_data = None
            return True
            
        if check_order['status'] == 'NEW' or check_order['status'] != "CANCELLED":
            Orders.cancel_order(symbol, orderId)
            self.order_id = 0
            self.order_data = None
            return True

    def calc(self, lastBid):
        try:

            return lastBid + (lastBid * self.option.profit / 100)

        except Exception as e:
            print ('c: %s' % (e))
            return

    def checkorder(self):
        # If there is an open order, exit.
        if self.order_id > 0:
            exit(1)

    def set_satoshi_count(self, lastPrice, lastBid, lastAsk):
        # Compare decimal places and use the largest for set_satoshi_count
        sats1 = int(str(Tools.e2f(lastPrice))[::-1].find('.'))
        sats2 = int(str(Tools.e2f(lastBid))[::-1].find('.'))
        sats3 = int(str(Tools.e2f(lastAsk))[::-1].find('.'))
        integers = [sats1, sats2, sats3]
        newCount = max(integers)
        if self.satoshi_count < newCount:
            self.satoshi_count = newCount

    def action(self, symbol):

        self.is_thread_open = True

        # Order amount
        quantity = self.quantity

        # Fetches the ticker price
        lastPrice = Orders.get_ticker(symbol)

        # Order book prices
        lastBid, lastAsk = Orders.get_order_book(symbol)

        # Target buy price, add little increase #87
        buyPrice = lastBid + (lastBid * self.increasing / 100)

        # Target sell price, decrease little 
        sellPrice = lastAsk - (lastAsk * self.decreasing / 100)

        # Spread ( profit )
        profitableSellingPrice = self.calc(lastBid)

        # Format sell price according to Binance restriction
        self.set_satoshi_count(lastPrice, lastBid, lastAsk)

        buyPrice = round(buyPrice, self.satoshi_count)
        sellPrice = round(sellPrice, self.satoshi_count)
        profitableSellingPrice = round(profitableSellingPrice, self.satoshi_count)

        # Order amount
        if self.quantity > 0:
            quantity = self.quantity
        else:
            quantity = self.amount / lastBid
            if self.satoshi_count <= 6:
                quantity = round(quantity, 3)
            elif self.satoshi_count <= 7:
                quantity = round(quantity, 2)
            else:
                quantity = int(round(quantity))

        # Check working mode
        if self.option.mode == 'range':

            buyPrice = float(self.option.buyprice)
            sellPrice = float(self.option.sellprice)
            profitableSellingPrice = sellPrice

        # Screen log
        if self.option.prints and self.order_id == 0:
            print ('price:%.8f buyp:%.8f sellp:%.8f-bid:%.8f ask:%.8f' % (lastPrice, buyPrice, profitableSellingPrice, lastBid, lastAsk))

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

            # Sell price with proper sat count
            profitableSellingPrice = round((profitableSellingPrice - (profitableSellingPrice * self.option.decreasing / 100)), self.satoshi_count)

            # Perform buy action
            sellAction = threading.Thread(target=self.sell, args=(symbol, quantity, self.order_id, profitableSellingPrice, lastPrice,))
            sellAction.start()

            self.is_thread_open = False
            return

        '''
        Did profit get caught
        if ask price is greater than profit price,
        buy with my buy price,
        '''

        if (lastAsk >= profitableSellingPrice and self.option.mode == 'profit') or \
           (lastPrice <= float(self.option.buyprice) and self.option.mode == 'range'):

            if self.order_id == 0:
                self.buy(symbol, quantity, buyPrice)

                # Perform check/sell action
                # checkAction = threading.Thread(target=self.check, args=(symbol, self.order_id, quantity,))
                # checkAction.start()

        self.is_thread_open = False

    def logic(self):
        return 0

    def filters(self):

        symbol = self.option.symbol

        # Get symbol exchance info
        symbol_info = Orders.get_info(symbol)

        if not symbol_info:
            print ("Invalid symbol, please try again...")
            exit(1)

        symbol_info['filters'] = {item['filterType']: item for item in symbol_info['filters']}

        return symbol_info

    def validate(self):

        valid = True
        symbol = self.option.symbol
        filters = self.filters()['filters']

        lastPrice = Orders.get_ticker(symbol)

        minQty = float(filters['LOT_SIZE']['minQty'])
        minPrice = float(filters['PRICE_FILTER']['minPrice'])
        minNotional = float(filters['MIN_NOTIONAL']['minNotional'])
        quantity = float(self.option.quantity)
        
        if self.quantity > 0:
            quantity = float(self.quantity)
        else:
            lastBid, lastAsk = Orders.get_order_book(symbol)
            quantity = self.amount / lastBid
            satsQuantity1 = int(str(Tools.e2f(lastBid))[::-1].find('.'))
            satsQuantity2 = int(str(Tools.e2f(lastAsk))[::-1].find('.'))
            satsQuantity3 = int(str(Tools.e2f(lastPrice))[::-1].find('.'))
            integer = [satsQuantity1, satsQuantity2, satsQuantity3]
            satsQuantity = max(integer)

            if satsQuantity <= 6:
                quantity = round(quantity, 3)
            elif satsQuantity <= 7:
                quantity = round(quantity, 2)
            else:
                quantity = int(round(quantity))

        # stepSize defines the intervals that a quantity/icebergQty can be increased/decreased by.
        stepSize = float(filters['LOT_SIZE']['stepSize'])

        # tickSize defines the intervals that a price/stopPrice can be increased/decreased by
        tickSize = float(filters['PRICE_FILTER']['tickSize'])

        # Format quantity
        self.step_size = stepSize

        # If option increasing default tickSize greater than
        if (float(self.option.increasing) < tickSize):
            self.increasing = tickSize
        
        # If option decreasing default tickSize greater than
        if (float(self.option.decreasing) < tickSize):
            self.decreasing = tickSize
        
        # Just for validation
        price = lastPrice
        notional = lastPrice * quantity

        # minQty = minimum order quantity
        if quantity < minQty:
            print ("Invalid quantity, minQty: %.8f (u: %.8f)" % (minQty, quantity))
            valid = False

        if price < minPrice:
            print ("Invalid price, minPrice: %.8f (u: %.8f)" % (minPrice, price))
            valid = False

        # minNotional = minimum order value (price * quantity)
        if notional < minNotional:
            print ("Invalid notional, minNotional: %.8f (u: %.8f)" % (minNotional, notional))
            valid = False

        if not valid:
            exit(1)

    def run(self):

        cycle = 0
        actions = []

        symbol = self.option.symbol

        print ('@yasinkuyu, 2018')
        print ('Auto Trading for Binance.com. --symbol: %s\n' % symbol)

        # Validate symbol
        self.validate()

        if self.option.mode == 'range':

           if self.option.buyprice == 0 or self.option.sellprice == 0:
               print ('Plese enter --buyprice / --sellprice\n')
               quit()

           print ('Wait buyprice:%.8f sellprice:%.8f' % (self.option.buyprice, self.option.sellprice))

        else:
           print ('%s%% profit scanning for %s\n' % (self.option.profit, symbol))

        print ('... \n')

        while (cycle <= self.option.loop):

            if not self.is_thread_open:
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