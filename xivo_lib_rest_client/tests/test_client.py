# -*- coding: utf-8 -*-

# Copyright (C) 2014 Avencall
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>

import subprocess
import unittest
import os
import time

from hamcrest import assert_that
from hamcrest import equal_to
from ..client import make_client

Client = make_client('test_rest_client.commands')


class TestClient(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        os.chdir(os.path.dirname(__file__))
        cmd = ['python', '-m', 'SimpleHTTPServer']
        cls._server = subprocess.Popen(cmd)
        time.sleep(1)

    @classmethod
    def tearDownClass(cls):
        cls._server.terminate()

    def test_client_method_mapping(self):
        c = Client('localhost', 8000, '42')

        result = c.example.test()

        assert_that(result, equal_to('''{"foo": "bar"}'''))

    def test_client_command_with_call(self):
        c = Client('localhost', 8000, '42')

        result = c.example()

        assert_that(result, equal_to('''{"foo": "bar"}'''))
