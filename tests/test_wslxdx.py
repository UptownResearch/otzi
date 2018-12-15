
from unittest.mock import MagicMock, patch, Mock
from unittest import TestCase
from market_maker.lxdx import wslxdx


class Test_Exchange_Interface(TestCase):

    def setUp(self):
        #self.auth_patch = patch.object(exchange_interface, 'AWS4Auth')
        #self.requests_patch = patch.object(exchange_interface, 'requests')
        #self.auth = self.auth_patch.start()
        #self.requests = self.requests_patch.start()\
        pass

    def tearDown(self):
        #self.auth_patch.stop()
        #self.requests_patch.stop()
        pass

    def test_create_class(self):
        try:
            exchange = wslxdx.wsLXDX()
        except:
            assert False
        assert True

    def test_on_message_snapshot(self):

        with patch.object(wslxdx.wsLXDX, "__init__",
                          lambda x, **params: None):
            exchange = wslxdx.wsLXDX()
            exchange.logger = MagicMock()
            exchange.data = {}
            exchange.data['orderBookL2'] = {}
            ws = ""
            message = \
            '{"m": "s", "p": "btc-tusd", "t": 1544125064882256268, "s": 149, "b": [{"px": "4144.0", "qty": "0.053"},{"px": "4143.0", "qty": "0.003"} ], "a": [{"px": "4145.0", "qty": "0.024"}, {"px": "4146.0", "qty": "0.004"}]}'
            exchange._on_message(ws, message)
            print(exchange.data['orderBookL2'])
            assert exchange.data['orderBookL2']["btc-tusd"] == {
                'bids': {4144.0 : 0.053, 4143.0: 0.003},
                'asks': {4145.0 : 0.024, 4146.0: 0.004}
             }

    def test_on_message_update(self):
        with patch.object(wslxdx.wsLXDX, "__init__",
                          lambda x, **params: None):
            exchange = wslxdx.wsLXDX()
            exchange.logger = MagicMock()
            exchange.data = {}
            exchange.data['orderBookL2'] = {}
            exchange.data['orderBookL2']["btc-tusd"] = {
                'bids': {4144.0 : 0.053, 4143.0: 0.003},
                'asks': {4145.0 : 0.024, 4146.0: 0.004}
            }
            ws = ""
            message = \
            '{ "m": "u", "p": "btc-tusd", "t": "1542754793988206707", "s": 2, "b": [{"px": "4143.0", "qty": "0.093"}], "a": [{"px": "4145.0", "qty": "0.074"}]}'
            exchange._on_message(ws, message)
            print(exchange.data['orderBookL2'])
            assert exchange.data['orderBookL2']["btc-tusd"] == {
                'bids': {4144.0 : 0.053, 4143.0: 0.093},
                'asks': {4145.0 : 0.074, 4146.0: 0.004}
             }

    def test_on_message_volume(self):
        with patch.object(wslxdx.wsLXDX, "__init__",
                          lambda x, **params: None):
            exchange = wslxdx.wsLXDX()
            exchange.logger = MagicMock()
            exchange.data = {}
            ws = ""
            message = \
            '{"m": "v", "p": "btc-tusd", "events": [{ "t": "1541461093573557000", "s": "sell", "px": 4, "qty": 1}]}'
            exchange._on_message(ws, message)
            print(exchange.data['trade'])
            assert exchange.data['trade']["btc-tusd"] == [
                {"t": "1541461093573557000", "s": "sell", "px": 4, "qty": 1}
            ]
        #{"m": "u", "p": "btc-tusd", "t": 1544738388764184167, "s": 163, "b": [{"px": 4143.0, "qty": 0.853}], "a": []}
        #{"p": "btc-tusd", "m": "v", "events": [{"t": 1544738388653783720, "s": "sell", "px": 4143.0, "qty": 0.1}]}





    def test_on_message_limit_trade_length(self):
        with patch.object(wslxdx.wsLXDX, "__init__",
                          lambda x, **params: None):
            exchange = wslxdx.wsLXDX()
            exchange.logger = MagicMock()
            exchange.MAX_TABLE_LEN = 4
            exchange.data = {'trade': {}}
            exchange.data['trade']["btc-tusd"] = [
                {"t": "1541461093573557000", "s": "sell", "px": 4, "qty": 5},
                {"t": "1541461093573557000", "s": "sell", "px": 4, "qty": 4},
                {"t": "1541461093573557000", "s": "sell", "px": 4, "qty": 3},
                {"t": "1541461093573557000", "s": "sell", "px": 4, "qty": 2}
            ]
            ws = ""
            message = \
            '{"m": "v", "p": "btc-tusd", "events": [{ "t": "1541461093573557000", "s": "sell", "px": 4, "qty": 1}]}'
            exchange._on_message(ws, message)
            print(exchange.data['trade'])
            assert exchange.data['trade']["btc-tusd"] == [
                {"t": "1541461093573557000", "s": "sell", "px": 4, "qty": 4},
                {"t": "1541461093573557000", "s": "sell", "px": 4, "qty": 3},
                {"t": "1541461093573557000", "s": "sell", "px": 4, "qty": 2},
                {"t": "1541461093573557000", "s": "sell", "px": 4, "qty": 1}
            ]

    def test_get_ticker(self):
        with patch.object(wslxdx.wsLXDX, "__init__",
                          lambda x, **params: None):
            exchange = wslxdx.wsLXDX()
            exchange.data = {'orderBookL2':{}}
            exchange.data['orderBookL2']["btc-tusd"] = {
                'bids': {4144.0 : 0.053, 4143.0: 0.003},
                'asks': {4145.0 : 0.024, 4146.0: 0.004}
            }
            result = exchange.get_ticker('btc-tusd')
            mid = (4144.0 + 4145.0)/2
            assert result == {
                'buy' : 4144.0,
                'sell' : 4145.0,
                'mid' : mid,
                'bid': 4144.0,
                'bidVolume': 0.053,
                'ask': 4145.0,
                'askVolume': 0.024,
            }

    def test_get_orderbook(self):
        with patch.object(wslxdx.wsLXDX, "__init__",
                          lambda x, **params: None):
            exchange = wslxdx.wsLXDX()
            exchange.symbol = "btc-tusd"
            exchange.data = {'orderBookL2':{}}
            exchange.data['orderBookL2']["btc-tusd"] = {
                'bids': {4144.0 : 0.053, 4143.0: 0.003},
                'asks': {4145.0 : 0.024, 4146.0: 0.004}
            }
            result = exchange.get_orderbook('btc-tusd')
            assert result == {
                'bids': {4144.0 : 0.053, 4143.0: 0.003},
                'asks': {4145.0 : 0.024, 4146.0: 0.004}
            }

    def test_recent_trades(self):
        with patch.object(wslxdx.wsLXDX, "__init__",
                          lambda x, **params: None):
            exchange = wslxdx.wsLXDX()
            exchange.symbol = "btc-tusd"
            exchange.data = {'trade': {
                 "btc-tusd" : [{"t": 1544738388653783720, "s": "sell",
                                "px": 4143.0, "qty": 0.1}]}
            }
            result = exchange.recent_trades()
            assert result == [{"t": 1544738388653783720, "s": "sell",
                                "px": 4143.0, "qty": 0.1}]

    def test_recent_trades_no_trades(self):
        with patch.object(wslxdx.wsLXDX, "__init__",
                          lambda x, **params: None):
            exchange = wslxdx.wsLXDX()
            exchange.symbol = "btc-tusd"
            exchange.data = {}
            result = exchange.recent_trades()
            assert result == []