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

# python2.5 compatibility
from __future__ import with_statement

from weboob.capabilities.messages import ICapMessages, Message, Thread
from weboob.tools.backend import BaseBackend
from weboob.tools.newsfeed import Newsfeed

class GenericNewspaperBackend(BaseBackend, ICapMessages):
    "GenericNewspaperBackend class"
    MAINTAINER = 'Julien Hebert'
    EMAIL = 'juke@free.fr'
    VERSION = '0.9'
    LICENSE = 'AGPLv3+'
    STORAGE = {'seen': {}}
    RSS_FEED = None
    RSSID = None

    def get_thread(self, _id):
        if isinstance(_id, Thread):
            thread = _id
            _id = thread.id
        else:
            thread = None

        with self.browser:
            content = self.browser.get_content(_id)

        if content is None:
            return None

        if not thread:
            thread = Thread(_id)

        flags = Message.IS_HTML
        if not thread.id in self.storage.get('seen', default={}):
            flags |= Message.IS_UNREAD
        thread.title = content.title
        if not thread.date:
            thread.date = content.date

        thread.root = Message(
            thread=thread,
            id=0,
            title=content.title,
            sender=content.author,
            receivers=None,
            date=thread.date,
            parent=None,
            content=content.body,
            signature='URL: %s' % content.url,
            flags=flags,
            children= [])
        return thread

    def iter_threads(self):
        for article in Newsfeed(self.RSS_FEED, GenericNewspaperBackend.RSSID).iter_entries():
            thread = Thread(article.id)
            thread.title =  article.title
            thread.date = article.datetime
            yield(thread)

    def fill_thread(self, thread, fields):
        "fill the thread"
        t = self.get_thread(thread)
        return t or thread

    def iter_unread_messages(self, thread=None):
        for thread in self.iter_threads():
            self.fill_thread(thread, 'root')
            for msg in thread.iter_all_messages():
                if msg.flags & msg.IS_UNREAD:
                    yield msg

    def set_message_read(self, message):
        self.storage.set(
            'seen',
            message.thread.id,
            'comments',
            self.storage.get(
                'seen',
                message.thread.id,
                'comments',
                default=[]) + [message.id])
        self.storage.save()

    OBJECTS = {Thread: fill_thread}
