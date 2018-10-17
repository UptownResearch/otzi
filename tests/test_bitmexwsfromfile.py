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
        modules = {
            'market_maker.exchange_interface' : self.exchange_interface,
            'market_maker.coinbase.order_book' : self.coinbase_book,
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
        from market_maker.backtest.bitmexwsfromfile import BitMEXwsFromFile
        bitmexws = BitMEXwsFromFile(settings=self.settings_mock)
        print("This is seen")
        assert bitmexws is not None

    @patch('market_maker.backtest.bitmexwsfromfile.open')
    def test_patch_example(self, _open):
        _open = MagicMock()
        _open.return_value = MagicMock().readlines.ret_value = ''
        #from market_maker.backtest.bitmexwsfromfile import BitMEXwsFromFile
        #bitmexws = BitMEXwsFromFile(settings=self.settings_mock)
        #print("This is seen")
        #assert bitmexws is not None
        pass