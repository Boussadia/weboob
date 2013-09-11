# -*- coding: utf-8 -*-

# Copyright(C) 2009-2011  Romain Bignon, Florent Fourcot
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
import urllib
import hashlib

from weboob.tools.browser import BaseBrowser, BrowserIncorrectPassword
from weboob.capabilities.bank import Account, TransferError
from .pages import AccountsList, LoginPage, \
                   TransferPage, TransferConfirmPage, \
                   BillsPage, StopPage, TitrePage, \
                   TitreHistory


__all__ = ['Ing']


class Ing(BaseBrowser):
    DOMAIN = 'secure.ingdirect.fr'
    PROTOCOL = 'https'
    DEBUG_HTTP = False
    #DEBUG_HTTP = True
    ENCODING = None
    PAGES = {'.*pages/index.jsf.*':            AccountsList,
             '.*displayLogin.jsf.*':           LoginPage,
             '.*transferManagement.jsf':       TransferPage,
             '.*onHoldTransferManagement.jsf': TransferPage,
             '.*DisplayDoTransferCommand.*':   TransferPage,
             '.*transferCreateValidation.jsf': TransferConfirmPage,
             '.*eStatement.jsf':               BillsPage,
             '.*displayCoordonneesCommand.*':  StopPage,
             '.*portefeuille-TR.*':            (TitrePage, 'raw'),
             '.*compteTempsReelCK.php.*':      (TitrePage, 'raw'),
             '.*compte.php\?ong=3':            TitreHistory,
            }
    CERTHASH = "257100e5f69b3c24b27eaaa82951ca5539e9ca264dee433b7c8d4779e778a0b4"

    loginpage = '/public/displayLogin.jsf'
    accountspage = '/protected/pages/index.jsf'
    transferpage = '/protected/pages/cc/transfer/transferManagement.jsf'
    dotransferpage = '/general?command=DisplayDoTransferCommand'
    valtransferpage = '/protected/pages/cc/transfer/create/transferCreateValidation.jsf'
    billpage = '/protected/pages/common/estatement/eStatement.jsf'
    titrepage = 'https://bourse.ingdirect.fr/priv/portefeuille-TR.php'
    where = None

    def __init__(self, *args, **kwargs):
        self.birthday = kwargs.pop('birthday', None)
        BaseBrowser.__init__(self, *args, **kwargs)

    def home(self):
        self.location(self.loginpage)

    def is_logged(self):
        return not self.is_on_page(LoginPage)

    def login(self):
        assert isinstance(self.username, basestring)
        assert isinstance(self.password, basestring)
        assert isinstance(self.birthday, basestring)
        assert self.password.isdigit()
        assert self.birthday.isdigit()

        if not self.is_on_page(LoginPage):
            self.location(self.loginpage)

        self.page.prelogin(self.username, self.birthday)
        self.page.login(self.password)
        if self.page.error():
            raise BrowserIncorrectPassword()

    def get_accounts_list(self):
        if not self.is_on_page(AccountsList) or self.where != "start":
            self.location(self.accountspage)
        self.where = "start"
        return self.page.get_list()

    def get_account(self, id):
        assert isinstance(id, basestring)

        if not self.is_on_page(AccountsList) or self.where != "start":
            self.location(self.accountspage)
        self.where = "start"

        l = self.page.get_list()
        for a in l:
            if a.id == id:
                return a

        return None

    def viewing_html(self):
        # To prevent unknown mimetypes sent by server, we assume we
        # are always on a HTML document.
        return True

    def get_history(self, account):
        if not isinstance(account, Account):
            account = self.get_account(account)
        if account.type == Account.TYPE_MARKET:
            for tr in self.get_history_titre(account):
                yield tr
            return
        elif account.type != Account.TYPE_CHECKING and\
                account.type != Account.TYPE_SAVINGS:
            raise NotImplementedError()

        if self.where != "start":
            self.location(self.accountspage)
        data = {"AJAX:EVENTS_COUNT": 1,
                "AJAXREQUEST": "_viewRoot",
                "ajaxSingle": "index:setAccount",
                "autoScroll": "",
                "index": "index",
                "index:setAccount": "index:setAccount",
                "javax.faces.ViewState": account._jid,
                "cptnbr": account._id
                }
        self.location(self.accountspage, urllib.urlencode(data))
        self.where = "history"
        jid = self.page.get_history_jid()
        if jid is None:
            self.logger.info('There is no history for this account')
            return

        index = 0 # index, we get always the same page, but with more informations
        hashlist = []
        while True:
            i = index
            for transaction in self.page.get_transactions(index):
                while transaction.id in hashlist:
                    transaction.id = hashlib.md5(transaction.id + "1").hexdigest()
                hashlist.append(transaction.id)
                i += 1
                yield transaction
            # if there is no more transactions, it is useless to continue
            if i == index or self.page.islast():
                return
            index = i
            data = {"AJAX:EVENTS_COUNT": 1,
                    "AJAXREQUEST": "_viewRoot",
                    "autoScroll": "",
                    "index": "index",
                    "index:%s:moreTransactions" % jid: "index:%s:moreTransactions" % jid,
                    "javax.faces.ViewState": account._jid
                    }
            self.location(self.accountspage, urllib.urlencode(data))

    def get_recipients(self, account):
        if not self.is_on_page(TransferPage):
            self.location(self.transferpage)
        if self.page.ischecked(account):
            return self.page.get_recipients()
        else:
            # It is hard to check the box and to get the real list.
            # We try an alternative way like normal users
            self.get_history(account.id).next()
            self.location(self.dotransferpage)
            return self.page.get_recipients()

    def transfer(self, account, recipient, amount, reason):
        found = False
        # Automatically get the good transfer page
        self.logger.debug('Search %s' % recipient)
        for destination in self.get_recipients(account):
            self.logger.debug('Found %s ' % destination.id)
            if destination.id == recipient:
                found = True
                recipient = destination
                break
        if found:
            self.openurl(self.transferpage,
                    self.page.buildonclick(recipient, account))
            self.page.transfer(recipient, amount, reason)
            self.location(self.valtransferpage)
            if not self.is_on_page(TransferConfirmPage):
                raise TransferError("Invalid transfer (no confirmation page)")
            else:
                self.page.confirm(self.password)
                self.location(self.valtransferpage)
                return self.page.recap()
        else:
            raise TransferError('Recipient not found')

    def go_investments(self, account):
        if self.where != "start":
            self.location(self.accountspage)
        data = {"AJAX:EVENTS_COUNT": 1,
                "AJAXREQUEST": "_viewRoot",
                "ajaxSingle": "index:setAccount",
                "autoScroll": "",
                "index": "index",
                "index:setAccount": "index:setAccount",
                "javax.faces.ViewState": account._jid,
                "cptnbr": account._id
                }
        self.location(self.accountspage, urllib.urlencode(data))
        self.location('https://secure.ingdirect.fr/general?command=goToAccount&zone=COMPTE')
        self.where = "titre"

        self.location(self.titrepage)

    def get_investments(self, account):
        if account.type != Account.TYPE_MARKET:
            raise NotImplementedError()
        self.go_investments(account)

        self.location('https://bourse.ingdirect.fr/streaming/compteTempsReelCK.php')
        return self.page.iter_investments()

    def get_history_titre(self, account):
        self.go_investments(account)
        self.location('https://bourse.ingdirect.fr/priv/compte.php?ong=3')
        return self.page.iter_history()

    def get_subscriptions(self):
        self.location('/protected/pages/common/estatement/eStatement.jsf')
        return self.page.iter_account()

    def get_bills(self, subscription):
        if not self.is_on_page(BillsPage):
            self.location(self.billpage)
        data = {"AJAXREQUEST": "_viewRoot",
                "accountsel_form": "accountsel_form",
                subscription._formid: subscription._formid,
                "autoScroll": "",
                "javax.faces.ViewState": subscription._javax,
                "transfer_issuer_radio": subscription.id
               }
        self.location(self.billpage, urllib.urlencode(data))
        while True:
            for bill in self.page.iter_bills(subscription.id):
                yield bill
            if self.page.islast():
                return

            self.page.next_page()

    def predownload(self, bill):
        self.page.postpredown(bill._localid)
