# -*- coding: utf-8 -*-

# Copyright(C) 2010-2011 Romain Bignon, Florent Fourcot
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


# python2.5 compatibility
from __future__ import with_statement

from weboob.capabilities.bank import ICapBank, AccountNotFound, Account
from weboob.tools.backend import BaseBackend, BackendConfig
from weboob.tools.value import ValueBackendPassword

from .browser import Ing


__all__ = ['INGBackend']


class INGBackend(BaseBackend, ICapBank):
    NAME = 'ing'
    MAINTAINER = 'Florent Fourcot'
    EMAIL = 'weboob@flo.fourcot.fr'
    VERSION = '0.d'
    LICENSE = 'AGPLv3+'
    DESCRIPTION = 'ING Direct French bank website'
    CONFIG = BackendConfig(ValueBackendPassword('login',
                                                label='Account ID',
                                                masked=False),
                           ValueBackendPassword('password',
                                                label='Password',
                                                regexp='^(\d{6}|)$'),
                           ValueBackendPassword('birthday',
                                                label='Birthday',
                                                regexp='^(\d{8}|)$',
                                                masked=False)
                          )
    BROWSER = Ing

    def create_default_browser(self):
        return self.create_browser(self.config['login'].get(),
                                   self.config['password'].get(),
                                   birthday=self.config['birthday'].get())

    def iter_accounts(self):
        for account in self.browser.get_accounts_list():
            yield account

    def get_account(self, _id):
        with self.browser:
            account = self.browser.get_account(_id)
        if account:
            return account
        else:
            raise AccountNotFound()

    def iter_history(self, account):
        with self.browser:
            for history in self.browser.get_history(account.id):
                yield history

    def iter_transfer_recipients(self, account):
        with self.browser:
            if not isinstance(account, Account):
                account = self.get_account(account)
            for recipient in self.browser.get_recipients(account):
                yield recipient

    def transfer(self, account, recipient, amount, reason):
        with self.browser:
            if not isinstance(account, Account):
                account = self.get_account(account)
            return self.browser.transfer(account, recipient, amount, reason)
