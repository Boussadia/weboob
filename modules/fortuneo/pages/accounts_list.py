# -*- coding: utf-8 -*-

# Copyright(C) 2012 Gilles-Alexandre Quenot
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
import re
import datetime

from weboob.capabilities.bank import Account
from weboob.tools.browser import BasePage#, BrokenPageError
from weboob.capabilities import NotAvailable
from weboob.tools.capabilities.bank.transactions import FrenchTransaction


__all__ = ['AccountsList', 'AccountHistoryPage']


class Transaction(FrenchTransaction):
    PATTERNS = [(re.compile(u'^(?P<category>CHEQUE)(?P<text>.*)'),        FrenchTransaction.TYPE_CHECK),
                (re.compile('^(?P<category>FACTURE CARTE) DU (?P<dd>\d{2})(?P<mm>\d{2})(?P<yy>\d{2}) (?P<text>.*?)( CA?R?T?E? ?\d*X*\d*)?$'),
                                                            FrenchTransaction.TYPE_CARD),
                (re.compile('^(?P<category>(PRELEVEMENT|TELEREGLEMENT|TIP)) (?P<text>.*)'),
                                                            FrenchTransaction.TYPE_ORDER),
                (re.compile('^(?P<category>ECHEANCEPRET)(?P<text>.*)'),   FrenchTransaction.TYPE_LOAN_PAYMENT),
                (re.compile('^(?P<category>RETRAIT DAB) (?P<dd>\d{2})/(?P<mm>\d{2})/(?P<yy>\d{2})( (?P<HH>\d+)H(?P<MM>\d+))? (?P<text>.*)'),
                                                            FrenchTransaction.TYPE_WITHDRAWAL),
                (re.compile('^(?P<category>VIR(EMEN)?T? ((RECU|FAVEUR) TIERS|SEPA RECU)?)( /FRM)?(?P<text>.*)'),
                                                            FrenchTransaction.TYPE_TRANSFER),
                (re.compile('^(?P<category>REMBOURST)(?P<text>.*)'),     FrenchTransaction.TYPE_PAYBACK),
                (re.compile('^(?P<category>COMMISSIONS)(?P<text>.*)'),   FrenchTransaction.TYPE_BANK),
                (re.compile('^(?P<text>(?P<category>REMUNERATION).*)'),   FrenchTransaction.TYPE_BANK),
                (re.compile('^(?P<category>REMISE CHEQUES)(?P<text>.*)'), FrenchTransaction.TYPE_DEPOSIT),
               ]

class AccountHistoryPage(BasePage):
    def get_operations(self, _id):
        """history, see http://docs.weboob.org/api/capabilities/bank.html?highlight=transaction#weboob.capabilities.bank.Transaction"""

        # TODO need to rewrite that with FrenchTransaction class http://tinyurl.com/6lq4r9t
        operations = []
        tables = self.document.findall(".//*[@id='tabHistoriqueOperations']/tbody/tr")

        if len(tables) == 0:
            return []

        for i in range(len(tables)):
            operation = Transaction(len(operations))
            operation.type  = 0
            operation.category  = NotAvailable

            date_oper       = tables[i].xpath("./td[2]/text()")[0]
            date_val        = tables[i].xpath("./td[3]/text()")[0]
            label           = tables[i].xpath("./td[4]/text()")[0]
            amount          = tables[i].xpath("./td[5]/text() | ./td[6]/text()")

            operation.parse(date=date_val, raw=label)
            operation.rdate = datetime.datetime.strptime(date_oper,"%d/%m/%Y")

            if amount[1] == u'\xa0':
                amount = amount[0]
            else:
                amount = amount[1]

            operation.set_amount(amount)

            operations.append(operation)

        return operations

class AccountsList(BasePage):
    def get_list(self):
        l = []

        for cpt in self.document.xpath(".//*[@class='synthese_id_compte']"):
            account = Account()

            # account.id
            account.id = cpt.xpath("./span[1]/text()")[0].replace(u"\xa0", "").replace(',', '.').replace("EUR", "").replace("\n", "").replace("\t", "").replace(u"\xb0", '').replace(" ", "").replace('N', '')

            # account balance
            account.balance = Decimal(Transaction.clean_amount(cpt.xpath("./span[2]/text()")[0]))
            account.currency = account.get_currency(cpt.xpath("./span[2]/text()")[0])

            # account coming TODO
            #mycomingval = cpt.xpath("../../following-sibling::*[1]/td[2]/a[@class='lien_synthese_encours']/span/text()")[0].replace(',', '.').replace("EUR", "").replace("\n", "").replace("\t", "").replace(u"\xa0", "")
            #mycomingval = cpt.xpath("../../following-sibling::*[1]/td[2]")[0]
            #mycomingval = cpt.xpath("./../../../a[@class='lien_synthese_encours']/span[@class='synthese_encours']/text()")[0].replace(',', '.').replace("EUR", "").replace("\n", "").replace("\t", "").replace(u"\xa0", "")

            #if mycomingval == '-':
            #    account.coming = Decimal(0)
            #else:
            #    account.coming = Decimal(mycomingval)

            url_to_parse = cpt.xpath('@href')[0].replace("\n", "")  # link

            # account._link_id = lien vers historique d'un compte (courant of livret)
            if '/mes-comptes/livret/' in url_to_parse:
                compte_id_re = re.compile(r'.*\?(.*)$')
                account._link_id = '/fr/prive/mes-comptes/livret/consulter-situation/consulter-solde.jsp?%s' % \
                    (compte_id_re.search(url_to_parse).groups()[0])
            else:
                account._link_id = url_to_parse

            # account.label
            temp_label = cpt.xpath('./text()')[1].replace(u'-\xa0', '').replace("\n", "").replace("\t", "")
            account.label = " ".join(temp_label.split(" ")[:2])

            l.append(account)

        return l

# vim:ts=4:sw=4
