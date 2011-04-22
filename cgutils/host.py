# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Library General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
#
# See the COPYING file for license information.
#
# Copyright (c) 2011 peo3 <peo314159265@gmail.com>

from __future__ import with_statement
import os, os.path
import re

try:
    import multiprocessing
except ImportError:
    # For python 2.5 or older
    class Multiprocessing:
        def cpu_count(self):
            return readfile('/proc/cpuinfo').count('CPU')
    multiprocessing = Multiprocessing()

def readfile(filepath):
    with open(filepath) as f:
        return f.read()

class CPUInfo():
    def __init__(self):
        self._update()
        self._total_usage_prev = self.total_usage

    def get_online(self):
        return readfile("/sys/devices/system/cpu/online").strip()

    def _update(self):
        line = readfile('/proc/stat').split('\n')[0]
        line = line[5:] # get rid of 'cpu  '
        usages = map(lambda x: int(x), line.split(' '))
        self.total_usage = sum(usages)/multiprocessing.cpu_count()
        # Total ticks
        #self.total_usage = int(line.split(' ')[5])
    def update(self):
        self._total_usage_prev = self.total_usage
        self._update()
    def get_total_usage_delta(self):
        return self.total_usage - self._total_usage_prev

class MemInfo(dict):
    def get_online(self):
        if not os.path.exists('/sys/devices/system/node/'):
            return '0'
        else:
            return readfile('/sys/devices/system/node/online').strip()

    _p = re.compile('^(?P<key>[\w\(\)]+):\s+(?P<val>\d+)')
    def _update(self):
        for line in readfile('/proc/meminfo').split('\n'):
            m = self._p.search(line)
            if m:
                self[m.group('key')] = int(m.group('val'))*1024

    def _calc(self):
        self['MemUsed'] = self['MemTotal'] - self['MemFree'] - \
                          self['Buffers'] - self['Cached']
        self['SwapUsed'] = self['SwapTotal'] - self['SwapFree'] - \
                           self['SwapCached']
        self['MemKernel'] = self['Slab'] + self['KernelStack'] + \
                            self['PageTables'] + self['VmallocUsed']
    def update(self):
        self._update()
        self._calc()
