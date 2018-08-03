import sys

from market_maker.market_maker import OrderManager


class CustomOrderManager(OrderManager):
    """A sample order manager for implementing your own custom strategy"""

    def place_orders(self) -> None:
        # implement your custom strategy here

        # implement your custom strategy here

        buy_orders = []
        sell_orders = []
        ticker = self.exchange.get_ticker()
        mid = ticker["mid"]
        # populate buy and sell orders, e.g.
        if self.onlyone:
            buy_orders.append({'price': 7000, 'orderQty': 7000, 'side': "Buy"})
            sell_orders.append({'price': 8000, 'orderQty': 8000, 'side': "Sell"})
            self.onlyone = False

        self.converge_orders(buy_orders, sell_orders)


def run() -> None:
    order_manager = CustomOrderManager()

    # Try/except just keeps ctrl-c from printing an ugly stacktrace
    try:
        order_manager.run_loop()
    except (KeyboardInterrupt, SystemExit):
        sys.exit()
