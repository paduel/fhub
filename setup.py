#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#
# A pythonic way to use the Finnanhub data API.
# https://github.com/paduel/fhub


from setuptools import setup
from os import path

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='fhub',
    version='0.4.1',
    packages=['fhub'],
    url='https://github.com/paduel/fhub',
    license='Apache 2.0',
    author='Paduel',
    author_email='paduel@gmail.com',
    description='Python client for Finnhub API ',
    long_description=long_description,
    long_description_content_type='text/x-rst'
)
