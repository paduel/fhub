#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#
# A pythonic way to use the Finnanhub data API.
# https://github.com/paduel/fhub


from os import path

from setuptools import setup

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='fhub',
    version='0.0.13',
    packages=['fhub'],
    include_package_data=True,
    url='https://github.com/paduel/fhub',
    license='Apache 2.0',
    author='Paduel',
    author_email='paduel@gmail.com',
    description='Python client for Finnhub API ',
    long_description=long_description,
    long_description_content_type='text/x-rst',
    classifiers=[
        'License :: OSI Approved :: Apache Software License',
        'Development Status :: 3 - Alpha',
        # 'Development Status :: 4 - Beta',
        #'Development Status :: 5 - Production/Stable',
        'Operating System :: OS Independent',
        'Intended Audience :: Developers',
        'Topic :: Office/Business :: Financial',
        'Topic :: Office/Business :: Financial :: Investment',
        'Topic :: Scientific/Engineering :: Interface Engine/Protocol Translator',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',

        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ]
)
