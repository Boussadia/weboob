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


from weboob.tools.browser import BrowserUnavailable
from weboob.capabilities.dating import Optimization

from ..browser import AuMBrowser


__all__ = ['Visibility']


class Visibility(Optimization):
    def __init__(self, sched, browser):
        self.sched = sched
        self.browser = browser
        self.cron = None

    def start(self):
        self.cron = self.sched.repeat(60*5, self.reconnect)
        return True

    def stop(self):
        self.sched.cancel(self.cron)
        self.cron = None
        return True

    def is_running(self):
        return self.cron is not None

    def reconnect(self):
        try:
            AuMBrowser(self.browser.username,
                        self.browser.password,
                        proxy=self.browser.proxy)
        except BrowserUnavailable, e:
            print str(e)
            pass
