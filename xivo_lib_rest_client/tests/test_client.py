# -*- coding: utf-8 -*-

# Copyright (C) 2014-2016 Avencall
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

import os
import time
import requests
import subprocess
import unittest

from hamcrest import assert_that
from hamcrest import close_to
from hamcrest import contains_string
from hamcrest import equal_to
from hamcrest import ends_with
from hamcrest import has_entry
from mock import patch, ANY
from requests.exceptions import Timeout

from ..client import BaseClient, logger


class Client(BaseClient):

    namespace = 'test_rest_client.commands'

    def __init__(self,
                 host='localhost',
                 port=1234,
                 version='1.1',
                 username=None,
                 password=None,
                 https=False,
                 verify_certificate=False,
                 **kwargs):
        super(Client, self).__init__(host=host,
                                     port=port,
                                     version=version,
                                     https=https,
                                     verify_certificate=verify_certificate,
                                     **kwargs)
        self.username = username
        self.password = password

    def session(self):
        session = super(Client, self).session()
        if self.username and self.password:
            session.auth = requests.auth.HTTPDigestAuth(self.username, self.password)
        return session


class TestLiveClient(unittest.TestCase):

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


class TestBaseClient(unittest.TestCase):

    def new_client(self,
                   host=None,
                   port=None,
                   version=None,
                   username=None,
                   password=None,
                   https=None,
                   timeout=None,
                   verify_certificate=None,
                   token=None,
                   **kwargs):
        return Client(host=host,
                      port=port,
                      version=version,
                      username=username,
                      password=password,
                      https=https,
                      timeout=timeout,
                      verify_certificate=verify_certificate,
                      token=token,
                      **kwargs)

    @patch.object(logger, 'info')
    def test_that_extra_kwargs_are_ignored(self, logger_info):
        self.new_client(patate=True)

        logger_info.assert_called_once_with(ANY, 'Client', {'patate': True})

    def test_given_no_https_then_http_used(self):
        client = self.new_client(https=False)

        assert_that(client.url(), contains_string('http://'))

    def test_given_https_then_https_used(self):
        client = self.new_client(https=True)

        assert_that(client.url(), contains_string('https://'))

    @patch('xivo_lib_rest_client.client.disable_warnings')
    def test_given_https_then_warnings_are_disabled(self, disable_warnings):
        client = self.new_client(https=True)

        client.session()

        disable_warnings.assert_called_once_with()

    def test_given_connection_parameters_then_url_built(self):
        client = self.new_client(host='myhost', port=1234, version='1.234',
                                 https=True)

        assert_that(client.url(), equal_to('https://myhost:1234/1.234'))

    def test_given_resource_then_resource_name_is_in_url(self):
        client = self.new_client()

        assert_that(client.url('resource'), ends_with('/resource'))

    def test_given_username_and_password_then_session_authenticated(self):
        client = self.new_client(username='username', password='password')
        session = client.session()

        assert_that(session.auth.username, equal_to('username'))
        assert_that(session.auth.password, equal_to('password'))

    def test_timeout(self):
        client = self.new_client(timeout=1)

        session = client.session()

        try:
            start = time.time()
            session.get('http://169.254.0.1')
        except Timeout:
            assert_that(time.time() - start, close_to(1.0, 0.9))
        except KeyboardInterrupt:
            self.fail('Should have timedout after 1 second')
        else:
            self.fail('Should have timedout after 1 second')

    def test_token(self):
        token = 'the-one-ring'
        client = self.new_client(token=token)

        session = client.session()

        assert_that(session.headers, has_entry('X-Auth-Token', token))
