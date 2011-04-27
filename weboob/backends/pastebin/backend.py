# -*- coding: utf-8 -*-

# Copyright(C) 2011 Laurent Bachelier
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


from __future__ import with_statement

from weboob.capabilities.paste import ICapPaste
from weboob.tools.backend import BaseBackend
from weboob.capabilities.base import NotLoaded
from weboob.tools.value import Value, ValuesDict

from .browser import PastebinBrowser
from .paste import PastebinPaste


__all__ = ['PastebinBackend']


class PastebinBackend(BaseBackend, ICapPaste):
    NAME = 'pastebin'
    MAINTAINER = 'Laurent Bachelier'
    EMAIL = 'laurent@bachelier.name'
    VERSION = '0.8'
    DESCRIPTION = 'Pastebin paste tool'
    LICENSE = 'AGPLv3+'
    BROWSER = PastebinBrowser
    CONFIG = ValuesDict(
        Value('apikey', label='Optional API key', default='', masked=True),
    )

    def new_paste(self, *args, **kwargs):
        return PastebinPaste(*args, **kwargs)

    def can_post(self, public=None):
        return 1

    def get_paste(self, _id):
        with self.browser:
            return self.browser.get_paste(_id)

    def fill_paste(self, paste, fields):
        # if we only want the contents
        if fields == ['contents']:
            if paste.contents is NotLoaded:
                with self.browser:
                    contents = self.browser.get_contents(paste.id)
                paste.contents = contents
        # get all fields
        elif fields is None or len(fields):
            with self.browser:
                self.browser.fill_paste(paste)
        return paste

    def post_paste(self, paste):
        with self.browser:
            if self.config['apikey']:
                self.browser.api_post_paste(self.config['apikey'], paste)
            else:
                self.browser.post_paste(paste)

    OBJECTS = {PastebinPaste: fill_paste}
