# Copyright 2014-2022 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

from unittest import TestCase
from unittest.mock import Mock, sentinel
from requests.exceptions import HTTPError


class HTTPCommandTestCase(TestCase):

    def setUp(self):
        base_url = self.Command.resource
        self.client = Mock()
        self.client.timeout = sentinel.timeout
        self.client.tenant = Mock(return_value=None)
        self.client.url = Mock(return_value=base_url)
        self.session = self.client.session.return_value
        self.session.headers = {}
        self.command = self.Command(self.client)

    def assertRaisesHTTPError(self, function, *args, **kwargs):
        self.assertRaises(HTTPError, function, *args, **kwargs)

    @staticmethod
    def new_response(status_code, json=None, body=None):
        response = Mock()
        response.status_code = status_code
        if status_code >= 300:
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
        super().setUp()
        self.base_url = self.command.base_url
