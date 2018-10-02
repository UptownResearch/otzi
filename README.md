# Otzi
# A Market Maker with backtesting

Otzi is a market making bot designed for use with [BitMEX](https://www.bitmex.com). Otzi is based on BitMEX's sample market maker: https://github.com/BitMEX/sample-market-maker

Otzi provides the following:

* A `BitMEX` object wrapping the REST and WebSocket APIs.
  * All data is realtime and efficiently [fetched via the WebSocket](market_maker/ws/ws_thread.py). This is the fastest way to get market data.
  * Orders may be created, queried, and cancelled via `BitMEX.buy()`, `BitMEX.sell()`, `BitMEX.open_orders()` and the like.
  * Withdrawals may be requested (but they still must be confirmed via email and 2FA).
  * Connection errors and WebSocket reconnection is handled for you.
  * [Permanent API Key](https://testnet.bitmex.com/app/apiKeys) support is included.
* [A scaffolding for building your own trading strategies.](#advanced-usage)
  * Out of the box, a simple market making strategy is implemented that blankets the bid and ask.
  * More complicated strategies are up to the user. Try incorporating [index data](https://testnet.bitmex.com/app/index/.XBT),
    query other markets to catch moves early, or develop your own completely custom strategy.

**Develop on [Testnet](https://testnet.bitmex.com) first!** Testnet trading is completely free and is identical to the live market.


## Getting Started on Testnet

1. Create a [Testnet BitMEX Account](https://testnet.bitmex.com) and [deposit some TBTC](https://testnet.bitmex.com/app/deposit).
2. Install: `pip install bitmex-market-maker`. It is strongly recommeded to use a virtualenv.
3. Create a marketmaker project: run `marketmaker setup`
    * This will create `settings.py` and `market_maker/` in the working directory.
    * Modify `settings.py` to tune parameters.
4. Edit settings.py to add your [BitMEX API Key and Secret](https://testnet.bitmex.com/app/apiKeys) and change bot parameters.
    * Note that user/password authentication is not supported.
    * Run with `DRY_RUN=True` to test cost and spread.
5. Run it: `marketmaker [symbol]`
6. Satisfied with your bot's performance? Create a [live API Key](https://www.bitmex.com/app/apiKeys) for your
   BitMEX account, set the `BASE_URL` and start trading!



## Advanced usage

You can implement custom trading strategies using the market maker. `market_maker.OrderManager`
controls placing, updating, and monitoring orders on BitMEX. To implement your own custom
strategy, subclass `market_maker.OrderManager` and override `OrderManager.place_orders()`:

```
from market_maker.market_maker import OrderManager

class CustomOrderManager(OrderManager):
    def place_orders(self) -> None:
        # implement your custom strategy here
```

Your strategy should provide a set of orders. An order is a dict containing price, quantity, and
whether the order is buy or sell. For example:

```
buy_order = {
    'price': 1234.5, # float
    'orderQty': 100, # int
    'side': 'Buy'
}

sell_order = {
    'price': 9876.5, # float
    'orderQty': 100, # int
    'side': 'Sell'
}
```

Call `self.converge_orders()` to submit your orders. `converge_orders()` will create, amend,
and delete orders on BitMEX as necessary to match what you pass in:

```
def place_orders(self) -> None:
    buy_orders = []
    sell_orders = []

    # populate buy and sell orders, e.g.
    buy_orders.append({'price': 998.0, 'orderQty': 100, 'side': "Buy"})
    buy_orders.append({'price': 999.0, 'orderQty': 100, 'side': "Buy"})
    sell_orders.append({'price': 1000.0, 'orderQty': 100, 'side': "Sell"})
    sell_orders.append({'price': 1001.0, 'orderQty': 100, 'side': "Sell"})

    self.converge_orders(buy_orders, sell_orders)
```

To run your strategy, call `run_loop()`:
```
order_manager = CustomOrderManager()
order_manager.run_loop()
```

Your custom strategy will run until you terminate the program with CTRL-C. There is an example
in `custom_strategy.py`.

## Notes on Rate Limiting

By default, the BitMEX API rate limit is 300 requests per 5 minute interval (avg 1/second).

This bot uses the WebSocket and bulk order placement/amend to greatly reduce the number of calls sent to the BitMEX API.

Most calls to the API consume one request, except:

* Bulk order placement/amend: Consumes 0.1 requests, rounded up, per order. For example, placing 16 orders consumes
  2 requests.
* Bulk order cancel: Consumes 1 request no matter the size. Is not blocked by an exceeded ratelimit; cancels will
  always succeed. This bot will always cancel all orders on an error or interrupt.

If you are quoting multiple contracts and your ratelimit is becoming an obstacle, please
[email support](mailto:support@bitmex.com) with details of your quoting. In the vast majority of cases,
we are able to raise a user's ratelimit without issue.

## Troubleshooting

Common errors we've seen:

* `TypeError: __init__() got an unexpected keyword argument 'json'`
  * This is caused by an outdated version of `requests`. Run `pip install -U requests` to update.


## Compatibility

This module supports Python 3.5 and later.

## See also

BitMEX has a Python [REST client](https://github.com/BitMEX/api-connectors/tree/master/official-http/python-swaggerpy)
and [websocket client.](https://github.com/BitMEX/api-connectors/tree/master/official-ws/python)
