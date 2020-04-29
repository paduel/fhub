====
Fhub
====
Python client for Finnhub API
=============================
.. image:: https://img.shields.io/pypi/v/fhub?color=blue
    :target: https://pypi.org/project/fhub/
    :alt: PyPi version

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


Documentation
~~~~~~~~~~~~~

Official documentation of the API REST of Finnhub:

https://finnhub.io/docs/api

Only some of the functions available in the REST API have been implemented yet.
    