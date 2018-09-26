from unittest.mock import MagicMock, patch
from unittest import TestCase
import os
import os.path
from market_maker.backtest.exchangepairaccessor import ExchangePairAccessor
import iso8601
from market_maker.backtest.timekeeper import Timekeeper
from decimal import Decimal

bitmex_trades_file = \
'''time_exchange;time_coinapi;guid;price;base_amount;taker_side
2018-09-01T00:00:03.9320000;2018-09-01T00:00:05.3029459;5caec0c2-09f0-4232-8601-3e4e07521b73;7017;2000;SELL
2018-09-01T00:00:03.9880000;2018-09-01T00:00:05.3341976;d8bd9dfb-2ff3-40d3-b2b8-3ba5c8dcf06a;7017;685;SELL'''

timekeeper_parameters = [
iso8601.parse_date('2018-09-01T00:00:05.3029459'),
iso8601.parse_date('2018-09-01T00:00:05.3341976')
]

gdax_trades_file = \
'''time_exchange;time_coinapi;guid;price;base_amount;taker_side
2018-09-01T00:00:00.1580000;2018-09-01T00:00:01.0352064;a152778e-841d-4b1b-b4ac-23b0298284dd;7015.01;0.00397244;BUY
2018-09-01T00:00:00.3680000;2018-09-01T00:00:06.1289766;b0832333-c9d9-4ebe-8ac6-595baa3e8797;7015.01;0.00836892;BUY'''

#Deal with end cases

bitstamp_trades_end = \
'''2018-09-01T23:57:48.0000000;2018-09-01T23:57:49.1372185;6571505c-660c-42f4-b20d-4b6f9b5c70dd;7195.85;0.008053;BUY
2018-09-01T23:59:24.0000000;2018-09-01T23:59:24.4263571;babf4659-2cb8-401c-9a35-4f1c039ca5f7;7190.48;0.00280364;SELL
2018-09-01T23:59:24.0000000;2018-09-01T23:59:24.5044859;9dfcd286-ede2-4e9f-ad62-805b5d317f1b;7185.01;0.20791601;SELL
2018-09-01T23:59:24.0000000;2018-09-01T23:59:24.8638560;aae0de42-57f3-464e-8ca7-44f507a06ce3;7185.01;0.38928035;BUY'''

bitmex_trades_end = \
'''2018-09-01T23:56:53.8160000;2018-09-01T23:59:53.8915902;e75c27f2-1173-4331-ae73-b9dc9f658fd9;7196;39;SELL
2018-09-01T23:59:53.8160000;2018-09-01T23:59:53.8915902;aa2d9005-4183-4971-b98f-ec9e8d24b0ab;7196;5919;SELL
2018-09-01T23:59:53.9880000;2018-09-01T23:59:54.0321988;50d1fe3a-8332-4162-8f1e-22ee24a8c945;7196.5;250;BUY'''

orderbook = \
'''time_exchange;time_coinapi;asks[0].price;asks[0].size;bids[0].price;bids[0].size;asks[1].price;asks[1].size;bids[1].price;bids[1].size;asks[2].price;asks[2].size;bids[2].price;bids[2].size;asks[3].price;asks[3].size;bids[3].price;bids[3].size;asks[4].price;asks[4].size;bids[4].price;bids[4].size;asks[5].price;asks[5].size;bids[5].price;bids[5].size;asks[6].price;asks[6].size;bids[6].price;bids[6].size;asks[7].price;asks[7].size;bids[7].price;bids[7].size;asks[8].price;asks[8].size;bids[8].price;bids[8].size;asks[9].price;asks[9].size;bids[9].price;bids[9].size;asks[10].price;asks[10].size;bids[10].price;bids[10].size;asks[11].price;asks[11].size;bids[11].price;bids[11].size;asks[12].price;asks[12].size;bids[12].price;bids[12].size;asks[13].price;asks[13].size;bids[13].price;bids[13].size;asks[14].price;asks[14].size;bids[14].price;bids[14].size;asks[15].price;asks[15].size;bids[15].price;bids[15].size;asks[16].price;asks[16].size;bids[16].price;bids[16].size;asks[17].price;asks[17].size;bids[17].price;bids[17].size;asks[18].price;asks[18].size;bids[18].price;bids[18].size;asks[19].price;asks[19].size;bids[19].price;bids[19].size;asks[20].price;asks[20].size;bids[20].price;bids[20].size;asks[21].price;asks[21].size;bids[21].price;bids[21].size;asks[22].price;asks[22].size;bids[22].price;bids[22].size;asks[23].price;asks[23].size;bids[23].price;bids[23].size;asks[24].price;asks[24].size;bids[24].price;bids[24].size;asks[25].price;asks[25].size;bids[25].price;bids[25].size;asks[26].price;asks[26].size;bids[26].price;bids[26].size;asks[27].price;asks[27].size;bids[27].price;bids[27].size;asks[28].price;asks[28].size;bids[28].price;bids[28].size;asks[29].price;asks[29].size;bids[29].price;bids[29].size;asks[30].price;asks[30].size;bids[30].price;bids[30].size;asks[31].price;asks[31].size;bids[31].price;bids[31].size;asks[32].price;asks[32].size;bids[32].price;bids[32].size;asks[33].price;asks[33].size;bids[33].price;bids[33].size;asks[34].price;asks[34].size;bids[34].price;bids[34].size;asks[35].price;asks[35].size;bids[35].price;bids[35].size;asks[36].price;asks[36].size;bids[36].price;bids[36].size;asks[37].price;asks[37].size;bids[37].price;bids[37].size;asks[38].price;asks[38].size;bids[38].price;bids[38].size;asks[39].price;asks[39].size;bids[39].price;bids[39].size;asks[40].price;asks[40].size;bids[40].price;bids[40].size;asks[41].price;asks[41].size;bids[41].price;bids[41].size;asks[42].price;asks[42].size;bids[42].price;bids[42].size;asks[43].price;asks[43].size;bids[43].price;bids[43].size;asks[44].price;asks[44].size;bids[44].price;bids[44].size;asks[45].price;asks[45].size;bids[45].price;bids[45].size;asks[46].price;asks[46].size;bids[46].price;bids[46].size;asks[47].price;asks[47].size;bids[47].price;bids[47].size;asks[48].price;asks[48].size;bids[48].price;bids[48].size;asks[49].price;asks[49].size;bids[49].price;bids[49].size
00:00:03.8720000;00:00:05.2248216;7017.5;1597363;7017;65368;7018;956431;7016.5;13797;7018.5;30008;7016;184411;7019;24084;7015.5;29273;7019.5;166519;7015;216282;7020;37891;7014.5;72674;7020.5;40007;7014;38954;7021;25927;7013.5;13938;7021.5;99827;7013;78106;7022;17217;7012.5;79297;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
00:00:03.8850000;00:00:05.2560712;7017.5;1597363;7017;65368;7018;955831;7016.5;13797;7018.5;30008;7016;184411;7019;24084;7015.5;29273;7019.5;166519;7015;216282;7020;37891;7014.5;72674;7020.5;40007;7014;38954;7021;25927;7013.5;13938;7021.5;99827;7013;78106;7022;17217;7012.5;79297;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
00:00:03.8880000;00:00:05.2560712;7017.5;1597363;7017;65365;7018;955831;7016.5;13772;7018.5;30008;7016;184386;7019;24084;7015.5;29273;7019.5;166519;7015;216257;7020;37891;7014.5;72674;7020.5;40007;7014;38954;7021;25927;7013.5;13938;7021.5;99827;7013;78106;7022;17217;7012.5;79297;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;'''



def mock_csv_reader_generator(variable_with_mock_file):
    def read_lines(file, delimiter):
        for x in variable_with_mock_file.split("\n"):
            yield x.split(';')
    return read_lines


reader_calls = [mock_csv_reader_generator(bitmex_trades_end),
                      mock_csv_reader_generator(orderbook)]
def multiple_calls(file, delimiter):
    return reader_calls.pop(0)(file, delimiter)

class Test_ExchangePairAccessor(TestCase):


    @patch('market_maker.backtest.exchangepairaccessor.csv.reader', side_effect=mock_csv_reader_generator(bitmex_trades_file))
    @patch('market_maker.backtest.exchangepairaccessor.open')
    def test_calls_timekeeper(self,  new_open, reader_function):
        self.timekeeper = MagicMock()
        self.bt = ExchangePairAccessor(timekeeper = self.timekeeper, trades_filename = "fake.csv")
        print(self.bt._trade_data)
        self.timekeeper.contribute_times.assert_called_with(timekeeper_parameters)
        new_open.assert_called_with("fake.csv")

    @patch('market_maker.backtest.exchangepairaccessor.csv.reader', side_effect=mock_csv_reader_generator(bitmex_trades_file))
    @patch('market_maker.backtest.exchangepairaccessor.open')
    def test_EPA_check_timestamps_sync(self,  new_open, reader_function):
        self.timekeeper = Timekeeper()
        self.bt = ExchangePairAccessor(timekeeper = self.timekeeper, trades_filename = "fake.csv")

        #now load GDAX
        reader_function.side_effect = mock_csv_reader_generator(gdax_trades_file)
        self.gdax_accessor = ExchangePairAccessor(timekeeper = self.timekeeper, trades_filename = "fake.csv")
        self.timekeeper.initialize()
        assert self.bt.current_timestamp() == self.gdax_accessor.current_timestamp()
        #increment time and check again
        self.timekeeper.increment_time()
        assert self.bt.current_timestamp() == self.gdax_accessor.current_timestamp()

    @patch('market_maker.backtest.exchangepairaccessor.csv.reader', side_effect=mock_csv_reader_generator(bitmex_trades_file))
    @patch('market_maker.backtest.exchangepairaccessor.open')
    def test_EPA_fail_if_not_warm(self,  new_open, reader_function):
        self.timekeeper = Timekeeper()
        self.bt = ExchangePairAccessor(timekeeper = self.timekeeper, trades_filename = "fake.csv")

        #now load GDAX
        reader_function.side_effect = mock_csv_reader_generator(gdax_trades_file)
        self.gdax_accessor = ExchangePairAccessor(timekeeper = self.timekeeper, trades_filename = "fake.csv")
        self.timekeeper.initialize()
        self.assertRaises(Exception, self.bt.recent_trades)

    @patch('market_maker.backtest.exchangepairaccessor.csv.reader', side_effect=mock_csv_reader_generator(bitmex_trades_file))
    @patch('market_maker.backtest.exchangepairaccessor.open')
    def test_EPA_price_should_be_correct_at_time(self,  new_open, reader_function):
        self.timekeeper = Timekeeper()
        self.bt = ExchangePairAccessor(timekeeper = self.timekeeper, trades_filename = "fake.csv")

        #now load GDAX
        reader_function.side_effect = mock_csv_reader_generator(gdax_trades_file)
        self.gdax_accessor = ExchangePairAccessor(timekeeper = self.timekeeper, trades_filename = "fake.csv")
        self.timekeeper.initialize()
        while not(self.bt.is_warm() & self.gdax_accessor.is_warm()):
            self.timekeeper.increment_time()
        assert self.bt.recent_trades()[-1]['price'] == Decimal('7017')
        assert self.gdax_accessor.recent_trades()[-1]['price'] == Decimal('7015.01')



    @patch('market_maker.backtest.exchangepairaccessor.csv.reader', side_effect= multiple_calls)
    @patch('market_maker.backtest.exchangepairaccessor.open')
    def test_EPA_should_return_trades_and_orderbook(self,  new_open, reader_function):
        self.timekeeper = Timekeeper()
        self.bt = ExchangePairAccessor(timekeeper = self.timekeeper, trades_filename = "fake.csv", L2orderbook_filename = "fake2.csv")

        self.timekeeper.initialize()
        # increment time to get warm
        while not self.bt.is_warm():
            self.timekeeper.increment_time()
        assert self.bt.recent_trades() != []
        assert self.bt.market_depth() != []

