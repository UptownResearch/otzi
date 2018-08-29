from market_maker.paperless_tracker import paperless_tracker
import datetime
import iso8601
from unittest.mock import MagicMock
from market_maker.settings import settings

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
  'size': 132736,
  'price': 5001.5},
 {'symbol': 'XBTUSD',
  'id': 15599351350,
  'side': 'Sell',
  'size': 134939,
  'price': 5001},
 {'symbol': 'XBTUSD',
  'id': 15599351400,
  'side': 'Buy',
  'size': 1000,
  'price': 5000.5},
 {'symbol': 'XBTUSD',
  'id': 15599351450,
  'side': 'Buy',
  'size': 32728,
  'price': 5000}]

trades = [{'timestamp': '2018-08-09T20:11:57.000Z',
  'symbol': 'XBTUSD',
  'side': 'Sell',
  'size': 100,
  'price': 5000.5,
  'tickDirection': 'MinusTick',
  'trdMatchID': '5ff50e87-17e9-f86c-9464-e77d452637d1',
  'grossValue': 1999800,
  'homeNotional': 0.019998,
  'foreignNotional': 100},
 {'timestamp': '2018-08-09T20:11:56.000Z',
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
        
    def current_timestamp(self):
        return self.timestamp
    def market_depth(self, symbol):
        return orderbook
    def recent_trades(self):
        return trades 

def test_get_paperless_tracker():
	pp_tracker = paperless_tracker.getInstance()
	assert pp_tracker is not None

def test_rest_order_in_book():
	settings = MagicMock()
	settings.BACKTEST = True
	order_rest_in_book = [{'price': 5000.5, 'orderQty': 100, 'side': "Buy"}]
	pp_tracker = paperless_tracker.getInstance()
	pp_tracker.reset()
	Test1Ei = Test1()
	pp_tracker.provide_exchange(Test1Ei)
	pp_tracker.track_orders_created(order_rest_in_book)
	assert len(pp_tracker.buy_orders_created)  == 1
	assert pp_tracker.buy_orders_created[0]['price'] == 5000.5
	assert pp_tracker.buy_orders_created[0]['orderQty'] == 100

def test_add_and_remove_order():
	order_rest_in_book = [{'price': 5000.5, 'orderQty': 100, 'side': "Buy"}]
	pp_tracker = paperless_tracker.getInstance()
	pp_tracker.reset()
	Test1Ei = Test1()
	pp_tracker.provide_exchange(Test1Ei)
	pp_tracker.track_orders_created(order_rest_in_book)
	assert len(pp_tracker.buy_orders_created)  == 1
	orders = pp_tracker.get_orders()
	for order in orders:
		pp_tracker.cancel_order(order["orderID"])
	assert len(pp_tracker.get_orders())  == 0
