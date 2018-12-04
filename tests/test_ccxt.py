from unittest.mock import MagicMock, patch, Mock
from unittest import TestCase
from market_maker.ccxt import ccxtInterface


class Test_Exchange_Interface(TestCase):

    def setUp(self):
        #self.auth_patch = patch.object(exchange_interface, 'AWS4Auth')
        #self.requests_patch = patch.object(exchange_interface, 'requests')
        #self.auth = self.auth_patch.start()
        #self.requests = self.requests_patch.start()
        pass

    def tearDown(self):
        #self.auth_patch.stop()
        #self.requests_patch.stop()
        pass

    def test_create_class(self):
        try:
            exchange = ccxtInterface()
        except Exception as e:
            print(e)
            assert False
        assert True

