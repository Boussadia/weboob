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


from weboob.tools.browser import BasePage


__all__ = ['LoginPage']


class LoginPage(BasePage):
    def login(self, login, password):
        self.browser.select_form(nr=0)
#        self.browser['internal'] = 'P'
        self.browser['username'] = login
        self.browser['password'] = password
        self.browser['remember-me'] = ['on']
#        self.browser['identifier'] = ''
        self.browser.submit()
