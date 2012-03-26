# -*- coding: utf-8 -*-

# Copyright(C) 2012 Roger Philibert
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


from weboob.tools.browser import BasePage, BrokenPageError
from weboob.tools.ordereddict import OrderedDict
from weboob.tools.misc import html2text
from weboob.capabilities.contact import ProfileNode

class LoginPage(BasePage):
    def login(self, username, password):
        self.browser.select_form(name='loginf')
        self.browser['username'] = username.encode(self.browser.ENCODING)
        self.browser['password'] = password.encode(self.browser.ENCODING)
        self.browser.submit(id='login_btn', nologin=True)

class ThreadPage(BasePage):
    def get_threads(self):
        li_elems = self.parser.select(self.document.getroot(), "//div[@id='page_content']//li", method= 'xpath')

        threads = []
        for elem in li_elems:
            _class = elem.get('class', '')
            if 'clearfix' in _class.split():
                threads.append({
                        u'username' : elem.getchildren()[0].get('href').split('/')[-1],
                        u'id' : elem.get('id', '').split('_')[1],
                })

        return threads

class MessagesPage(BasePage):
    def get_thread_mails(self, count):
        ul_item = self.parser.select(self.document.getroot(), "//ul[@id='rows']", method='xpath')[0]

        mails = {
            'member' : {},
            'messages' : [],
        }

        for li_msg in ul_item.getchildren():
            div = li_msg.getchildren()[1]
            txt = self.parser.tostring(div.getchildren()[1])
            date = div.getchildren()[2].text
            id_from = li_msg.getchildren()[0].get('href').split('/')[-1]

            mails['messages'].append({
                'date' : date,
                'message' : txt,
                'id_from' : id_from,
            })

        return mails

class ProfilePage(BasePage):
    def get_profile(self):
        title = self.parser.select(self.document.getroot(), 'title', 1)
        if title.text == 'OkCupid: Account Not Found':
            return None

        profile = {}
        profile['id'] = title.text[len('OkCupid: '):]
        profile['data'] = OrderedDict()

        profile_p = self.parser.select(self.document.getroot(), "//div[@id='page_content']//p", method='xpath')

        profile['data']['infos'] = ProfileNode('infos', 'Informations', OrderedDict(), flags=ProfileNode.SECTION)

        info = {
                        'age' : profile_p[1].text.split(' / ')[0],
                        'sex' : profile_p[1].text.split(' / ')[1],
                        'orientation' : profile_p[1].text.split(' / ')[2],
                        'relationship' : profile_p[1].text.split(' / ')[3],
            }

        for key, val in info.iteritems():
            profile['data']['infos'].value[key] = ProfileNode(key, key.capitalize(), val)

        div_essays = self.parser.select(self.document.getroot(), "//div[@class='essay']", method='xpath')
        h3_essays = self.parser.select(self.document.getroot(), "//div[@id='page_content']//h3", method='xpath')
        essays = dict(zip(h3_essays, div_essays))

        profile['summary'] = div_essays[0].text.strip()

        profile['data']['essays'] = ProfileNode('essays', 'Essays', OrderedDict(), flags=ProfileNode.SECTION)

        for label, val in essays.iteritems():
            label = unicode(label.text).strip()
            val = unicode(val.text).strip()
            key = label.replace(' ', '_')
            profile['data']['essays'].value[key] = ProfileNode(key, label, val)
        #profile['data']['look_for'].value['orientation'] = ProfileNode('orientation', 'Orientation', div_essays[9].getchildren()[0].getchildren()[0].text.strip())
        #profile['data']['look_for'].value['location'] = ProfileNode('location', 'Location', div_essays[9].getchildren()[0].getchildren()[2].text.strip())
        #profile['data']['look_for'].value['relationship'] = ProfileNode('relationship', 'Relationship', div_essays[9].getchildren()[0].getchildren()[3].text.strip())
        #profile['data']['look_for'].value['what_for'] = ProfileNode('what_for', 'What for', div_essays[9].getchildren()[0].getchildren()[4].text.split('\n')[1].strip().split(', '))

        #age = div_essays[9].getchildren()[0].getchildren()[1].text[5:].strip().split(u'–')
        #profile['data']['look_for'].value['age_min'] = ProfileNode('age_min', 'Age min', int(age[0]))
        #profile['data']['look_for'].value['age_max'] = ProfileNode('age_max', 'Age max', int(age[1]))

        #div_essays = div_essays[1:-1]
        #h3_essays = h3_essays[1:-1]

        #for i, title in enumerate(h3_essays):
        #    profile['data']['essays'].value['essay_%i' % i] = ProfileNode('essay_%i' % i, title.text, div_essays[i].text.strip())

        details_div = self.parser.select(self.document.getroot(), "//div[@id='details']//li", method='xpath')
        profile['data']['details'] = ProfileNode('details', 'Details', OrderedDict(), flags=ProfileNode.SECTION)
        for elem in details_div:
            label = elem.getchildren()[0].text.strip()
            key = label.lower().replace(' ', '_')
            val = elem.getchildren()[1].text.strip()
            profile['data']['details'].value[key] = ProfileNode(key, label, val)

        return profile

class PhotosPage(BasePage):
    def get_photos(self):
        imgs = self.parser.select(self.document.getroot(), "//div[@class='pic clearfix']//img", method='xpath')
        return [img.get('src') for img in imgs]
