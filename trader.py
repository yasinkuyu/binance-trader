# -*- coding: UTF-8 -*-
# @yasinkuyu

import sys
import argparse

sys.path.insert(0, './app')

from Trading import Trading
      
if __name__ == '__main__':
    
    # Set parser
    parser = argparse.ArgumentParser()
    parser.add_argument('--quantity', type=float, help='Buy/Sell Quantity', default=200)
    parser.add_argument('--symbol', type=str, help='Market Symbol (Ex: XVGBTC)', required=True)
    parser.add_argument('--profit', type=float, help='Target Profit', default=1.3)

    # Stop-Loss (Todo: Not complated)
    parser.add_argument('--stoploss', type=float, help='Target Stop-Loss % (If the price drops by 6%, sell market_price.)', default=0) 

    parser.add_argument('--increasing', type=float, help='Buy Price +Increasing (0.00000001)', default=0.00000001)
    parser.add_argument('--decreasing', type=float, help='Sell Price -Decreasing (0.00000001)', default=0.00000001)

    # Manually defined --orderid try to sell 
    parser.add_argument('--orderid', type=int, help='Target Order Id (use balance.py)', default=0)

    parser.add_argument('--wait_time', type=int, help='Wait Time (seconds)', default=1)
    parser.add_argument('--test_mode', type=bool, help='Test Mode True/False', default=False)
    parser.add_argument('--prints', type=bool, help='Scanning Profit Screen Print True/False', default=True)
    parser.add_argument('--debug', type=bool, help='Debug True/False', default=True)
    parser.add_argument('--loop', type=int, help='Loop (0 unlimited)', default=0)

    # Working Modes  (Todo: Not complated)
    #  - profit: Find defined profit, buy and sell. (Ex: 1.3% profit)
    #  - range: Between target two price, buy and sell. (Ex: <= 0.00100 buy - >= 0.00150 sell )
    parser.add_argument('--mode', type=str, help='Working Mode', default='profit')
    parser.add_argument('--buyprice', type=float, help='Buy Price (Price is greater than equal <=)', default=0)
    parser.add_argument('--sellprice', type=float, help='Sell Price (Price is small than equal >=)', default=0)
    
    option = parser.parse_args()
    
    # Get start
    t = Trading(option)
    t.run()