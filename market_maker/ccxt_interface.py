import ccxt
import decimal
import logging
from ccxt.base.errors import OrderNotFound

testCredentials = {
            'apiKey': '46b32c0f5a32b7c263b4d966aebf995a',
            'secret': 'XB73Bo/E0v2gLSvPZNDhRdmqkBpJQ3DErXL60xEiu1OIdC1Ddx9zVkX64mjMPixThsT1oO/4NZtwsSL53jiTNA==',
            'password': 't5crbhy2r4',
            'timeout': 30000,
            'enableRateLimit': True,
        }

class ccxtInterface:
    def __init__(self, dry_run=False, settings={}, logger="orders",
                 exchange = 'gdax', credentials=testCredentials):
        self.dry_run = dry_run
        self.settings = settings
        self.symbol = self.settings.get('SYMBOL', 'BTC/USD')
        self.exchange_id = exchange
        exchange_class = getattr(ccxt, self.exchange_id)
        self.exchange = exchange_class(credentials)
        self.TEST_EXCHANGE = self.settings.get('USE_TEST_EXCHANGE', True)
        if self.TEST_EXCHANGE:
            self.exchange.urls['api'] = self.exchange.urls['test']
        self.logger = logging.getLogger("root")

    def get_instrument(self, symbol=None):
        if symbol is None:
            symbol = self.symbol
        markets = self.exchange.load_markets()
        instrument = markets[symbol]
        tickSize = instrument['info']['quote_increment']
        instrument['tickLog'] = decimal.Decimal(str(tickSize)).as_tuple().exponent * -1
        instrument['tickSize'] = float(tickSize)
        return instrument

    def get_ticker(self, symbol=None):
        if symbol is None:
            symbol = self.symbol
        ticker = self.exchange.fetchTicker(symbol)
        ticker['buy'] = float(ticker['info']['bid'])
        ticker['sell'] = float(ticker['info']['ask'])
        ticker['mid'] = (ticker['buy'] + ticker['sell'])/2
        return ticker

    def get_orders(self, symbol=None):
        # expects each order to have 'side', 'orderID',
        # 'price', 'orderQty', 'ordStatus'
        # 'submission_time' -- not needed
        # 'side' - is 'Buy' or 'Sell'
        # 'ordStatus' - 'Filled', 'Canceled', 'New'
        if symbol is None:
            symbol = self.symbol
        orders = self.exchange.fetchOpenOrders(symbol)
        for order in orders:
            order['side'] = 'Buy' if order['side'] == 'buy' else 'Sell'
            order['orderID'] = order['id']
            # ccxt provides 'open', 'closed', 'canceled'
            order['ordStatus'] = "".join((order['status'][0].upper(),order['status'][1:] ))
            order['ordStatus'] = 'Canceled' if order['ordStatus'] == 'Closed' else order['ordStatus']
            order['orderQty'] = order['amount']

        return orders

    def get_delta(self, symbol=None):
        if symbol is None:
            symbol = self.symbol
        return self.get_position(symbol)['currentQty']

    def get_position(self, symbol=None):
        # return dictionary with keys including 'avgCostPrice',
        # 'avgEntryPrice'
        if symbol is None:
            symbol = self.symbol
        account = self._get_base_currency(symbol)
        position_array = self.exchange.fetchBalance()['total']
        if account not in position_array:
            return {'currentQty': 0.0, 'avgCostPrice': 0.0, 'avgEntryPrice': 0.0}
        else:
            position_val = position_array[account]
            position = {'currentQty': position_val}
            position['avgCostPrice'] = 0
            position['avgEntryPrice'] = 0
            return position

    ### Not currently applicable:

    def get_margin(self):
        # return dictionary with keys including: marginBalance
        return {'marginBalance': 0.0}

    def calc_delta(self):
        # returns dictionary with keys including: 'spot'
        return {'spot': 0.0}

    def contracts_this_run(self):
        return 0.0

    #############################

    def market_deep(self, symbol=None):
        if symbol is None:
            symbol = self.symbol
        return self.get_orderbook(symbol)

    def get_orderbook(self, symbol=None):
        if symbol is None:
            symbol = self.symbol
        return self.exchange.fetchL2OrderBook ('BTC/USD')

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

    def recent_trades(self, symbol=None):
        if symbol is None:
            symbol = self.symbol
        return self.exchange.fetchTrades(symbol)

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
        if 'params' not in order:
            params = {}
        else:
            params = order['params']
        order['side'] = order['side'].lower()
        self.logger.info("Creating Order: %s %.2f @ %.2f" % (
             order['side'], order['orderQty'], order['price']))
        return self.exchange.createOrder(
                                    symbol,
                                    type,
                                    order['side'],
                                    amount,
                                    order['price'],
                                    params
                                    )

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
        self.logger.info("Canceling %s: %s %.2f @ %.2f" % (order['orderID'], order['side'], order['orderQty'], order['price']))
        try:
            self.exchange.cancelOrder(order['orderID'])
        except OrderNotFound:
            self.logger.warning("Order %s not found. Ignoring." % order['orderID'])

    def cancel_all_orders(self):
        orders = self.get_orders()
        for order in orders:
            self.cancel_order(order)

    def check_if_orderbook_empty(self):
        orderbook = self.get_orderbook()
        if len(orderbook['bids']) == 0 and len(orderbook['asks']) == 0:
            raise Exception("Orderbook is empty, cannot quote")

    def check_market_open(self):
        #exchange.load_markets()
        symbol = self.symbol
        markets = self.exchange.loadMarkets()
        if symbol not in markets or markets[symbol]['active'] is False:
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

    ################
    # Private Functions
    ################

    def _get_base_currency(self, pair):
        return pair.split('/')[0]
