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

from pandas import DataFrame, Series
from pandas import to_datetime, concat
from functools import wraps
from datetime import datetime


class Error(Exception):
    """Base class for exceptions in this module."""
    pass


class FinnhubError(Error):
    def __init__(self, message):
        self.message = message


available_kind = [
    'stock',
    'forex',
    'economic',
    'crypto',
    'indices'
]

names_dict = {
    'c': 'close',
    'h': 'high',
    'l': 'low',
    'o': 'open',
    'v': 'volume',
    'pc': 'previous_close',
    't': 'datetime'
}


def _check_resolution(resolution):
    if not str(resolution).upper() in [
        "1", "5", "15", "30", "60",
        "D", "W", "M"
    ]:
        print('Resolution must be one of 1, 5, 15, 30, 60, D, W, M')
        return False
    else:
        return True


def _rename_candle_columns(df):
    return df.rename(columns=names_dict)


def _rename_quote(quotes):
    quotes['t'] = to_datetime(quotes['t'], unit='s')
    return {names_dict[k]: v for k, v in quotes.items()}


def _json_to_df_candle(
        _json
):
    df = DataFrame(_json)
    df = df.set_index(
        to_datetime(df['t'], unit='s'),
    )
    df = df.drop(['t', 's'], axis=1)
    df = _rename_candle_columns(df)
    df.index.name = 'datetime'
    return df


# Decorator to convert json to dataframe
def _to_dataframe(_type='dataframe',
                  _parse_dates=None,
                  _index=None):
    def inner_function(func):
        @wraps(func)
        def helper(clase, *args, **kwargs):
            if _type == 'dataframe':
                _df = DataFrame(func(clase, *args, **kwargs))
                if list(_df.columns) == [0]:
                    _df.columns = [args[0]]
                if _parse_dates is not None:
                    for _col in _parse_dates:
                        try:
                            _df[_col] = to_datetime(_df[_col])
                        except :
                            print(f'Not possible parse dates of {_col}')
                            pass
                if _index is not None:
                    _df = _df.set_index(_index)
            elif _type == 'serie':
                _df = Series(func(clase, *args, **kwargs)).to_frame(args[0])
            else:
                _df = None
            return _df
        return helper
    return inner_function


# Decorator to check kind is right
def _check_kind(func):
    @wraps(func)
    def helper(clase, *args, **kwargs):
        if 'kind' in kwargs.keys():
            if not kwargs['kind'] in available_kind:
                print(f"Kind {kwargs['kind']} not available")
                return
        return func(clase, *args, **kwargs)
    return helper


# Decorator to accept one symbol or a list of symbols
def _recursive(func):
    @wraps(func)
    def helper(clase, *args, **kwargs):
        if isinstance(args[0], str):
            return func(clase, *args, **kwargs)
        elif isinstance(args[0], list):
            _dfs = {}
            for n in args[0]:
                _dfs[n] = func(clase, n, **kwargs)
            if isinstance(_dfs[n], DataFrame):
                _df = concat(_dfs, axis=1).swaplevel(0, 1, 1).sort_index(axis=1)
                if _df.columns.nlevels == 2:
                    if all(_df.columns.get_level_values(0) == _df.columns.get_level_values(1)):
                        _df = _df.droplevel(0, 1)
                return _df
            else:
                return _dfs
    return helper


def _normalize_date(date):
    assert isinstance(date, str)
    return date.replace('/', '-').replace('.', '-').replace(' ', '-')

def _unixtime(date):
    assert isinstance(date, str)
    return datetime.strptime(_normalize_date(date), "%Y-%m-%d").strftime("%s")