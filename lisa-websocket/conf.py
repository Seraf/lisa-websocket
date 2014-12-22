# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import collections
import sys

import six
from six.moves import configparser

_TRUE = ['True']
_FALSE = ['False']


class Config(object):

    parser = None
    _filename = None
    _cached = {}

    @staticmethod
    def _tr_str_to_sth(stringy):
        if not isinstance(stringy, str):
            # Do nothing else, we need a string
            return stringy
        try:
            stringy = int(stringy)
        except ValueError:
            if stringy in _TRUE:
                stringy = True
            if stringy in _FALSE:
                stringy = False
        return stringy

    def __init__(self):
        if self.parser is None:
            self.parser = configparser.SafeConfigParser()

    def _populate_cache(self):
        for section in self.parser.sections():
            for opt in self.parser.options():
                casted = self._tr_str_to_sth(self.parser.get(section, opt))
                self._cached.setdefault(section, {}).update({opt: casted})
        for def_opt in self.parser.defaults():
            casted = self._tr_str_to_sth(self.parser.get(section, opt))
            self._cached.setdefault(None, {}).update({def_opt: casted})

    def load(self, filename):
        """Import configuration from a ini file."""
        self._filename = filename
        self.parser.read(filename)
        self._populate_cache()

    def save(self, filename=None):
        """Persists configuration into a file or stdout."""
        if filename is None:
            filename = self._filename or sys.stdout
        self.parser.write(filename)

    def add_opt(self, name, value, section=None):

        if not isinstance(name, str):
            raise ConfigException(six.text_type("name must be a string"))
        try:
            int(name)
            raise ConfigException(six.text_type("name must be alphabetic"))
        except ValueError:
            if name in _TRUE or name in _FALSE:
                raise ConfigException(six.text_type("name must not be "
                                                    "True or False"))
        if name in self._cached.get(section, {}):
            # Do nothing as INI file must be preemptive
            return
        self._cached.setdefault(section, {}).update({name: value})
        if section is not None and not self.parser.has_section(section):
            self.parser.add_section(section)
        value = value if isinstance(value, str) else str(value)
        if section is None:
            self.parser._defaults.update({name: value})
        else:
            self.parser.set(section, name, value)

    def __getattr__(self, name):
        if name in self._cached:
            # This is a section, we need to return an object
            return collections.namedtuple(
                '_Section', self._cached[name])(**self._cached[name])
        if name in self._cached.get(None, {}):
            # This is a default opt, just return the value
            return self._cached[None][name]
        raise AttributeError


class ConfigException(Exception):
    pass

# Global object for convenient purpose
CONF = Config()
