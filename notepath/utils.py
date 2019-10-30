#!/usr/bin/env python3
# The function annotations in this module require Python 3.5 or higher.

import datetime
import os
import time

def _timestamp(pattern, when: float = None) -> str:
    if not when:
        when = time.time()
    date_object = datetime.datetime.fromtimestamp(when)
    timestamp = date_object.strftime(pattern)
    timestamp = timestamp.replace(' 0', ' ')
    return timestamp

def timestamp_for_filename(when: float = None) -> str:
    return _timestamp('%Y-%m-%d_%a_%H-%M-%S.%f', when)

def timestamp_for_logging(when: float = None) -> str:
    return _timestamp('%Y-%m-%d %a %H:%M:%S.%f', when)

def timestamp_for_journal(when: float = None) -> str:
    return _timestamp('%A %d %B %Y at %I:%M %p', when)

def format_filesize(num: int, suffix='B') -> str:
    for unit in ['','K','M','G','T','P','E','Z']:
        if abs(num) < 1024.0:
            return "%3.1f %s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f %s%s" % (num, 'Yi', suffix)

def get_readable_filesize(path: str) -> str:
    size = os.path.getsize(path)
    size = format_filesize(size)
    suffix = '.0 B'
    if size.endswith(suffix):
        size = size[:-len(suffix)] + ' bytes'
    return size

def get_readable_timespan(seconds: int) -> str:
    spans = [(60,    'second', 'seconds'),
             (60,    'minute', 'minutes'),
             (24,    'hour',   'hours'),
             (30,    'day',    'days'),
             (12,    'month',  'months'),
             (2**64, 'year',   'years'),
             ]
    num = seconds
    for limit, singular, plural in spans:
        if num < limit:
            n = int(num)
            rem = num - n
            if rem >= 0.5:
                n += 1
            unit = singular if n == 1 else plural
            return str(n) + ' ' + unit + ' ago'
        else:
            num /= limit
    return ''

def get_readable_moddate(path: str) -> str:
    # e.g. 2019-09-17 Tue 8:16 AM (2 hours ago)
    # or (1 day ago) or (30 minutes ago) or (2 months ago) or (2 years ago)
    try:
        then = os.path.getmtime(path)
    except OSError:
        return ''
    
    timestamp = timestamp_for_journal(then)
    now = time.time()
    span = get_readable_timespan(now - then)
    return timestamp + ' (' + span + ')'

if __name__ == '__main__':
    print('READABLE FILE STATS:')
    lines = []
    for f in os.scandir():
        lines.append(f.path
                     + ' --- ' + get_readable_filesize(f.path)
                     + ' --- ' + get_readable_moddate(f.path))
    lines.sort()
    for line in lines:
        print(line)

    print('')
    print('TIMESTAMPS IN THREE FORMATS:')
    print('--- Use in filenames:', timestamp_for_filename())
    print('--- Use in log files:', timestamp_for_logging())
    print('--- Use in a journal:', timestamp_for_journal())

