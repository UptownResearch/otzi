import datetime
import iso8601
from unittest.mock import MagicMock, patch
from unittest import TestCase
import sys
# Find code directory relative to our directory


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
            from os.path import dirname, abspath, join
            from market_maker.order_manager import OrderManager
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
        self.sleep = MagicMock()
        modules = {
            'market_maker.settings': self.settings_mock,
            'market_maker.exchange_interface' : self.exchange_interface,
            'market_maker.coinbase.order_book' : self.coinbase_book,
            'market_maker.utils.log.setup_custom_logger' : self.log,
            'market_maker.market_maker.log' : self.log,
            'logging' : self.logging,
            'time.sleep' : self.sleep

        }
        self.settings_mock.DRY_RUN = False
        self.settings_mock.BACKTEST = True
        self.settings_mock.SYMBOL = 'XBTUSD'
        self.module_patcher = patch.dict('sys.modules', modules)
        self.module_patcher.start()
        #from market_maker.utils import log
        from market_maker.order_manager import OrderManager
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
        self.om = self.orderManager(settings= self.settings_mock)
        #let's just check a function is called
        self.om.reset.assert_called()

    def test_run_loop_exits_on_EOF(self):
        self.orderManager.reset =  MagicMock()
        self.om = self.orderManager(settings= self.settings_mock)
        self.om.exchange.wait_update = MagicMock(side_effect=EOFError)
        self.om.run_loop()
        self.om.exchange.wait_update.assert_called()

    def test_ceilNearest(self):
        self.orderManager.reset =  MagicMock()
        self.om = self.orderManager(settings= self.settings_mock)
        assert self.om.ceilNearest(.1, .5) == .5
        assert self.om.ceilNearest(0, .5) == 0
        assert self.om.ceilNearest(5000.25, .5) == 5000.5
        assert self.om.ceilNearest(5000.45, .5) == 5000.5

    def test_floorNearest(self):
        self.orderManager.reset =  MagicMock()
        self.om = self.orderManager(settings= self.settings_mock)
        assert self.om.floorNearest(0.1, 0.5) == 0.0
        assert self.om.floorNearest(0.49, 0.5) == 0.0
        assert self.om.floorNearest(1.49, 0.5) == 1.0
        assert self.om.floorNearest(5000.25, 0.5) == 5000.0

    def test_run_loop_through_two_loops(self):
        self.orderManager.reset =  MagicMock()
        self.om = self.orderManager(settings= self.settings_mock)
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


    def test_prices_to_orders_create_two_new_orders(self):
        self.orderManager.reset =  MagicMock()
        self.om = self.orderManager(settings= self.settings_mock)
        self.om.exchange.get_instrument.return_value = {'tickLog': 1}
        self.om.exchange.get_orders.return_value = []
        self.om.exchange.get_ticker.return_value = {'last': 6433.5, 'buy': 6433.0, 'sell': 6433.5, 'mid': 6433.0}
        self.om.exchange.recent_trades.return_value = \
        [{'timestamp': '2018-07-19T18:51:15.606Z', 'symbol': 'XBTUSD', 'side': 'Sell', 
        'size': 100, 'price': 6433.5, 'tickDirection': 'MinusTick', 
        'trdMatchID': 'dddb8785-7156-f030-b325-c35daed19640', 'grossValue': 1349100, 
        'homeNotional': 0.013491, 'foreignNotional': 100}]
        #self.om.coinbase.get_bid.return_value = 6433.0
        #self.om.coinbase.get_ask.return_value = 6433.5
        self.om.prices_to_orders(6430, 6440)
        self.om.exchange.create_bulk_orders.assert_called()
        assert len(self.om.exchange.create_bulk_orders.call_args[0][0]) == 2


    def test_prices_to_orders_create_one_order(self):
        self.orderManager.reset =  MagicMock()
        self.om = self.orderManager(settings= self.settings_mock)
        self.om.exchange.get_instrument.return_value = {'tickLog': 1}
        self.om.exchange.get_orders.return_value = [{'price': 6430, 'orderQty': 100, 'side': 'Buy', 'theo': 6433.5, 'last_price': 6433.5, 'orderID': 68312, 'coinbase_mid': 6433.25}]
        self.om.exchange.get_ticker.return_value = {'last': 6433.5, 'buy': 6433.0, 'sell': 6433.5, 'mid': 6433.0}
        self.om.exchange.recent_trades.return_value = \
        [{'timestamp': '2018-07-19T18:51:15.606Z', 'symbol': 'XBTUSD', 'side': 'Sell', 
        'size': 100, 'price': 6433.5, 'tickDirection': 'MinusTick', 
        'trdMatchID': 'dddb8785-7156-f030-b325-c35daed19640', 'grossValue': 1349100, 
        'homeNotional': 0.013491, 'foreignNotional': 100}]
        #self.om.coinbase.get_bid.return_value = 6433.0
        #self.om.coinbase.get_ask.return_value = 6433.5
        self.om.prices_to_orders(6430, 6440)
        self.om.exchange.create_bulk_orders.assert_called()
        assert len(self.om.exchange.create_bulk_orders.call_args[0][0]) == 1

    def test_prices_to_orders_update_orders(self):
        self.orderManager.reset =  MagicMock()
        self.om = self.orderManager(settings= self.settings_mock)
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
        #self.om.coinbase.get_bid.return_value = 6433.0
        #self.om.coinbase.get_ask.return_value = 6433.5
        self.om.prices_to_orders(6429, 6439)
        self.om.exchange.create_bulk_orders.assert_not_called()
        self.om.exchange.amend_bulk_orders.assert_called()
        assert len(self.om.exchange.amend_bulk_orders.call_args[0][0]) == 2

    def test_prices_to_orders_update_orders(self):
        self.orderManager.reset =  MagicMock()
        self.om = self.orderManager(settings= self.settings_mock)
        self.om.exchange.get_instrument.return_value = {'tickLog': 1}
        self.om.prices_to_orders(6429, 6439, 
                                buyamount = 0, 
                                sellamount = 0)
        # No orders should have been created
        assert self.om.exchange.create_bulk_orders.call_args is None

    def test_prices_to_orders_with_promised_orders(self):
        pass

    def test_get_order_with_role_buy_roles(self):
        self.orderManager.reset =  MagicMock()
        self.om = self.orderManager(settings= self.settings_mock)
        self.om.exchange.get_instrument.return_value = {'tickLog': 1}
        orders = \
        [{'price': 6430, 'orderQty': 100, 'side': 'Buy', 'theo': 6433.5,
        'last_price': 6433.5, 'orderID': 33929, 'coinbase_mid': 6433.25,
        "leavesQty": 100, 'cumQty': 0, 'role': 'Buy'},
        {'price': 6440, 'orderQty': 100, 'side': 'Sell', 'theo': 6433.5,
        'last_price': 6433.5, 'orderID': 10429, 'coinbase_mid': 6433.25,
        "leavesQty": 100, 'cumQty': 0, 'role': 'Sell'}]
        assert  self.om.get_order_with_role(orders, 'Buy')['price'] == 6430

    def test_get_order_with_role_cancelled_order(self):
        self.orderManager.reset =  MagicMock()
        self.om = self.orderManager(settings= self.settings_mock)
        self.om.exchange.get_instrument.return_value = {'tickLog': 1}
        orders = \
        [{'price': 6430, 'orderQty': 100, 'side': 'Buy', 'theo': 6433.5,
        'last_price': 6433.5, 'orderID': 33929, 'coinbase_mid': 6433.25,
        "leavesQty": 100, 'cumQty': 0, 'role': 'Buy'},
        {'price': 6440, 'orderQty': 100, 'side': 'Sell', 'theo': 6433.5,
        'last_price': 6433.5, 'orderID': 10429, 'coinbase_mid': 6433.25,
        "leavesQty": 100, 'cumQty': 0, 'role': 'Sell'}]
        self.om.cancelled_orders = ['33929']
        assert  self.om.get_order_with_role(orders, 'Buy')['price'] == 6430

    def test_get_order_with_role(self):
        self.orderManager.reset =  MagicMock()
        self.om = self.orderManager(settings= self.settings_mock)
        self.om.exchange.get_instrument.return_value = {'tickLog': 1}
        orders = \
        [{'price': 6430, 'orderQty': 100, 'side': 'Buy', 'theo': 6433.5,
        'last_price': 6433.5, 'orderID': 33929, 'coinbase_mid': 6433.25,
        "leavesQty": 100, 'cumQty': 0},
        {'price': 6440, 'orderQty': 100, 'side': 'Sell', 'theo': 6433.5,
        'last_price': 6433.5, 'orderID': 10429, 'coinbase_mid': 6433.25,
        "leavesQty": 100, 'cumQty': 0}]
        assert self.om.get_order_with_role(orders, 'Buy')['price'] == 6430

    def test_get_all_order_with_role(self):
        self.orderManager.reset =  MagicMock()
        self.om = self.orderManager(settings= self.settings_mock)
        self.om.exchange.get_instrument.return_value = {'tickLog': 1}
        orders = \
        [{'price': 6430, 'orderQty': 100, 'side': 'Buy', 'theo': 6433.5,
        'last_price': 6433.5, 'orderID': 33929, 'coinbase_mid': 6433.25,
        "leavesQty": 100, 'cumQty': 0},
        {'price': 6440, 'orderQty': 100, 'side': 'Sell', 'theo': 6433.5,
        'last_price': 6433.5, 'orderID': 10429, 'coinbase_mid': 6433.25,
        "leavesQty": 100, 'cumQty': 0}]
        assert  len(self.om.get_all_orders_with_role(orders, 'Buy')) == 1


    def test_desired_to_orders_create_two_new_orders(self):
        self.orderManager.reset =  MagicMock()
        self.om = self.orderManager(settings= self.settings_mock)
        self.om.exchange.get_instrument.return_value = {'tickLog': 1}
        self.om.exchange.get_orders.return_value = []
        self.om.exchange.get_ticker.return_value = {'last': 6433.5, 'buy': 6433.0, 'sell': 6433.5, 'mid': 6433.0}
        self.om.exchange.recent_trades.return_value = \
        [{'timestamp': '2018-07-19T18:51:15.606Z', 'symbol': 'XBTUSD', 'side': 'Sell',
        'size': 100, 'price': 6433.5, 'tickDirection': 'MinusTick',
        'trdMatchID': 'dddb8785-7156-f030-b325-c35daed19640', 'grossValue': 1349100,
        'homeNotional': 0.013491, 'foreignNotional': 100}]
        #self.om.coinbase.get_bid.return_value = 6433.0
        #self.om.coinbase.get_ask.return_value = 6433.5
        self.om.desired_to_orders(6430, 6440)
        self.om.exchange.create_bulk_orders.assert_called()
        assert len(self.om.exchange.create_bulk_orders.call_args[0][0]) == 2

    def test_desired_to_orders_update_orders_(self):
        self.orderManager.reset =  MagicMock()
        self.om = self.orderManager(settings= self.settings_mock)
        self.om.exchange.get_instrument.return_value = {'tickLog': 1}
        self.om.desired_to_orders(6429, 6439,
                                buyamount = 0,
                                sellamount = 0)
        # No orders should have been created
        assert self.om.exchange.create_bulk_orders.call_args is None


    def test_desired_to_orders_create_one_order(self):
        self.orderManager.reset =  MagicMock()
        self.om = self.orderManager(settings= self.settings_mock)
        self.om.exchange.get_instrument.return_value = {'tickLog': 1}
        self.om.exchange.get_orders.return_value = [{'price': 6430, 'orderQty': 100, 'side': 'Buy', 'theo': 6433.5, 'last_price': 6433.5, 'orderID': 68312, 'coinbase_mid': 6433.25}]
        self.om.exchange.get_ticker.return_value = {'last': 6433.5, 'buy': 6433.0, 'sell': 6433.5, 'mid': 6433.0}
        self.om.exchange.recent_trades.return_value = \
        [{'timestamp': '2018-07-19T18:51:15.606Z', 'symbol': 'XBTUSD', 'side': 'Sell',
        'size': 100, 'price': 6433.5, 'tickDirection': 'MinusTick',
        'trdMatchID': 'dddb8785-7156-f030-b325-c35daed19640', 'grossValue': 1349100,
        'homeNotional': 0.013491, 'foreignNotional': 100}]
        #self.om.coinbase.get_bid.return_value = 6433.0
        #self.om.coinbase.get_ask.return_value = 6433.5
        self.om.desired_to_orders(6430, 6440)
        self.om.exchange.create_bulk_orders.assert_called()
        assert len(self.om.exchange.create_bulk_orders.call_args[0][0]) == 1


    def test_desired_to_orders_update_orders(self):
        self.orderManager.reset =  MagicMock()
        self.om = self.orderManager(settings= self.settings_mock)
        self.om.exchange.get_instrument.return_value = {'tickLog': 1}
        self.om.exchange.get_orders.return_value = \
        [{'price': 6430, 'orderQty': 100, 'side': 'Buy', 'theo': 6433.5,
        'last_price': 6433.5, 'orderID': 33929, 'coinbase_mid': 6433.25,
        "leavesQty": 100, 'cumQty': 0, 'ordStatus' : 'New'},
        {'price': 6440, 'orderQty': 100, 'side': 'Sell', 'theo': 6433.5,
        'last_price': 6433.5, 'orderID': 10429, 'coinbase_mid': 6433.25,
        "leavesQty": 100, 'cumQty': 0, 'ordStatus' : 'New' }]
        self.om.exchange.get_ticker.return_value = {'last': 6433.5, 'buy': 6433.0, 'sell': 6433.5, 'mid': 6433.0}
        self.om.exchange.recent_trades.return_value = \
        [{'timestamp': '2018-07-19T18:51:15.606Z', 'symbol': 'XBTUSD', 'side': 'Sell',
        'size': 100, 'price': 6433.5, 'tickDirection': 'MinusTick',
        'trdMatchID': 'dddb8785-7156-f030-b325-c35daed19640', 'grossValue': 1349100,
        'homeNotional': 0.013491, 'foreignNotional': 100}]
        #self.om.coinbase.get_bid.return_value = 6433.0
        #self.om.coinbase.get_ask.return_value = 6433.5
        self.om.desired_to_orders(6429, 6439)
        self.om.exchange.create_bulk_orders.assert_not_called()
        self.om.exchange.amend_bulk_orders.assert_called()
        assert len(self.om.exchange.amend_bulk_orders.call_args[0][0]) == 2
        print(self.om.exchange.amend_bulk_orders.call_args[0][0])


    def test_desired_to_orders_cancels_extra_orders(self):
        # This test is currently being ignored! Same name as next test!
        self.orderManager.reset =  MagicMock()
        self.om = self.orderManager(settings= self.settings_mock)
        self.om.exchange.get_instrument.return_value = {'tickLog': 1}
        self.om.exchange.get_orders.return_value = \
        [{'price': 6430, 'orderQty': 100, 'side': 'Buy', 'theo': 6433.5,
        'last_price': 6433.5, 'orderID': 33929, 'coinbase_mid': 6433.25,
        "leavesQty": 100, 'cumQty': 0},
        {'price': 6440, 'orderQty': 100, 'side': 'Sell', 'theo': 6433.5,
        'last_price': 6433.5, 'orderID': 10429, 'coinbase_mid': 6433.25,
        "leavesQty": 100, 'cumQty': 0},
         {'price': 6429, 'orderQty': 100, 'side': 'Buy', 'theo': 6433.5,
          'last_price': 6433.5, 'orderID': 33929, 'coinbase_mid': 6433.25,
          "leavesQty": 100, 'cumQty': 0},
         {'price': 6441, 'orderQty': 100, 'side': 'Sell', 'theo': 6433.5,
          'last_price': 6433.5, 'orderID': 10429, 'coinbase_mid': 6433.25,
          "leavesQty": 100, 'cumQty': 0}
         ]
        self.om.exchange.get_ticker.return_value = {'last': 6433.5, 'buy': 6433.0, 'sell': 6433.5, 'mid': 6433.0}
        self.om.exchange.recent_trades.return_value = \
        [{'timestamp': '2018-07-19T18:51:15.606Z', 'symbol': 'XBTUSD', 'side': 'Sell',
        'size': 100, 'price': 6433.5, 'tickDirection': 'MinusTick',
        'trdMatchID': 'dddb8785-7156-f030-b325-c35daed19640', 'grossValue': 1349100,
        'homeNotional': 0.013491, 'foreignNotional': 100}]
        #self.om.coinbase.get_bid.return_value = 6433.0
        #self.om.coinbase.get_ask.return_value = 6433.5
        self.om.desired_to_orders(6429, 6439)
        self.om.exchange.create_bulk_orders.assert_not_called()
        self.om.exchange.amend_bulk_orders.assert_called()
        #Assert that 4 orders are amended
        assert len(self.om.exchange.amend_bulk_orders.call_args[0][0]) == 2
        assert self.om.exchange.cancel_order.called
        print(self.om.exchange.amend_bulk_orders.call_args[0][0][0])

    def test_desired_to_orders_cancels_extra_orders(self):
        self.orderManager.reset = MagicMock()
        self.om = self.orderManager(settings=self.settings_mock)
        order1 = {"price": 6346.0, "orderQty": 100, "side": "Buy",
            "theo": 6346.75, "last_price": 6346.5, "orderID": 57632,
            "coinbase_mid": 6349.985, "clOrdID": "mm_bitmex_EPx3mojZT4yG2L0Zd9ylMQ",
            "symbol": "XBTUSD", "execInst": "ParticipateDoNotInitiate"}
        order2 = {"orderID": "9bb6b5da-729a-b2b3-c7a1-614f9b222784",
            "clOrdID": "mm_bitmex_EPx3mojZT4yG2L0Zd9ylMQ", "clOrdLinkID": "",
            "account": 779788, "symbol": "XBTUSD", "side": "Buy",
            "simpleOrderQty": None, "orderQty": 100, "price": 6346,
            "displayQty": None, "stopPx": None, "pegOffsetValue": None,
            "pegPriceType": "", "currency": "USD", "settlCurrency": "XBt",
            "ordType": "Limit", "timeInForce": "GoodTillCancel",
            "execInst": "ParticipateDoNotInitiate", "contingencyType": "",
            "exDestination": "XBME", "ordStatus": "New", "triggered": "",
            "workingIndicator": False, "ordRejReason": "",
            "simpleLeavesQty": None, "leavesQty": 100, "simpleCumQty": None,
            "cumQty": 0, "avgPx": None, "multiLegReportingType": "SingleSecurity",
            "text": "Submitted via API.", "transactTime": "2018-11-09T17:40:40.755Z",
            "timestamp": "2018-11-09T17:40:40.755Z"}
        assert self.om.is_live_order(order1) == False
        assert self.om.is_live_order(order2) == True

    def test_create_cancel_orders_from_orders(self):
        self.orderManager.reset = MagicMock()
        self.om = self.orderManager(settings=self.settings_mock)
        order1 = {"price": 6346.0, "orderQty": 100, "side": "Buy",
            "theo": 6346.75, "last_price": 6346.5, "orderID": 57632,
            "coinbase_mid": 6349.985, "clOrdID": "order_ID_1",
            "symbol": "XBTUSD", "execInst": "ParticipateDoNotInitiate",
            'submission_time' : 152424399.11 }
        order2 = {"orderID": "9bb6b5da-729a-b2b3-c7a1-614f9b222784",
            "clOrdID": "order_ID_2", "clOrdLinkID": "",
            "account": 779788, "symbol": "XBTUSD", "side": "Buy",
            "simpleOrderQty": None, "orderQty": 100, "price": 6346,
            "displayQty": None, "stopPx": None, "pegOffsetValue": None,
            "pegPriceType": "", "currency": "USD", "settlCurrency": "XBt",
            "ordType": "Limit", "timeInForce": "GoodTillCancel",
            "execInst": "ParticipateDoNotInitiate", "contingencyType": "",
            "exDestination": "XBME", "ordStatus": "New", "triggered": "",
            "workingIndicator": False, "ordRejReason": "",
            "simpleLeavesQty": None, "leavesQty": 100, "simpleCumQty": None,
            "cumQty": 0, "avgPx": None, "multiLegReportingType": "SingleSecurity",
            "text": "Submitted via API.", "transactTime": "2018-11-09T17:40:40.755Z",
            "timestamp": "2018-11-09T17:40:40.755Z"}
        orders = [order1, order2]
        result = self.om.create_cancel_orders_from_orders(orders)
        print(result)
        assert len(result) == 1
        assert result[0]['orderID'] == "9bb6b5da-729a-b2b3-c7a1-614f9b222784"

    def test_cancel_all_orders(self):
        self.orderManager.reset = MagicMock()
        self.om = self.orderManager(settings=self.settings_mock)
        order1 = {"price": 6346.0, "orderQty": 100, "side": "Buy",
            "theo": 6346.75, "last_price": 6346.5, "orderID": 57632,
            "coinbase_mid": 6349.985, "clOrdID": "order_ID_1",
            "symbol": "XBTUSD", "execInst": "ParticipateDoNotInitiate",
            'submission_time' : 152424399.11 }
        order2 = {"orderID": "9bb6b5da-729a-b2b3-c7a1-614f9b222784",
            "clOrdID": "order_ID_2", "clOrdLinkID": "",
            "account": 779788, "symbol": "XBTUSD", "side": "Buy",
            "simpleOrderQty": None, "orderQty": 100, "price": 6346,
            "displayQty": None, "stopPx": None, "pegOffsetValue": None,
            "pegPriceType": "", "currency": "USD", "settlCurrency": "XBt",
            "ordType": "Limit", "timeInForce": "GoodTillCancel",
            "execInst": "ParticipateDoNotInitiate", "contingencyType": "",
            "exDestination": "XBME", "ordStatus": "New", "triggered": "",
            "workingIndicator": False, "ordRejReason": "",
            "simpleLeavesQty": None, "leavesQty": 100, "simpleCumQty": None,
            "cumQty": 0, "avgPx": None, "multiLegReportingType": "SingleSecurity",
            "text": "Submitted via API.", "transactTime": "2018-11-09T17:40:40.755Z",
            "timestamp": "2018-11-09T17:40:40.755Z"}
        orders = [order1, order2]
        result = self.om.cancel_all_orders(orders)
        print(self.om.exchange.cancel_order.call_args_list)
        assert len(self.om.exchange.cancel_order.call_args_list) == 1

