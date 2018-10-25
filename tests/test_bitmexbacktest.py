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

    def tearDown(self):
        """
        Let's clean up
        """

        #self.module_patcher.stop()

    @patch('market_maker.backtest.bitmexwsfromfile.BitMEXwsFromFile')
    def test_module_loads(self, bmexws):
        bmexws = MagicMock()
        from market_maker.backtest.bitmexbacktest import BitMEXbacktest
        backtest_interface = BitMEXbacktest(settings=self.settings_mock)
        print("Also seen")
        assert BitMEXbacktest is not None

