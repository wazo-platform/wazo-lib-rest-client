# -*- coding: utf-8 -*-

# Copyright (C) 2014-20155555 Avencall
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


class TestRESTCommand(unittest.TestCase):

    def test_init_base_url_built(self):
        class TestCommand(RESTCommand):
            resource = 'test'

        session_builder = Mock()
        session_builder.timeout = sentinel.timeout
        url = session_builder.url.return_value = 'https://example.com:9000/42/test'

        c = TestCommand(session_builder)

        assert_that(c.base_url, equal_to(url))
        assert_that(c.timeout, equal_to(sentinel.timeout))
        session_builder.url.assert_called_once_with(TestCommand.resource)
