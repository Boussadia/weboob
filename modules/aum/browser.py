# -*- coding: utf-8 -*-

# Copyright(C) 2008-2011  Romain Bignon, Christophe Benz
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


import math
import re
import urllib

from weboob.tools.browser import BaseBrowser, BrowserIncorrectPassword, BrowserHTTPNotFound
from weboob.tools.json import json

from weboob.capabilities.base import UserError
from weboob.capabilities.messages import CantSendMessage


__all__ = ['AuMBrowser']


class AuMException(UserError):
    ERRORS = {"0.0.0":  "Bad signature",
              "0.0.1":  "Malformed request",
              "0.0.2":  "Not logged",
              "1.1.1":  "No member has this login",
              "1.1.2":  "Password don't match",
              "1.1.3":  "User has been banned",
              "1.12.1": "Invalid country",
              "1.12.1": "Invalid region",
              "4.0.1":  "Member not found",
              "4.1.1":  "Thread doesn't exist",
              "4.1.2":  "Cannot write to this member",
              "5.1.1":  "Member tergeted doesn't exist",
              "5.1.2":  "Sex member targeted is not the opposite of the member logged",
              "5.1.3":  "Not possible to send a charm",
              "5.1.4":  "Not possible to send a charm because the 5 charms has been already used",
              "5.1.5":  "Not possible because the guy has already send a charm to this girl",
              "5.1.6":  "No more money",
              "5.1.7":  "Not possible to add to basket",
              "5.2.1":  "Member doesn't exist",
              "5.3.1":  "Member doesn't exist",
             }

    def __init__(self, code):
        Exception.__init__(self, self.ERRORS.get(code, code))
        self.code = code

class AuMBrowser(BaseBrowser):
    DOMAIN = 'www.adopteunmec.com'
    APIKEY = 'fb0123456789abcd'

    consts = None
    my_sex = 0
    my_id = 0
    my_name = u''
    my_coords = (0,0)

    def __init__(self, username, password, search_query, *args, **kwargs):
        kwargs['get_home'] = False
        BaseBrowser.__init__(self, username, password, *args, **kwargs)

        self.add_password('http://www.adopteunmec.com/api/', self.username, self.password)
        self.home()

        self.search_query = search_query

    def id2url(self, id):
        return u'http://www.adopteunmec.com/index.php/profile/%s' % id

    def url2id(func):
        def inner(self, id, *args, **kwargs):
            m = re.match('^http://.*adopteunmec.com.*/(\d+)$', str(id))
            if m:
                id = int(m.group(1))
            else:
                m = re.match('^http://.*adopteunmec.com/index.php/profile/(\d+).*', str(id))
                if m:
                    id = int(m.group(1))
            return func(self, id, *args, **kwargs)
        return inner

    def api0_request(self, command, action, parameter='', data=None, nologin=False):
        if data is None:
            # Always do POST requests.
            data = ''
        elif isinstance(data, (list,tuple,dict)):
            data = urllib.urlencode(data)
        elif isinstance(data, unicode):
            data = data.encode('utf-8')

        url = self.buildurl('http://api.adopteunmec.com/api.php',
                                                     S=self.APIKEY,
                                                     C=command,
                                                     A=action,
                                                     P=parameter,
                                                     O='json')

        buf = self.openurl(url, data).read()

        try:
            r = json.loads(buf[buf.find('{'):])
        except ValueError:
            raise ValueError(buf)

        if 'errors' in r and r['errors'] != '0' and len(r['errors']) > 0:
            code = r['errors'][0]
            if code in (u'0.0.2', u'1.1.1', u'1.1.2'):
                if not nologin:
                    self.login()
                    return self.api0_request(command, action, parameter, data, nologin=True)
                else:
                    raise BrowserIncorrectPassword(AuMException.ERRORS[code])
            else:
                raise AuMException(code)

        return r

    def login(self):
        pass
        # XXX old API is disabled
        #r = self.api0_request('me', 'login', data={'login': self.username,
        #                                           'pass':  self.password,
        #                                          }, nologin=True)
        #self.my_coords = (float(r['result']['me']['lat']), float(r['result']['me']['lng']))
        #if not self.search_query:
        #    self.search_query = 'region=%s' % r['result']['me']['region']

    def api_request(self, command, **kwargs):
        if 'data' in kwargs:
            data = kwargs.pop('data').encode('utf-8', 'replace')
        else:
            data = None

        url = self.buildurl(self.absurl('/api/%s' % command), **kwargs)
        buf = self.openurl(url, data).read()

        try:
            r = json.loads(buf)
        except ValueError:
            raise ValueError(buf)

        return r

    def home(self):
        r = self.api_request('home/')
        self.my_sex = r['user']['sex']
        self.my_id = int(r['user']['id'])
        self.my_name = r['user']['pseudo']

        return r

    def get_consts(self):
        if self.consts is not None:
            return self.consts

        self.consts = [{}, {}]
        for key, sexes in self.api_request('values').iteritems():
            for sex, values in sexes.iteritems():
                if sex in ('boy', 'both'):
                    self.consts[0][key] = values
                if sex in ('girl', 'both'):
                    self.consts[1][key] = values

        return self.consts

    def score(self):
        r = self.home()
        return int(r['user']['points'])

    def get_my_name(self):
        return self.my_name

    def get_my_id(self):
        return self.my_id

    def nb_new_mails(self):
        r = self.home()
        return r['counters']['new_mails']

    def nb_new_baskets(self):
        r = self.home()
        return r['counters']['new_baskets']

    def nb_new_visites(self):
        r = self.home()
        return r['counters']['new_visits']

    def nb_available_charms(self):
        r = self.home()
        return r['subscription']['flashes_stock']

    def get_baskets(self):
        r = self.api_request('basket', count=30, offset=0)
        return r['results']

    def get_flashs(self):
        r = self.api_request('charms/', count=30, offset=0)
        return r['results']

    def get_visits(self):
        r = self.api_request('visits', count=30, offset=0)
        return r['results']

    def get_threads_list(self, count=30):
        r = self.api_request('threads', count=count, offset=0)
        return r['results']

    @url2id
    def get_thread_mails(self, id, count=30):
        r = self.api_request('threads/%s' % id, count=count, offset=0)
        return r

    @url2id
    def post_mail(self, id, content):
        content = content.replace('\n', '\r\n')

        try:
            self.api_request('threads/%s' % id, data=content)
        except BrowserHTTPNotFound:
            raise CantSendMessage('Unable to send message.')

    @url2id
    def delete_thread(self, id):
        r = self.api_request('message', 'delete', data={'id_user': id})
        self.logger.debug('Thread deleted: %r' % r)

    @url2id
    def send_charm(self, id):
        try:
            self.api_request('users/%s/charms' % id, data='')
        except BrowserHTTPNotFound:
            return False
        else:
            return True

    @url2id
    def add_basket(self, id):
        try:
            self.api_request('basket/%s' % id, data='')
        except BrowserHTTPNotFound:
            return False
        else:
            return True

    def search_profiles(self, **kwargs):
        if not self.search_query:
            # retrieve query
            self.login()

        r = self.api_request('users?count=100&offset=0&%s' % self.search_query)
        ids = [s['id'] for s in r['results']]
        return set(ids)

    @url2id
    def get_profile(self, id, with_pics=True):
        # XXX OLD API IS DISABLED (fucking faggots)
        #r = self.api0_request('member', 'view', data={'id': id})
        #if not 'result' in r:
        #    print r
        #profile = r['result']['member']

        profile = {}

        profile.update(self.api_request('users/%s' % id))

        # Calculate distance in km.
        profile['dist'] = 0.0
        if 'lat' in profile and 'lng' in profile:
            coords = (float(profile['lat']), float(profile['lng']))

            R = 6371
            lat1 = math.radians(self.my_coords[0])
            lat2 = math.radians(coords[0])
            lon1 = math.radians(self.my_coords[1])
            lon2 = math.radians(coords[1])
            dLat = lat2 - lat1
            dLong = lon2 - lon1
            a= pow(math.sin(dLat/2), 2) + math.cos(lat1) * math.cos(lat2) * pow(math.sin(dLong/2), 2)
            c= 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
            profile['dist'] = R * c

        return profile
