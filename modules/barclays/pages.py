# -*- coding: utf-8 -*-

# Copyright(C) 2012 Romain Bignon
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


import datetime
from decimal import Decimal
import re

from weboob.tools.browser import BasePage
from weboob.capabilities.bank import Account
from weboob.tools.capabilities.bank.transactions import FrenchTransaction


__all__ = ['LoginPage', 'Login2Page', 'IndexPage', 'AccountsPage', 'TransactionsPage',
           'CardPage', 'ValuationPage', 'LoanPage']


class LoginPage(BasePage):
    def login(self, login, passwd):
        self.browser.select_form(name='frmLogin')
        self.browser['username'] = login.encode(self.browser.ENCODING)
        self.browser['password'] = passwd.encode(self.browser.ENCODING)
        self.browser.submit(nologin=True)

    def has_redirect(self):
        if len(self.document.getroot().xpath('//form')) > 0:
            return False
        else:
            return True

class Login2Page(BasePage):
    def login(self, secret):
        label = self.document.xpath('//span[@class="PF_LABEL"]')[0].text.strip()
        letters = ''
        for n in re.findall('(\d+)', label):
            letters += secret[int(n) - 1]

        self.browser.select_form(name='frmControl')
        self.browser['word'] = letters
        self.browser.submit(name='valider', nologin=True)

class IndexPage(BasePage):
    pass

class AccountsPage(BasePage):
    ACCOUNT_TYPES = {u'Epargne':                Account.TYPE_SAVINGS,
                     u'Liquidités':             Account.TYPE_CHECKING,
                     u'Titres':                 Account.TYPE_MARKET,
                     u'Prêts':                  Account.TYPE_LOAN,
                    }

    def get_list(self):
        accounts = []

        for block in self.document.xpath('//div[@class="pave"]/div'):
            head_type = block.xpath('./div/span[@class="accGroupLabel"]')[0].text.strip()
            account_type = self.ACCOUNT_TYPES.get(head_type, Account.TYPE_UNKNOWN)
            for tr in block.cssselect('ul li.tbord_account'):
                id = tr.attrib.get('id', '')
                if id.find('contratId') != 0:
                    self.logger.warning('Unable to parse contract ID: %r' % id)
                    continue
                id = id[id.find('contratId')+len('contratId'):]

                link = tr.cssselect('span.accountLabel a')[0]
                balance = Decimal(FrenchTransaction.clean_amount(tr.cssselect('span.accountTotal')[0].text))

                if id.endswith('CRT'):
                    account = accounts[-1]
                    account._card_links.append(link.attrib['href'])
                    if not account.coming:
                        account.coming = Decimal('0.0')
                    account.coming += balance
                    continue

                account = Account()
                account.id = id
                account.label = unicode(link.text.strip())
                account.type = account_type
                account.balance = balance
                account.currency = account.get_currency(tr.cssselect('span.accountDev')[0].text)
                account._link = link.attrib['href']
                account._card_links = []
                accounts.append(account)

        return accounts


class Transaction(FrenchTransaction):
    PATTERNS = [(re.compile('^RET DAB (?P<text>.*?) RETRAIT DU (?P<dd>\d{2})(?P<mm>\d{2})(?P<yy>\d{2}).*'),
                                                              FrenchTransaction.TYPE_WITHDRAWAL),
                (re.compile('^RET DAB (?P<text>.*?) CARTE ?:.*'),
                                                              FrenchTransaction.TYPE_WITHDRAWAL),
                (re.compile('^RET DAB (?P<dd>\d{2})/(?P<mm>\d{2})/(?P<yy>\d{2}) (?P<text>.*?) CARTE .*'),
                                                              FrenchTransaction.TYPE_WITHDRAWAL),
                (re.compile('^(?P<text>.*) RETRAIT DU (?P<dd>\d{2})(?P<mm>\d{2})(?P<yy>\d{2}) .*'),
                                                              FrenchTransaction.TYPE_WITHDRAWAL),
                (re.compile('(\w+) (?P<dd>\d{2})(?P<mm>\d{2})(?P<yy>\d{2}) CB[:\*][^ ]+ (?P<text>.*)'),
                                                              FrenchTransaction.TYPE_CARD),
                (re.compile('^(?P<category>VIR(EMEN)?T? (SEPA)?(RECU|FAVEUR)?)( /FRM)?(?P<text>.*)'),
                                                              FrenchTransaction.TYPE_TRANSFER),
                (re.compile('^PRLV (?P<text>.*) (REF \w+)?$'),FrenchTransaction.TYPE_ORDER),
                (re.compile('^CHEQUE.*? (REF \w+)?$'),        FrenchTransaction.TYPE_CHECK),
                (re.compile('^(AGIOS /|FRAIS) (?P<text>.*)'), FrenchTransaction.TYPE_BANK),
                (re.compile('^(CONVENTION \d+ )?COTIS(ATION)? (?P<text>.*)'),
                                                              FrenchTransaction.TYPE_BANK),
                (re.compile('^REMISE (?P<text>.*)'),          FrenchTransaction.TYPE_DEPOSIT),
                (re.compile('^(?P<text>.*)( \d+)? QUITTANCE .*'),
                                                              FrenchTransaction.TYPE_ORDER),
                (re.compile('^.* LE (?P<dd>\d{2})/(?P<mm>\d{2})/(?P<yy>\d{2})$'),
                                                              FrenchTransaction.TYPE_UNKNOWN),
               ]


class TransactionsPage(BasePage):
    def get_history(self):
        for tr in self.document.xpath('//table[@id="operation"]/tbody/tr'):
            tds = tr.findall('td')

            if len(tds) < 5:
                continue

            t = Transaction(tds[-1].findall('img')[-1].attrib.get('id', ''))

            date = u''.join([txt.strip() for txt in tds[0].itertext()])
            raw = u' '.join([txt.strip() for txt in tds[1].itertext()])
            debit = u''.join([txt.strip() for txt in tds[-3].itertext()])
            credit = u''.join([txt.strip() for txt in tds[-2].itertext()])
            t.parse(date, re.sub(r'[ ]+', ' ', raw))
            t.set_amount(credit, debit)
            t._coming = False

            if t.raw.startswith('ACHAT CARTE -DEBIT DIFFERE'):
                continue

            yield t


class CardPage(BasePage):
    def get_history(self):
        debit_date = None
        coming = True
        for tr in self.document.xpath('//table[@class="report"]/tbody/tr'):
            tds = tr.findall('td')

            if len(tds) == 2:
                # headers
                m = re.match('.* (\d+)/(\d+)/(\d+)', tds[0].text.strip())
                debit_date = datetime.date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
                if debit_date < datetime.date.today():
                    coming = False

            if len(tds) != 3:
                continue

            t = Transaction(0)
            date = u''.join([txt.strip() for txt in tds[0].itertext()])
            raw = u' '.join([txt.strip() for txt in tds[1].itertext()])
            amount = u''.join([txt.strip() for txt in tds[-1].itertext()])
            t.parse(date, re.sub(r'[ ]+', ' ', raw))
            if debit_date is not None:
                t.date = debit_date
            t.label = unicode(tds[1].find('span').text.strip())
            t.type = t.TYPE_CARD
            t._coming = coming
            t.set_amount(amount)
            yield t

class ValuationPage(BasePage):
    def get_history(self):
        return iter([])

class LoanPage(BasePage):
    def get_history(self):
        return iter([])
