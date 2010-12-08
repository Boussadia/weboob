# -*- coding: utf-8 -*-

# Copyright(C) 2010  Nicolas Duhamel
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


import re

from weboob.capabilities.bank import TransferError
from weboob.tools.browser import BasePage
from weboob.tools.misc import to_unicode


__all__ = ['TransferChooseAccounts', 'CompleteTransfer', 'TransferConfirm', 'TransferSummary']


class TransferChooseAccounts(BasePage):
    def set_accouts(self, from_account, to_account):
        self.browser.select_form(name="AiguillageForm")
        self.browser["idxCompteEmetteur"] = [from_account.id]
        self.browser["idxCompteReceveur"] = [to_account.id]
        self.browser.submit()


class CompleteTransfer(BasePage):
    def complete_transfer(self, amount):
        self.browser.select_form(name="VirementNationalForm")
        self.browser["montant"] = str(amount)
        self.browser.submit()


class TransferConfirm(BasePage):
    def confirm(self):
        self.browser.location('https://voscomptesenligne.labanquepostale.fr/voscomptes/canalXHTML/virementsafran/'
            'virementnational/4-virementNational.ea')


class TransferSummary(BasePage):
    def get_transfer_id(self):
        p = self.document.xpath("//form/div/p")[0]

        #HACK for deal with bad encoding ...
        try:
            text = p.text
        except UnicodeDecodeError, error:
            text = error.object.strip()

        match = re.search("Votre virement N.+ ([0-9]+) ", text)
        if match:
            id_transfer = match.groups()[0]
            return id_transfer

        if text.startswith(u"Votre virement n'a pas pu"):
            if p.find('br') is not None:
                errmsg = to_unicode(p.find('br').tail).strip()
                raise TransferError('Unable to process transfer: %s' % errmsg)
            else:
                self.browser.logger.warning('Unable to find the error reason')

        self.browser.logger.error('Unable to parse the text result: %r' % text)
        raise TransferError('Unable to process transfer: %r' % text)
