# -*- coding: utf-8 -*-

# Copyright 2014-2018 The Wazo Authors  (see the AUTHORS file)
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
from requests import HTTPError
from requests import RequestException
from requests import Session
from requests.packages.urllib3 import disable_warnings
from six import text_type
from stevedore import extension

logger = logging.getLogger(__name__)


class InvalidArgumentError(Exception):

    def __init__(self, argument_name):
        super(InvalidArgumentError, self).__init__('Invalid value for argument "{}"'.format(argument_name))


class BaseClient(object):

    namespace = None
    _url_fmt_with_port = '{scheme}://{host}:{port}{prefix}/{version}'
    _url_fmt_no_port = '{scheme}://{host}{prefix}/{version}'

    def __init__(self,
                 host,
                 port,
                 version='',
                 token=None,
                 tenant=None,
                 default_tenant=None,
                 https=True,
                 timeout=10,
                 verify_certificate=True,
                 prefix=None,
                 **kwargs):
        if not host:
            raise InvalidArgumentError('host')

        self.host = host
        self.port = port
        self.timeout = timeout
        self._version = version
        self._token_id = token
        self._tenant_id = tenant
        self._default_tenant_id = default_tenant
        self._https = https
        self._verify_certificate = verify_certificate
        self._prefix = self._build_prefix(prefix)
        if kwargs:
            logger.debug('%s received unexpected arguments: %s', self.__class__.__name__, list(kwargs.keys()))
        self._load_plugins()

    def _build_prefix(self, prefix):
        if not prefix:
            return ''
        if not prefix.startswith('/'):
            prefix = '/' + prefix
        return prefix

    def _load_plugins(self):
        if not self.namespace:
            raise ValueError('You must redefine BaseClient.namespace')

        extension_manager = extension.ExtensionManager(self.namespace)
        try:
            extension_manager.map(self._add_command_to_client)
        except RuntimeError:
            logger.warning('No commands found')

    def _add_command_to_client(self, extension_):
        command = extension_.plugin(self)
        setattr(self, extension_.name, command)

    def session(self):
        session = Session()
        session.headers = {'Connection': 'close'}

        if self.timeout is not None:
            session.request = partial(session.request, timeout=self.timeout)

        if self._https:
            if not self._verify_certificate:
                disable_warnings()
                session.verify = False
            else:
                session.verify = self._verify_certificate

        if self._token_id:
            session.headers['X-Auth-Token'] = self._token_id

        if self._tenant_id:
            session.headers['Wazo-Tenant'] = self._tenant_id

        return session

    def set_tenant(self, tenant):
        self._tenant_id = tenant

    def set_default_tenant(self, tenant):
        self._default_tenant_id = tenant

    def tenant(self):
        return self._tenant_id or self._default_tenant_id

    def set_token(self, token):
        self._token_id = token

    def url(self, *fragments):
        url_fmt = self._url_fmt_with_port if self.port else self._url_fmt_no_port
        base = url_fmt.format(
            scheme='https' if self._https else 'http',
            host=self.host,
            port=self.port,
            prefix=self._prefix,
            version=self._version
        )
        if fragments:
            base = "{base}/{path}".format(base=base, path='/'.join(text_type(fragment) for fragment in fragments))

        return base

    def is_server_reachable(self):
        try:
            self.session().head(self.url())
            return True
        except HTTPError:
            return True
        except RequestException as e:
            logger.debug('Server unreachable: %s', e)
            return False
