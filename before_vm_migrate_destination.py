#!/usr/bin/python

import os
import sys
import ast
import hooking
import tempfile
import traceback
from xml.dom import minidom

def createFloppy(filename, path, content):

    if os.path.exists(path):
        os.remove(path)

    # create floppy file system
    command = ['/sbin/mkfs.msdos', '-C', path, '1440']
    retcode, out, err = hooking.execCmd(command, sudo=True, raw=True)
    if retcode != 0:
        sys.stderr.write('floppyinject-before-dest-migration: error /sbin/mkfs.msdos fs: %s\n' % err)
        sys.exit(2)

    owner = '36:36'
    command = ['/bin/chown', owner, path]
    retcode, out, err = hooking.execCmd(command, sudo=True, raw=True)
    if retcode != 0:
        sys.stderr.write('floppyinject-before-dest-migration: error /bin/chown: %s' % err)
        sys.exit(2)


    # create floppy file system
    command = ['/bin/chmod', '0770', path]
    retcode, out, err = hooking.execCmd(command, sudo=True, raw=True)
    if retcode != 0:
        sys.stderr.write('floppyinject-before-dest-migration: error /bin/chmod: %s' % err)
        sys.exit(2)

    
    # mount the floppy file
    mntpoint = tempfile.mkdtemp()
    command = ['/bin/mount', '-o', 'loop,uid=36,gid=36' , path, mntpoint]
    sys.stderr.write('shahar: %s\n' % ' '.join(command))
    retcode, out, err = hooking.execCmd(command, sudo=True, raw=True)
    if retcode != 0:
        sys.stderr.write('floppyinject-before-dest-migration: error /bin/mount: %s' % err)
        sys.exit(2)


    # write the file content
    contentpath = os.path.join(mntpoint, filename)
    f = open(contentpath, 'w')
    f.write(content)
    f.close()


    # unmounting
    command = ['/bin/umount', mntpoint]
    retcode, out, err = hooking.execCmd(command, sudo=True, raw=True)
    if retcode != 0:
        sys.stderr.write('floppyinject-before-dest-migration: error /bin/umount: %s' % err)
        sys.exit(2)


    # remove tempdir
    command = ['/bin/rmdir',  mntpoint]
    retcode, out, err = hooking.execCmd(command, sudo=True, raw=True)
    if retcode != 0:
        sys.stderr.write('floppyinject-before-dest-migration: error /bin/rmdir: %s' % err)
        sys.exit(2)


if os.environ.has_key('floppyinject'):
    try:
        pos = os.environ['floppyinject'].find(':')
        filename = os.environ['floppyinject'][:pos]
        content = os.environ['floppyinject'][pos+1:]

        path = '/tmp/%s' % filename

        createFloppy(filename, path, content)

    except:
        sys.stderr.write('floppyinject-before-dest-migration: [unexpected error]: %s\n' % traceback.format_exc())
        sys.exit(2)
