from datetime import datetime, timezone, timedelta
import iso8601
from unittest.mock import MagicMock, patch, Mock
from unittest import TestCase
import sys
# Find code directory relative to our directory



class Test_Exchange_Interface_Module(TestCase):

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
        self.bitmex = MagicMock()
        self.paper_trading = MagicMock()
        self.market_maker = MagicMock()
        modules = {
            'market_maker.settings': self.settings_mock,
            'market_maker.backtest.bitmexbacktest' : self.bitmex,
            'market_maker.paper_trading' : self.paper_trading,
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


    def test_module_loads(self):
        from market_maker.exchange_interface import ExchangeInterface
        exchange_interface_ = ExchangeInterface(settings=self.settings_mock)
        assert exchange_interface_ is not None

    @patch('market_maker.paper_trading.PaperTrading')
    @patch('market_maker.backtest.bitmexbacktest.BitMEXbacktest')
    def test_places_order_in_backtest(self, backtest, paper): 
        self.settings_mock.ORDERID_PREFIX  = "test_"
        from market_maker.exchange_interface import ExchangeInterface
        self.exchange_interface = ExchangeInterface(settings=self.settings_mock)
        to_create = []
        neworder1 = {'orderID': 1,  'orderQty': 100, 
            'price':  6001, 'side': "Sell" , 'theo': 6000}
        neworder2 = {'orderID': 2,  'orderQty': 100, 
            'price':  5999, 'side': "Buy" , 'theo': 6000}
        to_create.extend([neworder1, neworder2])
        self.exchange_interface.create_bulk_orders(to_create)
        print(paper.return_value.mock_calls)
        paper.return_value.track_orders_created.assert_called()

        # self.exchange.create_bulk_orders(to_create)
        #self.exchange.amend_bulk_orders(to_amend)

    @patch('market_maker.bitmex.BitMEX')
    @patch('market_maker.paper_trading.PaperTrading')
    @patch('market_maker.backtest.bitmexbacktest.BitMEXbacktest')
    def test_places_order_in_live(self, backtest, paper, bitmex): 
        self.settings_mock.ORDERID_PREFIX  = "live_"
        self.settings_mock.BACKTEST = False
        from market_maker.exchange_interface import ExchangeInterface
        self.exchange_interface = ExchangeInterface(settings=self.settings_mock)
        to_create = []
        neworder1 = {'orderID': 1,  'orderQty': 100, 
            'price':  6001, 'side': "Sell" , 'theo': 6000}
        neworder2 = {'orderID': 2,  'orderQty': 100, 
            'price':  5999, 'side': "Buy" , 'theo': 6000}
        to_create.extend([neworder1, neworder2])
        self.exchange_interface.create_bulk_orders(to_create)
        print(bitmex.return_value.mock_calls)
        bitmex.return_value.create_bulk_orders.assert_called()



    @patch('market_maker.bitmex.BitMEX')
    @patch('market_maker.paper_trading.PaperTrading')
    @patch('market_maker.backtest.bitmexbacktest.BitMEXbacktest')
    def test_places_order_in_live(self, backtest, paper, bitmex): 
        self.settings_mock.ORDERID_PREFIX  = "live_"
        self.settings_mock.BACKTEST = False
        from market_maker.exchange_interface import ExchangeInterface
        self.exchange_interface = ExchangeInterface(settings=self.settings_mock)
        to_create = []
        neworder1 = {'orderID': 1,  'orderQty': 100, 
            'price':  6001, 'side': "Sell" , 'theo': 6000}
        neworder2 = {'orderID': 2,  'orderQty': 100, 
            'price':  5999, 'side': "Buy" , 'theo': 6000}
        to_create.extend([neworder1, neworder2])
        self.exchange_interface.create_bulk_orders(to_create)
        print(bitmex.return_value.mock_calls)
        bitmex.return_value.create_bulk_orders.assert_called()


    @patch('market_maker.bitmex.BitMEX')
    @patch('market_maker.paper_trading.PaperTrading')
    @patch('market_maker.backtest.bitmexbacktest.BitMEXbacktest')
    def test_rate_limit_order_creation(self, backtest, paper, bitmex): 
        self.settings_mock.ORDERID_PREFIX  = "live_"
        self.settings_mock.BACKTEST = False
        ts = datetime.now().replace(tzinfo=timezone.utc).timestamp()
        from market_maker.exchange_interface import ExchangeInterface
        self.exchange_interface = ExchangeInterface(settings=self.settings_mock)
        current_timestamp = MagicMock()
        self.exchange_interface._current_timestamp = current_timestamp
        to_create  = [{"price": 6346.0, "orderQty": 100, "side": "Buy", 
            "theo": 6346.75, "last_price": 6346.5, "orderID": 57632, 
            "coinbase_mid": 6349.985, "clOrdID": "mm_bitmex_EPx3mojZT4yG2L0Zd9ylMQ", 
            "symbol": "XBTUSD", "execInst": "ParticipateDoNotInitiate"}]
        # submit order without changing time, should be rejected
        current_timestamp.return_value = ts
        self.exchange_interface.create_bulk_orders(to_create)
        print(self.exchange_interface.live_orders)
        to_create2 = [{"price": 6346.0, "orderQty": 100, "side": "Buy", 
            "theo": 6346.75, "last_price": 6346, "orderID": 7606, 
            "coinbase_mid": 6349.985, "clOrdID": "mm_bitmex_gR5i6JLFQOGZ1E2+ppZvPw", 
            "symbol": "XBTUSD", "execInst": "ParticipateDoNotInitiate"}]
        self.exchange_interface.create_bulk_orders(to_create2)
        assert len(self.exchange_interface.live_orders) == 1
        # Now submit order one second later, should be accepted
        current_timestamp.return_value = ts + 1
        self.exchange_interface.create_bulk_orders(to_create2)
        print(self.exchange_interface.live_orders)
        assert len(self.exchange_interface.live_orders) == 2


    @patch('market_maker.bitmex.BitMEX')
    @patch('market_maker.paper_trading.PaperTrading')
    @patch('market_maker.backtest.bitmexbacktest.BitMEXbacktest')
    def test_get_orders_returns_order_in_backtest(self, backtest, paper, bitmex): 
        to_create  = [{"price": 6346.0, "orderQty": 100, "side": "Buy", 
            "theo": 6346.75, "last_price": 6346.5, "orderID": 57632, 
            "coinbase_mid": 6349.985, "clOrdID": "mm_bitmex_EPx3mojZT4yG2L0Zd9ylMQ", 
            "symbol": "XBTUSD", "execInst": "ParticipateDoNotInitiate"}]
        self.settings_mock.ORDERID_PREFIX  = "live_"
        self.settings_mock.BACKTEST = True
        self.settings_mock.PAPERTRADING = True
        paper.return_value = MagicMock()
        paper.return_value.get_orders.return_value = to_create
        from market_maker.exchange_interface import ExchangeInterface
        self.exchange_interface = ExchangeInterface(settings=self.settings_mock)
        self.exchange_interface.create_bulk_orders(to_create)       
        orders = self.exchange_interface.get_orders()
        print(orders)
        assert orders[0]['orderID'] == 57632


    @patch('market_maker.bitmex.BitMEX')
    @patch('market_maker.paper_trading.PaperTrading')
    @patch('market_maker.backtest.bitmexbacktest.BitMEXbacktest')
    def test__converge_open_orders(self, backtest, paper, bitmex):
        self.settings_mock.ORDERID_PREFIX  = "live_"
        self.settings_mock.PAPERTRADING = False
        self.settings_mock.BACKTEST = False
        bitmex.return_value = MagicMock()
        to_create  = [{"price": 6346.0, "orderQty": 100, "side": "Buy", 
            "theo": 6346.75, "last_price": 6346.5, "orderID": 57632, 
            "coinbase_mid": 6349.985, "clOrdID": "mm_bitmex_EPx3mojZT4yG2L0Zd9ylMQ", 
            "symbol": "XBTUSD", "execInst": "ParticipateDoNotInitiate"}]
        from_exchange = [{"orderID": "9bb6b5da-729a-b2b3-c7a1-614f9b222784", 
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
            "timestamp": "2018-11-09T17:40:40.755Z"}]

        bitmex.return_value.open_orders.return_value = from_exchange
        from market_maker.exchange_interface import ExchangeInterface
        self.exchange_interface = ExchangeInterface(settings=self.settings_mock)
        self.exchange_interface._generate_clOrdID = Mock()
        self.exchange_interface._generate_clOrdID.return_value = \
            "mm_bitmex_EPx3mojZT4yG2L0Zd9ylMQ"
        # set up timestamp 
        ts = datetime.now().replace(tzinfo=timezone.utc).timestamp()
        self.exchange_interface._current_timestamp = Mock()
        self.exchange_interface._current_timestamp.return_value = ts

        self.exchange_interface.create_bulk_orders(to_create)
        self.exchange_interface._converge_open_orders()
        #print(self.exchange_interface.live_orders)
        assert self.exchange_interface.live_orders == from_exchange

    @patch('market_maker.bitmex.BitMEX')
    @patch('market_maker.paper_trading.PaperTrading')
    @patch('market_maker.backtest.bitmexbacktest.BitMEXbacktest')
    def test_local_orders_live_5_seconds(self, backtest, paper, bitmex):
        self.settings_mock.ORDERID_PREFIX  = "live_"
        self.settings_mock.PAPERTRADING = False
        self.settings_mock.BACKTEST = False
        bitmex.return_value = MagicMock()
        to_create  = [{"price": 6346.0, "orderQty": 100, "side": "Buy", 
            "theo": 6346.75, "last_price": 6346.5, "orderID": 57632, 
            "coinbase_mid": 6349.985, "clOrdID": "mm_bitmex_EPx3mojZT4yG2L0Zd9ylMQ", 
            "symbol": "XBTUSD", "execInst": "ParticipateDoNotInitiate"}]

        bitmex.return_value.open_orders.return_value = []
        from market_maker.exchange_interface import ExchangeInterface
        self.exchange_interface = ExchangeInterface(settings=self.settings_mock)
        self.exchange_interface._generate_clOrdID = Mock()
        self.exchange_interface._generate_clOrdID.return_value = \
            "mm_bitmex_EPx3mojZT4yG2L0Zd9ylMQ"
        # set up timestamp 
        ts = datetime.now().replace(tzinfo=timezone.utc).timestamp()
        self.exchange_interface._current_timestamp = Mock()
        self.exchange_interface._current_timestamp.return_value = ts
        self.exchange_interface.create_bulk_orders(to_create)
        self.exchange_interface._current_timestamp.return_value = ts + 6
        print(ts + 6)
        self.exchange_interface._converge_open_orders()
        print(self.exchange_interface.live_orders)
        assert self.exchange_interface.live_orders == []



    @patch('market_maker.bitmex.BitMEX')
    @patch('market_maker.paper_trading.PaperTrading')
    @patch('market_maker.backtest.bitmexbacktest.BitMEXbacktest')
    def test_return_promise_until_exchange_acks_order(self, backtest, paper, bitmex):
        self.settings_mock.ORDERID_PREFIX  = "live_"
        self.settings_mock.PAPERTRADING = False
        self.settings_mock.BACKTEST = False
        ts = datetime.now().replace(tzinfo=timezone.utc).timestamp()
        from market_maker.exchange_interface import ExchangeInterface
        self.exchange_interface = ExchangeInterface(settings=self.settings_mock)
        to_create  = [{"price": 6346.0, "orderQty": 100, "side": "Buy", 
            "theo": 6346.75, "last_price": 6346.5, "orderID": 57632, 
            "coinbase_mid": 6349.985, "clOrdID": "mm_bitmex_EPx3mojZT4yG2L0Zd9ylMQ", 
            "symbol": "XBTUSD", "execInst": "ParticipateDoNotInitiate"}]
        # submit order without changing time, should be rejected
        ts = datetime.now().replace(tzinfo=timezone.utc).timestamp()
        self.exchange_interface._current_timestamp = Mock()
        self.exchange_interface._current_timestamp.return_value = ts
        self.exchange_interface.create_bulk_orders(to_create)
        orders = self.exchange_interface.get_orders()
        assert orders[0]['orderID'] == 57632

