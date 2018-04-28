# -*- coding: utf-8 -*-
# Copyright (C) 2014-2015 Avencall
# SPDX-License-Identifier: GPL-3.0+

from .command import RESTCommand


class ExampleCommand(RESTCommand):

    resource = 'test'

    def __call__(self):
        return self.test()

    def test(self):
        r = self.session.get(self.base_url)
        return r.content
