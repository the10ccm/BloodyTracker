# -*- coding: utf-8 -*-

import re
from setuptools import setup

from bloodytracker.contrib import __version__


setup(
    name="bloodytracker",
    packages=["bloodytracker"],
    entry_points={
        "console_scripts": ['bloodytracker = bloodytracker.bloodytracker:run']
        },
    license='BSD',
    version=__version__,
    description="BloodyTracker is a console time tracker.",
    long_description='',
    author="Andrey Aleksandrov",
    author_email="the10ccm@googlemail.com",
    url="https://github.com/the10ccm/BloodyTracker",
    install_requires=[
        'mock==2.0.0',
        'tabulate==0.7.7',
        'future==0.16.0'
        ]
    )
