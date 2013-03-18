# -*- coding: utf-8 -*-

# Copyright(C) 2013 Julien Veyssier
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

from PyQt4.QtGui import QFrame, QImage, QPixmap, QApplication
from PyQt4.QtCore import Qt

from weboob.applications.qcineoob.ui.minimovie_ui import Ui_MiniMovie
from weboob.capabilities.base import empty


class MiniMovie(QFrame):
    def __init__(self, weboob, backend, movie, parent=None):
        QFrame.__init__(self, parent)
        self.parent = parent
        self.ui = Ui_MiniMovie()
        self.ui.setupUi(self)

        self.weboob = weboob
        self.backend = backend
        self.movie = movie
        self.ui.titleLabel.setText(movie.original_title)
        self.ui.shortDescLabel.setText(movie.short_description)
        self.ui.backendLabel.setText(backend.name)

    def gotThumbnail(self):
        self.backend.fill_movie(self.movie, ('thumbnail_url'))
        if not empty(self.movie.thumbnail_url):
            data = urllib.urlopen(self.movie.thumbnail_url).read()
            img = QImage.fromData(data)
            self.ui.imageLabel.setPixmap(QPixmap.fromImage(img))

    def enterEvent(self, event):
        self.setFrameShadow(self.Sunken)
        QFrame.enterEvent(self, event)

    def leaveEvent(self, event):
        self.setFrameShadow(self.Raised)
        QFrame.leaveEvent(self, event)

    def mousePressEvent(self, event):
        QFrame.mousePressEvent(self, event)

        if event.button() == 2:
            self.gotThumbnail()
        else:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            movie = self.backend.get_movie(self.movie.id)
            if movie:
                self.parent.doAction('Details of movie "%s"' %
                                     movie.original_title, self.parent.displayMovie, [movie, self.backend])
