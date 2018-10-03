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
from market_maker.settings import settings
from market_maker.utils import log, errors
from market_maker import paper_trading
from market_maker.backtest.exchangepairaccessor import ExchangePairAccessor
from market_maker.backtest.timekeeper import Timekeeper
#
# Helpers
#
logger = logging.getLogger("root")
compare_logger = logging.getLogger("paperless")


class BacktestInterface:
    def __init__(self, timekeeper = None, trades_filename = "", L2orderbook_filename = "",
                name = ""):
        self.paper = paper_trading.PaperTrading()
        if timekeeper == None:
            self.timekeeper = Timekeeper()
            self.own_timekeeper = True
        else:
            self.own_timekeeper = False
            self.timekeeper = timekeeper
        self.accessor = ExchangePairAccessor(self.timekeeper, trades_filename, L2orderbook_filename, name)        
        self.paper.provide_exchange(self.accessor)
        self.paper.reset()
        self.orderIDPrefix="BT_"
        if self.own_timekeeper:
            self.timekeeper.initialize()

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
        raise NotImplementedError("get_portfolio not implemented in backtest_interface")

    def calc_delta(self):
        raise NotImplementedError("calc_delta not implemented in backtest_interface")

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
        if self.accessor.market_depth("") == []:
            raise errors.MarketEmptyError("Orderbook is empty, cannot quote")

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
        raise NotImplementedError("current_api_call_timing not implemented in backtest_interface")

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
            print("Unknown Error occurred while running.")
            raise
        return True

    def exit_exchange(self):
        pass