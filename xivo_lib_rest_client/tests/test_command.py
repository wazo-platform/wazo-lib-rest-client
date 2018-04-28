# -*- coding: utf-8 -*-
# Copyright 2014-2017 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

import unittest

from ..command import HTTPCommand, RESTCommand
from hamcrest import assert_that
from hamcrest import equal_to
from mock import Mock, sentinel


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
        except (TypeError):
            self.fail('TypeError unexpectedly raised')


class TestRESTCommand(unittest.TestCase):

    def test_init_base_url_built(self):
        class TestCommand(RESTCommand):
            resource = 'test'

        client = Mock()
        client.timeout = sentinel.timeout
        url = client.url.return_value = 'https://example.com:9000/42/test'

        c = TestCommand(client)

        assert_that(c.base_url, equal_to(url))
        assert_that(c.timeout, equal_to(sentinel.timeout))
        client.url.assert_called_once_with(TestCommand.resource)
