"browser for 20minutes website"
# -*- coding: utf-8 -*-

# Copyright(C) 2011  Julien Hebert
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

from .pages.article import ArticlePage
from .pages.simple import SimplePage
from weboob.tools.browser import BaseBrowser
from .tools import id2url


class Newspaper20minutesBrowser(BaseBrowser):
    "Newspaper20minutesBrowser class"
    PAGES = {
             'http://www.20minutes.fr/article/?.*': ArticlePage,
             'http://www.20minutes.fr/ledirect/?.*': SimplePage,
             'http://www.20minutes.fr/preums/?.*': SimplePage
            }

    def is_logged(self):
        return False

    def login(self):
        pass

    def fillobj(self, obj, fields):
        pass

    def get_content(self, _id):
        "return page article content"
        try :
            url = id2url(_id)
        except ValueError:
            url = _id
        self.location(url)

        if self.page is not None:
            return self.page.get_article(_id)
