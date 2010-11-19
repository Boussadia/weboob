# -*- coding: utf-8 -*-

# Copyright(C) 2010  Christophe Benz
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


import urllib

from .pages.compose import ClosePage, ComposePage, ConfirmPage, SentPage
from .pages.login import LoginPage

from weboob.capabilities.messages import CantSendMessage
from weboob.tools.browser import BaseBrowser, BrowserIncorrectPassword


__all__ = ['SfrBrowser']


class SfrBrowser(BaseBrowser):
    DOMAIN = 'www.sfr.fr'
    PAGES = {
        'http://messagerie-.+.sfr.fr/webmail/close_xms_tab.html': ClosePage,
        'http://www.sfr.fr/xmscomposer/index.html\?todo=compose': ComposePage,
        'http://www.sfr.fr/xmscomposer/mc/envoyer-texto-mms/confirm.html': ConfirmPage,
        'https://www.sfr.fr/cas/login\?service=.*': LoginPage,
        'http://www.sfr.fr/xmscomposer/mc/envoyer-texto-mms/send.html': SentPage,
        }

    def home(self):
        self.location('http://www.sfr.fr/xmscomposer/index.html?todo=compose')

    def is_logged(self):
        return 'loginForm' not in [form.name for form in self.forms()]

    def login(self):
        service_url = 'http://www.sfr.fr/xmscomposer/j_spring_cas_security_check'
        self.location('https://www.sfr.fr/cas/login?service=%s' % urllib.quote_plus(service_url), no_login=True)
        self.page.login(self.username, self.password)
        if not self.is_logged():
            raise BrowserIncorrectPassword()

    def post_message(self, message):
        if not self.is_on_page(ComposePage):
            self.location('http://www.sfr.fr/xmscomposer/index.html\?todo=compose')
        self.page.post_message(message)
        if self.is_on_page(ConfirmPage):
            self.page.confirm()
        if self.is_on_page(ClosePage):
            raise CantSendMessage('Invalid receiver.')
