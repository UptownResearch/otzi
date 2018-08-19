import sys

from market_maker.market_maker import OrderManager, logger 
from market_maker.settings import settings
from market_maker.utils import log, constants, errors, math

#
# Helpers
#

import logging

# create file handler which logs even debug messages
if settings.ROOT_LOG:
    import datetime
    file_location = settings.ROOT_LOG_LOCATION + f"{datetime.datetime.now():%Y-%m-%d}" + ".log"
    fh = logging.FileHandler(file_location, mode='a')
    formatter = logging.Formatter(fmt='%(asctime)s - %(levelname)s - %(module)s - %(message)s')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
        rootlogger.addHandler(fh)
    rootlogger.setLevel(logging.DEBUG)
    level = logging.getLogger().getEffectiveLevel()
    rootlogger.info('Root at level %s - Logging to file: %s' % (level, file_location))



class CustomOrderManager(OrderManager):
    """A sample order manager for implementing your own custom strategy"""

    
    def get_ticker(self):
        ticker = self.exchange.get_ticker()
        tickLog = self.exchange.get_instrument()['tickLog']

        # Set up our buy & sell positions as the smallest possible unit above and below the current spread
        # and we'll work out from there. That way we always have the best price but we don't kill wide
        # and potentially profitable spreads.
        self.start_position_buy = ticker["buy"] + self.instrument['tickSize']
        self.start_position_sell = ticker["sell"] - self.instrument['tickSize']

        # If we're maintaining spreads and we already have orders in place,
        # make sure they're not ours. If they are, we need to adjust, otherwise we'll
        # just work the orders inward until they collide.
        if settings.MAINTAIN_SPREADS:
            if ticker['buy'] == self.exchange.get_highest_buy()['price']:
                self.start_position_buy = ticker["buy"]
            if ticker['sell'] == self.exchange.get_lowest_sell()['price']:
                self.start_position_sell = ticker["sell"]

        # Back off if our spread is too small.
        if self.start_position_buy * (1.00 + settings.MIN_SPREAD) > self.start_position_sell:
            self.start_position_buy *= (1.00 - (settings.MIN_SPREAD / 2))
            self.start_position_sell *= (1.00 + (settings.MIN_SPREAD / 2))

        
        # Midpoint, used for simpler order placement.
        self.start_position_mid = ticker["mid"]

        # Add leans to take the position into account
        # note prices before leans


        # calculate offset for inventory
        if settings.compare:
            position, trackerpos = self.exchange.get_delta()
        else:
            position = self.exchange.get_delta()
        if abs(position) >= settings.MAX_OR_MIN_POSITION:          
            logger.info("Position exceeds limits: %s" % (position,))

        position_skew = position / (settings.MAX_OR_MIN_POSITION )
        ask_skew = int((settings.QUOTE_RANGE/2.0) * (1.0 - position_skew)) * self.instrument['tickSize']
        bid_skew = int((settings.QUOTE_RANGE/2.0) * (1.0 + position_skew)) * self.instrument['tickSize']
        logger.info('Leans: Bid: %.*f, Ask: %.*f' %
                (tickLog, bid_skew, tickLog, ask_skew))
        self.start_position_buy -= bid_skew
        self.start_position_sell += ask_skew

        # math.toNearest(start_position * (1 + settings.INTERVAL) ** index, self.instrument['tickSize']

        if position >= settings.MAX_POSITION:     
            self.start_position_sell = ticker["sell"] - self.instrument['tickSize']

        if position <= settings.MIN_POSITION: 
            self.start_position_buy = ticker["buy"] + self.instrument['tickSize']

        #log 
        logger.info(
            "%s Ticker: Buy: %.*f, Sell: %.*f" %
            (self.instrument['symbol'], tickLog, ticker["buy"], tickLog, ticker["sell"])
        )
        logger.info('Start Positions: Buy: %.*f, Sell: %.*f, Mid: %.*f' %
                    (tickLog, self.start_position_buy, tickLog, self.start_position_sell,
                     tickLog, self.start_position_mid))
        return ticker


    def place_orders(self) -> None:
        # implement your custom strategy here
        self.make_orders()
        #Invetory skew can be found in get_ticker()

        #buy_orders = []
        #sell_orders = []

        # populate buy and sell orders, e.g.
        # buy_orders.append({'price': 999.0, 'orderQty': 100, 'side': "Buy"})
        # sell_orders.append({'price': 1001.0, 'orderQty': 100, 'side': "Sell"})


        # Start with the example

        # Create orders from the outside in. This is intentional - let's say the inner order gets taken;
        # then we match orders from the outside in, ensuring the fewest number of orders are amended and only
        # a new order is created in the inside. If we did it inside-out, all orders would be amended
        # down and a new order would be created at the outside.

        '''
        for i in reversed(range(1, settings.ORDER_PAIRS + 1)):
            if not self.long_position_limit_exceeded():
                buy_orders.append( self.prepare_order(-i))
            if not self.short_position_limit_exceeded():
                sell_orders.append(self.prepare_order(i))        

        self.converge_orders(buy_orders, sell_orders)
        '''

    def make_orders(self) -> None:
        tickLog = self.exchange.get_instrument()['tickLog']
        to_amend = []
        to_create = []

        existing_orders = self.exchange.get_orders()

         {'price': price, 'orderQty': quantity, 'side': "Buy" if index < 0 else "Sell"}
         math.toNearest(start_position * (1 + settings.INTERVAL) ** index, self.instrument['tickSize'])
         self.start_position_buy
         self.start_position_sell

        if len(existing_orders) == 2:
            for order in existing_orders:
                if order['side'] == "Buy" and order['price'] != self.start_position_buy:
                    neworder = {'price':  self.start_position_buy, 'orderQty': settings.ORDER_START_SIZE, 'side': "Buy" }
                    to_amend.append(neworder)
                elif order['price'] != self.start_position_sell:
                    neworder = {'price':  self.start_position_sell, 'orderQty': settings.ORDER_START_SIZE, 'side': "Sell" }
                    to_amend.append(neworder)

            if len(to_amend) > 0:
                for amended_order in reversed(to_amend):
                    reference_order = [o for o in existing_orders if o['orderID'] == amended_order['orderID']][0]
                    logger.info("Amending %4s: %d @ %.*f to %d @ %.*f (%+.*f)" % (
                        amended_order['side'],
                        reference_order['leavesQty'], tickLog, reference_order['price'],
                        (amended_order['orderQty'] - reference_order['cumQty']), tickLog, amended_order['price'],
                        tickLog, (amended_order['price'] - reference_order['price'])
                    ))
                # This can fail if an order has closed in the time we were processing.
                # The API will send us `invalid ordStatus`, which means that the order's status (Filled/Canceled)
                # made it not amendable.
                # If that happens, we need to catch it and re-tick.
                try:
                    self.exchange.amend_bulk_orders(to_amend)
                except requests.exceptions.HTTPError as e:
                    errorObj = e.response.json()
                    if errorObj['error']['message'] == 'Invalid ordStatus':
                        logger.warn("Amending failed. Waiting for order data to converge and retrying.")
                        sleep(0.5)
                        return self.place_orders()
                    else:
                        logger.error("Unknown error on amend: %s. Exiting" % errorObj)
                        sys.exit(1)
        else if len(existing_orders) == 1:
            for order in existing_orders:
                side = "Buy" if order['side'] == "Sell" else "Sell"
                price = self.start_position_buy if order['side'] == "Sell" else self.start_position_sell
                neworder = {'price':  price, 'orderQty': settings.ORDER_START_SIZE, 'side': side }
                to_create.append(neworder)
        else:
            #cancel existing orders and create new ones
            self.exchange.cancel_all_orders()
            buyorder = {'price':  self.start_position_buy, 'orderQty': settings.ORDER_START_SIZE, 'side': "Buy" }
            sellorder = {'price':  self.start_position_sell, 'orderQty': settings.ORDER_START_SIZE, 'side': "Sell" }
            to_create.append(buyorder)
            to_create.append(sellorder)

        if len(to_create) > 0:
            logger.info("Creating %d orders:" % (len(to_create)))
            #compare_logger.info("Creating %d orders:" % (len(to_create)))
            for order in reversed(to_create):
                logger.info("%4s %d @ %.*f" % (order['side'], order['orderQty'], tickLog, order['price']))
                #compare_logger.info("%4s %d @ %.*f" % (order['side'], order['orderQty'], tickLog, order['price']))
            self.exchange.create_bulk_orders(to_create)


def run() -> None:
    order_manager = CustomOrderManager()
    #order_manager = OrderManager()

    # Try/except just keeps ctrl-c from printing an ugly stacktrace
    try:
        order_manager.run_loop()
    except (KeyboardInterrupt, SystemExit):
        sys.exit()


run()
# run python3 ./custom_strategy.py