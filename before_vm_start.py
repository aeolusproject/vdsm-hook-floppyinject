#!/usr/bin/python

import os
import base64
import sys
import ast
import utils
import hooking
import tempfile
import traceback
import datetime
from xml.dom import minidom

'''
floppyinject vdsm hook
======================
Hook create a floppy disk on the fly with user provided content.
ie. user supply file name and file content and hooks will create
floppy disk on destination host, will mount it as floppy disk -
and will handle migration.
giving the input "myfile.vfd:data" will create a floppy with single
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

FDA_PATH = "/var/run/vdsm"

def get_date():
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def log(msg, fd=sys.stderr):
    fd.write("[%s] %s\n" % (get_date(), msg))

def format_error(command, err=None):
    return "floppyinject error: %s (%s)" % (" ".join(command), err)

def addFloppyElement(domxml, path):
    if not os.path.isfile(path):
        raise Exception(format_error("file does not exist: %s" % path))

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

    # create floppy file system
    command = ['/sbin/mkfs.msdos', '-C', path, '1440']
    retcode, out, err = utils.execCmd(command, sudo=True, raw=True)
    if retcode != 0:
        log(format_error(command, err))
        raise Exception(format_error(command, err))

    owner = '36:36'
    command = ['/bin/chown', owner, path]
    retcode, out, err = utils.execCmd(command, sudo=True, raw=True)
    if retcode != 0:
        raise Exception(format_error(command, err))

    command = ['/bin/chmod', '0770', path]
    retcode, out, err = utils.execCmd(command, sudo=True, raw=True)
    if retcode != 0:
        raise Exception(format_error(command, err))

    try:
        # mount the floppy device in a tmpdir as a loopback
        mntpoint = tempfile.mkdtemp()
        command = ['/bin/mount', '-o', 'loop,uid=36,gid=36' , path, mntpoint]
        log('shahar: %s\n' % ' '.join(command))
        retcode, out, err = utils.execCmd(command, sudo=True, raw=True)
        if retcode != 0:
            raise Exception(format_error(command, err))

        # base64 decode the content
        content = base64.decodestring(content)

        # write the file content
        contentpath = os.path.join(mntpoint, filename)
        f = open(contentpath, 'w')
        f.write(content)
        f.close()
    finally:
        # unmount the loopback
        command = ['/bin/umount', mntpoint]
        retcode, out, err = utils.execCmd(command, sudo=True, raw=True)
        if retcode != 0:
            # record the error, but don't die ... still need to rm tmpdir
            log("floppyinject error: %s (%s)" % (command.join(" "), err))

        # remove tempdir
        command = ['/bin/rmdir',  mntpoint]
        retcode, out, err = utils.execCmd(command, sudo=True, raw=True)
        if retcode != 0:
            # record the error, but don't die
            log("floppyinject error: %s (%s)" % (command.join(" "), err))


def getVirtXML():
    return hooking.read_domxml()

def writeVirtXML(xml):
    hooking.write_domxml(xml)

def getVirtUUID(xml):
   uuid_node = xml.getElementsByTagName("uuid")[0]
   return uuid_node.firstChild.nodeValue

def getFloppyDeviceDir(xml):
    uuid = getVirtUUID(xml)
    floppy_device_dir = "%s/%s.fda" % (FDA_PATH, uuid)
    return floppy_device_dir

if os.environ.has_key('floppyinject'):
    try:
        virt_xml = getVirtXML()

        filename, content = os.environ['floppyinject'].split(":")

        path = getFloppyDeviceDir(virt_xml)
        createFloppy(filename, path, content)

        addFloppyElement(virt_xml, path)

        writeVirtXML(virt_xml)
    except Exception as e:
        log('floppyinject: [unexpected error]: %s\n' % traceback.format_exc())
        sys.exit(2)
