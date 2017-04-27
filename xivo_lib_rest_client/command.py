# -*- coding: utf-8 -*-

# Copyright 2014-2017 The Wazo Authors  (see the AUTHORS file)
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

import abc
import json


class HTTPCommand(object):

    def __init__(self, client):
        self._client = client

    @property
    def session(self):
        return self._client.session()

    @staticmethod
    def raise_from_response(response):
        try:
            response.reason = json.loads(response.text)['message']
        except (ValueError, KeyError, TypeError):
            pass

        response.raise_for_status()


class RESTCommand(HTTPCommand):

    __metaclass__ = abc.ABCMeta

    @abc.abstractproperty
    def resource(self):
        return

    def __init__(self, client):
        super(RESTCommand, self).__init__(client)
        self.base_url = self._client.url(self.resource)
        self.timeout = self._client.timeout
