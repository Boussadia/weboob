# -*- coding: utf-8 -*-

# Copyright(C) 2013  Florent Fourcot
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


from weboob.capabilities.base import empty
from weboob.capabilities.gauge import ICapGauge, SensorNotFound
from weboob.tools.application.repl import ReplApplication
from weboob.tools.application.formatters.iformatter import IFormatter

import sys

__all__ = ['Boobsize']


class GaugeFormatter(IFormatter):
    MANDATORY_FIELDS = ('name', 'object', 'sensors')

    def start_format(self, **kwargs):
        # Name = 27   Object = 10   City = 10  Sensors = 33
        self.output(' Name and ID                  Object     City       Sensors                         ')
        self.output('----------------------------+----------+----------+---------------------------------')

    def format_obj(self, obj, alias):
        name = obj.name
        city = u""
        if not empty(obj.city):
            city = obj.city

        if not obj.sensors or (len(obj.sensors) == 0):
            result = u' %s %s %s \n' %\
                   (self.colored('%-27s' % name[:27], 'red'),
                    self.colored('%-10s' % obj.object[:10], 'yellow'),
                    self.colored('%-10s' % city[:10], 'yellow')
                    )
            result += u' %s \n' % self.colored('%-47s' % obj.fullid[:47], 'blue')
        else:
            first = True
            firstaddress = obj.sensors[0].address
            for sensor in obj.sensors:
                sensorname = sensor.name
                # This is a int value, do not display it as a float
                if not empty(sensor.lastvalue.level):
                    if int(sensor.lastvalue.level) == sensor.lastvalue.level:
                        lastvalue = "%d " % sensor.lastvalue.level
                    else:
                        lastvalue = "%r " % sensor.lastvalue.level
                    if not empty(sensor.unit):
                        lastvalue += "%s" % sensor.unit
                else:
                    lastvalue = u"? "
                if first:
                    result = u' %s %s %s ' %\
                             (self.colored('%-27s' % name[:27], 'red'),
                              self.colored('%-10s' % obj.object[:10], 'yellow'),
                              self.colored('%-10s' % city[:10], 'yellow'),
                              )
                    if not empty(firstaddress):
                        result += u'%s' % self.colored('%-33s' % sensor.address[:33], 'yellow')
                    result += u'\n'
                    result += u' %s' % self.colored('%-47s' % obj.fullid[:47], 'blue')
                    result += u'   %s %s\n' %\
                              (self.colored('%-20s' % sensorname[:20], 'magenta'),
                               self.colored('%-13s' % lastvalue[:13], 'red')
                               )
                    first = False
                else:
                    result += u'                                                   %s %s\n' %\
                              (self.colored('%-20s' % sensorname[:20], 'magenta'),
                               self.colored('%-13s' % lastvalue[:13], 'red')
                               )
                    if not empty(sensor.address) and sensor.address != firstaddress:
                        result += u'                                                   %s \n' %\
                                  self.colored('%-33s' % sensor.address[:33], 'yellow')

        return result


class Boobsize(ReplApplication):
    APPNAME = 'Boobsize'
    VERSION = '0.i'
    COPYRIGHT = 'Copyright(C) 2013 Florent Fourcot'
    DESCRIPTION = "Console application allowing to display various sensors and gauges values."
    SHORT_DESCRIPTION = "display sensors and gauges values"
    CAPS = (ICapGauge)
    DEFAULT_FORMATTER = 'table'
    EXTRA_FORMATTERS = {'gauge_list':   GaugeFormatter, }
    COMMANDS_FORMATTERS = {'search':    'gauge_list',
                           }

    def main(self, argv):
        self.load_config()
        return ReplApplication.main(self, argv)

    def bcall_error_handler(self, backend, error, backtrace):
        if isinstance(error, SensorNotFound):
            msg = unicode(error) or 'Sensor not found (hint: try details command)'
            print >>sys.stderr, 'Error(%s): %s' % (backend.name, msg)
        else:
            return ReplApplication.bcall_error_handler(self, backend, error, backtrace)

    def do_search(self, pattern):
        """
        search [PATTERN]

        Display all gauges. If PATTERN is specified, search on a pattern.
        """
        self.change_path([u'gauges'])
        self.start_format()
        for backend, gauge in self.do('iter_gauges', pattern or None, caps=ICapGauge):
            self.cached_format(gauge)

    def complete_search(self, text, line, *ignored):
        args = line.split(' ')
        if len(args) == 2:
            return self._complete_object()

    def do_details(self, line):
        """
        details GAUGE_ID

        Display details of all sensors of the gauge.
        """
        gauge, pattern = self.parse_command_args(line, 2, 1)
        _id, backend_name = self.parse_id(gauge)

        self.start_format()
        for backend, sensor in self.do('iter_sensors', _id, pattern=pattern, backends=backend_name, caps=ICapGauge):
            self.format(sensor)

    def do_history(self, line):
        """
        history SENSOR_ID

        Get history of a specific sensor (use 'search' to find a gauge, and sensors GAUGE_ID to list sensors attached to the gauge).
        """
        gauge, = self.parse_command_args(line, 1, 1)
        _id, backend_name = self.parse_id(gauge)

        self.start_format()
        for backend, measure in self.do('iter_gauge_history', _id, backends=backend_name, caps=ICapGauge):
            self.format(measure)

    def complete_last_sensor_measure(self, text, line, *ignored):
        args = line.split(' ')
        if len(args) == 2:
            return self._complete_object()

    def do_last_sensor_measure(self, line):
        """
        last_sensor_measure SENSOR_ID

        Get last measure of a sensor.
        """
        gauge, = self.parse_command_args(line, 1, 1)
        _id, backend_name = self.parse_id(gauge)

        self.start_format()
        for backend, measure in self.do('get_last_measure', _id, backends=backend_name, caps=ICapGauge):
            self.format(measure)
