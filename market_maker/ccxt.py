import ccxt

testCredentials = {
            'apiKey': '46b32c0f5a32b7c263b4d966aebf995a',
            'secret': 'XB73Bo/E0v2gLSvPZNDhRdmqkBpJQ3DErXL60xEiu1OIdC1Ddx9zVkX64mjMPixThsT1oO/4NZtwsSL53jiTNA==',
            'password': 't5crbhy2r4',
            'timeout': 30000,
            'enableRateLimit': True,
        }

class ccxtInterface:
    def __init__(self, dry_run=False, settings={}, logger="orders",
                 exchange = 'gdax', credentials=testCredentials):
        self.dry_run = dry_run
        self.settings = settings
        self.symbol = self.settings.get('SYMBOL', 'BTC/USD')
        self.exchange_id = exchange
        exchange_class = getattr(ccxt, self.exchange_id)
        self.exchange = exchange_class(credentials)
        self.TEST_EXCHANGE = self.settings.get('USE_TEST_EXCHANGE', True)
        if self.TEST_EXCHANGE:
            self.exchange.urls['api'] = self.exchange.urls['test']

    def get_instrument(self, symbol=None):
        if symbol is None:
            symbol = self.symbol
        return self.bitmex.instrument(symbol)