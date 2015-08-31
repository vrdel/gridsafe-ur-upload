from distutils.core import setup
import os, sys

NAME='gridsafe-ur-upload'

def get_ver():
    try:
        for line in open(NAME+'.spec'):
            if "Version:" in line:
                return line.split()[1]
    except IOError:
        print "Make sure that %s is in directory"  % (NAME+'.spec')
        sys.exit(1)

setup(name=NAME,
    version=get_ver(),
    description='Package provides scripts for generating and uploading usage records to Gridsafe Accounting Web Service',
    author='SRCE',
    author_email='daniel.vrcic@srce.hr',
    license='GPL',
    long_description='''Package provides scripts for generating and uploading usage records to Gridsafe
                        Accounting Web Service. It is a bridge between batch2ur utility that generates
                        usage records from Globus DB and SGE accounting file and gridsafe-ige-client
                        that uploads them to Web Service.''',
    scripts = ['bin/ur_genupl.py', 'bin/ur_jobdates.py'],
    data_files = [
        ('/etc/gridsafe-ur-upload/', ['conf/gridsafe-ur-upload.ini']),
        ('/etc/cron.d/', ['cronjobs/gridsafe-ur-upload']),
    ]
)
