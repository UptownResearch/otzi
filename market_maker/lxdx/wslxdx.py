import sys
import logging
import ssl
import websocket
import threading
from time import sleep
import json

class wsLXDX:

    # Don't grow a table larger than this amount. Helps cap memory usage.
    MAX_TABLE_LEN = 200

    def __init__(self, settings={}):
        self.settings = settings
        self.logger = logging.getLogger('root')
        self.messagelogger = logging.getLogger('wsLXDX')
        self.__reset()
        self.data = {}

        #log root to console for now
        handler = logging.StreamHandler()
        formatter = logging.Formatter(fmt='%(asctime)s - %(levelname)s - %(module)s - %(message)s')
        handler.setFormatter(formatter)
        handler.setLevel(logging.INFO)
        #   logger.setLevel(log_level)
        self.logger.setLevel(logging.DEBUG)
        if not len(self.logger.handlers):
            self.logger.addHandler(handler)


    def connect(self):
        '''Connect to the websocket and initialize data stores.'''

        self.logger.debug("Connecting Data Feed WebSocket.")

        # Determine subscriptions
        subscriptions = {"action": "subscribe", "products": ["btc-tusd"],  "feeds": ["snapshot"]}

        # Get WS URL
        wsURL = "wss://iris-cert.lxdx-svcs.net/v1/orderbook"

        # Connect
        self.logger.info("Connecting to %s" % wsURL)
        self.__connect(wsURL)

    #
    # Public methods
    #

    def get_ticker(self, symbol=None):
        if symbol is None:
            symbol = self.symbol

        orderbook = self.data['orderBookL2']["btc-tusd"]
        result = {}
        result['bid'] = result['buy'] = max(orderbook['bids'].keys())
        result['ask'] = result['sell'] = min(orderbook['asks'].keys())
        result['bidVolume'] = orderbook['bids'][result['bid']]
        result['askVolume'] = orderbook['asks'][result['ask']]
        result['mid'] = (result['bid'] + result['ask'])/2.0
        return result

    def get_orderbook(self, symbol=None):
        if symbol is None:
            symbol = self.symbol
        return self.data['orderBookL2'][symbol]

    def recent_trades(self, symbol=None):
        if symbol is None:
            symbol = self.symbol
        if 'trade' in self.data:
            return self.data['trade'][symbol]
        else:
            return []


    #
    # Lifecycle methods
    #
    def error(self, err):
        self._error = err
        self.logger.error(err)
        self.exit()

    def exit(self):
        self.exited = True
        self.ws.close()


    #
    # Private methods
    #

    def _on_message(self, ws, message):
        #self.logger.info(message)
        message = json.loads(message)
        message_type = message['m']
        if message_type == 's':
            #Process a snapshot
            '''
            m -  Message Type.
            p - Product
            t - Timestamp of last update to the book. nanoseconds since unix epoch.
            s - Sequence Number
            b -  bid levels
            a - ask levels
            '''
            if 'orderBookL2' not in self.data:
                self.data['orderBookL2'] = {}
            product = message['p']
            if product not in self.data['orderBookL2']:
                self.data['orderBookL2'][product] = {}
            timestamp = message['t']
            sequence_num = message['s']
            bids = message['b']
            new_bids = {}
            for bid in bids:
                new_bids[float(bid['px'])] = float(bid['qty'])
            asks = message['a']
            new_asks = {}
            for ask in asks:
                new_asks[float(ask['px'])] = float(ask['qty'])
            self.data['orderBookL2'][product] = {'bids': new_bids, 'asks': new_asks}

        elif message_type == 'u':
            '''
            m - Message Type.
            p - Product
            t - Timestamp of last update. Provided as nanoseconds since unix epoch.
            s - Sequence Number
            b - A list of bid levels. px denotes the level's price, qty denotes the quantity available for the level.
            a - A list of ask levels. px denotes the level's price, qty denotes the quantity available for the level.
            '''

            product = message['p']
            if 'orderBookL2' in self.data and product in self.data['orderBookL2']:
                timestamp = message['t']
                sequence_num = message['s']
                bids = message['b']
                for bid in bids:
                    px = float(bid['px']); qty = float(bid['qty'])
                    self.data['orderBookL2'][product]['bids'][px] = qty
                asks = message['a']
                for ask in asks:
                    px = float(ask['px']); qty = float(ask['qty'])
                    self.data['orderBookL2'][product]['asks'][px] = qty
        elif message_type == 'v':
            '''
            m - Message Type.
            p - Product
            events - A list of Volume Events
            events.t - Timestamp for the trade.
            events.s - Aggressor for the trade.
            events.px - Price of the trade.
            events.qty - Quantity of the trade.
            '''
            if 'trade' not in self.data:
                self.data['trade'] = {}
            product = message['p']
            if product not in self.data['trade']:
                self.data['trade'][product] = []
            self.data['trade'][product].extend(message["events"])
            table_length = len(self.data['trade'][product])
            if table_length > self.MAX_TABLE_LEN:
                self.data['trade'][product] = \
                    self.data['trade'][product][table_length - self.MAX_TABLE_LEN :]

    def _on_open(self, ws):
        self.logger.debug("Data Feed Websocket Opened.")
        request = '{"action": "subscribe", "products": ["btc-tusd"],  "feeds": ["all"]}'
        self.logger.debug("Sending subscription request: %s" % request)
        ws.send(request)

    def _on_close(self, ws):
        self.logger.info('Data Feed Websocket Closed')
        self.exit()

    def _on_error(self, ws, error):
        if not self.exited:
            self.error(error)

    def __get_auth(self):
        '''Return auth headers. Not currently authenticating so return empty.'''
        return []

    def __reset(self):
        self.data = {}
        self.keys = {}
        self.exited = False
        self._error = None

    def __connect(self, wsURL):
        '''Connect to the websocket in a thread.'''
        self.logger.debug("Data Feed - Starting thread")

        ssl_defaults = ssl.get_default_verify_paths()
        sslopt_ca_certs = {'ca_certs': ssl_defaults.cafile}
        self.ws = websocket.WebSocketApp(wsURL,
                                         on_message=lambda ws, msg: self._on_message(ws, msg),
                                         on_close=  lambda ws: self._on_close(ws),
                                         on_open=   lambda ws: self._on_open(ws),
                                         on_error=  lambda ws, msg: self._on_error(ws, msg),
                                         header=self.__get_auth()
                                         )

        #self.wst = threading.Thread(target=lambda: self.ws.run_forever(sslopt=sslopt_ca_certs))
        self.wst = threading.Thread(target=lambda: self.ws.run_forever())
        self.wst.daemon = True
        self.wst.start()

        # Wait for connect before continuing
        conn_timeout = 5
        while (not self.ws.sock or not self.ws.sock.connected) and conn_timeout and not self._error:
            sleep(1)
            conn_timeout -= 1

        if not conn_timeout or self._error:
            self.logger.error("Couldn't connect to WS! Exiting.")
            self.exit()
            sys.exit(1)


def findItemByKeys(keys, table, matchData):
    for item in table:
        matched = True
        for key in keys:
            if item[key] != matchData[key]:
                matched = False
        if matched:
            return item

if __name__ == "__main__":
    # create console handler and set level to debug
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    # create formatter
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    # add formatter to ch
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    ws = wsLXDX()
    ws.logger = logger
    ws.connect()
    while(ws.ws.sock.connected):
        sleep(1)
