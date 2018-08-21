
from market_maker.settings import settings
from market_maker import market_maker
from market_maker.utils import constants
import copy
import datetime
import random
import logging
import json

#log orders to file
pt_logger = logging.getLogger("paperless_orders")
pt_logger.setLevel(logging.INFO)

if settings.LOG_ORDERS_TO_FILE: 
    order_file = settings.ROOT_LOG_LOCATION + "pt_orders/" + \
                ('p' if settings.paperless else "") + \
                f"{datetime.datetime.now():%Y-%m-%d}" + ".log"
    ofh = logging.FileHandler(order_file)
    simple_formatter = logging.Formatter('%(asctime)s - %(message)s')
    ofh.setFormatter(simple_formatter)
    pt_logger.addHandler(ofh)


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
            self.random_base = random.randint(0, 100000)
            self.exchange = market_maker.ExchangeInterface(settings.DRY_RUN)
            self.timestamp = None
            self.auxFunds = 0
            self.position = self.position = {'avgCostPrice': 0, 'avgEntryPrice': 0, 'currentQty': 0, 'symbol': "XBTUSD"}
            paperless_tracker.__instance = self


    def track_orders_created(self, orders):

        if settings.paperless == False and settings.compare == False:
            return None
        buy_orders = []
        sell_orders = []
        for order in orders:
            order_out = {
            'status': 'Created',
            'paperless' : settings.paperless,
            'type' : 'Paper',
            'data' : order
            }
            pt_logger.info(json.dumps(order_out))
            if order["side"] == "Buy":
                buy_orders.append(copy.deepcopy(order))
            else:
                sell_orders.append(copy.deepcopy(order))

        if len(buy_orders) > 0:
            self.buy_orders_created.extend(buy_orders)
        if len(sell_orders) > 0:
            self.sell_orders_created.extend(sell_orders)

        order_book = self.exchange.market_deep()

        ask = []
        bid = []
        for order in order_book:
            if order['side'] == "Sell":
                ask.append(order)
            else:
                bid.append(order)

        if settings.compare ==  False:
            for order in buy_orders:
                self.random_base += 1
                order["orderID"] = self.random_base
                order["cumQty"] = 0
                order["leavesQty"] = order["orderQty"] - order["cumQty"]
                for i in range(len(ask) - 1, -1, -1):
                    temp = ask[i]
                    if order["price"] >= temp["price"] and temp["size"] > 0:
                        if (order["orderQty"] - order["cumQty"]) >= temp["size"]:
                            order["cumQty"] = order["cumQty"] + temp["size"]
                            self.calculate_position(order, temp["size"])
                            order["leavesQty"] = order["orderQty"] - order["cumQty"]
                            self.insert_to_log("Order Partially Filled - ID:" + str(order["orderID"]) + " " + order["side"] + " " + str(order["cumQty"]) + " @ " + str(order["price"]) + " " + " Total size: " + str(order["orderQty"]) + " By OderBook: " + str(temp["size"]) + " @ " + str(temp["price"]))
                            order_out = {
                                'status' : 'Partially Filled',
                                'paperless' : settings.paperless,
                                'type' : 'Paper',
                                'fillprice' : temp["price"],
                                'fillsize' : temp["size"],
                                'data' : order
                            }
                            pt_logger.info(json.dumps(order_out))
                            temp["size"] = 0
                        else:
                            temp["size"] = temp["size"] - (order["orderQty"] - order["cumQty"])
                            self.calculate_position(order, (order["orderQty"] - order["cumQty"]))
                            order["cumQty"] = order["orderQty"]
                            order["leavesQty"] = 0
                            self.filled.append(order)
                            self.insert_to_log("Order Filled - ID:" + str(order["orderID"]) + " " + order["side"] + " " + str(order["orderQty"]) + " @ " + str(order["price"]) + " By OderBook: " + str(temp["size"]) + " @ " + str(temp["price"]))
                            order_out = {
                                'status' : 'Filled',
                                'paperless' : settings.paperless,
                                'type' : 'Paper',
                                'fillprice' : temp["price"],
                                'fillsize' : temp["size"],
                                'data' : order
                            }
                            pt_logger.info(json.dumps(order_out))
                            break
                else:
                    self.buy_partially_filled.append(order)
                    self.insert_to_log("Order Not Filled - ID:" + str(order["orderID"]) + " " + order["side"] + " " + str(order["cumQty"]) + " @ " + str(order["price"]) + " " + " Total size: " + str(order["orderQty"]))

            for order in sell_orders:
                self.random_base += 1
                order["orderID"] = self.random_base
                order["cumQty"] = 0
                order["leavesQty"] = order["orderQty"] - order["cumQty"]
                for i in range(0, len(bid)):
                    temp = bid[i]
                    if order["price"] <= temp["price"] and temp["size"] > 0:
                        if (order["orderQty"] - order["cumQty"]) >= temp["size"]:
                            order["orderQty"] = order["orderQty"]
                            order["cumQty"] = order["cumQty"] + temp["size"]
                            self.calculate_position(order, temp["size"])
                            order["leavesQty"] = order["orderQty"] - order["cumQty"]
                            self.insert_to_log("Order Partially Filled - ID:" + str(order["orderID"]) + " " + order["side"] + " " + str(order["orderQty"]) + " @ " + str(order["price"]) + " " + " Total size: " + str(order["orderQty"]) + " By OderBook: " + str(temp["size"]) + " @ " + str(temp["price"]))
                            order_out = {
                                'status' : 'Partially Filled',
                                'paperless' : settings.paperless,
                                'type' : 'Paper',
                                'fillprice' : temp["price"],
                                'fillsize' : temp["size"],
                                'data' : order
                            }
                            pt_logger.info(json.dumps(order_out))
                            temp["size"] = 0
                        else:
                            temp["size"] = temp["size"] - (order["orderQty"] - order["cumQty"])
                            self.calculate_position(order, (order["orderQty"] - order["cumQty"]))
                            order["cumQty"] = order["orderQty"]
                            order["leavesQty"] = 0
                            self.filled.append(order)
                            self.insert_to_log("Order Filled - ID:" + str(order["orderID"]) + " " + order["side"] + " " + str(order["orderQty"]) + " @ " + str(order["price"]) + " By OderBook: " + str(temp["size"]) + " @ " + str(temp["price"]))
                            order_out = {
                                'status' : 'Filled',
                                'paperless' : settings.paperless,
                                'type' : 'Paper',
                                'fillprice' : temp["price"],
                                'fillsize' : temp["size"],
                                'data' : order
                            }
                            pt_logger.info(json.dumps(order_out))
                            break
                else:
                    self.sell_partially_filled.append(order)
                    self.insert_to_log("Order Not Filled - ID:" + str(order["orderID"]) + " " + order["side"] + " " + str(order["cumQty"]) + " @ " + str(order["price"]) + " " + " Total size: " + str(order["orderQty"]))
        else:
            for order in buy_orders:
                order["leavesQty"] = order["orderQty"] - order["cumQty"]
                for i in range(len(ask) - 1, -1, -1):
                    temp = ask[i]
                    if order["price"] >= temp["price"] and temp["size"] > 0:
                        if (order["orderQty"] - order["cumQty"]) >= temp["size"]:
                            order["cumQty"] = order["cumQty"] + temp["size"]
                            self.calculate_position(order, temp["size"])
                            order["leavesQty"] = order["orderQty"] - order["cumQty"]
                            self.insert_to_log("Order Partially Filled - ID:" + str(order["orderID"]) + " " + order[
                                "side"] + " " + str(order["cumQty"]) + " @ " + str(
                                order["price"]) + " " + " Total size: " + str(
                                order["orderQty"]) + " By OderBook: " + str(temp["size"]) + " @ " + str(temp["price"]))
                            order_out = {
                                'status': 'Partially Filled',
                                'paperless': settings.paperless,
                                'type': 'Paper',
                                'fillprice': temp["price"],
                                'fillsize': temp["size"],
                                'data': order
                            }
                            pt_logger.info(json.dumps(order_out))
                            temp["size"] = 0
                        else:
                            temp["size"] = temp["size"] - (order["orderQty"] - order["cumQty"])
                            self.calculate_position(order, (order["orderQty"] - order["cumQty"]))
                            order["cumQty"] = order["orderQty"]
                            order["leavesQty"] = 0
                            self.filled.append(order)
                            self.insert_to_log(
                                "Order Filled - ID:" + str(order["orderID"]) + " " + order["side"] + " " + str(
                                    order["orderQty"]) + " @ " + str(order["price"]) + " By OderBook: " + str(
                                    temp["size"]) + " @ " + str(temp["price"]))
                            order_out = {
                                'status': 'Filled',
                                'paperless': settings.paperless,
                                'type': 'Paper',
                                'fillprice': temp["price"],
                                'fillsize': temp["size"],
                                'data': order
                            }
                            pt_logger.info(json.dumps(order_out))
                            break
                else:
                    self.buy_partially_filled.append(order)
                    self.insert_to_log(
                        "Order Not Filled - ID:" + str(order["orderID"]) + " " + order["side"] + " " + str(
                            order["cumQty"]) + " @ " + str(order["price"]) + " " + " Total size: " + str(
                            order["orderQty"]))

            for order in sell_orders:
                order["leavesQty"] = order["orderQty"] - order["cumQty"]
                for i in range(0, len(bid)):
                    temp = bid[i]
                    if order["price"] <= temp["price"] and temp["size"] > 0:
                        if (order["orderQty"] - order["cumQty"]) >= temp["size"]:
                            order["orderQty"] = order["orderQty"]
                            order["cumQty"] = order["cumQty"] + temp["size"]
                            self.calculate_position(order, temp["size"])
                            order["leavesQty"] = order["orderQty"] - order["cumQty"]
                            self.insert_to_log("Order Partially Filled - ID:" + str(order["orderID"]) + " " + order[
                                "side"] + " " + str(order["orderQty"]) + " @ " + str(
                                order["price"]) + " " + " Total size: " + str(
                                order["orderQty"]) + " By OderBook: " + str(temp["size"]) + " @ " + str(temp["price"]))
                            order_out = {
                                'status': 'Partially Filled',
                                'paperless': settings.paperless,
                                'type': 'Paper',
                                'fillprice': temp["price"],
                                'fillsize': temp["size"],
                                'data': order
                            }
                            pt_logger.info(json.dumps(order_out))
                            temp["size"] = 0
                        else:
                            temp["size"] = temp["size"] - (order["orderQty"] - order["cumQty"])
                            self.calculate_position(order, (order["orderQty"] - order["cumQty"]))
                            order["cumQty"] = order["orderQty"]
                            order["leavesQty"] = 0
                            self.filled.append(order)
                            self.insert_to_log(
                                "Order Filled - ID:" + str(order["orderID"]) + " " + order["side"] + " " + str(
                                    order["orderQty"]) + " @ " + str(order["price"]) + " By OderBook: " + str(
                                    temp["size"]) + " @ " + str(temp["price"]))
                            order_out = {
                                'status': 'Filled',
                                'paperless': settings.paperless,
                                'type': 'Paper',
                                'fillprice': temp["price"],
                                'fillsize': temp["size"],
                                'data': order
                            }
                            pt_logger.info(json.dumps(order_out))
                            break
                else:
                    self.sell_partially_filled.append(order)
                    self.insert_to_log(
                        "Order Not Filled - ID:" + str(order["orderID"]) + " " + order["side"] + " " + str(
                            order["cumQty"]) + " @ " + str(order["price"]) + " " + " Total size: " + str(
                            order["orderQty"]))

    def track_orders(self):

        if settings.paperless == False:
            return None

        trades = self.exchange.recent_trades()

        sell = []
        buy = []

        for trade in trades:
            if trade['side'] == "Sell":
                sell.append(trade)
            else:
                buy.append(trade)

        for order in self.buy_partially_filled:
            orignal_size = order["orderQty"]
            for i in range(0, len(sell)):
                temp = sell[i]
                temp["timestamp"] = temp["timestamp"].replace('T', " ").replace('Z', "")
                temp_date = datetime.datetime.strptime(temp["timestamp"], '%Y-%m-%d %H:%M:%S.%f')
                if self.timestamp == None or temp_date >= self.timestamp:
                    if order["price"] >= temp["price"] and temp["size"] > 0:
                        if (orignal_size - order["cumQty"]) >= temp["size"]:
                            order["orderQty"] = orignal_size
                            order["cumQty"] = order["cumQty"] + temp["size"]
                            self.calculate_position(order, temp["size"])
                            order["leavesQty"] = order["orderQty"] - order["cumQty"]
                            self.insert_to_log("Order Partially Filled - ID:" + str(order["orderID"]) + " " + order["side"] + " " + str(order["cumQty"]) + " @ " + str(order["price"]) + " " + " Total size: " + str(orignal_size) + " By Trade: " + str(temp["size"]) + " @ " + str(temp["price"]) + " " + str(temp["timestamp"]))
                            self.timestamp = temp_date
                            order_out = {
                            'status' : 'Partially Filled',
                            'paperless' : settings.paperless,
                            'type' : 'Paper',
                            'fillprice' : temp["price"],
                            'fillsize' : temp["size"], 
                            'data' : order
                            }
                            pt_logger.info(json.dumps(order_out))
                            temp["size"] = 0
                        else:
                            self.insert_to_log("Order Filled - ID:" + str(order["orderID"]) + " " + order["side"] + " " + str(orignal_size) + " @ " + str(order["price"]) + " By Trade: " + str(temp["size"]) + " @ " + str(temp["price"]) + " " + str(temp["timestamp"]))
                            temp["size"] = temp["size"] - (orignal_size - order["cumQty"])
                            self.calculate_position(order, (order["orderQty"] - order["cumQty"]))
                            order["orderQty"] = orignal_size
                            order["cumQty"] = orignal_size
                            order["leavesQty"] = 0
                            self.timestamp = temp_date
                            order_out = {
                            'status' : 'Filled',
                            'paperless' : settings.paperless,
                            'type' : 'Paper',
                            'fillprice' : temp["price"],
                            'fillsize' : temp["size"], 
                            'data' : order
                            }
                            pt_logger.info(json.dumps(order_out))
                            break

        for order in self.sell_partially_filled:
            orignal_size = order["orderQty"]
            for i in range(0, len(buy)):
                temp = buy[i]
                temp["timestamp"] = temp["timestamp"].replace('T', " ").replace('Z', "")
                temp_date = datetime.datetime.strptime(temp["timestamp"], '%Y-%m-%d %H:%M:%S.%f')
                if self.timestamp == None or temp_date >= self.timestamp:
                    if order["price"] <= temp["price"] and temp["size"] > 0:
                        if (orignal_size - order["cumQty"]) >= temp["size"]:
                            order["orderQty"] = orignal_size
                            order["cumQty"] = order["cumQty"] + temp["size"]
                            self.calculate_position(order, temp["size"])
                            order["leavesQty"] = order["orderQty"] - order["cumQty"]
                            self.insert_to_log("Order Partially Filled - ID:" + str(order["orderID"]) + " " + order["side"] + " " + str(order["cumQty"]) + " @ " + str(order["price"]) + " " + " Total size: " + str(orignal_size) + " By Trade: " + str(temp["size"]) + " @ " + str(temp["price"]) + " " +  str(temp["timestamp"]))
                            order_out = {
                            'status' : 'Partially Filled',
                            'paperless' : settings.paperless,
                            'type' : 'Paper',
                            'fillprice' : temp["price"],
                            'fillsize' : temp["size"],
                            'data' : order
                            }
                            pt_logger.info(json.dumps(order_out))
                            temp["size"] = 0
                            self.timestamp = temp_date
                        else:
                            self.insert_to_log("Order Filled - ID:" + str(order["orderID"]) + " " + order["side"] + " " + str(orignal_size) + " @ " + str(order["price"]) + " By Trade: " + str(temp["size"]) + " @ " + str(temp["price"]) + " " + str(temp["timestamp"]))
                            temp["size"] = temp["size"] - (orignal_size - order["cumQty"])
                            self.calculate_position(order, (order["orderQty"] - order["cumQty"]))
                            order["orderQty"] = orignal_size
                            order["cumQty"] = orignal_size
                            order["leavesQty"] = 0
                            self.timestamp = temp_date
                            order_out = {
                            'status' : 'Filled',
                            'paperless' : settings.paperless,
                            'type' : 'Paper',
                            'fillprice' : temp["price"],
                            'fillsize' : temp["size"], 
                            'data' : order
                            }
                            pt_logger.info(json.dumps(order_out))
                            break

        self.from_partially_to_filled()

    def from_partially_to_filled(self):

        auxclone = copy.deepcopy(self.buy_partially_filled)
        deleted_ones = 0

        for i in range(0, len(auxclone)):
            if auxclone[i]["orderQty"] == auxclone[i]["cumQty"]:
                self.filled.append(auxclone[i])
                del self.buy_partially_filled[i - deleted_ones]
                deleted_ones += 1

        auxclone = copy.deepcopy(self.sell_partially_filled)
        deleted_ones = 0

        for i in range(0, len(auxclone)):
            if auxclone[i]["orderQty"] == auxclone[i]["cumQty"]:
                self.filled.append(auxclone[i])
                del self.sell_partially_filled[i - deleted_ones]
                deleted_ones += 1

    def get_funds(self):
        return {"marginBalance": (settings.DRY_BTC + self.auxFunds) * constants.XBt_TO_XBT}

    def get_position(self, symbol):

        self.position["symbol"] = symbol
        return self.position

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

        for order in self.filled:
            if order["side"] == "Buy":
                count += order["orderQty"]
            else:
                count -= order["orderQty"]

        for order in self.buy_partially_filled:
            count += order["cumQty"]

        for order in self.sell_partially_filled:
            count -= order["cumQty"]

        return count

    def contract_traded_this_run(self):
        count = 0

        for order in self.filled:
            count += order["orderQty"]

        for order in self.buy_partially_filled:
            count += order["cumQty"]

        for order in self.sell_partially_filled:
            count += order["cumQty"]

        for order in self.closed:
            count += order["orderQty"]

        return count

    def insert_to_log(self, action):

        file = open("trading_log.txt", "a+")
        file.write(str(datetime.datetime.now()) + " - INFO - paperless_tracker" + action + "\n")
        file.close()

    def get_orders(self):

        final = []

        for order in self.buy_partially_filled:
            final.append(order)

        for order in self.sell_partially_filled:
            final.append(order)

        return final

    def cancel_order(self, orderID):

        for i in range(0, len(self.buy_partially_filled)):
            if self.buy_partially_filled[i]["orderID"] == orderID:
                if self.buy_partially_filled[i]["cumQty"] > 0:
                    self.buy_partially_filled[i]["orderQty"] = self.buy_partially_filled[i]["cumQty"]
                    self.filled.append(self.buy_partially_filled[i])
                self.insert_to_log(" Cancelling - ID:" + str(self.buy_partially_filled[i]["orderID"]) + " " + self.buy_partially_filled[i]["side"] + " " + str(self.buy_partially_filled[i]["orderQty"]) + " @ " + str(self.buy_partially_filled[i]["price"]))
                order_out = {
                'status' : 'Cancelled',
                'paperless' : settings.paperless,
                'type' : 'Paper',
                'data' : self.buy_partially_filled[i]
                }
                pt_logger.info(json.dumps(order_out))
                del self.buy_partially_filled[i]
                break

        for i in range(0, len(self.sell_partially_filled)):
            if self.sell_partially_filled[i]["orderID"] == orderID:
                if self.sell_partially_filled[i]["cumQty"] > 0:
                    self.sell_partially_filled[i]["orderQty"] = self.sell_partially_filled[i]["cumQty"]
                    self.filled.append(self.sell_partially_filled[i])
                self.insert_to_log(" Cancelling - ID:" + str(self.sell_partially_filled[i]["orderID"]) + " " + self.sell_partially_filled[i]["side"] + " " + str(self.sell_partially_filled[i]["orderQty"]) + " @ " + str(self.sell_partially_filled[i]["price"]))
                order_out = {
                'status' : 'Cancelled',
                'paperless' : settings.paperless,
                'type' : 'Paper',
                'data' : self.sell_partially_filled[i]
                }
                pt_logger.info(json.dumps(order_out))
                del self.sell_partially_filled[i]
                break

    def cancel_all_orders(self):

        cloneBuy = copy.deepcopy(self.buy_partially_filled)

        cloneSell = copy.deepcopy(self.sell_partially_filled)

        for order in cloneBuy:
            self.cancel_order(order["orderID"])

        for order in cloneSell:
            self.cancel_order(order["orderID"])

    def calculate_position(self, order, Qty):

        clone = Qty

        if order["side"] == "Sell":
            clone *= -1

        if self.position["currentQty"] == 0:
            self.position = {'avgCostPrice': order["price"], 'avgEntryPrice': order["price"], 'currentQty': clone, 'symbol': "XBTUSD"}
            return

        if (self.position["currentQty"] < 0 and clone < 0) or (self.position["currentQty"] > 0 and clone > 0):

            newQTY = self.position["currentQty"] + clone

            newPrice = (self.position["avgEntryPrice"] * self.position["currentQty"]) + (clone * order["price"])

            self.position["avgCostPrice"] = newPrice / newQTY
            self.position["avgEntryPrice"] = newPrice / newQTY
            self.position["currentQty"] = newQTY

        else:

            if self.position["currentQty"] > Qty:

                    if self.position["currentQty"] > 0:
                        profit = ((1/self.position["avgEntryPrice"]) - (1/order["price"])) * Qty
                    else:
                        profit = ((1/order["price"]) - (1/self.position["avgEntryPrice"])) * Qty

                    self.position["currentQty"] = self.position["currentQty"] + clone

                    self.auxFunds += profit

            else:

                if self.position["currentQty"] > 0:
                    profit = ((1/self.position["avgEntryPrice"]) - (1/order["price"])) * abs(self.position["currentQty"])
                else:
                    profit = ((1/order["price"]) - (1/self.position["avgEntryPrice"])) * abs(self.position["currentQty"])

                self.position["avgEntryPrice"] = order["price"]
                self.position["avgCostPrice"] = order["price"]
                self.position["currentQty"] = self.position["currentQty"] + clone

                self.auxFunds += profit
                
    def amend_bulk_orders(self, orders):
        order_book = self.exchange.market_deep()

        ask = []
        bid = []
        for order_in_book in order_book:
            if order_in_book['side'] == "Sell":
                ask.append(order_in_book)
            else:
                bid.append(order_in_book)
        for order in orders:
            if order["side"] == "Buy":
                for to_amend in self.buy_partially_filled:
                    if to_amend["orderID"] == order["orderID"]:
                        if to_amend["cumQty"] > order["orderQty"]:
                            to_amend["orderQty"] = to_amend["cumQty"]
                            to_amend["leavesQty"] = 0
                            to_amend["price"] = order["price"]
                            break
                        else:
                            order["cumQty"] = to_amend["cumQty"]
                            self.buy_partially_filled.remove(to_amend)
                            aux_orders = []
                            aux_orders.append(order)
                            self.track_orders_created(aux_orders)
                            self.insert_to_log("Order Amended - ID:" + str(order["orderID"]) + " " + order["side"] + " " + str(order["orderQty"]))
                            break

            elif order["side"] == "Sell":
                for to_amend in self.sell_partially_filled:
                    if to_amend["orderID"] == order["orderID"]:
                        if to_amend["cumQty"] > order["orderQty"]:
                            to_amend["orderQty"] = to_amend["cumQty"]
                            to_amend["leavesQty"] = 0
                            break
                        else:
                            order["cumQty"] = to_amend["cumQty"]
                            self.sell_partially_filled.remove(to_amend)
                            aux_orders = []
                            aux_orders.append(order)
                            self.track_orders_created(aux_orders)
                            self.insert_to_log("Order Amended - ID:" + str(order["orderID"]) + " " + order["side"] + " " + str(order["orderQty"]))
                            break









