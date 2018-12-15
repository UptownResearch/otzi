import sys
from os.path import dirname, abspath, join

THIS_DIR = dirname(__file__)
CODE_DIR = abspath(THIS_DIR)
sys.path.insert(0, CODE_DIR)

from market_maker.lxdx import auth_lxdx
from market_maker.lxdx import wslxdx
import logging

class lxdxInterface:

    def __init__(self, settings = {}):
        self.settings = {}
        self.logger = logging.getLogger('root')
        self.symbol = self.settings.get('SYMBOL', 'btc-tusd')

        # Set up account and data feed
        self.account = auth_lxdx.AccountConnection(settings=settings)
        self.account.connect()
        self.feed = wslxdx.wsLXDX()
        self.feed.connect()

    def exit(self):
        self.account.exit()
        self.feed.exit()

    def get_instrument(self, symbol=None):
        if symbol is None:
            symbol = self.symbol
        products = self.account.get_products()
        if not symbol in products:
            return {}
        instrument = products[symbol]
        instrument['tickLog'] = int(instrument["quotation_tick_size_decimals"])
        instrument['tickSize'] = 1.0 / 10**instrument['tickLog']
        return instrument

    def get_ticker(self, symbol=None):
        if symbol is None:
            symbol = self.symbol
        return self.feed.get_ticker(symbol)

    def get_orders(self, symbol=None):
        if symbol is None:
            symbol = self.symbol
        orders = self.account.get_orders()['orders']
        result = []
        for order in orders:
            if order['symbol'] == symbol:
                order['side'] = 'Buy' if order['side'] == 'buy' else 'Sell'
                order['orderID'] = order['order_id']
                # ccxt provides 'open', 'closed', 'canceled'
                order['ordStatus'] = 'Open'
                order['orderQty'] = order['qty']
                result.append(order)
        return orders

    def create_order(self, order):
        if 'amount' not in order:
            amount = order['orderQty']
        else:
            amount = order['amount']
        if 'symbol' not in order:
            symbol = self.symbol
        else:
            symbol = order['symbol']

        if 'type' not in order:
            type = 'limit'
        else:
            type = order['type']
        order['side'] = order['side'].lower()
        self.logger.info("Creating Order: %s %d @ %.2f" % (
             order['side'], order['orderQty'], order['price']))
        return self.account.place(order['price'],
                                  amount,
                                  symbol,
                                  order['side'],
                                  time_in_force='DAY',
                                  type = type,
                                  post_only=True)

    def create_bulk_orders(self, orders):
        returned = []
        for order in orders:
            returned.append(self.create_order(order))
        return returned

    def amend_bulk_orders(self, orders):
        for order in orders:
            # Cancel Order
            self.cancel_order(order)
            #Create new Order
            the_keys = ['side', 'orderQty', 'price']
            new_order = dict((key, value) for key, value in \
                                   order.items() if key in the_keys)
            self.create_order(new_order)

    def cancel_order(self, order):
        self.logger.info(
            "Canceling %s: %s %d @ %.2f" % (order['orderID'], order['side'], order['orderQty'], order['price']))
        try:
            self.account.cancel(order['orderID'], self.symbol)
        except:
            self.logger.warning("Order %s not found. Ignoring." % order['orderID'])

    def cancel_all_orders(self):
        orders = self.account.get_orders()['orders']
        for order in orders:
            self.account.cancel(order['order_id'], order['symbol'])

    def get_position(self, symbol=None):
        # return dictionary with keys including 'avgCostPrice',
        # 'avgEntryPrice'
        if symbol is None:
            symbol = self.symbol
        account = self._get_base_currency(symbol)
        position_array = self.account.get_position()['balances']
        if account not in position_array:
            return {'currentQty': 0.0, 'avgCostPrice':0.0, 'avgEntryPrice': 0.0}
        else:
            position_val = position_array[account]
            position = {'currentQty': position_val}
            position['avgCostPrice'] = 0
            position['avgEntryPrice'] = 0
            return position

    def get_delta(self, symbol=None):
        if symbol is None:
            symbol = self.symbol
        return self.get_position(symbol)['currentQty']

    def market_deep(self, symbol=None):
        if symbol is None:
            symbol = self.symbol
        return self.get_orderbook(symbol)

    def get_orderbook(self, symbol=None):
        if symbol is None:
            symbol = self.symbol
        return self.feed.get_orderbook(symbol)

    def recent_trades(self, symbol=None):
        if symbol is None:
            symbol = self.symbol
        trades = self.feed.recent_trades(symbol)
        for trade in trades:
            trade['price'] = trade['px']
            trade['size'] = trade['qty']
            trade['side'] =  "".join((trade['s'][0].upper(),trade['s'][1:]))
            trade['timestamp'] = trade['t']
        return trades

    def get_highest_buy(self):
        buys = [o for o in self.get_orders() if o['side'].lower() == 'buy']
        if not len(buys):
            return {'price': -2**32}
        highest_buy = max(buys or [], key=lambda o: o['price'])
        return highest_buy if highest_buy else {'price': -2**32}

    def get_lowest_sell(self):
        sells = [o for o in self.get_orders() if o['side'].lower() == 'sell']
        if not len(sells):
            return {'price': 2**32}
        lowest_sell = min(sells or [], key=lambda o: o['price'])
        return lowest_sell if lowest_sell else {'price': 2**32}  # ought to be enough for anyone

    def check_if_orderbook_empty(self):
        orderbook = self.get_orderbook()
        if len(orderbook['bids']) == 0 and len(orderbook['asks']) == 0:
            raise Exception("Orderbook is empty, cannot quote")

    def check_market_open(self):
        #exchange.load_markets()
        symbol = self.symbol
        markets = self.get_instrument()
        if markets == {}:
            raise Exception("Market %s is not open!" % symbol)
        else:
            return True

    def is_open(self):
        return self.check_market_open()

    def exit_exchange(self):
        # CCXT doesn't require an explicit shutdown (or so it appears).
        return True

    def wait_update(self):
        # No loop to check for updates
        return True

    def ok_to_enter_order(self):
        # Rate Limiting code is yet to be implemented
        return True


    ### Not currently applicable:

    def get_margin(self):
        # return dictionary with keys including: marginBalance
        return {'marginBalance': 0.0}

    def calc_delta(self):
        # returns dictionary with keys including: 'spot'
        return {'spot': 0.0}

    def contracts_this_run(self):
        return 0.0


    ################
    # Private Functions
    ################

    def _get_base_currency(self, pair):
        return pair.replace('-', '/').split('/')[0]