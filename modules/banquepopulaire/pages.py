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


from urlparse import urlsplit, parse_qsl
from decimal import Decimal
import re
from mechanize import Cookie

from weboob.tools.browser import BasePage, BrowserUnavailable, BrokenPageError
from weboob.capabilities.bank import Account
from weboob.tools.capabilities.bank.transactions import FrenchTransaction


__all__ = ['LoginPage', 'IndexPage', 'AccountsPage', 'TransactionsPage', 'UnavailablePage', 'RedirectPage']


class WikipediaARC4(object):
    def __init__(self, key = None):
        self.state = range(256)
        self.x = self.y = 0

        if key is not None:
            self.init(key)

    def init(self, key):
        for i in range(256):
            self.x = (ord(key[i % len(key)]) + self.state[i] + self.x) & 0xFF
            self.state[i], self.state[self.x] = self.state[self.x], self.state[i]
        self.x = 0

    def crypt(self, input):
        output = [None]*len(input)
        for i in xrange(len(input)):
            self.x = (self.x + 1) & 0xFF
            self.y = (self.state[self.x] + self.y) & 0xFF
            self.state[self.x], self.state[self.y] = self.state[self.y], self.state[self.x]
            output[i] = chr((ord(input[i]) ^ self.state[(self.state[self.x] + self.state[self.y]) & 0xFF]))
        return ''.join(output)

class RedirectPage(BasePage):
    """
    var i = 'lyhrnu551jo42yfzx0jm0sqk';
    setCookie('i', i);
    var welcomeMessage = decodeURI('M MACHIN');
    var lastConnectionDate = decodeURI('17 Mai 2013');
    var lastConnectionTime = decodeURI('14h27');
    var userId = '12345678';
    var userCat = '1';
    setCookie('uwm', $.rc4EncryptStr(welcomeMessage, i));
    setCookie('ulcd', $.rc4EncryptStr(lastConnectionDate, i));
    setCookie('ulct', $.rc4EncryptStr(lastConnectionTime, i));
    setCookie('uid', $.rc4EncryptStr(userId, i));
    setCookie('uc', $.rc4EncryptStr(userCat, i));
    var agentCivility = 'Mlle';
    var agentFirstName = decodeURI('Jeanne');
    var agentLastName = decodeURI('Machin');
    var agentMail = decodeURI('gary@example.org');
    setCookie('ac', $.rc4EncryptStr(agentCivility, i));
    setCookie('afn', $.rc4EncryptStr(agentFirstName, i));
    setCookie('aln', $.rc4EncryptStr(agentLastName, i));
    setCookie('am', $.rc4EncryptStr(agentMail, i));
    var agencyLabel = decodeURI('DTC');
    var agencyPhoneNumber = decodeURI('0123456789');
    setCookie('al', $.rc4EncryptStr(agencyLabel, i));
    setCookie('apn', $.rc4EncryptStr(agencyPhoneNumber, i));

    Note: that cookies are useless to login on website
    """

    def add_cookie(self, name, value):
        c = Cookie(0, name, value,
                      None, False,
                      '.' + self.browser.DOMAIN, True, True,
                      '/', False,
                      False,
                      None,
                      False,
                      None,
                      None,
                      {})
        cookiejar = self.browser._ua_handlers["_cookies"].cookiejar
        cookiejar.set_cookie(c)

    def on_loaded(self):
        redirect_url = None
        args = {}
        RC4 = None
        for script in self.document.xpath('//script'):
            if script.text is None:
                continue

            m = re.search('window.location=\'([^\']+)\'', script.text, flags=re.MULTILINE)
            if m:
                redirect_url = m.group(1)

            for line in script.text.split('\r\n'):
                m = re.match("^var (\w+) = [^']*'([^']*)'.*", line)
                if m:
                    args[m.group(1)] = m.group(2)

                m = re.match("^setCookie\('([^']+)', (\w+)\);", line)
                if m:
                    self.add_cookie(m.group(1), args[m.group(2)])

                m = re.match("^setCookie\('([^']+)', .*rc4EncryptStr\((\w+), \w+\)", line)
                if m:
                    self.add_cookie(m.group(1), RC4.crypt(args[m.group(2)]).encode('hex'))

                if RC4 is None and 'i' in args:
                    RC4 = WikipediaARC4(args['i'])

        if redirect_url is not None:
            self.browser.location(self.browser.request_class(self.browser.absurl(redirect_url), None, {'Referer': self.url}))

class UnavailablePage(BasePage):
    def on_loaded(self):
        try:
            a = self.document.xpath('//a[@class="btn"]')[0]
        except IndexError:
            raise BrowserUnavailable()
        else:
            self.browser.location(a.attrib['href'])


class LoginPage(BasePage):
    def on_loaded(self):
        try:
            h1 = self.parser.select(self.document.getroot(), 'h1', 1)
        except BrokenPageError:
            pass

        if h1.text is not None and h1.text.startswith('Le service est moment'):
            try:
                raise BrowserUnavailable(self.document.xpath('//h4')[0].text)
            except KeyError:
                raise BrowserUnavailable(h1.text)

    def login(self, login, passwd):
        self.browser.select_form(name='Login')
        self.browser['IDToken1'] = login.encode(self.browser.ENCODING)
        self.browser['IDToken2'] = passwd.encode(self.browser.ENCODING)
        self.browser.submit(nologin=True)


class IndexPage(BasePage):
    def get_token(self):
        url = self.document.getroot().xpath('//frame[@name="portalHeader"]')[0].attrib['src']
        v = urlsplit(url)
        args = dict(parse_qsl(v.query))
        return args['token']


class HomePage(BasePage):
    def get_token(self):
        vary = self.group_dict['vary']

        #r = self.browser.openurl(self.browser.request_class(self.browser.buildurl(self.browser.absurl("/portailinternet/_layouts/Ibp.Cyi.Application/GetuserInfo.ashx"), action='UInfo', vary=vary), None, {'Referer': self.url}))
        #print r.read()

        r = self.browser.openurl(self.browser.request_class(self.browser.buildurl(self.browser.absurl('/portailinternet/Transactionnel/Pages/CyberIntegrationPage.aspx'), vary=vary), 'taskId=aUniversMesComptes', {'Referer': self.url}))
        doc = self.browser.get_document(r)
        date = None
        for script in doc.xpath('//script'):
            if script.text is None:
                continue

            m = re.search('lastConnectionDate":"([^"]+)"', script.text)
            if m:
                date = m.group(1)

        r = self.browser.openurl(self.browser.request_class(self.browser.absurl('/cyber/ibp/ate/portal/integratedInternet.jsp'), 'session%%3Aate.lastConnectionDate=%s&taskId=aUniversMesComptes' % date, {'Referer': r.geturl()}))
        v = urlsplit(r.geturl())
        args = dict(parse_qsl(v.query))
        return args['token']


class AccountsPage(BasePage):
    ACCOUNT_TYPES = {u'Mes comptes d\'épargne':     Account.TYPE_SAVINGS,
                     u'Mes comptes':                Account.TYPE_CHECKING,
                    }

    def is_error(self):
        for script in self.document.xpath('//script'):
            if script.text is not None and u"Le service est momentanément indisponible" in script.text:
                return True

        return False

    def get_list(self):
        account_type = Account.TYPE_UNKNOWN

        params = {}
        for field in self.document.xpath('//input'):
            params[field.attrib['name']] = field.attrib.get('value', '')

        for div in self.document.xpath('//div[@class="btit"]'):
            account_type = self.ACCOUNT_TYPES.get(div.text.strip(), Account.TYPE_UNKNOWN)

            for tr in div.getnext().xpath('.//tbody/tr'):
                if not 'id' in tr.attrib:
                    continue

                args = dict(parse_qsl(tr.attrib['id']))
                tds = tr.findall('td')

                if len(tds) < 4 or not 'identifiant' in args:
                    self.logger.warning('Unable to parse an account')
                    continue

                account = Account()
                account.id = args['identifiant']
                account.label = u' '.join([u''.join([txt.strip() for txt in tds[1].itertext()]),
                                           u''.join([txt.strip() for txt in tds[2].itertext()])]).strip()
                account.type = account_type
                balance = u''.join([txt.strip() for txt in tds[3].itertext()])
                account.balance = Decimal(FrenchTransaction.clean_amount(balance))
                account.currency = account.get_currency(balance)
                account._params = params.copy()
                account._params['dialogActionPerformed'] = 'SOLDE'
                account._params['attribute($SEL_$%s)' % tr.attrib['id'].split('_')[0]] = tr.attrib['id'].split('_', 1)[1]
                yield account

        return


class Transaction(FrenchTransaction):
    PATTERNS = [(re.compile('^RET DAB (?P<text>.*?) RETRAIT (DU|LE) (?P<dd>\d{2})(?P<mm>\d{2})(?P<yy>\d+).*'),
                                                            FrenchTransaction.TYPE_WITHDRAWAL),
                (re.compile('^RET DAB (?P<text>.*?) CARTE ?:.*'),
                                                            FrenchTransaction.TYPE_WITHDRAWAL),
                (re.compile('^(?P<text>.*) RETRAIT DU (?P<dd>\d{2})(?P<mm>\d{2})(?P<yy>\d{2}) .*'),
                                                            FrenchTransaction.TYPE_WITHDRAWAL),
                (re.compile('^(RETRAIT CARTE )?RET(RAIT)? DAB (?P<text>.*)'),
                                                            FrenchTransaction.TYPE_WITHDRAWAL),
                (re.compile('((\w+) )?(?P<dd>\d{2})(?P<mm>\d{2})(?P<yy>\d{2}) CB[:\*][^ ]+ (?P<text>.*)'),
                                                            FrenchTransaction.TYPE_CARD),
                (re.compile('^VIR(EMENT)? (?P<text>.*)'),   FrenchTransaction.TYPE_TRANSFER),
                (re.compile('^(PRLV|PRELEVEMENT) (?P<text>.*)'),
                                                            FrenchTransaction.TYPE_ORDER),
                (re.compile('^CHEQUE.*'),                   FrenchTransaction.TYPE_CHECK),
                (re.compile('^(AGIOS /|FRAIS) (?P<text>.*)', re.IGNORECASE),
                                                            FrenchTransaction.TYPE_BANK),
                (re.compile('^(CONVENTION \d+ )?COTIS(ATION)? (?P<text>.*)', re.IGNORECASE),
                                                            FrenchTransaction.TYPE_BANK),
                (re.compile('^REMISE (?P<text>.*)'),        FrenchTransaction.TYPE_DEPOSIT),
                (re.compile('^(?P<text>.*)( \d+)? QUITTANCE .*'),
                                                            FrenchTransaction.TYPE_ORDER),
                (re.compile('^.* LE (?P<dd>\d{2})/(?P<mm>\d{2})/(?P<yy>\d{2})$'),
                                                            FrenchTransaction.TYPE_UNKNOWN),
               ]


class TransactionsPage(BasePage):
    def get_next_params(self):
        nxt = self.document.xpath('//li[@id="tbl1_nxt"]')
        if len(nxt) == 0 or nxt[0].attrib.get('class', '') == 'nxt-dis':
            return None

        params = {}
        for field in self.document.xpath('//input'):
            params[field.attrib['name']] = field.attrib.get('value', '')

        params['validationStrategy'] = 'NV'
        params['pagingDirection'] = 'NEXT'
        params['pagerName'] = 'tbl1'

        return params

    def get_history(self):
        for tr in self.document.xpath('//table[@id="tbl1"]/tbody/tr'):
            tds = tr.findall('td')

            if len(tds) < 5:
                continue

            t = Transaction(tr.attrib['id'].split('_', 1)[1])

            date = u''.join([txt.strip() for txt in tds[4].itertext()])
            raw = u' '.join([txt.strip() for txt in tds[1].itertext()])
            debit = u''.join([txt.strip() for txt in tds[-2].itertext()])
            credit = u''.join([txt.strip() for txt in tds[-1].itertext()])
            t.parse(date, re.sub(r'[ ]+', ' ', raw))
            t.set_amount(credit, debit)
            yield t
