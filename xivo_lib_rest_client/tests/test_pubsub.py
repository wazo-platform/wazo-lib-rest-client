# -*- coding: utf-8 -*-
# Copyright 2018 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

import unittest

from mock import Mock, patch

from ..pubsub import Pubsub

SOME_TOPIC = 'abcd'
SOME_MESSAGE = 'defg'


class TestPubsub(unittest.TestCase):

    def setUp(self):
        self.pubsub = Pubsub()

    def test_subscribe_and_publish(self):
        callback = Mock()
        self.pubsub.subscribe(SOME_TOPIC, callback)

        self.pubsub.publish(SOME_TOPIC, SOME_MESSAGE)

        callback.assert_called_once_with(SOME_MESSAGE)

    def test_multiple_subscribe_on_same_topic_and_one_publish(self):
        callback_1 = Mock()
        callback_2 = Mock()
        self.pubsub.subscribe(SOME_TOPIC, callback_1)
        self.pubsub.subscribe(SOME_TOPIC, callback_2)

        self.pubsub.publish(SOME_TOPIC, SOME_MESSAGE)

        callback_1.assert_called_once_with(SOME_MESSAGE)
        callback_2.assert_called_once_with(SOME_MESSAGE)

    def test_multiple_subscribe_on_different_topics_and_two_publish(self):
        callback = Mock()
        message_1 = Mock()
        message_2 = Mock()
        topic_1 = 'abcd'
        topic_2 = 'efgh'
        self.pubsub.subscribe(topic_1, callback)
        self.pubsub.subscribe(topic_2, callback)

        self.pubsub.publish(topic_1, message_1)
        self.pubsub.publish(topic_2, message_2)

        callback.assert_any_call(message_1)
        callback.assert_any_call(message_2)
        self.assertEquals(callback.call_count, 2)

    def publish_when_nobody_subscribed(self):
        try:
            self.pubsub.publish(SOME_TOPIC, SOME_MESSAGE)
        except Exception:
            self.fail('publish should not raise exceptions')

    @patch('xivo_lib_rest_client.pubsub.logger')
    def test_when_exception_then_exception_is_logged_by_default(self, logger):
        callback = Mock()
        exception = callback.side_effect = Exception()
        self.pubsub.subscribe(SOME_TOPIC, callback)

        self.pubsub.publish(SOME_TOPIC, SOME_MESSAGE)

        logger.exception.assert_called_once_with(exception)
