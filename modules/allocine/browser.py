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


from weboob.tools.browser import BaseBrowser
from weboob.capabilities.base import NotAvailable, NotLoaded
from weboob.capabilities.cinema import Movie, Person
from weboob.tools.json import json

from datetime import datetime

__all__ = ['AllocineBrowser']


class AllocineBrowser(BaseBrowser):
    DOMAIN = 'api.allocine.fr'
    PROTOCOL = 'http'
    ENCODING = 'utf-8'
    USER_AGENT = BaseBrowser.USER_AGENTS['wget']

    def iter_movies(self, pattern):
        res = self.readurl('http://api.allocine.fr/rest/v3/search?partner=YW5kcm9pZC12M3M&filter=movie&q=%s&format=json' % pattern.encode('utf-8'))
        jres = json.loads(res)
        for m in jres['feed']['movie']:
            tdesc = u''
            if 'title' in m:
                tdesc += '%s' % m['title']
            if 'productionYear' in m:
                tdesc += ' ; %s' % m['productionYear']
            elif 'release' in m:
                tdesc += ' ; %s' % m['release']['releaseDate']
            if 'castingShort' in m and 'actors' in m['castingShort']:
                tdesc += ' ; %s' % m['castingShort']['actors']
            short_description = tdesc.strip('; ')
            movie = Movie(m['code'], unicode(m['originalTitle']))
            movie.other_titles = NotLoaded
            movie.release_date = NotLoaded
            movie.duration = NotLoaded
            movie.short_description = short_description
            movie.pitch = NotLoaded
            movie.country = NotLoaded
            movie.note = NotLoaded
            movie.roles = NotLoaded
            movie.all_release_dates = NotLoaded
            movie.thumbnail_url = NotLoaded
            yield movie

    def iter_persons(self, pattern):
        res = self.readurl('http://api.allocine.fr/rest/v3/search?partner=YW5kcm9pZC12M3M&filter=person&q=%s&format=json' % pattern.encode('utf-8'))
        jres = json.loads(res)
        for p in jres['feed']['person']:
            thumbnail_url = NotAvailable
            if 'picture' in p:
                thumbnail_url = unicode(p['picture']['href'])
            person = Person(p['code'], unicode(p['name']))
            desc = u''
            if 'birthDate' in p:
                desc += '(%s), ' % p['birthDate']
            if 'activity' in p:
                for a in p['activity']:
                    desc += '%s, ' % a['$']
            person.real_name = NotLoaded
            person.birth_place = NotLoaded
            person.birth_date = NotLoaded
            person.death_date = NotLoaded
            person.gender = NotLoaded
            person.nationality = NotLoaded
            person.short_biography = NotLoaded
            person.short_description = desc.strip(', ')
            person.roles = NotLoaded
            person.thumbnail_url = thumbnail_url
            yield person

    def get_movie(self, id):
        res = self.readurl(
                'http://api.allocine.fr/rest/v3/movie?partner=YW5kcm9pZC12M3M&code=%s&profile=large&mediafmt=mp4-lc&format=json&filter=movie&striptags=synopsis,synopsisshort' % id)
        if res is not None:
            jres = json.loads(res)['movie']
        else:
            return None
        title = NotAvailable
        duration = NotAvailable
        release_date = NotAvailable
        pitch = NotAvailable
        country = NotAvailable
        note = NotAvailable
        short_description = NotAvailable
        thumbnail_url = NotAvailable
        other_titles = []
        genres = []
        roles = {}

        if 'originalTitle' not in jres:
            return
        title = unicode(jres['originalTitle'].strip())
        if 'picture' in jres:
            thumbnail_url = unicode(jres['picture']['href'])
        if 'genre' in jres:
            for g in jres['genre']:
                genres.append(g['$'])
        if 'runtime' in jres:
            nbsecs = jres['runtime']
            duration = nbsecs / 60
        if 'release' in jres:
            dstr = str(jres['release']['releaseDate'])
            tdate = dstr.split('-')
            day = 1
            month = 1
            year = 1901
            if len(tdate) > 2:
                year = int(tdate[0])
                month = int(tdate[1])
                day = int(tdate[2])
            release_date = datetime(year, month, day)
        if 'nationality' in jres:
            country = u''
            for c in jres['nationality']:
                country += '%s, ' % c['$']
            country = country.strip(', ')
        if 'synopsis' in jres:
            pitch = unicode(jres['synopsis'])
        if 'statistics' in jres and 'userRating' in jres['statistics']:
            note = u'%s/10 (%s votes)' % (jres['statistics']['userRating'], jres['statistics']['userReviewCount'])
        if 'castMember' in jres:
            for cast in jres['castMember']:
                if cast['activity']['$'] not in roles:
                    roles[cast['activity']['$']] = []
                roles[cast['activity']['$']].append(cast['person']['name'])

        movie = Movie(id, title)
        movie.other_titles = other_titles
        movie.release_date = release_date
        movie.duration = duration
        movie.genres = genres
        movie.pitch = pitch
        movie.country = country
        movie.note = note
        movie.roles = roles
        movie.short_description = short_description
        movie.all_release_dates = NotLoaded
        movie.thumbnail_url = thumbnail_url
        return movie

    def get_person(self, id):
        res = self.readurl(
                'http://api.allocine.fr/rest/v3/person?partner=YW5kcm9pZC12M3M&profile=large&code=%s&mediafmt=mp4-lc&filter=movie&format=json&striptags=biography' % id)
        if res is not None:
            jres = json.loads(res)['person']
        else:
            return None
        name = NotAvailable
        short_biography = NotAvailable
        biography = NotAvailable
        short_description = NotAvailable
        birth_place = NotAvailable
        birth_date = NotAvailable
        death_date = NotAvailable
        real_name = NotAvailable
        gender = NotAvailable
        thumbnail_url = NotAvailable
        roles = {}
        nationality = NotAvailable

        if 'name' in jres:
            name = u''
            if 'given' in jres['name']:
                name += jres['name']['given']
            if 'family' in jres['name']:
                name += ' %s' % jres['name']['family']
        if 'biographyShort' in jres:
            short_biography = unicode(jres['biographyShort'])
        if 'birthPlace' in jres:
            birth_place = unicode(jres['birthPlace'])
        if 'birthDate' in jres:
            df = jres['birthDate'].split('-')
            birth_date = datetime(int(df[0]), int(df[1]), int(df[2]))
        if 'deathDate' in jres:
            df = jres['deathDate'].split('-')
            death_date = datetime(int(df[0]), int(df[1]), int(df[2]))
        if 'realName' in jres:
            real_name = unicode(jres['realName'])
        if 'gender' in jres:
            gcode = jres['gender']
            if gcode == 1:
                gender = u'Male'
            else:
                gender = u'Female'
        if 'picture' in jres:
            thumbnail_url = unicode(jres['picture']['href'])
        if 'nationality' in jres:
            nationality = u''
            for n in jres['nationality']:
                nationality += '%s, ' % n['$']
            nationality = nationality.strip(', ')
        if 'biography' in jres:
            biography = unicode(jres['biography'])
        if 'participation' in jres:
            for m in jres['participation']:
                if m['activity']['$'] not in roles:
                    roles[m['activity']['$']] = []
                roles[m['activity']['$']].append(u'(%s) %s' % (m['movie']['productionYear'], m['movie']['originalTitle']))


        person = Person(id, name)
        person.real_name = real_name
        person.birth_date = birth_date
        person.death_date = death_date
        person.birth_place = birth_place
        person.gender = gender
        person.nationality = nationality
        person.short_biography = short_biography
        person.biography = biography
        person.short_description = short_description
        person.roles = roles
        person.thumbnail_url = thumbnail_url
        return person

    def iter_movie_persons(self, movie_id, role):
        res = self.readurl(
                'http://api.allocine.fr/rest/v3/movie?partner=YW5kcm9pZC12M3M&code=%s&profile=large&mediafmt=mp4-lc&format=json&filter=movie&striptags=synopsis,synopsisshort' % movie_id)
        if res is not None:
            jres = json.loads(res)['movie']
        else:
            return
        if 'castMember' in jres:
            for cast in jres['castMember']:
                id = cast['person']['code']
                name = unicode(cast['person']['name'])
                short_description = unicode(cast['activity']['$'])
                if 'role' in cast:
                    short_description += ', %s' % cast['role']
                thumbnail_url = NotAvailable
                if 'picture' in cast:
                    thumbnail_url = unicode(cast['picture']['href'])
                person = Person(id, name)
                person.short_description = short_description
                person.real_name = NotLoaded
                person.birth_place = NotLoaded
                person.birth_date = NotLoaded
                person.death_date = NotLoaded
                person.gender = NotLoaded
                person.nationality = NotLoaded
                person.short_biography = NotLoaded
                person.roles = NotLoaded
                person.thumbnail_url = thumbnail_url
                yield person

    def iter_person_movies(self, person_id, role_filter):
        res = self.readurl(
                'http://api.allocine.fr/rest/v3/filmography?partner=YW5kcm9pZC12M3M&profile=medium&code=%s&filter=movie&format=json' % person_id)
        if res is not None:
            jres = json.loads(res)['person']
        else:
            return
        for m in jres['participation']:
            if (role_filter is None or (role_filter is not None and m['activity']['$'].lower().strip() == role_filter)):
                prod_year = '????'
                if 'productionYear' in m['movie']:
                    prod_year = m['movie']['productionYear']
                short_description = u'(%s) %s' % (prod_year, m['activity']['$'])
                if 'role' in m:
                    short_description += ', %s' % m['role']
                movie = Movie(m['movie']['code'], unicode(m['movie']['originalTitle']))
                movie.other_titles = NotLoaded
                movie.release_date = NotLoaded
                movie.duration = NotLoaded
                movie.short_description = short_description
                movie.pitch = NotLoaded
                movie.country = NotLoaded
                movie.note = NotLoaded
                movie.roles = NotLoaded
                movie.all_release_dates = NotLoaded
                movie.thumbnail_url = NotLoaded
                yield movie

    def iter_person_movies_ids(self, person_id):
        res = self.readurl(
                'http://api.allocine.fr/rest/v3/filmography?partner=YW5kcm9pZC12M3M&profile=medium&code=%s&filter=movie&format=json' % person_id)
        if res is not None:
            jres = json.loads(res)['person']
        else:
            return
        for m in jres['participation']:
            yield unicode(m['movie']['code'])

    def iter_movie_persons_ids(self, movie_id):
        res = self.readurl(
                'http://api.allocine.fr/rest/v3/movie?partner=YW5kcm9pZC12M3M&code=%s&profile=large&mediafmt=mp4-lc&format=json&filter=movie&striptags=synopsis,synopsisshort' % movie_id)
        if res is not None:
            jres = json.loads(res)['movie']
        else:
            return
        if 'castMember' in jres:
            for cast in jres['castMember']:
                yield unicode(cast['person']['code'])

    def get_movie_releases(self, id, country):
        return
