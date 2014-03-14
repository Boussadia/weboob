# -*- coding: utf-8 -*-
# Copyright(C) 2014 Laurent Bachelier
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

import requests.cookies
import cookielib


class WeboobCookieJar(requests.cookies.RequestsCookieJar):
    @classmethod
    def from_cookiejar(klass, cj):
        """
        Create a WeboobCookieJar from another CookieJar instance.
        """
        return requests.cookies.merge_cookies(klass(), cj)

    def export(self, filename):
        """
        Export all cookies to a file, regardless of expiration, etc.
        """
        cj = requests.cookies.merge_cookies(cookielib.LWPCookieJar(), self)
        cj.save(filename, ignore_discard=True, ignore_expires=True)
