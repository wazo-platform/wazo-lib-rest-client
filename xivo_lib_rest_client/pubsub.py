# -*- coding: utf-8 -*-
# Copyright 2018 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

import logging

from collections import defaultdict

logger = logging.getLogger(__name__)


class Pubsub(object):

    def __init__(self):
        self._subscribers = defaultdict(list)

    def subscribe(self, topic, callback):
        logger.debug('Subscribing callback "%s" to topic "%s"', callback, topic)
        self._subscribers[topic].append(callback)

    def publish(self, topic, message=None):
        logger.debug('Publishing to topic "%s": "%s"', topic, message)
        for callback in self._subscribers[topic]:
            self.publish_one(callback, message)

    def publish_one(self, callback, message):
        logger.debug('Publishing to callback "%s": "%s"', callback, message)
        try:
            callback(message)
        except Exception as e:
            logger.exception(e)
