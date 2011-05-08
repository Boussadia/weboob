# -*- coding: utf-8 -*-

# Copyright(C) 2011  Julien Hebert
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
"backend for http://www.lesinrocks.com"

# python2.5 compatibility
from __future__ import with_statement

from weboob.capabilities.messages import ICapMessages
from .browser import NewspaperInrocksBrowser
from .GenericBackend import GenericNewspaperBackend

class NewspaperInrocksBackend(GenericNewspaperBackend, ICapMessages):
    "NewspaperInrocksBackend class"
    MAINTAINER = 'Julien Hebert'
    EMAIL = 'juke@free.fr'
    VERSION = '0.9'
    LICENSE = 'AGPLv3+'
    STORAGE = {'seen': {}}
    NAME = 'inrocks'
    DESCRIPTION = u'Inrock French news website'
    BROWSER = NewspaperInrocksBrowser
    RSS_FEED = 'http://www.lesinrocks.com/fileadmin/rss/actus.xml'

