# Copyright 2014-2024 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

from __future__ import annotations

import logging
import os
import sys
from functools import partial
from typing import Any

from requests import HTTPError, RequestException, Session
from requests.packages.urllib3 import disable_warnings
from stevedore import extension

logger = logging.getLogger(__name__)

global PLUGINS_CACHE
PLUGINS_CACHE: dict[str, list[extension.Extension]] = {}


class InvalidArgumentError(Exception):
    def __init__(self, argument_name: str) -> None:
        super().__init__(f'Invalid value for argument "{argument_name}"')


class BaseClient:

    namespace: str | None = None
    _url_fmt = '{scheme}://{host}{port}{prefix}{version}'

    def __init__(
        self,
        host: str,
        port: int,
        version: str = '',
        token: str | None = None,
        tenant: str | None = None,
        https: bool = True,
        timeout: int = 10,
        verify_certificate: bool = True,
        prefix: str | None = None,
        user_agent: str = '',
        **kwargs: Any,
    ) -> None:
        if not host:
            raise InvalidArgumentError('host')
        if not user_agent:
            user_agent = os.path.basename(sys.argv[0])
        self.host = host
        self.port = port
        self.timeout = timeout
        self._version = version
        self._token_id = token
        self._https = https
        self._verify_certificate = verify_certificate
        self._prefix = self._build_prefix(prefix)
        self._user_agent = user_agent
        if kwargs:
            logger.debug(
                '%s received unexpected arguments: %s',
                self.__class__.__name__,
                list(kwargs.keys()),
            )
        self._load_plugins()

        self.tenant_uuid = tenant

    def _build_prefix(self, prefix: str | None) -> str:
        if not prefix:
            return ''
        if not prefix.startswith('/'):
            prefix = '/' + prefix
        return prefix

    def _load_plugins(self) -> None:
        global PLUGINS_CACHE

        if not self.namespace:
            raise ValueError('You must redefine BaseClient.namespace')

        if self.namespace not in PLUGINS_CACHE:
            PLUGINS_CACHE[self.namespace] = list(
                extension.ExtensionManager(self.namespace)
            )

        plugins = PLUGINS_CACHE[self.namespace]
        if not plugins:
            logger.warning('No commands found')
            return

        for ext in plugins:
            setattr(self, ext.name, ext.plugin(self))

    def session(self) -> Session:
        session = Session()
        session.headers = {'Connection': 'close'}

        if self.timeout is not None:
            session.request = partial(  # type: ignore[assignment]
                session.request, timeout=self.timeout
            )

        if self._https:
            if not self._verify_certificate:
                disable_warnings()
                session.verify = False
            else:
                session.verify = self._verify_certificate

        if self._token_id:
            session.headers['X-Auth-Token'] = self._token_id

        if self.tenant_uuid:
            session.headers['Wazo-Tenant'] = self.tenant_uuid

        if self._user_agent:
            session.headers['User-agent'] = self._user_agent

        return session

    def set_tenant(self, tenant_uuid: str) -> None:
        logger.warning('set_tenant() is deprecated. Please use tenant_uuid')
        self.tenant_uuid = tenant_uuid

    def tenant(self) -> str | None:
        logger.warning('tenant() is deprecated. Please use tenant_uuid')
        return self.tenant_uuid

    def set_token(self, token: str) -> None:
        self._token_id = token

    def url(self, *fragments: str) -> str:
        base = self._url_fmt.format(
            scheme='https' if self._https else 'http',
            host=self.host,
            port=f':{self.port}' if self.port else '',
            prefix=self._prefix,
            version=f'/{self._version}' if self._version else '',
        )
        if fragments:
            path = '/'.join(str(fragment) for fragment in fragments)
            base = f"{base}/{path}"
        return base

    def is_server_reachable(self) -> bool:
        try:
            self.session().head(self.url())
            return True
        except HTTPError:
            return True
        except RequestException as e:
            logger.debug('Server unreachable: %s', e)
            return False
