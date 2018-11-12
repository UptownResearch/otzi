from __future__ import absolute_import
from time import sleep
import sys
from datetime import datetime, timezone, timedelta
from os.path import getmtime
import random
import requests
import atexit
import signal
import json
import base64
import uuid

# Find code directory relative to our directory
from os.path import dirname, abspath, join
import sys
THIS_DIR = dirname(__file__)
CODE_DIR = abspath(join(THIS_DIR, '..', '..' ))
sys.path.append(CODE_DIR)

from market_maker import bitmex
#from market_maker.settings import settings
from market_maker.utils import  constants, errors, math
#from market_maker import paper_trading
import market_maker.paper_trading as paper_trading
#import paper_trading

from market_maker.backtest.bitmexbacktest import BitMEXbacktest

import logging


#
# Helpers
#
logger = logging.getLogger("root")

compare_logger = logging.getLogger("PAPERTRADING")




class ExchangeInterface:
    def __init__(self, dry_run=False, settings = None, logger="orders"):
        self.dry_run = dry_run
        # let's only use the symbol from the settings
        #if len(sys.argv) > 1:
        #    self.symbol = sys.argv[1]
        #else:
        #    self.symbol = self.settings.SYMBOL
        self.settings = settings
        self.symbol = self.settings.SYMBOL
        if self.settings.BACKTEST:
            self.bitmex = BitMEXbacktest( settings = self.settings)
        else:
            self.bitmex = bitmex.BitMEX(base_url=self.settings.BASE_URL, symbol=self.symbol,
                                    apiKey=self.settings.API_KEY, apiSecret=self.settings.API_SECRET,
                                    orderIDPrefix=self.settings.ORDERID_PREFIX, postOnly=self.settings.POST_ONLY,
                                    settings = self.settings, timeout=self.settings.TIMEOUT)
        if self.settings.PAPERTRADING:
            self.paper = paper_trading.PaperTrading(settings=self.settings, logger=logger)
            self.paper.provide_exchange(self.bitmex)
            self.paper.reset()
        self.orderIDPrefix=self.settings.ORDERID_PREFIX
        self.rate_limit  = 1
        self.rate_limit_remaining = 0
        self.last_order_time = None
        self.live_orders = []

    def cancel_order(self, order):
        tickLog = self.get_instrument()['tickLog']
        if self.settings.PAPERTRADING:
            logger.info("Canceling: %s %d @ %.*f" % (order['side'], order['orderQty'], tickLog, order['price']))
            return self.paper.cancel_order(order['orderID'])

        logger.info("Canceling: %s %d @ %.*f" % (order['side'], order['orderQty'], tickLog, order['price']))
        while True:
            try:
                self.bitmex.cancel(order['orderID'])
                sleep(self.settings.API_REST_INTERVAL)
            except ValueError as e:
                logger.info(e)
                sleep(self.settings.API_ERROR_INTERVAL)
            else:
                break
        new_live_orders = []
        for c_order in self.live_orders:
            if 'orderID' in c_order and \
                c_order['orderID'] != order['orderID']:
                new_live_orders.append(c_order)
        self.live_orders = new_live_orders

    def cancel_all_orders(self):
        if self.dry_run and self.settings.PAPERTRADING == False:
            return
        if self.settings.PAPERTRADING:
            logger.info("Resetting current position. Canceling all existing orders.")
            return self.paper.cancel_all_orders()
        logger.info("Resetting current position. Canceling all existing orders.")
        tickLog = self.get_instrument()['tickLog']
        # In certain cases, a WS update might not make it through before we call this.
        # For that reason, we grab via HTTP to ensure we grab them all.
        orders = self.bitmex.http_open_orders()
        for order in orders:
            logger.info("Canceling: %s %d @ %.*f" % (order['side'], order['orderQty'], tickLog, order['price']))

        orderIDs = [order['orderID'] for order in orders]
        if len(orders):
            self.bitmex.cancel(orderIDs)

        new_live_orders = []
        for c_order in self.live_orders:
            if 'orderID' in c_order and \
                c_order['orderID'] not in orderIDs:
                new_live_orders.append(c_order)
        self.live_orders = new_live_orders

        #sleep(self.settings.API_REST_INTERVAL)


    def get_portfolio(self):
        contracts = self.settings.CONTRACTS
        portfolio = {}
        for symbol in contracts:
            if self.settings.PAPERTRADING:
                position = self.paper.get_position(symbol=symbol)
            else:
                position = self.bitmex.position(symbol=symbol)
            instrument = self.bitmex.instrument(symbol=symbol)

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
        if self.settings.compare is not True:
            if symbol is None:
                symbol = self.symbol

            if self.settings.PAPERTRADING:
                return self.paper.current_contract()

            return self.get_position(symbol)['currentQty']
        else:
            if symbol is None:
                symbol = self.symbol

            
            return self.bitmex.position(symbol)['currentQty'], self.paper.current_contract()

    def get_instrument(self, symbol=None):
        if symbol is None:
            symbol = self.symbol
        return self.bitmex.instrument(symbol)

    def get_margin(self):
        if self.settings.compare is not True:

            if self.dry_run and self.settings.PAPERTRADING == False:
                return {'marginBalance': float(self.settings.DRY_BTC), 'availableFunds': float(self.settings.DRY_BTC)}

            if self.settings.PAPERTRADING:
                return self.paper.get_funds()

            return self.bitmex.funds()
        else:
            
            return self.bitmex.funds(), self.paper.get_funds()

    def get_orders(self):
        if self.dry_run and self.settings.PAPERTRADING == False:
            return []
        if self.settings.PAPERTRADING:
            return self.paper.get_orders()
        #orders = self.bitmex.open_orders()
        self._converge_open_orders()
        return self.live_orders

    def _converge_open_orders(self):
        orders = self.bitmex.open_orders() 
        time = self._current_timestamp() 
        new_live_orders = []
        for order in self.live_orders:
            matched_order = [o for o in orders if \
                                o["clOrdID"] == order["clOrdID"]]
            if len(matched_order) > 0:
                new_live_orders.append(matched_order[0])
            else:
                #let's keep local live orders around for only 5 seconds
                if 'submission_time' in order and \
                    time  > order['submission_time'] + 5:
                        continue
                new_live_orders.append(order)
        self.live_orders = new_live_orders

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
        if self.settings.compare is not True:
            if symbol is None:
                symbol = self.symbol

            if self.settings.PAPERTRADING:
                return self.paper.get_position(symbol)

            return self.bitmex.position(symbol)
        else:
            if symbol is None:
                symbol = self.symbol

            
            return self.bitmex.position(symbol), self.paper.get_position(symbol)

    def get_ticker(self, symbol=None):
        if symbol is None:
            symbol = self.symbol
        return self.bitmex.ticker_data(symbol)

    def is_open(self):
        """Check that websockets are still open."""
        return not self.bitmex.ws.exited

    def check_market_open(self):
        instrument = self.get_instrument()
        if instrument["state"] != "Open" and instrument["state"] != "Closed":
            raise errors.MarketClosedError("The instrument %s is not open. State: %s" %
                                           (self.symbol, instrument["state"]))

    def check_if_orderbook_empty(self):
        """This function checks whether the order book is empty"""
        instrument = self.get_instrument()
        if instrument['midPrice'] is None:
            raise errors.MarketEmptyError("Orderbook is empty, cannot quote")

    def amend_bulk_orders(self, orders):
        self.last_order_time = self._current_timestamp() 
        if self.settings.PAPERTRADING:
            self.paper.cancel_all_orders()
            self.paper.track_orders_created(orders)
        if self.settings.compare is not True:

            if self.dry_run and self.settings.PAPERTRADING == False:
                return orders

            if self.settings.PAPERTRADING:
                return orders

            return self.bitmex.amend_bulk_orders(orders)
        else:

            return self.bitmex.amend_bulk_orders(orders), orders

    def _generate_clOrdID(self):
        return self.orderIDPrefix + base64.b64encode(uuid.uuid4().bytes).decode('utf8').rstrip('=\n')

    def create_bulk_orders(self, orders):
        self.last_order_time = self._current_timestamp() 
        for order in orders:
            order['clOrdID'] = self._generate_clOrdID()
            order['submission_time'] = self.last_order_time
        if self.dry_run:
            return orders  
        
        # Rate limit same-side submission of orders 
        MIN_TIME_BETWEEN_ORDERS = .5
        acceptable_orders = []
        for order in orders:
            delete = False
            for e_order in self.live_orders:
                if order['side'] == e_order['side'] and \
                    order['submission_time'] < e_order['submission_time'] + \
                    MIN_TIME_BETWEEN_ORDERS:
                        logger.warn("Rejected order: %s" % json.dumps(order))
                        delete = True
            if not delete:
                acceptable_orders.append(order)

        if self.settings.BACKTEST:
            self.paper.track_orders_created(acceptable_orders)
            self.live_orders.extend(acceptable_orders)
            return acceptable_orders 
        else:
            self.live_orders.extend(acceptable_orders)
            return self.bitmex.create_bulk_orders(acceptable_orders)

    def cancel_bulk_orders(self, orders):
        self.last_order_time = self._current_timestamp() 
        if self.settings.compare is not True:
            if self.dry_run and self.settings.PAPERTRADING == False:
                return orders

            if self.settings.PAPERTRADING:
                return orders

            return self.bitmex.cancel([order['orderID'] for order in orders])
        else:

            return self.bitmex.cancel([order['orderID'] for order in orders])

    def recent_trades(self):
        return self.bitmex.recent_trades()

    def market_deep(self):
        return self.bitmex.market_depth("x")

    def current_timestamp(self):
        return self.bitmex.current_timestamp().replace(tzinfo=timezone.utc).timestamp()

    def contracts_this_run(self):

        if self.dry_run and self.settings.PAPERTRADING == False and self.settings.compare is not True:
            self.get_delta()

        if self.settings.PAPERTRADING or self.settings.compare:
           return self.paper.contract_traded_this_run()

        return 0

    def _current_timestamp(self):
        return self.bitmex.current_timestamp().replace(tzinfo=timezone.utc).timestamp()

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
        if self.rate_limit == 1:
            #have not received rate limit, default to 1 second
            return 1
        elif self.rate_limit_remaining < 1:
            # need to wait until reset time, it appears
            return self.rate_limit_reset - self._current_timestamp() 
        else:
            time_till_reset = self.rate_limit_reset - self._current_timestamp()           
            return  float(time_till_reset) / self.rate_limit_remaining


    def loop(self):
        self.bitmex.wait_update()
        (self.rate_limit, self.rate_limit_remaining, self.rate_limit_reset) = \
            self.bitmex.rate_limits()
        if self.settings.PAPERTRADING or self.settings.compare:
            self.paper.loop_functions()

    def wait_update(self):         
        if self.settings.PAPERTRADING or self.settings.compare:
            self.paper.loop_functions()
        (self.rate_limit, self.rate_limit_remaining, self.rate_limit_reset) = \
            self.bitmex.rate_limits()
        try:
            self.bitmex.wait_update()
        except EOFError:
            raise
        except:
            logger.error("Unknown error occurred in bitmex.wait_update")
            raise
        return True

    def exit_exchange(self):
        self.bitmex.exit()