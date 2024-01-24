#!/usr/bin/env python3
# Copyright 2015-2024 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

from setuptools import find_packages, setup

REQUIREMENTS = [
    'requests==2.25.1',
    'stevedore==3.2.2',
]

setup(
    name='wazo_lib_rest_client',
    version='0.2',
    description='a simple library to instantiate REST clients',
    author='Wazo Authors',
    author_email='dev.wazo@gmail.com',
    url='http://wazo.community',
    packages=find_packages(),
    install_requires=REQUIREMENTS,
    entry_points={
        'test_rest_client.commands': [
            'example = wazo_lib_rest_client.example_cmd:ExampleCommand',
        ],
    },
)
