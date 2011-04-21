#!/usr/bin/python

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
import sys
import os, os.path
import optparse

import cgroup
import host
import formatter

legends = {
    'cpuacct':"Consumed CPU time",
    'memory': "TotalUsed, RSS, SwapUsed",
    'blkio':  "Read, Write",
    'freezer':"State",
    }

def format_cpu(usages):
    return None

def format_cpuacct(usages):
    n = formatter.max_width_time
    return formatter.usec2str(usages['usage']).rjust(n)

def format_cpuset(usages):
    return None

def format_memory(usages):
    vals = [usages['total'],usages['rss'],usages['swap']]
    to_s = lambda v: formatter.byte2str(v).rjust(formatter.max_width_memory)
    return ','.join([to_s(val) for val in vals])

def format_blkio(usages):
    vals = [usages['read'],usages['write']]
    to_s = lambda v: formatter.byte2str(v).rjust(formatter.max_width_memory)
    return ','.join([to_s(val) for val in vals])

def format_freezer(usages):
    return usages['state']

formatters = {
    'cpu':    format_cpu,
    'cpuacct':format_cpuacct,
    'cpuset': format_cpuset,
    'memory': format_memory,
    'blkio':  format_blkio,
    'freezer':format_freezer,
    }

def get_cpuset_global_status():
    cpuinfo = host.CPUInfo()
    meminfo = host.MemInfo()
    return "Online CPU %s, Online Node %s"%(cpuinfo.get_online(),
                                            meminfo.get_online())

def get_memory_global_status():
    meminfo = host.MemInfo()
    meminfo.update()
    return "Total=%s, Used(w/o buffer/cache)=%s, SwapUsed=%s"% \
           (formatter.byte2str(meminfo['MemTotal']),
            formatter.byte2str(meminfo['MemUsed']),
            formatter.byte2str(meminfo['SwapUsed']))

get_global_status = {
    'cpu':    lambda: None,
    'cpuacct':lambda: None,
    'cpuset': get_cpuset_global_status,
    'memory': get_memory_global_status,
    'blkio':  lambda: None,
    'freezer':lambda: None,
    }

def print_cgroup(subsys_name, _cgroup, show_pid, verbose):
    status = formatters[subsys_name](_cgroup.usages)

    _cgroup.update_pids()
    if show_pid:
        cmds = sorted(["%s(%d)"%(_cgroup.get_cmd(pid),pid)
                       for pid in _cgroup.pids
                       if not _cgroup.is_kthread(pid)])
    else:
        cmds = sorted([_cgroup.get_cmd(pid)
                       for pid in _cgroup.pids
                       if not _cgroup.is_kthread(pid)])
    if verbose:
        procs = cmds
        s = "%s%s: %s"%('  '*_cgroup.depth, _cgroup.name, cmds)
    else:
        procs = ('%d procs'%(len(cmds),)).rjust(10)
        proc_indent = 12
        status_indent = 24
        s = "%s%s:"%('  '*_cgroup.depth, _cgroup.name)
        indent = proc_indent-len(s)
        indent = min(indent, 0)
        s = "%s%s%s"%(s,' '*indent, procs)
        indent = status_indent-len(s)
        indent = min(indent, 0)
        if status is None:
            s = "%s%s"%(s,' '*indent)
        else:
            s = "%s%s(%s)"%(s,' '*indent, status)
    print(s)

def main():
    DEFAULT_SUBSYSTEM = 'cpu'

    parser = optparse.OptionParser()
    parser.add_option('-o', action='store', type='string',
                      dest='target_subsystem', default=DEFAULT_SUBSYSTEM,
                      help='Specify a subsystem')
    parser.add_option('-v', '--verbose', action='store_true', dest='verbose',
                      default=False, help='Show detailed messages')
    parser.add_option('--debug', action='store_true', dest='debug',
                      default=False, help='Show debug messages')
    parser.add_option('-p', '--show-pid', action='store_true',
                      dest='show_pid', default=False,
                      help='Show PID (use with -v)')
    (options, _args) = parser.parse_args()
    if options.debug:
        print options

    if options.target_subsystem not in cgroup.subsystem2path:
        print('No such subsystem: %s'%(options.target_subsystem,))
        sys.exit(3)
    target_path = cgroup.subsystem2path[options.target_subsystem]
    mount_point = target_path

    root_cgroup = cgroup.scan_directory_recursively(
                      options.target_subsystem,
                      mount_point, mount_point)

    def print_cgroups_recursively(_cgroup):
        if options.debug:
            print(_cgroup)

        print_cgroup(options.target_subsystem, _cgroup, options.show_pid, options.verbose)
        for child in _cgroup.childs:
            print_cgroups_recursively(child)

    global_status = get_global_status[options.target_subsystem]()
    if global_status is not None:
        print('# '+global_status)
    if options.target_subsystem in legends:
        legend = legends[options.target_subsystem]
        print("# Legend: # of procs (%s)"%(legend,))
    else:
        print('# Legend: # of procs')
    print_cgroups_recursively(root_cgroup)

if __name__ == "__main__":
    main()
