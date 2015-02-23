# -*- coding: utf-8 -*-

# Copyright (C) 2014-2015 Avencall
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


class _SessionBuilder(object):

    def __init__(self, host, port, version, username, password, https, timeout):
        self.scheme = 'https' if https else 'http'
        self.host = host
        self.port = port
        self.version = version
        self.username = username
        self.password = password
        self.timeout = timeout

    def session(self):
        session = Session()
        if self.timeout is not None:
            session.request = partial(session.request, timeout=self.timeout)
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

    def __init__(self, host=None, port=None, version=None, username=None,
                 password=None, https=None, timeout=None):

        session_args = {
            'host': host or self.default_host,
            'port': port or self.default_port,
            'version': version or self.default_version,
            'username': username or self.default_username,
            'password': password or self.default_password,
            'https': https if https is not None else self.default_https,
            'timeout': timeout if timeout is not None else self.default_timeout,
        }

        self._session_builder = _SessionBuilder(**session_args)
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


def make_client(ns, host='localhost', port=None, version=None,
                username=None, password=None, timeout=30, https=True):

    class Client(_BaseClient):
        namespace = ns
        default_host = host
        default_port = port
        default_version = version
        default_username = username
        default_password = password
        default_timeout = timeout
        default_https = https

    return Client
