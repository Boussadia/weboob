# -*- coding: utf-8 -*-

# Copyright(C) 2010-2013  Romain Bignon, Pierre Mazière, Noé Rubinstein
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

from decimal import Decimal

from weboob.capabilities.bank import Account
from weboob.tools.browser import BasePage
from weboob.tools.capabilities.bank.transactions import FrenchTransaction

from ..pages import Transaction


class RootPage(BasePage):
    pass


class LogoutPage(BasePage):
    pass


class LogoutOkPage(BasePage):
    pass


class MessagesPage(BasePage):
    pass


class AlreadyConnectedPage(BasePage):
    pass


class ExpiredPage(BasePage):
    pass


class MovementsPage(BasePage):
    def get_account(self):
        LABEL_XPATH = '//*[@id="perimetreMandatEnfantLib"]'
        BALANCE_XPATH = '//div[contains(text(),"Solde comptable :")]/strong'

        account = Account()

        account.id = 0
        account.label = self.document.xpath(LABEL_XPATH)[0] \
            .text_content().strip()
        balance_txt = self.document.xpath(BALANCE_XPATH)[0] \
            .text_content().strip()
        account.balance = Decimal(FrenchTransaction.clean_amount(balance_txt))
        account.currency = Account.get_currency(balance_txt)

        return account

    def get_operations(self):
        LINE_XPATH = '//table[@id="listeEffets"]/tbody/tr'

        for line in self.document.xpath(LINE_XPATH):
            _id = line.xpath('./@id')[0]
            tds = line.xpath('./td')

            [date, vdate, raw, debit, credit] = [td.text_content() for td in tds]

            operation = Transaction(_id)
            operation.parse(date=date, raw=raw)
            operation.set_amount(credit, debit)

            yield operation


class HomePage(BasePage):
    def login(self, login, passwd):
        p = lambda f: f.attrs.get('id') == "form_autoComplete"
        self.browser.select_form(predicate=p)
        self.browser["Ident_identifiant_"] = login.encode('utf-8')
        self.browser["Ident_password_"] = passwd.encode('utf-8')
        self.browser.submit(nologin=True)
