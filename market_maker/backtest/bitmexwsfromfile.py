import sys
import websocket
import threading
import traceback
import ssl
from time import sleep
import json
import decimal
import logging

# Find code directory relative to our directory
from os.path import dirname, abspath, join
import sys
THIS_DIR = dirname(__file__)
CODE_DIR = abspath(join(THIS_DIR, '..', '..' ))
sys.path.append(CODE_DIR)

from market_maker.settings import settings
from market_maker.modifiable_settings import ModifiableSettings
from market_maker.auth.APIKeyAuth import generate_nonce, generate_signature
from market_maker.utils.log import setup_custom_logger
from market_maker.utils.math import toNearest
from future.utils import iteritems
from future.standard_library import hooks
with hooks():  # Python 2/3 compat
    from urllib.parse import urlparse, urlunparse

#New modules
import datetime
import iso8601

class BitMEXwsFromFile():

    # Don't grow a table larger than this amount. Helps cap memory usage.
    MAX_TABLE_LEN = 200

    def __init__(self):
        self.logger = logging.getLogger('root')
        self.messagelogger = logging.getLogger('bitmex_ws')
        self.last_action = None
        self.__reset()
        self.modifiable_settings = ModifiableSettings.getInstance()
        try:
            self.end_time = iso8601.parse_date(self.modifiable_settings.END_TIME)
        except:
            self.end_time = None
        try:
            self.start_time = iso8601.parse_date(self.modifiable_settings.START_TIME)        
        except:
            self.start_time = None   
        


    def __del__(self):
        #self.exit()
        pass

    def increment_timestep(self):
        parse = self.lines[self.currentline].split(' - ')
        #timestep = iso8601.parse_date(parse[0])
        #if not self.last_action:
        #    self.last_action = timestep
        self.last_action = parse[0]
        if self.end_time:
            current_time = iso8601.parse_date(parse[0])
            if current_time > self.end_time:
                raise EOFError("reached end time")
        continue_waiting = self.__on_message("", parse[1])
        if self.currentline < (len(self.lines) -1):
            self.currentline += 1
        else:
            raise EOFError("reached end of file")
            
        return continue_waiting

        
    def connect(self, endpoint="", symbol="XBTN15", shouldAuth=True):
        '''Connect to the websocket and initialize data stores.'''

        self.logger.debug("Connecting WebSocket.")
        self.symbol = symbol
        #self.shouldAuth = shouldAuth

        # We can subscribe right in the connection querystring, so let's build that.
        # Subscribe to all pertinent endpoints
        #subscriptions = [sub + ':' + symbol for sub in ["quote", "trade"]]
        #subscriptions += ["instrument"]  # We want all of them
        #if self.shouldAuth:
        #    subscriptions += [sub + ':' + symbol for sub in ["order", "execution", "orderBookL2"]]
        #    subscriptions += ["margin", "position"]

        # Get WS URL and connect.
        #urlParts = list(urlparse(endpoint))
        #urlParts[0] = urlParts[0].replace('http', 'ws')
        #urlParts[2] = "/realtime?subscribe=" + ",".join(subscriptions)
        #wsURL = urlunparse(urlParts)
        wsURL=""
        #self.logger.info("Connecting to %s" % wsURL)
        self.__connect(wsURL)
        #self.logger.info('Connected to WS. Waiting for data images, this may take a moment...')

        #Open the log file
        self.logger.info("Opening File: %s" % settings.WS_LOG_FILE)
        #modifiable_settings = ModifiableSettings.getInstance()
        self.lines = open(settings.WS_LOG_FILE, 'r').readlines()
        self.currentline = 0 

        #process first line of file to get an initial timestamp
        #self.recorded_action_time = self.increment_timestep()
        

        while not {'instrument', 'trade', 'quote'} <= set(self.data):
            self.increment_timestep()
        
        while not {'margin', 'position', 'order'} <= set(self.data):
            self.increment_timestep()

        # Is there an available start time?
        if self.start_time:
            parse = self.lines[self.currentline].split(' - ')
            current_time = iso8601.parse_date(parse[0])
            print( "Start Time: %s  Current Websocket Time: %s" % (self.modifiable_settings.START_TIME, parse[0]))
            if current_time > self.start_time:
                self.logger.warn("Start Time may be misconfigured!")
            while current_time < self.start_time:
                parse = self.lines[self.currentline].split(' - ')
                current_time = iso8601.parse_date(parse[0])
                self.currentline += 1

           
        # Connected. Wait for partials
        #self.__wait_for_symbol(symbol)
        #if self.shouldAuth:
        #    self.__wait_for_account()
        self.logger.info('Got all market data. Starting.')

    #
    # Data methods
    #
    def wait_update(self):    
        '''
        def wait_update(self):    
            if not self.recorded_action_time:
                self.recorded_action_time = self.last_action
            #Always process at least one message
            current_timestep = self.increment_timestep()
            while self.recorded_action_time <= self.last_action:
                try:
                    self.increment_timestep()
                except:
                    raise EOFError
            else:
                self.last_action = current_timestep
                return
        '''
        while True:
            try:
                #Increment timestep, if True, then an action has occurred
                if self.increment_timestep():
                    return
                else:
                    continue
            except:
                raise EOFError


    def current_timestamp(self):
        return iso8601.parse_date(self.last_action)
    
    
    def get_instrument(self, symbol="XBTUSD"):
        instruments = self.data['instrument']
        matchingInstruments = [i for i in instruments if i['symbol'] == symbol]
        if len(matchingInstruments) == 0:
            raise Exception("Unable to find instrument or index with symbol: " + symbol)
        instrument = matchingInstruments[0]
        # Turn the 'tickSize' into 'tickLog' for use in rounding
        # http://stackoverflow.com/a/6190291/832202
        instrument['tickLog'] = decimal.Decimal(str(instrument['tickSize'])).as_tuple().exponent * -1
        return instrument

    def get_ticker(self, symbol):
        '''Return a ticker object. Generated from instrument.'''

        instrument = self.get_instrument(symbol)

        # If this is an index, we have to get the data from the last trade.
        if instrument['symbol'][0] == '.':
            ticker = {}
            ticker['mid'] = ticker['buy'] = ticker['sell'] = ticker['last'] = instrument['markPrice']
        # Normal instrument
        else:
            bid = instrument['bidPrice'] or instrument['lastPrice']
            ask = instrument['askPrice'] or instrument['lastPrice']
            ticker = {
                "last": instrument['lastPrice'],
                "buy": bid,
                "sell": ask,
                "mid": (bid + ask) / 2
            }

        # The instrument has a tickSize. Use it to round values.
        return {k: toNearest(float(v or 0), instrument['tickSize']) for k, v in iteritems(ticker)}

    def funds(self):
        return self.data['margin'][0]

    def market_depth(self, symbol):
        return self.data['orderBookL2']
        #raise NotImplementedError('orderBook is not subscribed; use askPrice and bidPrice on instrument')
        # return self.data['orderBook25'][0]

    def open_orders(self, clOrdIDPrefix):
        orders = self.data['order']
        # Filter to only open orders (leavesQty > 0) and those that we actually placed
        return [o for o in orders if str(o['clOrdID']).startswith(clOrdIDPrefix) and o['leavesQty'] > 0]
        #return [o for o in orders if o['leavesQty'] > 0]

    def position(self, symbol):
        positions = self.data['position']
        pos = [p for p in positions if p['symbol'] == symbol]
        if len(pos) == 0:
            # No position found; stub it
            return {'avgCostPrice': 0, 'avgEntryPrice': 0, 'currentQty': 0, 'symbol': symbol}
        return pos[0]

    def recent_trades(self):
        return self.data['trade']

    #
    # Lifecycle methods
    #
    def error(self, err):
        self._error = err
        self.logger.error(err)
        self.exit()

    def exit(self):
        self.exited = True
    #    self.ws.close()

    #
    # Private methods
    #

    def __connect(self, wsURL):
        '''Connect to the websocket in a thread.'''
        self.logger.debug("Starting thread")

        #ssl_defaults = ssl.get_default_verify_paths()
        #sslopt_ca_certs = {'ca_certs': ssl_defaults.cafile}
        #self.ws = websocket.WebSocketApp(wsURL,
        #                                 on_message=self.__on_message,
        #                                 on_close=self.__on_close,
        #                                 on_open=self.__on_open,
        #                                 on_error=self.__on_error,
        #                                 header=self.__get_auth()
        #                                 )

        #setup_custom_logger('websocket', log_level=settings.LOG_LEVEL)
        #self.wst = threading.Thread(target=lambda: self.ws.run_forever(sslopt=sslopt_ca_certs))
        #self.wst.daemon = True
        #self.wst.start()
        self.logger.info("Started thread")

        # Wait for connect before continuing
        #conn_timeout = 5
        #while (not self.ws.sock or not self.ws.sock.connected) and conn_timeout and not self._error:
        #    sleep(1)
        #   conn_timeout -= 1

        #if not conn_timeout or self._error:
        #    self.logger.error("Couldn't connect to WS! Exiting.")
        #    self.exit()
        #    sys.exit(1)

    def __get_auth(self):
        '''Return auth headers. Will use API Keys if present in settings.'''

        #if self.shouldAuth is False:
        #    return []

        self.logger.info("Authenticating with API Key.")
        # To auth to the WS using an API key, we generate a signature of a nonce and
        # the WS API endpoint.
        #nonce = generate_nonce()
        #return [
        #    "api-nonce: " + str(nonce),
        #    "api-signature: " + generate_signature(settings.API_SECRET, 'GET', '/realtime', nonce, ''),
        #    "api-key:" + settings.API_KEY
        #]

    #def __wait_for_account(self):
    #    '''On subscribe, this data will come down. Wait for it.'''
    #    # Wait for the keys to show up from the ws
    #    while not {'margin', 'position', 'order'} <= set(self.data):
    #        sleep(0.1)

    #def __wait_for_symbol(self, symbol):
    #    '''On subscribe, this data will come down. Wait for it.'''
    #    while not {'instrument', 'trade', 'quote'} <= set(self.data):
    #        sleep(0.1)

    def __send_command(self, command, args):
        '''Send a raw command.'''
        #self.ws.send(json.dumps({"op": command, "args": args or []}))
        raise NotImplementedError
        
    def __on_message(self, ws, message):
        '''Handler for parsing WS messages.'''
        try:
        	message = json.loads(message)
        except:
        	self.logger.error("Failed on message %s." % message)
        	self.exit()

        # wait_action_occured signals whether to return from wait_update, or continue
        wait_action_occurred = False
        table = message['table'] if 'table' in message else None
        action = message['action'] if 'action' in message else None
        try:
            if 'subscribe' in message:
                if message['success']:
                    self.logger.debug("Subscribed to %s." % message['subscribe'])
                else:
                    self.error("Unable to subscribe to %s. Error: \"%s\" Please check and restart." %
                               (message['request']['args'][0], message['error']))
            elif 'status' in message:
                if message['status'] == 400:
                    self.error(message['error'])
                if message['status'] == 401:
                    self.error("API Key incorrect, please check and restart.")
            elif action:

                if table not in self.data:
                    self.data[table] = []

                if table not in self.keys:
                    self.keys[table] = []

                # There are four possible actions from the WS:
                # 'partial' - full table image
                # 'insert'  - new row
                # 'update'  - update row
                # 'delete'  - delete row
                if action == 'partial':
                    self.logger.debug("%s: partial" % table)
                    self.data[table] += message['data']
                    # Keys are communicated on partials to let you know how to uniquely identify
                    # an item. We use it for updates.
                    self.keys[table] = message['keys']
                elif action == 'insert':
                    self.logger.debug('%s: inserting %s' % (table, message['data']))
                    self.data[table] += message['data']

                    # Limit the max length of the table to avoid excessive memory usage.
                    # Don't trim orders because we'll lose valuable state if we do.
                    if table not in ['order', 'orderBookL2'] and len(self.data[table]) > BitMEXwsFromFile.MAX_TABLE_LEN:
                        self.data[table] = self.data[table][(BitMEXwsFromFile.MAX_TABLE_LEN // 2):]

                    #record when new information arrives
                    if table in [ 'quote', 'trade', 'orderBookL2']:
                        wait_action_occurred = True
                    
                elif action == 'update':
                    self.logger.debug('%s: updating %s' % (table, message['data']))
                    # Locate the item in the collection and update it.
                    for updateData in message['data']:
                        item = findItemByKeys(self.keys[table], self.data[table], updateData)
                        if not item:
                            continue  # No item found to update. Could happen before push

                        # Log executions
                        if table == 'order':
                            is_canceled = 'ordStatus' in updateData and updateData['ordStatus'] == 'Canceled'
                            if 'cumQty' in updateData and not is_canceled:
                                contExecuted = updateData['cumQty'] - item['cumQty']
                                if contExecuted > 0:
                                    instrument = self.get_instrument(item['symbol'])
                                    self.logger.info("Execution: %s %d Contracts of %s at %.*f" %
                                             (item['side'], contExecuted, item['symbol'],
                                              instrument['tickLog'], item['price']))

                        # Update this item.
                        item.update(updateData)

                        # Remove canceled / filled orders
                        if table == 'order' and item['leavesQty'] <= 0:
                            self.data[table].remove(item)

                        #record when new information arrives
                        if table in [ 'quote', 'trade', 'orderBookL2']:
                            wait_action_occurred = True
                elif action == 'delete':
                    self.logger.debug('%s: deleting %s' % (table, message['data']))
                    # Locate the item in the collection and remove it.
                    for deleteData in message['data']:
                        item = findItemByKeys(self.keys[table], self.data[table], deleteData)
                        self.data[table].remove(item)
                else:
                    raise Exception("Unknown action: %s" % action)
        except ValueError:
            self.logger.info(traceback.format_exc())
        except:
            self.logger.error(traceback.format_exc())
        return wait_action_occurred

    def __on_open(self, ws):
        self.logger.debug("Websocket Opened.")

    def __on_close(self, ws):
        self.logger.info('Websocket Closed')
        self.exit()

    def __on_error(self, ws, error):
        if not self.exited:
            self.error(error)

    def __reset(self):
        self.data = {}
        self.keys = {}
        self.exited = False
        self._error = None


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
    wsfromfile = BitMEXwsFromFile()
    wsfromfile.logger = logger
    wsfromfile.connect(endpoint="", symbol="XBTUSD", shouldAuth=True)
    logger.info(wsfromfile.get_ticker("XBTUSD"))
    logger.info(wsfromfile.current_timestamp())
    wsfromfile.wait_update()
    logger.info(wsfromfile.current_timestamp())

