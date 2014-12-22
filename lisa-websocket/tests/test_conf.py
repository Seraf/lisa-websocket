# -*- coding: utf-8 -*-

# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""
test_sandbox
----------------------------------

Tests for `sandbox` module.
"""

import sys

import mock

from sandbox import conf
from sandbox.tests import base


class TestConf(base.TestCase):

    def setUp(self):
        super(TestConf, self).setUp()
        # We need to reset the CONF object for each test
        self.CONF = conf.Config()

    def test_init(self):
        config = conf.Config()
        self.assertTrue(config.parser)
        self.assertTrue(isinstance(config.parser,
                                   conf.configparser.SafeConfigParser))

    def test_global(self):
        self.assertTrue(conf.CONF.parser)
        self.assertTrue(isinstance(conf.CONF, conf.Config))

    @mock.patch.object(conf.Config, '_populate_cache')
    @mock.patch.object(conf.configparser.SafeConfigParser, 'read')
    def test_load(self, mock_read, mock_pop_cache):
        self.CONF.load('filename')
        self.assertTrue('filename', self.CONF._filename)
        mock_read.assert_called_once_with('filename')
        mock_pop_cache.assert_called_once_with()

    @mock.patch.object(conf.configparser.SafeConfigParser, 'write')
    def test_save_with_filename(self, mock_write):
        self.CONF.save('filename')
        mock_write.assert_called_once_with('filename')

    @mock.patch.object(conf.configparser.SafeConfigParser, 'write')
    def test_save_with_no_filename_and_no_cache(self, mock_write):
        self.assertIsNone(self.CONF._filename)
        self.CONF.save()
        mock_write.assert_called_once_with(sys.stdout)

    @mock.patch.object(conf.configparser.SafeConfigParser, 'write')
    def test_save_with_no_filename_and_cache(self, mock_write):
        self.CONF._filename = 'fake'
        self.CONF.save()
        mock_write.assert_called_once_with('fake')

    def test_add_opt_no_section(self):
        self.CONF.add_opt('fake', 'val')
        # NOTE(sbauza) : Using the SafeConfigParser to make sure it's good
        # We could just check that the call would be done but it's better
        # if it's rather a functional test
        self.assertTrue({'fake': 'val'}, self.CONF.parser.defaults())
        self.assertEqual({None: {'fake': 'val'}})

    def test_add_opt_cast_val_to_string(self):
        self.CONF.add_opt('fakeint', 1)
        # NOTE(sbauza) : Using the SafeConfigParser to make sure it's good
        # We could just check that the call would be done but it's better
        # if it's rather a functional test
        self.assertTrue({'fake': 'val', 'fakeint': '1'},
                        self.CONF.parser.defaults())
        self.assertEqual({None: {'fakeint': 1}})

    def test_add_opt_with_section(self):
        # NOTE(sbauza) : Using the SafeConfigParser to make sure it's good
        # We could just check that the call would be done but it's better
        # if it's rather a functional test
        self.assertFalse(self.CONF.parser.has_section('sect'))
        self.CONF.add_opt('fake', 'val', section='sect')
        self.assertTrue(self.CONF.parser.has_section('sect'))
        self.assertEqual('val', self.CONF.parser.get('sect', 'fake'))
        self.assertEqual({'sect': {'fake': 'val'}})

    def test_object_attributes(self):
        self.CONF.add_opt('fake1', 'val1')
        self.CONF.add_opt('fake2', 'val2', section='sect1')

        self.assertEqual('val1', self.CONF.fake1)
        self.assertEqual('val2', self.CONF.sect1.fake2)

        self.assertRaises(AttributeError, getattr, self.CONF, 'wrong')
