# -*- coding: utf-8 -*-

# Copyright(C) 2008-2011  Romain Bignon
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


import socket
from datetime import datetime
from dateutil.parser import parse as parse_dt

from weboob.tools.ordereddict import OrderedDict
from weboob.capabilities.contact import Contact as _Contact, ProfileNode
from weboob.tools.misc import html2text

class FieldBase:
    def __init__(self, key, key2=None):
        self.key = key
        self.key2 = key2

    def get_value(self, value, consts):
        raise NotImplementedError

class FieldStr(FieldBase):
    def get_value(self, profile, consts):
        return html2text(unicode(profile[self.key])).strip()

class FieldBool(FieldBase):
    def get_value(self, profile, consts):
        return bool(int(profile[self.key]))

class FieldIP(FieldBase):
    def get_hostname(self, s):
        try:
            return socket.gethostbyaddr(s)[0]
        except (socket.gaierror, socket.herror):
            return s

    def get_value(self, profile, consts):
        s = self.get_hostname(profile[self.key])
        if profile[self.key] != profile[self.key2]:
            s += ' (first %s)' % self.get_hostname(profile[self.key2])
        return s

class FieldProfileURL(FieldBase):
    def get_value(self, profile, consts):
        id = int(profile[self.key])
        if id > 0:
            return 'http://www.adopteunmec.com/%d' % id
        else:
            return ''

class FieldPopu(FieldBase):
    def get_value(self, profile, consts):
        return unicode(profile['popu'][self.key])

class FieldOld(FieldBase):
    def get_value(self, profile, consts):
        birthday = parse_dt(profile[self.key])
        return int((datetime.now() - birthday).days / 365.25)

class FieldSplit(FieldBase):
    def get_value(self, profile, consts):
        return [html2text(s).strip() for s in profile[self.key].split(self.key2) if len(s.strip()) > 0]

class FieldBMI(FieldBase):
    def __init__(self, key, key2, fat=False):
        FieldBase.__init__(self, key, key2)
        self.fat = fat

    def get_value(self, profile, consts):
        height = int(profile[self.key])
        weight = int(profile[self.key2])
        if height == 0 or weight == 0:
            return ''

        bmi = (weight/float(pow(height/100.0, 2)))
        if not self.fat:
            return bmi
        elif bmi < 15.5:
            return 'severely underweight'
        elif bmi < 18.4:
            return 'underweight'
        elif bmi < 24.9:
            return 'normal'
        elif bmi < 30:
            return 'overweight'
        else:
            return 'obese'

class FieldFlags(FieldBase):
    def get_value(self, profile, consts):
        i = int(profile[self.key])
        labels = []
        for d in consts[self.key]:
            if i & (1 << int(d['value'])):
                labels.append(html2text(d['label']).strip())
        return labels

class FieldList(FieldBase):
    def get_value(self, profile, consts):
        i = int(profile[self.key])
        for d in consts[self.key]:
            if i == int(d['value']):
                return html2text(d['label']).strip()
        return ''

class Contact(_Contact):
    TABLE = OrderedDict((
                 ('_info',        OrderedDict((
                                    ('IPaddr',              FieldIP('last_ip', 'first_ip')),
                                    ('admin',               FieldBool('admin')),
                                    ('ban',                 FieldBool('isBan')),
                                    ('first',               FieldStr('first_cnx')),
                                    ('godfather',           FieldProfileURL('godfather')),
                                  ))),
                 ('_stats',       OrderedDict((
                                    ('mails',               FieldPopu('mails')),
                                    ('baskets',             FieldPopu('contacts')),
                                    ('charms',              FieldPopu('flashs')),
                                    ('visites',             FieldPopu('visites')),
                                    ('invits',              FieldPopu('invits')),
                                    ('bonus',               FieldPopu('bonus')),
                                    ('score',               FieldPopu('popu')),
                                  ))),
                 ('details',      OrderedDict((
                                    ('old',                 FieldOld('birthday')),
                                    ('birthday',            FieldStr('birthday')),
                                    ('zipcode',             FieldStr('zip')),
                                    ('location',            FieldStr('city')),
                                    ('country',             FieldStr('country')),
                                    ('eyes',                FieldList('eyes')),
                                    ('hair_color',          FieldList('hair_color')),
                                    ('hair_size',           FieldList('hair_size')),
                                    ('height',              FieldList('size')),
                                    ('weight',              FieldList('weight')),
                                    ('BMI',                 FieldBMI('size', 'weight')),
                                    ('fat',                 FieldBMI('size', 'weight', fat=True)),
                                    ('origins',             FieldList('origins')),
                                    ('signs',               FieldFlags('checks1')),
                                    ('job',                 FieldStr('job')),
                                    ('style',               FieldList('style')),
                                    ('food',                FieldList('food')),
                                    ('drink',               FieldList('drink')),
                                    ('smoke',               FieldList('smoke')),
                                  ))),
                ('tastes',        OrderedDict((
                                    ('hobbies',             FieldStr('hobbies')),
                                    ('music',               FieldSplit('music', '<br>')),
                                    ('cinema',              FieldSplit('cinema', '<br>')),
                                    ('books',               FieldSplit('books', '<br>')),
                                    ('tv',                  FieldSplit('tvs', '<br>')),
                                  ))),
                ('sex',           OrderedDict((
                                    ('underwear',           FieldFlags('checks7')),
                                    ('practices',           FieldFlags('checks5')),
                                    ('favorite',            FieldFlags('checks3')),
                                    ('toys',                FieldFlags('checks6')),
                                  ))),
                ('personality',   OrderedDict((
                                    ('snap',                FieldStr('texts1')),
                                    ('exciting',            FieldStr('texts2')),
                                    ('hate',                FieldStr('texts3')),
                                    ('vices',               FieldStr('texts4')),
                                    ('assets',              FieldStr('texts6')),
                                    ('fantasies',           FieldStr('texts5')),
                                    ('is',                  FieldFlags('checks2')),
                                  )))
        ))

    def parse_profile(self, profile, consts):
        if int(profile['cat']) == 1:
            self.status = Contact.STATUS_ONLINE
            self.status_msg = u'online'
        elif int(profile['cat']) == 2:
            self.status = Contact.STATUS_AWAY
            self.status_msg = u'away'
        elif int(profile['cat']) == 3:
            self.status = Contact.STATUS_OFFLINE
            self.status_msg = u'last connexion %s' % profile['last_cnx']

        self.summary = html2text(profile['about1']).strip().replace('\n\n', '\n')
        if len(profile['about2']) > 0:
            self.summary += u'\n\nLooking for:\n%s' % html2text(profile['about2']).strip().replace('\n\n', '\n')

        for photo in profile['pictures']:
            self.set_photo(photo['url'].split('/')[-1],
                              url=photo['url'],
                              thumbnail_url=photo['url'].replace('image', 'thumb1_'),
                              hidden=photo['hidden'])
        self.profile = []

        for section, d in self.TABLE.iteritems():
            flags = ProfileNode.SECTION
            if section.startswith('_'):
                flags |= ProfileNode.HEAD
                section = section.lstrip('_')
            s = ProfileNode(section, section.capitalize(), [], flags=flags)

            for key, builder in d.iteritems():
                value = builder.get_value(profile, consts[int(profile['sex'])])
                s.value.append(ProfileNode(key, key.capitalize().replace('_', ' '), value))

            self.profile.append(s)

        self.aum_profile = profile

    def get_text(self):
        def print_node(node, level=1):
            result = u''
            if node.flags & node.SECTION:
                result += u'\t' * level + node.label + '\n'
                for sub in node.value:
                    result += print_node(sub, level+1)
            else:
                if isinstance(node.value, (tuple,list)):
                    value = ', '.join(unicode(v) for v in node.value)
                elif isinstance(node.value, float):
                    value = '%.2f' % node.value
                else:
                    value = node.value
                result += u'\t' * level + u'%-20s %s\n' % (node.label + ':', value)
            return result

        result = u'Nickname: %s\n' % self.name
        if self.status & Contact.STATUS_ONLINE:
            s = 'online'
        elif self.status & Contact.STATUS_OFFLINE:
            s = 'offline'
        elif self.status & Contact.STATUS_AWAY:
            s = 'away'
        else:
            s = 'unknown'
        result += u'Status: %s (%s)\n' % (s, self.status_msg)
        result += u'URL: %s\n' % self.url
        result += u'Photos:\n'
        for name, photo in self.photos.iteritems():
            result += u'\t%s\n' % photo
        result += u'\nProfile:\n'
        for head in self.profile:
            result += print_node(head)
        result += u'Description:\n'
        for s in self.summary.split('\n'):
            result += u'\t%s\n' % s
        return result
