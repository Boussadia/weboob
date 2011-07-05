# -*- coding: utf-8 -*-

# Copyright(C) 2010-2011 Romain Bignon
#
# This file is part of weboob.
#
# weboob is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# weboob is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with weboob. If not, see <http://www.gnu.org/licenses/>.


import re
from .ordereddict import OrderedDict


__all__ = ['ValuesDict', 'Value', 'ValueInt', 'ValueBool', 'ValueFloat']


class ValuesDict(OrderedDict):
    def __init__(self, *values):
        OrderedDict.__init__(self)
        for v in values:
            self[v.id] = v

class Value(object):
    def __init__(self, *args, **kwargs):
        if len(args) > 0:
            self.id = args[0]
        else:
            self.id = ''
        self.label = kwargs.get('label', kwargs.get('description', None))
        self.description = kwargs.get('description', kwargs.get('label', None))
        self.default = kwargs.get('default', None)
        self.regexp = kwargs.get('regexp', None)
        self.choices = kwargs.get('choices', None)
        if isinstance(self.choices, (list,tuple)):
            self.choices = dict(((v, v) for v in self.choices))
        self.masked = kwargs.get('masked', False)
        self.required = kwargs.get('required', self.default is None)
        self._value = kwargs.get('value', None)

    def check_valid(self, v):
        if v == '' and self.default != '':
            raise ValueError('Value can\'t be empty')
        if self.regexp is not None and not re.match(self.regexp, unicode(v)):
            raise ValueError('Value "%s" does not match regexp "%s"' % (v, self.regexp))
        if self.choices is not None and not v in self.choices.iterkeys():
            raise ValueError('Value "%s" is not in list: %s' % (
                v, ', '.join(unicode(s) for s in self.choices.iterkeys())))

    def load(self, domain, v, callbacks):
        return self.set(v)

    def set(self, v):
        self.check_valid(v)
        self._value = v

    def dump(self):
        return self.get()

    def get(self):
        return self._value

class ValueBackendPassword(Value):
    _domain = None
    _callbacks = {}
    _stored = True

    def __init__(self, *args, **kwargs):
        kwargs['masked'] = kwargs.pop('masked', True)
        self.noprompt = kwargs.pop('noprompt', False)
        Value.__init__(self, *args, **kwargs)

    def load(self, domain, password, callbacks):
        self._domain = domain
        self._value = password
        self._callbacks = callbacks

    def check_valid(self, passwd):
        if passwd == '':
            # always allow empty passwords
            return True
        return Value.check_valid(self, passwd)

    def set(self, passwd):
        self.check_valid(passwd)
        if passwd is None:
            # no change
            return
        self._value = ''
        if passwd == '':
            return
        if self._domain is None:
            self._value = passwd
            return

        try:
            import keyring
            keyring.set_password(self._domain, self.id, passwd)
        except Exception:
            self._value = passwd
        else:
            self._value = ''

    def dump(self):
        if self._stored:
            return self._value
        else:
            return ''

    def get(self):
        if self._value == '' and self._domain is not None:
            try:
                import keyring
            except ImportError:
                return ''
            else:
                passwd = keyring.get_password(self._domain, self.id)
                if passwd is None:
                    if not self.noprompt and 'login' in self._callbacks:
                        self._value = self._callbacks['login'](self._domain, self)
                        if self._value is None:
                            self._value = ''
                        else:
                            self._stored = False
                    return self._value
                else:
                    return passwd
        else:
            return self._value

class ValueInt(Value):
    def __init__(self, *args, **kwargs):
        kwargs['regexp'] = '^\d+$'
        Value.__init__(self, *args, **kwargs)

    def get(self):
        return int(self._value)

class ValueFloat(Value):
    def __init__(self, *args, **kwargs):
        kwargs['regexp'] = '^[\d\.]+$'
        Value.__init__(self, *args, **kwargs)

    def check_valid(self, v):
        try:
            float(v)
        except ValueError:
            raise ValueError('Value "%s" is not a float value')

    def get(self):
        return float(self._value)

class ValueBool(Value):
    def __init__(self, *args, **kwargs):
        kwargs['choices'] = {'y': 'True', 'n': 'False'}
        Value.__init__(self, *args, **kwargs)

    def check_valid(self, v):
        if not isinstance(v, bool) and \
           not unicode(v).lower() in ('y', 'yes', '1', 'true',  'on',
                                      'n', 'no',  '0', 'false', 'off'):
            raise ValueError('Value "%s" is not a boolean (y/n)' % v)

    def get(self):
        return (isinstance(self._value, bool) and self._value) or \
                unicode(self._value).lower() in ('y', 'yes', '1', 'true', 'on')
