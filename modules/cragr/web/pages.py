# -*- coding: utf-8 -*-

# Copyright(C) 2013  Romain Bignon
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
from decimal import Decimal

from weboob.capabilities.bank import Account
from weboob.tools.browser import BasePage
from weboob.tools.capabilities.bank.transactions import FrenchTransaction as Transaction


__all__ = ['HomePage', 'LoginPage', 'LoginErrorPage', 'AccountsPage', 'TransactionsPage']


class HomePage(BasePage):
    def get_post_url(self):
        for script in self.document.xpath('//script'):
            text = script.text
            if text is None or not 'CCPTE' in text:
                continue

            m = re.search(r'var chemin = "([^"]+)"', text, re.MULTILINE)
            if m:
                return m.group(1)

        return None

class LoginPage(BasePage):
    def login(self, password):
        assert password.isdigit()
        assert len(password) == 6

        imgmap = {}
        for td in self.document.xpath('//table[@id="pave-saisie-code"]/tr/td'):
            a = td.find('a')
            num = a.text.strip()
            if num.isdigit():
                imgmap[num] = int(a.attrib['tabindex']) - 1

        self.browser.select_form(name='formulaire')
        self.browser.set_all_readonly(False)
        self.browser['CCCRYC'] = ','.join(['%02d' % imgmap[c] for c in password])
        self.browser['CCCRYC2'] = '0' * len(password)
        self.browser.submit(nologin=True)

    def get_result_url(self):
        return self.parser.tocleanstring(self.document.getroot())

class LoginErrorPage(BasePage):
    pass

class _AccountsPage(BasePage):
    COL_LABEL    = 0
    COL_ID       = 2
    COL_VALUE    = 4
    COL_CURRENCY = 5

    def get_list(self):
        for tr in self.document.xpath('//table[@class="ca-table"]/tr'):
            if not tr.attrib.get('class', '').startswith('colcelligne'):
                continue

            cols = tr.findall('td')
            if not cols:
                continue

            account = Account()
            account.id = self.parser.tocleanstring(cols[self.COL_ID])
            account.label = self.parser.tocleanstring(cols[self.COL_LABEL])
            account.balance = Decimal(Transaction.clean_amount(self.parser.tocleanstring(cols[self.COL_VALUE])))
            account.currency = account.get_currency(self.parser.tocleanstring(cols[self.COL_CURRENCY]))
            account._link = None

            a = cols[0].find('a')
            if a is not None:
                account._link = a.attrib['href'].replace(' ', '%20')

            yield account

class AccountsPage(_AccountsPage):
    pass

class SavingsPage(_AccountsPage):
    COL_ID       = 1

class TransactionsPage(BasePage):
    def get_next_url(self):
        links = self.document.xpath('//span[@class="pager"]/a[@class="liennavigationcorpspage"]')
        if len(links) < 1:
            return None

        img = links[-1].find('img')
        if img.attrib.get('alt', '') == 'Page suivante':
            return links[-1].attrib['href']

        return None

    COL_DATE  = 0
    COL_TEXT  = 1
    COL_DEBIT = None
    COL_CREDIT = -1

    TYPES = {'Paiement Par Carte':          Transaction.TYPE_CARD,
             'Retrait Au Distributeur':     Transaction.TYPE_WITHDRAWAL,
             'Frais':                       Transaction.TYPE_BANK,
             'Cotisation':                  Transaction.TYPE_BANK,
             'Virement Emis':               Transaction.TYPE_TRANSFER,
             'Virement':                    Transaction.TYPE_TRANSFER,
             'Cheque Emis':                 Transaction.TYPE_CHECK,
             'Remise De Cheque':            Transaction.TYPE_DEPOSIT,
             'Prelevement':                 Transaction.TYPE_ORDER,
            }

    def get_history(self, date_guesser):
        i = 0
        for tr in self.document.xpath('//table[@class="ca-table"]//tr'):
            parent = tr.getparent()
            while parent is not None and parent.tag != 'table':
                parent = parent.getparent()

            if parent.attrib.get('class', '') != 'ca-table':
                continue

            if tr.attrib.get('class', '') == 'tr-thead':
                heads = tr.findall('th')
                for i, head in enumerate(heads):
                    key = self.parser.tocleanstring(head)
                    if key == u'Débit':
                        self.COL_DEBIT = i - len(heads)
                    if key == u'Crédit':
                        self.COL_CREDIT = i - len(heads)
                    if key == u'Libellé':
                        self.COL_TEXT = i

            if not tr.attrib.get('class', '').startswith('ligne-'):
                continue

            cols = tr.findall('td')

            # On loan accounts, there is a ca-table with a summary. Skip it.
            if tr.find('th') is not None or len(cols) < 3:
                continue

            t = Transaction(i)

            date = self.parser.tocleanstring(cols[self.COL_DATE])
            raw = self.parser.tocleanstring(cols[self.COL_TEXT])
            credit = self.parser.tocleanstring(cols[self.COL_CREDIT])
            if self.COL_DEBIT is not None:
                debit =  self.parser.tocleanstring(cols[self.COL_DEBIT])
            else:
                debit = ''

            day, month = map(int, date.split('/', 1))
            t.date = date_guesser.guess_date(day, month)
            t.rdate = t.date
            t.raw = raw

            # On some accounts' history page, there is a <font> tag in columns.
            col_text = cols[self.COL_TEXT]
            if col_text.find('font') is not None:
                col_text = col_text.find('font')

            t.category = unicode(col_text.text.strip())
            t.label = col_text.find('br').tail
            if t.label is not None:
                t.label = t.label.strip()
            else:
                # If there is only one line, try to separate category from label.
                t.label = re.sub('(.*)  (.*)', r'\2', t.category).strip()
            # Sometimes, the category contains the label, even if there is another line with it again.
            t.category = re.sub('(.*)  .*', r'\1', t.category).strip()

            t.type = self.TYPES.get(t.category, t.TYPE_UNKNOWN)

            # Parse operation date in label (for card transactions for example)
            m = re.match('(.*) (\d{2})/(\d{2})$', t.label)
            if m:
                if t.type == t.TYPE_CARD:
                    t.rdate = date_guesser.guess_date(int(m.group(2)), int(m.group(3)), change_current_date=False)
                t.label = m.group(1).strip()

            # Strip city or other useless information from label.
            t.label = re.sub('(.*)  .*', r'\1', t.label).strip()
            t.set_amount(credit, debit)
            yield t

            i += 1
