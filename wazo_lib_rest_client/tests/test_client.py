# Copyright 2014-2026 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

from __future__ import annotations

import os
import subprocess
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import ANY, Mock, patch

import requests
from hamcrest import (
    assert_that,
    close_to,
    contains_string,
    ends_with,
    equal_to,
    has_entry,
    is_,
)
from requests import Session
from requests.exceptions import HTTPError, RequestException, Timeout

from ..client import BaseClient, logger
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
        assert self._session is not None
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

    def _request_headers(self, client):
        session = client.session()
        with patch.object(session, 'send', return_value=Mock()) as send:
            session.get('http://example.invalid')
        return send.call_args.args[0].headers

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

    def test_timeout_change_is_applied_to_existing_session(self):
        client = self.new_client(timeout=1)
        session = client.session()

        client.timeout = 5

        with patch.object(session, 'send', return_value=Mock()) as send:
            session.get('http://example.invalid')

        assert_that(send.call_args.kwargs, has_entry('timeout', 5))

    def test_token(self):
        token_id = 'the-one-ring'
        client = self.new_client(token=token_id)

        headers = self._request_headers(client)

        assert_that(headers, has_entry('X-Auth-Token', token_id))

    def test_set_token(self):
        token_id = 'the-one-ring'
        client = self.new_client()

        client.set_token(token_id)

        headers = self._request_headers(client)
        assert_that(headers, has_entry('X-Auth-Token', token_id))

    def test_tenant_param(self):
        tenant_id = 'my-tenant'
        client = self.new_client(tenant=tenant_id)

        headers = self._request_headers(client)
        assert_that(headers, has_entry('Wazo-Tenant', tenant_id))

    def test_set_tenant(self):
        tenant_id = 'my-tenant'
        client = self.new_client()

        client.set_tenant(tenant_id)

        headers = self._request_headers(client)
        assert_that(headers, has_entry('Wazo-Tenant', tenant_id))

    def test_tenant(self):
        tenant_id = 'my-tenant'
        client = self.new_client()
        client.set_tenant(tenant_id)

        result = client.tenant()

        assert_that(result, equal_to(tenant_id))

    def test_session_is_persistent(self):
        client = self.new_client()

        assert_that(client.session() is client.session())

    def test_set_token_applies_to_later_requests(self):
        client = self.new_client(token='old-token')
        session = client.session()

        client.set_token('new-token')

        assert_that(client.session() is session)
        headers = self._request_headers(client)
        assert_that(headers, has_entry('X-Auth-Token', 'new-token'))

    def test_set_empty_token_removes_header_from_later_requests(self):
        client = self.new_client(token='a-token')
        client.session()

        client.set_token('')

        headers = self._request_headers(client)
        assert_that('X-Auth-Token' not in headers)

    def test_tenant_uuid_assignment_applies_to_later_requests(self):
        client = self.new_client(tenant='old-tenant')
        session = client.session()

        client.tenant_uuid = 'new-tenant'

        assert_that(client.session() is session)
        headers = self._request_headers(client)
        assert_that(headers, has_entry('Wazo-Tenant', 'new-tenant'))

    def test_request_headers_override_client_token_and_tenant(self):
        client = self.new_client(token='client-token', tenant='client-tenant')
        session = client.session()

        with patch.object(session, 'send', return_value=Mock()) as send:
            session.get(
                'http://example.invalid',
                headers={'X-Auth-Token': 'call-token', 'Wazo-Tenant': 'call-tenant'},
            )

        headers = send.call_args.args[0].headers
        assert_that(headers, has_entry('X-Auth-Token', 'call-token'))
        assert_that(headers, has_entry('Wazo-Tenant', 'call-tenant'))

    def test_request_headers_override_regardless_of_casing(self):
        client = self.new_client(token='client-token', tenant='client-tenant')
        session = client.session()

        with patch.object(session, 'send', return_value=Mock()) as send:
            session.get(
                'http://example.invalid',
                headers={'x-auth-token': 'call-token', 'wazo-tenant': 'call-tenant'},
            )

        headers = send.call_args.args[0].headers
        assert_that(headers, has_entry('x-auth-token', 'call-token'))
        assert_that(headers, has_entry('wazo-tenant', 'call-tenant'))

    def test_prepare_request_path_gets_token_and_tenant_injected(self):
        client = self.new_client(token='the-token', tenant='the-tenant')
        session = client.session()

        request = requests.Request('GET', 'http://example.invalid')
        prepared = session.prepare_request(request)

        assert_that(prepared.headers, has_entry('X-Auth-Token', 'the-token'))
        assert_that(prepared.headers, has_entry('Wazo-Tenant', 'the-tenant'))

    def test_default_no_connection_close(self):
        client = self.new_client()

        session = client.session()

        assert_that('Connection' not in session.headers)

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


class ConnectionTrackingHandler(BaseHTTPRequestHandler):
    # HTTP/1.1 keeps connections alive by default, which is what lets us
    # observe real connection reuse from the client.
    protocol_version = 'HTTP/1.1'

    def do_GET(self) -> None:
        body = b'{"foo": "bar"}'
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        # The client's source port identifies the underlying TCP connection: a
        # reused (kept-alive) connection keeps the same port across requests,
        # while a fresh connection gets a new ephemeral port.
        self.send_header('X-Client-Port', str(self.client_address[1]))
        # Echo the connection-management request headers back for assertions.
        self.send_header('X-Seen-Connection', self.headers.get('Connection', ''))
        self.send_header('Set-Cookie', 'session=should-not-be-kept; Path=/')
        self.send_header('X-Seen-Cookie', self.headers.get('Cookie', ''))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        pass  # silence per-request logging during tests


class TestConnectionReuse(unittest.TestCase):
    def setUp(self) -> None:
        self._server = ThreadingHTTPServer(('127.0.0.1', 0), ConnectionTrackingHandler)
        self._port = self._server.server_address[1]
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()

    def tearDown(self) -> None:
        self._server.shutdown()
        self._server.server_close()
        self._thread.join()

    def _client(self, **kwargs: object) -> Client:
        return Client(
            host='127.0.0.1', port=self._port, version='', https=False, **kwargs
        )

    def test_connection_is_reused_across_requests_by_default(self) -> None:
        client = self._client()
        session = client.session()

        first = session.get(client.url())
        second = session.get(client.url())

        # Same source port on both requests => the TCP connection was reused.
        assert_that(
            first.headers['X-Client-Port'],
            equal_to(second.headers['X-Client-Port']),
        )
        # No Connection header is sent at all, so HTTP/1.1 keep-alive applies.
        assert_that(first.headers['X-Seen-Connection'], equal_to(''))

    def test_server_cookies_are_not_persisted_across_requests(self) -> None:
        client = self._client()
        session = client.session()

        session.get(client.url())
        second = session.get(client.url())

        assert_that(second.headers['X-Seen-Cookie'], equal_to(''))
        assert_that(len(session.cookies), equal_to(0))
