import random
import logging
import json
import requests

logger = logging.getLogger("root")

class orderServices:

    '''Generalizes desired_to_orders functionality to accept a passed class.'''

    def __init__(self):
        self.amend_error_counter = 0
        self.cancelled_orders = []

    def cancel_all_orders(self, exchange, existing_orders):
        for order in existing_orders:
            if 'orderID' not in order:
                logger.warning("Can't Cancel - No orderID in order: %s" % json.dumps(order))
                continue
            if isinstance(order['orderID'], int):
                logger.warning("Can't Cancel - OrderID length must be 36 characters: %s" % json.dumps(order))
                continue
            self.cancelled_orders.append(order['orderID'])
        return exchange.cancel_all_orders()

    def cancel_orders(self, exchange, orders):
        for order in orders:
            if 'orderID' not in order:
                logger.warning("Can't Cancel - No orderID in order: %s" % json.dumps(order))
                continue
            if isinstance(order['orderID'], int):
                logger.warning("Can't Cancel - OrderID must be a string (perhaps you are canceling a promised order: %s" % \
                            json.dumps(order))
                continue
            exchange.cancel_order(order)
            self.cancelled_orders.append(order['orderID'])

    def create_new_orders(self, exchange, to_create):
        tickLog = exchange.get_instrument()['tickLog']
        logger.info("Creating %d orders:" % (len(to_create)))
        #compare_logger.info("Creating %d orders:" % (len(to_create)))
        for order in reversed(to_create):
            logger.info("%4s %d @ %.*f" % (order['side'], order['orderQty'], tickLog, order['price']))
            #compare_logger.info("%4s %d @ %.*f" % (order['side'], order['orderQty'], tickLog, order['price']))
        # TO-DO: Add handling for ccxt.base.errors.InsufficientFunds
        # Example: ccxt.base.errors.InsufficientFunds: gdax Insufficient funds
        exchange.create_bulk_orders(to_create)


    def amend_orders(self, exchange, to_amend, existing_orders):
        tickLog = exchange.get_instrument()['tickLog']
        logger.info("Amending Orders %s" % json.dumps(to_amend))
        for amended_order in reversed(to_amend):
            reference_order = [o for o in existing_orders if o['orderID'] == amended_order['orderID']][0]
            # Below is commented out because 'leavesQty is not available for CCXT
            #logger.info("Amending %4s: %d @ %.*f to %d @ %.*f (%+.*f)" % (
            #    amended_order['side'],
            #    reference_order['leavesQty'], tickLog, reference_order['price'],
            #    (amended_order['orderQty'] - reference_order['cumQty']), tickLog, amended_order['price'],
            #    tickLog, (amended_order['price'] - reference_order['price'])
            #))
        # This can fail if an order has closed in the time we were processing.
        # The API will send us `invalid ordStatus`, which means that the order's status (Filled/Canceled)
        # made it not amendable.
        # If that happens, we need to catch it and re-tick.
        try:
            exchange.amend_bulk_orders(to_amend)
        except requests.exceptions.HTTPError as e:
            errorObj = e.response.json()
            if errorObj['error']['message'] == 'Invalid ordStatus':
                logger.warn("Amending failed. Waiting for order data to converge and retrying.")
                logger.warn("Failed on orders: %s" % json.dumps(to_amend))
                for order in to_amend:
                    self.cancelled_orders.append(order['orderID'])
                #try:
                #    self.cancel_orders(to_amend)
                #except:
                #    logger.warn("Couldn't cancel orders!: %s" % json.dumps(to_amend))
                #    raise
                # sleep(0.5)
                # return self.place_orders()
                self.amend_error_counter += 1
            else:
                logger.error("Unknown error on amend: %s. Exiting" % errorObj)
                sys.exit(1)
        except ValueError as e:
            logger.error('Failed to amend order (Ignoring amend request): ' + str(e))

    def is_live_order(self, order):
        ''' Checks order for liveness. Liveness means that it is an order confirmed
        by the exchange to be live, and is not a promise created by exchange_interface to
        record an expected live order.'''
        if order.get('ordStatus', "") not in ['Filled', 'Canceled'] and \
                'submission_time' not in order and 'ordStatus' in order:
            return True
        else:
            return False

    def live_orders(self, orders):
        '''Tries to determine orders that are live on the exchange.'''
        ret_orders = []
        for order in orders:
            if self.is_live_order(order):
                ret_orders.append(order)
        return ret_orders

    def get_order_with_role(self, orders, role):
        '''Return first order with role.'''
        for order in orders:
            if order.get('side', "") == role and \
                order.get('orderID', "") not in self.cancelled_orders and \
                order.get('ordStatus', "") not in  ['Filled', 'Canceled']:
                return order
        return None

    def get_all_orders_with_role(self, orders, role):
        '''Return all orders with role.'''
        ret_orders = []
        for order in orders:
            if order.get('side', "") == role and \
                order.get('orderID', "") not in self.cancelled_orders and \
                order.get('ordStatus', "") not in  ['Filled', 'Canceled']:
                ret_orders.append(order)
        return ret_orders

    def create_cancel_orders_from_orders(self, orders):
        to_cancel = []
        for order in orders:
            if not self.is_live_order(order):
                logger.warning("Waiting to cancel order: %s" % json.dumps(order))
                continue
            the_keys = ['orderID', 'side', 'orderQty', 'price']
            order_to_cancel = dict((key, value) for key, value in \
                                   order.items() if key in the_keys)
            to_cancel.append(order_to_cancel)
        return to_cancel

    def desired_to_orders(self, exchange, buyprice, sellprice,
                          buyamount=100, sellamount=100, tags={}):
        tickLog = exchange.get_instrument()['tickLog']
        existing_orders = exchange.get_orders()
        to_create = []
        to_amend = []
        to_cancel = []

        # Perform some initial checks
        if len(self.live_orders(existing_orders)) > 4:
            logger.warning("Number of orders exceeds 4, canceling all orders")
            self.cancel_orders(exchange, existing_orders)
            return

        # Manage Buy Order
        buy_orders = self.get_all_orders_with_role(existing_orders, 'Buy')
        if buy_orders != []:
            buy_order = buy_orders[0]
            if len(buy_orders) > 1:
                # cancel all orders above 1
                to_cancel.extend(self.create_cancel_orders_from_orders(buy_orders[1:]))

            # If a recently submitted order, let's not amend
            if self.is_live_order(buy_order) and buy_order['price'] != buyprice:
                the_keys = ['orderID', 'side']
                amended_order = dict((key, value) for key, value in \
                                     buy_order.items() if key in the_keys)
                amended_order['price'] = buyprice
                amended_order['orderQty'] = buyamount
                amended_order.update(tags)
                if amended_order['orderQty'] > 0:
                    to_amend.append(amended_order)
        else:
            # let's create a new order
            buyorder = {'price': buyprice, 'orderQty': buyamount, 'side': "Buy",
                        'orderID': random.randint(0, 100000)}
            buyorder.update(tags)
            if buyorder['orderQty'] > 0:
                to_create.append(buyorder)

        # Manage Sell Order
        sell_orders = self.get_all_orders_with_role(existing_orders, 'Sell')
        if sell_orders != []:
            sell_order = sell_orders[0]
            if len(sell_orders) > 1:
                # cancel all orders above 1
                to_cancel.extend(self.create_cancel_orders_from_orders(sell_orders[1:]))
            # If a recently submitted order, let's not amend
            if self.is_live_order(sell_order) and sell_order['price'] != sellprice:
                the_keys = ['orderID', 'side']
                amended_order = dict((key, value) for key, value in \
                                     sell_order.items() if key in the_keys)
                amended_order['price'] = sellprice
                amended_order['orderQty'] = sellamount
                amended_order.update(tags)
                if amended_order['orderQty'] > 0:
                    to_amend.append(amended_order)
        else:
            # let's create a new order
            sellorder = {'price': sellprice, 'orderQty': sellamount, 'side': "Sell",
                         'orderID': random.randint(0, 100000)}
            sellorder.update(tags)
            if sellorder['orderQty'] > 0:
                to_create.append(sellorder)

        # Amend orders as needed
        if len(to_amend) > 0:
            self.amend_orders(exchange, to_amend, existing_orders)
        # Create any needed new orders
        if len(to_create) > 0:
            self.create_new_orders(exchange, to_create)
        # Cancel any needed orders
        if len(to_cancel) > 0:
            self.cancel_orders(exchange, to_cancel)
