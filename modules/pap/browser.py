# -*- coding: utf-8 -*-

# Copyright(C) 2012 Romain Bignon
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


import urllib
import json

from weboob.tools.browser import BaseBrowser

from .pages import SearchResultsPage, HousingPage


__all__ = ['PapBrowser']


class PapBrowser(BaseBrowser):
    PROTOCOL = 'http'
    DOMAIN = 'www.pap.fr'
    ENCODING = 'utf-8'
    PAGES = {
         'http://www.pap.fr/annonce/.*':  SearchResultsPage,
         'http://www.pap.fr/annonces/.*': HousingPage,
        }

    def search_geo(self, pattern):
        fp = self.openurl(self.buildurl('http://www.pap.fr/index/ac-geo', q=pattern))
        return json.load(fp)

    def search_housings(self, cities, area_min, area_max, cost_min, cost_max):
        data = {'geo_objets_ids': ','.join(cities),
                'surface[min]':   area_min or '',
                'surface[max]':   area_max or '',
                'prix[min]':      cost_min or '',
                'prix[max]':      cost_max or '',
                'produit':        'location',
                'recherche':      1,
                'nb_resultats_par_page': 40,
                'submit':         'rechercher',
                'typesbien[]':    'appartement',
               }
        self.location('/annonce/', urllib.urlencode(data))
        assert self.is_on_page(SearchResultsPage)

        return self.page.iter_housings()

    def get_housing(self, housing):
        self.location('/annonces/%s' % urllib.quote(housing))

        assert self.is_on_page(HousingPage)
        return self.page.get_housing()
