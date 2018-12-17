from unittest.mock import MagicMock, patch, Mock
from unittest import TestCase
from market_maker import lxdxinterface



class Test_Exchange_Interface(TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_create_class(self):
        try:
            with patch.object(lxdxinterface.lxdxInterface, "__init__",
                              lambda x, **params: None):
                exchange = lxdxinterface.lxdxInterface()
        except Exception as e:
            print(e)
            assert False
        assert True

    def test_init_sets_up_REST_and_data_ws(self):
        with patch('market_maker.lxdx.auth_lxdx.AccountConnection') as account_con:
            with patch('market_maker.lxdx.wslxdx.wsLXDX') as ws:
                account_con.return_value = MagicMock()
                ws.return_value = MagicMock()
                exchange = lxdxinterface.lxdxInterface()
                print(account_con.called)
                account_con.assert_called()
                account_con.return_value.connect.assert_called()
                ws.assert_called()
                ws.return_value.connect.assert_called()

    def test_get_instrument(self):
        with patch.object(lxdxinterface.lxdxInterface, "__init__",
                          lambda x, **params: None):
            exchange = lxdxinterface.lxdxInterface()
            exchange.account = MagicMock()
            exchange.symbol = "btc-tusd"
            exchange.account.get_products.return_value = \
                {"btc-tusd": {"symbol": "btc-tusd", "security_id": "67", "contract_id": "1",
                                  "security_id_num": "33", "security_id_denom": "81", "num_ratio": "1",
                                  "denom_ratio": "1", "num_typeid": "1", "denom_typeid": "1", "maker_fee": "-0.0002",
                                  "taker_fee": "0.0012", "quotation_id": "33", "quotation_type_id": "1",
                                  "quotation_tick_size_decimals": "3", "price_size_mult": "1000000",
                                  "price_tick_size_decimals": "0", "price_tick_size": "1", "qty_size_mult": "1000000",
                                  "qty_tick_size": "0.001", "qty_tick_size_decimals": "3", "min_qty": "0.001",
                                  "max_qty": "9999", "min_price": "0.001", "max_price": "999999", "settlement_id": "81",
                                  "settlement_type_id": "1", "settlement_tick_size_decimals": "3",
                                  "value_of_point": "1"}}
            result = exchange.get_instrument()
            instrument = exchange.get_instrument("btc-tusd")
            assert 'tickLog' in instrument
            print(instrument['tickLog'])
            assert instrument['tickLog'] == 1
            assert instrument['tickSize'] == 1


    def test_get_ticker(self):
        with patch.object(lxdxinterface.lxdxInterface, "__init__",
                          lambda x, **params: None):
            exchange = lxdxinterface.lxdxInterface()
            exchange.feed = MagicMock()
            exchange.symbol = "btc-tusd"
            exchange.feed.get_ticker.return_value = {
                    'buy' : 4144.0,
                    'sell' : 4145.0,
                    'mid' : (4144.0 + 4145.0)/2,
                    'bid': 4144.0,
                    'bidVolume': 0.053,
                    'ask': 4145.0,
                    'askVolume': 0.024,
                }
            result = exchange.get_ticker("btc-tusd")
            exchange.feed.get_ticker.assert_called_with("btc-tusd")
            assert result == {
                    'buy' : 4144.0,
                    'sell' : 4145.0,
                    'mid' : (4144.0 + 4145.0)/2,
                    'bid': 4144.0,
                    'bidVolume': 0.053,
                    'ask': 4145.0,
                    'askVolume': 0.024,
                }

    def test_get_orders(self):
        with patch.object(lxdxinterface.lxdxInterface, "__init__",
                          lambda x, **params: None):
            exchange = lxdxinterface.lxdxInterface()
            exchange.account = MagicMock()
            exchange.symbol = "btc-tusd"
            exchange.account.get_orders.return_value = \
                {'request_id': '392368834', 'order_start_index': '0', 'total_orders': '2', 'num_orders': '2',
                 'orders': [{'price': 4500.0, 'qty': 0.1, 'remaining_qty': 0.1, 'order_id': '9386821750097823867',
                             'customer_order_ref': '274926922', 'symbol': 'btc-tusd', 'side': 'buy',
                             'post_only': '0', 'time_in_force': 'DAY', 'state': '1', 'request_id': '748504350',
                             'original_qty': 0.1, 'timestamp': '1544481038176407095'},
                            {'price': 5000.1, 'qty': 0.2, 'remaining_qty': 0.2, 'order_id': '9386821750097479803',
                             'customer_order_ref': '4456549', 'symbol': 'btc-tusd', 'side': 'sell',
                             'post_only': '1', 'time_in_force': 'GTC', 'state': '1', 'request_id': '12234345',
                             'original_qty': 0.2, 'timestamp': '1544222257062996209'}]}
            orders = exchange.get_orders('btc-tusd')
            # Check output
            assert orders == [{'price': 4500.0, 'qty': 0.1, 'remaining_qty': 0.1, 'order_id': '9386821750097823867',
                             'customer_order_ref': '274926922', 'symbol': 'btc-tusd', 'side': 'Buy',
                             'post_only': '0', 'time_in_force': 'DAY', 'state': '1', 'request_id': '748504350',
                             'original_qty': 0.1, 'timestamp': '1544481038176407095', 'orderID': '9386821750097823867',
                               'ordStatus' : 'Open', 'orderQty':  0.1 },
                            {'price': 5000.1, 'qty': 0.2, 'remaining_qty': 0.2, 'order_id': '9386821750097479803',
                             'customer_order_ref': '4456549', 'symbol': 'btc-tusd', 'side': 'Sell',
                             'post_only': '1', 'time_in_force': 'GTC', 'state': '1', 'request_id': '12234345',
                             'original_qty': 0.2, 'timestamp': '1544222257062996209', 'orderID': '9386821750097479803',
                             'ordStatus': 'Open', 'orderQty':  0.2}]
            print(orders)
            assert orders[0]['side'] == 'Buy'
            assert orders[0]['orderID'] == '9386821750097823867'
            assert orders[0]['ordStatus'] == 'Open'
            assert orders[0]['orderQty'] == 0.1

    def test_get_orders_no_orders(self):
        with patch.object(lxdxinterface.lxdxInterface, "__init__",
                          lambda x, **params: None):
            exchange = lxdxinterface.lxdxInterface()
            exchange.account = MagicMock()
            exchange.symbol = "btc-tusd"
            exchange.account.get_orders.return_value = \
                {'request_id': '392368834', 'order_start_index': '0', 'total_orders': '2', 'num_orders': '2',
                 'orders': []}
            orders = exchange.get_orders('btc-tusd')
            # Check output
            assert orders == []

    def test_create_orders(self):
        with patch.object(lxdxinterface.lxdxInterface, "__init__",
                          lambda x, **params: None):
            exchange = lxdxinterface.lxdxInterface()
            exchange.account = MagicMock()
            exchange.symbol = "btc-tusd"
            exchange.logger = MagicMock()
            exchange.account.place.return_value = \
                {'m': 'order_submitted', 'type': '2',
                 'payload': {'response': '0', 'order_id': '9386821750097856635', 'orderId': '9386821750097856635',
                             'customer_order_ref': '21452345234', 'request_id': '228919273',
                             'remaining_quantity': 0.1, 'timestamp': '1544730929631357557', 'price': 4400.0,
                             'qty': 0.1, 'symbol': 'btc-tusd', 'side': 'buy'}}
            order = {
                'type': 'limit',
                'side': 'Buy',
                'price': 4400.0,
                'orderQty': 0.1,
                'postonly': True
            }
            exchange.create_order(order)
            exchange.account.place.assert_called_with(4400, 0.1, 'btc-tusd', 'buy', time_in_force='DAY',
                                    type='limit', post_only=True)

    def test_cancel_order(self):
        with patch.object(lxdxinterface.lxdxInterface, "__init__",
                          lambda x, **params: None):
            exchange = lxdxinterface.lxdxInterface()
            exchange.account = MagicMock()
            exchange.symbol = "btc-tusd"
            exchange.logger = MagicMock()
            exchange.account.cancel.return_value = \
                {'m': 'order_canceled', 'type': '3',
                 'payload': {'order_id': '9386821750097856635', 'unfilledQty': '0.1', 'unfilled_qty': '0.1',
                             'response': '0', 'request_id': '866598873'}}
            order =  {
                'side': 'Buy',
                'price': 4400.0,
                'orderQty': 0.1,
                'orderID': '9386821750097856635'
            }
            exchange.cancel_order(order)
            exchange.account.cancel.assert_called_with('9386821750097856635', 'btc-tusd')

    def test_cancel_all_orders(self):
        with patch.object(lxdxinterface.lxdxInterface, "__init__",
                          lambda x, **params: None):
            exchange = lxdxinterface.lxdxInterface()
            exchange.account = MagicMock()
            exchange.symbol = "btc-tusd"
            exchange.account.get_orders.return_value = \
                {'request_id': '392368834', 'order_start_index': '0', 'total_orders': '2', 'num_orders': '2',
                 'orders': [{'price': 4500.0, 'qty': 0.1, 'remaining_qty': 0.1, 'order_id': '9386821750097823867',
                             'customer_order_ref': '274926922', 'symbol': 'btc-tusd', 'side': 'buy',
                             'post_only': '0', 'time_in_force': 'DAY', 'state': '1', 'request_id': '748504350',
                             'original_qty': 0.1, 'timestamp': '1544481038176407095'},
                            {'price': 5000.1, 'qty': 0.2, 'remaining_qty': 0.2, 'order_id': '9386821750097479803',
                             'customer_order_ref': '4456549', 'symbol': 'btc-tusd', 'side': 'sell',
                             'post_only': '1', 'time_in_force': 'GTC', 'state': '1', 'request_id': '12234345',
                             'original_qty': 0.2, 'timestamp': '1544222257062996209'}]}
            exchange.cancel_all_orders()
            exchange.account.cancel.assert_any_call('9386821750097823867', 'btc-tusd')
            exchange.account.cancel.assert_any_call('9386821750097479803', 'btc-tusd')

    def test_get_position(self):
        with patch.object(lxdxinterface.lxdxInterface, "__init__",
                          lambda x, **params: None):
            exchange = lxdxinterface.lxdxInterface()
            exchange.account = MagicMock()
            exchange.account.get_position.return_value = \
                    {"request_id": "23453452",
                       "coin_tier": "0",
                       "balances": {"usdt": 25000.0, "btc": 15.1,
                                    "eth": 200.0, "xrp": 50000.0,
                                    "tusd": 1230.74996}}
            response = exchange.get_position('btc-tusd')
            assert response['currentQty'] ==  15.1
            assert 'avgCostPrice' in response
            assert 'avgEntryPrice' in response

    def test_get_orderbook(self):
        with patch.object(lxdxinterface.lxdxInterface, "__init__",
                          lambda x, **params: None):
            exchange = lxdxinterface.lxdxInterface()
            exchange.symbol = "btc-tusd"
            exchange.feed = MagicMock()
            exchange.feed.get_orderbook.return_value = \
                {
                    'bids': {4144.0 : 0.053, 4143.0: 0.003},
                    'asks': {4145.0 : 0.024, 4146.0: 0.004}
                }
            result = exchange.get_orderbook()
            assert result == {
                    'bids': {4144.0 : 0.053, 4143.0: 0.003},
                    'asks': {4145.0 : 0.024, 4146.0: 0.004}
                }

    def test_recent_trades(self):
        with patch.object(lxdxinterface.lxdxInterface, "__init__",
                          lambda x, **params: None):
            exchange = lxdxinterface.lxdxInterface()
            exchange.symbol = "btc-tusd"
            exchange.feed = MagicMock()
            exchange.feed.recent_trades.return_value = \
                [{"t": 1544738388653783720, "s": "sell", "px": 4143.0, "qty": 0.1}]
            result = exchange.recent_trades()
            print(result)
            assert result == [{'t': 1544738388653783720, 's': 'sell',
                               'px': 4143.0, 'qty': 0.1, 'price': 4143.0,
                               'size': 0.1, 'side': 'Sell',
                               'timestamp': 1544738388653783720}]
            assert 'side' in result[0]
            assert 'price' in result[0]
            assert 'timestamp' in result[0]
            assert 'size' in result[0]

    def test_get_highest_buy(self):
        with patch.object(lxdxinterface.lxdxInterface, "__init__",
                          lambda x, **params: None):
            with patch.object(lxdxinterface.lxdxInterface, "get_orders") as get_orders:
                exchange = lxdxinterface.lxdxInterface()
                exchange.account = MagicMock()
                exchange.symbol = "btc-tusd"
                get_orders.return_value = \
                    [{'price': 4500.0, 'qty': 0.1, 'remaining_qty': 0.1, 'order_id': '9386821750097823867',
                      'customer_order_ref': '274926922', 'symbol': 'btc-tusd', 'side': 'Buy',
                      'post_only': '0', 'time_in_force': 'DAY', 'state': '1', 'request_id': '748504350',
                      'original_qty': 0.1, 'timestamp': '1544481038176407095', 'orderID': '9386821750097823867',
                      'ordStatus': 'Open', 'orderQty': 0.1},
                     {'price': 5000.1, 'qty': 0.2, 'remaining_qty': 0.2, 'order_id': '9386821750097479803',
                      'customer_order_ref': '4456549', 'symbol': 'btc-tusd', 'side': 'Sell',
                      'post_only': '1', 'time_in_force': 'GTC', 'state': '1', 'request_id': '12234345',
                      'original_qty': 0.2, 'timestamp': '1544222257062996209', 'orderID': '9386821750097479803',
                      'ordStatus': 'Open', 'orderQty': 0.2}]
                result = exchange.get_highest_buy()
                assert result == {'price': 4500.0, 'qty': 0.1, 'remaining_qty': 0.1, 'order_id': '9386821750097823867',
                      'customer_order_ref': '274926922', 'symbol': 'btc-tusd', 'side': 'Buy',
                      'post_only': '0', 'time_in_force': 'DAY', 'state': '1', 'request_id': '748504350',
                      'original_qty': 0.1, 'timestamp': '1544481038176407095', 'orderID': '9386821750097823867',
                      'ordStatus': 'Open', 'orderQty': 0.1}

    def test_get_lowest_sell(self):
        with patch.object(lxdxinterface.lxdxInterface, "__init__",
                          lambda x, **params: None):
            with patch.object(lxdxinterface.lxdxInterface, "get_orders") as get_orders:
                exchange = lxdxinterface.lxdxInterface()
                exchange.account = MagicMock()
                exchange.symbol = "btc-tusd"
                get_orders.return_value = \
                    [{'price': 4500.0, 'qty': 0.1, 'remaining_qty': 0.1, 'order_id': '9386821750097823867',
                      'customer_order_ref': '274926922', 'symbol': 'btc-tusd', 'side': 'Buy',
                      'post_only': '0', 'time_in_force': 'DAY', 'state': '1', 'request_id': '748504350',
                      'original_qty': 0.1, 'timestamp': '1544481038176407095', 'orderID': '9386821750097823867',
                      'ordStatus': 'Open', 'orderQty': 0.1},
                     {'price': 5000.1, 'qty': 0.2, 'remaining_qty': 0.2, 'order_id': '9386821750097479803',
                      'customer_order_ref': '4456549', 'symbol': 'btc-tusd', 'side': 'Sell',
                      'post_only': '1', 'time_in_force': 'GTC', 'state': '1', 'request_id': '12234345',
                      'original_qty': 0.2, 'timestamp': '1544222257062996209', 'orderID': '9386821750097479803',
                      'ordStatus': 'Open', 'orderQty': 0.2}]
                result = exchange.get_lowest_sell()
                assert result == {'price': 5000.1, 'qty': 0.2, 'remaining_qty': 0.2, 'order_id': '9386821750097479803',
                             'customer_order_ref': '4456549', 'symbol': 'btc-tusd', 'side': 'Sell',
                             'post_only': '1', 'time_in_force': 'GTC', 'state': '1', 'request_id': '12234345',
                             'original_qty': 0.2, 'timestamp': '1544222257062996209', 'orderID': '9386821750097479803',
                             'ordStatus': 'Open', 'orderQty':  0.2}

    def test_check_if_orderbook_empty(self):
        with patch.object(lxdxinterface.lxdxInterface, "__init__", lambda x, **params: None):
            with patch.object(lxdxinterface.lxdxInterface, "get_orderbook") as get_orderbook:
                exchange = lxdxinterface.lxdxInterface()
                exchange.account = MagicMock()
                exchange.symbol = "btc-tusd"
                get_orderbook.return_value = {
                'bids': [],
                'asks': [],
                'timestamp': None,
                'datetime': None,
                'nonce': None}
                self.assertRaises(Exception, exchange.check_if_orderbook_empty)

    def test_check_market_open(self):
        with patch.object(lxdxinterface.lxdxInterface, "__init__", lambda x, **params: None):
            with patch.object(lxdxinterface.lxdxInterface, "get_instrument") as get_instrument:
                exchange = lxdxinterface.lxdxInterface()
                exchange.account = MagicMock()
                exchange.symbol = "btc-tusd"
                get_instrument.return_value = \
                 {"symbol": "btc-tusd", "security_id": "67", "contract_id": "1",
                                  "security_id_num": "33", "security_id_denom": "81", "num_ratio": "1",
                                  "denom_ratio": "1", "num_typeid": "1", "denom_typeid": "1", "maker_fee": "-0.0002",
                                  "taker_fee": "0.0012", "quotation_id": "33", "quotation_type_id": "1",
                                  "quotation_tick_size_decimals": "3", "price_size_mult": "1000000",
                                  "price_tick_size_decimals": "0", "price_tick_size": "1", "qty_size_mult": "1000000",
                                  "qty_tick_size": "0.001", "qty_tick_size_decimals": "3", "min_qty": "0.001",
                                  "max_qty": "9999", "min_price": "0.001", "max_price": "999999", "settlement_id": "81",
                                  "settlement_type_id": "1", "settlement_tick_size_decimals": "3",
                                  "value_of_point": "1"}
                result = exchange.check_market_open()
                exchange.get_instrument.assert_called()
                # Now test failing condition
                get_instrument.return_value = {}
                self.assertRaises(Exception, exchange.check_market_open)

    def test_create_bulk_orders(self):
        with patch.object(lxdxinterface.lxdxInterface, "__init__", lambda x, **params: None):
            with patch.object(lxdxinterface.lxdxInterface, "create_order") as create_order:
                exchange = lxdxinterface.lxdxInterface()
                exchange.account = MagicMock()
                exchange.symbol = "btc-tusd"
                orders = [ {
                    'type': 'limit',
                    'side': 'Buy',
                    'price': 4400.0,
                    'orderQty': 0.1
                }, {
                    'type': 'limit',
                    'side': 'Sell',
                    'price': 4500.0,
                    'orderQty': 0.1
                }]
                exchange.create_bulk_orders(orders)
                print(create_order.call_args_list)
                create_order.assert_any_call({
                    'type': 'limit',
                    'side': 'Buy',
                    'price': 4400.0,
                    'orderQty': 0.1
                })
                create_order.assert_any_call({
                    'type': 'limit',
                    'side': 'Sell',
                    'price': 4500.0,
                    'orderQty': 0.1
                })

    def test_amend_bulk_orders(self):
        with patch.object(lxdxinterface.lxdxInterface, "__init__", lambda x, **params: None):
            with patch.object(lxdxinterface.lxdxInterface, "cancel_order") as cancel_order:
                with patch.object(lxdxinterface.lxdxInterface, "create_order") as create_order:
                    exchange = lxdxinterface.lxdxInterface()
                    exchange.symbol = "btc-tusd"
                    exchange.logger = MagicMock()
                    orders = [{
                        'side': 'sell',
                        'price': 12000.0,
                        'orderQty': 0.01,
                        'orderID': '12'
                    }, {
                        'side': 'buy',
                        'price': 11000.0,
                        'orderQty': 0.01,
                        'orderID' : '13'
                    }]
                    exchange.amend_bulk_orders(orders)
                    exchange.cancel_order.assert_called()
                    exchange.create_order.assert_called()