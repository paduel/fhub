#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2020 Antonio Rodríguez García
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from datetime import datetime
from functools import wraps
from time import sleep as _sleep

import requests
from pandas import concat, json_normalize, \
    DataFrame, to_datetime, read_pickle
from pkg_resources import resource_filename

from .utils import FinnhubError
from .utils import _json_to_df_candle, _rename_quote, _check_resolution
from .utils import _normalize_indicator_schema
from .utils import _to_dataframe, _check_kind, _recursive
from .utils import _unixtime, _normalize_date, _to_time_cols


class Session:
    """
    Finnhub API client.  You need a valid API key from Finnhub.
    """
    BASE_URL = 'https://finnhub.io/api/v1/'
    available_metrics = [
        'price',
        'valuation',
        'growth',
        'margin',
        'management',
        'financialStrength',
        'perShare'
    ]
    _premium_msg = 'Premium Account Only. Please upgrade to help keep Finnhub free for everyone.'

    def __init__(
            self,
            key,
            proxies=None,
            verbose=False
    ):
        self.key = key
        self.verbose = verbose
        if proxies is not None:
            assert isinstance(proxies, dict)
        self.session = self._init__session()
        self.session.proxies = proxies
        self.ind_info = read_pickle(resource_filename('fhub', 'indicator_info.pkl'))

    @staticmethod
    def _init__session():
        session = requests.Session()
        session.headers.update({'Accept': 'application/json',
                                'User-Agent': 'finnhub/api'})
        return session

    def _request(self,
                 endpoint,
                 params=None):
        if params is None:
            params = {'token': self.key}
        else:
            params.update({'token': self.key})
        r = self.session.get(
            f"{self.BASE_URL}{endpoint}",
            params=params
        )
        if self.verbose:
            print(r.url)
            print(r.status_code)
            print(r.content)
        if r.ok:
            if r.text == self._premium_msg:
                raise Exception(self._premium_msg)
            else:
                return r.json()
        else:
            raise FinnhubError(r.content.decode("utf-8"))

# --------------------- Stock Fundamentals --------------------- #

    @_check_kind
    @_to_dataframe()
    def exchanges(self,
                  kind='stock'):
        """
        Get a list supported exchanges.
        :param kind: Kind of exchanges, default stock. Available: stock, forex, crypto.
        :return: dataframe with name, code and currency of exchanges.
        """
        _endpoint = f"{kind}/exchange"
        return self._request(_endpoint)

    @_check_kind
    @_to_dataframe()
    def symbols(self,
                exchange,
                kind='stock'):
        """
        Get a list supported symbols for a exchange.
        :param exchange: str, exchange to get the symbols.
        :param kind: str, Kind of the exchange, default stock. Available: stock, forex, crypto.
        :return: pandas dataframe, list of symbols with description and name.
        """
        _endpoint = f"{kind}/symbol"
        params = {
            'exchange': exchange
        }
        return self._request(_endpoint, params)

    @_to_dataframe()
    def profile(
            self,
            symbol=None,
            isin=None,
            cusip=None
    ):
        """NOT TESTED, premium needed"""
        _ticker = {
            'symbol': symbol,
            'isin': isin,
            'cusip': cusip
        }

        if not any(_ticker.values()):
            print('You must pass one of symbol, isin or cusip')
            return

        params = {k: v for k, v in _ticker.items() if v}
        if len(params) > 1:
            print('You must pass only one of symbol, isin or cusip')
            return

        _endpoint = f"news/profile"
        return self._request(_endpoint, params)

    def executive(
            self,
            symbol
    ):
        """
        Get a list of company's executives and members of the Board.
        :param symbol: str, symbol of the company.
        :return: pandas dataframe, list of company's executives.
        """
        _endpoint = 'stock/executive'
        params = {'symbol': symbol}

        _json = self._request(
            _endpoint,
            params
        )
        return json_normalize(
            _json,
            record_path='executive',
            meta='symbol',
        )

    @_to_dataframe()
    def news(self,
             category='general',
             minid=0):
        _endpoint = 'news'
        params = {
            'category': category,
            'minId': minid
        }
        return self._request(_endpoint, params)

    @_to_dataframe(_parse_dates=['datetime'])
    def company_news(
            self,
            symbol,
            start=None,
            end=None
    ):
        _endpoint = "company-news"
        params = {'symbol': symbol}
        if start is not None:
            params.update({'from': _normalize_date(start)})
        else:
            params.update({'from': "2019-01-01"})
        if end is not None:
            params.update({'to': _normalize_date(end)})

        return self._request(_endpoint, params)

    @_to_dataframe(_parse_dates=['datetime'])
    def major_development(
            self,
            symbol,
            start=None,
            end=None
    ):
        _endpoint = "major-development"
        params = {'symbol': symbol}
        if start is not None:
            params.update({'from': _normalize_date(start)})
        if end is not None:
            params.update({'to': _normalize_date(end)})

        return self._request(
            _endpoint,
            params
        )['majorDevelopment']

    @_recursive
    def sentiment(
            self,
            symbol
    ):
        _endpoint = 'news-sentiment'
        params = {'symbol': symbol}

        _json = self._request(
            _endpoint,
            params
        )
        return json_normalize(_json).T.rename(
            columns={0: _json['symbol']}
        )

    @_recursive
    def peers(
            self,
            symbol
    ):
        """
        Get company peers. Return a list of peers in the same country and GICS sub-industry
        :param symbol: symbol of the company
        :return: list of peers symbols
        """
        _endpoint = 'stock/peers'
        params = {'symbol': symbol}

        return self._request(
            _endpoint,
            params
        )

    @_recursive
    def metrics(
            self,
            symbol,
            metric='margin'
    ):

        _endpoint = 'stock/metric'
        params = {
            'symbol': symbol,
            'metric': metric
        }
        _json = self._request(
            _endpoint,
            params
        )
        _df = DataFrame.from_dict(_json['metric'], orient='index')
        _df.columns = [_json['symbol']]
        return _df

    @_recursive
    def all_metrics(
            self,
            symbol
    ):
        _metrics = {}
        for _metric in self.available_metrics:
            _metrics[_metric] = self.metrics(symbol, _metric)
            _sleep(0.1)
        return concat(_metrics)

    def investor_ownership(
            self,
            symbol,
            limit=None
    ):
        _endpoint = 'stock/investor-ownership'
        params = {'symbol': symbol}
        if limit is not None:
            params.update({'limit': limit})
        _json = self._request(
            _endpoint,
            params
        )
        _df = json_normalize(
            _json,
            record_path='ownership',
            meta='symbol',
        )
        return _df

    def fund_ownership(
            self,
            symbol,
            limit=None
    ):
        _endpoint = 'stock/fund-ownership'
        params = {'symbol': symbol}
        if limit is not None:
            params.update({'limit': limit})
        _json = self._request(
            _endpoint,
            params
        )
        _df = json_normalize(
            _json,
            record_path='ownership',
            meta='symbol',
        )
        return _df

    def ownership(
            self,
            symbol
    ):
        _invs = self.investor_ownership(symbol)
        _funds = self.fund_ownership(symbol)
        _invs['kind'] = 'INVESTOR'
        _funds['kind'] = 'FUND'
        return concat([_invs, _funds])

    # TODO  premium needed
    def financials(self,
                   symbol,
                   freq):
        _endpoint = "stock/financials"
        pass

    @_to_dataframe(_parse_dates=['date'],
                   _index=['date'])
    def calendar_ipo(self,
                     start=None,
                     end=None):
        """
        Get recent and coming IPO.
        :param start: str, from date, format "2020-12-31".
        :param end: str, to date,  format "2020-12-31".
        :return: pandas dataframe, calendar of recent and coming IPO
        """
        _endpoint = "calendar/ipo"
        if end is None:
            end = datetime.now().strftime("%Y-%m-%d")
        if start is None:
            start = '1900-01-01'
        params = {
            'from': _normalize_date(start),
            'to': _normalize_date(end)
        }
        return self._request(
            _endpoint,
            params
        )['ipoCalendar']

    @wraps(calendar_ipo)
    def ipos(self, *args, **kwargs):
        return self.calendar_ipo(*args, **kwargs)

# --------------------- Stock Analysts --------------------- #

    @_recursive
    def recommendation(
            self,
            symbol
    ):
        """
        Get latest analyst recommendation trends for a company.
        :param symbol: symbol of the company
        :return: dataframe with recommendations
        """
        _endpoint = 'stock/recommendation'
        params = {'symbol': symbol}

        _df = DataFrame(self._request(
            _endpoint,
            params
        ))

        _df['period'] = to_datetime(_df['period'])
        return _df.set_index('period')[['strongBuy', 'buy', 'hold', 'sell', 'strongSell']]

    @_recursive
    @_to_dataframe('serie')
    def price_target(
            self,
            symbol
    ):
        """
        Get latest price target consdf = pd.DataFrame(ensus.
        :param symbol: symbol of the company
        :return: dataframe with recommendations
        """
        _endpoint = 'stock/price-target'
        params = {'symbol': symbol}

        return self._request(
            _endpoint,
            params
        )

    @_recursive
    def upgrade_downgrade(
            self,
            symbol
    ):
        """
        Get latest stock upgrade and downgrade
        :param symbol: symbol of the company
        :return: dataframe with latest stock upgrades/downgrades
        """
        _endpoint = 'stock/upgrade-downgrade'
        params = {'symbol': symbol}
        _json = self._request(
            _endpoint,
            params
        )
        _df = DataFrame(_json)
        _df['gradeTime'] = to_datetime(_df['gradeTime'], unit='s')
        return _df

    # --------------------- Stock Price --------------------- #

    @_recursive
    @_to_dataframe(_type='serie')
    def quote(
            self,
            symbol
    ):
        _endpoint = 'quote'
        params = {'symbol': symbol}

        return _rename_quote(
            self._request(
                _endpoint,
                params
            )
        )

    @_recursive
    @_check_kind
    def candle(
            self,
            symbol,
            kind='stock',
            start=None,
            end=None,
            resolution='D',
            adjusted=True
    ):
        if not _check_resolution(resolution):
            return
        adjusted = 'true' if adjusted else 'false'
        if end is None:
            end = datetime.now().strftime("%Y-%m-%d")
        if start is None:
            start = '1900-01-01'

        params = {
            'symbol': symbol,
            'resolution': resolution,
            'from': _unixtime(start),
            'to': _unixtime(end)
        }

        if kind == 'stock':
            params.update({'adjusted': adjusted})
        _endpoint = f'{kind}/candle'
        _json = self._request(
            _endpoint,
            params
        )
        if self.verbose:
            print(_json)
        if _json is None:
            return None
        else:
            if _json['s'] == 'no_data':
                print(f"{params['symbol']} :  Data no available.")
                return None
            else:
                df = _json_to_df_candle(_json)
                return df

    # --------------------- Alternative Data --------------------- #

    @_to_dataframe(_parse_dates=['updated'])
    def covid19(self):
        """
        Get real-time updates on the number of COVID-19 (Corona virus) cases in the US with a state-by-state breakdown.
        Data is sourced from CDC and reputable sources.
        :return: pandas dataframe, COVID-19 data
        """
        _endpoint = 'covid19/us'
        return self._request(_endpoint)

    # --------------------- Economic --------------------- #

    @_to_dataframe()
    def economic_code(self):
        """
        List codes of supported economic data.
        :return: pandas dataframe, list of codes
        """
        _endpoint = "economic/code"
        return self._request(_endpoint)

    @_to_dataframe(_parse_dates=['date'])
    def economic(
            self,
            economic_code,
            get_unit=False
    ):
        """
        Get economic data.
        :param economic_code: Finnhub code for economic data
        :param get_unit: use unit of data as column name
        :return: pandas dataframe with economic data
        """
        _endpoint = "economic"
        params = {
            'code': economic_code
        }

        _json = self._request(
            _endpoint,
            params
        )
        _df = DataFrame(_json)
        _codes = self.economic_code()
        _unit = 'value'
        if get_unit:
            _unit = _codes.set_index('code').loc[economic_code, 'unit']
        _df.columns = ['date', _unit]
        _df = _df.set_index('date')
        _df.index = to_datetime(_df.index)
        return _df

    @_to_dataframe(_parse_dates=['date'])
    def economic_calendar(self):
        """
        Get recent and coming economic releases.
        :return: pandas dataframe with economic calendar
        """
        _endpoint = 'calendar/economic'
        return self._request(_endpoint)['economicCalendar']['result']

    # --------------------- Technical analysis --------------------- #

    def indicator_info(self, indicator):
        print('\n'.join([k + ": " + v
                         for k, v in self.ind_info.loc[indicator].to_dict().items()]))

    @_recursive
    @_check_kind
    def indicator(
            self,
            symbol,
            start=None,
            end=None,
            resolution='D',
            indicator='sma',
            indicator_fields=None,
            only_indicator=False
    ):
        if not _check_resolution(resolution):
            return
        if end is None:
            end = datetime.now().strftime("%Y-%m-%d")
        if start is None:
            start = '1900-01-01'

        params = {
            'symbol': symbol,
            'resolution': resolution,
            'from': _unixtime(start),
            'to': _unixtime(end),
            'indicator': indicator
        }

        if indicator_fields is not None:
            if not isinstance(indicator_fields, dict):
                raise Exception('Dictionary with fields names and values must be passed')
            else:
                params.update(indicator_fields)
        _endpoint = f'indicator'
        _json = self._request(
            _endpoint,
            params
        )
        if self.verbose:
            print(_json)
        if _json is None:
            return None
        else:
            if _json['s'] == 'no_data':
                print(f"{params['symbol']} :  Data no available.")
                return None
            else:
                df = _json_to_df_candle(_json)
                df = df[df.abs().cumsum() > 0]
                if only_indicator:
                    df = df.drop(['close', 'high', 'low', 'open', 'volume'], axis=1)
                return df

    def indicators_bulk(self,
                        symbol,
                        start=None,
                        end=None,
                        resolution='D',
                        indicators_schema=None,
                        ):
        if not _check_resolution(resolution):
            return
        data = {}
        only_indicator = False
        indicators_schema = _normalize_indicator_schema(indicators_schema)
        for indicator_name, indicator_params in indicators_schema.items():
            indicator, params = indicator_params
            name = indicator_name if only_indicator else 'price'
            data[name] = self.indicator(symbol,
                                        start=start,
                                        end=end,
                                        resolution=resolution,
                                        indicator=indicator,
                                        indicator_fields=params,
                                        only_indicator=only_indicator)
            if not only_indicator:
                price_cols = ['close', 'high', 'low', 'open', 'volume']
                data[indicator_name] = data[name].drop(price_cols, axis=1)
                data[name] = data[name][price_cols]
                only_indicator = True
        return concat(data, axis=1)

    @_recursive
    def pattern(self,
                symbol,
                resolution='D'):
        """
        Run pattern recognition algorithm on symbols. Support double top/bottom, triple top/bottom, head and shoulders, triangle, wedge, channel, flag, and candlestick patterns.
        :param symbol: symbol or list of symbols
        :param resolution: Supported resolution includes 1, 5, 15, 30, 60, D, W, M .Some timeframes might not be available depending on the exchange.
        :return: dataframe of patterns
        """
        if not _check_resolution(resolution):
            return
        endpoint = 'scan/pattern'
        params = dict(
            symbol=symbol,
            resolution=resolution
        )
        _json = self._request(endpoint, params)
        return _to_time_cols(DataFrame(_json['points'])).T

    @_recursive
    @_to_dataframe('serie')
    def support_resistance(self,
                           symbol,
                           resolution='D'):
        """
        Get support and resistance levels for symbols.
        :param symbol: symbol or list of symbols
        :param resolution: Supported resolution includes 1, 5, 15, 30, 60, D, W, M .Some timeframes might not be available depending on the exchange.
        :return: dataframe of support and resistance levels
        """
        if not _check_resolution(resolution):
            return
        endpoint = 'scan/support-resistance'
        params = dict(
            symbol=symbol,
            resolution=resolution
        )
        return self._request(endpoint, params)['levels']

    @_recursive
    def technical_indicator(self,
                            symbol,
                            resolution='D'):
        """
        Get aggregate signal of multiple technical indicators such as MACD, RSI, Moving Average v.v.
        :param symbol: symbol or list of symbols
        :param resolution: Supported resolution includes 1, 5, 15, 30, 60, D, W, M .Some timeframes might not be available depending on the exchange.
        :return: dataframe of signals
        """
        if not _check_resolution(resolution):
            return
        endpoint = 'scan/technical-indicator'
        params = dict(
            symbol=symbol,
            resolution=resolution
        )
        _json = self._request(endpoint, params)
        return json_normalize(_json).T.rename(columns={0: symbol})
