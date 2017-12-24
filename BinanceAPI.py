import time
import hashlib
import requests

try:
    from urllib import urlencode
except ImportError:
    from urllib.parse import urlencode

#from urllib.parse import urlencode
#from urllib import urlencode
#https://github.com/purboox/BinanceAPI

class BinanceAPI:
    BASE_URL = "https://www.binance.com/api/v1"

    def __init__(self, key, secret):
        self.key = key
        self.secret = secret


    def get_ticker(self, market):
        path = "%s/ticker/24hr" % self.BASE_URL
        params = {"symbol": market}
        return self._get_no_sign(path, params)


    def get_orderbooks(self, market, limit=50):
        path = "%s/depth" % self.BASE_URL
        params = {"symbol": market, "limit": limit}
        return self._get_no_sign(path, params)


    def get_account(self):
        path = "%s/account" % self.BASE_URL
        return self._get(path, {})


    def get_open_orders(self, market, limit = 100):
        path = "%s/openOrders" % self.BASE_URL
        params = {"symbol": market}
        return self._get(path, params)


    def buy_limit(self, market, quantity, rate):
        path = "%s/order" % self.BASE_URL
        params = {"symbol": market, "side": "BUY", \
            "type": "LIMIT", "timeInForce": "GTC", \
            "quantity": quantity, "price": '%.8f' % rate}
        return self._post(path, params)


    def sell_limit(self, market, quantity, rate):
        path = "%s/order" % self.BASE_URL
        params = {"symbol": market, "side": "SELL", \
            "type": "LIMIT", "timeInForce": "GTC", \
            "quantity": quantity, "price": '%.8f' % rate}
        return self._post(path, params)


    def buy_market(self, market, quantity):
        path = "%s/order" % self.BASE_URL
        params = {"symbol": market, "side": "BUY", \
            "type": "MARKET", "quantity": quantity}
        return self._post(path, params)


    def sell_market(self, market, quantity):
        path = "%s/order" % self.BASE_URL
        params = {"symbol": market, "side": "SELL", \
            "type": "MARKET", "quantity": quantity}
        return self._post(path, params)


    def query_order(self, market, orderId):
        path = "%s/order" % self.BASE_URL
        params = {"symbol": market, "orderId": orderId}
        return self._get(path, params)


    def cancel(self, market, order_id):
        path = "%s/order" % self.BASE_URL
        params = {"symbol": market, "orderId": order_id}
        return self._delete(path, params)


    def _get_no_sign(self, path, params={}):
        query = urlencode(params)
        url = "%s?%s" % (path, query)
        return requests.get(url, timeout=30, verify=True).json()

    
    def _sign(self, params={}):
        data = params.copy()

        ts = str(int(1000 * time.time()))
        data.update({"timestamp": ts})

        h = self.secret + "|" + urlencode(data)
        signature = hashlib.sha256(h).hexdigest()
        data.update({"signature": signature})
        return data
    

    def _get(self, path, params={}):
        params.update({"recvWindow": 120000})
        query = urlencode(self._sign(params))
        url = "%s?%s" % (path, query)
        header = {"X-MBX-APIKEY": self.key}
        return requests.get(url, headers=header, \
            timeout=30, verify=True).json()


    def _post(self, path, params={}):
        params.update({"recvWindow": 120000})
        query = urlencode(self._sign(params))
        url = "%s?%s" % (path, query)
        header = {"X-MBX-APIKEY": self.key}
        return requests.post(url, headers=header, \
            timeout=30, verify=True).json()


    def _delete(self, path, params={}):
        params.update({"recvWindow": 120000})
        query = urlencode(self._sign(params))
        url = "%s?%s" % (path, query)
        header = {"X-MBX-APIKEY": self.key}
        return requests.delete(url, headers=header, \
            timeout=30, verify=True).json()