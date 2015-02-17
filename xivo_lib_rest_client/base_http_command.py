# -*- coding: utf-8 -*-

# Copyright (C) 2014 Avencall
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

import json


class BaseHTTPCommand(object):

    @property
    def resource(self):
        raise NotImplementedError('The implementation of a command must have a resource field')

    def __init__(self, session_builder):
        self._session_builder = session_builder
        self.base_url = self._session_builder.url(self.resource)

    @property
    def session(self):
        return self._session_builder.session()

    @staticmethod
    def raise_from_response(response):
        try:
            msg = json.loads(response.text)['message']
            response.reason = msg
        finally:
            response.raise_for_status()
