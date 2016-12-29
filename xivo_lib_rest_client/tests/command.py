# -*- coding: utf-8 -*-

# Copyright (C) 2014-2015 Avencall
# Copyright (C) 2016 Proformatique Inc.
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
from mock import Mock, sentinel
from requests.exceptions import HTTPError


class HTTPCommandTestCase(unittest.TestCase):

    def setUp(self):
        self.client = Mock()
        self.client.timeout = sentinel.timeout
        self.session = self.client.session.return_value
        self.session.headers = {}
        self.command = self.Command(self.client)

    def assertRaisesHTTPError(self, function, *args, **kwargs):
        self.assertRaises(HTTPError, function, *args, **kwargs)

    @staticmethod
    def new_response(status_code, json=None, body=None):
        response = Mock()
        response.status_code = status_code
        response.raise_for_status.side_effect = HTTPError()
        if json is not None:
            response.json.return_value = json
        elif body is not None:
            response.text = body
            response.content = body
        else:
            response.json.side_effect = ValueError()
        return response

    def set_response(self, action, status_code, body=None):
        mock_action = getattr(self.session, action)
        mock_action.return_value = self.new_response(status_code, json=body)
        return body

    def assert_request_sent(self, action, url, **kwargs):
        mock_action = getattr(self.session, action)
        mock_action.assert_called_once_with(url, **kwargs)


class RESTCommandTestCase(HTTPCommandTestCase):

    scheme = 'http'
    host = 'wazo.community'
    port = 9486
    version = '1.0'

    def setUp(self):
        super(RESTCommandTestCase, self).setUp()
        self.base_url = self.command.base_url
