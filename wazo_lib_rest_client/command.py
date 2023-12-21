# Copyright 2014-2023 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+
from __future__ import annotations

import abc
import json

from requests import Response, Session

from wazo_lib_rest_client.client import BaseClient


class HTTPCommand:
    def __init__(self, client: BaseClient) -> None:
        self._client = client

    @property
    def session(self) -> Session:
        return self._client.session()

    @staticmethod
    def raise_from_response(response: Response) -> None:
        try:
            response.reason = json.loads(response.text)['message']
        except (ValueError, KeyError, TypeError):
            pass

        response.raise_for_status()


class RESTCommand(HTTPCommand):

    __metaclass__ = abc.ABCMeta

    _headers = {'Accept': 'application/json'}

    @abc.abstractproperty
    def resource(self) -> str:
        pass

    def __init__(self, client: BaseClient) -> None:
        super().__init__(client)
        self.base_url = self._client.url(self.resource)
        self.timeout = self._client.timeout

    def _get_headers(self, **kwargs: str) -> dict[str, str]:
        headers = dict(self._headers)
        # The requests session will use self.tenant_uuid by default
        tenant_uuid = kwargs.pop('tenant_uuid', None)
        if tenant_uuid:
            headers['Wazo-Tenant'] = str(tenant_uuid)
        return headers
