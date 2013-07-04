# -*- coding: utf-8 -*-

# Copyright(C) 2013      Bezleputh
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

from weboob.tools.browser.decorators import id2url
from weboob.tools.browser import BaseBrowser
from .job import LolixJobAdvert
from .pages import SearchPage, AdvertPage

__all__ = ['LolixBrowser']


class LolixBrowser(BaseBrowser):
    PROTOCOL = 'http'
    DOMAIN = 'fr.lolix.org/search/offre'
    ENCODING = 'iso-8859-1'

    PAGES = {
        '%s://%s/date.php' % (PROTOCOL, DOMAIN): SearchPage,
        '%s://%s/offre.php\?id=(?P<id>.+)' % (PROTOCOL, DOMAIN): AdvertPage,
    }

    def search_job(self):
        self.location('%s://%s/date.php' % (self.PROTOCOL, self.DOMAIN))
        assert self.is_on_page(SearchPage)
        return self.page.iter_job_adverts()

    @id2url(LolixJobAdvert.id2url)
    def get_job_advert(self, url, advert):
        self.location(url)
        assert self.is_on_page(AdvertPage)
        return self.page.get_job_advert(url, advert)
