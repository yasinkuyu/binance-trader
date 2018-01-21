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

    # percent (When you drop 10%, sell panic.)
    stop_loss = 0

    # Buy/Sell qty
    quantity = 0

    # float(step_size * math.floor(float(free)/step_size))
    step_size = 0
    tick_size = 0

    # Check bot status
    bot_status = "scan"

    # Define static vars
    WAIT_TIME_BUY_SELL = 1 # seconds
    WAIT_TIME_CHECK_BUY = 0.5 # seconds
    WAIT_TIME_CHECK_SELL = 5 # seconds
    WAIT_TIME_STOP_LOSS = 20 # seconds

    def __init__(self, option):

        # Get argument parse options
        self.option = option

        # Define parser vars
        self.order_id = self.option.orderid
        self.quantity = self.option.quantity
        self.wait_time = self.option.wait_time
        self.stop_loss = self.option.stop_loss
        self.max_amount = self.option.max_amount

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

            self.bot_status = "buy"

            return orderId

        except Exception as e:
            print ('bl: %s' % (e))
            time.sleep(self.WAIT_TIME_BUY_SELL)
            self.bot_status = "cancel"
            return None

    def sell(self, symbol, quantity, orderId, sell_price, last_price):

        '''
        The specified limit will try to sell until it reaches.
        If not successful, the order will be canceled.
        '''

        buy_order = Orders.get_order(symbol, orderId)

        if not buy_order:
            print ("SERVER DELAY! Rechecking...")
            return

        if buy_order['status'] == 'FILLED' and buy_order['side'] == "BUY":

            print ("Buy order filled... Try sell...")

        else:

            time.sleep(self.WAIT_TIME_CHECK_BUY)
            buy_order = Orders.get_order(symbol, orderId)

            if buy_order['status'] == 'FILLED' and buy_order['side'] == "BUY":

                print ("Buy order filled after 0.5 second... Try sell...")

            elif buy_order['status'] == 'PARTIALLY_FILLED' and buy_order['side'] == "BUY":

                print ("Buy order partially filled... Try sell... Cancel remaining buy...")
                self.cancel(symbol, orderId)
                quantity = Orders.get_order(symbol, orderId)['executedQty']

                if self.step_size == 1:
                    quantity = int(round(quantity))
                else:
                    quantity = round(quantity, self.step_size)

            else:

                self.cancel(symbol, orderId)
                print ("Buy order fail (Not filled) Cancel order...")

                time.sleep(self.WAIT_TIME_BUY_SELL)
                buy_order = Orders.get_order(symbol, orderId)

                if buy_order['status'] == 'FILLED':
                    print ("Binance server delayed! Try sell...")
                else:
                    self.bot_status = "cancel"
                    return


        sell_id = Orders.sell_limit(symbol, quantity, sell_price)['orderId']

        print ('Sell order create id: %d' % sell_id)

        # 5 seconds wait time before checking sell order
        time.sleep(self.WAIT_TIME_CHECK_SELL)

        if Orders.get_order(symbol, sell_id)['status'] == 'FILLED':

            print ('Sell order (Filled) id: %d' % sell_id)
            print ('LastPrice : %.8f' % last_price)
            print ('Profit: %%%s. Buy price: %.8f Sell price: %.8f' % (self.option.profit, float(buy_order['price']), sell_price))

            self.order_id = 0
            self.bot_status = "sell"
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
                lastPrice = float(Orders.get_ticker(symbol)['lastPrice'])
                print ('Status: %s Current price: %s Sell price: %s' % (sell_status, lastPrice, sell_price))

            print ('Sold! Continue trading...')

        self.order_id = 0
        self.bot_status = "sell"

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
            print('Order filled')
            return True
        else:
            return False

    def cancel(self,symbol, orderId):
        # If order is not filled, cancel it.
        check_order = Orders.get_order(symbol, orderId)
        
        if not check_order:
            self.order_id = 0
            return True
            
        if check_order['status'] == 'NEW' or check_order['status'] != "CANCELLED":
            Orders.cancel_order(symbol, orderId)
            self.order_id = 0
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

    def action(self, symbol):

        # Order amount
        quantity = self.quantity

        # Fetches the ticker price
        ticker = Orders.get_ticker(symbol)

        lastPrice = float(ticker['lastPrice'])
        lastBid = float(ticker['bidPrice'])
        lastAsk = float(ticker['askPrice'])

        # Target buy price, add little increase #87
        buyPrice = lastBid + (lastBid * self.increasing / 100)

        # Target sell price, decrease little 
        sellPrice = lastAsk - (lastAsk * self.decreasing / 100)

        # Spread ( profit )
        profitableSellingPrice = self.calc(lastBid)

        # Format Buy /Sell price according to Binance restriction
        buyPrice = round(buyPrice, self.tick_size)
        sellPrice = round(sellPrice, self.tick_size)

        # Order amount
        if self.quantity > 0:
            quantity = self.quantity
        else:
            if self.max_amount:
                self.amount = float(Orders.get_balance("BTC"))

            quantity = self.amount / buyPrice

        if self.step_size == 1:
            quantity = int(round(quantity))
        else:
            quantity = round(quantity, self.step_size)

        # Check working mode
        if self.option.mode == 'range':

            buyPrice = float(self.option.buyprice)
            sellPrice = float(self.option.sellprice)
            profitableSellingPrice = sellPrice

        # Screen log
        if self.option.prints and self.order_id == 0:
            print ('price:%.8f buyp:%.8f sellp:%.8f-bid:%.8f ask:%.8f' % (lastPrice, buyPrice, profitableSellingPrice, lastBid, lastAsk))

        '''
        Did profit get caught
        if ask price is greater than profit price,
        buy with my buy price,
        '''

        if (lastAsk >= profitableSellingPrice and self.option.mode == 'profit') or \
           (lastPrice <= float(self.option.buyprice) and self.option.mode == 'range'):

            if self.order_id == 0:

                while (self.bot_status != "buy"):

                    if self.bot_status == "cancel":
                        self.bot_status = "scan"
                        return

                    self.buy(symbol, quantity, buyPrice)

        if self.order_id > 0:

            # range mode
            if self.option.mode == 'range':
                profitableSellingPrice = self.option.sellprice

            # Sell price with proper sat count
            profitableSellingPrice = round((profitableSellingPrice - (profitableSellingPrice * self.option.decreasing / 100)), self.tick_size)

            '''
            If the order is complete,
            try to sell it.
            '''

            while (self.bot_status != "sell"):

                if self.bot_status == "cancel":
                    self.bot_status = "scan"
                    return

                self.sell(symbol, quantity, self.order_id, profitableSellingPrice, lastPrice)

        self.bot_status = "scan"

    def filters(self):

        symbol = self.option.symbol

        # Get symbol exchance info
        symbol_info = Orders.get_info(symbol)

        if not symbol_info:
            print ("Invalid symbol, please try again...")
            exit(1)

        symbol_info['filters'] = {item['filterType']: item for item in symbol_info['filters']}

        return symbol_info

    def get_satoshi_count(self, num):
        return int(str(Tools.e2f(num))[::-1].find('.'))

    def validate(self):

        valid = True
        symbol = self.option.symbol

        filters = self.filters()['filters']

        minQty = float(filters['LOT_SIZE']['minQty'])
        minPrice = float(filters['PRICE_FILTER']['minPrice'])
        minNotional = float(filters['MIN_NOTIONAL']['minNotional'])
        quantity = float(self.option.quantity)

        lastPrice = float(Orders.get_ticker(symbol)['lastPrice'])

        # stepSize defines the intervals that a quantity/icebergQty can be increased/decreased by.
        self.step_size = self.get_satoshi_count(float(filters['LOT_SIZE']['stepSize']))

        # tickSize defines the intervals that a price/stopPrice can be increased/decreased by.
        # -1 because it doesn't return decimal point, pure exponential form
        self.tick_size = self.get_satoshi_count(float(filters['PRICE_FILTER']['tickSize'])) - 1

        if self.quantity > 0:
            quantity = float(self.quantity)
        else:
            if self.max_amount:
                self.amount = float(Orders.get_balance("BTC"))

            lastBid, lastAsk = Orders.get_order_book(symbol)
            quantity = self.amount / lastBid

        if self.step_size == 1:
            quantity = int(round(quantity))
        else:
            quantity = round(quantity, self.step_size)

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

            startTime = time.time()

            self.action(symbol)

            endTime = time.time()

            if endTime - startTime < self.wait_time:

               time.sleep(self.wait_time - (endTime - startTime))

               # 0 = Unlimited loop
               if self.option.loop > 0:
                   cycle = cycle + 1