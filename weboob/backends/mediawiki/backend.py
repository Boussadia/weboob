# -*- coding: utf-8 -*-

# Copyright(C) 2011  Clément Schreiner
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

from weboob.tools.backend import BaseBackend
from weboob.capabilities.content import ICapContent, Content
from weboob.tools.value import ValuesDict, Value


from .browser import MediawikiBrowser


__all__ = ['MediawikiBackend']

class MediawikiBackend(BaseBackend, ICapContent):
    NAME = 'mediawiki'
    MAINTAINER = 'Clément Schreiner'
    EMAIL = '0.6'
    LICENSE = 'GPLv3'
    DESCRIPTION = 'Mediawiki wiki software application'
    CONFIG = ValuesDict(Value('url',      label='URL of the Mediawiki website'),
                        Value('apiurl',   label='URL of the Mediawiki website\'s API'),
                        Value('username', label='Login'),
                        Value('password', label='Password', masked=True))

    BROWSER = MediawikiBrowser
    def create_default_browser(self):
        return self.create_browser(self.config['url'], self.config['apiurl'], self.config['username'], self.config['password'])

    def get_content(self, _id):
        _id = _id.replace(' ', '_').encode('utf-8')
        content = Content(_id)
        page = _id
        with self.browser:
            data = self.browser.get_wiki_source(page)

        content.content = data
        return content

    def iter_revisions(self, _id):
        for rev in self.browser.iter_wiki_revisions(_id):
            yield rev
    

    def push_content(self, content, message=None, minor=False):
        self.browser.set_wiki_source(content, message, minor)

    def get_content_preview(self, content):
        return self.browser.get_wiki_preview(content)
