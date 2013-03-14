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

import os,codecs

from PyQt4.QtCore import SIGNAL, Qt, QStringList
from PyQt4.QtGui import QApplication, QCompleter

from weboob.capabilities.cinema import ICapCinema
from weboob.capabilities.torrent import ICapTorrent
from weboob.capabilities.subtitle import ICapSubtitle
from weboob.tools.application.qt import QtMainWindow, QtDo
from weboob.tools.application.qt.backendcfg import BackendCfg

from weboob.applications.suboob.suboob import LANGUAGE_CONV
from weboob.applications.qcineoob.ui.main_window_ui import Ui_MainWindow

from .minimovie import MiniMovie
from .miniperson import MiniPerson
from .minitorrent import MiniTorrent
from .minisubtitle import MiniSubtitle
from .movie import Movie
from .person import Person
from .torrent import Torrent
from .subtitle import Subtitle

class MainWindow(QtMainWindow):
    def __init__(self, config, weboob, parent=None):
        QtMainWindow.__init__(self, parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.config = config
        self.weboob = weboob
        self.minis = []
        self.current_info_widget = None

        # search history is a list of patterns which have been searched
        self.search_history = self.loadSearchHistory()
        self.updateCompletion()

        # action history is composed by the last action and the action list
        # An action is a function, a list of arguments and a description string
        self.action_history = {'last_action':None,'action_list':[]}
        self.connect(self.ui.backButton, SIGNAL("clicked()"), self.doBack)
        self.ui.backButton.hide()

        self.connect(self.ui.searchEdit, SIGNAL("returnPressed()"), self.search)
        self.connect(self.ui.typeCombo, SIGNAL("returnPressed()"), self.search)
        self.connect(self.ui.typeCombo, SIGNAL("currentIndexChanged(QString)"), self.typeComboChanged)

        self.connect(self.ui.actionBackends, SIGNAL("triggered()"), self.backendsConfig)
        self.connect(self.ui.actionQuit, SIGNAL("triggered()"), self.close)

        self.loadBackendsList()

        if self.ui.backendEdit.count() == 0:
            self.backendsConfig()

        langs = LANGUAGE_CONV.keys()
        langs.sort()
        for lang in langs:
            self.ui.langCombo.addItem(lang)
        self.ui.langCombo.hide()
        self.ui.langLabel.hide()

    def backendsConfig(self):
        bckndcfg = BackendCfg(self.weboob, (ICapCinema,ICapTorrent,ICapSubtitle,), self)
        if bckndcfg.run():
            self.loadBackendsList()

    def loadBackendsList(self):
        self.ui.backendEdit.clear()
        for i, backend in enumerate(self.weboob.iter_backends()):
            if i == 0:
                self.ui.backendEdit.addItem('All backends', '')
            self.ui.backendEdit.addItem(backend.name, backend.name)
            if backend.name == self.config.get('settings', 'backend'):
                self.ui.backendEdit.setCurrentIndex(i+1)

        if self.ui.backendEdit.count() == 0:
            self.ui.searchEdit.setEnabled(False)
        else:
            self.ui.searchEdit.setEnabled(True)

    def loadSearchHistory(self):
        ''' Return search string history list loaded from history file
        '''
        result = []
        history_path = os.path.join(self.weboob.workdir, 'qcineoob_history')
        if os.path.exists(history_path):
            f=codecs.open(history_path,'r','utf-8')
            conf_hist = f.read()
            f.close()
            if conf_hist != None and conf_hist.strip() != '':
                result = conf_hist.strip().split('\n')
        return result

    def saveSearchHistory(self):
        ''' Save search history in history file
        '''
        if len(self.search_history) > 0:
            history_path = os.path.join(self.weboob.workdir, 'qcineoob_history')
            f=codecs.open(history_path,'w','utf-8')
            f.write('\n'.join(self.search_history))
            f.close()

    def updateCompletion(self):
        qc = QCompleter(QStringList(self.search_history),self)
        qc.setCaseSensitivity(Qt.CaseInsensitive)
        self.ui.searchEdit.setCompleter(qc)

    def typeComboChanged(self,value):
        if unicode(value) == 'subtitle':
            self.ui.langCombo.show()
            self.ui.langLabel.show()
        else:
            self.ui.langCombo.hide()
            self.ui.langLabel.hide()

    def doAction(self, description, fun, args):
        ''' Call fun with args as arguments
        and save it in the action history
        '''
        self.ui.currentActionLabel.setText(description)
        if self.action_history['last_action'] != None:
            self.action_history['action_list'].append(self.action_history['last_action'])
            self.ui.backButton.setToolTip(self.action_history['last_action']['description'])
            self.ui.backButton.show()
        self.action_history['last_action'] = {'function':fun,'args':args,'description':description}
        return fun(*args)

    def doBack(self):
        ''' Go back in action history
        Basically call previous function and update history
        '''
        if len(self.action_history['action_list']) > 0:
            todo = self.action_history['action_list'].pop()
            self.ui.currentActionLabel.setText(todo['description'])
            self.action_history['last_action'] = todo
            if len(self.action_history['action_list']) == 0:
                self.ui.backButton.hide()
            else:
                self.ui.backButton.setToolTip(self.action_history['action_list'][-1]['description'])
            return todo['function'](*todo['args'])

    def castingAction(self, id, role):
        self.ui.stackedWidget.setCurrentWidget(self.ui.list_page)
        for mini in self.minis:
            self.ui.list_content.layout().removeWidget(mini)
            mini.hide()
            mini.deleteLater()

        self.minis = []
        self.ui.searchEdit.setEnabled(False)
        QApplication.setOverrideCursor( Qt.WaitCursor )

        backend_name = str(self.ui.backendEdit.itemData(self.ui.backendEdit.currentIndex()).toString())

        self.process = QtDo(self.weboob, self.addPerson)
        self.process.do('iter_movie_persons', id, role, backends=backend_name, caps=ICapCinema)

    def filmographyAction(self, id, role):
        self.ui.stackedWidget.setCurrentWidget(self.ui.list_page)
        for mini in self.minis:
            self.ui.list_content.layout().removeWidget(mini)
            mini.hide()
            mini.deleteLater()

        self.minis = []
        self.ui.searchEdit.setEnabled(False)
        QApplication.setOverrideCursor( Qt.WaitCursor )

        backend_name = str(self.ui.backendEdit.itemData(self.ui.backendEdit.currentIndex()).toString())

        self.process = QtDo(self.weboob, self.addMovie)
        self.process.do('iter_person_movies', id, role, backends=backend_name, caps=ICapCinema)

    def search(self):
        pattern = unicode(self.ui.searchEdit.text())
        # arbitrary max number of completion word
        if len(self.search_history) > 50:
            self.search_history.pop(0)
        if pattern not in self.search_history:
            self.search_history.append(pattern)
            self.updateCompletion()

        tosearch = self.ui.typeCombo.currentText()
        if tosearch == 'person':
            self.searchPerson()
        elif tosearch == 'movie':
            self.searchMovie()
        elif tosearch == 'torrent':
            self.searchTorrent()
        elif tosearch == 'subtitle':
            self.searchSubtitle()

    def searchMovie(self):
        pattern = unicode(self.ui.searchEdit.text())
        if not pattern:
            return
        self.doAction(u'Search movie "%s"'%pattern,self.searchMovieAction,[pattern])

    def searchMovieAction(self,pattern):
        self.ui.stackedWidget.setCurrentWidget(self.ui.list_page)
        for mini in self.minis:
            self.ui.list_content.layout().removeWidget(mini)
            mini.hide()
            mini.deleteLater()

        self.minis = []
        self.ui.searchEdit.setEnabled(False)
        QApplication.setOverrideCursor( Qt.WaitCursor )

        backend_name = str(self.ui.backendEdit.itemData(self.ui.backendEdit.currentIndex()).toString())

        self.process = QtDo(self.weboob, self.addMovie)
        self.process.do('iter_movies', pattern, backends=backend_name, caps=ICapCinema)

    def addMovie(self, backend, movie):
        if not backend:
            self.ui.searchEdit.setEnabled(True)
            QApplication.restoreOverrideCursor()
            self.process = None
            return
        minimovie = MiniMovie(self.weboob, backend, movie, self)
        self.ui.list_content.layout().addWidget(minimovie)
        self.minis.append(minimovie)

    def displayMovie(self, movie, backend):
        self.ui.stackedWidget.setCurrentWidget(self.ui.info_page)
        if self.current_info_widget != None:
            self.ui.info_content.layout().removeWidget(self.current_info_widget)
            self.current_info_widget.hide()
            self.current_info_widget.deleteLater()
        wmovie = Movie(movie,backend,self)
        self.ui.info_content.layout().addWidget(wmovie)
        self.current_info_widget = wmovie
        QApplication.restoreOverrideCursor()

    def searchPerson(self):
        pattern = unicode(self.ui.searchEdit.text())
        if not pattern:
            return
        self.doAction(u'Search person "%s"'%pattern,self.searchPersonAction,[pattern])

    def searchPersonAction(self,pattern):
        self.ui.stackedWidget.setCurrentWidget(self.ui.list_page)
        for mini in self.minis:
            self.ui.list_content.layout().removeWidget(mini)
            mini.hide()
            mini.deleteLater()

        self.minis = []
        self.ui.searchEdit.setEnabled(False)
        QApplication.setOverrideCursor( Qt.WaitCursor )

        backend_name = str(self.ui.backendEdit.itemData(self.ui.backendEdit.currentIndex()).toString())

        self.process = QtDo(self.weboob, self.addPerson)
        self.process.do('iter_persons', pattern, backends=backend_name, caps=ICapCinema)

    def addPerson(self, backend, person):
        if not backend:
            self.ui.searchEdit.setEnabled(True)
            QApplication.restoreOverrideCursor()
            self.process = None
            return
        miniperson = MiniPerson(self.weboob, backend, person, self)
        self.ui.list_content.layout().addWidget(miniperson)
        self.minis.append(miniperson)

    def displayPerson(self, person, backend):
        self.ui.stackedWidget.setCurrentWidget(self.ui.info_page)
        if self.current_info_widget != None:
            self.ui.info_content.layout().removeWidget(self.current_info_widget)
            self.current_info_widget.hide()
            self.current_info_widget.deleteLater()
        wperson = Person(person,backend,self)
        self.ui.info_content.layout().addWidget(wperson)
        self.current_info_widget = wperson
        QApplication.restoreOverrideCursor()

    def searchTorrent(self):
        pattern = unicode(self.ui.searchEdit.text())
        if not pattern:
            return
        self.doAction(u'Search torrent "%s"'%pattern,self.searchTorrentAction,[pattern])

    def searchTorrentAction(self,pattern):
        self.ui.stackedWidget.setCurrentWidget(self.ui.list_page)
        for mini in self.minis:
            self.ui.list_content.layout().removeWidget(mini)
            mini.hide()
            mini.deleteLater()

        self.minis = []
        self.ui.searchEdit.setEnabled(False)
        QApplication.setOverrideCursor( Qt.WaitCursor )

        backend_name = str(self.ui.backendEdit.itemData(self.ui.backendEdit.currentIndex()).toString())

        self.process = QtDo(self.weboob, self.addTorrent)
        self.process.do('iter_torrents', pattern, backends=backend_name, caps=ICapTorrent)

    def addTorrent(self, backend, torrent):
        if not backend:
            self.ui.searchEdit.setEnabled(True)
            QApplication.restoreOverrideCursor()
            self.process = None
            return
        minitorrent = MiniTorrent(self.weboob, backend, torrent, self)
        self.ui.list_content.layout().addWidget(minitorrent)
        self.minis.append(minitorrent)

    def displayTorrent(self, torrent, backend):
        self.ui.stackedWidget.setCurrentWidget(self.ui.info_page)
        if self.current_info_widget != None:
            self.ui.info_content.layout().removeWidget(self.current_info_widget)
            self.current_info_widget.hide()
            self.current_info_widget.deleteLater()
        wtorrent = Torrent(torrent, backend, self)
        self.ui.info_content.layout().addWidget(wtorrent)
        self.current_info_widget = wtorrent

    def searchSubtitle(self):
        pattern = unicode(self.ui.searchEdit.text())
        lang = unicode(self.ui.langCombo.currentText())
        if not pattern:
            return
        self.doAction(u'Search subtitle "%s" (lang:%s)'%(pattern,lang),self.searchSubtitleAction,[lang,pattern])

    def searchSubtitleAction(self, lang, pattern):
        self.ui.stackedWidget.setCurrentWidget(self.ui.list_page)
        for mini in self.minis:
            self.ui.list_content.layout().removeWidget(mini)
            mini.hide()
            mini.deleteLater()

        self.minis = []
        self.ui.searchEdit.setEnabled(False)
        QApplication.setOverrideCursor( Qt.WaitCursor )

        backend_name = str(self.ui.backendEdit.itemData(self.ui.backendEdit.currentIndex()).toString())

        self.process = QtDo(self.weboob, self.addSubtitle)
        self.process.do('iter_subtitles', lang, pattern, backends=backend_name, caps=ICapSubtitle)

    def addSubtitle(self, backend, subtitle):
        if not backend:
            self.ui.searchEdit.setEnabled(True)
            QApplication.restoreOverrideCursor()
            self.process = None
            return
        minisubtitle = MiniSubtitle(self.weboob, backend, subtitle, self)
        self.ui.list_content.layout().addWidget(minisubtitle)
        self.minis.append(minisubtitle)

    def displaySubtitle(self, subtitle, backend):
        self.ui.stackedWidget.setCurrentWidget(self.ui.info_page)
        if self.current_info_widget != None:
            self.ui.info_content.layout().removeWidget(self.current_info_widget)
            self.current_info_widget.hide()
            self.current_info_widget.deleteLater()
        wsubtitle = Subtitle(subtitle, backend, self)
        self.ui.info_content.layout().addWidget(wsubtitle)
        self.current_info_widget = wsubtitle

    def closeEvent(self, ev):
        self.config.set('settings', 'backend', str(self.ui.backendEdit.itemData(self.ui.backendEdit.currentIndex()).toString()))
        self.saveSearchHistory()

        self.config.save()
        ev.accept()
