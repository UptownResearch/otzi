"""BitMEX API Connector."""
from __future__ import absolute_import
import requests
import time
import datetime
import json
import base64
import uuid
import logging

# Find code directory relative to our directory
from os.path import dirname, abspath, join
import sys
THIS_DIR = dirname(__file__)
CODE_DIR = abspath(join(THIS_DIR, '..', '..' ))
sys.path.append(CODE_DIR)


from market_maker.backtest.bitmexwsfromfile import BitMEXwsFromFile



class BitMEXbacktest(object):

    """BitMEX API Connector."""

    def __init__(self, base_url=None, symbol=None, apiKey=None, apiSecret=None,
                 orderIDPrefix='mm_bitmex_', shouldWSAuth=True, postOnly=False, timeout=7):
        """Init connector."""
        #self.logger = logging.getLogger('root')
        self.base_url = base_url
        self.symbol = symbol
        self.postOnly = postOnly
        #Don't need to authenticate, so just set apiKey
        self.apiKey = "Some Key"
        if (apiKey is None):
            raise Exception("Please set an API key and Secret to get started. See " +
                            "https://github.com/BitMEX/sample-market-maker/#getting-started for more information."
                            )
        self.apiKey = apiKey
        self.apiSecret = apiSecret
        if len(orderIDPrefix) > 13:
            raise ValueError("settings.ORDERID_PREFIX must be at most 13 characters long!")
        self.orderIDPrefix = orderIDPrefix
        self.retries = 0  # initialize counter

        # Prepare HTTPS session
        #self.session = requests.Session()
        # These headers are always sent
        #self.session.headers.update({'user-agent': 'liquidbot-' + constants.VERSION})
        #self.session.headers.update({'content-type': 'application/json'})
        #self.session.headers.update({'accept': 'application/json'})
        self.headers = None
        # Create websocket for streaming data
        self.ws = BitMEXwsFromFile()
        self.ws.connect(base_url, symbol, shouldAuth=shouldWSAuth)

        self.timeout = timeout

    def __del__(self):
        self.exit()

    def exit(self):
        self.ws.exit()

    #
    # Public methods
    #
    def current_timestamp(self):
        return self.ws.current_timestamp()

    def wait_update(self):
        try:
            return self.ws.wait_update()
        except:
            raise 

    
    def ticker_data(self, symbol=None):
        """Get ticker data."""
        if symbol is None:
            symbol = self.symbol
        return self.ws.get_ticker(symbol)

    def instrument(self, symbol):
        """Get an instrument's details."""
        return self.ws.get_instrument(symbol)
        #raise NotImplementedError
        
    def instruments(self, filter=None):
        #query = {}
        #if filter is not None:
        #    query['filter'] = json.dumps(filter)
        #return self._curl_bitmex(path='instrument', query=query, verb='GET')
        raise NotImplementedError
        
    def market_depth(self, symbol):
        """Get market depth / orderbook."""
        return self.ws.market_depth(symbol)

    def recent_trades(self):
        """Get recent trades.

        Returns
        -------
        A list of dicts:
              {u'amount': 60,
               u'date': 1306775375,
               u'price': 8.7401099999999996,
               u'tid': u'93842'},

        """
        return self.ws.recent_trades()

    def rate_limits(self):
        if self.headers:
            return (int(self.headers.get("x-ratelimit-limit",1)), 
                    int(self.headers.get("x-ratelimit-remaining",0)),
                    int(self.headers.get("x-ratelimit-reset",0)))
        else:
            #send default values
            return (300,300, self.ws.current_timestamp().timestamp()  + 300)

    #
    # Authentication required methods
    #
    def authentication_required(fn):
        """Annotation for methods that require auth."""
        def wrapped(self, *args, **kwargs):
            if not (self.apiKey):
                msg = "You must be authenticated to use this method"
                #raise errors.AuthenticationError(msg)
                raise Exception(msg)
            else:
                return fn(self, *args, **kwargs)
        return wrapped

    @authentication_required
    def funds(self):
        """Get your current balance."""
        return self.ws.funds()

    @authentication_required
    def position(self, symbol):
        """Get your open position."""
        return self.ws.position(symbol)

    @authentication_required
    def isolate_margin(self, symbol, leverage, rethrow_errors=False):
        """Set the leverage on an isolated margin position"""
        path = "position/leverage"
        postdict = {
            'symbol': symbol,
            'leverage': leverage
        }
        return self._curl_bitmex(path=path, postdict=postdict, verb="POST", rethrow_errors=rethrow_errors)

    @authentication_required
    def delta(self):
        return self.position(self.symbol)['homeNotional']

    @authentication_required
    def buy(self, quantity, price):
        """Place a buy order.

        Returns order object. ID: orderID
        """
        return self.place_order(quantity, price)

    @authentication_required
    def sell(self, quantity, price):
        """Place a sell order.

        Returns order object. ID: orderID
        """
        return self.place_order(-quantity, price)

    @authentication_required
    def place_order(self, quantity, price):
        """Place an order."""
        if price < 0:
            raise Exception("Price must be positive.")

        endpoint = "order"
        # Generate a unique clOrdID with our prefix so we can identify it.
        clOrdID = self.orderIDPrefix + base64.b64encode(uuid.uuid4().bytes).decode('utf8').rstrip('=\n')
        postdict = {
            'symbol': self.symbol,
            'orderQty': quantity,
            'price': price,
            'clOrdID': clOrdID
        }
        return self._curl_bitmex(path=endpoint, postdict=postdict, verb="POST")

    @authentication_required
    def amend_bulk_orders(self, orders):
        """Amend multiple orders."""
        # Note rethrow; if this fails, we want to catch it and re-tick
        #return self._curl_bitmex(path='order/bulk', postdict={'orders': orders}, verb='PUT', rethrow_errors=True)
        return True

    @authentication_required
    def create_bulk_orders(self, orders):
        """Create multiple orders."""
        for order in orders:
            order['clOrdID'] = self.orderIDPrefix + base64.b64encode(uuid.uuid4().bytes).decode('utf8').rstrip('=\n')
            order['symbol'] = self.symbol
            if self.postOnly:
                order['execInst'] = 'ParticipateDoNotInitiate'
        return True
        #return self._curl_bitmex(path='order/bulk', postdict={'orders': orders}, verb='POST')

    @authentication_required
    def open_orders(self):
        """Get open orders."""
        return self.ws.open_orders(self.orderIDPrefix)

    @authentication_required
    def http_open_orders(self):
        """Get open orders via HTTP. Used on close to ensure we catch them all."""
        # Not currently planned for use
        #raise NotImplementedError
        return []

    @authentication_required
    def cancel(self, orderID):
        """Cancel an existing order."""
        #path = "order"
        #postdict = {
        #    'orderID': orderID,
        #}
        #return self._curl_bitmex(path=path, postdict=postdict, verb="DELETE")
        return True

    @authentication_required
    def withdraw(self, amount, fee, address):
        # we will not be making any withdrawls
        raise NotImplementedError

    def _curl_bitmex(self, path, query=None, postdict=None, timeout=None, verb=None, rethrow_errors=False,
                     max_retries=None):
        #we are not going to be making any calls
        raise NotImplementedError

