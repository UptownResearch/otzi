import sys
import requests
import logging
import json
import ssl
import websocket
import threading
import random
from time import sleep
import time

from requests_aws4auth import AWS4Auth


class AccountConnection:
    def __init__(self, settings = {}):
        self.logger = logging.getLogger('root')
        self.settings = settings

        # class settings from settings dict should be retrieved here
        self.region  = self.settings.get('LXDX_REGION','ap-southeast-1')
        self.service = self.settings.get('LXDX_SERVICE', 'execute-api' )
        self.key     = self.settings.get('LXDX_KEY','AKIAIQZAX5JGUTN6GGYQ')
        self.secret  = self.settings.get('LXDX_SECRET', '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')
        self.base_url= self.settings.get('LXDX_BASE_URL', 'https://api-cert.lxdx-svcs.net/v1/')
        self.timeout = self.settings.get('TIMEOUT', 7)
        self.session = self._prep_session()
        self.headers = None

        self.__reset()

        #log root to console for now
        handler = logging.StreamHandler()
        formatter = logging.Formatter(fmt='%(asctime)s - %(levelname)s - %(module)s - %(message)s')
        handler.setFormatter(formatter)
        handler.setLevel(logging.DEBUG)
        #   logger.setLevel(log_level)
        self.logger.setLevel(logging.DEBUG)
        if not len(self.logger.handlers):
            self.logger.addHandler(handler)


    def _get_token(self):
        return self._curl_exchange(path='messages/token')['token']


    def connect(self):
        '''Connect to the websocket and initialize data stores.'''

        self.logger.debug("Connecting to Account WebSocket.")

        # Get token
        token = self._get_token()

        # Get WS URL
        wsURL = "wss://iris-cert.lxdx-svcs.net/v1/account?token=%s" % token

        # Connect
        self.logger.info("Connecting to %s" % wsURL)
        self._connect(wsURL)
        self.logger.info('Connected to Account WS.')


    #
    # Data Access methods
    #

    def get_assets(self):
        return self._curl_exchange(path='data/assets')

    def get_products(self):
        return self._curl_exchange(path='data/products')

    def get_position(self):
        return self._post('snapshots/positions/total')

    def get_orders(self):
        return self._post('snapshots/orders')

    def get_fills(self):
        return self._post('snapshots/fills')

    def get_positions_available(self):
        return self._post('snapshots/positions/available')

    def get_deposits(self):
        return self._post('snapshots/deposits')

    def get_withdrawals(self):
        return self._post('snapshots/withdrawals')

    def place(self, price, qty, symbol, side,
                        time_in_force = 'DAY', customer_order_ref = None,
                        type='limit', post_only= False):

        if customer_order_ref is None:
            customer_order_ref = str(random.randint(1,1000000000))
        order = {
            'price': str(price),
            'qty': str(qty),
            'symbol': symbol,
            'side': side,
            'time_in_force': time_in_force,
            'type': type,
            'post_only': post_only,
            'customer_order_ref' : customer_order_ref
        }
        return self._post('orders', postdict=order)

    def cancel(self, order_id, symbol):
        postdict = {
            "order_id": order_id,
            "symbol": symbol
        }
        return self._post('orders/cancel', postdict=postdict)

    #
    # Lifecycle methods
    #

    def error(self, err):
        self._error = err
        self.logger.error(err)
        self.exit()

    def exit(self):
        self.exited = True
        self.ws.close()

    #
    # Private methods
    #

    def _post(self, path, postdict={}):
        request_id = self.get_request_id()
        postdict["request_id"] = request_id
        request_response = self._curl_exchange(path=path,
                                               verb='POST', postdict=postdict)
        self._wait_for_response_to_request(request_id)
        ws_result = self._is_request_id_available(request_id)
        if not ws_result:
            self.logger.warning("Timed out requesting path %s. Request #: %s." % (path, request_id))
            raise Exception("Timed out requesting path %s. Request #: %s." % (path, request_id))
        else:
            # Response received.
            response = self.data[request_id]
            return response

    def get_request_id(self):
        return str(random.randint(1,1000000000))

    def _is_request_id_available(self, request_id):
        return request_id in self.data


    def _wait_for_response_to_request(self, request_id, seconds=1):
        ''' Waits for the websocket to receive a response to a request_id'''
        t_end = time.time() + seconds
        while time.time() < t_end:
            if self._is_request_id_available(request_id):
                return True
        self.logger.warning("Timed out on request: %s..." % request_id)
        return False

    def _on_message(self, ws, message):

        message = json.loads(message)
        has_no_request_id = ['ping', 'market_closed', 'market_open']
        if message['m'] in has_no_request_id:
            if message['m'] == 'market_closed' and self.open == True:
                self.logger.info("The Market has closed! Type is %s" % message['type'])

            if message['m'] == 'market_open':
                self.open = True
        else:
            self.logger.info(message)
            request_id = message['payload']['request_id']
            self.data[request_id] = message['payload']
        # Unhandled messages:
        # {'m': 'market_closed', 'type': '20'}
        # {'m': 'market_open', 'type': '18'}


    def _on_open(self, ws):
        self.logger.debug("Account Websocket Opened.")

    def _on_close(self, ws):
        self.logger.info('Account Websocket Closed')
        self.exit()

    def _on_error(self, ws, error):
        if not self.exited:
            self.error(error)

    def __get_auth(self):
        '''Return auth headers. Not currently authenticating so return empty.'''
        return []

    def __reset(self):
        self.data = {}
        self.keys = {}
        self.exited = False
        self._error = None
        remove_handlers = [self.logger.removeHandler(h) for h in self.logger.handlers]

    def _connect(self, wsURL):
        '''Connect to the websocket in a thread.'''
        self.logger.debug("Starting thread")

        ssl_defaults = ssl.get_default_verify_paths()
        sslopt_ca_certs = {'ca_certs': ssl_defaults.cafile}
        self.ws = websocket.WebSocketApp(wsURL,
                                         on_message=lambda ws, msg: self._on_message(ws, msg),
                                         on_close=  lambda ws: self._on_close(ws),
                                         on_open=   lambda ws: self._on_open(ws),
                                         on_error=  lambda ws, msg: self._on_error(ws, msg),
                                         header=self.__get_auth()
                                         )

        #self.wst = threading.Thread(target=lambda: self.ws.run_forever(sslopt=sslopt_ca_certs))
        self.wst = threading.Thread(target=lambda: self.ws.run_forever())
        self.wst.daemon = True
        self.wst.start()

        # Wait for connect before continuing
        conn_timeout = 5
        while (not self.ws.sock or not self.ws.sock.connected) and conn_timeout and not self._error:
            sleep(1)
            conn_timeout -= 1

        if not conn_timeout or self._error:
            self.logger.error("Couldn't connect to Account WS! Exiting.")
            self.exit()
            sys.exit(1)

    def _prep_auth(self):
        return AWS4Auth(self.key, self.secret, self.region, self.service)

    def _prep_session(self):
        # Prepare HTTPS session
        session = requests.Session()
        # These headers are always sent
        session.headers.update({'user-agent': 'liquidbot'})
        session.headers.update({'content-type': 'application/json'})
        session.headers.update({'accept': 'application/json'})
        return session


    def _curl_exchange(self, path, query=None, postdict=None, timeout=None,
                       verb=None, rethrow_errors=False, max_retries=None):
        '''Send a request to the exchange.'''
        # Handle URL
        url = self.base_url + path

        if timeout is None:
            timeout = self.timeout

        # Default to POST if data is attached, GET otherwise
        if not verb:
            verb = 'POST' if postdict else 'GET'

        # By default don't retry POST or PUT. Retrying GET/DELETE is okay because they are idempotent.
        if max_retries is None:
            max_retries = 0 if verb in ['POST', 'PUT'] else 3

        # Auth: API Key/Secret
        auth = self._prep_auth()

        def exit_or_throw(e):
            if rethrow_errors:
                raise e
            else:
                exit(1)

        def retry():
            self.retries += 1
            if self.retries > max_retries:
                raise Exception("Max retries on %s (%s) hit, raising." % (path, json.dumps(postdict or '')))
            return self._curl_exchange(path, query, postdict, timeout, verb, rethrow_errors, max_retries)

        # Make the request
        response = None
        try:
            self.logger.info("sending req to %s: %s" % (url, json.dumps(postdict or query or '')))
            req = requests.Request(verb, url, json=postdict, auth=auth, params=query)
            prepped = self.session.prepare_request(req)
            response = self.session.send(prepped, timeout=timeout)
            self.headers = response.headers
            # Make non-200s throw
            response.raise_for_status()

        except requests.exceptions.HTTPError as e:
            if response is None:
                raise e

            # 401 - Auth error. This is fatal.
            if response.status_code == 401:
                self.logger.error("API Key or Secret incorrect, please check and restart.")
                self.logger.error("Error: " + response.text)
                if postdict:
                    self.logger.error(postdict)
                # Always exit, even if rethrow_errors, because this is fatal
                sys.exit(1)

            # 404, can be thrown if order canceled or does not exist.
            elif response.status_code == 404:
                if verb == 'DELETE':
                    self.logger.error("Order not found: %s" % postdict['orderID'])
                    return
                self.logger.error("Unable to contact the Exchange API (404). " +
                                  "Request: %s \n %s" % (url, json.dumps(postdict)))
                exit_or_throw(e)

            # 429, ratelimit; cancel orders & wait until X-Ratelimit-Reset
            elif response.status_code == 429:
                self.logger.error("Ratelimited on current request. Sleeping, then trying again. Try fewer " +
                                  "order pairs or contact exchange to raise your limits. " +
                                  "Request: %s \n %s" % (url, json.dumps(postdict)))

                # Figure out how long we need to wait.
                ratelimit_reset = response.headers['X-Ratelimit-Reset']
                to_sleep = int(ratelimit_reset) - int(time.time())
                reset_str = datetime.datetime.fromtimestamp(int(ratelimit_reset)).strftime('%X')

                # We're ratelimited, and we may be waiting for a long time. Should Cancel orders.

                self.logger.error("Your ratelimit will reset at %s. Sleeping for %d seconds." % (reset_str, to_sleep))
                time.sleep(to_sleep)

                # Retry the request.
                return retry()

            # 503 - Exchange temporary downtime, likely due to a deploy. Try again
            elif response.status_code == 503:
                self.logger.warning("Unable to contact the Exchange API (503), retrying. " +
                                    "Request: %s \n %s" % (url, json.dumps(postdict)))
                time.sleep(3)
                return retry()

            elif response.status_code == 400:
                pass

            # If we haven't returned or re-raised yet, we get here.
            self.logger.error("Unhandled Error: %s: %s" % (e, response.text))
            self.logger.error("Endpoint was: %s %s: %s" % (verb, path, json.dumps(postdict)))
            exit_or_throw(e)

        except requests.exceptions.Timeout as e:
            # Timeout, re-run this request
            self.logger.warning("Timed out on request: %s (%s), retrying..." % (path, json.dumps(postdict or '')))
            return retry()

        except requests.exceptions.ConnectionError as e:
            self.logger.warning("Unable to contact the Exchange API (%s). Please check the URL. Retrying. " +
                                "Request: %s %s \n %s" % (e, url, json.dumps(postdict)))
            time.sleep(1)
            return retry()

            # Reset retry counter on success
        self.retries = 0

        return response.json()