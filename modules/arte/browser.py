# -*- coding: utf-8 -*-

# Copyright(C) 2010-2011 Romain Bignon
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


from weboob.tools.browser import BaseBrowser
from weboob.tools.browser.decorators import id2url

from .pages import IndexPage, VideoPage
from .video import ArteVideo


__all__ = ['ArteBrowser']


class ArteBrowser(BaseBrowser):
    DOMAIN = u'videos.arte.tv'
    ENCODING = None
    PAGES = {r'http://videos.arte.tv/\w+/videos/toutesLesVideos.*': IndexPage,
             r'http://videos.arte.tv/\w+/do_search/videos/.*': IndexPage,
             r'http://videos.arte.tv/\w+/videos/(?P<id>.+)\.html': VideoPage
            }

    SEARCH_LANG = {'fr': 'recherche', 'de': 'suche', 'en': 'search'}

    def __init__(self, lang, quality, *args, **kwargs):
        BaseBrowser.__init__(self, *args, **kwargs)
        self.lang = lang
        self.quality = quality

    @id2url(ArteVideo.id2url)
    def get_video(self, url, video=None):
        self.location(url)
        return self.page.get_video(video, self.lang, self.quality)

    def home(self):
        self.location('http://videos.arte.tv/fr/videos/toutesLesVideos')

    def search_videos(self, pattern):
        self.location(self.buildurl('/%s/do_search/videos/%s' % (self.lang, self.SEARCH_LANG[self.lang]), q=pattern.encode('utf-8')))
        assert self.is_on_page(IndexPage)
        return self.page.iter_videos()

    def latest_videos(self):
        self.home()
        assert self.is_on_page(IndexPage)
        return self.page.iter_videos()
