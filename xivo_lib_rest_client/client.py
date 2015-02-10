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

import requests
import logging

from functools import partial
from requests import Session
from stevedore import extension

logger = logging.getLogger(__name__)


class _BaseClient(object):

    @property
    def namespace(self):
        raise NotImplementedError('The implementation of a command must have a namespace field')

    def __init__(self, host='localhost', port=9487, version='1.1', username=None, password=None, timeout=None):
        self._host = host
        self._port = port
        self._version = version
        self._username = username
        self._password = password
        self._scheme = 'http' if username is None or password is None else 'https'
        self._default_timeout = timeout
        self._session = self._new_session()
        self._load_plugins()

    def _new_session(self):
        session = Session()
        if self._default_timeout is not None:
            session.request = partial(session.request, timeout=self._default_timeout)
        if self._scheme == 'https':
            session.verify = False
        if self._username and self._password:
            session.auth = requests.auth.HTTPDigestAuth(self._username, self._password)
        return session

    def _load_plugins(self):
        extension_manager = extension.ExtensionManager(self.namespace)
        try:
            extension_manager.map(self._add_command_to_client)
        except RuntimeError:
            logger.warning('No commands found')

    def _add_command_to_client(self, extension):
        command = extension.plugin(self._scheme, self._host, self._port, self._version, self._session)
        setattr(self, extension.name, command)


def make_client(ns):

    class Client(_BaseClient):
        namespace = ns

    return Client
