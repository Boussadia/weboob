# -*- coding: utf-8 -*-

# Copyright(C) 2010-2012 Julien Veyssier
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


from .base import IBaseCap, CapBaseObject, Field, StringField, FloatField, \
                  DateField, IntField, UserError


__all__ = ['Subtitle', 'ICapSubtitle']


class Subtitle(CapBaseObject):
    """
    Subtitle object.
    """
    name =      StringField('Name of subtitle')
    url =       StringField('Direct url to subtitle file')
    fps =       StringField('Framerate of corresponding video')
    description =       StringField('Description of corresponding video')

    def __init__(self, id, name):
        CapBaseObject.__init__(self, id)
        self.name = name


class ICapSubtitle(IBaseCap):
    """
    Subtitle providers.
    """
    def iter_subtitles(self, pattern):
        """
        Search subtitles and iterate on results.

        :param pattern: pattern to search
        :type pattern: str
        :rtype: iter[:class:`Subtitle`]
        """
        raise NotImplementedError()

    def get_subtitle(self, _id):
        """
        Get a subtitle object from an ID.

        :param _id: ID of subtitle
        :type _id: str
        :rtype: :class:`Subtitle`
        """
        raise NotImplementedError()

    def get_subtitle_file(self, _id):
        """
        Get the content of the subtitle file.

        :param _id: ID of subtitle
        :type _id: str
        :rtype: str
        """
        raise NotImplementedError()
