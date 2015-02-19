# -*- coding: utf-8 -*-

# Copyright (C) 2014-2015 Avencall
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
from hamcrest import contains_string
from hamcrest import ends_with
from ..client import make_client
from ..client import _SessionBuilder

Client = make_client('test_rest_client.commands')


class TestClient(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        os.chdir(os.path.dirname(__file__))
        cmd = ['python', 'server/run.py']
        cls._server = subprocess.Popen(cmd)
        time.sleep(1)

    @classmethod
    def tearDownClass(cls):
        cls._server.terminate()

    def test_client_method_mapping(self):
        c = Client('localhost', 8000, '42', https=False)

        result = c.example.test()

        assert_that(result, equal_to('''{"foo": "bar"}'''))

    def test_client_command_with_call(self):
        c = Client('localhost', 8000, '42', https=False)

        result = c.example()

        assert_that(result, equal_to('''{"foo": "bar"}'''))

    def test_client_command_after_session_expiry(self):
        c = Client('localhost', 8000, 'auth/42',
                   username='username', password='password', https=False)

        result = c.example()
        assert_that(result, equal_to('''{"foo": "bar"}'''))

        time.sleep(2)

        result = c.example()
        assert_that(result, equal_to('''{"foo": "bar"}'''))


class TestSessionBuilder(unittest.TestCase):

    def test_given_no_https_then_http_used(self):
        builder = _SessionBuilder(https=False)

        assert_that(builder.url(), contains_string('http://'))

    def test_given_https_then_https_used(self):
        builder = _SessionBuilder(https=True)

        assert_that(builder.url(), contains_string('https://'))

    def test_given_connection_parameters_then_url_built(self):
        builder = _SessionBuilder(host='myhost', port=1234, version='1.234',
                                  https=True)

        assert_that(builder.url(), equal_to('https://myhost:1234/1.234/'))

    def test_given_resource_then_resource_name_is_in_url(self):
        builder = _SessionBuilder()

        assert_that(builder.url('resource'), ends_with('/resource'))

    def test_given_username_and_password_then_session_authenticated(self):
        builder = _SessionBuilder(username='username', password='password')
        session = builder.session()

        assert_that(session.auth.username, equal_to('username'))
        assert_that(session.auth.password, equal_to('password'))
        assert_that(session.verify, equal_to(False))
