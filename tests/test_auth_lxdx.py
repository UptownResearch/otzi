
from unittest.mock import MagicMock, patch, Mock
from unittest import TestCase
from market_maker.lxdx import auth_lxdx


class Test_Exchange_Interface(TestCase):

    def setUp(self):
        self.auth_patch = patch.object(auth_lxdx, 'AWS4Auth')
        #self.requests_patch = patch.object(exchange_interface, 'requests')
        self.auth = self.auth_patch.start()
        #self.requests = self.requests_patch.start()

    def tearDown(self):
        self.auth_patch.stop()
        #self.requests_patch.stop()

    def test_create_class(self):
        try:
            exchange = auth_lxdx.AccountConnection()
        except:
            assert False
        assert True


    def test_prep_auth(self):
        settings_mock = {}
        exchange = auth_lxdx.AccountConnection(settings=settings_mock)
        print(exchange._prep_auth())
        print(self.auth.called)
        self.auth.assert_called_with('AKIAIQZAX5JGUTN6GGYQ',
                                'Ljg6cC5IFqt2nalb902y7TRwJb2okokosLQUKPNa',
                                'ap-southeast-1', 'execute-api')

    def test_prep_session(self):
        settings_mock = {}
        with patch.object(auth_lxdx.AccountConnection, "__init__",
                          lambda x, **params: None):
            old_session = auth_lxdx.requests.Session
            auth_lxdx.requests.Session = MagicMock()
            exchange = auth_lxdx.AccountConnection(settings=settings_mock)
            value = exchange._prep_session()
            auth_lxdx.requests.Session.assert_called()
            auth_lxdx.requests.Session.return_value.headers.update.assert_called()
            # Undo Monkey-patch
            auth_lxdx.requests.Session = old_session

    def test_curl_exchange_calls_request(self):
        settings_mock = {}
        session_mock = MagicMock()
        session_mock.return_value = MagicMock()
        old_session = auth_lxdx.requests.Session
        auth_lxdx.requests.Session = session_mock
        exchange = auth_lxdx.AccountConnection(settings=settings_mock)
        response = exchange._curl_exchange(path = 'messages/token')
        print(session_mock.return_value.prepare_request.call_args_list)
        # Undo Monkey-patch
        auth_lxdx.requests.Session = old_session

    def test_curl_exchange_calls_session_send(self):
        settings_mock = {}
        exchange = auth_lxdx.AccountConnection(settings=settings_mock)
        exchange.session.send = Mock()
        response = exchange._curl_exchange(path='messages/token')
        print(dir(exchange.session.send.call_args_list[0][0][0].path_url))
        print(exchange.session.send.call_args_list[0][0][0].path_url)
        assert exchange.session.send.call_args_list[0][0][0].path_url == \
                        '/v1/messages/token'

    def test__get_token(self):
        settings_mock = {}
        with patch.object(auth_lxdx.AccountConnection, "_curl_exchange") as curl_mock:
            curl_mock.return_value = {'token': 'b1053f1b-ddb5-484c-9ef0-4fc3100aae46', 'expires_at': 1544463666}
            exchange = auth_lxdx.AccountConnection(settings=settings_mock)
            token = exchange._get_token()
            assert token == "b1053f1b-ddb5-484c-9ef0-4fc3100aae46"
            print(curl_mock.call_args)
            curl_mock.assert_called_with(path='messages/token')

    def test_connect_provides_correct_wsURL(self):
        settings_mock = {}
        with patch.object(auth_lxdx.AccountConnection, "_curl_exchange") as curl_mock:
            with patch.object(auth_lxdx.AccountConnection, "_connect") as connect_mock:
                curl_mock.return_value = {'token': 'b1053f1b-ddb5-484c-9ef0-4fc3100aae46', 'expires_at': 1544463666}
                exchange = auth_lxdx.AccountConnection(settings=settings_mock)
                exchange.connect()
                connect_mock.assert_called_with("wss://iris-cert.lxdx-svcs.net/v1/account?token=b1053f1b-ddb5-484c-9ef0-4fc3100aae46")

    def test_on_message_writes_to_data(self):
        with patch.object(auth_lxdx.AccountConnection, "__init__",
                          lambda x, **params: None):
            ws = ""
            message = \
                '{"m": "total_position_snapshot", "type": "25", "payload": {"request_id": "23453452", "coin_tier": "0", "balances": {"usdt": 25000.0, "btc": 15.1, "eth": 200.0, "xrp": 50000.0, "tusd": 1230.74996}}}'
            exchange = auth_lxdx.AccountConnection()
            exchange.logger = MagicMock()
            exchange.data = {}
            exchange._on_message(ws, message)
            assert exchange.data == { "23453452" : {"request_id": "23453452", "coin_tier": "0", "balances": {"usdt": 25000.0, "btc": 15.1, "eth": 200.0, "xrp": 50000.0, "tusd": 1230.74996}}}

    def test__is_request_id_available(self):
        with patch.object(auth_lxdx.AccountConnection, "__init__",
                          lambda x, **params: None):
            exchange = auth_lxdx.AccountConnection()
            exchange.data = {}
            assert not exchange._is_request_id_available(34235)
            exchange.data = {23425: 1}
            assert exchange._is_request_id_available(23425)


    @patch('time.time', side_effect=[1, 1.1, 1.5, 2.1, 2.5, 3.5])
    def test_wait_for_response_to_request_waits(self, time_class):
        with patch.object(auth_lxdx.AccountConnection, "__init__",
                          lambda x, **params: None):
            with patch.object(auth_lxdx.AccountConnection, "_is_request_id_available") as data_check:
                #First have _wait_for_request return True
                data_check.side_effect = [False, True, True, True]
                exchange = auth_lxdx.AccountConnection()
                exchange.logger = MagicMock()
                assert exchange._wait_for_response_to_request("234435") == True
                print(data_check.call_count)
                assert data_check.call_count == 2
                # Now have _wait_for_request return False
                data_check.side_effect = [False, False, False, False, False]
                assert exchange._wait_for_response_to_request("234435") == False

    def test__post_waits_for_response_to_request(self):
        with patch.object(auth_lxdx.AccountConnection, "__init__",
                          lambda x, **params: None):
            with patch.object(auth_lxdx.AccountConnection, "_curl_exchange") as curl:
                with patch.object(auth_lxdx.AccountConnection, "_wait_for_response_to_request") as wait:
                    exchange = auth_lxdx.AccountConnection()
                    exchange.data = {}
                    self.assertRaises(Exception, exchange._post, 'snapshots/orders')
                    wait.assert_called()

    def test_get_position(self):
        with patch.object(auth_lxdx.AccountConnection, "__init__",
                          lambda x, **params: None):
            with patch.object(auth_lxdx.AccountConnection, "_post") as post:
                exchange = auth_lxdx.AccountConnection()
                post.return_value = \
                     {  "request_id": "23453452",
                        "coin_tier": "0",
                        "balances": {"usdt": 25000.0, "btc": 15.1,
                             "eth": 200.0, "xrp": 50000.0,
                             "tusd": 1230.74996}}
                response = exchange.get_position()
                assert response == post.return_value
                assert 'balances' in response
                post.assert_called_with('snapshots/positions/total')

    def test_get_assets(self):
        with patch.object(auth_lxdx.AccountConnection, "__init__",
                          lambda x, **params: None):
            with patch.object(auth_lxdx.AccountConnection, "_curl_exchange") as curl:
                exchange = auth_lxdx.AccountConnection()
                curl.return_value = \
                    {"usdt": {"security_id": "17", "wallet_min_tick_pow10": "8", "wallet_min_tick_pow10_num": "1",
                              "confirmations": "2", "balance_decimals": "8"},
                     "btc": {"security_id": "33", "wallet_min_tick_pow10": "8", "wallet_min_tick_pow10_num": "1",
                             "confirmations": "2", "balance_decimals": "8"},
                     "eth": {"security_id": "49", "wallet_min_tick_pow10": "18", "wallet_min_tick_pow10_num": "1",
                             "confirmations": "12", "balance_decimals": "18"},
                     "xrp": {"security_id": "65", "wallet_min_tick_pow10": "6", "wallet_min_tick_pow10_num": "1",
                             "confirmations": "0", "balance_decimals": "6"},
                     "tusd": {"security_id": "81", "wallet_min_tick_pow10": "18", "wallet_min_tick_pow10_num": "1",
                              "confirmations": "12", "balance_decimals": "18"}}
                result = exchange.get_assets()
                curl.assert_called_with(path='data/assets')
                assert result == curl.return_value


    def test_get_products(self):
        with patch.object(auth_lxdx.AccountConnection, "__init__",
                          lambda x, **params: None):
            with patch.object(auth_lxdx.AccountConnection, "_curl_exchange") as curl:
                exchange = auth_lxdx.AccountConnection()
                curl.return_value = \
                    {"tusd-usdt": {"symbol": "tusd-usdt", "security_id": "19", "contract_id": "4",
                                   "security_id_num": "81", "security_id_denom": "17", "num_ratio": "1",
                                   "denom_ratio": "1", "num_typeid": "1", "denom_typeid": "1", "maker_fee": "-0.0002",
                                   "taker_fee": "0.0012", "quotation_id": "81", "quotation_type_id": "1",
                                   "quotation_tick_size_decimals": "3", "price_size_mult": "1000000",
                                   "price_tick_size_decimals": "2", "price_tick_size": "0.01",
                                   "qty_size_mult": "1000000", "qty_tick_size": "0.001", "qty_tick_size_decimals": "3",
                                   "min_qty": "0.001", "max_qty": "999999", "min_price": "0.001", "max_price": "9999",
                                   "settlement_id": "17", "settlement_type_id": "1",
                                   "settlement_tick_size_decimals": "3", "value_of_point": "1"},
                     "xrp-tusd": {"symbol": "xrp-tusd", "security_id": "35", "contract_id": "3",
                                  "security_id_num": "65", "security_id_denom": "81", "num_ratio": "1",
                                  "denom_ratio": "1", "num_typeid": "1", "denom_typeid": "1", "maker_fee": "-0.0002",
                                  "taker_fee": "0.0012", "quotation_id": "65", "quotation_type_id": "1",
                                  "quotation_tick_size_decimals": "3", "price_size_mult": "1000000",
                                  "price_tick_size_decimals": "2", "price_tick_size": "0.01",
                                  "qty_size_mult": "1000000", "qty_tick_size": "0.001", "qty_tick_size_decimals": "3",
                                  "min_qty": "0.001", "max_qty": "999999", "min_price": "0.001", "max_price": "9999",
                                  "settlement_id": "81", "settlement_type_id": "1",
                                  "settlement_tick_size_decimals": "3", "value_of_point": "1"},
                     "eth-tusd": {"symbol": "eth-tusd", "security_id": "51", "contract_id": "2",
                                  "security_id_num": "49", "security_id_denom": "81", "num_ratio": "1",
                                  "denom_ratio": "1", "num_typeid": "1", "denom_typeid": "1", "maker_fee": "-0.0002",
                                  "taker_fee": "0.0012", "quotation_id": "49", "quotation_type_id": "1",
                                  "quotation_tick_size_decimals": "3", "price_size_mult": "1000000",
                                  "price_tick_size_decimals": "1", "price_tick_size": "0.1", "qty_size_mult": "1000000",
                                  "qty_tick_size": "0.001", "qty_tick_size_decimals": "3", "min_qty": "0.001",
                                  "max_qty": "99999", "min_price": "0.001", "max_price": "99999", "settlement_id": "81",
                                  "settlement_type_id": "1", "settlement_tick_size_decimals": "3",
                                  "value_of_point": "1"},
                     "btc-tusd": {"symbol": "btc-tusd", "security_id": "67", "contract_id": "1",
                                  "security_id_num": "33", "security_id_denom": "81", "num_ratio": "1",
                                  "denom_ratio": "1", "num_typeid": "1", "denom_typeid": "1", "maker_fee": "-0.0002",
                                  "taker_fee": "0.0012", "quotation_id": "33", "quotation_type_id": "1",
                                  "quotation_tick_size_decimals": "3", "price_size_mult": "1000000",
                                  "price_tick_size_decimals": "0", "price_tick_size": "1", "qty_size_mult": "1000000",
                                  "qty_tick_size": "0.001", "qty_tick_size_decimals": "3", "min_qty": "0.001",
                                  "max_qty": "9999", "min_price": "0.001", "max_price": "999999", "settlement_id": "81",
                                  "settlement_type_id": "1", "settlement_tick_size_decimals": "3",
                                  "value_of_point": "1"}}
                result = exchange.get_products()
                curl.assert_called_with(path='data/products')
                assert result == curl.return_value


    def test_get_orders(self):
        with patch.object(auth_lxdx.AccountConnection, "__init__",
                          lambda x, **params: None):
            with patch.object(auth_lxdx.AccountConnection, "_post") as post:
                exchange = auth_lxdx.AccountConnection()
                post.return_value = \
                    {'request_id': '392368834', 'order_start_index': '0', 'total_orders': '2', 'num_orders': '2',
                     'orders': [{'price': 4500.0, 'qty': 0.1, 'remaining_qty': 0.1, 'order_id': '9386821750097823867',
                                 'customer_order_ref': '274926922', 'symbol': 'btc-tusd', 'side': 'buy',
                                 'post_only': '0', 'time_in_force': 'DAY', 'state': '1', 'request_id': '748504350',
                                 'original_qty': 0.1, 'timestamp': '1544481038176407095'},
                                {'price': 5000.1, 'qty': 0.2, 'remaining_qty': 0.2, 'order_id': '9386821750097479803',
                                 'customer_order_ref': '4456549', 'symbol': 'btc-tusd', 'side': 'sell',
                                 'post_only': '1', 'time_in_force': 'GTC', 'state': '1', 'request_id': '12234345',
                                 'original_qty': 0.2, 'timestamp': '1544222257062996209'}]}
                result = exchange.get_orders()
                post.assert_called_with('snapshots/orders')
                assert result == post.return_value


    def test_place_orders(self):
        with patch.object(auth_lxdx.AccountConnection, "__init__",
                          lambda x, **params: None):
            with patch.object(auth_lxdx.AccountConnection, "_post") as post:
                exchange = auth_lxdx.AccountConnection()
                post.return_value = \
                    {'m': 'order_submitted', 'type': '2',
                     'payload': {'response': '0', 'order_id': '9386821750097856635', 'orderId': '9386821750097856635',
                                 'customer_order_ref': '21452345234', 'request_id': '228919273',
                                 'remaining_quantity': 0.1, 'timestamp': '1544730929631357557', 'price': 4400.0,
                                 'qty': 0.1, 'symbol': 'btc-tusd', 'side': 'buy'}}

                result = exchange.place(4400, 0.1, 'btc-tusd', 'buy', time_in_force='DAY', customer_order_ref='21452345234',
                               type='limit', post_only=True)
                assert result == post.return_value
                postdict = \
                {"price": "4400", "qty": "0.1", "symbol": "btc-tusd", "side": "buy", "time_in_force": "DAY",
                 "type": "limit", "post_only": True, "customer_order_ref": "21452345234"}
                post.assert_called_with('orders', postdict=postdict)


    def test_cancel_order(self):
        with patch.object(auth_lxdx.AccountConnection, "__init__",
                          lambda x, **params: None):
            with patch.object(auth_lxdx.AccountConnection, "_post") as post:
                exchange = auth_lxdx.AccountConnection()
                post.return_value = \
                    {'m': 'order_canceled', 'type': '3',
                     'payload': {'order_id': '9386821750097856635', 'unfilledQty': '0.1', 'unfilled_qty': '0.1',
                                 'response': '0', 'request_id': '866598873'}}

                response = exchange.cancel('9386821750097856635', 'btc-tusd')
                assert response == post.return_value
                postdict = {"order_id": "9386821750097856635", "symbol": "btc-tusd"}
                post.assert_called_with('orders/cancel', postdict=postdict)



