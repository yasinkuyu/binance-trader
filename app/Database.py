# -*- coding: UTF-8 -*-
# @yasinkuyu

import sqlite3

class Database():
    
    def __init__(self):
                
        # Define Custom import vars
        self.conn = sqlite3.connect('orders.db', check_same_thread = False)
    
    # Database (Todo: Not complated)
    @staticmethod
    def write(data):
        '''    
        Save order
        data = orderid,symbol,amount,price,side,quantity,profit
        Create a database connection
        '''
        cur = self.conn.cursor()
        cur.execute('''INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?, ?)''', data)
        self.conn.commit()
    
    @staticmethod
    def read(orderid):
        '''
        Query order info by id
        :param orderid: the buy/sell order id
        :return:
        '''
        cur = self.conn.cursor()
        cur.execute('SELECT * FROM orders WHERE orderid = ?', (orderid,))
        return cur.fetchone()
    