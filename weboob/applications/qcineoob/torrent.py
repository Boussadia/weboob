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

import sys

from PyQt4.QtCore import Qt,SIGNAL
from PyQt4.QtGui import QFrame, QFileDialog

from weboob.applications.qcineoob.ui.torrent_ui import Ui_Torrent
from weboob.capabilities.base import NotAvailable, NotLoaded

class Torrent(QFrame):
    def __init__(self, torrent, backend, parent=None):
        QFrame.__init__(self, parent)
        self.parent = parent
        self.backend = backend
        self.ui = Ui_Torrent()
        self.ui.setupUi(self)

        self.connect(self.ui.downloadButton, SIGNAL("clicked()"), self.download)

        self.torrent = torrent
        self.ui.nameLabel.setText(u'%s'%torrent.name)
        if torrent.url != NotAvailable:
            self.ui.urlEdit.setText(u'%s'%torrent.url)
        else:
            self.ui.urlFrame.hide()
            self.ui.downloadButton.setDisabled(True)
            self.ui.downloadButton.setToolTip('Use the magnet link')
        if torrent.magnet != NotAvailable and torrent.magnet != NotLoaded:
            self.ui.magnetEdit.setText(u'%s'%torrent.magnet)
        else:
            self.ui.magnetFrame.hide()

        self.ui.verticalLayout.setAlignment(Qt.AlignTop)

    def download(self):
        fileDial = QFileDialog(self,'Save "%s" torrent file'%self.torrent.name,'%s.torrent'%self.torrent.name,'Torrent file (*.torrent);;all files (*)')
        fileDial.setAcceptMode(QFileDialog.AcceptSave)
        fileDial.setLabelText(QFileDialog.Accept,'Save torrent file')
        fileDial.setLabelText(QFileDialog.FileName,'Torrent file name')
        ok = (fileDial.exec_() == 1)
        if not ok:
            return
        result = fileDial.selectedFiles()
        if len(result) > 0:
            dest = result[0]
            data = self.backend.get_torrent_file(self.torrent.id)
            try:
                with open(dest, 'w') as f:
                    f.write(data)
            except IOError, e:
                print >>sys.stderr, 'Unable to write .torrent in "%s": %s' % (dest, e)
                return 1
            return

