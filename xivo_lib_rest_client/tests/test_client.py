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
from hamcrest import close_to
from hamcrest import equal_to
from hamcrest import contains_string
from hamcrest import ends_with
from requests.exceptions import Timeout
from ..client import new_client_factory
from ..client import _SessionBuilder

Client = new_client_factory('test_rest_client.commands', 1234, '1.1', auth_method='digest')


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

    def new_session_builder(self, host=None, port=None, version=None,
                            username=None, password=None, https=None, timeout=None,
                            auth_method=None):
        return _SessionBuilder(host, port, version, username, password, https, timeout, auth_method)

    def test_given_no_https_then_http_used(self):
        builder = self.new_session_builder(https=False)

        assert_that(builder.url(), contains_string('http://'))

    def test_given_https_then_https_used(self):
        builder = self.new_session_builder(https=True)

        assert_that(builder.url(), contains_string('https://'))

    def test_given_connection_parameters_then_url_built(self):
        builder = self.new_session_builder(host='myhost', port=1234, version='1.234',
                                           https=True)

        assert_that(builder.url(), equal_to('https://myhost:1234/1.234/'))

    def test_given_resource_then_resource_name_is_in_url(self):
        builder = self.new_session_builder()

        assert_that(builder.url('resource'), ends_with('/resource'))

    def test_given_username_and_password_then_session_authenticated(self):
        builder = self.new_session_builder(username='username', password='password', auth_method='digest')
        session = builder.session()

        assert_that(session.auth.username, equal_to('username'))
        assert_that(session.auth.password, equal_to('password'))

    def test_timeout(self):
        builder = self.new_session_builder(timeout=1)

        session = builder.session()

        try:
            start = time.time()
            session.get('http://169.0.0.1')
        except Timeout:
            assert_that(time.time() - start, close_to(1.0, 0.9))
        except KeyboardInterrupt:
            self.fail('Should have timedout after 1 second')
        else:
            self.fail('Should have timedout after 1 second')
