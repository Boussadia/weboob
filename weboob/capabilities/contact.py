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


from .base import IBaseCap, CapBaseObject
from weboob.tools.ordereddict import OrderedDict


__all__ = ['ICapContact', 'Contact']

class ProfileNode(object):
    HEAD =    0x01
    SECTION = 0x02

    def __init__(self, name, label, value, sufix=None, flags=0):
        self.name = name
        self.label = label
        self.value = value
        self.sufix = sufix
        self.flags = flags

class ContactPhoto(CapBaseObject):
    def __init__(self, name):
        CapBaseObject.__init__(self, name)
        self.add_field('name', basestring, name)
        self.add_field('url', basestring)
        self.add_field('data', str)
        self.add_field('thumbnail_url', basestring)
        self.add_field('thumbnail_data', basestring)
        self.add_field('hidden', bool, False)

    def __iscomplete__(self):
        return (self.data and (not self.thumbnail_url or self.thumbnail_data))

    def __str__(self):
        return self.url

    def __repr__(self):
        return u'<ContactPhoto "%s" data=%do tndata=%do>' % (self.id,
                                                             len(self.data) if self.data else 0,
                                                             len(self.thumbnail_data) if self.thumbnail_data else 0)

class Contact(CapBaseObject):
    STATUS_ONLINE =  0x001
    STATUS_AWAY =    0x002
    STATUS_OFFLINE = 0x004
    STATUS_ALL =     0xfff

    def __init__(self, id, name, status):
        CapBaseObject.__init__(self, id)
        self.add_field('name', basestring, name)
        self.add_field('status', int, status)
        self.add_field('url', basestring)
        self.add_field('status_msg', basestring)
        self.add_field('summary', basestring)
        self.add_field('photos', dict, OrderedDict())
        self.add_field('profile', list)

    def set_photo(self, name, **kwargs):
        if not name in self.photos:
            self.photos[name] = ContactPhoto(name)

        photo = self.photos[name]
        for key, value in kwargs.iteritems():
            setattr(photo, key, value)

class QueryError(Exception):
    pass

class Query(CapBaseObject):
    def __init__(self, id, message):
        CapBaseObject.__init__(self, id)
        self.add_field('message', basestring, message)

class ICapContact(IBaseCap):
    def iter_contacts(self, status=Contact.STATUS_ALL, ids=None):
        """
        Iter contacts

        @param status  get only contacts with the specified status
        @param ids  if set, get the specified contacts
        @return  iterator over the contacts found
        """
        raise NotImplementedError()

    def get_contact(self, id):
        """
        Get a contact from his id.

        The default implementation only calls iter_contacts()
        with the proper values, but it might be overloaded
        by backends.

        @param id  the ID requested
        @return  the Contact object, or None if not found
        """

        l = self.iter_contacts(ids=[id])
        try:
            return l[0]
        except IndexError:
            return None

    def send_query(self, id):
        """
        Send a query to a contact

        @param id  the ID of contact
        @return  a Query object
        @except QueryError
        """
        raise NotImplementedError()
