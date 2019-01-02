from unittest.mock import MagicMock, patch, Mock
from unittest import TestCase
from market_maker import order_services



class Test_order_services(TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_create_class(self):
        try:
            with patch.object(order_services.orderServices, "__init__",
                              lambda x, **params: None):
                os = order_services.orderServices()
        except Exception as e:
            print(e)
            assert False
        assert True

    def test_cancel_all_orders(self):
        with patch.object(order_services.orderServices, "__init__",
                          lambda x, **params: None):
            os = order_services.orderServices()
            os.cancelled_orders = []
            exchange = MagicMock()
            order1 = {"orderID": "order1"}
            order2 = {"orderID": "order2"}
            orders = [order1, order2]
            result = os.cancel_all_orders(exchange, orders)
            exchange.cancel_all_orders.assert_called()

    def test_desired_to_orders_create_two_new_orders(self):
        with patch.object(order_services.orderServices, "__init__",
                          lambda x, **params: None):
            om =  order_services.orderServices()
            exchange = MagicMock()
            exchange.get_instrument.return_value = {'tickLog': 1}
            exchange.get_orders.return_value = []
            exchange.get_ticker.return_value = {'last': 6433.5, 'buy': 6433.0, 'sell': 6433.5, 'mid': 6433.0}
            exchange.recent_trades.return_value = \
            [{'timestamp': '2018-07-19T18:51:15.606Z', 'symbol': 'XBTUSD', 'side': 'Sell',
            'size': 100, 'price': 6433.5, 'tickDirection': 'MinusTick',
            'trdMatchID': 'dddb8785-7156-f030-b325-c35daed19640', 'grossValue': 1349100,
            'homeNotional': 0.013491, 'foreignNotional': 100}]
            om.desired_to_orders(exchange, 6430, 6440)
            exchange.create_bulk_orders.assert_called()
            assert len(exchange.create_bulk_orders.call_args[0][0]) == 2

    def test_desired_to_orders_update_orders_(self):
        with patch.object(order_services.orderServices, "__init__",
                          lambda x, **params: None):
            om =  order_services.orderServices()
            om.cancelled_orders = []
            exchange = MagicMock()
            exchange.get_instrument.return_value = {'tickLog': 1}
            om.desired_to_orders(exchange, 6429, 6439,
                                    buyamount = 0,
                                    sellamount = 0)
            # No orders should have been created
            assert exchange.create_bulk_orders.call_args is None

    def test_desired_to_orders_create_one_order(self):
        with patch.object(order_services.orderServices, "__init__",
                          lambda x, **params: None):
            om =  order_services.orderServices()
            om.cancelled_orders = []
            exchange = MagicMock()
            exchange.get_instrument.return_value = {'tickLog': 1}
            exchange.get_orders.return_value = [{'price': 6430, 'orderQty': 100, 'side': 'Buy', 'theo': 6433.5, 'last_price': 6433.5, 'orderID': 68312, 'coinbase_mid': 6433.25}]
            exchange.get_ticker.return_value = {'last': 6433.5, 'buy': 6433.0, 'sell': 6433.5, 'mid': 6433.0}
            exchange.recent_trades.return_value = \
            [{'timestamp': '2018-07-19T18:51:15.606Z', 'symbol': 'XBTUSD', 'side': 'Sell',
            'size': 100, 'price': 6433.5, 'tickDirection': 'MinusTick',
            'trdMatchID': 'dddb8785-7156-f030-b325-c35daed19640', 'grossValue': 1349100,
            'homeNotional': 0.013491, 'foreignNotional': 100}]
            #self.om.coinbase.get_bid.return_value = 6433.0
            #self.om.coinbase.get_ask.return_value = 6433.5
            om.desired_to_orders(exchange, 6430, 6440)
            exchange.create_bulk_orders.assert_called()
            assert len(exchange.create_bulk_orders.call_args[0][0]) == 1

    def test_desired_to_orders_update_orders(self):
        with patch.object(order_services.orderServices, "__init__",
                          lambda x, **params: None):
            om =  order_services.orderServices()
            om.cancelled_orders = []
            exchange = MagicMock()
            exchange.get_instrument.return_value = {'tickLog': 1}
            exchange.get_orders.return_value = \
            [{'price': 6430, 'orderQty': 100, 'side': 'Buy', 'theo': 6433.5,
            'last_price': 6433.5, 'orderID': 33929, 'coinbase_mid': 6433.25,
            "leavesQty": 100, 'cumQty': 0, 'ordStatus' : 'New'},
            {'price': 6440, 'orderQty': 100, 'side': 'Sell', 'theo': 6433.5,
            'last_price': 6433.5, 'orderID': 10429, 'coinbase_mid': 6433.25,
            "leavesQty": 100, 'cumQty': 0, 'ordStatus' : 'New' }]
            exchange.get_ticker.return_value = {'last': 6433.5, 'buy': 6433.0, 'sell': 6433.5, 'mid': 6433.0}
            exchange.recent_trades.return_value = \
            [{'timestamp': '2018-07-19T18:51:15.606Z', 'symbol': 'XBTUSD', 'side': 'Sell',
            'size': 100, 'price': 6433.5, 'tickDirection': 'MinusTick',
            'trdMatchID': 'dddb8785-7156-f030-b325-c35daed19640', 'grossValue': 1349100,
            'homeNotional': 0.013491, 'foreignNotional': 100}]
            om.desired_to_orders(exchange, 6429, 6439)
            exchange.create_bulk_orders.assert_not_called()
            exchange.amend_bulk_orders.assert_called()
            assert len(exchange.amend_bulk_orders.call_args[0][0]) == 2
            print(exchange.amend_bulk_orders.call_args[0][0])

    def test_desired_to_orders_cancels_extra_orders(self):
        with patch.object(order_services.orderServices, "__init__",
                          lambda x, **params: None):
            om = order_services.orderServices()
            om.cancelled_orders = []
            exchange = MagicMock()
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
            assert om.is_live_order(order1) == False
            assert om.is_live_order(order2) == True

    def test_create_cancel_orders_from_orders(self):
        with patch.object(order_services.orderServices, "__init__",
                          lambda x, **params: None):
            om = order_services.orderServices()
            om.cancelled_orders = []
            exchange = MagicMock()
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
            result = om.create_cancel_orders_from_orders(orders)
            assert len(result) == 1
            assert result[0]['orderID'] == "9bb6b5da-729a-b2b3-c7a1-614f9b222784"

    def test_cancel_all_orders(self):
        with patch.object(order_services.orderServices, "__init__",
                          lambda x, **params: None):
            om = order_services.orderServices()
            om.cancelled_orders = []
            exchange = MagicMock()
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
            result = om.cancel_all_orders(exchange, orders)
            exchange.cancel_all_orders.assert_called()
            assert len(om.cancelled_orders) == 1
