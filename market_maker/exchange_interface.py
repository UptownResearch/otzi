from __future__ import absolute_import
from time import sleep
import sys
from datetime import datetime
from os.path import getmtime
import random
import requests
import atexit
import signal
import json
import base64
import uuid

from market_maker import bitmex
from market_maker.settings import settings
from market_maker.utils import log, constants, errors, math
from market_maker import paperless_tracker

from market_maker.backtest.bitmexbacktest import BitMEXbacktest

import logging


# Used for reloading the bot - saves modified times of key files
import os
watched_files_mtimes = [(f, getmtime(f)) for f in settings.WATCHED_FILES]


#
# Helpers
#
logger = logging.getLogger("root")

compare_logger = logging.getLogger("paperless")




class ExchangeInterface:
    def __init__(self, dry_run=False):
        self.dry_run = dry_run
        if len(sys.argv) > 1:
            self.symbol = sys.argv[1]
        else:
            self.symbol = settings.SYMBOL
        if settings.BACKTEST:
            self.bitmex = BitMEXbacktest(base_url=settings.BASE_URL, symbol=self.symbol,
                                    apiKey=settings.API_KEY, apiSecret=settings.API_SECRET,
                                    orderIDPrefix=settings.ORDERID_PREFIX, postOnly=settings.POST_ONLY,
                                    timeout=settings.TIMEOUT)
        else:
            self.bitmex = bitmex.BitMEX(base_url=settings.BASE_URL, symbol=self.symbol,
                                    apiKey=settings.API_KEY, apiSecret=settings.API_SECRET,
                                    orderIDPrefix=settings.ORDERID_PREFIX, postOnly=settings.POST_ONLY,
                                    timeout=settings.TIMEOUT)
        if settings.paperless:
            pp_tracker = paperless_tracker.paperless_tracker.getInstance()
            pp_tracker.provide_exchange(self.bitmex)
        self.orderIDPrefix=settings.ORDERID_PREFIX
        self.rate_limit  = 1
        self.rate_limit_remaining = 0
        self.last_order_time = None

    def cancel_order(self, order):
        if settings.compare is not True:
            tickLog = self.get_instrument()['tickLog']
            if settings.paperless:
                pp_tracker = paperless_tracker.paperless_tracker.getInstance()
                logger.info("Canceling: %s %d @ %.*f" % (order['side'], order['orderQty'], tickLog, order['price']))
                return pp_tracker.cancel_order(order['orderID'])

            logger.info("Canceling: %s %d @ %.*f" % (order['side'], order['orderQty'], tickLog, order['price']))
            while True:
                try:
                    self.bitmex.cancel(order['orderID'])
                    sleep(settings.API_REST_INTERVAL)
                except ValueError as e:
                    logger.info(e)
                    sleep(settings.API_ERROR_INTERVAL)
                else:
                    break
        else:
            tickLog = self.get_instrument()['tickLog']

            pp_tracker = paperless_tracker.paperless_tracker.getInstance()
            pp_tracker.cancel_order(order['orderID'])
            compare_logger.info("Canceling: %s %d @ %.*f" % (order['side'], order['orderQty'], tickLog, order['price']))

            logger.info("Canceling: %s %d @ %.*f" % (order['side'], order['orderQty'], tickLog, order['price']))
            while True:
                try:
                    self.bitmex.cancel(order['orderID'])
                    sleep(settings.API_REST_INTERVAL)
                except ValueError as e:
                    logger.info(e)
                    sleep(settings.API_ERROR_INTERVAL)
                else:
                    break

    def cancel_all_orders(self):
        if settings.compare is not True:
            if self.dry_run and settings.paperless == False:
                return

            if settings.paperless:
                pp_tracker = paperless_tracker.paperless_tracker.getInstance()
                logger.info("Resetting current position. Canceling all existing orders.")
                return pp_tracker.cancel_all_orders()

            logger.info("Resetting current position. Canceling all existing orders.")
            tickLog = self.get_instrument()['tickLog']

            # In certain cases, a WS update might not make it through before we call this.
            # For that reason, we grab via HTTP to ensure we grab them all.
            orders = self.bitmex.http_open_orders()

            for order in orders:
                logger.info("Canceling: %s %d @ %.*f" % (order['side'], order['orderQty'], tickLog, order['price']))

            if len(orders):
                self.bitmex.cancel([order['orderID'] for order in orders])



            sleep(settings.API_REST_INTERVAL)
        else:

            pp_tracker = paperless_tracker.paperless_tracker.getInstance()
            compare_logger.info("Resetting current position. Canceling all existing orders.")
            pp_tracker.cancel_all_orders()

            logger.info("Resetting current position. Canceling all existing orders.")
            tickLog = self.get_instrument()['tickLog']

            # In certain cases, a WS update might not make it through before we call this.
            # For that reason, we grab via HTTP to ensure we grab them all.
            orders = self.bitmex.http_open_orders()

            for order in orders:
                logger.info("Canceling: %s %d @ %.*f" % (order['side'], order['orderQty'], tickLog, order['price']))

            if len(orders):
                self.bitmex.cancel([order['orderID'] for order in orders])

            sleep(settings.API_REST_INTERVAL)

    def get_portfolio(self):
        contracts = settings.CONTRACTS
        portfolio = {}
        for symbol in contracts:
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
        if settings.compare is not True:
            if symbol is None:
                symbol = self.symbol

            if settings.paperless:
                pp_tracker = paperless_tracker.paperless_tracker.getInstance()
                return pp_tracker.current_contract()

            return self.get_position(symbol)['currentQty']
        else:
            if symbol is None:
                symbol = self.symbol

            pp_tracker = paperless_tracker.paperless_tracker.getInstance()

            return self.bitmex.position(symbol)['currentQty'], pp_tracker.current_contract()

    def get_instrument(self, symbol=None):
        if symbol is None:
            symbol = self.symbol
        return self.bitmex.instrument(symbol)

    def get_margin(self):
        if settings.compare is not True:

            if self.dry_run and settings.paperless == False:
                return {'marginBalance': float(settings.DRY_BTC), 'availableFunds': float(settings.DRY_BTC)}

            if settings.paperless:
                pp_tracker = paperless_tracker.paperless_tracker.getInstance()
                return pp_tracker.get_funds()

            return self.bitmex.funds()
        else:
            pp_tracker = paperless_tracker.paperless_tracker.getInstance()

            return self.bitmex.funds(), pp_tracker.get_funds()

    def get_orders(self):
        if settings.compare is not True:
            if self.dry_run and settings.paperless == False:
                return []

            if settings.paperless:
                pp_tracker = paperless_tracker.paperless_tracker.getInstance()
                return pp_tracker.get_orders()

            return self.bitmex.open_orders()
        else:
            pp_tracker = paperless_tracker.paperless_tracker.getInstance()

            return self.bitmex.open_orders()

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
        if settings.compare is not True:
            if symbol is None:
                symbol = self.symbol

            if settings.paperless:
                pp_tracker = paperless_tracker.paperless_tracker.getInstance()
                return pp_tracker.get_position(symbol)

            return self.bitmex.position(symbol)
        else:
            if symbol is None:
                symbol = self.symbol

            pp_tracker = paperless_tracker.paperless_tracker.getInstance()

            return self.bitmex.position(symbol), pp_tracker.get_position(symbol)

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
        self.last_order_time = self.bitmex.current_timestamp().timestamp() 
        if settings.paperless:
            pp_tracker = paperless_tracker.paperless_tracker.getInstance()
            pp_tracker.cancel_all_orders()
            pp_tracker.track_orders_created(orders)
        if settings.compare is not True:

            if self.dry_run and settings.paperless == False:
                return orders

            if settings.paperless:
                return orders

            return self.bitmex.amend_bulk_orders(orders)
        else:

            return self.bitmex.amend_bulk_orders(orders), orders

    def create_bulk_orders(self, orders):
        self.last_order_time = self.bitmex.current_timestamp().timestamp() 
        for order in orders:
            order['clOrdID'] = self.orderIDPrefix + base64.b64encode(uuid.uuid4().bytes).decode('utf8').rstrip('=\n')
        if settings.compare is not True:
            if self.dry_run and settings.paperless == False:
                return orders

            if settings.paperless:
                ppl_tracker = paperless_tracker.paperless_tracker.getInstance()
                ppl_tracker.track_orders_created(orders)
                return orders 

            return self.bitmex.create_bulk_orders(orders)
        else:
            ppl_tracker = paperless_tracker.paperless_tracker.getInstance()
            ppl_tracker.track_orders_created(orders)

            return self.bitmex.create_bulk_orders(orders)

    def cancel_bulk_orders(self, orders):
        self.last_order_time = self.bitmex.current_timestamp().timestamp() 
        if settings.compare is not True:
            if self.dry_run and settings.paperless == False:
                return orders

            if settings.paperless:
                return orders

            return self.bitmex.cancel([order['orderID'] for order in orders])
        else:

            return self.bitmex.cancel([order['orderID'] for order in orders])

    def recent_trades(self):
        return self.bitmex.recent_trades()

    def market_deep(self):
        return self.bitmex.market_depth("x")

    def current_timestamp(self):
        return self.bitmex.current_timestamp()

    def contracts_this_run(self):

        if self.dry_run and settings.paperless == False and settings.compare is not True:
            self.get_delta()

        if settings.paperless or settings.compare:
            pp_tracker = paperless_tracker.paperless_tracker.getInstance()
            return pp_tracker.contract_traded_this_run()

        return 0

    def ok_to_enter_order(self):
        if self.last_order_time:
            time_since_last = self.bitmex.current_timestamp().timestamp() - self.last_order_time 
            # force a 1 second wait for now
            if time_since_last > max(self.current_api_call_timing(), 1):
                self.last_order_time = self.bitmex.current_timestamp().timestamp() 
                return True
            else:
                return False
        else:
            self.last_order_time = self.bitmex.current_timestamp().timestamp() 
            return True


    def current_api_call_timing(self):
        '''calculates the recommended time until next API call'''
        if self.rate_limit == 1:
            #have not received rate limit, default to 1 second
            return 1
        elif self.rate_limit_remaining < 1:
            # need to wait until reset time, it appears
            return self.rate_limit_reset - self.bitmex.current_timestamp().timestamp() 
        else:
            time_till_reset = self.rate_limit_reset - self.bitmex.current_timestamp().timestamp()           
            return  float(time_till_reset) / self.rate_limit_remaining


    def loop(self):
        self.bitmex.wait_update()
        (self.rate_limit, self.rate_limit_remaining, self.rate_limit_reset) = \
            self.bitmex.rate_limits()
        if settings.paperless or settings.compare:
            pp_tracker = paperless_tracker.paperless_tracker.getInstance()
            pp_tracker.loop_functions()

    def wait_update(self):         
        if settings.paperless or settings.compare:
            pp_tracker = paperless_tracker.paperless_tracker.getInstance()
            pp_tracker.loop_functions()
        (self.rate_limit, self.rate_limit_remaining, self.rate_limit_reset) = \
            self.bitmex.rate_limits()
        self.bitmex.wait_update()
        return True