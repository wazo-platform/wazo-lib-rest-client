# Copyright 2014-2023 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+
from __future__ import annotations

import os
import time
import subprocess
import unittest

from hamcrest import (
    assert_that,
    close_to,
    contains_string,
    equal_to,
    ends_with,
    has_entry,
    is_,
)
from unittest.mock import (
    ANY,
    Mock,
    patch,
)
import requests
from requests import Session
from requests.exceptions import (
    HTTPError,
    RequestException,
    Timeout,
)

from ..client import (
    BaseClient,
    logger,
)
from ..example_cmd import ExampleCommand


class Client(BaseClient):

    namespace = 'test_rest_client.commands'
    example: ExampleCommand

    def __init__(
        self,
        host='localhost',
        port=1234,
        version='1.1',
        username=None,
        password=None,
        https=False,
        verify_certificate=False,
        **kwargs,
    ):
        super().__init__(
            host=host,
            port=port,
            version=version,
            https=https,
            verify_certificate=verify_certificate,
            **kwargs,
        )
        self.username = username
        self.password = password

    def session(self) -> Session:
        session = super().session()
        if self.username and self.password:
            session.auth = requests.auth.HTTPDigestAuth(self.username, self.password)
        return session


class MockSessionClient(BaseClient):

    namespace = 'some-namespace'

    def __init__(self, session: Session) -> None:
        super().__init__('localhost', 1234)
        self._session = session

    def session(self) -> Session:
        return self._session


class TestLiveClient(unittest.TestCase):
    _server: subprocess.Popen

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

        assert_that(result, equal_to(b'''{"foo": "bar"}'''))

    def test_client_command_with_call(self):
        c = Client('localhost', 8000, '42', https=False)

        result = c.example()

        assert_that(result, equal_to(b'''{"foo": "bar"}'''))

    def test_client_command_after_session_expiry(self):
        assert_that(self._server.returncode, equal_to(None), 'server should be running')

        c = Client(
            'localhost',
            8000,
            'auth/42',
            username='username',
            password='password',
            https=False,
        )

        result = c.example()
        assert_that(result, equal_to(b'''{"foo": "bar"}'''))

        time.sleep(2)

        result = c.example()
        assert_that(result, equal_to(b'''{"foo": "bar"}'''))


class TestBaseClient(unittest.TestCase):
    def new_client(
        self,
        host='localhost',
        port=None,
        version=None,
        username=None,
        password=None,
        https=None,
        timeout=None,
        verify_certificate=None,
        token=None,
        **kwargs,
    ):
        return Client(
            host=host,
            port=port,
            version=version,
            username=username,
            password=password,
            https=https,
            timeout=timeout,
            verify_certificate=verify_certificate,
            token=token,
            **kwargs,
        )

    @patch.object(logger, 'debug')
    def test_that_extra_kwargs_are_ignored(self, logger_debug):
        self.new_client(patate=True)

        logger_debug.assert_called_once_with(ANY, 'Client', ['patate'])

    def test_given_no_https_then_http_used(self):
        client = self.new_client(https=False)

        assert_that(client.url(), contains_string('http://'))

    def test_given_https_then_https_used(self):
        client = self.new_client(https=True)

        assert_that(client.url(), contains_string('https://'))

    @patch('wazo_lib_rest_client.client.disable_warnings')
    def test_given_https_then_warnings_are_disabled(self, disable_warnings):
        client = self.new_client(https=True)

        client.session()

        disable_warnings.assert_called_once_with()

    def test_given_connection_parameters_then_url_built(self):
        client = self.new_client(host='myhost', port=1234, version='1.234', https=True)

        assert_that(client.url(), equal_to('https://myhost:1234/1.234'))

    def test_given_prefix_then_prefix_used(self):
        client = self.new_client(host='myhost', port=80, prefix='/api', version='1.0')

        assert_that(client.url(), contains_string('myhost:80/api/1.0'))

    def test_given_prefix_with_missing_leading_slash_then_prefix_used(self):
        client = self.new_client(host='myhost', port=80, prefix='api', version='1.0')

        assert_that(client.url(), contains_string('myhost:80/api/1.0'))

    def test_given_no_port_then_url_do_not_contains_double_dot(self):
        client = self.new_client(host='myhost', port=None, prefix='', version='')

        assert_that(client.url(), contains_string('myhost'))

    def test_given_no_version_then_prefix_do_not_end_with_slash(self):
        client = self.new_client(host='myhost', port=80, prefix='api', version='')

        assert_that(client.url(), contains_string('myhost:80/api'))

    def test_given_no_version_and_no_prefix_then_port_do_not_end_with_slash(self):
        client = self.new_client(host='myhost', port=80, prefix='', version='')

        assert_that(client.url(), contains_string('myhost:80'))

    def test_given_version_and_no_prefix_then_version_do_not_start_with_double_slash(
        self,
    ):
        client = self.new_client(host='myhost', port=80, prefix='', version='0.1')

        assert_that(client.url(), contains_string('myhost:80/0.1'))

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
            self.fail('Should have timeout after 1 second')
        else:
            self.fail('Should have timeout after 1 second')

    def test_token(self):
        token_id = 'the-one-ring'
        client = self.new_client(token=token_id)

        session = client.session()

        assert_that(session.headers, has_entry('X-Auth-Token', token_id))

    def test_set_token(self):
        token_id = 'the-one-ring'
        client = self.new_client()

        client.set_token(token_id)

        session = client.session()
        assert_that(session.headers, has_entry('X-Auth-Token', token_id))

    def test_tenant_param(self):
        tenant_id = 'my-tenant'
        client = self.new_client(tenant=tenant_id)

        session = client.session()
        assert_that(session.headers, has_entry('Wazo-Tenant', tenant_id))

    def test_set_tenant(self):
        tenant_id = 'my-tenant'
        client = self.new_client()

        client.set_tenant(tenant_id)

        session = client.session()
        assert_that(session.headers, has_entry('Wazo-Tenant', tenant_id))

    def test_tenant(self):
        tenant_id = 'my-tenant'
        client = self.new_client()
        client.set_tenant(tenant_id)

        result = client.tenant()

        assert_that(result, equal_to(tenant_id))

    def test_given_no_exception_when_is_server_reachable_then_true(self):
        session = Mock()
        client = MockSessionClient(session)

        result = client.is_server_reachable()

        assert_that(result, is_(True))

    def test_given_httperror_exception_when_is_server_reachable_then_true(self):
        session = Mock()
        session.head.side_effect = HTTPError
        client = MockSessionClient(session)

        result = client.is_server_reachable()

        assert_that(result, is_(True))

    def test_given_requestexception_when_is_server_reachable_then_false(self):
        session = Mock()
        session.head.side_effect = RequestException
        client = MockSessionClient(session)

        result = client.is_server_reachable()

        assert_that(result, is_(False))
