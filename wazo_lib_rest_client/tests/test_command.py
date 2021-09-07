# -*- coding: utf-8 -*-
# Copyright 2014-2021 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

import unittest

from hamcrest import assert_that
from hamcrest import equal_to
from mock import Mock, sentinel

from ..command import HTTPCommand, RESTCommand


class TestHTTPCommand(unittest.TestCase):

    def test_raise_from_response_no_message(self):
        class ExpectedError(Exception):
            pass

        response = Mock(text='not a dict with message',
                        raise_for_status=Mock(side_effect=ExpectedError))

        self.assertRaises(ExpectedError, HTTPCommand.raise_from_response, response)

    def test_raise_from_response_substitute_reason_for_the_message(self):
        class ExpectedError(Exception):
            pass

        response = Mock(text='{"message": "Expected reason"}',
                        raise_for_status=Mock(side_effect=ExpectedError))

        self.assertRaises(ExpectedError, HTTPCommand.raise_from_response, response)
        assert_that(response.reason, equal_to('Expected reason'))

    def test_raise_from_response_does_not_raise_keyerror_or_valueerror(self):
        response = Mock(text='not a dict with message')

        try:
            HTTPCommand.raise_from_response(response)
        except (KeyError, ValueError):
            self.fail('KeyError or ValueError unexpectedly raised')

    def test_raise_from_response_does_not_raise_typeerror(self):
        response = Mock(text=None)

        try:
            HTTPCommand.raise_from_response(response)
        except TypeError:
            self.fail('TypeError unexpectedly raised')


class TestRESTCommand(unittest.TestCase):

    def setUp(self):
        class TestCommand(RESTCommand):
            resource = 'test'

        self.TestCommand = TestCommand

    def test_init_base_url_built(self):
        client = Mock()
        client.timeout = sentinel.timeout
        url = client.url.return_value = 'https://example.com:9000/42/test'

        c = self.TestCommand(client)

        assert_that(c.base_url, equal_to(url))
        assert_that(c.timeout, equal_to(sentinel.timeout))
        client.url.assert_called_once_with(self.TestCommand.resource)

    def test_get_headers_accept(self):
        client = Mock()
        client.tenant.return_value = None

        c = self.TestCommand(client)

        expected_headers = {'Accept': 'application/json'}
        assert_that(c._get_headers(), equal_to(expected_headers))

    def test_get_headers_default_tenant(self):
        client = Mock()
        client.tenant.return_value = 'default-tenant'

        c = self.TestCommand(client)

        expected_headers = {'Accept': 'application/json', 'Wazo-Tenant': 'default-tenant'}
        assert_that(c._get_headers(), equal_to(expected_headers))

    def test_get_headers_custom_tenant(self):
        client = Mock()
        client.tenant.return_value = 'default-tenant'
        kwargs = {'tenant_uuid': 'custom-tenant'}

        c = self.TestCommand(client)

        expected_headers = {'Accept': 'application/json', 'Wazo-Tenant': 'custom-tenant'}
        assert_that(c._get_headers(**kwargs), equal_to(expected_headers))
