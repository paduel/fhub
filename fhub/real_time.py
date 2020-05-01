import inspect
import json
import ssl
import sys
import threading
import types
from datetime import datetime
from time import sleep

import websocket
from pandas import DataFrame


class Ticker:
    def __init__(self,
                 symbol,
                 max_history=1000):
        """
        Ticker object for a symbol data subscription.
        :param symbol: string : Finnhub symbol.
        :param max_history: integer : maximum number of ticks to saved.
        """
        self.symbol = symbol
        self.last = {}
        self.price = None
        self.volume = None
        self.datetime = None
        self.max_history = max_history
        self.history = DataFrame(columns=['price', 'volume', 'datetime'])

    def set_last_trade(self, info):
        for _key, _value in info.items():
            setattr(self, _key, _value)

    def __repr__(self):
        return f'fhub ticker({self.symbol})'

    def __str__(self):
        return f'Ticker(symbol: {self.symbol}, ' \
               f'last price: {self.price}, last datetime{self.datetime}, ' \
               f'last volume{self.volume}, history records: {self.history.shape[0]})'


class Subscription:
    """Stream real-time trades for US stocks, forex and crypto."""

    def __init__(self, key):
        self.key = key
        self.data = None
        self.ws_url = f"wss://ws.finnhub.io?token={self.key}"
        self.on_tick = None
        self.tickers = None
        self.max_history = 0
        self.timeout = 5
        self._cols = {'s': 'symbol', 'p': 'price', 't': 'datetime', 'v': 'volume'}
        self.ws = None
        self.wst = None

    def connect(self,
                symbols,
                on_tick=None,
                max_history=1000,
                timeout=5,
                enable_trace=False):
        """
        Conect to Finnhub websocket server for a list of symbols
        :param symbols: list : list of Finhhub symbols of assets to subscribe
        :param on_tick: function : callback when new tick is received.
        :param max_history: integer : maximum number of ticks to save for each symbol, 0 for no save history. Default 1000.
        :param timeout: integer : timeout for websocket conexion. Default 5.
        :param enable_trace: boolean : True for enable websocket connection trace. Deafult False.
        :return: a websocket connection to Finnhub.
        """
        print("Starting connexion")
        self.max_history = max_history
        self.tickers = {}
        for _symbol in symbols:
            self.tickers[_symbol] = Ticker(_symbol, self.max_history)
        self.timeout = timeout
        if isinstance(on_tick, types.FunctionType):
            self.on_tick = on_tick
        if enable_trace:
            websocket.enableTrace(True)
        else:
            websocket.enableTrace(False)
        ssl_defaults = ssl.get_default_verify_paths()
        sslopt_ca_certs = {"ca_certs": ssl_defaults.cafile}

        self.ws = websocket.WebSocketApp(self.ws_url,
                                         on_message=self.__on_message,
                                         on_close=self.__on_close,
                                         on_open=self.__on_open,
                                         on_error=self.__on_error,
                                         )
        self.wst = threading.Thread(
            target=lambda: self.ws.run_forever(sslopt=sslopt_ca_certs))
        self.wst.daemon = True
        self.wst.start()
        _timeout = self.timeout
        while (not self.ws.sock or not self.ws.sock.connected) and _timeout:
            sleep(1)
            _timeout -= 1
        if not _timeout:
            print("Not possible connect to Finnhub, closing.")
            sys.exit(1)

    def _callback(self, callback, *args):
        if callback:
            try:
                if inspect.ismethod(callback):
                    callback(*args)
                else:
                    callback(self, *args)
            except:
                pass

    def __on_message(self, msg):
        # print(msg)
        _json = json.loads(msg)
        if _json['type'] == 'trade':
            self._feeder(_json)
        elif _json['type'] == 'error':
            print(f"Finnhub error : {_json['msg']}")

    def __on_open(self):
        for _symbol in self.tickers.keys():
            self.ws.send('{"type":"subscribe","symbol": "' + _symbol + '"}')
        print("Subscription started")

    def __on_close(self):
        print("Subscription closed")

    def __on_error(self, error):
        print(f"Error {error}")

    def close(self):
        self.ws.close()

    def _feeder(self, _json):
        if 'data' in _json.keys():
            for _data in _json['data']:
                _info = self._to_dict(_data)
                _symbol = _info.pop('symbol')
                if self.max_history > 0:
                    _info['history'] = self.tickers[_symbol].history.append(
                        _info, ignore_index=True).tail(self.tickers[_symbol].max_history)
                self.tickers[_symbol].set_last_trade(_info)
                if self.on_tick:
                    self.on_tick(self.tickers[_symbol])

    def _to_dict(self, _data):
        return {self._cols[k]: datetime.fromtimestamp(
            v / 1000) if k == 't' else v for k, v in
                _data.items()}
