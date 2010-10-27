# -*- coding: utf-8 -*-

# Copyright(C) 2010  Christophe Benz, Romain Bignon
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.


__all__ = ['FormattersLoader', 'FormatterLoadError']


class FormatterLoadError(Exception):
    pass

class FormattersLoader(object):
    BUILTINS = ['htmltable', 'multiline', 'simple', 'table', 'csv', 'webkit']

    def __init__(self):
        self.formatters = {}

    def register_formatter(self, name, klass):
        self.formatters[name] = klass

    def get_available_formatters(self):
        l = set(self.formatters.iterkeys())
        l = l.union(self.BUILTINS)
        l = list(l)
        l.sort()
        return l

    def build_formatter(self, name):
        if not name in self.formatters:
            try:
                self.formatters[name] = self.load_builtin_formatter(name)
            except ImportError, e:
                FormattersLoader.BUILTINS.remove(name)
                raise FormatterLoadError('Unable to load formatter "%s": %s' % (name, e))
        return self.formatters[name]()

    def load_builtin_formatter(self, name):
        if not name in self.BUILTINS:
            raise FormatterLoadError('Formatter "%s" does not exist' % name)

        if name == 'htmltable':
            from .table import HTMLTableFormatter
            return HTMLTableFormatter
        elif name == 'table':
            from .table import TableFormatter
            return TableFormatter
        elif name == 'simple':
            from .simple import SimpleFormatter
            return SimpleFormatter
        elif name == 'multiline':
            from .multiline import MultilineFormatter
            return MultilineFormatter
        elif name == 'webkit':
            from .webkit import WebkitGtkFormatter
            return WebkitGtkFormatter
        elif name == 'csv':
            from .csv import CSVFormatter
            return CSVFormatter
