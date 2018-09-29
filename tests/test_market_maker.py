import datetime
import iso8601
from unittest.mock import MagicMock, patch
from unittest import TestCase
import sys


class Test_Market_Maker_Module(TestCase):

    def setUp(self):
        """
        It's patching time
        """

        #http://www.voidspace.org.uk/python/mock/examples.html#mocking-imports-with-patch-dict
        self.settings_mock = MagicMock()
        #self.settings_mock.settings.BACKTEST.return_value = True
        #self.settings_mock.settings.paperless = True
        self.exchange_interface = MagicMock()
        self.coinbase_book = MagicMock()
        self.logging = MagicMock()
        self.log = MagicMock()
        modules = {
            'market_maker.settings': self.settings_mock,
            'market_maker.exchange_interface' : self.exchange_interface,
            'market_maker.coinbase.order_book' : self.coinbase_book,
            'market_maker.utils.log' : self.log,
            'logging' : self.logging
        }
        '''
            To patch:
            from market_maker import bitmex
            from market_maker.settings import settings
            from market_maker.utils import log, constants, errors, math
            from market_maker.exchange_interface import ExchangeInterface
            from market_maker.modifiable_settings import ModifiableSettings
            from market_maker.coinbase.order_book import OrderBook


            '''  
        self.settings_mock.DRY_RUN = False
        self.settings_mock.BACKTEST = True
        self.settings_mock.SYMBOL = 'XBTUSD'
        self.module_patcher = patch.dict('sys.modules', modules)
        self.module_patcher.start()
        #from my_module import MyModule
        #from market_maker.market_maker import OrderManager
        #self.om = OrderManager()

    def tearDown(self):
        """
        Let's clean up
        """

        self.module_patcher.stop()

    def test_calls_logging(self):
        import logging
        with patch('logging.getLogger') as mock_method:
            from market_maker.market_maker import OrderManager
        #print(self.log.call_count)
        mock_method.assert_called()


class Test_OrderManager(TestCase):

    def setUp(self):
        """
        It's patching time
        """

        #http://www.voidspace.org.uk/python/mock/examples.html#mocking-imports-with-patch-dict
        self.settings_mock = MagicMock()
        #self.settings_mock.settings.BACKTEST.return_value = True
        #self.settings_mock.settings.paperless = True
        self.exchange_interface = MagicMock()
        self.coinbase_book = MagicMock()
        self.logging = MagicMock()

        self.log = MagicMock()
        modules = {
            'market_maker.settings': self.settings_mock,
            'market_maker.exchange_interface' : self.exchange_interface,
            'market_maker.coinbase.order_book' : self.coinbase_book,
            'market_maker.utils.log.setup_custom_logger' : self.log,
            'market_maker.market_maker.log' : self.log,
            'logging' : self.logging
        }
        self.settings_mock.DRY_RUN = False
        self.settings_mock.BACKTEST = True
        self.settings_mock.SYMBOL = 'XBTUSD'
        self.module_patcher = patch.dict('sys.modules', modules)
        self.module_patcher.start()
        #from market_maker.utils import log
        with patch('market_maker.utils.log.setup_custom_logger') as mock_logger:
            from market_maker.market_maker import OrderManager
        #from market_maker.market_maker import OrderManager
        #print(sys.modules.items())
        self.orderManager = OrderManager
        #with patch('market_maker.utils.log.setup_custom_logger') as mock_logger:
        #    import market_maker.market_maker
        #with patch.dict(sys.modules, modules) as patched:
        #    import market_maker.market_maker
        #self.orderManager = market_maker.market_maker.OrderManager

    def tearDown(self):
        """
        Let's clean up
        """

        self.module_patcher.stop()

    def test_market_maker_init(self):
        self.orderManager.reset =  MagicMock()
        self.om = self.orderManager()
        #let's just check a function is called
        self.om.reset.assert_called()

    def test_run_loop_exits_on_EOF(self):
        self.orderManager.reset =  MagicMock()
        self.om = self.orderManager()
        self.om.exchange.wait_update = MagicMock(side_effect=EOFError)
        self.om.run_loop()
        self.om.exchange.wait_update.assert_called()

    def test_run_loop_through_two_loops(self):
        self.orderManager.reset =  MagicMock()
        self.om = self.orderManager()
        self.sanity_check = MagicMock()
        returns = iter([True, True])
        def side_effect(*args, **kwargs):
            try:
                return next(returns)
            except StopIteration:
                # raised all exceptions, call original
                raise EOFError()
        self.om.exchange.wait_update = MagicMock(side_effect=side_effect)
        self.om.exchange.ok_to_enter_order = MagicMock()
        self.om.exchange.ok_to_enter_order.return_value = False
        self.om.run_loop()
        assert self.om.exchange.ok_to_enter_order.call_count == 2
        self.sanity_check.assert_not_called()
        print("SOME SHIT!")


    def test_prices_to_orders_create_two_new_orders(self):
        self.orderManager.reset =  MagicMock()
        self.om = self.orderManager()
        self.om.exchange.get_instrument.return_value = {'tickLog': 1}
        self.om.exchange.get_orders.return_value = []
        self.om.exchange.get_ticker.return_value = {'last': 6433.5, 'buy': 6433.0, 'sell': 6433.5, 'mid': 6433.0}
        self.om.exchange.recent_trades.return_value = \
        [{'timestamp': '2018-07-19T18:51:15.606Z', 'symbol': 'XBTUSD', 'side': 'Sell', 
        'size': 100, 'price': 6433.5, 'tickDirection': 'MinusTick', 
        'trdMatchID': 'dddb8785-7156-f030-b325-c35daed19640', 'grossValue': 1349100, 
        'homeNotional': 0.013491, 'foreignNotional': 100}]
        self.om.coinbase.get_bid.return_value = 6433.0
        self.om.coinbase.get_ask.return_value = 6433.5
        self.om.prices_to_orders(6430, 6440)
        self.om.exchange.create_bulk_orders.assert_called()
        assert len(self.om.exchange.create_bulk_orders.call_args[0][0]) == 2
        print(self.om.exchange.create_bulk_orders.call_args[0][0])


    def test_prices_to_orders_create_one_order(self):
        self.orderManager.reset =  MagicMock()
        self.om = self.orderManager()
        self.om.exchange.get_instrument.return_value = {'tickLog': 1}
        self.om.exchange.get_orders.return_value = [{'price': 6430, 'orderQty': 100, 'side': 'Buy', 'theo': 6433.5, 'last_price': 6433.5, 'orderID': 68312, 'coinbase_mid': 6433.25}]
        self.om.exchange.get_ticker.return_value = {'last': 6433.5, 'buy': 6433.0, 'sell': 6433.5, 'mid': 6433.0}
        self.om.exchange.recent_trades.return_value = \
        [{'timestamp': '2018-07-19T18:51:15.606Z', 'symbol': 'XBTUSD', 'side': 'Sell', 
        'size': 100, 'price': 6433.5, 'tickDirection': 'MinusTick', 
        'trdMatchID': 'dddb8785-7156-f030-b325-c35daed19640', 'grossValue': 1349100, 
        'homeNotional': 0.013491, 'foreignNotional': 100}]
        self.om.coinbase.get_bid.return_value = 6433.0
        self.om.coinbase.get_ask.return_value = 6433.5
        self.om.prices_to_orders(6430, 6440)
        self.om.exchange.create_bulk_orders.assert_called()
        assert len(self.om.exchange.create_bulk_orders.call_args[0][0]) == 1
        print(self.om.exchange.create_bulk_orders.call_args[0][0])

    def test_prices_to_orders_update_orders(self):
        self.orderManager.reset =  MagicMock()
        self.om = self.orderManager()
        self.om.exchange.get_instrument.return_value = {'tickLog': 1}
        self.om.exchange.get_orders.return_value = \
        [{'price': 6430, 'orderQty': 100, 'side': 'Buy', 'theo': 6433.5, 
        'last_price': 6433.5, 'orderID': 33929, 'coinbase_mid': 6433.25,
        "leavesQty": 100, 'cumQty': 0}, 
        {'price': 6440, 'orderQty': 100, 'side': 'Sell', 'theo': 6433.5, 
        'last_price': 6433.5, 'orderID': 10429, 'coinbase_mid': 6433.25,
        "leavesQty": 100, 'cumQty': 0}]
        self.om.exchange.get_ticker.return_value = {'last': 6433.5, 'buy': 6433.0, 'sell': 6433.5, 'mid': 6433.0}
        self.om.exchange.recent_trades.return_value = \
        [{'timestamp': '2018-07-19T18:51:15.606Z', 'symbol': 'XBTUSD', 'side': 'Sell', 
        'size': 100, 'price': 6433.5, 'tickDirection': 'MinusTick', 
        'trdMatchID': 'dddb8785-7156-f030-b325-c35daed19640', 'grossValue': 1349100, 
        'homeNotional': 0.013491, 'foreignNotional': 100}]
        self.om.coinbase.get_bid.return_value = 6433.0
        self.om.coinbase.get_ask.return_value = 6433.5
        self.om.prices_to_orders(6429, 6439)
        self.om.exchange.create_bulk_orders.assert_not_called()
        self.om.exchange.amend_bulk_orders.assert_called()
        assert len(self.om.exchange.amend_bulk_orders.call_args[0][0]) == 2
        print(self.om.exchange.amend_bulk_orders.call_args[0][0])

