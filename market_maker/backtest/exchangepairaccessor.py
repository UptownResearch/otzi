import csv
import iso8601
import os
#from market_maker.backtest.timekeeper import Timekeeper
from decimal import Decimal
import datetime
import time

default_instrument =   {
    "symbol": "XBTUSD",    "rootSymbol": "XBT",    "state": "Open",    "typ": "FFWCSX",    "listing": "2016-05-13T12:00:00.000Z",    "front": "2016-05-13T12:00:00.000Z",    "expiry": "",    "settle": "",    "relistInterval": "",    "inverseLeg": "",    "sellLeg": "",    "buyLeg": "",    "optionStrikePcnt": "",    "optionStrikeRound": "",    "optionStrikePrice": "",    "optionMultiplier": "",    "positionCurrency": "USD",    "underlying": "XBT",    "quoteCurrency": "USD",    "underlyingSymbol": "XBT=",    "reference": "BMEX",    "referenceSymbol": ".BXBT",    "calcInterval": "",    "publishInterval": "",    "publishTime": "",    "maxOrderQty": 10000000,    "maxPrice": 1000000,    "lotSize": 1,    "tickSize": 0.5,    "multiplier": -100000000,    "settlCurrency": "XBt",    "underlyingToPositionMultiplier": "",    "underlyingToSettleMultiplier": -100000000,    "quoteToSettleMultiplier": "",    "isQuanto": False,    "isInverse": True,    "initMargin": 0.01,    "maintMargin": 0.005,    "riskLimit": 20000000000,    "riskStep": 10000000000,    "limit": "",    "capped": False,    "taxed": True,    "deleverage": True,    "makerFee": -0.00025,    "takerFee": 0.00075,    "settlementFee": 0,    "insuranceFee": 0,    "fundingBaseSymbol": ".XBTBON8H",    "fundingQuoteSymbol": ".USDBON8H",    "fundingPremiumSymbol": ".XBTUSDPI8H",    "fundingTimestamp": "2018-10-03T20:00:00.000Z",    "fundingInterval": "2000-01-01T08:00:00.000Z",    "fundingRate": 0.0001,    "indicativeFundingRate": 0.0001,    "rebalanceTimestamp": "",    "rebalanceInterval": "",    "openingTimestamp": "2018-10-03T18:00:00.000Z",    "closingTimestamp": "2018-10-03T19:00:00.000Z",    "sessionInterval": "2000-01-01T01:00:00.000Z",    "prevClosePrice": 6451.54,    "limitDownPrice": "",    "limitUpPrice": "",    "bankruptLimitDownPrice": "",    "bankruptLimitUpPrice": "",    "prevTotalVolume": 843248673960,    "totalVolume": 843321480688,    "volume": 72806728,    "volume24h": 1484161853,    "prevTotalTurnover": 11494286280786176,    "totalTurnover": 11495415121904324,    "turnover": 1128841118149,    "turnover24h": 22951738503074,    "homeNotional24h": 229517.38503074567,    "foreignNotional24h": 1484161853,    "prevPrice24h": 6521.5,    "vwap": 6466.6322,    "highPrice": 6549.5,    "lowPrice": 6394,    "lastPrice": 6446.5,    "lastPriceProtected": 6446.5,    "lastTickDirection": "ZeroPlusTick",    "lastChangePcnt": -0.0115,    "bidPrice": 6446,    "midPrice": 6446.25,    "askPrice": 6446.5,    "impactBidPrice": 6446.2064,    "impactMidPrice": 6446.5,    "impactAskPrice": 6446.622,    "hasLiquidity": True,    "openInterest": 735085826,    "openValue": 11404121504564,    "fairMethod": "FundingRate",    "fairBasisRate": 0.1095,    "fairBasis": 0.11,    "fairPrice": 6445.68,    "markMethod": "FairPrice",    "markPrice": 6445.68,    "indicativeTaxRate": 0,    "indicativeSettlePrice": 6445.57,    "optionUnderlyingPrice": "",    "settledPrice": "",    "timestamp": "2018-10-03T18:38:00.759Z"
  }

class ExchangePairAccessor(object):

    """ExchangePairAccessor. Use to access data for a single pair at a single exchange."""

    def __init__(self, timekeeper = None, trades_filename = "", L2orderbook_filename = "",
                name = "", settings = None):
        """Init BacktestExchangePair."""
        self.settings = settings
        self.symbol = self.settings.SYMBOL
        # variables holding data dependent on current timestamp
        # timestamp tracking location of last read data line
        self.present_timestamp = None
        self.trades = []
        # timestamp tracking most recent timestamp that was requested to update up to
        self.external_timestamp = None
        # Using the '_' prefix to indicate persistent variables that have data  
        # that should not be directly shared outside of the class
        trade_data = []
        trades_csvfile = open(trades_filename)            
        tradereader = csv.reader(trades_csvfile, delimiter=';')
        self._timestamps = []
        unprocessed_trade_data = []
        for row in tradereader:
            unprocessed_trade_data.append(row)
        self._headers = unprocessed_trade_data.pop(0)
        self._trade_data = []
        #store the date prefix for the orderbook data
        self._date_prefix = unprocessed_trade_data[0][1][0:11]
        previous_timestamp = None
        start_time_present = False
        if isinstance(self.settings.get('START_TIME', None), str):
            self.start_time = datetime.datetime.strptime(self.settings.START_TIME, "%H:%M:%S.%f0").time()
        else:
            self.start_time = None

        for row in unprocessed_trade_data:
            # Use exchange timestamps because files are ordered on them
            # using local timestamps would require re-ordering the data file
            timestamp = iso8601.parse_date(row[0])
            if self.start_time is not None:
                if timestamp.time() < self.start_time:
                    continue

            if previous_timestamp is None or previous_timestamp != timestamp:
                self._timestamps.append(timestamp)
            # 'time_coinapi', 'price', 'base_amount', 'taker_side'
            side = 'Buy' if row[5] == 'BUY' else 'Sell'
            completed_trade = {'time_object': timestamp, 'timestamp':row[0], 
                                "trdMatchID": row[2], 'price': float(row[3]), 
                               'size': float(row[4]), 'side': row[5]}
            self._trade_data.append(completed_trade)
            previous_timestamp = timestamp 
        
        # load orderbook data
        self.orderbook_timestamp = None
        self.last_line = None #holds last valid orderbook at present_timestamp 
        self.current_orderbook = None
        if L2orderbook_filename != "": 
            orderbook_csvfile = open(L2orderbook_filename)            
            self.orderbookreader = csv.reader(orderbook_csvfile, delimiter=';')
            self._headers2 = next(self.orderbookreader)
            self.current_orderbook = next(self.orderbookreader)

        # Contribute to timekeeper
        self._timekeeper = timekeeper
        self._timekeeper.contribute_times(self._timestamps)
        self._current_trades_location = 0
        self.name = name
        if isinstance(self.settings.EARLY_STOP_TIME, str):
            self.early_stop_time = datetime.datetime.strptime(self.settings.EARLY_STOP_TIME, "%H:%M:%S.%f0").time()
        else:
            self.early_stop_time = None
        self.reached_EOF = False
        
    #
    # Public methods
    #
    def current_timestamp(self):
        self._make_updates()
        return self.external_timestamp

    def wait_update(self):
        if self.reached_EOF == True:
            raise EOFError
        self._make_updates()
    
    def is_warm(self):
        self._make_updates()
        '''Checks to see if there is market data.'''
        return len(self.trades) > 0
     
    def instrument(self, symbol=None):
        instrument = default_instrument 
        if symbol is None:
            symbol = self.settings.SYMBOL 
        tick_size = self.settings.TICK_SIZE[symbol]
        instrument['symbol'] = symbol
        instrument['tickLog'] = Decimal(str(tick_size)).as_tuple().exponent * -1
        return instrument

    def get_instrument(self, symbol=None):
        '''Only really used to provide ticklog '''
        instrument = default_instrument
        if symbol is None:
            symbol = self.settings.SYMBOL 
        tick_size = self.settings.TICK_SIZE[symbol]
        instrument['symbol'] = symbol
        instrument['tickLog'] = Decimal(str(tick_size)).as_tuple().exponent * -1
        return instrument
    
    def ticker_data(self, symbol=None):
        """Get ticker data."""
        self._make_updates()
        if symbol == None or symbol == self.symbol:             
            current_ob = self.market_depth("")
            ticker = {
                'buy'  : current_ob[1]['price'],
                'sell' : current_ob[0]['price'],
                'mid'  : float(current_ob[0]['price'] + current_ob[1]['price'])/2
            }
            return ticker
        else:
            return {}

    def market_depth(self, symbol):
        """Get market depth / orderbook. Returns orderbook or empty list.
        Symbol is ignored."""
        self._make_updates()
        #fail if trades requested before warm
        self._fail_if_not_warm()

        orderbook_snapshot = []
        if self.last_line is None:
            return []
        row = self.last_line
        self.ob_local_timestamp = iso8601.parse_date(self._date_prefix+row[1])
        self.ob_exc_timestamp = iso8601.parse_date(self._date_prefix+row[0])
        for x in range(0,5):
            ask_price = row[4*x + 2]
            ask_size  = row[4*x + 3]
            bid_price = row[4*x + 4]
            bid_size  = row[4*x + 5]
            if ask_price != "":
                orderbook1 = { 'side': 'Sell',
                               'size': float(ask_size),
                               'price': float(ask_price)}
                orderbook_snapshot.append(orderbook1)
            if bid_price != "":
                orderbook2 = { 'side': 'Buy',
                               'size': float(bid_size),
                               'price': float(bid_price)}
                orderbook_snapshot.append(orderbook2)
        return orderbook_snapshot

    def recent_trades(self, number=50):
        """Get recent trades. Defaults to returning 50 trades. 

        Returns
        -------
        A list of dicts:
               {'time_object': datetime.datetime(2018, 9, 1, 0, 0, 3, 932000, 
                   tzinfo=datetime.timezone.utc),
                'timestamp': 2018-09-01T00:00:03.9320000,
                'trdMatchID': 'd180ef47-1e99-455a-8e88-be6c0ccc4d6e', 
                'price': 7017.0, 
                'size': 2000.0, 
                'side': 'SELL'} # or 'BUY'

        """
        self._make_updates()
        #fail if trades requested before warm
        self._fail_if_not_warm()
        number_to_return = min(len(self.trades), number)
        return self.trades[-number_to_return:]

    def get_orderbook_time(self):
        return self.orderbook_timestamp
    
    #
    # Private methods
    #

    def _update_to_timestamp(self, timestamp):
        next_trade = self._trade_data[self._current_trades_location]
        while next_trade['time_object'] <= timestamp:
            if self.early_stop_time is not None:
                if next_trade['time_object'].time() > self.early_stop_time:
                    self.reached_EOF = True
                    break
            #Apply Trade Data
            self.trades.append(next_trade) 
            self.present_timestamp = next_trade['time_object']     
            self._current_trades_location += 1
            if self._current_trades_location == len(self._trade_data):
                self.reached_EOF = True
                break
            next_trade = self._trade_data[self._current_trades_location]


        
    def _update_orderbook(self, timestamp):
        # process self.current_orderbook
        self.orderbook_timestamp = iso8601.parse_date(self._date_prefix+self.current_orderbook[1])
        while self.orderbook_timestamp <= timestamp:
            self.last_line = self.current_orderbook
            try:
                self.current_orderbook = next(self.orderbookreader)
            except StopIteration:
                break
            self.orderbook_timestamp = iso8601.parse_date(self._date_prefix+self.current_orderbook[1])

    def _make_updates(self):
        if self.reached_EOF:
            return
        to_timestamp = self._timekeeper.get_time()
        if self.present_timestamp is None or \
            self.external_timestamp is None or \
            self.external_timestamp <= to_timestamp:
            self._update_to_timestamp(to_timestamp)
        if self.current_orderbook:
            self._update_orderbook(to_timestamp)
        self.external_timestamp = to_timestamp
        # _update_to_timestamp should not have put the current_timestamp 
        # ahead of the timekeeper
        if len(self.trades) > 0:
            assert self.trades[-1]['time_object'] <= to_timestamp
    
    def _fail_if_not_warm(self):
        # use to ensure data is not requested before it is created
        to_timestamp = self._timekeeper.get_time()
        if self.trades == []:
            raise Exception("Accessing trades before class is warm!")
        #check that we haven't updated past the current timekeeper
        assert self.external_timestamp <= to_timestamp
