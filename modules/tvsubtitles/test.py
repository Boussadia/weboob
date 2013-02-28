# -*- coding: utf-8 -*-

# Copyright(C) 2010-2011 Julien Veyssier
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

from weboob.tools.test import BackendTest

import urllib
from random import choice

class TvsubtitlesTest(BackendTest):
    BACKEND = 'tvsubtitles'

    def test_subtitle(self):
        subtitles = list(self.backend.iter_subtitles('fr','sopranos'))
        assert (len(subtitles) > 0)
        for subtitle in subtitles:
            path, qs = urllib.splitquery(subtitle.url)
            assert path.endswith('.zip')

        # get the file of a random sub
        if len(subtitles):
            subtitle = choice(subtitles)
            self.backend.get_subtitle_file(subtitle.id)
