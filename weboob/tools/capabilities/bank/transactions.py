# -*- coding: utf-8 -*-

# Copyright(C) 2009-2012  Romain Bignon
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

from weboob.capabilities.bank import Transaction
from weboob.capabilities import NotAvailable
from weboob.tools.misc import to_unicode


__all__ = ['FrenchTransaction']


class FrenchTransaction(Transaction):
    """
    Transaction with some helpers for french bank websites.
    """
    PATTERNS = []

    def clean_amount(self, text):
        """
        Clean a string containing an amount.
        """
        return text.replace(' ', '').replace('.','') \
                   .replace(',','.').strip(u' \t\u20ac\xa0€\n\r')

    def set_amount(self, credit='', debit=''):
        """
        Set an amount value from a string.

        Can take two strings if there are both credit and debit
        columns.
        """
        credit = self.clean_amount(credit)
        debit = self.clean_amount(debit)

        if len(debit) > 0:
            self.amount = - Decimal(debit)
        else:
            self.amount = Decimal(credit)

    def parse(self, date, raw):
        """
        Parse date and raw strings to create datetime.date objects,
        determine the type of transaction, and create a simplified label

        When calling this method, you should have defined patterns (in the
        PATTERN class attribute) with a list containing tuples of regexp
        and the associated type, for example::

            PATTERNS = [(re.compile('^VIR(EMENT)? (?P<text>.*)'), FrenchTransaction.TYPE_TRANSFER),
                        (re.compile('^PRLV (?P<text>.*)'),        FrenchTransaction.TYPE_ORDER),
                        (re.compile('^(?P<text>.*) CARTE \d+ PAIEMENT CB (?P<dd>\d{2})(?P<mm>\d{2}) ?(.*)$'),
                                                                  FrenchTransaction.TYPE_CARD)
                       ]

        In regexps, you can define this patterns:

            * text: part of label to store in simplified label
            * yy, mm, dd, HH, MM: date and time parts
        """
        if not isinstance(date, (datetime.date, datetime.datetime)):
            if date.isdigit() and len(date) == 8:
                date = datetime.date(int(date[4:8]), int(date[2:4]), int(date[0:2]))
            elif '/' in date:
                date = datetime.date(*reversed([int(x) for x in date.split('/')]))

        self.date = date
        self.rdate = date
        self.raw = to_unicode(re.sub(u'[ ]+', u' ', raw.replace(u'\n', u' ')).strip())
        self.category = NotAvailable

        if '  ' in self.raw:
            self.category, useless, self.label = [part.strip() for part in self.raw.partition('  ')]
        else:
            self.label = self.raw

        for pattern, _type in self.PATTERNS:
            m = pattern.match(self.raw)
            if m:
                args = m.groupdict()
                self.type = _type
                if 'text' in args:
                    self.label = args['text'].strip()

                # Set date from information in raw label.
                if 'dd' and 'mm' in args:
                    dd = int(args['dd'])
                    mm = int(args['mm'])

                    if 'yy' in args:
                        yy = int(args['yy'])
                    else:
                        d = datetime.date.today()
                        try:
                            d = d.replace(month=mm, day=dd)
                        except ValueError:
                            d = d.replace(year=d.year-1, month=mm, day=dd)

                        yy = d.year
                        if d > datetime.date.today():
                            yy -= 1

                    if yy < 100:
                        yy += 2000

                    if 'HH' in args and 'MM' in args:
                        self.rdate = datetime.datetime(yy, mm, dd, int(args['HH']), int(args['MM']))
                    else:
                        self.rdate = datetime.date(yy, mm, dd)

                return
