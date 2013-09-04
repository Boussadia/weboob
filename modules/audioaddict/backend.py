# -*- coding: utf-8 -*-

# Copyright(C) 2013 Pierre Mazière
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


from weboob.capabilities.radio import ICapRadio, Radio, Stream, Emission
from weboob.capabilities.collection import ICapCollection, Collection
from weboob.tools.backend import BaseBackend, BackendConfig
from weboob.tools.value import Value
from weboob.tools.browser import StandardBrowser
from weboob.tools.misc import to_unicode
import time

__all__ = ['AudioAddictBackend']

#
# WARNING
#
# AudioAddict playlists do not seem to be appreciated by mplayer
# VLC plays them successfully, therefore I advice to set the media_player
# option to another player in the ~/.config/weboob/radioob config file:
# [ROOT]
# media_player = your_non_mplayer_player

class AudioAddictBackend(BaseBackend, ICapRadio, ICapCollection):
    NAME = 'audioaddict'
    MAINTAINER = u'Pierre Mazière'
    EMAIL = 'pierre.maziere@gmx.com'
    VERSION = '0.h'
    DESCRIPTION = u'Internet radios powered by audioaddict.com services'
    LICENSE = 'AGPLv3+'
    BROWSER = StandardBrowser

# Data extracted from http://tobiass.eu/api-doc.html
    NETWORKS = {
        'DI': {
            'desc': 'Digitally Imported addictive electronic music',
            'domain': 'di.fm',
            'streams': {'android_low':{'rate': 40, 'fmt': 'aac'},
                        'android': {'rate': 64, 'fmt': 'aac'},
                        'android_high': {'rate': 96, 'fmt': 'aac'},
                        'android_premium_low': {'rate': 40, 'fmt': 'aac'},
                        'android_premium_medium': {'rate': 64, 'fmt': 'aac'},
                        'android_premium': {'rate': 128, 'fmt': 'aac'},
                        'android_premium_high': {'rate': 256, 'fmt': 'aac'},
                        'public1': {'rate': 64, 'fmt': 'aac'},
                        'public2': {'rate': 40, 'fmt': 'aac'},
                        'public3': {'rate': 96, 'fmt': 'mp3'},
                        'premium_low': {'rate': 40, 'fmt': 'aac'},
                        'premium_medium': {'rate': 64, 'fmt': 'aac'},
                        'premium': {'rate': 128, 'fmt': 'aac'},
                        'premium_high': {'rate': 256, 'fmt': 'mp3'}
                        }
        },
        'SKYfm': {
            'desc': 'SKY FM radio',
            'domain': 'sky.fm',
            'streams': {'appleapp_low': {'rate': 40, 'fmt': 'aac'},
                        'appleapp': {'rate': 64, 'fmt': 'aac'},
                        'appleapp_high': {'rate': 96, 'fmt': 'mp3'},
                        'appleapp_premium_medium': {'rate': 64, 'fmt': 'aac'},
                        'appleapp_premium': {'rate': 128, 'fmt': 'aac'},
                        'appleapp_premium_high': {'rate': 256, 'fmt': 'mp3'},
                        'public1': {'rate': 40, 'fmt': 'aac'},
                        'public5': {'rate': 40, 'fmt': 'wma'},
                        'public3': {'rate': 96, 'fmt': 'mp3'},
                        'premium_low': {'rate': 40, 'fmt': 'aac'},
                        'premium_medium': {'rate': 64, 'fmt': 'aac'},
                        'premium': {'rate': 128, 'fmt': 'aac'},
                        'premium_high': {'rate': 256, 'fmt': 'mp3'}
                        }
        },
        'JazzRadio': {
            'desc': 'Jazz Radio',
            'domain': 'jazzradio.com',
            'streams': {'appleapp_low': {'rate': 40, 'fmt': 'aac'},
                        'appleapp': {'rate': 64, 'fmt': 'aac'},
                        'appleapp_premium_medium': {'rate': 64, 'fmt': 'aac'},
                        'appleapp_premium': {'rate': 128, 'fmt': 'aac'},
                        'appleapp_premium_high': {'rate': 256, 'fmt': 'mp3'},
                        'public1': {'rate': 40, 'fmt': 'aac'},
                        'public3': {'rate': 64, 'fmt': 'mp3'},
                        'premium_low': {'rate': 40, 'fmt': 'aac'},
                        'premium_medium': {'rate': 64, 'fmt': 'aac'},
                        'premium': {'rate': 128, 'fmt': 'aac'},
                        'premium_high': {'rate': 256, 'fmt': 'mp3'}
                        }
        },
    'RockRadio': {
        'desc': 'Rock Radio',
        'domain': 'rockradio.com',
        'streams': {'android_low': {'rate': 40, 'fmt': 'aac'},
                    'android': {'rate': 64, 'fmt': 'aac'},
                    'android_premium_medium': {'rate': 64, 'fmt': 'aac'},
                    'android_premium': {'rate': 128, 'fmt': 'aac'},
                    'android_premium_high': {'rate': 256, 'fmt': 'mp3'},
                    'public3': {'rate': 96, 'fmt': 'mp3'}
                    }
    },
    }

    CONFIG = BackendConfig(Value('networks',
                                 label='Selected Networks [%s](space separated)'%\
                                 ' '.join(NETWORKS.keys()), default=''),
                           Value('quality', label='Radio streaming quality',
                                 choices={'h':'high','l':'low'},
                                 default='h')
                           )

    def __init__(self, *a, **kw):
        super(AudioAddictBackend, self).__init__(*a, **kw)
        self.RADIOS = {}
        self.HISTORY = {}

    def _get_tracks_history(self, network):
        self._fetch_radio_list()
        domain=self.NETWORKS[network]['domain']
        url='http://api.audioaddict.com/v1/%s/track_history' %\
                (domain[:domain.rfind('.')])
        self.HISTORY[network] = self.browser.location(url)
        return self.HISTORY

    def create_default_browser(self):
        return self.create_browser(parser='json')

    def _get_stream_name(self,network,quality):
        streamName='public3'
        for name in self.NETWORKS[network]['streams'].keys():
            if name.startswith('public') and \
               self.NETWORKS[network]['streams'][name]['rate']>=64:
                if quality=='h':
                    streamName=name
                    break
            else:
                if quality=='l':
                    streamName=name
                    break
        return streamName

    def _fetch_radio_list(self):
        quality=self.config['quality'].get()
        for network in self.config['networks'].get().split():
            streamName=self._get_stream_name(network,quality)
            if not self.RADIOS:
                self.RADIOS={}
            if not network in self.RADIOS:
                document = self.browser.location('http://listen.%s/%s'%\
                                                 (self.NETWORKS[network]['domain'],
                                                  streamName))
                self.RADIOS[network]={}
                for info in document:
                    radio = info['key']
                    self.RADIOS[network][radio] = {}
                    self.RADIOS[network][radio]['id'] = info['id']
                    self.RADIOS[network][radio]['description'] = info['description']
                    self.RADIOS[network][radio]['name'] = info['name']
                    self.RADIOS[network][radio]['playlist'] = info['playlist']

        return self.RADIOS

    def iter_radios_search(self, pattern):
        self._fetch_radio_list()

        pattern = pattern.lower()
        for network in self.config['networks'].get().split():
            for radio in self.RADIOS[network]:
                radio_dict = self.RADIOS[network][radio]
                if pattern in radio_dict['name'].lower() or pattern in radio_dict['description'].lower():
                    yield self.get_radio(network,radio)

    def iter_resources(self, objs, split_path):
        self._fetch_radio_list()

        if Radio in objs:
            for network in self.config['networks'].get().split():
                if split_path == [network]:
                    for radio in self.RADIOS[network]:
                        yield self.get_radio(network,radio)
                    return
            for network in self.config['networks'].get().split():
                yield Collection([network],self.NETWORKS[network]['desc'])

    def get_current(self, network, radio):
        channel={}
        if not network in self.HISTORY:
            self._get_tracks_history(network)
            channel=self.HISTORY[network].get(str(self.RADIOS[network][radio]['id']))
        else:
            now=time.time()
            channel=self.HISTORY[network].get(str(self.RADIOS[network][radio]['id']))
            if channel is None:
                return 'Unknown', 'Unknown'
            if (channel.get('started')+channel.get('duration')) < now:
                self._get_tracks_history(network)
                channel=self.HISTORY[network].get(str(self.RADIOS[network][radio]['id']))

        artist = u'' + (channel.get('artist', '') or 'Unknown')
        title = u''+(channel.get('title', '') or 'Unknown')

        return artist, title

    def get_radio(self, network, radio):
        self._fetch_radio_list()

        if not isinstance(radio, Radio):
            radio = Radio(radio)

        if not radio.id in self.RADIOS[network]:
            return None

        radio_dict = self.RADIOS[network][radio.id]
        radio.title = radio_dict['name']
        radio.description = radio_dict['description']
        radio._network=network

        artist, title = self.get_current(network,radio.id)
        current = Emission(0)
        current.artist = artist
        current.title = title
        radio.current = current

        radio.streams = []
        name=self._get_stream_name(network,self.config['quality'].get())
        stream = Stream(name)
        stream.title = u'%s %skbps' %\
                (self.NETWORKS[network]['streams'][name]['fmt'],
                 self.NETWORKS[network]['streams'][name]['rate'])
        stream.url = 'http://listen.%s/%s/%s.pls'%\
                (self.NETWORKS[network]['domain'],name,radio.id)
        radio.streams.append(stream)
        return radio

    def fill_radio(self, radio, fields):
        if 'current' in fields:
            radio.current = Emission(0)
            radio.current.artist, radio.current.title = self.get_current(radio._network,radio.id)
            return radio

    OBJECTS = {Radio: fill_radio}

