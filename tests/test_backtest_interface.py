from unittest.mock import MagicMock, patch
from unittest import TestCase
import os
import os.path
#from market_maker.backtest.exchangepairaccessor import ExchangePairAccessor
import iso8601
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

    def test_BackTest_stack(self):
        timekeeper = Timekeeper()
        bmex = BacktestInterface(timekeeper = timekeeper, 
            trades_filename = MEX_BTC_USD, L2orderbook_filename = MEX_OB_BTC_USD)
        timekeeper.initialize()
        orders =    [{"orderID": "1", "orderQty": 10, "price": 7017.5, "side": "Sell" },
                    {"orderID": "2", "orderQty": 10, "price": 7017, "side": "Buy" }]
        bmex.create_bulk_orders(orders)
        for x in range(5):
            timekeeper.increment_time()
        bmex.loop()
        print(timekeeper.get_time())
        print(bmex.get_position())
        assert bmex.get_position()['currentQty']  == 10
