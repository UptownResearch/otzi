
import datetime
import iso8601
from unittest.mock import MagicMock, patch
from unittest import TestCase
#from market_maker.settings import settings

class ExchangeInterface:
    def current_timestamp(self):
        pass
    def market_depth(self, symbol):
        pass
    def recent_trades(self):
        pass


orderbook = \
[{'symbol': 'XBTUSD',
  'id': 15599351300,
  'side': 'Sell',
  'size': 1000,
  'price': 5001.5},
 {'symbol': 'XBTUSD',
  'id': 15599351350,
  'side': 'Sell',
  'size': 1000,
  'price': 5001},
 {'symbol': 'XBTUSD',
  'id': 15599351400,
  'side': 'Buy',
  'size': 1000,
  'price': 5000.5},
 {'symbol': 'XBTUSD',
  'id': 15599351450,
  'side': 'Buy',
  'size': 1000,
  'price': 5000}]

trades = [{'timestamp': '2018-08-09T20:11:56.000Z',
  'symbol': 'XBTUSD',
  'side': 'Sell',
  'size': 100,
  'price': 5000.5,
  'tickDirection': 'MinusTick',
  'trdMatchID': '5ff50e87-17e9-f86c-9464-e77d452637d1',
  'grossValue': 1999800,
  'homeNotional': 0.019998,
  'foreignNotional': 100},
 {'timestamp': '2018-08-09T20:11:57.000Z',
  'symbol': 'XBTUSD',
  'side': 'Buy',
  'size': 100,
  'price': 5001,
  'tickDirection': 'PlusTick',
  'trdMatchID': 'df7f3037-b303-08ea-0f3d-699cb42f15bb',
  'grossValue': 1999600,
  'homeNotional': 0.01999600,
  'foreignNotional': 100}]


class Test1(ExchangeInterface):
    
    def __init__(self):
        self.timestamp = iso8601.parse_date('2018-08-09T20:11:55.000Z')
        self.trades_calls = [[], *[trades]*12]
    def current_timestamp(self):
        return self.timestamp
    def market_depth(self, symbol):
        return orderbook
    def recent_trades(self):
        print("Recent Trades Called!")
        return self.trades_calls.pop(0)
    def get_orderbook_time(self):
        return self.timestamp
    def get_instrument(self, symbol=None):
        return {'tickSize': 0.5}





class Test_Paper_Trading(TestCase):

    def setUp(self):
        """
        It's patching time
        """

        #http://www.voidspace.org.uk/python/mock/examples.html#mocking-imports-with-patch-dict
        self.settings_mock = MagicMock()
        self.settings_mock.settings.BACKTEST.return_value = True
        self.settings_mock.settings.paperless = True
        self.settings_mock.settings.SYMBOL = "XBTUSD"
        self.exchange_mock = MagicMock()
        modules = {
            'market_maker.settings': self.settings_mock
        }

        self.module_patcher = patch.dict('sys.modules', modules)
        self.module_patcher.start()
        #from my_module import MyModule
        #from market_maker.paper_trading import paper_trading
        #self.paper_trading = paper_trading
        from market_maker.paper_trading import PaperTrading
        self.paper_trading = PaperTrading


    def tearDown(self):
        """
        Let's clean up
        """

        self.module_patcher.stop()

    def test_get_paper_trading(self):
        ptrading = self.paper_trading(settings=self.settings_mock)
        assert ptrading is not None

    def test_rest_order_in_book(self):
        order_rest_in_book = [{'price': 5000.5, 'orderQty': 100, 'side': "Buy"}]
        ptrading = self.paper_trading(settings=self.settings_mock)
        ptrading.reset()
        Test1Ei = Test1()
        ptrading.provide_exchange(Test1Ei)
        ptrading.track_orders_created(order_rest_in_book)
        print(ptrading.buy_orders_created)
        assert len(ptrading.buy_partially_filled)  == 1
        assert ptrading.buy_partially_filled[0]['price'] == 5000.5
        assert ptrading.buy_partially_filled[0]['orderQty'] == 100

    def test_crossing_non_agress_orders_should_be_cancelled(self):
        order_rest_in_book = [{'price': 5001, 'orderQty': 100, 'side': "Buy"}]
        ptrading = self.paper_trading(settings=self.settings_mock)
        ptrading.reset()
        Test1Ei = Test1()
        ptrading.provide_exchange(Test1Ei)
        ptrading.track_orders_created(order_rest_in_book)
        print(ptrading.buy_orders_created)
        assert len(ptrading.buy_partially_filled)  == 0

    def test_crossing_non_agress_orders_should_be_cancelled_sell(self):
        order_rest_in_book = [{'price': 5000.5, 'orderQty': 100, 'side': "Sell"}]
        ptrading = self.paper_trading(settings=self.settings_mock)
        ptrading.reset()
        Test1Ei = Test1()
        ptrading.provide_exchange(Test1Ei)
        ptrading.track_orders_created(order_rest_in_book)
        print(ptrading.sell_orders_created)
        assert len(ptrading.sell_partially_filled)  == 0


    def test_crossing_non_agress_orders_outside_of_book_should_be_cancelled(self):
        order_rest_in_book = [{'price': 5100, 'orderQty': 100, 'side': "Buy"}]
        ptrading = self.paper_trading(settings=self.settings_mock)
        ptrading.reset()
        Test1Ei = Test1()
        ptrading.provide_exchange(Test1Ei)
        ptrading.track_orders_created(order_rest_in_book)
        print(ptrading.buy_orders_created)
        assert len(ptrading.buy_partially_filled)  == 0

    def test_crossing_non_agress_orders_outside_of_book_should_be_cancelled_sell(self):
        order_rest_in_book = [{'price': 4900, 'orderQty': 100, 'side': "Sell"}]
        ptrading = self.paper_trading(settings=self.settings_mock)
        ptrading.reset()
        Test1Ei = Test1()
        ptrading.provide_exchange(Test1Ei)
        ptrading.track_orders_created(order_rest_in_book)
        print(ptrading.sell_orders_created)
        assert len(ptrading.sell_partially_filled)  == 0








    def test_stale_orderbook_cancel_orders_inside_last_orders_buy(self):
        ''' test_stale_orderbook_cancel_orders_inside_last_orders_buy
        In fast markets, the orderbook can be stale. The paper trading
        simulator should cancel orders that fall between the best orderbook
        order and the last trade. 
        '''
        trades = [{'timestamp': '2018-08-09T20:11:56.000Z',
                  'symbol': 'XBTUSD',
                  'side': 'Sell',
                  'size': 100,
                  'price': 5000.5,
                  'trdMatchID': '5ff50e87-17e9-f86c-9464-e77d452637d1'},
                 {'timestamp': '2018-08-09T20:11:56.000Z',
                  'symbol': 'XBTUSD',
                  'side': 'Buy',
                  'size': 1000,
                  'price': 5001,
                  'trdMatchID': 'df7f3037-b303-08ea-0f3d-699cb42f15bb',
                    }, 
                {'timestamp': '2018-08-09T20:11:56.000Z',
                  'symbol': 'XBTUSD',
                  'side': 'Buy',
                  'size': 500,
                  'price': 5001.5,
                  'trdMatchID': 'dfisinurfdfs42f15bb',
                    },
               {'timestamp': '2018-08-09T20:11:57.000Z',
                  'symbol': 'XBTUSD',
                  'side': 'Buy',
                  'size': 100,
                  'price': 5001.5,
                  'trdMatchID': 'dfisinurfdfs42f15bb',
                    }, 
                {'timestamp': '2018-08-09T20:11:58.000Z',
                  'symbol': 'XBTUSD',
                  'side': 'Buy',
                  'size': 100,
                  'price': 5001.5,
                  'trdMatchID': 'dfisinurfdfs42f15bb',
                    }]
        class Test_Stale(Test1):   
            def __init__(self):
                super().__init__() 
                self.timestamps = [iso8601.parse_date('2018-08-09T20:11:59.000Z')]     
                self.trades_calls = [trades,[]]
            def current_timestamp(self):
                return self.timestamps.pop(0)
            def market_depth(self, symbol):
                return orderbook
            def get_orderbook_time(self):
                return iso8601.parse_date('2018-08-09T20:11:55.000Z')

        order_rest_in_book = [{'price': 5001, 'orderQty': 100, 'side': "Sell"}]
        ptrading = self.paper_trading(settings=self.settings_mock)
        ptrading.reset()
        Test1Ei = Test_Stale()
        ptrading.provide_exchange(Test1Ei)
        ptrading.track_orders_created(order_rest_in_book)
        ptrading.simulate_fills_from_trades()
        assert len(ptrading.get_orders())  == 0

    def test_add_and_remove_order(self):
        order_rest_in_book = [{'price': 5000.5, 'orderQty': 100, 'side': "Buy", "orderID":2}]
        ptrading = self.paper_trading(settings=self.settings_mock)
        ptrading.reset()
        Test1Ei = Test1()
        ptrading.provide_exchange(Test1Ei)
        ptrading.track_orders_created(order_rest_in_book)
        assert len(ptrading.buy_orders_created)  == 1
        orders = ptrading.get_orders()
        for order in orders:
        	ptrading.cancel_order(order["orderID"])
        assert len(ptrading.get_orders())  == 0

    def test_add_resting_but_not_filling(self):
        order_rest_in_book = [{'price': 5000.5, 'orderQty': 100, 'side': "Buy"}]
        ptrading = self.paper_trading(settings=self.settings_mock)
        ptrading.reset()
        Test1Ei = Test1()
        ptrading.provide_exchange(Test1Ei)
        ptrading.track_orders_created(order_rest_in_book)
        #ptrading.loop_functions()
        ptrading.simulate_fills_from_trades()
        ptrading.close_positions()
        assert ptrading.filled == []

    def test_getting_filled_after_several_loops(self):
        class Test2(Test1):   
            def __init__(self):
                super().__init__() 
                self.timestamp = iso8601.parse_date('2018-08-09T20:11:55.000Z')
                self.counter = 0
            def current_timestamp(self):
                return self.timestamp
            def market_depth(self, symbol):
                return orderbook
            def updated_timestamp(self, timestamp):
                self.timestamp = timestamp
            def get_orderbook_time(self):
                return self.timestamp
        order_rest_in_book = [{'price': 5000.5, 'orderQty': 100, 'side': "Buy"}]
        ptrading = self.paper_trading(settings=self.settings_mock)
        ptrading.reset()
        Test2Ei = Test2()
        ptrading.provide_exchange(Test2Ei)
        ptrading.track_orders_created(order_rest_in_book)
        counter = 0
        while counter < 12:
            counter += 1
            for trade in trades:
                trade["trdMatchID"] = str(counter)
            ptrading.simulate_fills_from_trades()
            ptrading.close_positions()
        assert ptrading.buy_partially_filled == []
        assert len(ptrading.filled) == 1

    def test_buy_fills_with_multiple_orders(self):
        orders = [{'price': 5000.5, 'orderQty': 100, 'side': "Buy"},
                        {'price': 5000, 'orderQty': 100, 'side': "Buy"},
                       {'price': 4999.5, 'orderQty': 100, 'side': "Buy"}]
        btrades = [{'timestamp': '2018-08-09T20:11:57.000Z',
            'symbol': 'XBTUSD',
            'side': 'Sell',
            'size': 1100,
            'price': 5000.5,
            'trdMatchID': "qxinnierwinal"},
            {'timestamp': '2018-08-09T20:11:56.000Z',
            'symbol': 'XBTUSD',
            'side': 'Sell',
            'size': 1050,
            'price': 5000,
            'trdMatchID': "cwniniewal"}]
        class Test3(Test1):   
            def __init__(self):
                super().__init__() 
                self.timestamp = iso8601.parse_date('2018-08-09T20:11:55.000Z')
                self.trades_calls = [[], btrades, btrades]
            def current_timestamp(self):
                return self.timestamp
            def market_depth(self, symbol):
                return orderbook
            def updated_timestamp(self, timestamp):
                self.timestamp = timestamp
            def get_orderbook_time(self):
                return self.timestamp
        ptrading = self.paper_trading(settings=self.settings_mock)
        ptrading.reset()
        TestC = Test3()
        ptrading.provide_exchange(TestC)
        ptrading.track_orders_created(orders)
        ptrading.simulate_fills_from_trades()
        ptrading.close_positions()
        assert ptrading.position["currentQty"] == 150
        assert len(ptrading.get_orders()) == 2

    def test_sell_fills_with_multiple_orders(self):
        orders = [{'price': 5001, 'orderQty': 100, 'side': "Sell"},
                        {'price': 5001.5, 'orderQty': 100, 'side': "Sell"},
                       {'price': 5002, 'orderQty': 100, 'side': "Sell"}]
        ltrades = [{'timestamp': '2018-08-09T20:11:57.000Z',
            'symbol': 'XBTUSD',
            'side': 'Buy',
            'size': 1100,
            'price': 5001,
            'trdMatchID': "aevninaeirinrv"},
            {'timestamp': '2018-08-09T20:11:56.000Z',
            'symbol': 'XBTUSD',
            'side': 'Buy',
            'size': 1050,
            'price': 5001.5,
            'trdMatchID': "asdfasdfnneef"}]
        class Test3(Test1):   
            def __init__(self):
                super().__init__() 
                self.timestamp = iso8601.parse_date('2018-08-09T20:11:55.000Z')
                self.trades_calls = [[], ltrades, ltrades]
            def current_timestamp(self):
                return self.timestamp
            def market_depth(self, symbol):
                return orderbook
            def updated_timestamp(self, timestamp):
                self.timestamp = timestamp
            def get_orderbook_time(self):
                return self.timestamp
        ptrading = self.paper_trading(settings=self.settings_mock)
        ptrading.reset()
        TestC = Test3()
        ptrading.provide_exchange(TestC)
        ptrading.track_orders_created(orders)
        ptrading.simulate_fills_from_trades()
        ptrading.close_positions()
        print(ptrading.position["currentQty"])
        assert ptrading.position["currentQty"] == -150
        assert len(ptrading.get_orders()) == 2


    def test_no_fills_from_the_past(self):
        orders = [{'price': 5001, 'orderQty': 100, 'side': "Sell"},
                        {'price': 5001.5, 'orderQty': 100, 'side': "Sell"},
                       {'price': 5002, 'orderQty': 100, 'side': "Sell"}]
        ltrades = [ {'timestamp': '2018-08-09T20:11:54.000Z',
            'symbol': 'XBTUSD',
            'side': 'Buy',
            'size': 1100,
            'price': 5001.5,
            'trdMatchID': "asasffdvvvrhrgdinrv"},
        {'timestamp': '2018-08-09T20:11:57.000Z',
            'symbol': 'XBTUSD',
            'side': 'Buy',
            'size': 1100,
            'price': 5001,
            'trdMatchID': "aevninaeirinrv"},
            {'timestamp': '2018-08-09T20:11:56.000Z',
            'symbol': 'XBTUSD',
            'side': 'Buy',
            'size': 1050,
            'price': 5001.5,
            'trdMatchID': "asdfasdfnneef"}]
        class Test3(Test1):   
            def __init__(self):
                self.timestamp = iso8601.parse_date('2018-08-09T20:11:55.000Z')
                self.trades_calls = [[], ltrades]
            def current_timestamp(self):
                return self.timestamp
            def market_depth(self, symbol):
                return orderbook
            def updated_timestamp(self, timestamp):
                self.timestamp = timestamp
            def get_orderbook_time(self):
                return self.timestamp

        ptrading = self.paper_trading(settings=self.settings_mock)
        ptrading.reset()
        TestC = Test3()
        ptrading.provide_exchange(TestC)
        ptrading.track_orders_created(orders)
        ptrading.simulate_fills_from_trades()
        ptrading.close_positions()
        assert ptrading.position["currentQty"] == -150
        assert len(ptrading.get_orders()) == 2


    def test_no_fills_from_the_past_sells(self):
        orders = [{'price': 5000.5, 'orderQty': 100, 'side': "Buy"},
                        {'price': 5000.0, 'orderQty': 100, 'side': "Buy"},
                       {'price': 4999.5, 'orderQty': 100, 'side': "Buy"}]
        # Trades First trades should not result in any fills (its in the past)
        ltrades = [ {'timestamp': '2018-08-09T20:11:54.000Z',
            'symbol': 'XBTUSD',
            'side': 'Sell',
            'size': 1100,
            'price': 5000.5,
            'trdMatchID': "asasffdvvvrhrgdinrv"},
        {'timestamp': '2018-08-09T20:11:57.000Z',
            'symbol': 'XBTUSD',
            'side': 'Sell',
            'size': 1100,
            'price': 5000.5,
            'trdMatchID': "aevninaeirinrv"},
            {'timestamp': '2018-08-09T20:11:56.000Z',
            'symbol': 'XBTUSD',
            'side': 'Buy',
            'size': 1050,
            'price': 5000.0,
            'trdMatchID': "asdfasdfnneef"}]
        class Test3(Test1):   
            def __init__(self):
                self.timestamp = iso8601.parse_date('2018-08-09T20:11:55.000Z')
                self.trades_calls = [[], ltrades]
            def current_timestamp(self):
                return self.timestamp
            def market_depth(self, symbol):
                return orderbook
            def updated_timestamp(self, timestamp):
                self.timestamp = timestamp
            def get_orderbook_time(self):
                return self.timestamp
        ptrading = self.paper_trading(settings=self.settings_mock)
        ptrading.reset()
        TestC = Test3()
        ptrading.provide_exchange(TestC)
        ptrading.track_orders_created(orders)
        ptrading.simulate_fills_from_trades()
        ptrading.close_positions()
        assert ptrading.position["currentQty"] == 150
        assert len(ptrading.get_orders()) == 2


    def test_fill_deeper_in_book(self):
        orders = [{'price': 5000, 'orderQty': 100, 'side': "Buy"},
                        {'price': 5001.5, 'orderQty': 100, 'side': "Sell"}]
        
        ltrades = [ {'timestamp': '2018-08-09T20:11:52.000Z',
            'symbol': 'XBTUSD',
            'side': 'Sell',
            'size': 1100,
            'price': 5000.5,
            'trdMatchID': "arbrtbrthdhdinrv"},
        {'timestamp': '2018-08-09T20:11:54.000Z',
            'symbol': 'XBTUSD',
            'side': 'Buy',
            'size': 1100,
            'price': 5001.5,
            'trdMatchID': "asasffdvvvrhrgdinrv"},
        {'timestamp': '2018-08-09T20:11:57.000Z',
            'symbol': 'XBTUSD',
            'side': 'Buy',
            'size': 1000,
            'price': 5001,
            'trdMatchID': "aevninaeirinrv"},
            {'timestamp': '2018-08-09T20:11:57.000Z',
            'symbol': 'XBTUSD',
            'side': 'Buy',
            'size': 500,
            'price': 5001.5,
            'trdMatchID': "gmhmhjrrgef"},
            {'timestamp': '2018-08-09T20:11:57.000Z',
            'symbol': 'XBTUSD',
            'side': 'Buy',
            'size': 550,
            'price': 5001.5,
            'trdMatchID': "wetrwtasccscsnneef"},
            {'timestamp': '2018-08-09T20:11:57.000Z',
            'symbol': 'XBTUSD',
            'side': 'Buy',
            'size': 25,
            'price': 5001.5,
            'trdMatchID': "xvbcbbmoinjnneef"}, 
            {'timestamp': '2018-08-09T20:11:58.000Z',
            'symbol': 'XBTUSD',
            'side': 'Sell',
            'size': 1000,
            'price': 5000.5,
            'trdMatchID': "rtyytjmoinjnneef"}, 
            {'timestamp': '2018-08-09T20:11:58.000Z',
            'symbol': 'XBTUSD',
            'side': 'Sell',
            'size': 500,
            'price': 5000.0,
            'trdMatchID': "uliomoinjnneef"},
            {'timestamp': '2018-08-09T20:11:58.000Z',
            'symbol': 'XBTUSD',
            'side': 'Sell',
            'size': 550,
            'price': 5000.0,
            'trdMatchID': "zsfdzfmoinjnneef"},
            {'timestamp': '2018-08-09T20:11:58.000Z',
            'symbol': 'XBTUSD',
            'side': 'Sell',
            'size': 24,
            'price': 5000.0,
            'trdMatchID': "qevrkmoinjnneef"},]
        class Test3(Test1):   
            def __init__(self):
                self.timestamp = iso8601.parse_date('2018-08-09T20:11:55.000Z')
                self.trades_calls = [[], ltrades]
            def current_timestamp(self):
                return self.timestamp
            def market_depth(self, symbol):
                return orderbook
            def updated_timestamp(self, timestamp):
                self.timestamp = timestamp
            def get_orderbook_time(self):
                return self.timestamp
        ptrading = self.paper_trading(settings=self.settings_mock)
        ptrading.reset()
        TestC = Test3()
        ptrading.provide_exchange(TestC)
        ptrading.track_orders_created(orders)
        ptrading.simulate_fills_from_trades()
        ptrading.close_positions()
        print(ptrading.position["currentQty"])
        print(ptrading.get_orders())
        assert ptrading.position["currentQty"] == -1
        assert len(ptrading.get_orders()) == 2

        # Need a test of orders entered crossing the market!

