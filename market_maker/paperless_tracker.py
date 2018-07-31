
from market_maker.settings import settings
from market_maker import market_maker
from market_maker.utils import constants
import copy
import datetime


class paperless_tracker:

    __instance = None

    @staticmethod
    def getInstance():
        """ Static access method. """
        if paperless_tracker.__instance == None:
            paperless_tracker()
        return paperless_tracker.__instance

    def __init__(self):
        """ Virtually private constructor. """
        if paperless_tracker.__instance != None:
            raise Exception("Request instance")
        else:
            self.buy_orders_created = []
            self.sell_orders_created = []
            self.filled = []
            self.buy_partially_filled = []
            self.sell_partially_filled = []
            self.closed = []
            self.exchange = market_maker.ExchangeInterface(settings.DRY_RUN)
            self.timestamp = None
            paperless_tracker.__instance = self

    def track_orders_created(self, order):

        if settings.paperless == False:
            return None
        buy_orders = []
        sell_orders = []
        for orders in order:
            if orders["side"] == "Buy":
                buy_orders.append(copy.deepcopy(orders))
            else:
                sell_orders.append(copy.deepcopy(orders))

        for order in buy_orders:
            order["orderQty"] = order["orderQty"] / order["price"]

        for order in sell_orders:
            order["orderQty"] = order["orderQty"] / order["price"]

        if len(buy_orders) > 0:
            self.buy_orders_created.extend(buy_orders)
        if len(sell_orders) > 0:
            self.sell_orders_created.extend(sell_orders)

        order_book = self.exchange.market_deep()

        ask = []
        bid = []
        for orders in order_book:
            if orders['side'] == "Sell":
                ask.append(orders)
            else:
                bid.append(orders)

        for orders in buy_orders:
            orignal_size = orders["orderQty"]
            orders["orderQty"] = 0
            for i in range(len(ask) - 1, -1, -1):
                temp = ask[i]
                if orders["price"] >= temp["price"] and temp["size"] > 0:
                    if (orignal_size - orders["orderQty"]) >= temp["size"]:
                        orders["orderQty"] = orders["orderQty"] + temp["size"]
                        self.insert_to_log("Order Partially Filled - " + " " + orders["side"] + " " + str(orders["orderQty"]) + " @ " + str(orders["price"]) + " " + " Total size: " + str(orignal_size) + " By OderBook: " + str(temp["size"]) + " @ " + str(temp["price"]))
                        temp["size"] = 0
                    else:
                        temp["size"] = temp["size"] - (orignal_size - orders["orderQty"])
                        orders["orderQty"] = orignal_size
                        self.filled.append(orders)
                        self.insert_to_log("Order Filled - " + orders["side"] + " " + str(orders["orderQty"]) + " @ " + str(orders["price"]) + " By OderBook: " + str(temp["size"]) + " @ " + str(temp["price"]))
                        break
            else:
                self.buy_partially_filled.append((orders, orignal_size))

        for orders in sell_orders:
            orignal_size = orders["orderQty"]
            orders["orderQty"] = 0
            for i in range(0, len(bid)):
                temp = bid[i]
                if orders["price"] <= temp["price"] and temp["size"] > 0:
                    if (orignal_size - orders["orderQty"]) >= temp["size"]:
                        orders["orderQty"] = orders["orderQty"] + temp["size"]
                        self.insert_to_log("Order Partially Filled - " + orders["side"] + " " + str(orders["orderQty"]) + " @ " + str(orders["price"]) + " " + " Total size: " + str(orignal_size) + " By OderBook: " + str(temp["size"]) + " @ " + str(temp["price"]))
                        temp["size"] = 0
                    else:
                        temp["size"] = temp["size"] - (orignal_size - orders["orderQty"])
                        orders["orderQty"] = orignal_size
                        self.filled.append(orders)
                        self.insert_to_log("Order Filled - " + " " + orders["side"] + " " + str(orders["orderQty"]) + " @ " + str(orders["price"]) + " By OderBook: " + str(temp["size"]) + " @ " + str(temp["price"]))
                        break
            else:
                self.sell_partially_filled.append((orders, orignal_size))

    def track_orders(self):

        if settings.paperless == False:
            return None

        trades = self.exchange.recent_trades()

        sell = []
        buy = []

        for orders in trades:
            if orders['side'] == "Sell":
                sell.append(orders)
            else:
                buy.append(orders)

        for orders in self.buy_partially_filled:
            orignal_size = orders[1]
            for i in range(0, len(sell)):
                temp = sell[i]
                temp["timestamp"] = temp["timestamp"].replace('T', " ").replace('Z', "")
                temp_date = datetime.datetime.strptime(temp["timestamp"], '%Y-%m-%d %H:%M:%S.%f')
                if self.timestamp == None or temp_date >= self.timestamp:
                    if orders[0]["price"] >= temp["price"] and temp["size"] > 0:
                        if (orignal_size - orders[0]["orderQty"]) >= temp["size"]:
                            orders[0]["orderQty"] = orders[0]["orderQty"] + temp["size"]
                            self.insert_to_log("Order Partially Filled - " + " " + orders[0]["side"] + " " + str(orders[0]["orderQty"]) + " @ " + str(orders[0]["price"]) + " " + " Total size: " + str(orignal_size) + " By Trade: " + str(temp["size"]) + " @ " + str(temp["price"]) + " " + str(temp["timestamp"]))
                            temp["size"] = 0
                            self.timestamp = temp_date
                        else:
                            self.insert_to_log("Order Filled - " + orders[0]["side"] + " " + str(orignal_size) + " @ " + str(orders[0]["price"]) + " By Trade: " + str(temp["size"]) + " @ " + str(temp["price"]) + " " + str(temp["timestamp"]))
                            temp["size"] = temp["size"] - (orignal_size - orders[0]["orderQty"])
                            orders[0]["orderQty"] = orignal_size
                            self.timestamp = temp_date
                            break

        for orders in self.sell_partially_filled:
            orignal_size = orders[1]
            for i in range(0, len(buy)):
                temp = buy[i]
                temp["timestamp"] = temp["timestamp"].replace('T', " ").replace('Z', "")
                temp_date = datetime.datetime.strptime(temp["timestamp"], '%Y-%m-%d %H:%M:%S.%f')
                if self.timestamp == None or temp_date >= self.timestamp:
                    if orders[0]["price"] <= temp["price"] and temp["size"] > 0:
                        if (orignal_size - orders[0]["orderQty"]) >= temp["size"]:
                            orders[0]["orderQty"] = orders[0]["orderQty"] + temp["size"]
                            self.insert_to_log("Order Partially Filled - " + " " + orders[0]["side"] + " " + str(orders[0]["orderQty"]) + " @ " + str(orders[0]["price"]) + " " + " Total size: " + str(orignal_size) + " By Trade: " + str(temp["size"]) + " @ " + str(temp["price"]) + " " +  str(temp["timestamp"]))
                            temp["size"] = 0
                            self.timestamp = temp_date
                        else:
                            self.insert_to_log("Order Filled - " + orders[0]["side"] + " " + str(orignal_size) + " @ " + str(orders[0]["price"]) + " By Trade: " + str(temp["size"]) + " @ " + str(temp["price"]) + " " + str(temp["timestamp"]))
                            temp["size"] = temp["size"] - (orignal_size - orders[0]["orderQty"])
                            orders[0]["orderQty"] = orignal_size
                            self.timestamp = temp_date
                            break

        self.from_partially_to_filled()

    def from_partially_to_filled(self):

        auxclone = copy.deepcopy(self.buy_partially_filled)
        deleted_ones = 0

        for i in range(0, len(auxclone)):
            if auxclone[i][0]["orderQty"] == auxclone[i][1]:
                self.filled.append(auxclone[i][0])
                del self.buy_partially_filled[i - deleted_ones]
                deleted_ones += 1

        auxclone = copy.deepcopy(self.sell_partially_filled)
        deleted_ones = 0

        for i in range(0, len(auxclone)):
            if auxclone[i][0]["orderQty"] == auxclone[i][1]:
                self.filled.append(auxclone[i][0])
                del self.sell_partially_filled[i - deleted_ones]
                deleted_ones += 1

    def get_funds(self):

        buy_average = 0
        buy_quantity = 0

        sell_average = 0
        sell_quantity = 0

        for order in self.closed:
            if order["side"] == "Buy":
                buy_average = buy_average + (order["orderQty"] * order["price"])
                buy_quantity = buy_quantity + order["orderQty"]
            else:
                sell_average = sell_average + (order["orderQty"] * order["price"])
                sell_quantity = sell_quantity + order["orderQty"]

        if (buy_quantity > 0):
            buy_average = buy_average / buy_quantity
        else:
            buy_average = 0

        if (sell_quantity > 0):
            sell_average = sell_average / sell_quantity
        else:
            sell_average = 0

        funds = 0
        if buy_quantity > 0:
            funds = (sell_average - buy_average) * buy_quantity
        if sell_quantity > 0:
            funds = (sell_average - buy_average) * sell_quantity

        ticker = self.exchange.get_ticker()
        mid = ticker["mid"]
        in_btc = funds / mid

        return {"marginBalance": (settings.DRY_BTC + in_btc) * constants.XBt_TO_XBT}

    def get_position(self, symbol):

        '''
        buy_average = 0
        buy_quantity = 0

        sell_average = 0
        sell_quantity = 0

        for order in self.filled:
            if order["side"] == "Buy":
                buy_average = buy_average + (order["orderQty"] * order["price"])
                buy_quantity = buy_quantity + (order["orderQty"] * order["price"])
            else:
                sell_average = sell_average + (order["orderQty"] * order["price"])
                sell_quantity = sell_quantity + (order["orderQty"] * order["price"])

        for order in self.buy_partially_filled:
            buy_average = buy_average + (order[0]["orderQty"] * order[0]["price"])
            buy_quantity = buy_quantity + (order[0]["orderQty"] * order[0]["price"])

        for order in self.sell_partially_filled:
            sell_average = sell_average + (order[0]["orderQty"] * order[0]["price"])
            sell_quantity = sell_quantity + (order[0]["orderQty"] * order[0]["price"])

        if (buy_quantity > 0):
            buy_average = buy_average / buy_quantity
        else:
            buy_average = 0

        if (sell_quantity > 0):
            sell_average = sell_average / sell_quantity
        else:
            sell_average = 0

        if buy_average == 0 and sell_average == 0:
            return {'avgCostPrice': 0, 'avgEntryPrice': 0, 'currentQty': 0, 'symbol': symbol}
        elif buy_average == 0 and sell_average > 0:
            return {'avgCostPrice': 0, 'avgEntryPrice': 0, 'currentQty': 0, 'symbol': symbol}
        elif buy_average > 0 and sell_average == 0:
            return {'avgCostPrice': 0, 'avgEntryPrice': 0, 'currentQty': 0, 'symbol': symbol}
        '''

        buy_quantity = 0
        sell_quantity = 0
        sumAux = 0

        for orders in self.filled:
            sumAux += ((orders["orderQty"] * orders["price"]) / orders["price"])
            buy_quantity = buy_quantity + (orders["orderQty"] * orders["price"])

        for orders in self.buy_partially_filled:
            sumAux += ((orders[0]["orderQty"] * orders[0]["price"]) / orders[0]["price"])
            buy_quantity = buy_quantity + (orders[0]["orderQty"] * orders[0]["price"])

        for orders in self.sell_partially_filled:
            sumAux += ((orders[0]["orderQty"] * orders[0]["price"]) / orders[0]["price"])
            buy_quantity = buy_quantity + (orders[0]["orderQty"] * orders[0]["price"])

        new_qty = buy_quantity + sell_quantity
        if new_qty == 0:
            return {'avgCostPrice': 0, 'avgEntryPrice': 0, 'currentQty': 0, 'symbol': symbol}
        #X2 = sell_average - (buy_quantity * ((sell_average - buy_average) / new_qty))
        #total_quantity / ((quantity_1 / price_1) + (quantity_2 / price_2)) = entry_price

        X2 = new_qty / sumAux

        if new_qty > 0:
            return {'avgCostPrice': X2, 'avgEntryPrice': X2, 'currentQty': new_qty, 'symbol': symbol}

        elif new_qty < 0:
            return {'avgCostPrice': X2, 'avgEntryPrice': X2, 'currentQty': new_qty, 'symbol': symbol}

    def close_positions(self):

        if settings.paperless == False:
            return None

        auxsum = 0
        auxlist = copy.deepcopy(self.filled)
        to_delete = 0
        last_insert = 0
        for i in range(0, len(auxlist)):

            Q = auxlist[i]

            if Q["side"] == "Buy":
                auxsum = auxsum + Q["orderQty"]
            else:
                auxsum = auxsum - Q["orderQty"]

            to_delete += 1

            if auxsum == 0:
                for j in range(last_insert, i + 1):
                    self.closed.append(auxlist[j])
                for j in range(0, to_delete):
                    del self.filled[0]
                to_delete = 0
                last_insert = i + 1

    def loop_functions(self):

        if settings.paperless == False:
            return None

        self.track_orders()
        self.close_positions()

    def current_contract(self):
        count = 0

        for orders in self.filled:
            if orders["side"] == "Buy":
                count += orders["orderQty"]
            else:
                count -= orders["orderQty"]

        for orders in self.buy_partially_filled:
            count += orders[0]["orderQty"]

        for orders in self.sell_partially_filled:
            count -= orders[0]["orderQty"]

        return count

    def contract_traded_this_run(self):
        count = 0

        for orders in self.filled:
            count += orders["orderQty"]

        for orders in self.buy_partially_filled:
            count += orders[0]["orderQty"]

        for orders in self.sell_partially_filled:
            count += orders[0]["orderQty"]

        for orders in self.closed:
            count += orders["orderQty"]

        return count

    def insert_to_log(self, action):

        file = open("trading_log.txt", "a+")
        file.write(str(datetime.datetime.now()) + " - INFO - paperless_tracker" + action + "\n")
        file.close()

    def get_orders(self):

        final = []

        for orders in self.filled:
            final.append(orders)

        for orders in self.buy_partially_filled:
            final.append(orders[0])

        for orders in self.sell_partially_filled:
            final.append(orders[0])

        return final





