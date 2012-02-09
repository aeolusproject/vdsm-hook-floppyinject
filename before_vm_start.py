#!/usr/bin/python

import os
import base64
import sys
import ast
import utils
import hooking
import tempfile
import traceback
from xml.dom import minidom

'''
floppyinject vdsm hook
======================
Hook create a floppy disk on the fly with user provided content.
ie. user supply file name and file content and hooks will create
floppy disk on destination host, will mount it as floppy disk -
and will handle migration.
giving the input "myfile.vfd=data" will create a floppy with single
file name myfile.vfd and the file content will be "data"

syntax:
floppyinject=myfile.txt:<file content>

libvirt:
<disk type='file' device='floppy'>
    <source file='/tmp/my.vfd'/>
    <target dev='fda' />
</disk>

Note:
    some linux distro need to load the floppy disk kernel module:
    # modprobe floppy
'''

def addFloppyElement(domxml, path):
    if not os.path.isfile(path):
        sys.stderr.write('floppyinject: file not exists: %s\n' % path)
        sys.exit(2)

    devices = domxml.getElementsByTagName('devices')[0]

    disk = domxml.createElement('disk')
    disk.setAttribute('type', 'file')
    disk.setAttribute('device', 'floppy')
    devices.appendChild(disk)

    source = domxml.createElement('source')
    source.setAttribute('file', path)
    disk.appendChild(source)

    target = domxml.createElement('target')
    target.setAttribute('dev', 'fda')
    disk.appendChild(target)

def createFloppy(filename, path, content):

    if os.path.exists(path):
        os.remove(path)

    # create floppy file system
    command = ['/sbin/mkfs.msdos', '-C', path, '1440']
    retcode, out, err = utils.execCmd(command, sudo=True, raw=True)
    if retcode != 0:
        sys.stderr.write('floppyinject: error /sbin/mkfs.msdos fs: %s\n' % err)
        sys.exit(2)

    owner = '36:36'
    command = ['/bin/chown', owner, path]
    retcode, out, err = utils.execCmd(command, sudo=True, raw=True)
    if retcode != 0:
        sys.stderr.write('floppyinject: error /bin/chown: %s' % err)
        sys.exit(2)


    # create floppy file system
    command = ['/bin/chmod', '0770', path]
    retcode, out, err = utils.execCmd(command, sudo=True, raw=True)
    if retcode != 0:
        sys.stderr.write('floppyinject: error /bin/chmod: %s' % err)
        sys.exit(2)


    # mount the floppy file
    mntpoint = tempfile.mkdtemp()
    command = ['/bin/mount', '-o', 'loop,uid=36,gid=36' , path, mntpoint]
    sys.stderr.write('shahar: %s\n' % ' '.join(command))
    retcode, out, err = utils.execCmd(command, sudo=True, raw=True)
    if retcode != 0:
        sys.stderr.write('floppyinject: error /bin/mount: %s' % err)
        sys.exit(2)

    # base64 decode the content
    content = base64.decodestring(content)

    # write the file content
    contentpath = os.path.join(mntpoint, filename)
    f = open(contentpath, 'w')
    f.write(content)
    f.close()


    # unmounting
    command = ['/bin/umount', mntpoint]
    retcode, out, err = utils.execCmd(command, sudo=True, raw=True)
    if retcode != 0:
        sys.stderr.write('floppyinject: error /bin/umount: %s' % err)
        sys.exit(2)


    # remove tempdir
    command = ['/bin/rmdir',  mntpoint]
    retcode, out, err = utils.execCmd(command, sudo=True, raw=True)
    if retcode != 0:
        sys.stderr.write('floppyinject: error /bin/rmdir: %s' % err)
        sys.exit(2)


if os.environ.has_key('floppyinject'):
    try:
        pos = os.environ['floppyinject'].find(':')
        filename = os.environ['floppyinject'][:pos]
        content = os.environ['floppyinject'][pos+1:]

        path = '/tmp/%s' % filename

        createFloppy(filename, path, content)

        domxml = hooking.read_domxml()
        addFloppyElement(domxml, path)

        hooking.write_domxml(domxml)

    except:
        sys.stderr.write('floppyinject: [unexpected error]: %s\n' % traceback.format_exc())
        sys.exit(2)
