# * -*- coding: utf-8 -*-

# Copyright(C) 2013  Thomas Lecavelier
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

from weboob.tools.browser import BasePage
from weboob.capabilities.radio import Radio, Stream, Emission

__all__ = ['LivePage', 'ProgramPage']

class LivePage(BasePage):
    def iter_radios_list(self):
        radio = Radio('nihon')
        radio.title = 'Nihon no Oto'
        radio.description = u'Nihon no Oto: le son du Japon'
        radio.streams = []

        index = -1
       
        for el in self.document.xpath('//source'):
            index += 1
            mime_type  = el.attrib['type']
            stream_url = el.attrib['src']
            stream = Stream(index)
            stream.title = radio.title + ' ' + mime_type
            stream.url = stream_url
            radio.streams.append(stream)

        yield radio



class ProgramPage(BasePage):
    def get_current_emission(self):
        self.document.xpath('//p')[0].text
        current = Emission(0)
        current.artist, current.title = self.document.xpath('//p')[0].text.split('/////')[0].split(' - ')
        return current
