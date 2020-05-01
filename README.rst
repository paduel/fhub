====
Fhub
====
Python client for Finnhub API
=============================
.. image:: https://img.shields.io/pypi/pyversions/fhub?color=g
    :target: https://pypi.org/project/fhub/
    :alt: Python version
.. image:: https://img.shields.io/pypi/v/fhub?color=blue
    :target: https://pypi.org/project/fhub/
    :alt: PyPi version
.. image:: https://img.shields.io/github/license/paduel/fhub?color=orange
    :target: https://pypi.org/project/fhub/
    :alt: License Apache 2.0
.. image:: https://img.shields.io/pypi/status/fhub?color=purple
    :target: https://pypi.org/project/fhub/
    :alt: Status
.. image:: https://img.shields.io/badge/contributions-welcome-yellowgreen
    :target: https://pypi.org/project/fhub/
    :alt: contributions welcome

\
A pythonic way to use the Finnanhub data API.

This package is still in a very early stage of development, so it is still incomplete and may contain bugs. It should only be used to test its functionality.
\

Installation
~~~~~~~~~~~~


 .. code:: bash

   pip install fhub


Quick start
~~~~~~~~~~~

You need a Finnhub API Key, you can get free one, at https://finnhub.io.  

.. code:: python

    from fhub import Session
    hub = Session(<your API Key here>)
    
    # Download prices time serie of Tesla.
    tsla = hub.candle('TSLA')
   
    # Download prices for several tickers from a date.
    data = hub.candle(['AMZN', 'NFLX', 'DIS'], start="2018-01-01")


Real-time subscription via Finnhub's websocket is easy using fhub, even using custom functions for each tick received.

.. code:: python

    from fhub.real_time import Subscription
    from time import sleep

    def price_monitor(ticker):
        # Callback function receive a ticker object
        # calculate the average of the last 30 ticks using the ticker history
        average = ticker.history.price.tail(30).mean().round(2)
        # display the price and the calculated average
        print (f'{ticker.symbol}. Price: {ticker.price} Average(30) : {average}')
        # show a message if price is over its average
        if ticker.price > average:
            print(f'{ticker.symbol} is over its average price')
        return

    # Create a subscription and connect
    subs = Subscription()
    # A list of the symbols to which to subscribe is passed
    # Created function  is assigned as a callback when a new tick is received
    subs.connect(["BINANCE:BTCUSDT", "IC MARKETS:1", "AAPL"],
                 on_tick=price_monitor
                )

    # The subscription is maintained for 20 seconds and then closed.
    for f in range(120):
        sleep(1)
    subs.close()


See more examples of use at quick_start_ notebook

.. _quick_start: https://github.com/paduel/fhub/blob/master/examples/quick_start.ipynb


Documentation
~~~~~~~~~~~~~

Official documentation of the API REST of Finnhub:

https://finnhub.io/docs/api

Only some of the functions available in the REST API have been implemented yet.
    