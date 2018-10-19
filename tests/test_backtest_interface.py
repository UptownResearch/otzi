from unittest.mock import MagicMock, patch
from unittest import TestCase
import os
import os.path
#from market_maker.backtest.exchangepairaccessor import ExchangePairAccessor
import iso8601
# Find code directory relative to our directory
from os.path import dirname, abspath, join
import sys
THIS_DIR = dirname(__file__)
CODE_DIR = abspath(join(THIS_DIR, '..' ))
sys.path.append(CODE_DIR)
from market_maker.backtest.timekeeper import Timekeeper
from market_maker.backtest.backtest_interface import BacktestInterface

from decimal import Decimal


def mock_csv_reader_generator(variable_with_mock_file):
    def read_lines(file, delimiter):
        for x in variable_with_mock_file.split("\n"):
            yield x.split(';')
    return read_lines

#reader_calls = [mock_csv_reader_generator(bitmex_trades_end),
#                      mock_csv_reader_generator(orderbook)]
#def multiple_calls(file, delimiter):
#    return reader_calls.pop(0)(file, delimiter)

directory = os.path.split(os.path.abspath(__file__))[0]
MEX_BTC_USD =  directory + '/test_files/bitmex_trades_test.csv'
MEX_OB_BTC_USD = directory + '/test_files/bitmex_ob_test.csv'

class Test_BacktestInterface(TestCase):

    def setUp(self):
        """
        It's patching time
        """

        #http://www.voidspace.org.uk/python/mock/examples.html#mocking-imports-with-patch-dict
        self.settings_mock = MagicMock()
        modules = {
            'market_maker.settings.settings': self.settings_mock,
            'market_maker.paper_trading.settings': self.settings_mock
        }
        self.settings_mock.DRY_RUN = False
        self.settings_mock.BACKTEST = True
        self.settings_mock.SYMBOL = 'XBTUSD'
        self.module_patcher = patch.dict('sys.modules', modules)
        self.module_patcher.start()

    def tearDown(self):
        """
        Let's clean up
        """

        self.module_patcher.stop()

    def test_check_if_orderbook_empty(self):
        timekeeper = Timekeeper()
        bmex = BacktestInterface(timekeeper = timekeeper, settings = self.settings_mock,
            trades_filename = MEX_BTC_USD, L2orderbook_filename = MEX_OB_BTC_USD)
        timekeeper.initialize()
        print(bmex.check_if_orderbook_empty())
        assert bmex.check_if_orderbook_empty() is True 

        while bmex.check_if_orderbook_empty():
            timekeeper.increment_time()

        assert bmex.check_if_orderbook_empty() is False 

    def test_BackTest_stack(self):
        timekeeper = Timekeeper()
        bmex = BacktestInterface(timekeeper = timekeeper, settings = self.settings_mock,
            trades_filename = MEX_BTC_USD, L2orderbook_filename = MEX_OB_BTC_USD)
        timekeeper.initialize()
        while bmex.check_if_orderbook_empty():
            timekeeper.increment_time()
        print(bmex.get_ticker())
        print(bmex.get_orderbook_time())
        print(bmex.recent_trades()[-1])
        orders =    [{"orderID": "1", "orderQty": 10, "price": 7016.5, "side": "Sell" },
                    {"orderID": "2", "orderQty": 10, "price": 7016, "side": "Buy" }]
        bmex.create_bulk_orders(orders)
        for x in range(20):
            timekeeper.increment_time()
        bmex.loop()
        print(timekeeper.get_time())
        print(bmex.get_position())
        assert bmex.get_position()['currentQty']  == -10

    def test_BackTest_is_warm(self):
        timekeeper = Timekeeper()
        bmex = BacktestInterface(timekeeper = timekeeper, settings = self.settings_mock,
            trades_filename = MEX_BTC_USD, L2orderbook_filename = MEX_OB_BTC_USD)
        timekeeper.initialize()
        assert bmex.is_warm() is not None
        assert bmex.is_warm() == True or bmex.is_warm() == False

    def test_BackTest_wait_update(self):
        bmex = BacktestInterface(settings = self.settings_mock,
            trades_filename = MEX_BTC_USD, L2orderbook_filename = MEX_OB_BTC_USD)
        orders =    [{"orderID": "1", "orderQty": 10, "price": 7016.5, "side": "Sell" },
                    {"orderID": "2", "orderQty": 10, "price": 7016, "side": "Buy" }]
        while bmex.check_if_orderbook_empty():
            timekeeper.increment_time()

        print(bmex.get_ticker())
        print(bmex.get_orderbook_time())
        print(bmex.recent_trades()[-1])
        bmex.create_bulk_orders(orders)
        for x in range(20):
            bmex.wait_update()
        print(bmex.current_timestamp())
        print(bmex.get_position())
        assert bmex.get_position()['currentQty']  == -10

    @patch('market_maker.backtest.exchangepairaccessor.ExchangePairAccessor')
    @patch('market_maker.paper_trading.PaperTrading')
    def test_order_qty_type(self, paper, EPA):
        self.timekeeper = MagicMock()
        EPA = MagicMock()
        paper = MagicMock()
        self.bt = BacktestInterface(settings = self.settings_mock,
            trades_filename = MEX_BTC_USD, 
            L2orderbook_filename = MEX_OB_BTC_USD,
            orderqty_type = 'USD')
        assert self.bt.get_orderqty_type() == 'USD'
        self.bt2 = BacktestInterface(settings = self.settings_mock,
            trades_filename = MEX_BTC_USD, 
            L2orderbook_filename = MEX_OB_BTC_USD,
            orderqty_type = 'BTC')
        assert self.bt2.get_orderqty_type() == 'BTC'
 


