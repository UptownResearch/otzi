from unittest.mock import MagicMock, patch, Mock
from unittest import TestCase
from market_maker.ccxt import ccxtInterface


class Test_Exchange_Interface(TestCase):

    def setUp(self):
        #self.auth_patch = patch.object(exchange_interface, 'AWS4Auth')
        #self.requests_patch = patch.object(exchange_interface, 'requests')
        #self.auth = self.auth_patch.start()
        #self.requests = self.requests_patch.start()
        pass

    def tearDown(self):
        #self.auth_patch.stop()
        #self.requests_patch.stop()
        pass

    def test_create_class(self):
        try:
            exchange = ccxtInterface()
        except Exception as e:
            print(e)
            assert False
        assert True

    def test_get_instrument(self):
        with patch.object(ccxtInterface, "__init__",
                          lambda x, **params: None):
            exchange = ccxtInterface()
            exchange.exchange = MagicMock()
            exchange.exchange.load_markets.return_value = {
                    'BTC/USD' : {'fee_loaded': False,
                 'percentage': True,
                 'tierBased': True,
                 'maker': 0.0,
                 'taker': 0.003,
                 'precision': {'amount': 8, 'price': 2},
                 'limits': {'amount': {'min': 0.001, 'max': 10000.0},
                  'price': {'min': 0.01, 'max': None},
                  'cost': {'min': None, 'max': None}},
                 'id': 'BTC-USD',
                 'symbol': 'BTC/USD',
                 'base': 'BTC',
                 'quote': 'USD',
                 'active': True,
                 'info': {'id': 'BTC-USD',
                  'base_currency': 'BTC',
                  'quote_currency': 'USD',
                  'base_min_size': '0.001',
                  'base_max_size': '10000',
                  'quote_increment': '0.01',
                  'display_name': 'BTC/USD',
                  'status': 'online',
                  'margin_enabled': True,
                  'status_message': None,
                  'min_market_funds': None,
                  'max_market_funds': None,
                  'post_only': False,
                  'limit_only': False,
                  'cancel_only': False}}
            }
            instrument = exchange.get_instrument('BTC/USD')
            assert 'tickLog' in instrument
            assert instrument['tickLog'] == 2

    def test_get_ticker(self):
        with patch.object(ccxtInterface, "__init__", lambda x, **params: None):
            exchange = ccxtInterface()
            exchange.exchange = MagicMock()
            exchange.exchange.fetchTicker.return_value = {'symbol': 'BTC/USD',
                 'timestamp': 1543268883923,
                 'datetime': '2018-11-26T21:48:03.923Z',
                 'high': None,
                 'low': None,
                 'bid': 6543.14,
                 'bidVolume': None,
                 'ask': 6630.12,
                 'askVolume': None,
                 'vwap': None,
                 'open': None,
                 'close': 6543.14,
                 'last': 6543.14,
                 'previousClose': None,
                 'change': None,
                 'percentage': None,
                 'average': None,
                 'baseVolume': 70.80099681,
                 'quoteVolume': None,
                 'info': {'trade_id': 2180090,
                  'price': '6543.14000000',
                  'size': '2.18100000',
                  'bid': '6543.14',
                  'ask': '6630.12',
                  'volume': '70.80099681',
                  'time': '2018-11-26T21:48:03.923000Z'}}
            ticker = exchange.get_ticker('BTC/USD')
            assert 'mid' in ticker
            assert 'buy' in ticker
            assert 'sell' in ticker
            assert ticker['mid'] == (6543.14 + 6630.12)/2

    def test_get_orders(self):
        with patch.object(ccxtInterface, "__init__", lambda x, **params: None):
            exchange = ccxtInterface()
            exchange.exchange = MagicMock()
            exchange.exchange.fetchOrders.return_value = [
                { 'id': '9dfe9ad7-601f-4926-a893-4095e769b65b',
                  'info': {'id': '9dfe9ad7-601f-4926-a893-4095e769b65b',
                   'price': '10000.00000000',
                   'size': '0.01000000',
                   'product_id': 'BTC-USD',
                   'side': 'sell',
                   'type': 'limit',
                   'time_in_force': 'GTC',
                   'post_only': False,
                   'created_at': '2018-12-04T22:34:55.158107Z',
                   'fill_fees': '0.0000000000000000',
                   'filled_size': '0.00000000',
                   'executed_value': '0.0000000000000000',
                   'status': 'open',
                   'settled': False},
                  'timestamp': 1543962895158,
                  'datetime': '2018-12-04T22:34:55.158Z',
                  'lastTradeTimestamp': None,
                  'status': 'closed',
                  'symbol': 'BTC/USD',
                  'type': 'limit',
                  'side': 'sell',
                  'price': 10000.0,
                  'cost': 0.0,
                  'amount': 0.01,
                  'filled': 0.0,
                  'remaining': 0.01,
                  'fee': {'cost': 0.0, 'currency': None, 'rate': None}}]
            orders = exchange.get_orders('BTC/USD')
            assert orders[0]['side'] == 'Sell'
            assert orders[0]['orderID'] == '9dfe9ad7-601f-4926-a893-4095e769b65b'
            assert orders[0]['ordStatus'] == 'Canceled'
            assert orders[0]['orderQty'] == 0.01

    def test_create_orders(self):
        with patch.object(ccxtInterface, "__init__", lambda x, **params: None):
            exchange = ccxtInterface()
            exchange.exchange = MagicMock()
            exchange.symbol = 'BTC/USD'
            exchange.logger = MagicMock()
            exchange.exchange.createOrder.return_value = {'id': 'b6fb529b-56e8-41a1-aa88-96957b061643',
                 'info': {'id': 'b6fb529b-56e8-41a1-aa88-96957b061643',
                  'price': '12000.00000000',
                  'size': '0.01000000',
                  'product_id': 'BTC-USD',
                  'side': 'sell',
                  'stp': 'dc',
                  'type': 'limit',
                  'time_in_force': 'GTC',
                  'post_only': False,
                  'created_at': '2018-12-05T22:45:26.824114Z',
                  'fill_fees': '0.0000000000000000',
                  'filled_size': '0.00000000',
                  'executed_value': '0.0000000000000000',
                  'status': 'pending',
                  'settled': False},
                 'timestamp': 1544049926824,
                 'datetime': '2018-12-05T22:45:26.824Z',
                 'lastTradeTimestamp': None,
                 'status': 'open',
                 'symbol': 'BTC/USD',
                 'type': 'limit',
                 'side': 'sell',
                 'price': 12000.0,
                 'cost': 0.0,
                 'amount': 0.01,
                 'filled': 0.0,
                 'remaining': 0.01,
                 'fee': {'cost': 0.0, 'currency': None, 'rate': None}}
            order = {
                'type': 'limit',
                'side': 'sell',
                'price': 12000.0,
                'orderQty': 0.01
            }
            exchange.create_order(order)
            print(exchange.exchange.createOrder.mock_calls)
            exchange.exchange.createOrder.assert_called_with('BTC/USD', 'limit', 'sell', .01, 12000.0)

    def test_amend_bulk_orders(self):
        with patch.object(ccxtInterface, "__init__", lambda x, **params: None):
            exchange = ccxtInterface()
            exchange.exchange = MagicMock()
            exchange.symbol = 'BTC/USD'
            exchange.logger = MagicMock()
            orders = [{
                'side': 'sell',
                'price': 12000.0,
                'orderQty': 0.01,
                'orderID': '12'
            }, {
                'side': 'buy',
                'price': 11000.0,
                'orderQty': 0.01,
                'orderID' : '13'
            }]
            exchange.amend_bulk_orders(orders)
            exchange.exchange.cancelOrder.assert_called()
            exchange.exchange.createOrder.assert_called()

    def test_cancel_order(self):
        with patch.object(ccxtInterface, "__init__", lambda x, **params: None):
            exchange = ccxtInterface()
            exchange.exchange = MagicMock()
            exchange.symbol = 'BTC/USD'
            exchange.logger = MagicMock()
            order = {
                'side': 'sell',
                'price': 12000.0,
                'orderQty': 0.01,
                'orderID': '12'
            }
            exchange.cancel_order(order)
            exchange.exchange.cancelOrder.assert_called()

    def test_cancel_all_orders(self):
        with patch.object(ccxtInterface, "__init__", lambda x, **params: None):
            with patch.object(ccxtInterface, "get_orders") as get_orders:
                exchange = ccxtInterface()
                exchange.exchange = MagicMock()
                exchange.symbol = 'BTC/USD'
                exchange.logger = MagicMock()
                get_orders.return_value = [
                    {'id': '9dfe9ad7-601f-4926-a893-4095e769b65b',
                     'info': {'id': '9dfe9ad7-601f-4926-a893-4095e769b65b',
                              'price': '10000.00000000', 'size': '0.01000000',
                              'product_id': 'BTC-USD', 'side': 'sell', 'type': 'limit',
                              'time_in_force': 'GTC', 'post_only': False,
                              'created_at': '2018-12-04T22:34:55.158107Z',
                              'fill_fees': '0.0000000000000000', 'filled_size': '0.00000000',
                              'executed_value': '0.0000000000000000', 'status': 'open',
                              'settled': False},
                     'timestamp': 1543962895158, 'datetime': '2018-12-04T22:34:55.158Z',
                     'lastTradeTimestamp': None, 'status': 'closed', 'symbol': 'BTC/USD',
                     'type': 'limit', 'side': 'Sell', 'price': 10000.0, 'cost': 0.0,
                     'amount': 0.01, 'filled': 0.0, 'remaining': 0.01,
                     'fee': {'cost': 0.0, 'currency': None, 'rate': None},
                     'orderID': '9dfe9ad7-601f-4926-a893-4095e769b65b',
                     'ordStatus': 'Canceled', 'orderQty': 0.01}]
                exchange.cancel_all_orders()
                get_orders.assert_called()
                exchange.exchange.cancelOrder.assert_called()


    def test_get_position(self):
        with patch.object(ccxtInterface, "__init__", lambda x, **params: None):
            exchange = ccxtInterface()
            exchange.exchange = MagicMock()
            exchange.symbol = 'BTC/USD'
            exchange.logger = MagicMock()
            exchange.exchange.fetchBalance.return_value = \
                { 'total': {'LTC': 0.0,
                  'GBP': 0.0,
                  'EUR': 0.0,
                  'ETH': 62.31306081,
                  'ETC': 0.0,
                  'BTC': 49.8296833,
                  'ZRX': 0.0,
                  'USD': 200603.95797549683,
                  'BCH': 0.0,
                  'BAT': 0.0}}
            position = exchange.get_position()
            assert 'avgCostPrice' in position
            assert 'avgEntryPrice' in position
            exchange.exchange.fetchBalance.assert_called()

    def test__get_base_currency(self):
        with patch.object(ccxtInterface, "__init__", lambda x, **params: None):
            exchange = ccxtInterface()
            assert exchange._get_base_currency('BTC/USD') == 'BTC'

    def test_get_delta(self):
        with patch.object(ccxtInterface, "__init__", lambda x, **params: None):
            with patch.object(ccxtInterface, "get_position") as get_position:
                exchange = ccxtInterface()
                exchange.exchange = MagicMock()
                exchange.symbol = 'BTC/USD'
                exchange.logger = MagicMock()
                get_position.return_value = \
                {'currentQty': 49.8296833, 'avgCostPrice': 0, 'avgEntryPrice': 0}
                delta = exchange.get_delta()
                assert delta == 49.8296833

    def test_get_orderbook(self):
        with patch.object(ccxtInterface, "__init__", lambda x, **params: None):
            exchange = ccxtInterface()
            exchange.exchange = MagicMock()
            exchange.symbol = 'BTC/USD'
            exchange.logger = MagicMock()
            exchange.exchange.fetchL2OrderBook.return_value = \
                {'bids': [[300.33, 5108.25295524],
                          [300.01, 11783.38915117],
                          [250.0, 1.543],
                          [201.0, 0.04001]],
                 'asks': [[4988.88, 35.36992734],
                          [4988.89, 0.01],
                          [5000.0, 498.17380412]],
                 'timestamp': None,
                 'datetime': None,
                 'nonce': None}
            orderbook = exchange.get_orderbook('BTC/USD')
            assert orderbook == {
                'bids': [[300.33, 5108.25295524],
                          [300.01, 11783.38915117],
                          [250.0, 1.543],
                          [201.0, 0.04001]],
                'asks': [[4988.88, 35.36992734],
                          [4988.89, 0.01],
                          [5000.0, 498.17380412]],
                'timestamp': None,
                'datetime': None,
                'nonce': None}
            exchange.exchange.fetchL2OrderBook.assert_called()


    def test_recent_trades(self):
        with patch.object(ccxtInterface, "__init__", lambda x, **params: None):
            exchange = ccxtInterface()
            exchange.exchange = MagicMock()
            exchange.symbol = 'BTC/USD'
            exchange.logger = MagicMock()
            exchange.exchange.fetchTrades.return_value = \
            [{'id': '2183667',
              'order': None,
              'info': {'time': '2018-12-10T10:39:46.297Z',
                       'trade_id': 2183667,
                       'price': '5000.00000000',
                       'size': '0.00400000',
                       'side': 'sell'},
              'timestamp': 1544438386297,
              'datetime': '2018-12-10T10:39:46.297Z',
              'symbol': 'BTC/USD',
              'type': None,
              'side': 'buy',
              'price': 5000.0,
              'amount': 0.004,
              'fee': {'cost': None, 'currency': 'USD', 'rate': None},
              'cost': 20.0},
             {'id': '2183668',
              'order': None,
              'info': {'time': '2018-12-10T10:39:46.836Z',
                       'trade_id': 2183668,
                       'price': '5000.00000000',
                       'size': '0.00200000',
                       'side': 'sell'},
              'timestamp': 1544438386836,
              'datetime': '2018-12-10T10:39:46.836Z',
              'symbol': 'BTC/USD',
              'type': None,
              'side': 'buy',
              'price': 5000.0,
              'amount': 0.002,
              'fee': {'cost': None, 'currency': 'USD', 'rate': None},
              'cost': 10.0}]
            trades = exchange.recent_trades()
            assert len(trades) == 2
            exchange.exchange.fetchTrades.assert_called()

    def test_get_highest_buy(self):
        with patch.object(ccxtInterface, "__init__", lambda x, **params: None):
            with patch.object(ccxtInterface, "get_orders") as get_orders:
                exchange = ccxtInterface()
                exchange.exchange = MagicMock()
                exchange.symbol = 'BTC/USD'
                exchange.logger = MagicMock()
                get_orders.return_value = [
                    {'side': 'Sell', 'price': 10000.0},
                    {'side': 'Sell', 'price': 9000.0},
                    {'side': 'Buy', 'price': 8000.0},
                    {'side': 'Buy', 'price': 7000.0},
                ]
                highest_buy = exchange.get_highest_buy()
                assert highest_buy['price'] == 8000.0

    def test_get_lowest_sell(self):
        with patch.object(ccxtInterface, "__init__", lambda x, **params: None):
            with patch.object(ccxtInterface, "get_orders") as get_orders:
                exchange = ccxtInterface()
                exchange.exchange = MagicMock()
                exchange.symbol = 'BTC/USD'
                exchange.logger = MagicMock()
                get_orders.return_value = [
                    {'side': 'Sell', 'price': 10000.0},
                    {'side': 'Sell', 'price': 9000.0},
                    {'side': 'Buy', 'price': 8000.0},
                    {'side': 'Buy', 'price': 7000.0},
                ]
                lowest_sell = exchange.get_lowest_sell()
                assert lowest_sell['price'] == 9000.0

    def test_check_if_orderbook_empty(self):
        with patch.object(ccxtInterface, "__init__", lambda x, **params: None):
            with patch.object(ccxtInterface, "get_orderbook") as get_orderbook:
                exchange = ccxtInterface()
                get_orderbook.return_value = {
                'bids': [],
                'asks': [],
                'timestamp': None,
                'datetime': None,
                'nonce': None}
                self.assertRaises(Exception, exchange.check_if_orderbook_empty)


    def test_check_market_open(self):
        with patch.object(ccxtInterface, "__init__", lambda x, **params: None):
            exchange = ccxtInterface()
            exchange.exchange = MagicMock()
            exchange.symbol = 'BTC/USD'
            exchange.logger = MagicMock()
            exchange.exchange.loadMarkets.return_value = {
                'BTC/USD': {'fee_loaded': False,
                 'percentage': True,
                 'tierBased': True,
                 'maker': 0.0,
                 'taker': 0.003,
                 'precision': {'amount': 8, 'price': 2},
                 'limits': {'amount': {'min': 0.001, 'max': 10000.0},
                            'price': {'min': 0.01, 'max': None},
                            'cost': {'min': None, 'max': None}},
                 'id': 'BTC-USD',
                 'symbol': 'BTC/USD',
                 'base': 'BTC',
                 'quote': 'USD',
                 'active': True,
                 'info': {'id': 'BTC-USD',
                          'base_currency': 'BTC',
                          'quote_currency': 'USD',
                          'base_min_size': '0.001',
                          'base_max_size': '10000',
                          'quote_increment': '0.01',
                          'display_name': 'BTC/USD',
                          'status': 'online',
                          'margin_enabled': True,
                          'status_message': None,
                          'min_market_funds': None,
                          'max_market_funds': None,
                          'post_only': False,
                          'limit_only': False,
                          'cancel_only': False}}
            }
            is_open = exchange.check_market_open()
            assert is_open == True
            exchange.exchange.loadMarkets.assert_called()
            # Now test failing condition
            exchange.exchange.loadMarkets.return_value['BTC/USD']['active'] = False
            self.assertRaises(Exception, exchange.check_market_open)
            # Test other failing condition
            exchange.exchange.loadMarkets.return_value = {}
            self.assertRaises(Exception, exchange.check_market_open)


