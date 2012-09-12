# -*- coding: utf-8 -*-

# Copyright(C) 2010-2011 Romain Bignon
# Copyright(C) 2012 François Revol
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

#from .pages.index import IndexPage
from .pages import VideoPage
from .video import VimeoVideo


__all__ = ['VimeoBrowser']


class VimeoBrowser(BaseBrowser):
    DOMAIN = 'vimeo.com'
    ENCODING = None
    # USER_AGENT = BaseBrowser.USER_AGENTS['wget']
    # TODO: determine this dynamically, like:
    # wget -d 127.0.0.1 -O /dev/null 2>&1 | grep '^User-Agent:'
    #USER_AGENT = 'Wget/1.14 (linux-gnu)'
    PAGES = {r'http://[w\.]*vimeo\.com/(?P<id>\d+).*': VideoPage,
            }

    @id2url(VimeoVideo.id2url)
    def get_video(self, url, video=None):
        self.location(url)
        return self.page.get_video(video)

    # def search_videos(self, pattern, sortby):
    #     return None
    #     self.location(self.buildurl('http://vimeo.com/search%s' % q=pattern.encode('utf-8')))
    #     assert self.is_on_page(IndexPage)
    #     return self.page.iter_videos()

    # def latest_videos(self):
    #     self.home()
    #     assert self.is_on_page(IndexPage)
    #     return self.page.iter_videos()
