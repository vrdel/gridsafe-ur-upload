#!/usr/bin/python27

# Copyright (C) 2015 Daniel Vrcic <daniel.vrcic@srce.hr>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301  USA



import argparse
import datetime
import logging
import logging.handlers
import os
import re
import subprocess
import sys
import tempfile
import time


def main():
    logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')
    logger = logging.getLogger(os.path.basename(sys.argv[0]))

    parser = argparse.ArgumentParser()
    parser.add_argument('-f', dest='acctfile', nargs=1, metavar='SGE accounting file', type=str, required=True)
    parser.add_argument('-d', dest='date', nargs=1, metavar='YEAR-MONTH-DAY', required=True)
    parser.add_argument('-l', dest='lookb', nargs=1, metavar='look behind num days before specified date', type=int)
    args = parser.parse_args()

    dateargs, jobdatesl, jobdates = [], [], set()

    tup = tuple([int(i) for i in args.date[0].split('-')])
    datespec = eval('datetime.date%s' % str(tup))

    if args.lookb:
        i = 1
        while i <= args.lookb[0]:
            dateargs.append(datespec - datetime.timedelta(days=i))
            i += 1
    else:
        dateargs.append(datespec)

    try:
        with open(args.acctfile[0]) as f:
            for line in f:
                if not re.match('^\s*\#', line):
                    fields = line.split(':')
                    if fields:
                        try:
                            datesge = datetime.date.fromtimestamp(float(fields[8]))
                            if datesge in dateargs:
                                jobdatesl.append(str(datesge))
                        except IndexError:
                            logger.error('Cannot parse submission time in SGE accounting file, line: %s' % line)
                    else:
                        logger.error('Cannot parse SGE accounting file')
                        raise SystemExit(1)

        jobdates = set(jobdatesl)

    except (IOError, OSError) as e:
        logger.error(str(e))
        raise SystemExit(1)

    if jobdates:
        logger.info('Jobs exist for dates: %s' % (' '.join(sorted(jobdates, key=lambda s: s))))
    else:
        logger.info('Jobs do not exist for given dates')

    raise SystemExit(0)

main()
