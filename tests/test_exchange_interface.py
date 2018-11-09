import datetime
import iso8601
from unittest.mock import MagicMock, patch
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

    @patch('market_maker.paper_trading.PaperTrading')
    @patch('market_maker.backtest.bitmexbacktest.BitMEXbacktest')
    def test_places_order_in_live(self, backtest, paper): 
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
        print(paper.return_value.mock_calls)
        paper.return_value.track_orders_created.assert_called()