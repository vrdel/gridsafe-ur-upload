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
import ConfigParser

GRIDSAFECLIENTPATH='/opt/gridsafe-ige/ige-rupi-client'

CONFIG = '/etc/gridsafe-ur-upload/gridsafe-ur-upload.ini'

def xml(output):
    for ur in output.split():
        if ur.endswith('.xml'):
            yield ur


def clean(temp):
    os.unlink(temp)
    os.unsetenv('BATCH2UR')


def main():
    lfs = '%(name)s[%(process)s]: %(levelname)s %(message)s'
    lf = logging.Formatter(lfs)
    lv = logging.INFO

    logging.basicConfig(level=lv, format=lfs)
    logger = logging.getLogger(os.path.basename(sys.argv[0]))
    sh = logging.handlers.SysLogHandler('/dev/log', logging.handlers.SysLogHandler.LOG_USER)
    sh.setFormatter(lf)
    sh.setLevel(lv)
    logger.addHandler(sh)

    acctfile, dirb2u, client, server, lookb = '', '', '', '', ''

    try:
        config = ConfigParser.ConfigParser()
        if config.read(CONFIG):
            for section in config.sections():
                if section.startswith('General'):
                    if config.has_option(section, 'SGEAccounting'):
                        acctfile = config.get(section, 'SGEAccounting')
                    if config.has_option(section, 'Batch2URRecordsPath'):
                        dirb2u = config.get(section, 'Batch2URRecordsPath')
                    if config.has_option(section, 'GridsafeRUPI'):
                        server = config.get(section, 'GridsafeRUPI')
                    if config.has_option(section, 'GridsafeClientPath'):
                        client = config.get(section, 'GridsafeClientPath')
                    if config.has_option(section, 'LookBehindDays'):
                        lookb = int(config.get(section, 'LookBehindDays'))
        else:
            logger.error('Missing %s' % CONFIG)
            raise SystemExit(1)

    except (ConfigParser.MissingSectionHeaderError, SystemExit) as e:
        if getattr(e, 'filename', False):
            logger.error(e.filename + ' is not a valid configuration file')
            logger.error(e.message)
        raise SystemExit(1)

    parser = argparse.ArgumentParser()
    parser.add_argument('-f', dest='acctfile', nargs=1, metavar='SGE accounting file', type=str)
    parser.add_argument('-u', dest='dirb2u', nargs=1, metavar='batch2ur upload directory', type=str)
    parser.add_argument('-s', dest='server', nargs=1, metavar='Gridsafe server RUPIService', type=str)
    parser.add_argument('-d', dest='date', nargs=1, metavar='YEAR-MONTH-DAY', required=True)
    parser.add_argument('-l', dest='lookb', nargs=1, metavar='look behind num days before specified date', type=int)
    args = parser.parse_args()

    exemptlines, dateargs = [], []

    try:
        tup = tuple([int(i) for i in args.date[0].split('-')])
        datespec = eval('datetime.date%s' % str(tup))
    except TypeError:
        logger.error('%s is not correct date format (YEAR-MONTH-DAY)' % str(tup))
        raise SystemExit(1)

    if not client:
        client = GRIDSAFECLIENTPATH
    if args.server:
        server = args.server[0]
    if args.acctfile:
        acctfile = args.acctfile[0]
    if args.dirb2u:
        dirb2u = args.dirb2u[0]
    if args.lookb:
        lookb = int(args.lookb[0])
    if lookb > 0:
        i = 1
        while i <= lookb:
            dateargs.append(datespec - datetime.timedelta(days=i))
            i += 1
    else:
        dateargs.append(datespec)

    try:
        os.stat(client)
        os.stat(dirb2u)
        with open(acctfile) as f:
            for line in f:
                if not re.match('^\s*\#', line):
                    fields = line.split(':')
                    if fields:
                        try:
                            datesge = datetime.date.fromtimestamp(float(fields[8]))
                            if datesge in dateargs:
                                exemptlines.append(line)
                        except IndexError:
                            logger.error('Cannot parse submission time in SGE accounting file, line: %s' % line)
                    else:
                        logger.error('Cannot parse SGE accounting file')
                        raise SystemExit(1)

    except (IOError, OSError, SystemExit) as e:
        logger.error(str(e))
        raise SystemExit(1)

    if exemptlines:
        logger.info('Selected %d jobs from %s for dates %s' % (len(exemptlines), acctfile, ' '.join([str(date) for date in dateargs])))

        handle, temp = tempfile.mkstemp(text=True)
        os.putenv('BATCH2UR', '/etc/batch2ur/batch2ur.conf')

        logger.info('Creating %s temp file' % temp)
        try:
            with open(temp, 'w') as f:
                f.writelines(exemptlines)
        except IOError as e:
            logger.error(str(e))
            raise SystemExit(1)

        st = time.time()
        try:
            logger.info('Called batch2ur %s' % temp)
            outb2ur = subprocess.check_output('batch2ur %s' % temp, shell=True, stderr=subprocess.STDOUT)

            dur = round(time.time() - st, 2)
            urs = [u for u in xml(outb2ur)]
            if len(urs) > 20:
                logger.info('Generated %d usage records in %.2fs at %s' % (len(urs), dur, dirb2u))
            else:
                logger.info('Generated %d usage records in %.2fs at %s: %s' % (len(urs), dur, dirb2u, ' '.join(urs)))

            os.chdir(client)

            pathurs = [str(dirb2u + '/' + u) for u in urs]
        except subprocess.CalledProcessError as e:
            logger.error(str(e))
            clean(temp)
            raise SystemExit(1)
        except KeyboardInterrupt:
            clean(temp)
            logger.error('Terminated batch2ur %s' % temp)
            raise SystemExit(1)

        st = time.time()
        logger.info('Called ige-rupi-client.sh %s for every generated usage record' % server)
        errur = 0
        for ur in pathurs:
            try:
                execstr = './ige-rupi-client.sh %s %s' % (server, ur)
                outcl = subprocess.check_output(execstr, shell=True, stderr=subprocess.STDOUT)
                if 'Exception' in outcl:
                    raise subprocess.CalledProcessError(1, cmd=execstr, output=outcl)
            except subprocess.CalledProcessError as e:
                logger.error(str(e))
                logger.error('Command output (512 chars): %.512s' % e.output.replace('\n', ' '))
                errur += 1
            except KeyboardInterrupt:
                clean(temp)
                logger.error('Terminated: %s' % execstr)
                raise SystemExit(1)

        if len(urs) - errur > 0:
            dur = round(time.time() - st, 2)
            logger.info('Uploaded to Gridsafe RUPIService %d usage records in %.2fs' % (len(urs) - errur, dur))
        else:
            logger.error('Failed to upload all usage records')

        clean(temp)
        raise SystemExit(0)

    else:
        logger.info('No jobs in %s for dates %s' % (acctfile, ' '.join([str(date) for date in dateargs])))
        raise SystemExit(0)

main()
