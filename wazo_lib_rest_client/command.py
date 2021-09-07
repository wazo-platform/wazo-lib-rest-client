# -*- coding: utf-8 -*-
# Copyright 2014-2021 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

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

    _ro_headers = {'Accept': 'application/json'}

    @abc.abstractproperty
    def resource(self):
        return

    def __init__(self, client):
        super(RESTCommand, self).__init__(client)
        self.base_url = self._client.url(self.resource)
        self.timeout = self._client.timeout

    def _get_headers(self, **kwargs):
        headers = dict(self._ro_headers)
        tenant_uuid = kwargs.pop('tenant_uuid', self._client.tenant())
        if tenant_uuid:
            headers['Wazo-Tenant'] = tenant_uuid
        return headers
