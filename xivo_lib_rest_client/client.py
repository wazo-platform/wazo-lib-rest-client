# -*- coding: utf-8 -*-

# Copyright (C) 2014-2016 Avencall
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

import logging

from functools import partial
from requests import Session
from requests.packages.urllib3 import disable_warnings
from stevedore import extension

logger = logging.getLogger(__name__)


class BaseClient(object):

    namespace = None

    def __init__(self,
                 host,
                 port,
                 version='',
                 token=None,
                 https=True,
                 timeout=10,
                 verify_certificate=True):
        self.host = host
        self.port = port
        self.version = version
        self.token_id = token
        self.https = https
        self.timeout = timeout
        self.verify_certificate = verify_certificate
        self._load_plugins()

    def _load_plugins(self):
        if not self.namespace:
            raise ValueError('You must redefine BaseClient.namespace')

        extension_manager = extension.ExtensionManager(self.namespace)
        try:
            extension_manager.map(self._add_command_to_client)
        except RuntimeError:
            logger.warning('No commands found')

    def _add_command_to_client(self, extension):
        command = extension.plugin(self)
        setattr(self, extension.name, command)

    def session(self):
        session = Session()
        session.headers = {'Connection': 'close'}

        if self.timeout is not None:
            session.request = partial(session.request, timeout=self.timeout)

        if self.https:
            if not self.verify_certificate:
                disable_warnings()
                session.verify = False
            else:
                session.verify = self.verify_certificate

        if self.token_id:
            session.headers['X-Auth-Token'] = self.token_id

        return session

    def set_token(self, token):
        self.token_id = token

    def url(self, *fragments):
        base = '{scheme}://{host}:{port}/{version}'.format(scheme='https' if self.https else 'http',
                                                           host=self.host,
                                                           port=self.port,
                                                           version=self.version)
        if fragments:
            base = "{base}/{path}".format(base=base, path='/'.join(fragments))

        return base
