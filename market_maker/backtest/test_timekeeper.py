from unittest.mock import MagicMock, patch
from unittest import TestCase
from market_maker.backtest.timekeeper import Timekeeper


timestamps_a = ['2018-09-01T00:00:05.1000000',
 '2018-09-01T00:01:05.3000000']
timestamps_b = ['2018-09-01T00:00:06.2000000',
 '2018-09-01T00:02:05.4000000']
timestamps_c = ['2018-09-01T00:01:05.3000000',
 '2018-09-01T00:02:05.4000000',
 '2018-09-01T00:05:05.5000000']

timestamps_a_b_in_order = [
'2018-09-01T00:00:05.1000000',
'2018-09-01T00:00:06.2000000',
'2018-09-01T00:01:05.3000000',
'2018-09-01T00:02:05.4000000'
]

timestamps_a_b_c_in_order = [
'2018-09-01T00:00:05.1000000',
'2018-09-01T00:00:06.2000000',
'2018-09-01T00:01:05.3000000',
'2018-09-01T00:05:05.5000000'
]

class Test_Timekeeper(TestCase):

    def test_contribute_times_must_be_called_first(self):
        tk = Timekeeper()
        self.assertRaises(Exception, tk.initialize)

    def test_initialize_must_be_called_before_get_time(self):
        tk = Timekeeper()
        tk.contribute_times(timestamps_a)
        self.assertRaises(Exception, tk.get_time)

    def test_initialize_must_be_called_before_increment_time(self):
        ''' initialize calls increment time first to avoid  starting later than
            expected. 
        '''
        tk = Timekeeper()
        tk.contribute_times(timestamps_a)
        self.assertRaises(Exception, tk.increment_time)

    def test_raise_EOFError_if_all_timestamps_consumed(self):
        tk = Timekeeper()
        tk.contribute_times(timestamps_a)
        tk.initialize()
        tk.increment_time()
        self.assertRaises(EOFError, tk.increment_time)

    def test_returns_timestamps_in_order(self):
        tk = Timekeeper()
        tk.contribute_times(timestamps_a)
        tk.contribute_times(timestamps_b)
        tk.initialize()
        for x in timestamps_a_b_in_order:
            assert tk.get_time() == x
            print("%s - %s" % (tk.get_time(), x))
            try:
                tk.increment_time()
            except EOFError:
                '''Attempting to increment_time after all times consumed raises Error '''
                pass

    def increment_time_ignores_duplicate_times(self):
        tk = Timekeeper()
        tk.contribute_times(timestamps_a)
        tk.contribute_times(timestamps_b)
        tk.initialize()
        for x in timestamps_a_b_c_in_order:
            assert tk.get_time() == x
            print("%s - %s" % (tk.get_time(), x))
            try:
                tk.increment_time()
            except EOFError:
                '''Attempting to increment_time after all times consumed raises Error '''
                pass
        

