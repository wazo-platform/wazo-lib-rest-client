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

from requests import Session
from stevedore import extension

logger = logging.getLogger(__name__)


class _SessionBuilder(object):

    def __init__(self, host='localhost', port=9487, version='1.1',
                 username=None, password=None, https=True):
        self.scheme = 'https' if https else 'http'
        self.host = host
        self.port = port
        self.version = version
        self.username = username
        self.password = password

    def session(self):
        session = Session()
        if self.scheme == 'https':
            session.verify = False
        if self.username and self.password:
            session.auth = requests.auth.HTTPDigestAuth(self.username, self.password)
        return session

    def url(self, resource=None):
        return '{scheme}://{host}:{port}/{version}/{resource}'.format(scheme=self.scheme,
                                                                      host=self.host,
                                                                      port=self.port,
                                                                      version=self.version,
                                                                      resource=resource or '')


class _BaseClient(object):

    @property
    def namespace(self):
        raise NotImplementedError('The implementation of a command must have a namespace field')

    def __init__(self, host='localhost', port=9487, version='1.1', username=None, password=None, https=True):
        self._session_builder = _SessionBuilder(host, port, version, username, password, https)
        self._load_plugins()

    def _load_plugins(self):
        extension_manager = extension.ExtensionManager(self.namespace)
        try:
            extension_manager.map(self._add_command_to_client)
        except RuntimeError:
            logger.warning('No commands found')

    def _add_command_to_client(self, extension):
        command = extension.plugin(self._session_builder)
        setattr(self, extension.name, command)


def make_client(ns):

    class Client(_BaseClient):
        namespace = ns

    return Client
