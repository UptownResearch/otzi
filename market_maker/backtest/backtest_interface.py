from __future__ import absolute_import
from time import sleep
from datetime import datetime, timezone
import base64
import uuid
import logging

# Find code directory relative to our directory
from os.path import dirname, abspath, join
import sys
THIS_DIR = dirname(__file__)
CODE_DIR = abspath(join(THIS_DIR, '..', '..' ))
sys.path.append(CODE_DIR)

#load files in our directories
#from market_maker.settings import settings
from market_maker.utils import log, errors
from market_maker import paper_trading
from market_maker.backtest.exchangepairaccessor import ExchangePairAccessor
from market_maker.backtest.timekeeper import Timekeeper
#
# Helpers
#
logger = logging.getLogger("root")
compare_logger = logging.getLogger("PAPERTRADING")


class BacktestInterface:
    def __init__(self, timekeeper = None, trades_filename = "", settings = None,
                L2orderbook_filename = "", name = ""):
        self.settings = settings
        self.paper = paper_trading.PaperTrading(settings = self.settings)
        if timekeeper == None:
            self.timekeeper = Timekeeper()
            self.own_timekeeper = True
        else:
            self.own_timekeeper = False
            self.timekeeper = timekeeper
        self.accessor = ExchangePairAccessor(self.timekeeper, 
                    trades_filename, L2orderbook_filename, name=name, settings = self.settings)        
        self.paper.provide_exchange(self.accessor)
        self.paper.reset()
        self.orderIDPrefix="BT_"
        if self.own_timekeeper:
            self.timekeeper.initialize()
        self.symbol = self.settings.symbol
        self.last_order_time = None

    def is_warm(self):
        self.accessor.is_warm()
 
    def cancel_order(self, order):
        tickLog = self.get_instrument()['tickLog']
        logger.info("Canceling: %s %d @ %.*f" % (order['side'], order['orderQty'], tickLog, order['price']))
        return self.paper.cancel_order(order['orderID'])

    def cancel_all_orders(self):
        logger.info("Resetting current position. Canceling all existing orders.")
        return self.paper.cancel_all_orders()

    def get_portfolio(self):
        contracts = self.settings.CONTRACTS
        portfolio = {}
        for symbol in contracts:
            position = self.paper.get_position(symbol=symbol)
            instrument = self.accessor.instrument(symbol=symbol)

            if instrument['isQuanto']:
                future_type = "Quanto"
            elif instrument['isInverse']:
                future_type = "Inverse"
            elif not instrument['isQuanto'] and not instrument['isInverse']:
                future_type = "Linear"
            else:
                raise NotImplementedError("Unknown future type; not quanto or inverse: %s" % instrument['symbol'])

            if instrument['underlyingToSettleMultiplier'] is None:
                multiplier = float(instrument['multiplier']) / float(instrument['quoteToSettleMultiplier'])
            else:
                multiplier = float(instrument['multiplier']) / float(instrument['underlyingToSettleMultiplier'])

            portfolio[symbol] = {
                "currentQty": float(position['currentQty']),
                "futureType": future_type,
                "multiplier": multiplier,
                "markPrice": float(instrument['markPrice']),
                "spot": float(instrument['indicativeSettlePrice'])
            }

        return portfolio

    def calc_delta(self):

        """Calculate currency delta for portfolio"""
        portfolio = self.get_portfolio()
        spot_delta = 0
        mark_delta = 0
        for symbol in portfolio:
            item = portfolio[symbol]
            if item['futureType'] == "Quanto":
                spot_delta += item['currentQty'] * item['multiplier'] * item['spot']
                mark_delta += item['currentQty'] * item['multiplier'] * item['markPrice']
            elif item['futureType'] == "Inverse":
                spot_delta += (item['multiplier'] / item['spot']) * item['currentQty']
                mark_delta += (item['multiplier'] / item['markPrice']) * item['currentQty']
            elif item['futureType'] == "Linear":
                spot_delta += item['multiplier'] * item['currentQty']
                mark_delta += item['multiplier'] * item['currentQty']
        basis_delta = mark_delta - spot_delta
        delta = {
            "spot": spot_delta,
            "mark_price": mark_delta,
            "basis": basis_delta
        }
        return delta

    def get_delta(self, symbol=None):
        return self.paper.current_contract()

    def get_instrument(self, symbol=None):
        if symbol is None:
            symbol = self.symbol
        return self.accessor.instrument(symbol)

    def get_margin(self):       
        return self.paper.get_funds()

    def get_orders(self): 
        return self.paper.get_orders()

    def get_highest_buy(self):
        buys = [o for o in self.get_orders() if o['side'] == 'Buy']
        if not len(buys):
            return {'price': -2**32}
        highest_buy = max(buys or [], key=lambda o: o['price'])
        return highest_buy if highest_buy else {'price': -2**32}

    def get_lowest_sell(self):
        sells = [o for o in self.get_orders() if o['side'] == 'Sell']
        if not len(sells):
            return {'price': 2**32}
        lowest_sell = min(sells or [], key=lambda o: o['price'])
        return lowest_sell if lowest_sell else {'price': 2**32}  # ought to be enough for anyone

    def get_position(self, symbol=None):
        return self.paper.get_position(symbol)
 
    def get_ticker(self, symbol=None):
        return self.accessor.ticker_data(symbol)

    def is_open(self):
        return True

    def check_market_open(self):
         return True

    def check_if_orderbook_empty(self):
        """This function checks whether the order book is empty"""
        #let's force an order book
        while self.accessor.market_depth("") == []:
            self.timekeeper.increment_time()


    def amend_bulk_orders(self, orders):
        self.last_order_time = self._current_timestamp() 
        self.paper.cancel_all_orders()
        self.paper.track_orders_created(orders)


    def create_bulk_orders(self, orders):
        self.last_order_time = self._current_timestamp() 
        for order in orders:
            order['clOrdID'] = self.orderIDPrefix + base64.b64encode(uuid.uuid4().bytes).decode('utf8').rstrip('=\n')
        self.paper.track_orders_created(orders)
        return orders 

    def cancel_bulk_orders(self, orders): 
        self.last_order_time = self._current_timestamp() 
        for order in orders:
            self.cancel_order(order)

    def recent_trades(self):
        return self.accessor.recent_trades()

    def market_deep(self):
        return self.accessor.market_depth("")

    def current_timestamp(self):
        return self.accessor.current_timestamp().timestamp()

    def contracts_this_run(self):
        return self.paper.contract_traded_this_run()

    def _current_timestamp(self):
        return self.accessor.current_timestamp().timestamp()

    def ok_to_enter_order(self):
        '''Used to rate limit the placement of orders.'''
        if self.last_order_time:
            time_since_last = self._current_timestamp() - self.last_order_time 
            # force a 1 second wait for now
            if time_since_last > max(self.current_api_call_timing(), 1):
                self.last_order_time = self._current_timestamp() 
                return True
            else:
                return False
        else:
            self.last_order_time = self._current_timestamp() 
            return True

    def current_api_call_timing(self):
        '''calculates the recommended time until next API call'''
        return 0.0

    def loop(self):
        self.accessor.wait_update()       
        self.paper.loop_functions()

    def wait_update(self):         
        self.paper.loop_functions()
        try:
            if self.own_timekeeper:
                self.timekeeper.increment_time()
            self.accessor.wait_update()
        except EOFError:
            raise
        except:
            logger.error("Unknown error occurred in backtest_interface.wait_update")
            raise
        return True

    def exit_exchange(self):
        pass