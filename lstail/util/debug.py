# -*- coding: utf-8 -*-
#
# This software may be modified and distributed under the terms
# of the MIT license.  See the LICENSE file for details.

from os import getpid


# ----------------------------------------------------------------------
def get_memory_usage():
    mem_usage = dict(rss=0.0)
    proc_status = f'/proc/{getpid()}/status'
    try:
        with open(proc_status, encoding='utf-8') as file_h:
            content = file_h.read()
    except IOError:
        return 0.0
    lines = content.strip().split('\n')
    for line in lines:
        if line.startswith('VmRSS:'):
            values = line.split(':')
            vmrss = values[1].strip()
            try:
                vmrss = vmrss.split()[0]
                vmrss = vmrss.strip()
                mem_usage['rss'] = float(vmrss) / 1024
                break
            except IndexError:
                break
    return mem_usage['rss']
