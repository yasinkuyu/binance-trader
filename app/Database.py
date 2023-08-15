# -*- coding: UTF-8 -*-
# @yasinkuyu

import os
import sqlite3

class Database():
    # Define Custom import vars
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../db/orders.db')
    
    @staticmethod
    def write(data):
        '''    
        Save order
        data = orderid, symbol, amount, price, side, quantity, profit
        Create a database connection
        '''
        conn = sqlite3.connect(Database.path, check_same_thread=False)
        cur = conn.cursor()
        cur.execute('''INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?, ?)''', data)
        conn.commit()
        conn.close()
    
    @staticmethod
    def read(orderid):
        '''
        Query order info by id
        :param orderid: the buy/sell order id
        :return:
        '''
        conn = sqlite3.connect(Database.path, check_same_thread=False)
        cur = conn.cursor()
        cur.execute('SELECT * FROM orders WHERE orderid = ?', (orderid,))
        result = cur.fetchone()
        conn.close()
        return result
