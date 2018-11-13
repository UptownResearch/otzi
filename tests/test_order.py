from unittest.mock import MagicMock, patch
from unittest import TestCase
from market_maker.order import Order


class Test_Market_Maker_Module(TestCase):

    def setUp(self):
        pass

    def tearDown(self):	
        pass

    def test_basics(self):
        a = Order()
        price = 100
        a['price'] = price
        assert a['price'] == price

    def test_del(self):
        a = Order()
        price = 100
        a['price'] = price
        del a['price']
        with self.assertRaises(KeyError):
            a['price'] + 1

    def test_get(self):
        a = Order()
        price = 100
        a['price'] = price
        del a['price']
        with self.assertRaises(KeyError):
            a['price'] + 1

    def test_get_function(self):
        a = Order()
        price = 100
        a['price'] = price
        assert a.get('price') == price
