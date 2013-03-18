# -*- coding: utf-8 -*-

# Copyright(C) 2013 Julien Veyssier
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


from weboob.capabilities.lyrics import SongLyrics
from weboob.capabilities.base import NotAvailable, NotLoaded
from weboob.tools.browser import BasePage


__all__ = ['SongResultsPage', 'SonglyricsPage', 'ArtistResultsPage', 'ArtistSongsPage']


class ArtistResultsPage(BasePage):
    def iter_lyrics(self):
        for link in self.parser.select(self.document.getroot(), 'table[title~=Results] a.tlink'):
            artist = unicode(link.text_content())
            self.browser.location('http://www.seeklyrics.com%s' % link.attrib.get('href', ''))
            assert self.browser.is_on_page(ArtistSongsPage)
            for lyr in self.browser.page.iter_lyrics(artist):
                yield lyr


class ArtistSongsPage(BasePage):
    def iter_lyrics(self, artist):
        for th in self.parser.select(self.document.getroot(), 'th.text'):
            txt = th.text_content()
            if txt.startswith('Top') and txt.endswith('Lyrics'):
                for link in self.parser.select(th.getparent().getparent(), 'a.tlink'):
                    title = unicode(link.attrib.get('title', '').replace(' Lyrics', ''))
                    id = link.attrib.get('href', '').replace('/lyrics/', '').replace('.html', '')
                    songlyrics = SongLyrics(id, title)
                    songlyrics.artist = artist
                    songlyrics.content = NotLoaded
                    yield songlyrics


class SongResultsPage(BasePage):
    def iter_lyrics(self):
        first = True
        for tr in self.parser.select(self.document.getroot(), 'table[title~=Results] tr'):
            if first:
                first = False
                continue
            artist = NotAvailable
            ftitle = self.parser.select(tr, 'a > font > font', 1)
            title = unicode(ftitle.getparent().getparent().text_content())
            id = ftitle.getparent().getparent().attrib.get('href', '').replace('/lyrics/', '').replace('.html', '')
            aartist = self.parser.select(tr, 'a')[-1]
            artist = unicode(aartist.text)
            songlyrics = SongLyrics(id, title)
            songlyrics.artist = artist
            songlyrics.content = NotLoaded
            yield songlyrics


class SonglyricsPage(BasePage):
    def get_lyrics(self, id):
        artist = NotAvailable
        title = NotAvailable
        l_artitle = self.parser.select(self.document.getroot(), 'table.text td > b > h2')
        if len(l_artitle) > 0:
            artitle = l_artitle[0].text.split(' Lyrics by ')
            artist = unicode(artitle[1])
            title = unicode(artitle[0])
        content = unicode(self.parser.select(self.document.getroot(), 'div#songlyrics', 1).text_content().strip())
        songlyrics = SongLyrics(id, title)
        songlyrics.artist = artist
        songlyrics.content = content
        return songlyrics
